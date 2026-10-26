# -*- coding: utf-8 -*-
"""hwpx 백엔드 시험 (Linux 에서 완결 — 한/글·COM 없이 가짜 실행기 사용).

    python3 -m unittest discover -s .claude/skills/office-drm-bridge/tests -v

층: 1) 정상 경로  2) 음성 대조  3) 변이(통제를 끄면 대응 시험이 실패한다)
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
sys.path.insert(0, HERE)
import bridge_core as core      # noqa: E402
import bridge_worker as worker  # noqa: E402
from test_bridge import make_root as make_office_root, req, raw  # noqa: E402

PY = "python"
RID = "261016_120000_ab12"
RID2 = "261016_120001_cd34"
RID3 = "261016_120002_ef56"


def make_root():
    root = make_office_root()
    for f in ("reference/form.hwpx", "reference/old.hwp", "reference/other.hwpx", "review_docs/plain.hwpx",
              ".git/a.hwpx", "bridge/quarantine/x.hwpx"):
        with open(os.path.join(root, f), "wb") as fh:
            fh.write(b"BMS DocuRay....")
    return root


class FakeHwpx:
    """hwpx_drm.py 흉내: --md-dir/--log/--out 파일을 만들고 상태 줄과 (새면 안 되는) 본문 줄을 낸다."""
    def __init__(self, protect=True, rc=0, make_out=True):
        self.calls, self.protect, self.rc, self.make_out = [], protect, rc, make_out
        self.timeouts = []

    def __call__(self, cmd, timeout):
        assert isinstance(cmd, list)
        self.calls.append(cmd)
        self.timeouts.append(timeout)
        op, src = cmd[2], cmd[3]
        opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in cmd if c.startswith("--") and "=" in c}
        if "--log" in opts:
            with open(opts["--log"], "w", encoding="utf-8") as f:
                f.write("# hwpx-drm 실행 기록\n")
        if "--md-dir" in opts:
            os.makedirs(opts["--md-dir"], exist_ok=True)
            stem = os.path.splitext(os.path.basename(src))[0]
            with open(os.path.join(opts["--md-dir"], "%s.%s.md" % (stem, op)), "w", encoding="utf-8") as f:
                f.write("# 문서 본문 SECRET-BODY\n")
        out = "SECRET-BODY 한/글 본문 줄\n표 3개 · 격자 불일치 0\n개요 문단 2개\n"
        if "--out" in opts and self.make_out and self.rc in (0, 1):
            with open(opts["--out"], "wb") as f:
                f.write((b"BMS DocuRay" if self.protect else b"PK\x03\x04") + b"....")
            out += "저장 %s · 선두 DOCURAY · 다시 열기 True\n" % opts["--out"]
        if self.rc:
            out += "중단(종료코드 %d): 가짜 오류\n" % self.rc
        return (self.rc, out)


class Base(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.scripts_dir = tempfile.mkdtemp(prefix="hwpx_scripts_")
        with open(os.path.join(self.scripts_dir, "hwpx_drm.py"), "w") as f:
            f.write("# fake\n")
        self.scripts = {"read": "/s/r.py", "write": "/s/w.py", "hwpx": os.path.join(self.scripts_dir, "hwpx_drm.py")}

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.scripts_dir, ignore_errors=True)

    def run_req(self, r, runner=None, confirm=None):
        runner = runner or FakeHwpx()
        res = core.handle_request(self.root, raw(r), r["id"], PY, self.scripts, runner, confirm)
        return res, runner

    def via_worker(self, r, runner=None):
        runner = runner or FakeHwpx()
        name = r["id"] + ".json"
        with open(os.path.join(self.root, "bridge", "inbox", name), "wb") as f:
            f.write(raw(r))
        return worker.process_one(self.root, name, PY, None, runner, self.scripts), runner

    def do_search(self, pattern="{{과제명}},○○○", rid=RID, path="reference/form.hwpx"):
        res, _ = self.via_worker(req("search", path, {"pattern": pattern}, rid=rid))
        self.assertEqual(res["status"], "ok", res)
        return rid

    def rejects(self, r, contains=None):
        with self.assertRaises(core.Reject) as cm:
            core.validate_request(raw(r), r["id"], self.root)
        if contains:
            self.assertIn(contains, str(cm.exception))


class TestHwpxNormal(Base):
    def test_inspect_command(self):
        res, rn = self.run_req(req("inspect", "reference/form.hwpx"))
        self.assertEqual(res["status"], "ok", res)
        cmd = rn.calls[0]
        self.assertEqual(cmd[:3], [PY, self.scripts["hwpx"], "inspect"])
        self.assertTrue(cmd[3].replace("\\", "/").endswith("reference/form.hwpx"))
        self.assertIn("--timeout=%d" % core.HWPX_COM_TIMEOUT, cmd)
        self.assertTrue(any(c.startswith("--md-dir=") and "%s_md" % RID in c for c in cmd))
        self.assertTrue(any(c.startswith("--log=") and "quarantine" in c for c in cmd))
        self.assertNotIn("--json", cmd)                    # --json 은 본문(개요 글)을 표준출력으로 낸다
        paths = [o["path"] for o in res["outputs"]]
        self.assertIn("bridge/quarantine/%s_md/form.inspect.md" % RID, paths)
        self.assertEqual(res["exit_meaning"], "성공")
        self.assertEqual(len(res["src_sha256"]), 64)
        self.assertEqual(rn.timeouts[0], core.HWPX_TIMEOUT_SEC)

    def test_stdout_tail_has_status_only(self):
        res, _ = self.run_req(req("inspect", "reference/form.hwpx"))
        text = json.dumps(res, ensure_ascii=False)
        self.assertNotIn("SECRET-BODY", text)
        self.assertIn("격자 불일치 0", res["stdout_tail"])

    def test_search_tables_verify_fields_outline(self):
        res, rn = self.run_req(req("search", "reference/form.hwpx", {"pattern": "-헬기,Heli"}))
        self.assertIn("--pattern=-헬기,Heli", rn.calls[0])
        res, rn = self.run_req(req("tables", "reference/form.hwpx", {"table": "s0.t3"}, rid=RID2))
        self.assertIn("--table=s0.t3", rn.calls[0])
        res, rn = self.run_req(req("verify", "reference/form.hwpx", rid=RID3))
        self.assertFalse([c for c in rn.calls[0] if c.startswith("--md-dir")])
        self.assertEqual(rn.calls[0][2], "verify")
        for op, rid in (("fields", "261016_120003_0001"), ("outline", "261016_120004_0002")):
            res, rn = self.run_req(req(op, "reference/form.hwpx", rid=rid))
            self.assertEqual(rn.calls[0][2], op)
            self.assertEqual(res["status"], "ok")

    def test_fill_default_out_map_file_and_log(self):
        seen = {}

        class R(FakeHwpx):
            def __call__(s, cmd, timeout):
                m = [c for c in cmd if c.startswith("--map=")][0][6:]
                seen["map"] = json.load(open(m, encoding="utf-8"))
                seen["map_path"] = m
                return FakeHwpx.__call__(s, cmd, timeout)
        res, rn = self.run_req(req("fill", "reference/form.hwpx", {"map": {"과제명": "첫 줄\n둘째 줄"}}), R())
        self.assertEqual(res["status"], "ok", res)
        self.assertEqual(seen["map"], {"과제명": "첫 줄\n둘째 줄"})
        self.assertFalse(os.path.exists(seen["map_path"]))                     # 값 파일은 지워진다
        cmd = rn.calls[0]
        out = [c for c in cmd if c.startswith("--out=")][0][6:]
        self.assertTrue(out.replace("\\", "/").endswith("output_docs/form_out.hwpx"))
        self.assertTrue(res["drm_signature"])
        self.assertTrue(any(c.startswith("--log=") and "outbox" in c for c in cmd))
        for bad in ("--force", "--overwrite", "--allow-running", "--json"):
            self.assertNotIn(bad, cmd)

    def test_hwp_source_defaults_to_hwpx_output(self):
        res, rn = self.run_req(req("fill", "reference/old.hwp", {"map": {"a": "b"}}))
        out = [c for c in rn.calls[0] if c.startswith("--out=")][0][6:]
        self.assertTrue(out.replace("\\", "/").endswith("output_docs/old_out.hwpx"), out)

    def test_replace_after_search_via_worker(self):
        sid = self.do_search()
        res, rn = self.via_worker(req("replace", "reference/form.hwpx",
                                      {"map": {"{{과제명}}": "OOO"}, "search_id": sid}, rid=RID2))
        self.assertEqual(res["status"], "ok", res)
        self.assertEqual(rn.calls[0][2], "replace")
        self.assertNotIn("--search-id", " ".join(rn.calls[0]))              # 선행조건은 명령줄에 나가지 않는다

    def test_exit_codes_are_explained(self):
        for rc, word in ((1, "검증"), (2, "사전조건"), (3, "평문"), (4, "열기"), (5, "시간 초과"), (6, "COM")):
            res, _ = self.run_req(req("verify", "reference/form.hwpx", rid="261016_1200%02d_00%02x" % (rc, rc)),
                                  FakeHwpx(rc=rc))
            self.assertEqual(res["status"], "error")
            self.assertIn(word, res["exit_meaning"])

    def test_bridge_timeout_is_explained(self):
        res, _ = self.run_req(req("verify", "reference/form.hwpx"), lambda cmd, t: (-9, "FAILED: 시간 초과"))
        self.assertEqual(res["status"], "error")
        self.assertIn("Hwp.exe", res["exit_meaning"])

    def test_plaintext_result_is_quarantined(self):
        res, _ = self.run_req(req("fill", "reference/form.hwpx", {"map": {"a": "b"}}), FakeHwpx(protect=False))
        self.assertEqual(res["status"], "error")
        self.assertFalse(os.path.exists(os.path.join(self.root, "output_docs", "form_out.hwpx")))
        self.assertTrue(os.path.exists(os.path.join(self.root, "bridge", "quarantine", "%s_plaintext_out.hwpx" % RID)))
        self.assertIn("quarantine", res["notes"][0])

    def test_success_without_output_is_error(self):
        res, _ = self.run_req(req("fill", "reference/form.hwpx", {"map": {"a": "b"}}), FakeHwpx(make_out=False))
        self.assertEqual(res["status"], "error")

    def test_backend_fingerprint(self):
        res, _ = self.run_req(req("verify", "reference/form.hwpx"))
        self.assertEqual(res["backend_sha256"], core.tree_sha(self.scripts_dir))
        self.assertEqual(len(res["backend_sha256"]), 16)

    def test_purge_removes_md_dir_and_plaintext(self):
        self.run_req(req("inspect", "reference/form.hwpx"))
        self.run_req(req("fill", "reference/form.hwpx", {"map": {"a": "b"}}, rid=RID2), FakeHwpx(protect=False))
        q = os.path.join(self.root, "bridge", "quarantine")
        self.assertIn("%s_md" % RID, os.listdir(q))
        res, _ = self.run_req(req("purge", None, {"target_id": RID}, rid=RID3))
        self.assertEqual(res["status"], "ok")
        left = os.listdir(q)
        self.assertFalse([n for n in left if n.startswith(RID + "_")])
        self.assertTrue([n for n in left if n.startswith(RID2 + "_")])         # 다른 id 는 그대로
        core.purge_target(self.root, RID2)
        self.assertFalse([n for n in os.listdir(q) if n.startswith(RID2 + "_")])
        self.assertIn("x.hwpx", os.listdir(q))                                  # id 로 시작하지 않는 파일은 그대로

    def test_purge_old_removes_old_dirs_only(self):
        self.run_req(req("inspect", "reference/form.hwpx"))
        d = os.path.join(self.root, "bridge", "quarantine", "%s_md" % RID)
        old = time.time() - 48 * 3600
        for n in os.listdir(d):
            os.utime(os.path.join(d, n), (old, old))
        os.utime(d, (old, old))
        self.run_req(req("inspect", "reference/form.hwpx", rid=RID2))
        gone = core.purge_old(self.root, 24)
        self.assertEqual(gone, ["bridge/quarantine/%s_md" % RID])
        self.assertTrue(os.path.isdir(os.path.join(self.root, "bridge", "quarantine", "%s_md" % RID2)))

    def test_worker_audit_has_path_and_backend_op(self):
        res, _ = self.via_worker(req("inspect", "reference/form.hwpx"))
        rec = [json.loads(x) for x in open(os.path.join(self.root, "bridge", "audit.jsonl"), encoding="utf-8")][-1]
        self.assertEqual(rec["op"], "inspect")
        self.assertEqual(rec["path"], "reference/form.hwpx")
        self.assertTrue(rec["outputs"])

    def test_office_still_routed_to_office_scripts(self):
        r = req("read", "reference/doc.xlsx")
        rn = FakeHwpx()
        core.handle_request(self.root, raw(r), r["id"], PY, self.scripts, rn, None)
        self.assertEqual(rn.calls[0][1], "/s/r.py")


class TestHwpxNegative(Base):
    def test_ops_do_not_cross_backends(self):
        self.rejects(req("read", "reference/form.hwpx"), contains="한/글")
        self.rejects(req("dump", "reference/form.hwpx"), contains="한/글")
        self.rejects(req("protect", "reference/form.hwpx"), contains="한/글")
        self.rejects(req("inspect", "reference/doc.xlsx"), contains="오피스")
        self.rejects(req("verify", "reference/doc.xlsx"), contains="오피스")

    def test_unknown_and_dangerous_args(self):
        for a in ({"json": True}, {"overwrite": True}, {"force": True}, {"allow_running": True},
                  {"md_dir": "x"}, {"timeout": 1}, {"log": "x"}):
            self.rejects(req("inspect", "reference/form.hwpx", a), contains="허용하지 않는 인자")
        self.rejects(req("fill", "reference/form.hwpx", {"map": {"a": "b"}, "force": True}), contains="허용하지 않는 인자")
        self.rejects(req("fill", "reference/form.hwpx", {"map": {"a": "b"}, "overwrite": True}), contains="허용하지 않는 인자")

    def test_required_and_types(self):
        self.rejects(req("search", "reference/form.hwpx", {}), contains="필수")
        self.rejects(req("fill", "reference/form.hwpx", {}), contains="필수")
        self.rejects(req("tables", "reference/form.hwpx", {"table": "s0.t3; calc"}))
        self.rejects(req("tables", "reference/form.hwpx", {"table": "../x"}))
        self.rejects(req("fill", "reference/form.hwpx", {"map": {"a": 1}}))
        self.rejects(req("fill", "reference/form.hwpx", {"map": {}}))
        self.rejects(req("search", "reference/form.hwpx", {"pattern": "a\x00b"}))

    def test_extension_and_paths(self):
        open(os.path.join(self.root, "reference", "a.txt"), "w").write("x")
        self.rejects(req("inspect", "reference/a.txt"), contains="확장자")
        self.rejects(req("inspect", ".git/a.hwpx"), contains="입력")
        self.rejects(req("inspect", "bridge/quarantine/x.hwpx"), contains="입력")
        self.rejects(req("inspect", "reference/none.hwpx"), contains="없다")
        self.rejects(req("inspect", "../outside.hwpx"))
        self.rejects(req("inspect", "/etc/passwd.hwpx"))

    def test_out_restrictions(self):
        ok = {"map": {"a": "b"}}
        self.rejects(req("fill", "reference/form.hwpx", dict(ok, out="reference/x.hwpx")), contains="아래에만")
        self.rejects(req("fill", "reference/form.hwpx", dict(ok, out="output_docs/x.xlsx")), contains="확장자")
        self.rejects(req("fill", "reference/form.hwpx", dict(ok, out="../x.hwpx")))
        self.rejects(req("fill", "reference/form.hwpx", dict(ok, out="review_docs/plain.hwpx")), contains="이미 있다")
        self.rejects(req("fill", "reference/form.hwpx", dict(ok, out="nodir/x.hwpx")))
        open(os.path.join(self.root, "output_docs", "form_out.hwpx"), "wb").write(b"x")
        self.rejects(req("fill", "reference/form.hwpx", ok), contains="이미 있다")

    def test_replace_requires_search(self):
        m = {"map": {"{{과제명}}": "OOO"}}
        self.rejects(req("replace", "reference/form.hwpx", m), contains="필수")
        self.rejects(req("replace", "reference/form.hwpx", dict(m, search_id="261016_999999_ffff")), contains="search_id")
        self.rejects(req("replace", "reference/form.hwpx", dict(m, search_id="not-an-id")))

    def test_replace_precondition_details(self):
        sid = self.do_search("{{과제명}},○○○")
        good = {"map": {"{{과제명}}": "OOO"}, "search_id": sid}
        core.validate_request(raw(req("replace", "reference/form.hwpx", good, rid=RID2)), RID2, self.root)
        # 찾지 않은 키
        self.rejects(req("replace", "reference/form.hwpx", {"map": {"{{책임자}}": "x"}, "search_id": sid}, rid=RID2),
                     contains="search 하지 않은 키")
        # 다른 파일
        self.rejects(req("replace", "reference/other.hwpx", good, rid=RID2), contains="다른 파일")
        # 파일이 바뀜
        with open(os.path.join(self.root, "reference", "form.hwpx"), "ab") as f:
            f.write(b"changed")
        self.rejects(req("replace", "reference/form.hwpx", good, rid=RID2), contains="바뀌었다")

    def test_replace_key_with_comma(self):
        """검색어 안의 쉼표는 '\\,' — 쉼표 든 바꿀 글자도 search 로 위치를 본 뒤 replace 할 수 있다(P-052)."""
        sid = self.do_search("기동헬기 경로설정\\, 지상작전부대 경로설정,○○○")
        key = "기동헬기 경로설정, 지상작전부대 경로설정"
        core.validate_request(raw(req("replace", "reference/form.hwpx", {"map": {key: key + ", 무인기 고장"},
                                                                         "search_id": sid}, rid=RID2)), RID2, self.root)
        # 쉼표를 그대로 쓴 search 는 두 검색어로 나뉘어 그 키를 찾지 않은 것이다
        sid2 = self.do_search("기동헬기 경로설정, 지상작전부대 경로설정", rid=RID3)
        self.rejects(req("replace", "reference/form.hwpx", {"map": {key: "x"}, "search_id": sid2},
                         rid="261016_120009_0009"), contains="search 하지 않은 키")

    def test_split_patterns(self):
        sp = core.split_patterns
        for text, want in (("a,b", ["a", "b"]), ("가\\, 나,다", ["가, 나", "다"]), ("x\\\\,y", ["x\\", "y"]),
                           ("C:\\p\\a,b", ["C:\\p\\a", "b"]), (" , a ,", ["a"]), ("끝\\", ["끝\\"])):
            self.assertEqual(sp(text), want, text)

    def test_replace_rejects_failed_or_non_search_ref(self):
        res, _ = self.via_worker(req("search", "reference/form.hwpx", {"pattern": "x"}), FakeHwpx(rc=4))
        self.assertEqual(res["status"], "error")
        self.rejects(req("replace", "reference/form.hwpx", {"map": {"x": "y"}, "search_id": RID}, rid=RID2),
                     contains="성공한 search")
        res, _ = self.via_worker(req("inspect", "reference/form.hwpx", rid=RID3))
        self.rejects(req("replace", "reference/form.hwpx", {"map": {"x": "y"}, "search_id": RID3}, rid="261016_120009_0009"),
                     contains="성공한 search")

    def test_replace_rejects_stale_search(self):
        sid = self.do_search()
        outp = os.path.join(self.root, "bridge", "outbox", sid + ".json")
        old = time.time() - 25 * 3600
        os.utime(outp, (old, old))
        self.rejects(req("replace", "reference/form.hwpx", {"map": {"○○○": "x"}, "search_id": sid}, rid=RID2),
                     contains="24시간")

    def test_rejected_never_calls_runner(self):
        rn = FakeHwpx()
        res, _ = self.run_req(req("replace", "reference/form.hwpx", {"map": {"a": "b"}}), rn)
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(rn.calls, [])

    def test_confirm_denied_never_calls_runner(self):
        rn = FakeHwpx()
        res, _ = self.run_req(req("inspect", "reference/form.hwpx"), rn, confirm=lambda r, p: False)
        self.assertEqual(res["status"], "denied")
        self.assertEqual(rn.calls, [])

    def test_runner_exception_does_not_escape(self):
        def boom(cmd, t):
            raise OSError("boom")
        res, _ = self.run_req(req("inspect", "reference/form.hwpx"), boom)
        self.assertEqual(res["status"], "error")


SPEC_OK = ("<!-- 메모 안의 ](hwpx:없는/x.hwpx#1) 는 도구처럼 지우고 본다 -->\n##### 새 절\n1) 단계.\n"
           "![캡션](hwpx:reference/other.hwpx#2 \"50x30\")\n")


class FakeInsert:
    """insert_doc.py 흉내: --report 보고(본문 글자)와 --out 보호본을 만들고 결과 줄을 낸다."""
    def __init__(self, protect=True, rc=0, make_out=True):
        self.calls, self.protect, self.rc, self.make_out, self.timeouts = [], protect, rc, make_out, []

    def __call__(self, cmd, timeout):
        self.calls.append(cmd)
        self.timeouts.append(timeout)
        opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in cmd if c.startswith("--") and "=" in c}
        with open(opts["--report"], "w", encoding="utf-8") as f:
            f.write("# 끼워 넣기 보고 SECRET-BODY\n")
        self.spec_seen = open(opts["--spec"], encoding="utf-8").read() if os.path.isfile(opts["--spec"]) else None
        if self.make_out and self.rc in (0, 1):
            with open(opts["--out"], "wb") as f:
                f.write((b"BMS DocuRay" if self.protect else b"PK\x03\x04") + b"....")
        line = "OK — %s" % opts["--out"] if self.rc == 0 else "FAIL — 넣은 문단이 명세와 다르다 SECRET-BODY"
        return self.rc, "SECRET-BODY 본문 줄\n경고: 보안승인 모듈 미등록\n%s\n보고: %s\n" % (line, opts["--report"])


class InsertBase(Base):
    def setUp(self):
        Base.setUp(self)
        os.makedirs(os.path.join(self.root, "tools", "doc-writer"))
        os.makedirs(os.path.join(self.root, "tools", "hwpx-drm", "scripts"))
        self.tool = os.path.join(self.root, "tools", "doc-writer", "insert_doc.py")
        with open(self.tool, "w") as f:
            f.write("# fake\n")
        with open(os.path.join(self.root, "tools", "hwpx-drm", "scripts", "hwpx_api.py"), "w") as f:
            f.write("# fake\n")
        self.spec("output_docs/ins.md", SPEC_OK)
        self.pin_dir = tempfile.mkdtemp(prefix="pin_")
        self.old_pin = core.INSERT_PIN
        core.INSERT_PIN = os.path.join(self.pin_dir, "insert_pin.json")
        self.write_pin()

    def write_pin(self):
        with open(core.INSERT_PIN, "w", encoding="utf-8") as f:
            json.dump({"dirs": core.insert_fingerprint(self.root)}, f)

    def tearDown(self):
        core.INSERT_PIN = self.old_pin
        shutil.rmtree(self.pin_dir, ignore_errors=True)
        Base.tearDown(self)

    def spec(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:    # Windows 에서도 LF — 명세 해시 비교(spec_sha256)
            f.write(text)
        return rel

    def args(self, **kw):
        a = {"spec": "output_docs/ins.md", "before": "작업의 종료", "out": "output_docs/new.hwpx"}
        a.update(kw)
        return a


class TestHwpxInsert(InsertBase):
    def test_command_and_outputs(self):
        res, rn = self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert())
        self.assertEqual(res["status"], "ok", res)
        cmd = rn.calls[0]
        self.assertEqual(cmd[:2], [PY, os.path.realpath(self.tool)])
        self.assertTrue(cmd[2].replace("\\", "/").endswith("reference/form.hwpx"))
        self.assertIn("--before=작업의 종료", cmd)
        self.assertIn("--timeout=%d" % core.HWPX_COM_TIMEOUT, cmd)
        spec = [c for c in cmd if c.startswith("--spec=")][0][7:]
        self.assertIn(os.path.join("bridge", "work", "%s_spec.md" % RID), spec)   # 검사한 글의 사본(D1-06)
        self.assertEqual(rn.spec_seen, SPEC_OK)
        self.assertFalse(os.path.exists(spec))                                      # 끝나면 지운다
        import hashlib
        self.assertEqual(res["spec_sha256"], hashlib.sha256(SPEC_OK.encode("utf-8")).hexdigest())
        self.assertTrue(any(c.startswith("--report=") and "quarantine" in c and "%s_insert_report.md" % RID in c
                            for c in cmd))
        self.assertTrue(any(c.startswith("--out=") and c.endswith("new.hwpx") for c in cmd))
        self.assertFalse([c for c in cmd if c.startswith(("--force", "--overwrite"))])
        self.assertTrue(res["drm_signature"])
        paths = [o["path"] for o in res["outputs"]]
        self.assertEqual(paths, ["bridge/quarantine/%s_insert_report.md" % RID, "output_docs/new.hwpx"])
        self.assertEqual(res["backend_sha256"], core.tree_sha(os.path.dirname(self.tool)))
        self.assertEqual(rn.timeouts[0], core.HWPX_TIMEOUT_SEC)
        self.assertNotIn("SECRET-BODY", json.dumps(res, ensure_ascii=False))
        self.assertIn("OK —", res["stdout_tail"])

    def test_fail_line_hides_reason(self):
        res, _ = self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert(rc=1))
        self.assertEqual(res["status"], "error")
        # 실패한 실행이 남긴 파일(확인 안 됨)은 output 에 두지 않는다(D1-07)
        self.assertFalse(os.path.exists(os.path.join(self.root, "output_docs", "new.hwpx")))
        self.assertTrue(os.path.exists(os.path.join(self.root, "bridge", "quarantine", "%s_unverified_out.hwpx" % RID)))
        self.assertNotIn("SECRET-BODY", json.dumps(res, ensure_ascii=False))
        self.assertIn("FAIL — 사유는 quarantine 의 보고", res["stdout_tail"])
        self.assertTrue(os.path.isfile(os.path.join(self.root, "bridge", "quarantine", "%s_insert_report.md" % RID)))

    def test_plaintext_result_is_quarantined(self):
        res, _ = self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert(protect=False))
        self.assertEqual(res["status"], "error")
        self.assertFalse(os.path.exists(os.path.join(self.root, "output_docs", "new.hwpx")))
        self.assertTrue(os.path.exists(os.path.join(self.root, "bridge", "quarantine", "%s_plaintext_out.hwpx" % RID)))

    def test_success_without_output_is_error(self):
        res, _ = self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert(make_out=False))
        self.assertEqual(res["status"], "error")

    def test_purge_removes_report(self):
        self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert())
        res, _ = self.run_req(req("purge", None, {"target_id": RID}, rid=RID2))
        self.assertIn("bridge/quarantine/%s_insert_report.md" % RID, res["removed"])

    def test_via_worker(self):
        res, rn = self.via_worker(req("insert", "reference/form.hwpx", self.args()), FakeInsert())
        self.assertEqual(res["status"], "ok", res)


class TestHwpxInsertNegative(InsertBase):
    def test_required_and_unknown(self):
        for k in ("spec", "before", "out"):
            a = self.args()
            del a[k]
            self.rejects(req("insert", "reference/form.hwpx", a), contains="필수")
        for extra in ({"force": True}, {"overwrite": True}, {"report": "x"}, {"timeout": 1}, {"template": "x"}):
            self.rejects(req("insert", "reference/form.hwpx", self.args(**extra)), contains="허용하지 않는 인자")
        self.rejects(req("insert", "reference/form.hwpx", self.args(before="a\nb")), contains="제어문자")
        self.rejects(req("insert", "reference/form.hwpx", self.args(before="가" * 201)), contains="너무 길다")
        self.rejects(req("insert", "reference/doc.xlsx", self.args()), contains="오피스")

    def test_spec_restrictions(self):
        self.spec("reference/s.md", SPEC_OK)
        self.spec("output_docs/s.txt", SPEC_OK)
        self.rejects(req("insert", "reference/form.hwpx", self.args(spec="reference/s.md")), contains="아래 명세만")
        self.rejects(req("insert", "reference/form.hwpx", self.args(spec="output_docs/s.txt")), contains=".md")
        self.rejects(req("insert", "reference/form.hwpx", self.args(spec="output_docs/none.md")), contains="없다")
        self.rejects(req("insert", "reference/form.hwpx", self.args(spec="../x.md")), contains="저장소 밖")
        with open(os.path.join(self.root, "output_docs", "cp.md"), "wb") as f:
            f.write("##### 제목".encode("cp949"))
        self.rejects(req("insert", "reference/form.hwpx", self.args(spec="output_docs/cp.md")), contains="UTF-8")

    def test_figure_source_restrictions(self):
        for src, why in (("../x.hwpx", "저장소 밖"), ("bridge/quarantine/x.hwpx", "입력"), (".git/a.hwpx", "입력"),
                         ("reference/doc.xlsx", "확장자"), ("reference/none.hwpx", "없다")):
            with self.subTest(src=src):
                self.spec("output_docs/f.md", "##### 절\n![캡션](hwpx:%s#1)\n" % src)
                self.rejects(req("insert", "reference/form.hwpx", self.args(spec="output_docs/f.md")), contains=why)
        # 꼴이 틀린 그림 줄은 거절 — '#' 든 경로·앞 빈칸·크기 쉼표·끝 글자·괄호 안 빈칸(검토 D1-06)
        for line in ("![c](hwpx:reference/form.hwpx#1x/other.hwpx#1)", " ![c](hwpx:reference/form.hwpx#1)",
                     '![c](hwpx:reference/form.hwpx#1 "5,5x3")', "![c](hwpx:reference/form.hwpx#1)。",
                     "![c]( hwpx:reference/form.hwpx#1)", "글 ](hwpx:reference/form.hwpx#1)", "![c](img/a.png)"):
            with self.subTest(line=line):
                self.spec("output_docs/f.md", "##### 절\n1) 단계\n%s\n" % line)
                self.rejects(req("insert", "reference/form.hwpx", self.args(spec="output_docs/f.md")), contains="꼴")

    def test_out_restrictions(self):
        self.rejects(req("insert", "reference/form.hwpx", self.args(out="reference/x.hwpx")), contains="아래에만")
        self.rejects(req("insert", "reference/form.hwpx", self.args(out="output_docs/x.docx")), contains="확장자")
        self.rejects(req("insert", "reference/form.hwpx", self.args(out="review_docs/plain.hwpx")), contains="이미 있다")
        self.rejects(req("insert", "reference/form.hwpx", self.args(out="reference/form.hwpx")))

    def test_tool_missing(self):
        os.remove(self.tool)
        self.rejects(req("insert", "reference/form.hwpx", self.args()), contains="tools/doc-writer/insert_doc.py")

    def test_tool_pin(self):
        """도구 코드가 배포 때 지문과 다르면 거절(검토 D1-01) — 작업 트리의 도구·hwpx-drm 을 원격으로 고친 뒤 실행 막기."""
        core.validate_request(raw(req("insert", "reference/form.hwpx", self.args())), RID, self.root)
        for rel in ("tools/doc-writer/insert_doc.py", "tools/doc-writer/write_doc.py", "tools/hwpx-drm/scripts/hwpx_api.py"):
            with self.subTest(rel=rel):
                with open(os.path.join(self.root, rel), "a") as f:
                    f.write("# changed\n")
                self.rejects(req("insert", "reference/form.hwpx", self.args()), contains="배포 때와 다르다")
                self.write_pin()
        os.remove(core.INSERT_PIN)
        self.rejects(req("insert", "reference/form.hwpx", self.args()), contains="insert_pin.json")

    def test_rejected_never_calls_runner(self):
        rn = FakeInsert()
        res, _ = self.run_req(req("insert", "reference/form.hwpx", self.args(spec="output_docs/none.md")), rn)
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(rn.calls, [])


class TestHwpxImages(Base):
    """images(P-052, D-062): 문서에 포함된 그림을 output_docs·review_docs 아래 새 폴더에 평문 파일로."""
    def test_command_and_outputs(self):
        def runner(cmd, timeout):
            opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in cmd if c.startswith("--") and "=" in c}
            os.makedirs(opts["--out-dir"])
            for n in ("fig01.png", "images.md"):
                with open(os.path.join(opts["--out-dir"], n), "wb") as f:
                    f.write(b"SECRET-BODY")
            with open(opts["--log"], "w", encoding="utf-8") as f:
                f.write("# log\n")
            runner.cmd = cmd
            return 0, "SECRET-BODY 캡션\n그림 2개 · 꺼냄 1 · 건너뜀 1\n만든 파일: x\n"
        res, _ = self.run_req(req("images", "reference/form.hwpx", {"out_dir": "output_docs/img"}), runner)
        self.assertEqual(res["status"], "ok", res)
        self.assertEqual(runner.cmd[:4], [PY, self.scripts["hwpx"], "images", runner.cmd[3]])
        self.assertTrue(any(c.startswith("--out-dir=") and c.endswith("img") for c in runner.cmd))
        self.assertTrue(any(c.startswith("--log=") and "outbox" in c for c in runner.cmd))
        paths = [o["path"] for o in res["outputs"]]
        self.assertIn("output_docs/img/fig01.png", paths)
        self.assertIn("그림 2개 · 꺼냄 1 · 건너뜀 1", res["stdout_tail"])
        self.assertNotIn("SECRET-BODY", json.dumps(res, ensure_ascii=False))

    def test_rejects(self):
        for a, why in (({"out_dir": "reference/img"}, "새 폴더만"), ({"out_dir": "output_docs"}, "새 폴더만"),
                       ({"out_dir": "../img"}, "저장소 밖"), ({}, "필수"), ({"out_dir": "output_docs/img", "md_dir": "x"}, "허용하지")):
            with self.subTest(a=a):
                self.rejects(req("images", "reference/form.hwpx", a), contains=why)
        self.rejects(req("images", "reference/doc.xlsx", {"out_dir": "output_docs/img"}), contains="오피스")
        os.makedirs(os.path.join(self.root, "output_docs", "img"))
        self.rejects(req("images", "reference/form.hwpx", {"out_dir": "output_docs/img"}), contains="이미 있다")


class FakePack:
    """figure_pack.py 흉내: --out-dir 에 all·figKK 보호본, --report 보고(캡션 글)를 만든다."""
    def __init__(self, rc=0, plain=(), unverified=()):
        self.calls, self.rc, self.plain, self.unverified = [], rc, set(plain), set(unverified)

    def __call__(self, cmd, timeout):
        self.calls.append(cmd)
        opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in cmd if c.startswith("--") and "=" in c}
        os.makedirs(opts["--out-dir"])
        for n in ("all.hwpx", "fig01.hwpx", "fig02.hwpx"):
            name = n.replace(".hwpx", ".unverified.hwpx") if n in self.unverified else n
            with open(os.path.join(opts["--out-dir"], name), "wb") as f:
                f.write((b"PK\x03\x04" if n in self.plain else b"BMS DocuRay") + b"....")
        with open(opts["--report"], "w", encoding="utf-8") as f:
            f.write("# 그림 꾸러미 보고 SECRET-BODY\n")
        line = "OK — %s" % opts["--out-dir"] if self.rc == 0 else "FAIL — 캡션 제목 다름 SECRET-BODY"
        return self.rc, "%s\n보고: %s\n" % (line, opts["--report"])


class TestHwpxFigpack(InsertBase):
    def setUp(self):
        InsertBase.setUp(self)
        with open(os.path.join(self.root, "tools", "doc-writer", "figure_pack.py"), "w") as f:
            f.write("# fake\n")
        self.write_pin()

    def test_command_and_outputs(self):
        res, rn = self.run_req(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack", "only": "1,2"}),
                               FakePack())
        self.assertEqual(res["status"], "ok", res)
        cmd = rn.calls[0]
        self.assertTrue(cmd[1].endswith("figure_pack.py"))
        self.assertIn("--only=1,2", cmd)
        self.assertTrue(any(c.startswith("--out-dir=") and c.endswith("pack") for c in cmd))
        self.assertTrue(any(c.startswith("--report=") and "%s_pack_report.md" % RID in c for c in cmd))
        paths = [o["path"] for o in res["outputs"]]
        self.assertIn("output_docs/pack/fig02.hwpx", paths)
        self.assertIn("bridge/quarantine/%s_pack_report.md" % RID, paths)
        self.assertNotIn("SECRET-BODY", json.dumps(res, ensure_ascii=False))
        self.assertTrue(res["drm_signature"])

    def test_plaintext_and_unverified_quarantined(self):
        res, _ = self.run_req(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack"}),
                              FakePack(rc=1, plain={"fig01.hwpx"}, unverified={"fig02.hwpx"}))
        self.assertEqual(res["status"], "error")
        left = sorted(os.listdir(os.path.join(self.root, "output_docs", "pack")))
        self.assertEqual(left, ["all.hwpx"])
        q = os.listdir(os.path.join(self.root, "bridge", "quarantine"))
        self.assertTrue(any(n.endswith("fig01.hwpx") for n in q) and any(n.endswith("fig02.unverified.hwpx") for n in q), q)
        self.assertFalse(res["drm_signature"])
        self.assertNotIn("SECRET-BODY", json.dumps(res, ensure_ascii=False))

    def test_rejects(self):
        for a, why in (({"out_dir": "reference/pack"}, "새 폴더만"), ({"out_dir": "output_docs"}, "새 폴더만"),
                       ({"out_dir": "output_docs/x/y"}, "부모"), ({"out_dir": "../pack"}, "저장소 밖"),
                       ({"out_dir": "output_docs/pack", "only": "1;2"}, "only"),
                       ({"out_dir": "output_docs/pack", "only": "1, 2"}, "only"), ({}, "필수"),
                       ({"out_dir": "output_docs/pack", "force": True}, "허용하지 않는")):
            with self.subTest(a=a):
                self.rejects(req("figpack", "reference/form.hwpx", a), contains=why)
        os.makedirs(os.path.join(self.root, "output_docs", "pack"))
        self.rejects(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack"}), contains="이미 있다")

    def test_pin(self):
        with open(os.path.join(self.root, "tools", "doc-writer", "figure_pack.py"), "a") as f:
            f.write("# changed\n")
        self.rejects(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack"}), contains="배포 때와 다르다")
        os.remove(os.path.join(self.root, "tools", "doc-writer", "figure_pack.py"))
        self.write_pin()
        self.rejects(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack"}), contains="figure_pack.py")


REAL_INSERT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "tools", "doc-writer", "insert_doc.py"))


class TestRealInsertCli(InsertBase):
    """브리지 insert 명령줄이 실제 insert_doc.py 파서에 받아들여지는지 — drmHWP 저장소(배포 사본)에서만 돈다."""
    def test_parses(self):
        if not os.path.isfile(REAL_INSERT):
            self.skipTest("이 저장소에 tools/doc-writer/insert_doc.py 가 없다")
        sys.path.insert(0, os.path.dirname(REAL_INSERT))
        try:
            import insert_doc
        except Exception as e:                      # noqa: BLE001 — 환경 문제
            self.skipTest("insert_doc 을 가져올 수 없다: %s" % e)
        finally:
            sys.path.remove(os.path.dirname(REAL_INSERT))
        res, rn = self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert())
        ns = insert_doc.build_parser().parse_args(rn.calls[0][2:])
        self.assertEqual(ns.before, "작업의 종료")
        self.assertEqual(ns.timeout, core.HWPX_COM_TIMEOUT)
        self.assertTrue(ns.out.endswith("new.hwpx") and ns.spec.endswith("%s_spec.md" % RID) and ns.report.endswith(".md"))


class TestRealFigpackCli(TestHwpxFigpack):
    """브리지 figpack 명령줄이 실제 figure_pack.py 파서에 받아들여지는지 — drmHWP 저장소(배포 사본)에서만 돈다."""
    def test_parses(self):
        real = os.path.join(os.path.dirname(REAL_INSERT), "figure_pack.py")
        if not os.path.isfile(real):
            self.skipTest("이 저장소에 tools/doc-writer/figure_pack.py 가 없다")
        sys.path.insert(0, os.path.dirname(real))
        try:
            import figure_pack
        except Exception as e:                      # noqa: BLE001 — 환경 문제
            self.skipTest("figure_pack 을 가져올 수 없다: %s" % e)
        finally:
            sys.path.remove(os.path.dirname(real))
        res, rn = self.run_req(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack", "only": "2"}),
                               FakePack())
        ns = figure_pack.build_parser().parse_args(rn.calls[0][2:])
        self.assertEqual((ns.only, ns.timeout), ("2", core.HWPX_COM_TIMEOUT))
        self.assertTrue(ns.out_dir.endswith("pack") and ns.report.endswith("_pack_report.md"))


REAL_HWPX_SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "..", "hwpx-drm", "scripts"))


class TestRealCli(Base):
    """브리지가 만드는 명령줄이 실제 hwpx_drm.py 의 인자 파서에 받아들여지는지 (옵션 이름 오타를 가짜 실행기는 못 잡는다).
    한/글은 열지 않는다 — 파서만 쓴다. 배포 사본이 없거나 가져올 수 없으면 건너뛴다."""
    def setUp(self):
        Base.setUp(self)
        if not os.path.isfile(os.path.join(REAL_HWPX_SCRIPTS, "hwpx_drm.py")):
            self.skipTest("hwpx-drm 배포 사본이 없다")
        sys.path.insert(0, REAL_HWPX_SCRIPTS)
        try:
            import hwpx_drm
        except Exception as e:                      # pywin32 등 환경 문제
            sys.path.remove(REAL_HWPX_SCRIPTS)
            self.skipTest("hwpx_drm 을 가져올 수 없다: %s" % e)
        self.parser = hwpx_drm.build_parser()
        self.scripts["hwpx"] = os.path.join(REAL_HWPX_SCRIPTS, "hwpx_drm.py")

    def tearDown(self):
        if REAL_HWPX_SCRIPTS in sys.path:
            sys.path.remove(REAL_HWPX_SCRIPTS)
        Base.tearDown(self)

    def test_split_patterns_same_as_hwpx_drm(self):
        """브리지 선행조건의 검색어 나누기 = hwpx_drm.py search 의 나누기(P-052, 다르면 찾은 키와 바꿀 키가 어긋난다)."""
        import hwpx_drm
        if not hasattr(hwpx_drm, "split_patterns"):
            self.skipTest("배포된 hwpx-drm 이 '\\,' 이전 판이다")
        for text in ("a,b", "가\\, 나,다", "x\\\\,y", "C:\\p\\a,b", " , a ,", "끝\\", "\\\\\\,", ",,", "a\\,b\\,c,d"):
            self.assertEqual(core.split_patterns(text), hwpx_drm.split_patterns(text), text)

    def test_every_op_parses(self):
        sid = self.do_search("a", rid="261016_129999_ffff")
        cases = [("inspect", None), ("outline", None), ("fields", None), ("verify", None),
                 ("tables", {"table": "s0.t3"}), ("search", {"pattern": "-헬기,Heli"}),
                 ("fill", {"map": {"a": "b"}, "out": "output_docs/a.hwpx"}),
                 ("replace", {"map": {"a": "c"}, "search_id": sid, "out": "output_docs/b.hwpx"}),
                 ("images", {"out_dir": "output_docs/img"})]
        for i, (op, a) in enumerate(cases):
            if op == "images" and "images" not in self.parser._subparsers._group_actions[0].choices:
                continue                                  # 배포된 hwpx-drm 이 images 이전 판(원본 저장소)
            res, rn = self.run_req(req(op, "reference/form.hwpx", a, rid="261016_1300%02d_aa%02x" % (i, i)))
            self.assertTrue(rn.calls, (op, res))
            ns = self.parser.parse_args(rn.calls[0][2:])
            self.assertEqual(ns.cmd, op)
            self.assertEqual(ns.timeout, core.HWPX_COM_TIMEOUT)
            if op in ("fill", "replace"):
                self.assertFalse(ns.force or ns.overwrite)
            if op == "images":
                self.assertTrue(ns.out_dir.endswith("img"))
            if op in ("inspect", "outline", "fields", "tables", "search", "fill", "replace"):
                self.assertFalse(getattr(ns, "json", False))
            self.assertFalse(ns.allow_running)


class TestBeater(Base):
    """긴 요청을 처리하는 동안에도 하트비트 seq 가 올라가야 클라이언트가 워커를 살아 있다고 본다."""
    def test_heartbeat_advances_while_busy(self):
        import bridge_client as client
        b = worker.Beater(self.root, "auto", interval=0.05)
        b.start()
        try:
            hb = os.path.join(self.root, "bridge", "worker_alive.json")
            first = json.load(open(hb, encoding="utf-8"))["seq"]
            time.sleep(0.4)                               # 메인 스레드가 '요청 처리 중'인 척 막혀 있다
            later = json.load(open(hb, encoding="utf-8"))["seq"]
            self.assertGreater(later, first + 2)
            alive, _ = client.worker_alive(self.root, wait=0.1)
            self.assertTrue(alive)
        finally:
            b.stop()

    def test_stop_stops_beating(self):
        b = worker.Beater(self.root, "auto", interval=0.05)
        b.start()
        b.stop()
        hb = os.path.join(self.root, "bridge", "worker_alive.json")
        seq = json.load(open(hb, encoding="utf-8"))["seq"]
        time.sleep(0.2)
        self.assertEqual(json.load(open(hb, encoding="utf-8"))["seq"], seq)

    def test_main_once_removes_heartbeat(self):
        self.assertEqual(worker.main(["--root", self.root, "--once", "--poll", "0.1"]), 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, "bridge", "worker_alive.json")))


class TestHwpxMutations(unittest.TestCase):
    """통제를 일부러 무력화하면 대응 시험이 실패해야 한다."""
    def run_case(self, case_cls, name):
        suite = unittest.TestSuite([case_cls(name)])
        return unittest.TextTestRunner(stream=open(os.devnull, "w", encoding="utf-8"), verbosity=0).run(suite).wasSuccessful()

    def mutate(self, attr, new, case_cls, name):
        old = getattr(core, attr)
        self.assertTrue(self.run_case(case_cls, name), "변이 전에는 통과해야 한다: " + name)
        setattr(core, attr, new)
        try:
            self.assertFalse(self.run_case(case_cls, name), "통제 %s 를 끄면 %s 가 실패해야 한다" % (attr, name))
        finally:
            setattr(core, attr, old)

    def test_M10_search_precondition(self):
        self.mutate("check_search_precondition", lambda *a: None, TestHwpxNegative, "test_replace_requires_search")
        self.mutate("check_search_precondition", lambda *a: None, TestHwpxNegative, "test_replace_precondition_details")

    def test_M11_plaintext_quarantine(self):
        self.mutate("drm_signature", lambda p: True, TestHwpxNormal, "test_plaintext_result_is_quarantined")

    def test_M12_stdout_filter(self):
        self.mutate("safe_tail_hwpx", lambda t, op=None: t, TestHwpxNormal, "test_stdout_tail_has_status_only")

    def test_M13_extension_check(self):
        self.mutate("HWPX_EXT", {".hwpx", ".hwp", ".txt"}, TestHwpxNegative, "test_extension_and_paths")

    def test_M14_out_extension(self):
        self.mutate("HWPX_OUT_EXT", {".hwpx", ".xlsx"}, TestHwpxNegative, "test_out_restrictions")

    def test_M15_dangerous_args_exposed(self):
        old = dict(core.HWPX_ARGS["fill"])
        self.assertTrue(self.run_case(TestHwpxNegative, "test_unknown_and_dangerous_args"))
        core.HWPX_ARGS["fill"] = dict(old, force=("bool",), overwrite=("bool",))
        try:
            self.assertFalse(self.run_case(TestHwpxNegative, "test_unknown_and_dangerous_args"))
        finally:
            core.HWPX_ARGS["fill"] = old

    def test_M16_backend_routing(self):
        """오피스 연산이 한/글 문서에 통하게 만들면 시험이 잡아야 한다."""
        self.mutate("OFFICE_OPS", core.OFFICE_OPS + core.HWPX_OPS, TestHwpxNegative, "test_ops_do_not_cross_backends")

    def test_M17_blocked_dirs(self):
        self.mutate("BLOCKED_SRC_DIRS", (), TestHwpxNegative, "test_extension_and_paths")

    def test_M19_insert_checks(self):
        """insert 명세 검사(위치·확장자·그림 출처)를 끄면 음성 시험이 잡아야 한다(P-052)."""
        def loose(root, spec):
            return (os.path.realpath(os.path.join(root, spec)), os.path.realpath(os.path.join(root, *core.INSERT_SCRIPT)))
        self.mutate("check_insert", loose, TestHwpxInsertNegative, "test_spec_restrictions")
        self.mutate("check_insert", loose, TestHwpxInsertNegative, "test_figure_source_restrictions")
        self.mutate("check_insert", loose, TestHwpxInsertNegative, "test_tool_missing")

    def test_M20_insert_figure_sources(self):
        import re
        self.mutate("INSERT_FIG_LINE", re.compile(r".*\(hwpx:(.+)#"), TestHwpxInsertNegative, "test_figure_source_restrictions")

    def test_M24_insert_pin(self):
        self.mutate("insert_fingerprint", lambda root: {}, TestHwpxInsertNegative, "test_tool_pin")   # 지문이 코드를 안 보면

    def test_M21_insert_fail_reason_hidden(self):
        self.mutate("STATUS_PREFIX_INSERT", core.STATUS_PREFIX_INSERT + ("FAIL",), TestHwpxInsert,
                    "test_fail_line_hides_reason")

    def test_M22_insert_spec_ext(self):
        self.mutate("SPEC_EXT", {".md", ".txt"}, TestHwpxInsertNegative, "test_spec_restrictions")

    def test_M23_insert_plaintext_quarantine(self):
        self.mutate("drm_signature", lambda p: True, TestHwpxInsert, "test_plaintext_result_is_quarantined")

    def test_M25_escaped_comma(self):
        """'\\,' 를 쉼표 그대로 나누게 되돌리면 쉼표 든 키의 replace 시험이 잡아야 한다(P-052)."""
        self.mutate("split_patterns", lambda s: [x.strip() for x in s.split(",") if x.strip()], TestHwpxNegative,
                    "test_replace_key_with_comma")

    def test_M26_figpack_quarantine(self):
        self.mutate("drm_signature", lambda p: True, TestHwpxFigpack, "test_plaintext_and_unverified_quarantined")

    def test_M27_figpack_out_dir(self):
        self.mutate("check_out_dir", lambda root, d: os.path.realpath(os.path.join(root, d)), TestHwpxFigpack, "test_rejects")

    def test_M28_images_out_dir(self):
        self.mutate("check_out_dir", lambda root, d: os.path.realpath(os.path.join(root, d)), TestHwpxImages, "test_rejects")

    def test_M18_md_dir_per_request(self):
        """읽기 결과 폴더가 요청마다 달라야 한다(같으면 같은 이름의 .md 가 서로 덮어쓴다)."""
        src = open(os.path.join(HERE, "..", "scripts", "bridge_core.py"), encoding="utf-8").read()
        self.assertIn('"%s_md" % rid', src)
        import types
        mutated = src.replace('"%s_md" % rid', '"shared_md"')
        ns = {"__name__": "mut_core2"}
        exec(compile(mutated, "mut_core2", "exec"), ns)
        mod = types.SimpleNamespace(**ns)

        class T(TestHwpxNormal):
            def run_req(self, r, runner=None, confirm=None):
                runner = runner or FakeHwpx()
                return mod.handle_request(self.root, raw(r), r["id"], PY, self.scripts, runner, confirm), runner
        self.assertFalse(self.run_case(T, "test_inspect_command"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
