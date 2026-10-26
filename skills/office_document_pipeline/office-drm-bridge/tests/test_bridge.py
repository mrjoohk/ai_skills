# -*- coding: utf-8 -*-
"""office-drm-bridge 시험 (Linux 에서 완결 — COM/Office 없이 가짜 실행기 사용).

    python3 -m unittest discover -s .claude/skills/office-drm-bridge/tests -v

시험은 세 층이다.
  1) 정상 경로 — 연산마다 만들어지는 명령줄이 정확하다
  2) 음성 대조 — 통제마다 거부되어야 하는 요청이 거부된다
  3) 변이 — 통제 하나를 일부러 무력화하면 대응하는 음성 시험이 실패한다(시험이 통제를 지키는지 확인)
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import bridge_core as core      # noqa: E402
import bridge_worker as worker  # noqa: E402
import bridge_client as client  # noqa: E402

SCRIPTS = {"read": "/s/read_office_doc.py", "write": "/s/write_office_doc.py"}
PY = "python"


def make_root():
    root = tempfile.mkdtemp(prefix="bridge_t_")
    for d in ("reference", "output_docs", "review_docs", ".git"):
        os.makedirs(os.path.join(root, d))
    core.ensure_dirs(root)
    for f in ("reference/doc.xlsx", "reference/tpl.docx", "reference/deck.pptx", "review_docs/plain.xlsx",
              "bridge/quarantine/x.xlsx", ".git/a.xlsx"):
        with open(os.path.join(root, f), "wb") as fh:
            fh.write(b"PK\x03\x04fake")
    return os.path.realpath(root)


class FakeRunner:
    """read/write 스크립트 흉내: --log/--dump/--out 파일을 만들고 상태 줄을 낸다."""
    def __init__(self, protect=True, rc=0, text=None):
        self.calls, self.protect, self.rc, self.text = [], protect, rc, text

    def __call__(self, cmd, timeout):
        assert isinstance(cmd, list), "셸 문자열이 아니라 리스트여야 한다"
        self.calls.append(cmd)
        opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in cmd if c.startswith("--") and "=" in c}
        for k in ("--log", "--dump"):
            if k in opts:
                with open(opts[k], "w", encoding="utf-8") as f:
                    f.write("# 문서 내용 SECRET-BODY\n")
        out = "source : x\nSECRET-BODY 문서 내용 줄\n"
        if "--out" in opts and self.rc == 0:
            with open(opts["--out"], "wb") as f:
                f.write((b"BMS DocuRay" if self.protect else b"PK\x03\x04") + b"....")
            out += "보호 확인: [보호됨] DocuRay 컨테이너\nDONE\n"
        if "--dump" in opts:
            out += "평문 덤프: %s\nDONE\n" % opts["--dump"]
        if self.rc:
            out += "FAILED: 가짜 오류\n"
        return (self.rc, self.text or out)


def req(op, path=None, args=None, rid=None, **kw):
    r = {"id": rid or "261016_120000_ab12", "op": op, "reason": "시험", "plan_ref": "수락한 계획"}
    if path:
        r["path"] = path
    if args is not None:
        r["args"] = args
    r.update(kw)
    return r


def raw(r):
    return json.dumps(r, ensure_ascii=False).encode("utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        self.root = make_root()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def validate(self, r, name_id=None):
        return core.validate_request(raw(r), name_id or r["id"], self.root)

    def run_req(self, r, runner=None, confirm=None):
        runner = runner or FakeRunner()
        res = core.handle_request(self.root, raw(r), r["id"], PY, SCRIPTS, runner, confirm)
        return res, runner


class TestNormal(Base):
    def test_read_command(self):
        res, rn = self.run_req(req("read", "reference/doc.xlsx", {"sheet": "1", "preview": 3}))
        self.assertEqual(res["status"], "ok")
        cmd = rn.calls[0]
        self.assertEqual(cmd[0], PY)
        self.assertEqual(cmd[1], SCRIPTS["read"])
        self.assertTrue(cmd[2].endswith("reference/doc.xlsx") or cmd[2].endswith("reference\\doc.xlsx"))
        self.assertIn("--sheet=1", cmd)
        self.assertIn("--preview=3", cmd)
        self.assertTrue(any(c.startswith("--log=") and "quarantine" in c for c in cmd))
        self.assertEqual(res["outputs"][0]["path"], "bridge/quarantine/261016_120000_ab12_read.md")

    def test_search_uses_equals_form(self):
        res, rn = self.run_req(req("search", "reference/doc.xlsx", {"pattern": "-헬기,Heli"}))
        self.assertIn("--pattern=-헬기,Heli", rn.calls[0])

    def test_log_and_dump_paths_are_distinct(self):
        """실측에서 발견한 결함: dump 의 --log 와 --dump 가 같은 파일이라 서로 덮어썼다."""
        _, rn = self.run_req(req("dump", "reference/doc.xlsx"))
        opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in rn.calls[0] if "=" in c and c.startswith("--")}
        self.assertNotEqual(os.path.normcase(opts["--log"]), os.path.normcase(opts["--dump"]))

    def test_no_two_outputs_share_a_path(self):
        for op, path, args in (("read", "reference/doc.xlsx", {}), ("search", "reference/doc.xlsx", {"pattern": "a"}),
                               ("dump", "reference/doc.xlsx", {}), ("protect", "review_docs/plain.xlsx", {})):
            res, _ = self.run_req(req(op, path, args, rid="261016_1200%02d_ab12" % len(op)))
            paths = [o["path"] for o in res["outputs"]]
            self.assertEqual(len(paths), len(set(paths)), op)

    def test_dump_outputs_in_quarantine(self):
        res, rn = self.run_req(req("dump", "reference/tpl.docx"))
        self.assertEqual(res["status"], "ok")
        paths = [o["path"] for o in res["outputs"]]
        self.assertIn("bridge/quarantine/261016_120000_ab12_dump.md", paths)
        self.assertTrue(all(p.startswith("bridge/quarantine/") for p in paths))

    def test_protect_default_out_and_signature(self):
        res, rn = self.run_req(req("protect", "review_docs/plain.xlsx"))
        self.assertEqual(res["status"], "ok")
        self.assertTrue(res["drm_signature"])
        self.assertIn("output_docs/plain_out.xlsx", [o["path"] for o in res["outputs"]])
        self.assertIn("--mode=protect", rn.calls[0])

    def test_replace_map_file_written_then_removed(self):
        res, rn = self.run_req(req("replace", "reference/tpl.docx", {"map": {"{{a}}": "가"}}))
        self.assertEqual(res["status"], "ok")
        m = [c for c in rn.calls[0] if c.startswith("--map=")][0][6:]
        self.assertFalse(os.path.exists(m), "치환표 임시 파일은 지워져야 한다")

    def test_fill_args(self):
        res, rn = self.run_req(req("fill", "reference/doc.xlsx",
                                   {"data": "a,b\n1,2\n", "sheet": "Input", "cell": "B3", "no_header": True}))
        self.assertEqual(res["status"], "ok")
        c = rn.calls[0]
        self.assertIn("--sheet=Input", c)
        self.assertIn("--cell=B3", c)
        self.assertIn("--no-header", c)
        self.assertNotIn("--overwrite", c)

    def test_stdout_tail_has_no_document_text(self):
        res, _ = self.run_req(req("read", "reference/doc.xlsx"))
        self.assertNotIn("SECRET-BODY", json.dumps(res, ensure_ascii=False))

    def test_purge_removes_only_that_id(self):
        self.run_req(req("dump", "reference/doc.xlsx"))
        self.run_req(req("dump", "reference/doc.xlsx", rid="261016_120001_cd34"))
        res, _ = self.run_req(req("purge", None, {"target_id": "261016_120000_ab12"}, rid="261016_120002_ef56"))
        self.assertEqual(res["status"], "ok")
        left = os.listdir(os.path.join(self.root, "bridge", "quarantine"))
        self.assertFalse([n for n in left if n.startswith("261016_120000_ab12_")])
        self.assertTrue([n for n in left if n.startswith("261016_120001_cd34_")])
        self.assertIn("x.xlsx", left)           # id 로 시작하지 않는 파일은 그대로

    def test_purge_old(self):
        p = os.path.join(self.root, "bridge", "quarantine", "old_dump.md")
        open(p, "w").write("x")
        old = time.time() - 48 * 3600
        os.utime(p, (old, old))
        gone = core.purge_old(self.root, 24)
        self.assertEqual(gone, ["bridge/quarantine/old_dump.md"])

    def test_runner_failure_is_error_status(self):
        res, _ = self.run_req(req("read", "reference/doc.xlsx"), FakeRunner(rc=1))
        self.assertEqual(res["status"], "error")
        self.assertIn("FAILED", res["stdout_tail"])


class TestNegative(Base):
    """통제 C1~C6: 거부되어야 하는 요청."""
    def rejects(self, r, name_id=None, contains=None):
        with self.assertRaises(core.Reject) as cm:
            self.validate(r, name_id)
        if contains:
            self.assertIn(contains, str(cm.exception))

    def test_path_escape_dotdot(self):
        self.rejects(req("read", "../outside.xlsx"), contains="저장소 밖")

    def test_path_escape_absolute(self):
        self.rejects(req("read", "/etc/passwd.xlsx"), contains="저장소 밖")

    def test_path_escape_symlink(self):
        out = tempfile.mkdtemp(prefix="bridge_out_")
        try:
            open(os.path.join(out, "secret.xlsx"), "wb").write(b"PK")
            try:
                os.symlink(out, os.path.join(self.root, "reference", "link"))
            except OSError as e:                     # Windows: 심볼릭 링크 권한(개발자 모드·관리자) 없음 — WinError 1314
                self.skipTest("심볼릭 링크를 만들 권한이 없다: %s" % e)
            self.rejects(req("read", "reference/link/secret.xlsx"), contains="저장소 밖")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_extension_not_office(self):
        open(os.path.join(self.root, "reference", "a.txt"), "w").write("x")
        self.rejects(req("read", "reference/a.txt"), contains="확장자")

    def test_blocked_source_dirs(self):
        self.rejects(req("read", ".git/a.xlsx"), contains="입력")
        self.rejects(req("read", "bridge/quarantine/x.xlsx"), contains="입력")

    def test_missing_file(self):
        self.rejects(req("read", "reference/none.xlsx"), contains="없다")

    def test_unknown_op_and_keys(self):
        self.rejects(req("exec", "reference/doc.xlsx"), contains="연산")
        self.rejects(req("read", "reference/doc.xlsx", cmd="calc.exe"), contains="알 수 없는 키")

    def test_unknown_and_dangerous_args(self):
        self.rejects(req("protect", "review_docs/plain.xlsx", {"overwrite": True}), contains="허용하지 않는 인자")
        self.rejects(req("protect", "review_docs/plain.xlsx", {"no_backup": True}), contains="허용하지 않는 인자")
        self.rejects(req("read", "reference/doc.xlsx", {"dump": "x.md"}), contains="허용하지 않는 인자")

    def test_arg_types_and_ranges(self):
        self.rejects(req("read", "reference/doc.xlsx", {"preview": "3"}))
        self.rejects(req("read", "reference/doc.xlsx", {"preview": True}))
        self.rejects(req("read", "reference/doc.xlsx", {"max_rows": 10**9}))
        self.rejects(req("fill", "reference/doc.xlsx", {"data": "a\n1", "cell": "A1; calc"}))
        self.rejects(req("search", "reference/doc.xlsx", {}), contains="필수")

    def test_control_chars(self):
        self.rejects(req("search", "reference/doc.xlsx", {"pattern": "a\nb"}))
        self.rejects(req("read", "reference/doc.xlsx", {"sheet": "a\x00b"}))

    def test_id_rules(self):
        self.rejects(req("read", "reference/doc.xlsx", rid="../../evil"), name_id="../../evil")
        r = req("read", "reference/doc.xlsx")
        self.rejects(r, name_id="261016_999999_ffff", contains="파일명")

    def test_reason_and_plan_ref_required(self):
        r = req("read", "reference/doc.xlsx")
        del r["plan_ref"]
        self.rejects(r)
        r = req("read", "reference/doc.xlsx")
        r["reason"] = ""
        self.rejects(r)

    def test_size_limits(self):
        r = req("fill", "reference/doc.xlsx", {"data": "x" * (core.MAX_BODY_CHARS + 1)})
        self.rejects(r)
        with self.assertRaises(core.Reject):
            core.validate_request(b"{" + b" " * (core.MAX_REQ_BYTES + 1) + b"}", "261016_120000_ab12", self.root)

    def test_not_json(self):
        with self.assertRaises(core.Reject):
            core.validate_request(b"{not json", "261016_120000_ab12", self.root)
        with self.assertRaises(core.Reject):
            core.validate_request(b"[1,2]", "261016_120000_ab12", self.root)

    def test_out_restrictions(self):
        src = "review_docs/plain.xlsx"
        self.rejects(req("protect", src, {"out": "reference/evil_out.xlsx"}), contains="아래에만")
        self.rejects(req("protect", src, {"out": "../evil.xlsx"}), contains="저장소 밖")
        self.rejects(req("protect", src, {"out": "output_docs/x.exe"}), contains="확장자")
        self.rejects(req("protect", src, {"out": "output_docs/nodir/x.xlsx"}), contains="폴더")
        self.rejects(req("protect", src, {"out": "review_docs/plain.xlsx"}), contains="원본")
        open(os.path.join(self.root, "output_docs", "taken.xlsx"), "wb").write(b"x")
        self.rejects(req("protect", src, {"out": "output_docs/taken.xlsx"}), contains="이미 있다")

    def test_purge_rules(self):
        self.rejects(req("purge", "reference/doc.xlsx", {"target_id": "261016_120000_ab12"}), contains="path")
        self.rejects(req("purge", None, {"target_id": "*"}))
        self.rejects(req("purge", None, {"target_id": "../x"}))

    def test_rejected_never_calls_runner(self):
        rn = FakeRunner()
        res, _ = self.run_req(req("read", "../x.xlsx"), rn)
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(rn.calls, [])

    def test_confirm_denied_never_calls_runner(self):
        rn = FakeRunner()
        res, _ = self.run_req(req("dump", "reference/doc.xlsx"), rn, confirm=lambda r, p: False)
        self.assertEqual(res["status"], "denied")
        self.assertEqual(rn.calls, [])

    def test_unprotected_output_is_error(self):
        res, _ = self.run_req(req("protect", "review_docs/plain.xlsx"), FakeRunner(protect=False))
        self.assertEqual(res["status"], "error")
        self.assertFalse(res["drm_signature"])

    def test_runner_exception_does_not_escape(self):
        def boom(cmd, timeout):
            raise OSError("boom")
        res, _ = self.run_req(req("read", "reference/doc.xlsx"), boom)
        self.assertEqual(res["status"], "error")


class TestWorker(Base):
    def put(self, r, name=None):
        name = name or r["id"] + ".json"
        with open(os.path.join(self.root, "bridge", "inbox", name), "wb") as f:
            f.write(raw(r))
        return name

    def test_process_moves_request_and_writes_result_and_audit(self):
        name = self.put(req("search", "reference/doc.xlsx", {"pattern": "a"}))
        res = worker.process_one(self.root, name, PY, None, FakeRunner(), SCRIPTS)
        self.assertEqual(res["status"], "ok")
        self.assertFalse(os.path.exists(os.path.join(self.root, "bridge", "inbox", name)))
        self.assertTrue(os.path.exists(os.path.join(self.root, "bridge", "done", name)))
        out = json.load(open(os.path.join(self.root, "bridge", "outbox", name), encoding="utf-8"))
        self.assertEqual(out["status"], "ok")
        line = json.loads(open(os.path.join(self.root, "bridge", "audit.jsonl"), encoding="utf-8").readline())
        self.assertEqual(line["status"], "ok")
        self.assertEqual(len(line["req_sha256"]), 64)

    def test_replay_of_same_id_rejected_and_result_not_overwritten(self):
        r = req("search", "reference/doc.xlsx", {"pattern": "a"})
        worker.process_one(self.root, self.put(r), PY, None, FakeRunner(), SCRIPTS)
        before = open(os.path.join(self.root, "bridge", "outbox", r["id"] + ".json"), "rb").read()
        rn = FakeRunner()
        res = worker.process_one(self.root, self.put(r), PY, None, rn, SCRIPTS)
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(rn.calls, [])
        after = open(os.path.join(self.root, "bridge", "outbox", r["id"] + ".json"), "rb").read()
        self.assertEqual(before, after)

    def test_bad_filename(self):
        name = self.put(req("read", "reference/doc.xlsx"), name="evil name.json")
        res = worker.process_one(self.root, name, PY, None, FakeRunner(), SCRIPTS)
        self.assertEqual(res["status"], "rejected")
        self.assertTrue(res["id"].startswith("invalid_"))

    def test_tmp_files_ignored_by_listing(self):
        open(os.path.join(self.root, "bridge", "inbox", "x.json.tmp"), "w").write("{")
        names = [n for n in os.listdir(os.path.join(self.root, "bridge", "inbox")) if n.endswith(".json")]
        self.assertEqual(names, [])


class TestHeartbeat(Base):
    def hb(self, ts, seq):
        core.write_json_atomic(os.path.join(self.root, "bridge", "worker_alive.json"),
                               {"pid": 1, "seq": seq, "ts": ts, "mode": "auto", "version": "1"})

    def test_no_file_is_down(self):
        self.assertFalse(client.worker_alive(self.root, wait=0)[0])

    def test_fresh_is_alive(self):
        self.hb(time.time(), 1)
        self.assertTrue(client.worker_alive(self.root, wait=0)[0])

    def test_stale_and_frozen_is_down(self):
        self.hb(time.time() - 300, 5)
        self.assertFalse(client.worker_alive(self.root, wait=0)[0])

    def test_clock_skew_but_seq_moving_is_alive(self):
        self.hb(time.time() - 300, 5)
        orig = time.sleep
        time.sleep = lambda s: self.hb(time.time() - 300, 6)      # 시계는 어긋났지만 seq 가 움직인다
        try:
            self.assertTrue(client.worker_alive(self.root, wait=1)[0])
        finally:
            time.sleep = orig

    def test_audit_has_path(self):
        name = req("read", "reference/doc.xlsx")["id"] + ".json"
        open(os.path.join(self.root, "bridge", "inbox", name), "wb").write(raw(req("read", "reference/doc.xlsx")))
        worker.process_one(self.root, name, PY, None, FakeRunner(), SCRIPTS)
        line = json.loads(open(os.path.join(self.root, "bridge", "audit.jsonl"), encoding="utf-8").readline())
        self.assertEqual(line["path"], "reference/doc.xlsx")


class TestMutations(unittest.TestCase):
    """통제를 일부러 무력화하면 대응 시험이 실패해야 한다."""
    def run_case(self, case_cls, name):
        suite = unittest.TestSuite([case_cls(name)])
        res = unittest.TextTestRunner(stream=open(os.devnull, "w", encoding="utf-8"), verbosity=0).run(suite)
        return res.wasSuccessful()

    def mutate(self, attr, new, case_cls, name):
        old = getattr(core, attr)
        self.assertTrue(self.run_case(case_cls, name), "변이 전에는 통과해야 한다: " + name)
        setattr(core, attr, new)
        try:
            self.assertFalse(self.run_case(case_cls, name), "통제 %s 를 끄면 %s 가 실패해야 한다" % (attr, name))
        finally:
            setattr(core, attr, old)

    def test_M1_path_inside_check(self):
        self.mutate("resolve_inside", lambda root, p: os.path.realpath(p if os.path.isabs(p) else os.path.join(root, p)),
                    TestNegative, "test_path_escape_dotdot")

    def test_M2_extension_check(self):
        self.mutate("OFFICE_EXT", {".xlsx", ".txt"}, TestNegative, "test_extension_not_office")
        self.assertTrue(True)

    def test_M3_overwrite_exposed(self):
        old = dict(core.ARGS["protect"])
        self.assertTrue(self.run_case(TestNegative, "test_unknown_and_dangerous_args"))
        core.ARGS["protect"] = dict(old, overwrite=("bool",), no_backup=("bool",))
        try:
            self.assertFalse(self.run_case(TestNegative, "test_unknown_and_dangerous_args"))
        finally:
            core.ARGS["protect"] = old

    def test_M4_out_dirs(self):
        self.mutate("OUT_DIRS", ("output_docs", "review_docs", "reference"), TestNegative, "test_out_restrictions")

    def test_M5_blocked_dirs(self):
        self.mutate("BLOCKED_SRC_DIRS", (), TestNegative, "test_blocked_source_dirs")

    def test_M6_id_regex(self):
        import re
        self.mutate("ID_RE", re.compile(r".*"), TestNegative, "test_id_rules")

    def test_M7_stdout_filter(self):
        self.mutate("safe_tail", lambda t: t, TestNormal, "test_stdout_tail_has_no_document_text")

    def test_M9_log_dump_collision(self):
        """dump 로그 이름을 dump 와 같게 되돌리면 시험이 잡아야 한다."""
        src = open(os.path.join(HERE, "..", "scripts", "bridge_core.py"), encoding="utf-8").read()
        self.assertIn('"dumplog" if op == "dump" else op', src)
        mutated = src.replace('"dumplog" if op == "dump" else op', 'op')
        ns = {"__name__": "mut_core"}
        exec(compile(mutated, "mut_core", "exec"), ns)
        saved = TestNormal.run_req
        class M(Base):
            def runTest(self):
                _, rn = self.run_req(req("dump", "reference/doc.xlsx"))
        # run_req 가 변이 모듈을 쓰도록 handle_request 를 교체
        import types
        mod = types.SimpleNamespace(**ns)
        class T(TestNormal):
            def run_req(self, r, runner=None, confirm=None):
                runner = runner or FakeRunner()
                return mod.handle_request(self.root, raw(r), r["id"], PY, SCRIPTS, runner, confirm), runner
        self.assertFalse(self.run_case(T, "test_log_and_dump_paths_are_distinct"))

    def test_M8_signature_check(self):
        self.mutate("drm_signature", lambda p: True, TestNegative, "test_unprotected_output_is_error")


if __name__ == "__main__":
    unittest.main(verbosity=2)
