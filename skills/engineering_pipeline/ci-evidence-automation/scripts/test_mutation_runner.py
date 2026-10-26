"""Tests for mutation_runner.py -- every status, selection, merging, chunking, baselines, process handling and the
gate's negative controls.

    python test_mutation_runner.py          (or: python -m unittest test_mutation_runner)

Each test builds a tiny project (calc.py + its unittest file) in a temp dir and runs the runner as a separate
process with an outer timeout, so a runner bug cannot hang the suite. Hanging mutants write a marker file named
after their process id (MR_MARK_DIR), so leftover processes are found and cleaned up on every OS; checks that need
signals or the CPU-time limit run on POSIX only.
"""
import contextlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

RUNNER = str(Path(__file__).resolve().with_name("mutation_runner.py"))
sys.path.insert(0, str(Path(RUNNER).parent))
import mutation_runner as mr  # noqa: E402

HAVE_PROC = os.path.isdir("/proc/self") and os.name != "nt"
POSIX = os.name != "nt"
CALC = textwrap.dedent('''\
    def add(a, b):
        x = a
        return x + b


    def sub(a, b):
        x = a
        return x - b


    def slow(n):
        return n


    class Box:
        def size(self):
            return 3
''')
TESTS = textwrap.dedent('''\
    import os, sys, unittest
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pkg"))
    import calc


    class T(unittest.TestCase):
        def test_add(self):
            self.assertEqual(calc.add(2, 3), 5)

        def test_sub_sign(self):                      # weak on purpose: abs() mutant survives
            self.assertTrue(calc.sub(5, 3) > 0)

        def test_slow(self):
            self.assertEqual(calc.slow(1), 1)

        def test_box(self):
            self.assertEqual(calc.Box().size(), 3)


    if __name__ == "__main__":
        unittest.main()
''')
F = "pkg/calc.py"


def hang_code(tag, body):
    """Mutant body for slow(): write MR_MARK_DIR/<tag>.<pid>, then run `body`."""
    return ("    import os\n"
            "    d = os.environ.get('MR_MARK_DIR')\n"
            "    if d:\n"
            "        os.makedirs(d, exist_ok=True)\n"
            "        open(os.path.join(d, %r %% os.getpid()), 'w').close()\n" % (tag + ".%d")) + body


GRANDCHILD = ("import os\nd = os.environ.get('MR_MARK_DIR')\nif d:\n    os.makedirs(d, exist_ok=True)\n"
              "    open(os.path.join(d, 'G01.%d' % os.getpid()), 'w').close()\nwhile True:\n    pass\n")
BUSY = hang_code("T01", "    while True:\n        pass\n")
BLOCKED = hang_code("H01", "    import time\n    time.sleep(600)\n    return n\n")
HANG_CHILD = hang_code("G01p", "    import subprocess, sys\n    subprocess.Popen([sys.executable, '-c', %r]).wait()\n"
                               "    return n\n" % GRANDCHILD)
SPEC = {
    "copy": ["pkg", "tests"],
    "test": "python -m unittest discover -s tests",
    "timeout": 4,
    "mutants": [
        {"id": "K01", "name": "add flipped", "edits": [{"file": F, "old": "return x + b", "new": "return x - b"}]},
        {"id": "S01", "name": "sub abs (weak test)", "edits": [{"file": F, "old": "return x - b", "new": "return abs(x - b)"}]},
        {"id": "P01", "name": "ambiguous pattern", "edits": [{"file": F, "old": "    x = a\n", "new": "    x = a + 1\n"}]},
        {"id": "A01", "name": "anchored to add", "edits": [{"file": F, "func": "add", "old": "    x = a\n", "new": "    x = a + 1\n"}]},
        {"id": "T01", "name": "hang", "edits": [{"file": F, "func": "slow", "old": "    return n\n", "new": BUSY}]},
        {"id": "I01", "name": "syntax error", "edits": [{"file": F, "old": "return x + b", "new": "return x +"}]},
        {"id": "C01", "name": "method anchor", "edits": [{"file": F, "func": "Box.size", "old": "return 3", "new": "return 4"}]},
        {"id": "G01", "name": "hang in a grandchild", "edits": [{"file": F, "func": "slow", "old": "    return n\n",
                                                                 "new": HANG_CHILD}]},
        {"id": "H01", "name": "blocked hang (sleep)", "edits": [{"file": F, "func": "slow", "old": "    return n\n",
                                                                 "new": BLOCKED}]},
    ],
}
N = len(SPEC["mutants"])
EXPECT = {"K01": "killed", "S01": "survived", "P01": "pattern", "A01": "killed", "T01": "timeout",
          "I01": "invalid", "C01": "killed", "G01": "timeout", "H01": "timeout"}


def procs_under(path):
    """PIDs whose working directory is inside `path` (Linux /proc)."""
    out, prefix = [], str(path)
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                if os.readlink("/proc/%s/cwd" % d).startswith(prefix):
                    out.append(int(d))
            except OSError:
                pass
    return out


def kill_under(path):
    if HAVE_PROC:
        for pid in procs_under(path):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass


def pid_alive(pid):
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"], capture_output=True, text=True).stdout
        return (" %d " % pid) in (" " + " ".join(out.split()) + " ")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:                                                     # a zombie is dead for our purpose
        with open("/proc/%d/stat" % pid) as f:
            return f.read().rsplit(")", 1)[-1].split()[0] != "Z"
    except OSError:
        return True


