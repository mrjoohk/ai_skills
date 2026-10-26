"""UF-03 HWPML 파서 시험. 정답지 = 한/글이 만든 합성 문서의 실제 HWPML (tests/fixtures/synthetic_hwpml.md)."""
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import hwpml_parse as hp          # noqa: E402
from fake_hwp import DECL16, SYN_FULL_HWPML   # noqa: E402

FIX = HERE / "fixtures" / "synthetic_hwpml.md"


def real_xml():
    return re.search(r"````xml\n(.*)\n````", FIX.read_text(encoding="utf-8"), re.S).group(1)


def doc(body, head=""):
    return (DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="1">%s</HEAD><BODY><SECTION Id="0">%s</SECTION></BODY></HWPML>'
            % (head, body))


def P(*inner):
    return '<P ParaShape="0" Style="0"><TEXT CharShape="0">%s</TEXT></P>' % "".join(inner)


def C(t):
    return "<CHAR>%s</CHAR>" % t


class TestRealFixture(unittest.TestCase):
    """한/글 13.0 실측 HWPML."""

    @classmethod
    def setUpClass(cls):
        if not FIX.exists():
            raise unittest.SkipTest("실측 픽스처 없음 - tools\\test_hwpx\\4.capture_hwpml.bat")
        cls.x = real_xml()
        cls.m = hp.parse(cls.x)
        cls.body = {b["id"]: b for b in hp.iter_blocks(cls.m["body"])}
        cls.cells = {c["id"]: c for b in hp.iter_blocks(cls.m["body"]) if b["type"] == "table" for c in b["cells"]}

    def test_counts_match_raw_tags(self):                    # 빠뜨린 문단·표·셀 없음 (E1 기준의 축소판)
        st = self.m["stats"]
        self.assertEqual((st["tables"], st["cells"]), (3, 18))
        self.assertEqual(self.m["coverage_mismatch"], {})
        self.assertEqual(st["p_elements"], len(re.findall(r"<P[ >]", self.x)))

    def test_heading_level_and_style(self):
        b = self.body["s0.p0"]
        self.assertEqual((b["text"], b["style"], b["level"], b["level_src"]), ("SYN_H1 개요 제목", "개요 1", 1, "outline"))
        self.assertNotIn("level", self.body["s0.p1"])

    def test_linebreak_and_tab(self):
        self.assertEqual(self.body["s0.p1"]["text"], "SYN_P1 본문 첫 문단\nSYN_P1_LINE2\tSYN_P1_TAB")

    def test_style_langs(self):
        """글자 모양의 언어 7가지(P-045, F-152) — 실측 HWPML 속성 이름 그대로 읽는다: 바탕글은 모든 언어가 함초롬바탕(ttf)·
        장평 100·자간 0·상대 크기 100."""
        langs = {s["name"]: s for s in self.m["styledefs"]}["바탕글"]["char"]["langs"]
        self.assertEqual(sorted(langs), sorted(k for _, k in hp.LANGS))
        self.assertEqual({tuple(sorted(v.items())) for v in langs.values()},
                         {(("font", "함초롬바탕"), ("ratio", "100"), ("relsize", "100"), ("spacing", "0"), ("type", "ttf"))})

    def test_clickhere_field(self):
        f = [f for f in self.m["fields"] if f["kind"] == "clickhere"]
        self.assertEqual(f, [{"name": "SYN_FIELD_A", "kind": "clickhere", "at": "s0.p2", "value": "SYN_FIELD_A_VALUE",
                              "guide": "SYN_GUIDE", "help": "SYN_MEMO"}])

    def test_cell_field(self):
        f = [f for f in self.m["fields"] if f["kind"] == "cell"]
        self.assertEqual(f, [{"name": "SYN_CELL_02", "kind": "cell", "at": "s0.t0.r0c2", "value": "SYN_A_R0C2"}])
        self.assertEqual(self.cells["s0.t0.r0c2"]["field"], "SYN_CELL_02")

    def test_cell_paragraphs_keep_boundary(self):            # F-023 교훈
        self.assertEqual(self.cells["s0.t0.r1c0"]["text"], "SYN_A_R1C0\nSYN_A_R1C0_P2")
        naive = "".join(re.findall(r"<CHAR>(.*?)</CHAR>", ET.tostring(
            next(c for c in ET.fromstring(hp.clean(self.x)[0].split("?>", 1)[1]).iter("CELL")
                 if "SYN_A_R1C0_P2" in "".join(c.itertext())), encoding="unicode")))
        self.assertEqual(naive, "SYN_A_R1C0SYN_A_R1C0_P2")   # 음성대조: CHAR 만 이으면 경계가 사라진다

    def test_nested_table_stays_in_cell(self):               # F-021 교훈
        outer = self.body["s0.t0"]
        self.assertEqual(len(outer["cells"]), 9)
        self.assertEqual({c["row"] for c in outer["cells"]}, {0, 1, 2})
        host = self.cells["s0.t0.r2c0"]
        self.assertEqual([t["id"] for t in host["tables"]], ["s0.t0.r2c0.t0"])
        self.assertEqual(host["text"], "SYN_A_R2C0")          # 셀 글자에는 중첩 표 글자도 자리표시도 없다
        self.assertEqual(self.cells["s0.t0.r2c0.t0.r0c1"]["text"], "SYN_N_R0C1")
        for c in outer["cells"]:
            self.assertNotIn("SYN_N_R0C0", c["text"])           # 바깥 셀에 중첩 표 글자가 섞이지 않는다
        tbl = next(t for t in ET.fromstring(hp.clean(self.x)[0].split("?>", 1)[1]).iter("TABLE")
                   if t.get("RowCount") == "3" and "SYN_A_R0C0" in "".join(t.itertext()))
        self.assertEqual(len(list(tbl.iter("ROW"))), 4)     # 음성대조: iter() 재귀면 중첩 행이 바깥 행으로 샌다

    def test_merged_cells_cover_grid(self):                  # F-022 교훈, REQ-002
        t = self.body["s0.t1"]
        spans = {c["id"]: (c["rowspan"], c["colspan"]) for c in t["cells"]}
        self.assertEqual(spans["s0.t1.r0c0"], (1, 2))
        self.assertEqual(spans["s0.t1.r1c2"], (2, 1))
        self.assertEqual(len(t["cells"]), 7)
        self.assertTrue(t["grid_ok"], t["grid_note"])
        self.assertEqual(self.cells["s0.t1.r1c2"]["text"], "SYN_B_R1C2\nSYN_B_R2C2")

    def test_footnote_and_memo_are_separate(self):
        self.assertEqual(self.m["footnotes"], [{"id": "s0.fn0", "at": "s0.p3", "text": "SYN_FOOTNOTE", "number": 1}])
        self.assertEqual(self.m["memos"], [{"id": "s0.m0", "at": "s0.p4", "anchor_text": "기준", "text": "SYN_MEMO_TEXT"}])
        self.assertEqual(self.body["s0.p3"]["text"], "SYN_P3 각주 기준")       # 각주 내용이 본문에 섞이지 않는다
        self.assertNotIn("SYN_MEMO_TEXT", self.body["s0.p4"]["text"])

    def test_ids_are_stable(self):
        again = hp.parse(self.x)
        self.assertEqual([b["id"] for b in hp.iter_blocks(again["body"])], list(self.body))

    def test_locations_cover_everything(self):
        locs = {i: t for i, k, t in hp.iter_locations(self.m)}
        for marker, loc in (("SYN_N_R0C1", "s0.t0.r2c0.t0.r0c1"), ("SYN_FOOTNOTE", "s0.fn0"),
                            ("SYN_MEMO_TEXT", "s0.m0"), ("SYN_END", "s0.p11")):
            self.assertIn(marker, locs[loc])

    def test_declaration_untouched_ok(self):                 # F-034: 선언 교체 전 문자열도 받는다
        self.assertEqual(hp.parse(DECL16 + self.x.split("?>", 1)[1])["stats"]["tables"], 3)


