"""끼워 넣기(insert_doc.py, P-052) 시험 — 가짜 COM·합성 문서. 가짜의 끼워 넣기·문단 끝 선택 지우기·캡션 자동 번호는
실측 PoC(21.p052_insert_poc.bat, logs/P-052_evidence/insert_poc_report.md)의 결과 꼴을 흉내 낸다."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "backends" / "hwp" / "tests"))
sys.path.insert(0, str(TOOLS / "hwpx-drm" / "tests"))
import insert_doc as ins          # noqa: E402
import hwp_session as hs          # noqa: E402
import hwpx_api as api            # noqa: E402
from fake_hwp import FakeHwp, make_env, DECL16   # noqa: E402

STYLES = ["바탕글", "03_본문_내용", "04_도표그림_제목"] + ["COMSAF 개요 %d" % i for i in range(1, 8)] + ["개요 1"]
SRC_STYLES = ["바탕글", "개요 1", "개요 2", "캡션"]
BODY, FIG = 1, 2
ANCHOR = "작업의 종료"


def H(n):
    return STYLES.index("COMSAF 개요 %d" % n)


def P(text="", style=0, styles=STYLES):
    ps = 0
    if styles[style].startswith("COMSAF"):
        ps = int(styles[style][-1])
    elif styles[style].startswith("개요"):
        ps = int(styles[style][-1])
    return '<P ParaShape="%d" Style="%d"><TEXT CharShape="0"><CHAR>%s</CHAR></TEXT></P>' % (ps, style, text)


def PIC(n, title, style=FIG, cap_style=FIG):
    cap = ('<CAPTION Side="Bottom"><PARALIST><P ParaShape="0" Style="%d"><TEXT CharShape="0"><CHAR>그림 </CHAR>'
           '<AUTONUM Number="%d" NumberType="Figure"/><CHAR> %s</CHAR></TEXT></P></PARALIST></CAPTION>' % (cap_style, n, title))
    return ('<P ParaShape="0" Style="%d"><TEXT CharShape="0"><PICTURE><SHAPEOBJECT NumberingType="Figure">'
            '<SIZE Width="14600" Height="8760"/>%s</SHAPEOBJECT></PICTURE></TEXT></P>' % (style, cap))


def doc(paras, styles=STYLES):
    st = "".join('<STYLE Id="%d" Name="%s" ParaShape="%d"/>' % (i, n, int(n[-1]) if n.startswith(("COMSAF", "개요")) else 0)
                 for i, n in enumerate(styles))
    ps = '<PARASHAPE Id="0" HeadingType="None" Level="0"/>' + "".join(
        '<PARASHAPE Id="%d" HeadingType="Outline" Level="%d"/>' % (k + 1, k) for k in range(7))
    return (DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="1"><MAPPINGTABLE><STYLELIST>%s</STYLELIST>'
            '<PARASHAPELIST>%s</PARASHAPELIST></MAPPINGTABLE></HEAD><BODY><SECTION Id="0">%s</SECTION></BODY></HWPML>'
            % (st, ps, "".join(paras)))


def target_doc(anchor=ANCHOR, extra=()):
    return doc([P("개요", H(1)), P("사용법", H(2)), P("통제", H(3)), P("앞 절", H(4)), P("1) 하나", BODY),
                PIC(1, "앞 그림"), P("본문에 그림 1 과 그림 2 를 본다.", BODY), P("8) 끝", BODY), P(anchor, H(2)),
                P("뒤", BODY), PIC(2, "뒤 그림")] + list(extra))


SRC = doc([P("고장 이벤트", 1, SRC_STYLES), P("단계 하나", 2, SRC_STYLES), PIC(1, "고장 버튼", 0, 3), P("", 0, SRC_STYLES),
           P("단계 둘", 2, SRC_STYLES), PIC(2, "할당 창", 0, 3), P("", 0, SRC_STYLES)], SRC_STYLES)

SPEC = '''<!-- 시험 명세 -->
#### 새 절
1) 첫 단계.
![고장 버튼](hwpx:src/고장.hwpx#1 "51.5x30.9")
2) 둘째 단계.
![할당 창](hwpx:src/고장.hwpx#2)
'''


class TestParse(unittest.TestCase):
    def test_blocks(self):
        b = ins.parse_blocks(SPEC)
        self.assertEqual([x["kind"] for x in b], ["heading", "para", "figure", "para", "figure"])
        self.assertEqual((b[2]["src"], b[2]["k"], b[2]["size"]), ("src/고장.hwpx", 1, [51.5, 30.9]))
        self.assertEqual(b[0]["level"], 4)

    def test_rejects(self):
        figs = ("![a](img/a.png)", "![a](hwpx:../x.hwpx#1)", "![a](hwpx:bridge/x.hwpx#1)", "![a](hwpx:K:/x.hwpx#1)",
                "![a](hwpx:src/x.docx#1)", "![a](hwpx:src/x.hwpx#0)", "![](hwpx:src/x.hwpx#1)",
                # 꼴이 틀린 그림 줄(검토 D1-02) — 본문 글자로 들어가지 않고 명세 오류
                " ![a](hwpx:src/x.hwpx#1)", '![a](hwpx:src/x.hwpx#1 "51,5x30")', "![a](hwpx:src/x.hwpx#1)。",
                '![a](hwpx:src/x.hwpx#1 "5x3" )',
                # 그림 출처 대소문자·'#'(D1-06)
                "![a](hwpx:Bridge/q/x.hwpx#1)", "![a](hwpx:.GIT/x.hwpx#1)", "![a](hwpx:src/a#b.hwpx#1)")
        bads = ("| a | b |", "> 작성 필요", "표: 캡션", "{{그림:x}} 를 본다", "<!-- 빈 -->", "####새 절",
                # 첫 블록 그림·그림 연속(D1-05)
                "![a](hwpx:src/x.hwpx#1)\n1) 단계", "1) 단계\n![a](hwpx:src/x.hwpx#1)\n![b](hwpx:src/x.hwpx#2)")
        ins.parse_blocks("1) 단계\n![a](hwpx:src/x.hwpx#1 \"5.5x3\")")             # 양성 대조: 글자 문단 뒤 그림 하나
        for bad in bads + tuple("1) 단계\n" + f for f in figs):
            with self.subTest(bad=bad), self.assertRaises(ins.SpecError):
                ins.parse_blocks(bad)


class TestPure(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(ins.numbers([1, 2, 3, 3, 2, 1, 2]), ["1", "1.1", "1.1.1", "1.1.2", "1.2", "2", "2.1"])
        self.assertEqual(ins.digits("4.3.4.2.6."), "4.3.4.2.6")

    def test_outside_same(self):
        a = [("text", "s", "a"), ("text", "s", "b")]
        self.assertIsNone(ins.outside_same(a, a[:1] + [("text", "x", "n")] + a[1:], 1, 1))
        self.assertIsNotNone(ins.outside_same(a, a[:1] + [("text", "x", "n")] + a[1:], 2, 1))
        self.assertIsNotNone(ins.outside_same(a, a + [("text", "x", "n")], 1, 2))

    def test_captions_shift(self):
        b = [("그림", 1, "가"), ("표", 1, "t"), ("그림", 2, "나")]
        a = [("그림", 1, "가"), ("표", 1, "t"), ("그림", 2, "새"), ("그림", 3, "나")]
        self.assertEqual(ins.captions_shift(b, a, 2, ["새"]), [])
        self.assertTrue(ins.captions_shift(b, a[:2] + [("그림", 2, "다른")] + a[3:], 2, ["새"]))
        self.assertTrue(ins.captions_shift(b, a[:3] + [("그림", 2, "나")], 2, ["새"]))
        self.assertTrue(ins.captions_shift(b, a[:1] + [("표", 2, "t")] + a[2:], 2, ["새"]))


class TestInsert(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target = self.tmp / "대상.hwpx"
        self.target.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 32)
        (self.tmp / "src").mkdir()
        (self.tmp / "src" / "고장.hwpx").write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 32)
        self.out = self.tmp / "out" / "결과.hwpx"
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_insert(self, spec=SPEC, target=None, fake_kw=None, before=ANCHOR, patch=None):
        fake = FakeHwp(docs={"대상.hwpx": target or target_doc(), "고장.hwpx": SRC}, **(fake_kw or {}))
        d, p, k, _ = make_env(fake)
        sess = hs.HwpSession(dispatch=d, pids=p, killer=k, sleep=lambda t: None)
        blocks = ins.parse_blocks(spec)
        with mock.patch.object(ins, "ROOT", self.tmp), mock.patch.object(api.HwpxSession, "__init__",
                                                                          _init_with(sess)):
            ctx = [mock.patch.object(ins, n, f) for n, f in (patch or {}).items()]
            for c in ctx:
                c.start()
            try:
                with api.HwpxSession() as s:
                    rec = ins.insert(s, self.target, blocks, before, self.out, log=lambda m: None)
            finally:
                for c in ctx:
                    c.stop()
        return rec, fake

    def test_ok(self):
        rec, fake = self.run_insert()
        self.assertTrue(rec["ok"], rec.get("error"))
        self.assertTrue(self.out.exists())
        self.assertEqual(rec["first_new_figure"], 2)
        self.assertEqual(rec["check"]["added"], 5)
        self.assertEqual(rec["headings"]["new"], {8: "1.1.1.2."})         # 앞 절 1.1.1.1 다음 (앵커 루트 8)
        self.assertEqual(rec["headings"]["mismatch"], [])
        x = fake.docs["결과.hwpx"]
        self.assertEqual(x.count("<PICTURE"), 4)
        self.assertIn("+개요 2", rec["styles_changed"])                      # 출처 스타일이 더해짐 — 경고
        self.assertTrue(any("스타일이 더해졌다" in w for w in rec["warnings"]))
        self.assertEqual(rec["literal_refs"], [("s0.p6", "본문에 그림 1 과 그림 2 를 본다.")])

    def test_caption_title_mismatch_not_saved(self):
        rec, _ = self.run_insert(SPEC.replace("![할당 창]", "![다른 창]"))
        self.assertFalse(rec["ok"])
        self.assertIn("그림 캡션", rec["error"])
        self.assertFalse(self.out.exists())

    def test_outside_change_not_saved(self):
        orig = ins.keep_only_picture

        def greedy(s, first, last, k):                                  # 마지막 그림에서 앵커 제목까지 지우는 잘못된 범위
            return orig(s, first, last + 1 if k == 2 else last, k)
        rec, _ = self.run_insert(patch={"keep_only_picture": greedy})
        self.assertFalse(rec.get("ok"))
        self.assertIn("넣은 곳 밖이 바뀌었다", rec["error"])
        self.assertFalse(self.out.exists())

    def test_caption_style_not_saved(self):
        rec, _ = self.run_insert(patch={"restyle_caption": lambda s, idx, root, style: [1, 0, 0]})
        self.assertFalse(rec["ok"])
        self.assertIn("그림 캡션 스타일", rec["error"])
        self.assertFalse(self.out.exists())

    def test_heading_number_not_saved(self):
        orig = ins.wd.heading_string
        calls = []

        def wrong(s, para):                                             # 쓴 뒤 읽기에서 새 제목만 다른 번호
            v = orig(s, para)
            calls.append(para)
            return "9.9." if v == "1.1.1.2." else v
        with mock.patch.object(ins.wd, "heading_string", wrong):
            rec, _ = self.run_insert()
        self.assertFalse(rec["ok"])
        self.assertIn("개요 번호", rec["error"])
        self.assertFalse(self.out.exists())

    def test_other_level(self):
        rec, _ = self.run_insert(SPEC.replace("#### 새 절", "### 새 절"))   # 명세 수준 3
        self.assertTrue(rec["ok"], rec.get("error"))                        # 수준 3 도 문서 셈과 맞으면 저장(번호 1.1.2)
        self.assertEqual(rec["headings"]["new"], {8: "1.1.2."})

    def test_new_para_text_not_saved(self):
        orig = ins.wd.insert_text

        def typo(s, text):
            return orig(s, text + "X" if text == "1) 첫 단계." else text)
        with mock.patch.object(ins.wd, "insert_text", typo):
            rec, _ = self.run_insert()
        self.assertFalse(rec["ok"])
        self.assertIn("넣은 문단이 명세와 다르다", rec["error"])

    def test_side_effects_not_saved(self):
        """끼워 넣기가 넣은 곳 밖의 표 칸·머리말·스타일 정의·새 번호 조판을 바꾸면 저장하지 않는다(가짜에 부작용을 심는다)."""
        table = ('<P ParaShape="0" Style="0"><TEXT CharShape="0"><TABLE ColCount="1" RowCount="1"><ROW><CELL ColAddr="0" '
                 'RowAddr="0" RowSpan="1" ColSpan="1"><PARALIST>%s</PARALIST></CELL></ROW></TABLE></TEXT></P>' % P("칸 글자"))
        head = '<HEADER ApplyPageType="Both"><PARALIST>%s</PARALIST></HEADER>' % P("머리 글자")
        tgt = target_doc(extra=[table]).replace("<CHAR>개요</CHAR>", head + "<CHAR>개요</CHAR>", 1)
        ps9 = '<PARASHAPE Id="0" HeadingType="None" Level="0"/><PARASHAPE Id="99" HeadingType="None" Level="0" Align="Center"/>'
        cases = (("칸 글자", "칸 글자X", "표 칸"), ("머리 글자", "머리 글자X", "머리말"),
                 ([('<PARASHAPE Id="0" HeadingType="None" Level="0"/>', ps9),
                   ('<P ParaShape="0" Style="1"><TEXT CharShape="0"><CHAR>뒤</CHAR>',
                    '<P ParaShape="99" Style="1"><TEXT CharShape="0"><CHAR>뒤</CHAR>')], None, "서식(정렬"),
                 ('<STYLE Id="1" Name="03_본문_내용" ParaShape="0"/>', '<STYLE Id="1" Name="03_본문_내용" ParaShape="1"/>',
                  "기존 스타일"),
                 ("<CHAR>뒤</CHAR>", '<NEWNUM Number="7" NumberType="Figure"/><CHAR>뒤</CHAR>', "새 번호"))
        for a, b, what in cases:
            with self.subTest(what=what):
                orig = ins.insert_file

                def side(s, path, a=a, b=b):
                    ok = orig(s, path)
                    for x, y in (a if isinstance(a, list) else [(a, b)]):
                        s.hwp.hwpml = s.hwp.hwpml.replace(x, y, 1)
                    return ok
                rec, _ = self.run_insert(target=tgt, patch={"insert_file": side})
                self.assertFalse(rec["ok"])
                self.assertIn(what, rec["error"])
                self.assertFalse(self.out.exists())
        rec, _ = self.run_insert(target=tgt)                              # 양성 대조: 부작용이 없으면 저장
        self.assertTrue(rec["ok"], rec.get("error"))

    def test_new_heading_unread_not_saved(self):
        orig = ins.wd.heading_string

        def unread(s, para):
            v = orig(s, para)
            return None if v == "1.1.1.2." else v                       # 넣은 제목만 못 읽음(검토 D1-03)
        with mock.patch.object(ins.wd, "heading_string", unread):
            rec, _ = self.run_insert()
        self.assertFalse(rec["ok"])
        self.assertIn("개요 번호를 읽지 못했다", rec["error"])
        self.assertFalse(self.out.exists())

    def test_pre_mismatch_excluded_new_still_checked(self):
        """쓰기 전부터 수준 셈과 다른 제목은 빼고 경고 — 넣은 제목은 그래도 대조한다(검토 D1-08)."""
        orig = ins.wd.heading_string

        def odd(s, para):
            v = orig(s, para)
            return "7.7." if v == "1.1." else v                         # 기존 제목 '사용법' 이 처음부터 다르게 읽힘
        with mock.patch.object(ins.wd, "heading_string", odd):
            rec, _ = self.run_insert()
        self.assertTrue(rec["ok"], rec.get("error"))
        self.assertTrue(any("이미 수준 셈과 다른 제목 1개" in w for w in rec["warnings"]))
        self.out.unlink()

        def odd_new(s, para):
            v = orig(s, para)
            return "7.7." if v in ("1.1.", "1.1.1.2.") else v
        with mock.patch.object(ins.wd, "heading_string", odd_new):
            rec, _ = self.run_insert()
        self.assertFalse(rec["ok"])
        self.assertIn("개요 번호", rec["error"])

    def test_preconditions(self):
        tbl = ('<P ParaShape="0" Style="0"><TEXT CharShape="0"><TABLE ColCount="1" RowCount="1"><ROW><CELL ColAddr="0" '
               'RowAddr="0" RowSpan="1" ColSpan="1"><PARALIST>%s</PARALIST></CELL></ROW></TABLE></TEXT></P>' % P("칸"))
        first = doc([P(ANCHOR, H(1)), P("뒤", BODY)])
        after_table = doc([P("개요", H(1)), tbl, P(ANCHOR, H(2))])
        for tgt, why in ((first, "첫 문단"), (after_table, "표")):
            with self.subTest(why=why), self.assertRaises(ins.SpecError) as cm:
                self.run_insert(target=tgt)
            self.assertIn("앞 문단", str(cm.exception))

    def test_unverified_save_is_moved(self):
        def open_ok(path, fmt, arg):
            return not str(path).endswith("결과.hwpx")                  # 저장한 결과를 다시 열지 못함(검토 D1-07)
        rec, _ = self.run_insert(fake_kw={"open_ok": open_ok})
        self.assertFalse(rec["ok"])
        self.assertIn("저장 확인 실패", rec["error"])
        self.assertFalse(self.out.exists())
        self.assertTrue(self.out.with_name("결과.unverified.hwpx").exists())

    def test_missing_picture(self):
        with self.assertRaises(api.EditFailed):
            self.run_insert(SPEC.replace("#2)", "#3)"))
        self.assertFalse(self.out.exists())

    def test_caption_not_entered(self):
        orig = FakeHwp._attach_caption
        with mock.patch.object(FakeHwp, "_attach_caption", lambda self: None), self.assertRaises(api.EditFailed):
            self.run_insert()
        self.assertIs(FakeHwp._attach_caption, orig)
        self.assertFalse(self.out.exists())

    def test_anchor(self):
        for tgt, before in ((target_doc(), "없는 제목"), (target_doc(extra=[P(ANCHOR, H(2))]), ANCHOR)):
            with self.subTest(before=before), self.assertRaises(ins.SpecError):
                self.run_insert(target=tgt, before=before)

    def test_plaintext_save(self):
        rec, _ = self.run_insert(fake_kw={"save_head": b"PK\x03\x04"})
        self.assertFalse(rec["ok"])
        self.assertEqual(rec.get("code"), 3)


def _init_with(sess):
    orig = api.HwpxSession.__init__

    def init(self, *a, **kw):
        orig(self, session=sess)
    return init


class TestMain(unittest.TestCase):
    def test_out_exists(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        t, o, sp = tmp / "t.hwpx", tmp / "o.hwpx", tmp / "s.md"
        for f in (t, o):
            f.write_bytes(b"x")
        sp.write_text(SPEC, encoding="utf-8")
        self.assertEqual(ins.main([str(t), "--spec", str(sp), "--before", ANCHOR, "--out", str(o),
                                   "--report", str(tmp / "r.md")]), 2)
        self.assertIn("덮어쓰지 않는다", (tmp / "r.md").read_text(encoding="utf-8"))

    def test_spec_error_report(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        t, sp = tmp / "t.hwpx", tmp / "s.md"
        t.write_bytes(b"x")
        sp.write_text("| a |", encoding="utf-8")
        self.assertEqual(ins.main([str(t), "--spec", str(sp), "--before", ANCHOR, "--out", str(tmp / "o.hwpx"),
                                   "--report", str(tmp / "r.md")]), 2)
        self.assertIn("FAIL", (tmp / "r.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
