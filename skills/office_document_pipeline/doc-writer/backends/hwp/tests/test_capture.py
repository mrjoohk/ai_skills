"""스키마 채취 스크립트 흐름 시험 (가짜 COM). 실제 한/글 동작은 사용자 PC 실행으로 확인한다."""
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL / "dev"))
sys.path.insert(0, str(HERE))
import hwp_session as hs          # noqa: E402
import capture_hwpml as cap       # noqa: E402
from fake_hwp import FakeHwp, FakeProcs, make_env, SYN_FULL_HWPML   # noqa: E402

REAL_LIKE = ('<STYLE Id="0" Name="바탕글" EngName="Normal"/><STYLE Id="2" Name="개요 1"/>'
             '<P><TEXT><CHAR>비밀 본문</CHAR></TEXT></P>'
             '<TABLE RowCount="2" ColCount="2"><ROW><CELL ColAddr="0" RowAddr="0" ColSpan="2" RowSpan="1">'
             '<PARALIST><P><TEXT><CHAR>셀 비밀</CHAR></TEXT></P></PARALIST></CELL></ROW></TABLE>'
             '<FIELDBEGIN Type="Memo" Name="숨은이름"/><CELL Name="AB12x"/><BOOKMARK Name="52"/>')


class TestCapture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.fix = self.tmp / "fixtures"
        self._orig = (cap.FIXTURES, hs.HwpSession)
        cap.FIXTURES = self.fix

    def tearDown(self):
        cap.FIXTURES, hs.HwpSession = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def patch(self, make_fake):
        orig = self._orig[1]

        def factory(**kw):
            d, p, k, _ = make_env(make_fake())
            return orig(dispatch=d, pids=p, killer=k, **kw)
        hs.HwpSession = factory

    def patch_procs(self, procs, make_fake):
        orig = self._orig[1]

        def factory(**kw):
            d, p, k = procs.env(make_fake())
            return orig(dispatch=d, pids=p, killer=k, sleep=lambda t: None, **kw)
        hs.HwpSession = factory

    def test_synthetic_fixture_written(self):
        self.patch(lambda: FakeHwp(hwpml=SYN_FULL_HWPML))
        code = cap.main(["--skip-vocab", "--work", str(self.tmp)])
        self.assertEqual(code, 0)
        md = (self.fix / "synthetic_hwpml.md").read_text(encoding="utf-8")
        xml = re.search(r"````xml\n(.*)\n````", md, re.S).group(1)
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        for marker in ("SYN_H1", "SYN_A_R2C0", "SYN_N_R0C1", "SYN_B_R2C2", "SYN_HEADER", "SYN_END"):
            self.assertIn(marker, xml)
        self.assertIn("SYN_FIELD_A", md)                       # 필드 목록
        self.assertTrue((self.tmp / "syn_fixture.hwpx").exists())
        self.assertIn("DOCURAY", md)

    def test_structure_checked_not_run_return(self):         # F-062: 단계는 OK 여도 구조가 없으면 1
        self.patch(lambda: FakeHwp())                         # 가짜 HWPML 에는 병합·머리말이 없다
        code = cap.main(["--skip-vocab", "--work", str(self.tmp)])
        self.assertEqual(code, 1)
        md = (self.fix / "synthetic_hwpml.md").read_text(encoding="utf-8")
        self.assertIn("| table_b_merge | OK |", md)
        self.assertRegex(md, r"\| merge_h \| [^|]+ \| MISSING \|")

    def test_header_footer_step_uses_setitem(self):          # F-063
        self.patch(lambda: FakeHwp(hwpml=SYN_FULL_HWPML))
        cap.main(["--skip-vocab", "--work", str(self.tmp)])
        md = (self.fix / "synthetic_hwpml.md").read_text(encoding="utf-8")
        row = [l for l in md.splitlines() if l.startswith("| header_footer |")][0]
        self.assertIn("| OK |", row)
        self.assertIn("HeaderFooter.HeaderFooterCtrlType", row)

    def test_header_footer_failure_keeps_body_clean(self):
        fake = FakeHwp(hwpml=SYN_FULL_HWPML, fail_actions={"HeaderFooter"})
        self.patch(lambda: fake)
        cap.main(["--skip-vocab", "--work", str(self.tmp)])
        self.assertIn("SYN_END 마지막 문단", fake.inserted)   # 다른 단계는 계속 진행됐고
        self.assertNotIn("SYN_HEADER", fake.inserted)        # 실패한 머리말 표지는 본문에 쓰지 않았다

    def test_check_synthetic_on_real_fixture(self):          # 실측 픽스처: Run 반환 False 였지만 병합은 됐다
        real = HERE / "fixtures" / "synthetic_hwpml.md"
        if not real.exists():
            self.skipTest("실측 픽스처 없음")
        x = re.search(r"````xml\n(.*)\n````", real.read_text(encoding="utf-8"), re.S).group(1)
        ch = cap.check_synthetic(x)
        for k in ("merge_h", "merge_v", "nested_table", "cell_field_named", "clickhere_named", "memo", "footnote"):
            self.assertTrue(ch[k], k)

    def test_vocab_reuses_one_session(self):                 # F-061: 문서마다 세션을 새로 띄우지 않는다
        procs = FakeProcs(linger=3)
        files = []
        for i in range(3):
            f = self.tmp / ("T%d.hwpx" % i)
            f.write_bytes(b"BMS DocuRay\x03\x01")
            files.append(str(f))
        self.patch_procs(procs, lambda: FakeHwp(hwpml_body=REAL_LIKE))
        code = cap.main(["--skip-synthetic", "--vocab"] + files + ["--work", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertEqual(len(procs.spawned), 1)
        self.assertEqual(procs.pids(), set())                 # 끝나면 내 Hwp.exe 도 끝나 있다

    def test_failed_step_recorded_not_fatal(self):
        self.patch(lambda: FakeHwp(fail_actions={"TableMergeCell"}))
        code = cap.main(["--skip-vocab", "--work", str(self.tmp)])
        self.assertEqual(code, 1)                               # 일부 실패 → 1, 그래도 정답지는 남는다
        md = (self.fix / "synthetic_hwpml.md").read_text(encoding="utf-8")
        self.assertIn("| table_b_merge | FAIL |", md)
        self.assertIn("| table_a_nested_cellfield | OK |", md)

    def test_vocab_has_no_body_text_or_names(self):            # 본문·필드 이름이 새지 않는다
        src = self.tmp / "T.hwpx"
        src.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 32)
        self.patch(lambda: FakeHwp(hwpml_body=REAL_LIKE))
        code = cap.main(["--skip-synthetic", "--vocab", str(src), "--work", str(self.tmp)])
        self.assertEqual(code, 0)
        md = (self.fix / "template_vocab.md").read_text(encoding="utf-8")
        for secret in ("비밀 본문", "셀 비밀", "숨은이름", "AB12x", '"52"'):   # 짧은 영숫자 이름도 (검토 16)
            self.assertNotIn(secret, md)
        self.assertIn('"ColSpan"', md)
        self.assertIn('"CELL>PARALIST"', md)                   # 부모>자식 요소 쌍
        self.assertIn('"Memo"', md)                            # 짧은 영숫자 값은 남는다
        self.assertIn("개요 1", md)                             # 스타일 이름은 남는다
        self.assertIn("| T.hwpx |", md)

    def test_vocab_open_failure_counted(self):
        src = self.tmp / "T.hwpx"
        src.write_bytes(b"x")
        self.patch(lambda: FakeHwp(open_ok=False))
        code = cap.main(["--skip-synthetic", "--vocab", str(src), "--work", str(self.tmp)])
        self.assertEqual(code, 1)
        md = (self.fix / "template_vocab.md").read_text(encoding="utf-8")
        self.assertIn("FAIL: OpenFailed", md)


if __name__ == "__main__":
    unittest.main()