class TestShapes(unittest.TestCase):
    """실측 픽스처에 아직 없는 배치 — 템플릿 어휘(부모>자식 쌍)로 재확인한다."""

    def test_header_footer(self):
        m = hp.parse(SYN_FULL_HWPML)
        self.assertEqual(m["headers"], [{"id": "s0.hd0", "text": "SYN_HEADER", "apply": "Both"}])
        self.assertEqual(m["footers"][0]["text"], "SYN_FOOTER")
        self.assertEqual(m["body"][0]["text"], "SYN_H1 개요 제목")   # F-023: 머리말이 첫 문단에 붙지 않는다

    def test_table_caption_with_autonum(self):
        cap = '<SHAPEOBJECT><CAPTION Side="Top"><PARALIST>%s</PARALIST></CAPTION></SHAPEOBJECT>' % P(
            C("표 "), '<AUTONUM Number="3" NumberType="Table"/>', C(". 일정"))
        x = doc(P('<TABLE RowCount="1" ColCount="1">%s<ROW><CELL RowAddr="0" ColAddr="0" RowSpan="1" ColSpan="1">'
                  '<PARALIST>%s</PARALIST></CELL></ROW></TABLE>' % (cap, P(C("A")))))
        m = hp.parse(x)
        self.assertEqual(m["body"][0]["caption"], "표 3. 일정")
        self.assertEqual(m["coverage_mismatch"], {})

    def test_textbox(self):
        x = doc(P(C("앞"), '<RECTANGLE><DRAWTEXT><PARALIST>%s</PARALIST></DRAWTEXT></RECTANGLE>' % P(C("글상자 글"))))
        m = hp.parse(x)
        self.assertEqual([(b["type"], b["text"]) for b in m["body"]], [("para", "앞"), ("textbox", "글상자 글")])
        self.assertEqual(m["stats"]["textboxes"], 1)

    def test_formula_field_in_cell(self):
        x = doc(P('<TABLE RowCount="1" ColCount="1"><ROW><CELL RowAddr="0" ColAddr="0" RowSpan="1" ColSpan="1"><PARALIST>%s'
                  '</PARALIST></CELL></ROW></TABLE>' % P('<FIELDBEGIN Type="Formula" Command="=SUM(A1:A3)"/>', C("6"),
                                                         '<FIELDEND Type="Formula"/>')))
        f = hp.parse(x)["fields"]
        self.assertEqual(f, [{"name": None, "kind": "formula", "at": "s0.t0.r0c0", "value": "6", "command": "=SUM(A1:A3)"}])

    def test_unknown_owner_kept_and_reported(self):
        x = doc(P(C("본문"), '<WEIRDBOX><PARALIST>%s</PARALIST></WEIRDBOX>' % P(C("숨은 글"))))
        m = hp.parse(x)
        self.assertEqual(m["stats"]["unknown_list_owners"], {"WEIRDBOX": 1})
        self.assertIn("숨은 글", [b.get("text") for b in m["body"]])

    def test_coverage_detects_unreached_paragraphs(self):    # 자체 점검의 음성대조
        x = (DECL16 + '<HWPML Version="2.91"><HEAD/><BODY><SECTION Id="0">%s</SECTION></BODY>'
             '<MASTERPAGE><PARALIST>%s</PARALIST></MASTERPAGE></HWPML>' % (P(C("a")), P(C("b"))))
        m = hp.parse(x)
        self.assertEqual(m["coverage_mismatch"]["P"], (1, 2))

    def test_grid_check_negative(self):
        t = {"rows": 2, "cols": 2, "cells": [
            {"id": "a", "row": 0, "col": 0, "rowspan": 1, "colspan": 2},
            {"id": "b", "row": 0, "col": 1, "rowspan": 1, "colspan": 1},
            {"id": "c", "row": 1, "col": 0, "rowspan": 1, "colspan": 2}]}
        ok, note = hp.grid_check(t)
        self.assertFalse(ok)
        self.assertIn("겹침", note)
        t["cells"].pop(1)
        self.assertEqual(hp.grid_check(t), (True, ""))
        t["cells"].pop()
        ok, note = hp.grid_check(t)
        self.assertFalse(ok)
        self.assertIn("빈 칸", note)

    def test_cleaning(self):
        x = doc(P(C("a\x01b"), C("c\ud800d")), head='<BINDATASTORAGE><BINDATA Id="1">QUJD</BINDATA></BINDATASTORAGE>')
        m = hp.parse(x)
        self.assertEqual(m["cleaning"], {"bindata_blocks": 1, "lone_surrogates": 1, "bad_xml_chars": 1})
        self.assertEqual(m["body"][0]["text"], "abc\ufffdd")

    def test_bad_input(self):
        for bad in ("", "<A/>", "<HWPML><BODY>"):
            with self.assertRaises(hp.ParseError):
                hp.parse(bad)

    def test_clickhere_command(self):
        self.assertEqual(hp.parse_clickhere_command("Clickhere:set:40:Direction:wstring:4:가 나다 HelpState:wstring:0: "),
                         {"Direction": "가 나다", "HelpState": ""})
        self.assertEqual(hp.parse_clickhere_command(None), {})

    def test_field_across_paragraphs(self):
        x = doc(P(C("x"), '<FIELDBEGIN Type="Clickhere" Name="F"/>', C("1줄")) + P(C("2줄"), '<FIELDEND Type="Clickhere"/>'))
        f = hp.parse(x)["fields"][0]
        self.assertEqual((f["value"], f["at"]), ("1줄\n2줄", "s0.p0"))   # 위치는 시작 문단 (검토 15)

    def test_numbered_headings_when_no_outline(self):        # F-083: SDP·시험평가 계획서 - 제목이 번호 글자
        x = doc(P(C("1 개요")) + P(C("1.1 적용범위")) + P(C("  2.1.1.1. 미군사 규격서 (Military)")) + P(C("본문 문장이다."))
                + P(C("2024. 10. 12")) + P(C("1. 본 문서는 체계를 기술한다.")) + P(C("1.2 목차 줄\t3"))
                + P(C("3")) + P(C("12.5 kg 이상")))
        m = hp.parse(x)
        got = [(b["text"].strip(), b.get("level"), b.get("level_src")) for b in m["body"]]
        self.assertEqual(got[:3], [("1 개요", 1, "number"), ("1.1 적용범위", 2, "number"),
                                   ("2.1.1.1. 미군사 규격서 (Military)", 4, "number")])
        self.assertTrue(all(lv is None for _, lv, _ in got[3:8]), got)   # 문장·날짜·'…다.'·목차 줄·숫자만은 제목 아님
        self.assertEqual((m["stats"]["headings"], m["stats"]["heading_source"]), (4, "number"))
        # 알려진 한계: '12.5 kg 이상'처럼 숫자로 시작하는 짧은 문단은 제목으로 잡힌다(문단 모양 개요가 없는 문서에서만)
        self.assertEqual(got[8][1], 2)

    def test_numbered_fallback_off_when_outline_exists(self):  # 음성대조: 개요 문단이 있으면 번호 글자를 쓰지 않는다
        head = ('<MAPPINGTABLE><STYLELIST><STYLE Id="0" Name="바탕글"/></STYLELIST><PARASHAPELIST>'
                '<PARASHAPE Id="0" HeadingType="None" Level="0"/><PARASHAPE Id="2" HeadingType="Outline" Level="1"/>'
                '</PARASHAPELIST></MAPPINGTABLE>')
        x = doc('<P ParaShape="2" Style="0"><TEXT><CHAR>적용범위</CHAR></TEXT></P>' + P(C("1.1 번호 문단")), head=head)
        m = hp.parse(x)
        self.assertEqual([(b.get("level"), b.get("level_src")) for b in m["body"]], [(2, "outline"), (None, None)])
        self.assertEqual(m["stats"]["heading_source"], "outline")

    def test_nested_table_in_header_kept(self):              # 검토 10: 머리말 표 안 중첩 표 글자를 버리지 않는다
        inner = '<TABLE RowCount="1" ColCount="1"><ROW><CELL RowAddr="0" ColAddr="0" RowSpan="1" ColSpan="1"><PARALIST>%s</PARALIST></CELL></ROW></TABLE>'
        x = doc('<P><TEXT><HEADER><PARALIST>%s</PARALIST></HEADER><CHAR>본문</CHAR></TEXT></P>'
                % P(inner % (P(C("바깥")) + P(inner % P(C("안쪽_ZQ"))))))
        m = hp.parse(x)
        self.assertIn("안쪽_ZQ", m["headers"][0]["text"])
        self.assertEqual(m["coverage_mismatch"], {})