def kill_pid(pid):
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def wait_for(cond, secs):
    t = time.time() + secs
    while time.time() < t:
        if cond():
            return True
        time.sleep(0.1)
    return cond()


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="mrtest_"))
        self.root = self.d / "proj"
        (self.root / "pkg").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / F).write_text(CALC, encoding="utf-8")
        (self.root / "tests" / "test_calc.py").write_text(TESTS, encoding="utf-8")
        self.marks = self.d / "marks"
        self.spec = self.write_spec(SPEC)
        self.out = self.d / "res.json"
        self.tmp = self.d / "tmp"

    def tearDown(self):
        for tag in ("T01", "H01", "G01", "G01p"):
            for pid in self.marked(tag):
                kill_pid(pid)
        kill_under(self.d)
        shutil.rmtree(self.d, ignore_errors=True)

    def write_spec(self, spec, name="spec.json"):
        spec = dict(spec, env=dict(spec.get("env") or {}, MR_MARK_DIR=str(self.marks)))
        p = self.d / name
        p.write_text(json.dumps(spec), encoding="utf-8")
        return p

    def marked(self, tag):
        return [int(p.name.split(".")[1]) for p in self.marks.glob(tag + ".*")] if self.marks.is_dir() else []

    def alive(self, *tags):
        return [pid for t in tags for pid in self.marked(t) if pid_alive(pid)]

    def cmd(self, *args, spec=None):
        return [sys.executable, RUNNER, str(spec or self.spec), "--root", str(self.root)] + list(args)

    def run_r(self, *args, spec=None, timeout=120, env=None):
        p = subprocess.run(self.cmd(*args, spec=spec), capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout + p.stderr

    def start_r(self, *args, spec=None):
        """Start the runner in the background; its output goes to <d>/bg.log."""
        self.bg_log = self.d / "bg.log"
        self.bg_fh = open(self.bg_log, "w")
        return subprocess.Popen(self.cmd(*args, spec=spec), stdout=self.bg_fh, stderr=subprocess.STDOUT)

    def stop_bg(self, a):
        try:
            a.kill()
            a.wait(timeout=20)
        finally:
            self.bg_fh.close()

    def results(self, path=None):
        return json.loads(Path(path or self.out).read_text(encoding="utf-8"))["results"]

    def listed(self, out):
        return [line.split()[1] for line in out.splitlines() if line[:4].strip().isdigit() and "[" in line]

    # ---- statuses and the gate
    def test_all_statuses(self):
        code, out = self.run_r("--jobs", "2", "--out", str(self.out), "--tmp", str(self.tmp))
        self.assertEqual(code, 1, out)                       # survived/pattern/invalid fail the gate
        got = {k: v["status"] for k, v in self.results().items()}
        self.assertEqual(got, EXPECT, out)
        r = self.results()
        self.assertIn("test_add", r["K01"]["failing"])
        self.assertEqual(r["P01"]["detail"], "PATTERN x2 in pkg/calc.py")
        self.assertIn("syntax error", r["I01"]["detail"])
        self.assertLess(r["T01"]["secs"], 4 + 5)             # killed at the timeout, not waited for
        self.assertLess(r["G01"]["secs"], 4 + 5)
        self.assertLess(r["H01"]["secs"], 4 + 5)
        self.assertEqual(list(r), [m["id"] for m in SPEC["mutants"]])   # spec order kept
        self.assertRegex(r["K01"]["at"], r"T\d\d:\d\d:\d\d[+-]\d\d:\d\d$")   # timestamps carry the UTC offset
        self.assertIn("GATE: FAIL", out)
        meta = json.loads(self.out.read_text(encoding="utf-8"))["meta"]
        self.assertTrue(meta["baselines"][SPEC["test"]]["ok"])
        self.assertEqual(len(meta["runner"]), 12)
        self.assertTrue(self.marked("G01") and self.marked("T01") and self.marked("H01"), "hang markers missing")
        self.assertEqual(self.alive("T01", "G01", "G01p", "H01"), [], "leftover test processes (tree not killed)")

    def test_gate_passes_without_bad_results(self):
        code, out = self.run_r("--only", "K01,A01,C01")
        self.assertEqual(code, 0, out)
        self.assertIn("GATE: PASS", out)

    def test_timeout_fails_only_strict(self):
        code, out = self.run_r("--only", "K01,T01")
        self.assertEqual(code, 0, out)
        code, out = self.run_r("--only", "K01,T01", "--strict")
        self.assertEqual(code, 1, out)

    def test_working_tree_untouched(self):
        before = (self.root / F).read_bytes()
        self.run_r("--jobs", "2", "--only", "K01,S01,I01,C01")
        self.assertEqual((self.root / F).read_bytes(), before)
        self.assertFalse(any(self.root.rglob("__pycache__")))

    def test_mutant_running_no_tests_is_error(self):
        spec = dict(SPEC, mutants=SPEC["mutants"] + [
            {"id": "N01", "name": "tests renamed away", "edits": [
                {"file": "tests/test_calc.py", "old": "def test_", "new": "def tst_", "count": 4}]}])
        code, out = self.run_r("--only", "N01", spec=self.write_spec(spec, "n.json"))
        self.assertEqual(code, 1, out)
        self.assertIn("N01      error", out)                 # not 'killed': nothing was tested
        self.assertIn("ran no tests", out)

    # ---- selection
    def test_only_glob_and_slice(self):
        code, out = self.run_r("--only", "K0*,A01,S01", "--slice", "1:2", "--out", str(self.out))
        self.assertEqual(list(self.results()), ["S01"], out)
        code, out = self.run_r("--only", "nope")
        self.assertEqual(code, 2, out)
        self.assertIn("matched nothing", out)
        code, out = self.run_r("--only", "K0*,K01", "--list")    # overlapping tokens are both satisfied
        self.assertEqual(code, 0, out)
        self.assertEqual(self.listed(out), ["K01"])
        code, out = self.run_r("--only", "K01 add flipped", "--list")
        self.assertEqual(self.listed(out), ["K01"], out)

    def test_changed_vs_snapshot(self):
        snap = self.d / "snap"
        code, out = self.run_r("--snapshot", str(snap))
        self.assertEqual(code, 0, out)
        self.run_r("--jobs", "2", "--out", str(self.out), "--only", "K01,S01,P01,A01,I01,C01")
        src = (self.root / F).read_text(encoding="utf-8").replace("    x = a\n    return x + b",
                                                                   "    x = a\n    y = 0\n    return x + b")
        (self.root / F).write_text(src, encoding="utf-8")
        code, out = self.run_r("--changed", str(snap), "--list")
        self.assertEqual(self.listed(out), ["K01", "P01", "A01", "I01"], out)   # add changed + P01 not unique
        code, out = self.run_r("--changed", str(snap), "--out", str(self.out), "--only", "K01,S01,P01,A01,I01,C01")
        self.assertIn("4 of %d mutants selected" % N, out)
        r = self.results()
        fresh = sorted(k for k, v in r.items() if v["fp"] == r["K01"]["fp"])
        self.assertEqual(fresh, ["A01", "I01", "K01", "P01"], out)   # only the changed ones were rerun
        # a mutant with no result in --out is selected even when its function did not change
        code, out = self.run_r("--changed", str(snap), "--out", str(self.d / "res2.json"), "--only", "K01,C01", "--list")
        self.assertEqual(self.listed(out), ["K01", "C01"], out)

    def test_changed_vs_git_ref(self):
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        g = ["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
        subprocess.run(g + ["init", "-q"], check=True, timeout=60)
        subprocess.run(g + ["add", "-A"], check=True, timeout=60)
        subprocess.run(g + ["commit", "-qm", "base"], check=True, timeout=60)
        src = (self.root / F).read_text(encoding="utf-8").replace("return 3", "return 3  # touched")
        (self.root / F).write_text(src, encoding="utf-8")
        code, out = self.run_r("--changed", "HEAD", "--list")
        self.assertEqual(self.listed(out), ["P01", "C01"], out)   # Box.size changed + P01 not unique

    def test_changed_every_occurrence_and_module_level(self):
        (self.root / "pkg" / "const.py").write_text("LIMIT = 3\n\n\ndef f():\n    return LIMIT\n", encoding="utf-8")
        spec = dict(SPEC, mutants=[
            {"id": "Q01", "name": "both x = a", "edits": [{"file": F, "old": "    x = a\n", "new": "    x = a + 0\n",
                                                           "count": 2}]},
            {"id": "Q02", "name": "module constant", "edits": [{"file": "pkg/const.py", "old": "LIMIT = 3", "new": "LIMIT = 4"}]},
            {"id": "Q03", "name": "box", "edits": [{"file": F, "func": "Box.size", "old": "return 3", "new": "return 4"}]},
            {"id": "Q04", "name": "new file", "edits": [{"file": "pkg/extra.py", "old": "A = 1", "new": "A = 2"}]},
        ])
        sp = self.write_spec(spec, "q.json")
        snap = self.d / "snap"
        self.run_r("--snapshot", str(snap), spec=sp)
        (self.root / "pkg" / "extra.py").write_text("A = 1\n", encoding="utf-8")
        src = (self.root / F).read_text(encoding="utf-8").replace("    x = a\n    return x - b",
                                                                   "    x = a\n    z = 1\n    return x - b")
        (self.root / F).write_text(src, encoding="utf-8")       # only sub (the 2nd occurrence) changed
        (self.root / "pkg" / "const.py").write_text("LIMIT = 3\n\n\ndef f():\n    return LIMIT + 0\n", encoding="utf-8")
        code, out = self.run_r("--changed", str(snap), "--list", spec=sp)
        self.assertEqual(self.listed(out), ["Q01", "Q02", "Q04"], out)

    # ---- merging, chunking, budget
    def test_out_merge_and_summary(self):
        self.run_r("--only", "K01", "--out", str(self.out))
        self.run_r("--only", "S01", "--out", str(self.out))
        self.assertEqual(sorted(self.results()), ["K01", "S01"])
        code, out = self.run_r("--out", str(self.out), "--summary")
        self.assertEqual(code, 1, out)                       # S01 survived
        self.assertIn("not run %d" % (N - 2), out)
        code, out = self.run_r("--out", str(self.out), "--summary", "--only", "K01")
        self.assertEqual(code, 0, out)
        code, out = self.run_r("--out", str(self.out), "--summary", "--only", "K01", "--strict")
        self.assertEqual(code, 0, out)
        code, out = self.run_r("--only", "K01", "--out", str(self.out))
        self.assertEqual(code, 0, out)                       # the gate of an --only call covers those mutants only

    def test_budget_resume_until_done(self):
        codes = []
        for _ in range(4):
            code, out = self.run_r("--only", "K01,A01,S01", "--out", str(self.out), "--budget", "0.01")
            codes.append(code)
        self.assertEqual(codes, [3, 3, 1, 1], out)           # one mutant per call, then the gate (S01 survived)
        self.assertEqual(sorted(self.results()), ["A01", "K01", "S01"])
        self.assertIn("0 of %d mutants selected" % N, out)   # 4th call: nothing left

    def test_budget_error_mutant_terminates(self):
        (self.root / "other").mkdir()
        (self.root / "other" / "x.py").write_text("V = 1\n", encoding="utf-8")
        spec = dict(SPEC, mutants=[{"id": "E01", "name": "outside copy", "edits": [
            {"file": "other/x.py", "old": "V = 1", "new": "V = 2"}]}] + SPEC["mutants"][:1] + SPEC["mutants"][3:4])
        sp = self.write_spec(spec, "e.json")
        codes = [self.run_r("--out", str(self.out), "--budget", "0.01", spec=sp)[0] for _ in range(4)]
        self.assertEqual(codes, [3, 3, 1, 1])                # an error result is not retried forever
        r = self.results()
        self.assertEqual({k: v["status"] for k, v in r.items()}, {"E01": "error", "K01": "killed", "A01": "killed"})
        code, out = self.run_r("--out", str(self.out), "--only", "E01", spec=sp)   # explicit rerun
        self.assertIn("E01      error", out)

    def test_budget_between_baselines(self):
        spec = dict(SPEC, mutants=[SPEC["mutants"][0], dict(SPEC["mutants"][1], id="S04",
                                                            test="python -m unittest tests.test_calc.T.test_sub_sign")])
        sp = self.write_spec(spec, "bb.json")
        code, out = self.run_r("--out", str(self.out), "--budget", "0.01", spec=sp)
        self.assertEqual(code, 3, out)                       # stops between baselines, keeps the first one
        self.assertIn("during the baselines", out)
        code, out = self.run_r("--out", str(self.out), "--budget", "0.01", spec=sp)
        self.assertIn("already passed", out)

    def test_budget_must_be_positive(self):
        code, out = self.run_r("--out", str(self.out), "--budget", "0")
        self.assertEqual(code, 2, out)

    def test_budget_uses_estimate(self):
        spec = dict(SPEC, mutants=[{"id": "W01", "name": "slow kill", "edits": [
            {"file": F, "func": "slow", "old": "    return n\n",
             "new": "    import time\n    time.sleep(2.0)\n    return n + 1\n"}]}] + SPEC["mutants"][:1])
        code, out = self.run_r("--out", str(self.out), "--budget", "3.5", spec=self.write_spec(spec, "w.json"))
        self.assertEqual(code, 3, out)                       # W01 (~2 s) done; K01 would not fit in what is left
        self.assertEqual(list(self.results()), ["W01"])

    def test_slice_before_resume(self):
        for s in ("0:3", "3:6", "6:"):
            self.run_r("--only", "K01,S01,A01,C01,I01,P01,T01", "--slice", s, "--resume", "--out", str(self.out))
        self.assertEqual(len(self.results()), 7, self.results().keys())

    def test_stale_after_code_change(self):
        self.run_r("--only", "K01,A01", "--out", str(self.out))
        code, out = self.run_r("--only", "K01,A01", "--out", str(self.out), "--summary", "--strict")
        self.assertEqual(code, 0, out)
        (self.root / F).write_text(CALC + "\n# changed\n", encoding="utf-8")
        code, out = self.run_r("--only", "K01,A01", "--out", str(self.out), "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("stale 2", out)
        code, out = self.run_r("--only", "K01,A01", "--out", str(self.out), "--summary", "--strict")
        self.assertEqual(code, 1, out)
        code, out = self.run_r("--only", "K01,A01", "--out", str(self.out), "--resume")
        self.assertIn("resume: 0 already fresh", out)        # code changed: nothing is fresh

    def test_stale_after_spec_change(self):
        self.run_r("--only", "K01", "--out", str(self.out))
        spec = json.loads(json.dumps(SPEC))
        spec["mutants"][0]["edits"][0]["new"] = "return x * b"
        sp = self.write_spec(spec, "k.json")
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--summary", spec=sp)
        self.assertIn("stale 1", out)
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--resume", spec=sp)
        self.assertIn("resume: 0 already fresh", out)        # the changed mutant runs again
        other = "python -m unittest discover -s tests -p test_calc.py"     # same tests, another command
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--summary", "--test", other, spec=sp)
        self.assertIn("stale 1", out)                        # the test command is part of the mutant
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--resume", "--test", other, spec=sp)
        self.assertIn("resume: 0 already fresh", out)

    def test_strict_needs_every_result_and_a_baseline(self):
        self.run_r("--only", "K01", "--out", str(self.out))
        code, out = self.run_r("--only", "K01,A01", "--out", str(self.out), "--summary", "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("not run: A01", out)
        out2 = self.d / "nobase.json"
        self.run_r("--only", "K01", "--out", str(out2), "--skip-baseline")
        code, out = self.run_r("--only", "K01", "--out", str(out2), "--summary")
        self.assertEqual(code, 0, out)
        code, out = self.run_r("--only", "K01", "--out", str(out2), "--summary", "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("unverified: K01", out)
        self.run_r("--only", "S01", "--out", str(self.out), "--skip-baseline")   # mixed: K01 verified, S01 not
        code, out = self.run_r("--only", "K01,S01", "--out", str(self.out), "--summary", "--strict")
        self.assertIn("unverified: S01)", out)
        code, out = self.run_r("--only", "K01", "--skip-baseline", "--strict")   # no --out: this run's gate
        self.assertEqual(code, 1, out)
        self.assertIn("unverified: K01", out)

    def test_timeout_retried_with_larger_timeout(self):
        self.run_r("--only", "T01", "--out", str(self.out), "--timeout", "2")
        code, out = self.run_r("--only", "T01", "--out", str(self.out), "--resume", "--timeout", "2", "--list")
        self.assertEqual(self.listed(out), [], out)          # same timeout: the result stands
        code, out = self.run_r("--only", "T01", "--out", str(self.out), "--resume", "--timeout", "3", "--list")
        self.assertEqual(self.listed(out), ["T01"], out)     # larger timeout: retried

    def test_timeout_must_be_positive(self):
        for t in ("0", "-1", "nan", "inf"):
            code, out = self.run_r("--only", "K01", "--timeout", t)
            self.assertEqual(code, 2, out)
            self.assertIn("positive", out)
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--budget", "nan")
        self.assertEqual(code, 2, out)

    def test_timeout_upper_bound(self):
        for args in (("--timeout", "1e19"), ("--timeout", "1000001"), ("--out", str(self.out), "--budget", "1e19")):
            code, out = self.run_r("--only", "K01", *args)
            self.assertEqual(code, 2, (args, out))            # not "int too large to convert to C rlim_t" in the run
            self.assertIn("at most 1e+06", out)
        code, out = self.run_r("--list", spec=self.write_spec(dict(SPEC, timeout=1e19), "huge.json"))
        self.assertEqual(code, 2, out)
        code, out = self.run_r("--list", "--timeout", "1e6")
        self.assertEqual(code, 0, out)
        self.assertLessEqual(mr.cpu_limit(1e12) + 5, 2 ** 31 - 1)  # the supervisor's hard limit fits any rlim_t
        code, out = self.run_r("--list", "--budget", "1e6", "--out", str(self.out))
        self.assertEqual(code, 0, out)                       # the bound itself is allowed
        legacy = self.d / "t.py"
        for text in ("TIMEOUT = True\n", "TIMEOUT = 10 ** 400\n", "TIMEOUT = 10 ** 4400\n", 'TIMEOUT = "30"\n',
                     "TIMEOUT = (10 ** 5000,)\n"):
            legacy.write_text('M = [("K01 a", [("pkg/calc.py", "x + b", "x - b")])]\n' + text, encoding="utf-8")
            code, out = self.run_r("--list", spec=legacy)
            self.assertEqual(code, 2, (text, out))
            self.assertIn("spec timeout must be a positive number of seconds (at most 1e+06", out)
            self.assertNotIn("unexpected", out)              # 10 ** 4400: no str() of a huge int in the message
            if "4400" in text:
                self.assertIn("got an integer of about 4401 digits", out)
            if "5000" in text:                               # repr refused inside a container
                self.assertIn("got <a tuple too large to show>", out)
        for bad in (True, "30"):
            code, out = self.run_r("--list", spec=self.write_spec(dict(SPEC, timeout=bad), "bad.json"))
            self.assertEqual(code, 2, (bad, out))

    def test_dump_spec_checks_values(self):
        legacy, dumped = self.d / "t.py", self.d / "dump.json"
        legacy.write_text('M = [("K01 a", [("pkg/calc.py", "x + b", "x - b")])]\nTIMEOUT = 2 * 10 ** 6\n', encoding="utf-8")
        for args in ((), ("--timeout", "30")):               # the dump writes the spec value, also under --timeout
            code, out = self.run_r("--dump-spec", str(dumped), *args, spec=legacy)
            self.assertEqual(code, 2, (args, out))
            self.assertIn("timeout must be a positive number of seconds", out)
            self.assertFalse(dumped.exists())
        legacy.write_text('M = [{"id": "K01", "test": 1e309, "edits": [{"file": "pkg/calc.py", "old": "x", "new": "y"}]}]\n',
                          encoding="utf-8")
        code, out = self.run_r("--dump-spec", str(dumped), spec=legacy)
        self.assertEqual(code, 2, out)                       # inf is not JSON: never written as Infinity
        self.assertIn("cannot write %s: Out of range float values are not JSON compliant" % dumped, out)
        self.assertNotIn("unexpected", out)
        self.assertFalse(dumped.exists())

    def test_legacy_huge_values_do_not_hang(self):
        legacy = self.d / "big.py"
        for tail, what in (("TIMEOUT = 10 ** 10 ** 9\n", "TIMEOUT cannot be read"),
                           ("TEST = \"a\"\nTEST *= 10 ** 8\n", "TEST cannot be read")):
            legacy.write_text('M = [("K01 a", [("pkg/calc.py", "x + b", "x - b")])]\n' + tail, encoding="utf-8")
            code, out = self.run_r("--list", spec=legacy, timeout=30)   # a process: a regression cannot hang the suite
            self.assertEqual(code, 2, (tail, out))
            self.assertIn(what, out)

    def test_out_and_tmp_outside_copied_paths(self):
        code, out = self.run_r("--only", "K01", "--out", str(self.root / "pkg" / "res.json"))
        self.assertEqual(code, 2, out)
        self.assertIn("inside the copied path", out)
        code, out = self.run_r("--only", "K01", "--copy", ".", "--tmp", str(self.root / "tmp"))
        self.assertEqual(code, 2, out)
        self.assertIn("inside the copied path", out)

    def test_summary_uses_recorded_test_and_copy(self):
        legacy = self.d / "legacy.py"
        legacy.write_text('W = "pkg/calc.py"\nM = [("K01 add", [(W, "return x + b", "return x - b")])]\n',
                          encoding="utf-8")
        code, out = self.run_r("--copy", "pkg", "--copy", "tests", "--test", SPEC["test"], "--out", str(self.out),
                               spec=legacy)
        self.assertEqual(code, 0, out)
        code, out = self.run_r("--out", str(self.out), "--summary", "--strict", spec=legacy)
        self.assertEqual(code, 0, out)                       # the run's --test/--copy come from the results file
        self.assertIn("recorded in", out)

    def test_nothing_selected(self):
        snap = self.d / "snap"
        self.run_r("--snapshot", str(snap))
        code, out = self.run_r("--changed", str(snap))
        self.assertEqual(code, 0, out)
        self.assertIn("nothing to run", out)
        self.assertNotIn("GATE: PASS", out)
        code, out = self.run_r("--changed", str(snap), "--strict")
        self.assertEqual(code, 1, out)

    # ---- baselines: the negative control of the setup
    def test_baseline_must_pass(self):
        (self.root / "tests" / "test_calc.py").write_text(TESTS.replace("calc.add(2, 3), 5", "calc.add(2, 3), 6"),
                                                          encoding="utf-8")
        code, out = self.run_r("--only", "K01")
        self.assertEqual(code, 2, out)
        self.assertIn("baseline tests FAIL", out)

    def test_baseline_must_run_tests(self):
        code, out = self.run_r("--only", "K01", "--test", "python -m unittest discover -s pkg")
        self.assertEqual(code, 2, out)
        self.assertIn("ran no tests", out)

    def test_baseline_rerun_after_change(self):
        code, out = self.run_r("--only", "K01", "--out", str(self.out))
        self.assertEqual(code, 0, out)
        (self.root / "tests" / "test_calc.py").write_text(TESTS.replace("calc.slow(1), 1", "calc.slow(1), 2"),
                                                          encoding="utf-8")
        code, out = self.run_r("--only", "K01", "--out", str(self.out))
        self.assertEqual(code, 2, out)                       # tests changed: the stored baseline is not reused
        self.assertIn("baseline tests FAIL", out)

    def test_baseline_per_test_command(self):
        code, out = self.run_r("--only", "K01", "--out", str(self.out))
        self.assertEqual(code, 0, out)
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--test", "python -m unittest discover -s pkg")
        self.assertEqual(code, 2, out)                       # a new command gets its own baseline
        self.assertIn("ran no tests", out)
        bad = dict(SPEC, mutants=[dict(SPEC["mutants"][1], id="S02", test="python -m unittest tests.test_calcx"),
                                  dict(SPEC["mutants"][1], id="S03", test="python -m unittest discover -s pkg"),
                                  dict(SPEC["mutants"][1], id="S04",
                                       test="python -m unittest tests.test_calc.T.test_sub_sign"),
                                  dict(SPEC["mutants"][0], id="S05",
                                       test="python -m unittest tests.test_calc.T.test_sub_sign")])
        sp = self.write_spec(bad, "per.json")
        for mid, why in (("S02", "baseline tests FAIL"), ("S03", "ran no tests")):
            code, out = self.run_r("--only", mid, spec=sp)
            self.assertEqual(code, 2, out)                   # a broken per-mutant command is a setup error, not a kill
            self.assertIn(why, out)
        code, out = self.run_r("--only", "S04,S05", spec=sp)
        self.assertEqual(code, 1, out)
        self.assertIn("S04      survived", out)              # a working per-mutant subset judges correctly
        self.assertIn("S05      survived", out)              # ...with its own command (test_add is not in it)

    def test_baseline_rerun_when_env_changes(self):
        self.run_r("--only", "K01", "--out", str(self.out))
        code, out = self.run_r("--only", "K01", "--out", str(self.out))
        self.assertIn("already passed", out)
        sp = self.write_spec(dict(SPEC, env={"MR_TEST_FLAG": "1"}), "env.json")
        code, out = self.run_r("--only", "K01", "--out", str(self.out), spec=sp)
        self.assertNotIn("already passed", out)              # another environment: the baseline runs again
        code, out = self.run_r("--only", "K01", "--out", str(self.out), "--resume")
        self.assertIn("resume: 0 already fresh", out)        # the spec env is part of the mutant fingerprint

    def _plain_import_project(self, env=None):
        (self.root / "tests2").mkdir()
        (self.root / "tests2" / "test_plain.py").write_text(
            "import unittest\nimport calc\n\n\nclass T(unittest.TestCase):\n"
            "    def test_add(self):\n        self.assertEqual(calc.add(2, 3), 5)\n", encoding="utf-8")
        spec = dict(SPEC, copy=["pkg", "tests2"], test="python -m unittest discover -s tests2",
                    mutants=SPEC["mutants"][:1])
        if env:
            spec["env"] = env
        return self.write_spec(spec, "plain.json")

    def test_outer_pythonpath_not_inherited(self):
        spec = self._plain_import_project()
        env = dict(os.environ, PYTHONPATH=str(self.root / "pkg"))     # points at the real, unmutated code
        code, out = self.run_r(spec=spec, env=env)
        self.assertEqual(code, 2, out)                       # the copy cannot import calc -> baseline fails
        self.assertIn("baseline tests FAIL", out)

    def test_env_tmp_substitution(self):
        spec = self._plain_import_project(env={"PYTHONPATH": "{tmp}/pkg"})
        code, out = self.run_r(spec=spec)
        self.assertEqual(code, 0, out)
        self.assertIn("K01      killed", out)                # the mutated copy was imported

    # ---- process handling
    def test_lock_one_runner_per_results_file(self):
        a = self.start_r("--only", "T01", "--timeout", "60", "--out", str(self.out), "--tmp", str(self.tmp))
        try:
            self.assertTrue(wait_for(lambda: self.marked("T01"), 60), "T01 never started")
            code, out = self.run_r("--only", "K01", "--out", str(self.out))
            self.assertEqual(code, 2, out)                   # one runner per results file
            self.assertIn("another mutation_runner", out)
        finally:
            self.stop_bg(a)
            for pid in self.marked("T01"):
                kill_pid(pid)

    @unittest.skipUnless(POSIX, "POSIX signals")
    def test_signals_kill_children(self):
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            shutil.rmtree(self.marks, ignore_errors=True)
            a = self.start_r("--only", "T01", "--timeout", "60", "--tmp", str(self.tmp))
            try:
                self.assertTrue(wait_for(lambda: self.marked("T01"), 60), "T01 never started")
                a.send_signal(sig)
                self.assertEqual(a.wait(timeout=20), 2, sig)
                self.assertIn("interrupted", self.bg_log.read_text())
                self.assertTrue(wait_for(lambda: not self.alive("T01"), 5), "children left after %s" % sig)
            finally:
                self.stop_bg(a)

    @unittest.skipUnless(POSIX, "POSIX supervisor")
    def test_orphans_end_when_runner_killed(self):
        a = self.start_r("--only", "T01,H01", "--jobs", "2", "--timeout", "60", "--tmp", str(self.tmp))
        try:
            self.assertTrue(wait_for(lambda: self.marked("T01") and self.marked("H01"), 60), "hangs never started")
            a.kill()                                         # SIGKILL: no handler can run
            a.wait(timeout=20)
            # busy and blocked hangs alike end with their runner (supervisor), long before any CPU limit
            self.assertTrue(wait_for(lambda: not self.alive("T01", "H01"), 5), "orphaned mutants still running")
        finally:
            self.stop_bg(a)

    @unittest.skipUnless(HAVE_PROC, "needs /proc")
    def test_supervisor_sees_a_runner_that_died_before_it_started(self):
        token = "mr-race-%d-%d" % (os.getpid(), int(time.time() * 1000))
        helper = self.d / "fake_runner.py"
        helper.write_text(textwrap.dedent("""\
            import os, subprocess, sys
            sys.path.insert(0, %r)
            import mutation_runner as mr
            code = "import time; time.sleep(600)  # %s"
            subprocess.Popen(mr._supervised([sys.executable, "-c", code], 10), start_new_session=True)
            os._exit(0)                                      # the 'runner' dies before the supervisor is up
        """ % (str(Path(RUNNER).parent), token)), encoding="utf-8")
        subprocess.run([sys.executable, str(helper)], timeout=60, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

        def with_token():
            out = []
            for d in os.listdir("/proc"):
                if d.isdigit():
                    try:
                        with open("/proc/%s/cmdline" % d, "rb") as f:
                            if token.encode() in f.read():
                                out.append(int(d))
                    except OSError:
                        pass
            return [pid for pid in out if pid_alive(pid)]
        time.sleep(3)
        left = with_token()
        for pid in left:
            kill_pid(pid)
        self.assertEqual(left, [], "the test outlived a runner that died before its supervisor started")

    @unittest.skipUnless(POSIX, "RLIMIT_CPU")
    def test_cpu_limit_is_timeout_not_kill(self):
        spec = dict(SPEC, mutants=[{"id": "X02", "name": "own CPU limit 1 s", "edits": [
            {"file": F, "func": "slow", "old": "    return n\n",
             "new": "    import resource\n    resource.setrlimit(resource.RLIMIT_CPU, (1, resource.getrlimit("
                    "resource.RLIMIT_CPU)[1]))\n    while True:\n        pass\n"}]},
            {"id": "X03", "name": "killed by SIGKILL", "edits": [
                {"file": F, "func": "slow", "old": "    return n\n",
                 "new": "    import os, signal\n    os.kill(os.getpid(), signal.SIGKILL)\n"}]}])
        code, out = self.run_r("--jobs", "2", "--timeout", "30", spec=self.write_spec(spec, "x.json"))
        self.assertIn("X02      timeout", out)              # SIGXCPU is a timeout, not a kill
        self.assertIn("CPU-time limit", out)
        self.assertIn("X03      error", out)                # an outside SIGKILL is not counted as caught

    def test_results_saved_after_each_mutant(self):
        a = self.start_r("--only", "K01,T01", "--jobs", "1", "--timeout", "90", "--out", str(self.out),
                         "--tmp", str(self.tmp))
        try:
            def has_k01():
                try:
                    return "K01" in self.results()
                except (OSError, ValueError):
                    return False
            self.assertTrue(wait_for(has_k01, 30), "K01 not saved while T01 still runs")   # not only at the end
            self.assertTrue(wait_for(lambda: self.marked("T01"), 30))
        finally:
            self.stop_bg(a)
            for pid in self.marked("T01"):
                kill_pid(pid)
        self.assertIn("K01", self.results())

    # ---- checks and spec formats
    def test_check_mode(self):
        code, out = self.run_r("--check", "--out", str(self.out))
        self.assertEqual(code, 1, out)
        self.assertIn("P01      pattern", out)
        self.assertIn("I01      invalid", out)
        self.assertFalse(self.out.exists())
        (self.root / "pkg" / "k.py").write_bytes("A = '한글'\n".encode("cp949"))
        sp = self.write_spec(dict(SPEC, mutants=[{"id": "U01", "name": "cp949", "edits": [
            {"file": "pkg/k.py", "old": "A", "new": "B"}]}]), "u.json")
        code, out = self.run_r("--check", spec=sp)
        self.assertEqual(code, 1, out)
        self.assertIn("cannot read", out)                    # reported, not a traceback

    def test_path_spellings_meet(self):
        sp = self.write_spec(dict(SPEC, mutants=[{"id": "X01", "name": "two spellings", "edits": [
            {"file": F, "old": "return x + b", "new": "return x - b"},
            {"file": "./" + F, "old": "def slow(n):", "new": "def slow(n):  # same file"}]}]), "x.json")
        code, out = self.run_r(spec=sp)
        self.assertIn("X01      killed", out)                # both edits land in the same file

    def test_legacy_py_spec_not_executed(self):
        legacy = self.d / "mutate_legacy.py"
        legacy.write_text(textwrap.dedent('''\
            import sys
            from pathlib import Path
            ROOT = Path(sys.argv[1])
            W, T = "pkg/calc.py", "tests/test_calc.py"
            OLD = ("return x "
                   "+ b")
            SUB = "return x %s b" % "-"
            NEW = "return "
            NEW += "x - b"
            M = [
             ("K01 add flipped", [(W, OLD, OLD.replace("+", "-"))]),
            ]
            M += [("S01 sub abs", [(W, SUB, "return abs(x - b)")])]
            M.append(("K02 add flipped again", [(W, OLD, NEW)]))
            if len(sys.argv) > 2:
                M = M[:1]
            raise SystemExit("this file must not be executed")
        '''), encoding="utf-8")
        code, out = self.run_r("--copy", "pkg", "--copy", "tests", "--test", "python -m unittest discover -s tests",
                               "--out", str(self.out), spec=legacy)
        self.assertEqual(code, 1, out)
        self.assertEqual({k: v["status"] for k, v in self.results().items()},
                         {"K01": "killed", "S01": "survived", "K02": "killed"})
        note = ("line 15: reading stops at 'if' -- lines 15-17 are %s (the tail rebinds M inside a block at line 16: "
                "ignored)" % NOT_READ)
        self.assertIn(note, out)
        meta = json.loads(self.out.read_text(encoding="utf-8"))["meta"]
        self.assertEqual(meta["spec_notes"], ["mutate_legacy.py " + note])   # the note is kept with the results
        dumped = self.d / "dump.json"
        self.run_r("--dump-spec", str(dumped), spec=legacy)
        self.assertEqual(json.loads(dumped.read_text(encoding="utf-8"))["mutants"][0],
                         {"id": "K01", "name": "add flipped", "edits": [{"file": F, "old": "return x + b",
                                                                          "new": "return x - b"}]})

    def test_legacy_errors_name_the_line(self):
        legacy = self.d / "alias.py"
        head = 'W = "pkg/calc.py"\nK = ("K01 a", [(W, "return x + b", "return x - b")])\n' \
               'S = ("S01 s", [(W, "return x - b", "return abs(x - b)")])\n'
        legacy.write_text(head + "M = [K]\nA = M\nA.append(S)\nA += [(\"K02 b\", K[1])]\n", encoding="utf-8")
        code, out = self.run_r("--list", spec=legacy)
        self.assertEqual(self.listed(out), ["K01", "S01", "K02"], out)    # aliases change the same list
        for tail, why in (("M = [K, S]\nlast = M.pop()\n", "line 5: unsupported Call at line 5"),
                          ("import os\nM = [K]\nM.append(os.sep)\n", "line 6: unsupported Attribute at line 6"),
                          ("M = [K, S]\nENV = {}\nENV.update(os.environ)\n", "line 6: unsupported Attribute at line 6"),
                          ("M = [K]\nMUTANTS = [m for m in M]\n", "line 5: unsupported ListComp at line 5")):
            legacy.write_text(head + tail, encoding="utf-8")
            code, out = self.run_r("--list", spec=legacy)
            self.assertEqual(code, 2, (tail, out))           # never a silently different list
            self.assertIn(why, out)

    def test_spec_errors(self):
        bad = self.write_spec({"mutants": [{"id": "X1", "edits": [{"file": F, "old": "a", "new": "b"}]},
                                           {"id": "X1", "edits": [{"file": F, "old": "c", "new": "d"}]}]}, "bad.json")
        code, out = self.run_r("--list", spec=bad)
        self.assertEqual(code, 2, out)
        self.assertIn("duplicate mutant ids: X1", out)
        code, out = self.run_r("--budget", "10")
        self.assertEqual(code, 2, out)                       # --budget without --out cannot resume
        self.assertIn("need --out", out)
        legacy = self.d / "bad_legacy.py"
        legacy.write_text('import os\nM = [("K01 x", [("pkg/calc.py", os.path.join("a"), "b")])]\n', encoding="utf-8")
        code, out = self.run_r("--list", spec=legacy)
        self.assertEqual(code, 2, out)
        self.assertIn("unsupported Attribute at line 2 (assignment at line 2)", out)   # where literal reading stopped
        legacy.write_text('M = [("K01 x", [("pkg/calc.py", "a", "b")])]\nM.sort(key=len)\n', encoding="utf-8")
        code, out = self.run_r("--list", spec=legacy)
        self.assertEqual(code, 2, out)                       # a change to M it cannot carry out is not ignored
        self.assertIn("line 2: unsupported name len at line 2", out)
        esc = self.write_spec({"mutants": [{"id": "X2", "edits": [{"file": "../x.py", "old": "a", "new": "b"}]}]}, "esc.json")
        code, out = self.run_r("--list", spec=esc)
        self.assertEqual(code, 2, out)
        self.assertIn("inside --root", out)
        self.out.write_text("{", encoding="utf-8")
        code, out = self.run_r("--out", str(self.out), "--summary")
        self.assertEqual(code, 2, out)                       # a broken results file is a setup error, not a gate fail
        self.assertIn("not readable JSON", out)


    def test_crash_exit_code_is_2(self):
        d = self.d / "res_dir.json"
        d.mkdir()                                            # --out is a directory: saving fails mid-run
        code, out = self.run_r("--only", "K01", "--out", str(d))
        self.assertEqual(code, 2, out)                       # a crash is a setup error, never 1 (= gate fail)
        self.assertIn("ERROR: unexpected", out)


NOT_READ = "runtime code: not read, and not checked except for direct changes to MUTANTS, M, COPY, TEST, TIMEOUT, ENV"
LEGACY_HEAD = ('W = "pkg/calc.py"\n'
               'K1 = {"id": "K01", "name": "a", "edits": [{"file": W, "old": "x + b", "new": "x - b"}]}\n'
               'K2 = {"id": "K02", "name": "b", "edits": [{"file": W, "old": "x - b", "new": "x + b"}]}\n'
               'M = [K1, K2]\n')                                # tails start at line 5


def exec_legacy(text):
    """What importing the legacy spec gives (the reference the reader must match)."""
    g = {"__name__": "legacy_spec"}
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):   # its print()s
        exec(compile(text, "spec.py", "exec"), g)
    muts = g.get("MUTANTS", g.get("M"))
    return {"mutants": list(muts), "copy": g.get("COPY"), "test": g.get("TEST"), "timeout": g.get("TIMEOUT"),
            "env": g.get("ENV")}


class LegacyReaderTest(unittest.TestCase):
    """_py_spec: the literal prefix of a legacy .py spec is carried out exactly; runtime code stops reading."""

    def read(self, tail, head=LEGACY_HEAD):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        (d / "spec.py").write_text(head + tail, encoding="utf-8")
        return mr._py_spec(d / "spec.py")

    def refused(self, tail, *parts):
        with self.assertRaises(mr.SpecError) as cm:
            self.read(tail)
        for part in parts:
            self.assertIn(part, str(cm.exception))

    def test_exact_in_place_and_sharing(self):
        tail = textwrap.dedent('''\
            A = M
            A.append({"id": "K03", "name": "c", "edits": []})
            A += [K1]
            MUTANTS = M[:]
            S, G = [M[1]], {"k": M[1]}
            M[0]["name"] = "y"
            G["k"]["edits"][0]["new"] = "z"
            M.pop()
            K = M[1]
            del K
            del M[2]["edits"]
            M[2].setdefault("test", "t")
            TIMEOUT = 60 * 3
            TIMEOUT += 20
            COPY = ["pkg"]
            COPY.append("tests")
            ENV = {"A": "1"}
            ENV.update(B="2")
            ENV["C"] = ENV.get("A") + "%d" % len(M)
        ''')
        got = self.read(tail)
        self.assertEqual(got.pop("notes"), [])
        self.assertEqual(got, exec_legacy(LEGACY_HEAD + tail))
        m = got["mutants"]
        self.assertEqual([x["id"] for x in m], ["K01", "K02", "K03", "K01"])   # A is M: += and append in place
        self.assertIs(m[3], m[0])                            # MUTANTS = M[:] shares the elements, as in Python
        self.assertEqual((m[0]["name"], m[1]["edits"][0]["new"]), ("y", "z"))
        self.assertEqual(m[2], {"id": "K03", "name": "c", "test": "t"})
        self.assertEqual((got["timeout"], got["copy"], got["env"]), (200, ["pkg", "tests"], {"A": "1", "B": "2", "C": "13"}))

    def test_exact_more_forms(self):
        tail = textwrap.dedent('''\
            MUTANTS = M = [K1]
            M.append(K2)
            M.extend([{"id": "K03", "name": "c", "edits": []}])
            M.insert(0, {"id": "K00", "name": "z", "edits": []})
            SET = {1}
            SET.add(2)
            SET.discard(1)
            SET.update({3, 4})
            SET.remove(4)
            L = W.split("/")
            TIMEOUT = +3
            TIMEOUT -= -2
            ENV = {"D": L[0], "N": "%d" % len(SET)}
            modules = ["pkg"]
            COPY = modules + ["tests"]
            print(len(M), "mutants")
            print(M, sep="-")
        ''')
        got = self.read(tail)
        self.assertEqual(got.pop("notes"), [])               # print(...) of readable values: reading goes on
        self.assertEqual(got, exec_legacy(LEGACY_HEAD + tail))
        self.assertEqual([x["id"] for x in got["mutants"]], ["K00", "K01", "K02", "K03"])   # MUTANTS = M = [...]: one list
        self.assertEqual((got["timeout"], got["env"], got["copy"]), (5, {"D": "pkg", "N": "2"}, ["pkg", "tests"]))

    def test_cp949_source_with_coding_line(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        text = '# -*- coding: cp949 -*-\nM = [("K01 \ud55c\uae00", [("pkg/calc.py", "a", "b")])]\n'
        (d / "spec.py").write_bytes(text.encode("cp949"))
        self.assertEqual(mr._py_spec(d / "spec.py")["mutants"][0][0], "K01 \ud55c\uae00")   # as Python reads it

    def test_del_name_only_unbinds(self):
        got = self.read("E = M[0]\ndel E\nMUTANTS = M\ndel M\n")
        self.assertEqual([x["name"] for x in got["mutants"]], ["a", "b"])

    def test_unknown_values_inert_or_error(self):
        got = self.read('import os\nR = os.path.join("a", "b")\nprint("x", file=os.devnull)\nX = "a"\nX += os.sep\n'
                        'os.getcwd()\nM.append(K1)\n')
        self.assertEqual((got["notes"], len(got["mutants"])), ([], 3))   # unknown names, never the list: reading goes on
        for tail, *parts in (("Y = [m for m in M]\n", "line 5: unsupported ListComp"),
                           ("str(M)\n", "line 5: unsupported Call"),
                           ('M[0]["edit"][0]["new"] = "x"\n', "line 5: unsupported Subscript at line 5 (KeyError: 'edit')"),
                           ('M[5]["name"] = "y"\n', "line 5: unsupported Subscript at line 5 (IndexError"),
                           ('del M[0]["nokey"]\n', "line 5: KeyError: 'nokey'"),
                           ("import os\nTIMEOUT = 60\nTIMEOUT *= int(os.environ.get(\"S\", \"1\"))\n",
                            "TIMEOUT cannot be read -- unsupported", "(augmented assignment at line 7)"),
                           ("import helpers\nK = (\"K01 a\", [K1])\nhelpers.add_edit(K)\n", "line 7: unsupported"),
                           ("import sys\nsys.modules[__name__].M.append(K1)\n", "line 6: modules is not supported"),
                           ("from os.path import join as len\nN = len(M)\n", "line 6: unsupported"),
                           ("import __main__\n", "line 5: 'import __main__' is not supported"),
                           ("from importlib import import_module\n", "line 5: 'import import_module' is not supported"),
                           ("X: M.append(K1) = 1\n", "line 5: the annotation cannot be read"),
                           ("A, B = M[:1]\n", "line 5: cannot unpack 1 values into 2 targets"),
                           ("import os\nM[0][\"name\"] = os.sep\n", "line 6: unsupported Attribute at line 6"),
                           ("import os\nY = [1]\nY += os.sep\n", "line 7: unsupported Attribute at line 7"),
                           ("import os\nM.append(os.sep)\n", "line 6"),
                           ("x = M.pop()\n", "line 5: unsupported Call"),
                           ("import os\nTEST = os.environ[\"T\"]\n", "TEST cannot be read -- unsupported", "line 6"),
                           ('globals()["M"] = M[:1]\n', "line 5: globals is not supported"),
                           ("from os import *\n", "line 5: 'import *' is not supported"),
                           ("import json as M\n", "no top-level literal MUTANTS (or M) list -- imported at line 5"),
                           ("global M\n", "line 5: 'global' is not supported"),
                           ("(M := M[:1])\n", "line 5: := is not supported"),
                           ("TEST = \"-\" * 20000000\n", "TEST cannot be read -- unsupported", "line 5")):
            with self.subTest(tail=tail):
                self.refused(tail, *parts)

    def test_stop_reading_at_runtime_code(self):
        note = "spec.py line %d: reading stops at '%s' -- lines %d-%d are " + NOT_READ + "%s"
        for tail, line, kind, last, extra in (
                ("for m in M:\n    print(m)\nX = 5\n", 5, "for", 7, ""),
                ("def f():\n    return len(M)\nf()\n", 7, "use of f()", 7, ""),
                ("def f(x=M):\n    return x\ng = f\n", 7, "use of f()", 7, ""),
                ("import os\ndef h(x=os.sep):\n    return x\nh()\n", 6, "def with default values it cannot read", 8, ""),
                ("def f(x: len(M)):\n    pass\n", 5, "def with annotations that run code", 6, ""),
                ("def deco(fn):\n    return fn\n@deco\ndef g():\n    pass\n", 7, "decorated def", 9, ""),
                ("class C:\n    X = len(M)\n", 5, "class", 6, ""),
                ("try:\n    import yaml\nexcept ImportError:\n    yaml = None\n", 5, "try", 8, ""),
                ("assert len(M) == 2\n", 5, "assert", 5, ""),
                ("A, *B = M\n", 5, "starred assignment", 5, ""),
                ("import os\nos.environ[\"X\"] = \"1\"\n", 6, "item or attribute assignment", 6, ""),
                ("import os\ndel os.environ[\"X\"]\n", 6, "item or attribute assignment", 6, ""),
                ("if True:\n    TIMEOUT = 5\n    M = M[:1]\n", 5, "if", 7,
                 " (the tail rebinds TIMEOUT inside a block at line 6, M inside a block at line 7: ignored)")):
            with self.subTest(tail=tail):
                got = self.read(tail)
                self.assertEqual(got["notes"], [note % (line, kind, line, last, extra)])
                self.assertEqual([x["id"] for x in got["mutants"]], ["K01", "K02"])   # nothing at or after the stop
                self.assertIsNone(got["timeout"])

    def test_tail_changes_are_errors(self):
        k3 = '{"id": "K03", "name": "c", "edits": []}'
        moved = "line %d: changes %s after reading stopped at line %d ('%s') -- move it above line %d or write the list out"
        for tail, msg in (                                   # D4-2-01 C1-C7 and the direct ways to change the spec
                ("for op in (\"*\", \"//\"):\n    M.append(%s)\n" % k3, moved % (6, "M", 5, "for", 5)),                # C1
                ("import sys\nif sys.platform == \"win32\":\n    W = W.replace(\"/\", \"x\")\nM += [K2]\n",
                 moved % (8, "M", 6, "if", 6)),                                                                      # C2
                ("def add(m):\n    M.append(m)\nadd(K2)\n", "line 6 (function add, defined at line 5): changes M -- it may "
                 "be called after reading stopped at line 7; move the change above line 7 or write the list out"),     # C4
                ("try:\n    import yaml\nexcept ImportError:\n    yaml = None\nM += [K2]\n", moved % (9, "M", 5, "try", 5)),
                ("assert len(M) == 2, \"ids\"\nM.append(K2)\n", moved % (6, "M", 5, "assert", 5)),                    # C6
                ("for m in M:\n    pass\nTIMEOUT = 600\n", moved % (7, "TIMEOUT", 5, "for", 5)),                       # C7
                ("for m in M:\n    for e in m[\"edits\"]:\n        e[\"new\"] = \"y\"\n", moved % (7, "e", 5, "for", 5)),
                ("for m in M:\n    m.update(test=\"t\")\n", moved % (6, "m", 5, "for", 5)),
                ("class C:\n    M.append(K1)\n", moved % (6, "M", 5, "class", 5)),
                ("def cut():\n    global M\n    M = M[:1]\ncut()\n", "line 6 (function cut, defined at line 5): changes M"),
                ("if True:\n    pass\nlist.append(M, K1)\n", moved % (7, "M", 5, "if", 5)),
                ("ENV = {}\nif True:\n    dict.update(ENV, A=\"1\")\n", moved % (7, "ENV", 6, "if", 6)),
                ("if True:\n    pass\nM[0].get(\"edits\").append(K1)\n", moved % (7, "M", 5, "if", 5)),
                ("if True:\n    pass\ndel M\n", moved % (7, "M", 5, "if", 5)),
                ("if True:\n    del M\n", moved % (6, "M", 5, "if", 5)),
                ("if True:\n    pass\nM = M + [K1]\n", moved % (7, "M", 5, "if", 5)),
                ("if True:\n    M += [K1]\n", moved % (6, "M", 5, "if", 5)),
                ("if True:\n    TEST += \" -v\"\n", moved % (6, "TEST", 5, "if", 5)),
                ("if True:\n    pass\n(M := [])\n", moved % (7, "M", 5, "if", 5))):                  # top-level walrus
            with self.subTest(tail=tail):
                self.refused(tail, msg)

    def test_tail_op_on_loop_variables(self):
        head = 'W = "pkg/calc.py"\nM = [("K01 a", [(W, "x + b", "x - b")]), ("K02 b", [(W, "x - b", "x + b")])]\n' \
               'if True:\n    pass\n'
        with self.assertRaises(mr.SpecError) as cm:          # edits names lists in the read data: += changes them
            self.read('for name, edits in M:\n    edits += [(W, "a", "b")]\n', head=head)
        self.assertIn("line 6: changes edits after reading stopped at line 3 ('if')", str(cm.exception))
        for tail in ('for name, edits in M:\n    name += "x"\n',                            # str values: rebinding only
                     'for name, edits in M:\n    for f, a, b in edits:\n        a += "!"\n',
                     'import os\nfor x in os.environ:\n    x += "y"\n',                   # not rooted: a note
                     'a, b = 0, 1\nfor name, edits in M[a:b]:\n    edits += [(W, "a", "b")]\n'):  # values unreadable
            with self.subTest(tail=tail):
                self.assertEqual(len(self.read(tail, head=head)["mutants"]), 2)
        self.refused('if True:\n    pass\nfor m in M:\n    for e in m["edits"]:\n        e |= {"new": "y"}\n',
                     "line 9: changes e after reading stopped at line 5 ('if')")       # dict values: |= changes them

    def test_tail_reads_copies_and_other_names_are_notes(self):
        head = 'TEST = "python -m unittest"\nENV = {"A": "1"}\nif True:\n    pass\n'                 # stop at line 7
        for tail in ('import sys\ncmd = TEST.split()\ncmd[0] = sys.executable\n', 'env = ENV.copy()\nenv["X"] = "1"\n',
                     'queue = M[:]\nqueue.pop()\n', 'cmd = TEST\ncmd += " -v"\n',
                     'for name, edits in M:\n    for f, old, new in edits:\n        old += "x"\n',     # op= on a str
                     'A = M\nA.append(K1)\n', 'for i, m in enumerate(M):\n    m["name"] = "y"\n'):  # not followed
            with self.subTest(tail=tail):
                got = self.read(head + tail)
                self.assertEqual(len(got["mutants"]), 2)
                self.assertIn("line 7: reading stops at 'if' -- lines 7-", got["notes"][0])
                self.assertIn("not checked except for direct changes to MUTANTS, M, COPY, TEST, TIMEOUT, ENV", got["notes"][0])

    def test_deep_tail_is_not_checked(self):
        got = self.read("if True:\n    pass\nY = " + "+".join(["1"] * 2000) + "\n")     # never read: no spec error
        self.assertIn("(tail not checked (nested too deeply))", got["notes"][0])
        self.assertEqual(len(got["mutants"]), 2)

    def test_print_fstring_and_order(self):
        tail = textwrap.dedent('''\
            import sys
            print(len(M), "mutants", file=sys.stderr, sep=" ", end="\\n", flush=True)
            print(f"{len(M)} mutants: {W!r:>24} {M[0]['id']!s} {W!a}")
            TEST = f"python -m unittest {W.split('/')[0]:>5}"
            i, M[i] = 1, K1
        ''')
        got = self.read(tail)
        self.assertEqual(got.pop("notes"), [])
        self.assertEqual(got, exec_legacy(LEGACY_HEAD + tail))
        self.assertEqual(([x["id"] for x in got["mutants"]], got["test"]), (["K01", "K01"], "python -m unittest   pkg"))

    def test_tail_like_p041_is_a_note(self):
        tail = textwrap.dedent('''\
            import sys
            if len(sys.argv) > 2 and sys.argv[2]:
                _a, _b = sys.argv[2].split(":")
                M = M[int(_a or 0):(int(_b) if _b else None)]
            res = []
            for name, edits in M:
                for e in edits:
                    cur = e["old"].upper()
                res.append((name, cur))
            for n, r in res:
                print("%-38s %s" % (n, r))
        ''')
        got = self.read(tail)
        self.assertEqual(got["notes"], ["spec.py line 6: reading stops at 'if' -- lines 6-15 are %s (the tail rebinds M "
                                        "inside a block at line 8: ignored)" % NOT_READ])
        self.assertEqual(len(got["mutants"]), 2)

    def test_main_guard_stops(self):
        got = self.read('if __name__ == "__main__":\n    M = M[:1]\n')        # a script runs it: runtime code
        self.assertEqual(len(got["mutants"]), 2)
        self.assertIn("line 5: reading stops at 'if'", got["notes"][0])
        self.refused('if __name__ == "__main__":\n    M.append(K1)\n', "line 6: changes M after reading stopped at line 5")

    def test_mutants_never_falls_back_to_m(self):
        self.refused('import json\nMUTANTS = json.loads("[]")\n', "no top-level literal MUTANTS (or M) list",
                     "unsupported name json at line 6 (imported at line 5) (assignment at line 6)")
        self.refused("MUTANTS = M[:1]\ndel MUTANTS\n", "deleted at line 6")

    def test_cycles_and_depth(self):
        got = self.read('A = []\nA.append(A)\nM[0]["edits"][0]["new"] = "x // b"\n')
        self.assertEqual(got["mutants"][0]["edits"][0]["new"], "x // b")           # a cycle elsewhere is harmless
        self.refused("X = " + "+".join(["1"] * 2000) + "\n", "nested too deeply to read")   # parse or evaluation stage
        with mock.patch.object(mr.ast, "parse", side_effect=RecursionError):
            self.refused("X = 1\n", "nested too deeply to read (cannot be parsed)")
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        (d / "spec.py").write_text(LEGACY_HEAD + 'Z = []\nZ.append(Z)\nM[0]["test"] = Z\n', encoding="utf-8")
        with self.assertRaises(mr.SpecError) as cm:
            mr.load_spec(d / "spec.py")                      # a mutant holding a cycle: SpecError, not a crash
        self.assertIn("spec.py: a mutant holds a value that is not plain data", str(cm.exception))


class UnitTest(unittest.TestCase):
    SRC = "import x\n\n@dec\ndef f():\n    a = 1\n    return a\n\n\nclass C:\n    def g(self):\n        a = 1\n        return a\n"

    def test_func_span_and_enclosing(self):
        lo, hi = mr.func_span(self.SRC, "f", "s")
        self.assertTrue(self.SRC[lo:hi].startswith("@dec\ndef f():"))
        self.assertTrue(self.SRC[lo:hi].endswith("return a\n"))
        lo, hi = mr.func_span(self.SRC, "C.g", "s")
        self.assertEqual(self.SRC[lo:hi], "    def g(self):\n        a = 1\n        return a\n")
        self.assertEqual(mr.func_span(self.SRC, "g", "s"), (lo, hi))      # unique simple name
        pos = self.SRC.index("return a\n", hi - 20)
        self.assertEqual(mr.enclosing_def(self.SRC, pos, pos + 8), "C.g")
        self.assertIsNone(mr.enclosing_def(self.SRC, 0, 8))
        with self.assertRaises(mr.PatternError):
            mr.func_span(self.SRC, "nope", "s")

    def test_apply_edit_counts(self):
        e = {"file": "s", "old": "    a = 1\n", "new": "    a = 2\n"}
        with self.assertRaises(mr.PatternError) as c:
            mr.apply_edit(self.SRC, e)
        self.assertIn("PATTERN x2", str(c.exception))
        out = mr.apply_edit(self.SRC, dict(e, func="C.g"))
        self.assertEqual(out.count("a = 2"), 1)
        self.assertEqual(mr.apply_edit(self.SRC, dict(e, count=2)).count("a = 2"), 2)
        with self.assertRaises(mr.PatternError):
            mr.apply_edit(self.SRC, dict(e, new=e["old"]))

    def test_form_feed_does_not_shift_spans(self):
        src = 'S = "a\\x0cb"\nT = """x\x0cy"""\n\ndef f():\n    return 1\n'
        lo, hi = mr.func_span(src, "f", "s")
        self.assertEqual(src[lo:hi], "def f():\n    return 1\n")

    def test_failing_tests_parsing(self):
        out = ("FAIL: test_a (m.T.test_a)\nERROR: test_b (m.T.test_b)\n"
               "ERROR: test_x (unittest.loader._FailedTest.test_x)\n"
               "ERROR: baseline tests FAIL on the unmutated copy (exit 1):\nERROR: could not open t.hwpx\n"
               "FAILED tests/test_x.py::TestC::test_c - AssertionError\n")
        self.assertEqual(mr.failing_tests(out), ["load error: test_x", "test_a", "test_b", "test_c"])

    def test_ran_no_tests(self):
        nested = ("....F\nAssertionError: 2 != 0 : mutation_runner output:\nRan 0 tests in 0.000s\n\nNO TESTS RAN\n"
                  "------\nRan 42 tests in 47.0s\n\nFAILED (failures=1)\n")
        self.assertFalse(mr.ran_no_tests(nested, 1))         # nested output in a failure message is not the run
        self.assertTrue(mr.ran_no_tests("\n------\nRan 0 tests in 0.000s\n\nNO TESTS RAN\n", 5))
        self.assertTrue(mr.ran_no_tests("Ran 0 tests in 0.000s\n\nOK\n", 0))       # Python <= 3.11 exits 0
        self.assertTrue(mr.ran_no_tests("collected 0 items\n\n== no tests ran in 0.01s ==\n", 5))   # pytest
        self.assertFalse(mr.ran_no_tests("collected 0 items / 1 error\n== 1 error in 0.1s ==\n", 2))
        self.assertFalse(mr.ran_no_tests("ImportError while loading conftest\n== no tests ran in 0.01s ==\n", 4))  # a kill

    def test_no_tests_pattern(self):
        for s in ("Ran 0 tests in 0.000s", "NO TESTS RAN", "collected 0 items\n", "== no tests ran in 0.01s =="):
            self.assertTrue(mr.NO_TESTS.search(s), s)
        for s in ("Ran 10 tests in 1s", "collected 0 items / 1 error", "collected 10 items"):
            self.assertFalse(mr.NO_TESTS.search(s), s)

    def test_split_cmd(self):
        cmd = 'python -m unittest discover -s "tools/doc writer/tests" -p "test_*.py"'
        want = ["python", "-m", "unittest", "discover", "-s", "tools/doc writer/tests", "-p", "test_*.py"]
        self.assertEqual(mr.split_cmd(cmd, windows=True), want)
        self.assertEqual(mr.split_cmd(cmd, windows=False), want)
        self.assertEqual(mr.split_cmd(r"python -m x C:\a\b", windows=True)[-1], r"C:\a\b")
        self.assertEqual(mr._argv("py -3 -m unittest")[:2], ["py", "-3"])      # the launcher keeps its arguments
        self.assertEqual(mr._argv("python -m unittest")[0], sys.executable)

    def test_stop_flag_blocks_new_children(self):
        mr._STOP.set()
        try:
            with self.assertRaises(RuntimeError):
                mr.run_cmd("python -c pass", Path(tempfile.gettempdir()), 5, {}, Path(tempfile.gettempdir()) / "x.log")
        finally:
            mr._STOP.clear()

    def test_save_out_retries(self):
        d = Path(tempfile.mkdtemp(prefix="mrsave_"))
        real, calls = os.replace, []

        def flaky(a, b):
            calls.append(1)
            if len(calls) < 3:
                raise PermissionError("in use")
            real(a, b)
        try:
            mr.os.replace = flaky
            mr.save_out(d / "r.json", {"meta": {}, "results": {}})
            self.assertEqual(len(calls), 3)
            self.assertTrue((d / "r.json").is_file())
            calls.clear()
            mr.os.replace = lambda a, b: (_ for _ in ()).throw(PermissionError("in use"))
            with self.assertRaises(PermissionError):
                mr.save_out(d / "r.json", {"meta": {}, "results": {}}, tries=2)
        finally:
            mr.os.replace = real
            shutil.rmtree(d, ignore_errors=True)

    @unittest.skipUnless(POSIX, "POSIX supervisor")
    def test_supervisor_passes_status_and_limits_cpu(self):
        import resource
        sup = [sys.executable, "-c", mr.SUPERVISOR]
        me = str(os.getpid())
        p = subprocess.run(sup + ["60", "30", me, sys.executable, "-c", "raise SystemExit(3)"], timeout=60)
        self.assertEqual(p.returncode, 3)
        p = subprocess.run(sup + ["60", "30", me, sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"],
                           timeout=60)
        self.assertEqual(p.returncode, -signal.SIGTERM)
        p = subprocess.run(sup + ["1", "30", me, sys.executable, "-c", "while True: pass"], timeout=60)
        self.assertEqual(p.returncode, -signal.SIGXCPU)      # the CPU-time limit
        p = subprocess.run(sup + ["60", "30", me, sys.executable, "-c", "while True: pass"], timeout=60,
                           preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (3, 3)))
        self.assertEqual(p.returncode, -signal.SIGXCPU)      # outside hard limit: SIGXCPU first, not the kernel's SIGKILL

    def test_paths_and_fingerprints(self):
        self.assertEqual(mr.norm_relpath("./pkg//calc.py", "f"), "pkg/calc.py")
        self.assertEqual(mr.norm_relpath("pkg\\calc.py", "f"), "pkg/calc.py")
        for bad in ("../x.py", "/abs/x.py", "C:/x.py", "pkg/../../x.py"):
            with self.assertRaises(mr.SpecError):
                mr.norm_relpath(bad, "f")
        self.assertEqual(mr.norm_copy(["tests", "./pkg", "pkg/sub", "tests"]), ["pkg", "tests"])
        d = Path(tempfile.mkdtemp(prefix="mrfp_"))
        try:
            for name, nl in (("lf", "\n"), ("crlf", "\r\n")):
                (d / name / "pkg").mkdir(parents=True)
                (d / name / "tests").mkdir()
                (d / name / "pkg" / "Zeta.py").write_bytes(CALC.replace("\n", nl).encode("utf-8"))
                (d / name / "pkg" / "alpha.py").write_bytes(b"A = 1" + nl.encode())
                (d / name / "tests" / "t.py").write_bytes(b"pass" + nl.encode())
            fp = mr.tree_fp(d / "lf", ["pkg", "tests"])
            self.assertEqual(mr.tree_fp(d / "lf", ["tests", "pkg"]), fp)            # --copy order does not matter
            self.assertEqual(mr.tree_fp(d / "crlf", ["pkg", "tests"]), fp)          # line endings do not matter
            m = {"edits": [{"file": "pkg/Zeta.py", "func": "add", "old": "    x = a\n", "new": "    x = a + 1\n"}]}
            self.assertIn("    x = a + 1\n", mr.apply_edits(d / "crlf", m)["pkg/Zeta.py"])   # "\n" pattern on CRLF
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
