"""UF-01·UF-02 시험 (가짜 COM). python -m unittest discover -s tools\\hwpx-drm\\tests"""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import hwp_session as hs          # noqa: E402
from fake_hwp import FakeHwp, make_env, DECL16   # noqa: E402


def session(fake, **kw):
    d, p, k, st = make_env(fake, pids_before=kw.pop("pids_before", ()), new_pid=kw.pop("new_pid", 4242))
    return hs.HwpSession(dispatch=d, pids=p, killer=k, **kw), st


class TestSession(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.doc = self.tmp / "a.hwpx"
        self.doc.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 32)

    def test_running_hwp_blocks_start(self):                 # F-026
        s, _ = session(FakeHwp(), pids_before={111})
        with self.assertRaises(hs.PreconditionError) as cm:
            s.start()
        self.assertEqual(cm.exception.code, 2)

    def test_allow_running_ok(self):
        s, _ = session(FakeHwp(), pids_before={111}, allow_running=True)
        with s:
            self.assertEqual(s.pid, 4242)

    def test_pywin32_missing_is_code6(self):
        def boom():
            raise ImportError("No module named win32com")
        s = hs.HwpSession(dispatch=boom, pids=lambda: set())
        with self.assertRaises(hs.ComUnavailable) as cm:
            s.start()
        self.assertEqual(cm.exception.code, 6)

    def test_module_warning_and_version(self):               # U-12
        msgs = []
        s, _ = session(FakeHwp(module_ok=False), log=msgs.append)
        with s:
            self.assertFalse(s.module_ok)
            self.assertEqual(s.version, "13, 0, 0, 3903")
        self.assertTrue(any("보안승인 모듈" in m for m in msgs))

    def test_open_fallback_then_fail_code4(self):
        seen = []
        fake = FakeHwp(open_ok=lambda p, f, a: seen.append(a) or False)
        s, _ = session(fake)
        with s, self.assertRaises(hs.OpenFailed) as cm:
            s.open(self.doc)
        self.assertEqual(cm.exception.code, 4)
        self.assertEqual(seen, [hs.OPEN_ARG, ""])             # 옵션 인자 → 빈 인자 순서로 재시도

    def test_open_fallback_success(self):
        fake = FakeHwp(open_ok=lambda p, f, a: a == "")
        s, _ = session(fake)
        with s:
            s.open(self.doc)
            self.assertEqual(s.open_arg_used, "")

    def test_missing_file_code2(self):
        s, _ = session(FakeHwp())
        with s, self.assertRaises(hs.PreconditionError):
            s.open(self.tmp / "nope.hwpx")

    def test_export_hwpml_fixes_decl(self):                  # F-034 음성대조: 고치기 전엔 파서가 거부
        fake = FakeHwp()
        fake.texts = ["SYN_X"]
        s, _ = session(fake)
        with s:
            raw = fake.GetTextFile("HWPML2X", "")
            with self.assertRaises(ET.ParseError):
                ET.fromstring(raw.encode("utf-8"))
            x = s.export_hwpml()
        self.assertEqual(ET.fromstring(x.encode("utf-8")).tag, "HWPML")
        self.assertNotIn("UTF-16", x)

    def test_unsupported_export_refused(self):               # F-047
        fake = FakeHwp()
        s, _ = session(fake)
        with s:
            with self.assertRaises(ValueError):
                s.export("HWPX")
        self.assertNotIn(("GetTextFile", "HWPX"), fake.log)

    def test_timeout_kills_only_own_pid_code5(self):         # F-019
        fake = FakeHwp(slow_export=1.2)
        s, st = session(fake, timeout=1)
        with s:
            with self.assertRaises(hs.TimeoutKilled) as cm:
                s.export_hwpml()
            self.assertEqual(cm.exception.code, 5)
            with self.assertRaises(hs.TimeoutKilled):        # 이후 호출도 막힌다
                s.export_text()
        self.assertEqual(st["killed"], [4242])
        self.assertNotIn(("Quit",), fake.log)                # 죽은 프로세스에 Quit 를 부르지 않음

    def test_no_pid_disables_watchdog(self):
        msgs = []
        s, st = session(FakeHwp(slow_export=0.2), timeout=0.05, new_pid=None, log=msgs.append)
        with s:
            s.export_hwpml()                                 # 감시 꺼짐 → 시간초과 없이 끝남
        self.assertEqual(st["killed"], [])
        self.assertTrue(any("PID" in m for m in msgs))

    def test_close_discards_and_quits(self):
        fake = FakeHwp()
        s, _ = session(fake)
        with s:
            pass
        self.assertIn(("Clear", 1), fake.log)
        self.assertIn(("Quit",), fake.log)

    def test_fix_decl_variants(self):
        self.assertEqual(hs.fix_decl(""), "")
        self.assertTrue(hs.fix_decl("﻿" + DECL16 + "<A/>").startswith('<?xml version="1.0" encoding="UTF-8"?><A/>'))
        self.assertEqual(hs.fix_decl("﻿<A/>"), "<A/>")

    def test_head_kind(self):
        p = self.tmp / "h.bin"
        for data, kind in ((b"BMS DocuRay\x03", "DOCURAY"), (b"PK\x03\x04xx", "PLAIN_ZIP"),
                           (b"\xd0\xcf\x11\xe0xx", "PLAIN_OLE2"), (b"", "EMPTY")):
            p.write_bytes(data)
            self.assertEqual(hs.head_kind(p), kind)


if __name__ == "__main__":
    unittest.main()