if __name__ == "__main__":
    unittest.main()


class TestStyleAndCtrlInventory(unittest.TestCase):
    """P-025: 스타일 정의·번호 모양·조판 개체 목록·문단 정렬 — 템플릿 서식 비교와 쪽 번호 검사용."""
    X = (DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="1"><MAPPINGTABLE>'
         '<BINDATALIST Count="1"><BINITEM BinData="1" Format="PNG" Type="Embedding"/></BINDATALIST>'
         '<FACENAMELIST><FONTFACE Count="1" Lang="Hangul"><FONT Id="0" Name="휴먼명조" Type="ttf"/></FONTFACE>'
         '<FONTFACE Count="1" Lang="Latin"><FONT Id="0" Name="Times New Roman" Type="ttf"/></FONTFACE></FACENAMELIST>'
         '<CHARSHAPELIST Count="1"><CHARSHAPE Height="1500" Id="0" TextColor="0"><FONTID Hangul="0" Latin="0"/>'
         '<RATIO Hangul="95"/><CHARSPACING Hangul="-5"/><BOLD/></CHARSHAPE></CHARSHAPELIST>'
         '<PARASHAPELIST Count="2"><PARASHAPE Align="Right" Id="0"><PARAMARGIN Left="0" LineSpacing="160"/></PARASHAPE>'
         '<PARASHAPE Align="Justify" HeadingType="Outline" Id="1" Level="1"><PARAMARGIN Left="0"/></PARASHAPE></PARASHAPELIST>'
         '<STYLELIST Count="2"><STYLE CharShape="0" Id="0" Name="바탕글" ParaShape="0" Type="Para"/>'
         '<STYLE CharShape="0" EngName="CS2" Id="1" Name="COMSAF 개요 2" ParaShape="1" Type="Para"/></STYLELIST>'
         '<NUMBERINGLIST Count="1"><NUMBERING Id="1" Start="0"><PARAHEAD Level="1" NumFormat="Digit" Start="1">^1</PARAHEAD>'
         '<PARAHEAD Level="2" NumFormat="Digit" Start="1">^1.^2</PARAHEAD></NUMBERING></NUMBERINGLIST>'
         '</MAPPINGTABLE></HEAD><BODY><SECTION Id="0">'
         '<P ParaShape="0" Style="0"><TEXT CharShape="0"><SECDEF OutlineShape="1"><STARTNUMBER Page="0"/></SECDEF>'
         '<PAGENUM FormatType="Digit" Pos="BottomCenter" SideChar="-"/><CHAR>문서번호 : X</CHAR></TEXT></P>'
         '<P ParaShape="1" Style="1"><TEXT CharShape="0"><CHAR>적용범위</CHAR></TEXT></P>'
         '</SECTION></BODY></HWPML>')

    def test_inventory(self):
        m = hp.parse(self.X)
        self.assertEqual(m["stats"]["bindata_items"], 1)
        sd = {s["name"]: s for s in m["styledefs"]}
        self.assertEqual(sd["COMSAF 개요 2"]["para"]["HeadingType"], "Outline")
        self.assertEqual(sd["COMSAF 개요 2"]["para"]["Level"], "1")
        self.assertEqual(sd["바탕글"]["char"]["hangul"], "휴먼명조")
        self.assertEqual((sd["바탕글"]["char"]["height"], sd["바탕글"]["char"]["bold"], sd["바탕글"]["char"]["ratio"]),
                         ("1500", True, "95"))
        self.assertEqual([h["text"] for h in m["numberings"]["1"]], ["^1", "^1.^2"])
        tags = [(c["at"], c["tag"]) for c in m["ctrls"]]
        self.assertEqual(tags, [("s0.p0", "SECDEF"), ("s0.p0", "PAGENUM")])
        self.assertEqual(m["ctrls"][0]["attrs"]["OutlineShape"], "1")
        self.assertEqual(m["ctrls"][1]["attrs"]["Pos"], "BottomCenter")
        self.assertEqual([b["align"] for b in m["body"]], ["Right", "Justify"])
        self.assertEqual(m["body"][1]["level"], 2)            # 개요 문단: Level 1 → 수준 2

    def test_style_langs_only_given(self):
        """언어별 값은 HWPML 에 있는 것만(P-045): 이 꼴은 FONTID 한글·라틴, 장평·자간은 한글만 — 없는 언어·값은 넣지 않는다."""
        sd = {s["name"]: s for s in hp.parse(self.X)["styledefs"]}
        self.assertEqual(sd["바탕글"]["char"]["langs"],
                         {"hangul": {"font": "휴먼명조", "type": "ttf", "ratio": "95", "spacing": "-5"},
                          "latin": {"font": "Times New Roman", "type": "ttf"}})

    def test_style_langs_differ(self):
        """언어마다 다른 글꼴·글꼴 종류·장평·자간·상대 크기(P-045) — 글꼴 번호는 그 언어 목록에서 찾는다(없는 번호는 None)."""
        head = ('<MAPPINGTABLE><FACENAMELIST><FONTFACE Count="1" Lang="Hangul"><FONT Id="0" Name="한양신명조" Type="hft"/>'
                '</FONTFACE><FONTFACE Count="2" Lang="Symbol"><FONT Id="0" Name="HY견명조" Type="ttf"/>'
                '<FONT Id="1" Name="기호체" Type="hft"/></FONTFACE></FACENAMELIST><CHARSHAPELIST Count="1">'
                '<CHARSHAPE Height="1000" Id="0"><FONTID Hangul="0" Symbol="1" User="7"/><RATIO Hangul="85" Symbol="100" '
                'User="100"/><CHARSPACING Hangul="-3" Symbol="0"/><RELSIZE Hangul="100" Symbol="120"/></CHARSHAPE>'
                '</CHARSHAPELIST><PARASHAPELIST Count="1"><PARASHAPE Id="0"/></PARASHAPELIST><STYLELIST Count="1">'
                '<STYLE CharShape="0" Id="0" Name="06" ParaShape="0" Type="Para"/></STYLELIST></MAPPINGTABLE>')
        c = {s["name"]: s for s in hp.parse(doc(P(C("x")), head))["styledefs"]}["06"]["char"]
        self.assertEqual(c["langs"], {"hangul": {"font": "한양신명조", "type": "hft", "ratio": "85", "spacing": "-3",
                                                 "relsize": "100"},
                                      "symbol": {"font": "기호체", "type": "hft", "ratio": "100", "spacing": "0",
                                                 "relsize": "120"},
                                      "user": {"font": None, "type": None, "ratio": "100"}})
        self.assertEqual((c["hangul"], c["ratio"], c["spacing"]), ("한양신명조", "85", "-3"))   # 한글 값(앞 키)은 그대로

    def test_marks_and_offsets(self):
        """P-025: 글자 아닌 개체의 글자 위치(marks, ctrls.offset) — 캐럿으로 번호 글자를 지울 때 개체를 피하는 근거."""
        m = hp.parse(self.X)
        self.assertEqual(m["body"][0]["marks"], [[0, "SECDEF"], [0, "PAGENUM"]])
        self.assertEqual([c["offset"] for c in m["ctrls"]], [0, 0])
        self.assertNotIn("marks", m["body"][1])              # 개체 없는 문단에는 키가 없다
        x = self.X.replace("<CHAR>적용범위</CHAR>", '<CHAR>1.1 적용</CHAR><BOOKMARK Name="b"/><CHAR>범위</CHAR>')
        b = hp.parse(x)["body"][1]
        self.assertEqual((b["text"], b["marks"]), ("1.1 적용범위", [[6, "BOOKMARK"]]))
        x = self.X.replace("<CHAR>적용범위</CHAR>", '<CHAR>1.1<TAB/>적용<TITLEMARK Ignore="false"/>범위</CHAR>')
        b = hp.parse(x)["body"][1]                             # CHAR 안 개체: 글자는 그대로, 자리는 marks 로
        self.assertEqual((b["text"], b["marks"]), ("1.1\t적용범위", [[6, "TITLEMARK"]]))

    def test_header_footer_page_number_flag(self):
        x = self.X.replace('<CHAR>문서번호 : X</CHAR>',
                           '<FOOTER ApplyPageType="Both"><PARALIST><P><TEXT><CHAR>D-1 - </CHAR>'
                           '<AUTONUM Number="3" NumberType="Page"/><CHAR> -</CHAR></TEXT></P></PARALIST></FOOTER>'
                           '<HEADER ApplyPageType="Both"><PARALIST><P><TEXT><CHAR>머리</CHAR></TEXT></P></PARALIST></HEADER>'
                           '<CHAR>문서번호 : X</CHAR>')
        m = hp.parse(x)
        self.assertEqual(m["footers"][0]["text"], "D-1 - 3 -")
        self.assertTrue(m["footers"][0]["page_number"])
        self.assertNotIn("page_number", m["headers"][0])      # 쪽 번호 필드 없는 머리말

    def test_object_positions_in_md(self):
        """P-027: 그림 개체의 자리·크기·캡션·앞 글 — 화면 그림이 많은 설명서를 옮겨 쓸 때 그림 자리를 찾는다."""
        import render_md as rm
        pic = ('<P ParaShape="0" Style="0"><TEXT CharShape="0"><PICTURE><SHAPEOBJECT/>'
               '<SHAPECOMPONENT CurWidth="28346" CurHeight="14173"/><IMAGE BinItem="1"/>'
               '<CAPTION><PARALIST><P><TEXT><CHAR>그림 3 로그인 화면</CHAR></TEXT></P></PARALIST></CAPTION></PICTURE>'
               '<CHAR/></TEXT></P>')
        x = self.X.replace("</SECTION>", pic + "</SECTION>")
        m = hp.parse(x)
        self.assertEqual([(c["at"], c["tag"], c.get("blocks")) for c in m["ctrls"] if c["tag"] == "PICTURE"],
                         [("s0.p2", "PICTURE", ["s0.c0"])])
        lines = rm.objects_lines(m)
        self.assertEqual(lines[0], "## 그림·개체 위치 (1)")
        self.assertIn("| 1 | PICTURE | `s0.p2` | 100×50 | 그림 3 로그인 화면 | `s0.p1` 적용범위 |", lines)
        self.assertEqual(rm.objects_lines(hp.parse(self.X)), [])          # 그림 없으면 절도 없다

    def test_root_kinds(self):
        """P-029: 최상위 문단 종류(글자·표·개체·빈 문단) — 작성기가 쓴 뒤 문단 배치를 맞춰 본다."""
        tbl = ('<P><TEXT><TABLE ColCount="1" RowCount="1"><ROW><CELL ColAddr="0" RowAddr="0" RowSpan="1" ColSpan="1">'
               '<PARALIST><P><TEXT><CHAR>칸</CHAR></TEXT></P></PARALIST></CELL></ROW></TABLE><CHAR/></TEXT></P>')
        x = self.X.replace("</SECTION>", tbl + '<P><TEXT><PICTURE/><CHAR/></TEXT></P><P><TEXT><SECDEF/><CHAR> </CHAR>'
                           '</TEXT></P></SECTION>')
        m = hp.parse(x)
        self.assertEqual([(r["id"], r["kind"]) for r in m["roots"]],
                         [("s0.p0", "text"), ("s0.p1", "text"), ("s0.p2", "table"), ("s0.p3", "object"), ("s0.p4", "empty")])

    def test_paragraph_char_heights(self):
        """P-031: 문단 글자 크기 — 글자가 있는 TEXT 의 글자 모양 크기만(빈 TEXT·개체만 있는 TEXT 는 빼고), 작은 것부터."""
        head = ('<MAPPINGTABLE><CHARSHAPELIST><CHARSHAPE Id="0" Height="1000"/><CHARSHAPE Id="1" Height="1200"/>'
                '<CHARSHAPE Id="2" Height="900"/></CHARSHAPELIST></MAPPINGTABLE>')
        body = ('<P><TEXT CharShape="1"><CHAR>본문</CHAR></TEXT></P>'
                '<P><TEXT CharShape="1"><CHAR>섞인 </CHAR></TEXT><TEXT CharShape="0"><CHAR>크기</CHAR></TEXT>'
                '<TEXT CharShape="2"><SECDEF/><CHAR/></TEXT></P>'
                '<P><TEXT CharShape="9"><CHAR>모르는 모양</CHAR></TEXT></P>')
        m = hp.parse(doc(body, head))
        self.assertEqual([(b["text"], b.get("heights")) for b in m["body"]],
                         [("본문", ["1200"]), ("섞인 크기", ["1000", "1200"]), ("모르는 모양", None)])
