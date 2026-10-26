"""그림 꾸러미(figure_pack.py, P-052) 시험 — 가짜 COM·합성 문서. 지우기 길(문단 끝 선택·문서 끝 지우기)은 실측 PoC I1·S1 꼴."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "backends" / "hwp" / "tests"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "hwpx-drm" / "tests"))
import figure_pack as fp          # noqa: E402
import insert_doc as ins          # noqa: E402
import hwp_session as hs          # noqa: E402
import hwpx_api as api            # noqa: E402
import test_insert as ti          # noqa: E402
from fake_hwp import FakeHwp, make_env   # noqa: E402

S = ti.SRC_STYLES
SRC = ti.doc([ti.P("고장 이벤트", 1, S), ti.P("단계 하나", 2, S), ti.PIC(1, "고장 버튼", 0, 3), ti.P("", 0, S),
              ti.P("단계 둘", 2, S), ti.PIC(2, "할당 창", 0, 3), ti.P("글과 그림 섞임", 2, S), ti.PIC(3, "확인 창", 0, 3),
              ti.P("끝", 0, S)], S)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "출처.hwpx"
        self.src.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 32)
        self.out = self.tmp / "pack"

    def session(self, fake):
        d, p, k, _ = make_env(fake)
        return api.HwpxSession(session=hs.HwpSession(dispatch=d, pids=p, killer=k, sleep=lambda t: None))

    def run_pack(self, src=SRC, only=None, fake_kw=None):
        fake = FakeHwp(docs={"출처.hwpx": src}, **(fake_kw or {}))
        with self.session(fake) as s:
            rec = fp.pack(s, self.src, self.out, only, log=lambda m: None)
        return rec, fake


class TestPure(unittest.TestCase):
    def test_root_pictures(self):
        rp = fp.root_pictures(SRC)
        self.assertEqual([len(p) for p in rp], [0, 0, 1, 0, 0, 1, 0, 1, 0])
        self.assertEqual(rp[2], [("고장버튼", (51.5, 30.9))])


class TestPack(Base):
    def test_ok(self):
        rec, fake = self.run_pack()
        self.assertTrue(rec["ok"], rec.get("error"))
        self.assertEqual([f["title"] for f in rec["figures"]], ["고장버튼", "할당창", "확인창"])
        self.assertEqual([f["file"] for f in rec["files"]], ["fig01.hwpx", "fig02.hwpx", "fig03.hwpx"])
        for name in ("all.hwpx", "fig01.hwpx", "fig02.hwpx", "fig03.hwpx"):
            self.assertTrue((self.out / name).exists(), name)
        x = fake.docs["fig02.hwpx"]
        self.assertEqual(x.count("<PICTURE"), 1)
        self.assertIn("할당 창", x)
        self.assertNotIn("단계 둘", x)                                   # 글 문단은 남지 않는다(첫 문단 그릇만)
        self.assertEqual(fake.docs["all.hwpx"].count("<PICTURE"), 3)

    def test_mixed_paragraph_skipped(self):
        mixed = ti.PIC(9, "섞인 그림", 0, 3).replace('<TEXT CharShape="0"><PICTURE>', '<TEXT CharShape="0"><CHAR>글</CHAR><PICTURE>')
        src = SRC.replace(ti.P("끝", 0, S), mixed + ti.P("끝", 0, S))
        rec, _ = self.run_pack(src)
        self.assertTrue(rec["ok"], rec.get("error"))
        self.assertEqual(len(rec["figures"]), 3)
        self.assertTrue(any("담지 않은 그림 1개" in w for w in rec["warnings"]), rec["warnings"])

    def test_only(self):
        rec, _ = self.run_pack(only=[2])
        self.assertTrue(rec["ok"], rec.get("error"))
        self.assertEqual([f["file"] for f in rec["files"]], ["fig02.hwpx"])
        self.assertFalse((self.out / "fig01.hwpx").exists())
        with self.assertRaises(fp.PackError):
            Base.setUp(self)
            self.run_pack(only=[4])

    def test_first_paragraph_picture_refused(self):
        with self.assertRaises(fp.PackError):
            self.run_pack(ti.doc([ti.PIC(1, "첫 그림", 0, 3), ti.P("뒤", 0, S)], S))

    def test_no_picture_refused(self):
        with self.assertRaises(fp.PackError):
            self.run_pack(ti.doc([ti.P("글", 0, S)], S))

    def test_wrong_delete_not_saved(self):
        """지우기가 그림을 잘못 남기면(남은 그림이 다름) 그 파일은 요청한 이름으로 남지 않는다."""
        orig = fp.tail_delete

        def off_by_one(s, a, b):                                     # 그림 하나를 덜 지움
            return orig(s, a, b - 1) if b - 1 > a else None
        with mock.patch.object(fp, "tail_delete", off_by_one):
            rec, _ = self.run_pack()
        self.assertFalse(rec["ok"])
        self.assertIn("그림", rec["error"])
        bad = [p.name for p in self.out.iterdir()]
        self.assertTrue(any(n.endswith(".unverified.hwpx") for n in bad), bad)

    def test_caption_change_not_saved(self):
        orig = fp.delete_after

        def side(s, a):
            orig(s, a)
            s.hwp.hwpml = s.hwp.hwpml.replace("할당 창", "다른 창")
        with mock.patch.object(fp, "delete_after", side):
            rec, _ = self.run_pack()
        self.assertFalse(rec["ok"])
        self.assertIn("캡션 제목", rec["error"])

    def test_extra_content_not_saved(self):
        """남은 문서에 그림이 더 있거나(첫 문단 안)·그림 크기가 바뀌거나·그림 문단 밖 문단이 남으면 저장하지 않는다 — 대조 따로."""
        orig = fp.delete_after
        extra_pic = ti.PIC(7, "덤", 0, 3)[len('<P ParaShape="0" Style="0"><TEXT CharShape="0">'):-len('</TEXT></P>')]
        cases = (("<CHAR>고장 이벤트</CHAR>", "<CHAR>고장 이벤트</CHAR>" + extra_pic, "그림 수"),
                 ('<SIZE Width="14600" Height="8760"/>', '<SIZE Width="14600" Height="9760"/>', "크기"),
                 ("</SECTION>", '<P ParaShape="0" Style="0"><TEXT CharShape="0"/></P></SECTION>', "그림 문단만"))
        for a, b, why in cases:
            with self.subTest(why=why):
                Base.setUp(self)

                def side(s, k, a=a, b=b):
                    orig(s, k)
                    s.hwp.hwpml = s.hwp.hwpml.replace(a, b, 1)
                with mock.patch.object(fp, "delete_after", side):
                    rec, _ = self.run_pack()
                self.assertFalse(rec["ok"])
                self.assertIn(why, rec["error"])

    def test_plaintext(self):
        with self.assertRaises(api.PlaintextSaved):
            self.run_pack(fake_kw={"save_head": b"PK\x03\x04"})


class TestWithInsert(Base):
    def test_insert_uses_pack_file(self):
        """꾸러미 파일(그림 하나)로 끼워 넣기 — 큰 출처 대신."""
        rec, fake = self.run_pack(only=[2])
        self.assertTrue(rec["ok"], rec.get("error"))
        spec = "#### 새 절\n1) 단계.\n![할당 창](hwpx:pack/fig02.hwpx#1)\n"
        target = self.tmp / "대상.hwpx"
        target.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 32)
        fake2 = FakeHwp(docs={"대상.hwpx": ti.target_doc(), "fig02.hwpx": fake.docs["fig02.hwpx"]})
        with mock.patch.object(ins, "ROOT", self.tmp), self.session(fake2) as s:
            r = ins.insert(s, target, ins.parse_blocks(spec), ti.ANCHOR, self.tmp / "결과.hwpx", log=lambda m: None)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["steps"][0]["inserted_roots"], 1)            # 첫 문단 + 그림 하나만 끼웠다


class TestMain(unittest.TestCase):
    def test_preconditions(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "s.hwpx").write_bytes(b"x")
        (tmp / "exists").mkdir()
        self.assertEqual(fp.main([str(tmp / "none.hwpx"), "--out-dir", str(tmp / "o"), "--report", str(tmp / "r.md")]), 2)
        self.assertEqual(fp.main([str(tmp / "s.hwpx"), "--out-dir", str(tmp / "exists"), "--report", str(tmp / "r.md")]), 2)
        self.assertIn("이미 있다", (tmp / "r.md").read_text(encoding="utf-8"))
        self.assertEqual(fp.main([str(tmp / "s.hwpx"), "--out-dir", str(tmp / "o"), "--only", "1;2",
                                  "--report", str(tmp / "r.md")]), 2)


if __name__ == "__main__":
    unittest.main()
