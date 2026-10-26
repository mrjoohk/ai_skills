"""표 서식(table_style.py) 시험 — 한/글 없이: 참고 표 → 서식 파일, 표 고르기, 칸 서식(그대로·자리별), 칸 너비, 쓴 뒤 대조."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import table_style as ts          # noqa: E402

K, N, D, GRAY = ["Solid", "0.4mm"], ["Solid", "0.12mm"], ["Solid", "0.15mm"], [214, 214, 214]


def bf(i, l, r, t, b, face=None, color=None):
    side = lambda tag, v: '<%s Type="%s" Width="%s"%s/>' % (tag, v[0], v[1], ' Color="%d"' % color if color else "")  # noqa
    fill = '<FILLBRUSH><WINDOWBRUSH Alpha="0" FaceColor="%d" HatchColor="0"/></FILLBRUSH>' % face if face else ""
    return '<BORDERFILL Id="%d">%s%s%s%s%s</BORDERFILL>' % (i, side("LEFTBORDER", l), side("RIGHTBORDER", r),
                                                          side("TOPBORDER", t), side("BOTTOMBORDER", b), fill)


def cell(r, c, bid, width, style=0, header=False, text="x"):
    return ('<CELL BorderFill="%d" ColAddr="%d" ColSpan="1" Header="%s" RowAddr="%d" RowSpan="1" Width="%d">'
            '<PARALIST VertAlign="Center"><P ParaShape="0" Style="%d"><TEXT CharShape="0"><CHAR>%s</CHAR></TEXT></P>'
            '</PARALIST></CELL>' % (bid, c, "true" if header else "false", r, width, style, text))


def table(rows_xml, nr, nc, margin=(538, 538, 0, 0), caption=None):
    cap = ('<SHAPEOBJECT><CAPTION><PARALIST><P ParaShape="0" Style="0"><TEXT CharShape="0"><CHAR>%s</CHAR></TEXT></P>'
           '</PARALIST></CAPTION></SHAPEOBJECT>' % caption) if caption else ""
    return ('<P ParaShape="0" Style="0"><TEXT CharShape="0"><TABLE BorderFill="1" ColCount="%d" RowCount="%d">%s'
            '<INSIDEMARGIN Left="%d" Right="%d" Top="%d" Bottom="%d"/>%s</TABLE></TEXT></P>' % (nc, nr, cap, *margin,
                                                                                             "".join(rows_xml)))


def doc(bfs, body, sec="1"):
    return ('<?xml version="1.0" encoding="UTF-8"?><HWPML><HEAD><MAPPINGTABLE><BORDERFILLLIST>%s</BORDERFILLLIST>'
            '<STYLELIST><STYLE Id="0" Name="바탕글"/><STYLE Id="1" Name="05_도표내용_항목제목"/>'
            '<STYLE Id="2" Name="06_도표내용_본문중앙"/><STYLE Id="3" Name="07_도표내용_본문혼합"/></STYLELIST>'
            '</MAPPINGTABLE></HEAD><BODY><SECTION Id="0"><P><TEXT><CHAR>표지</CHAR></TEXT></P></SECTION>'
            '<SECTION Id="%s">%s</SECTION></BODY></HWPML>' % ("".join(bfs), sec, body))


def ref_doc():
    """참고 표 2개(구역 1): '표 1 문서요약' 3×2 — 첫 줄 회색·바깥 0.4·안 0.12, 칸 너비 30:110; '표 2 용어' 2×3 — 안 0.15·제목 셀."""
    b = [bf(1, N, N, N, N), bf(10, K, N, K, K, 14079702), bf(11, N, K, K, K, 14079702),
         bf(12, K, N, K, N), bf(13, N, K, K, N), bf(14, K, N, N, K), bf(15, N, K, N, K),
         bf(20, K, D, K, K, 14079702, 4278190080), bf(21, D, D, K, K, 14079702), bf(22, D, K, K, K, 14079702),
         bf(23, K, D, K, K), bf(24, D, D, K, K), bf(25, D, K, K, K)]
    t1 = table(["<ROW>%s%s</ROW>" % (cell(0, 0, 10, 8504, 1), cell(0, 1, 11, 31181, 1)),
                "<ROW>%s%s</ROW>" % (cell(1, 0, 12, 8504, 3), cell(1, 1, 13, 31181, 3)),
                "<ROW>%s%s</ROW>" % (cell(2, 0, 14, 8504, 3), cell(2, 1, 15, 31181, 3))], 3, 2, caption="표 1 문서요약")
    t2 = table(["<ROW>%s%s%s</ROW>" % (cell(0, 0, 20, 2835, 1, True), cell(0, 1, 21, 5669, 1, True),
                                       cell(0, 2, 22, 31181, 1, True)),
                "<ROW>%s%s%s</ROW>" % (cell(1, 0, 23, 2835, 2), cell(1, 1, 24, 5669, 2), cell(1, 2, 25, 31181, 2))],
               2, 3, margin=(141, 141, 141, 141), caption="표 2 용어")
    return doc(b, t1 + t2)


def poc_report(x):
    return "# 보고\n\n## 자세히 (JSON)\n\n```json\n%s\n```\n" % json.dumps({"T0": ts.formats(x)}, ensure_ascii=False)


class TestParse(unittest.TestCase):
    def test_line_and_fill(self):
        self.assertEqual(ts.parse_line("Solid 0.4mm 0xFF000000"), ["Solid", "0.4mm"])
        self.assertEqual(ts.parse_line("없음"), ["None", "0.1mm"])
        self.assertIsNone(ts.parse_line("-"))
        self.assertEqual(ts.parse_fill("rgb(214,214,214)"), GRAY)
        self.assertIsNone(ts.parse_fill("없음"))
        self.assertEqual((ts.line_text(K), ts.line_text(["None", "0.1mm"]), ts.fill_text(None), ts.fill_text(GRAY)),
                         ("Solid 0.4mm", "없음", "없음", "rgb(214,214,214)"))
        self.assertEqual(ts.ref_caption("표 12 LAH 원격 제어 창 항목"), "LAH 원격 제어 창 항목")

    def test_from_poc(self):
        sf = ts.from_poc(poc_report(ref_doc()), "참고.hwpx", alias={"약어": "용어"}, default="용어", sections=("s1.",))
        self.assertEqual(sorted(sf["tables"]), ["문서요약", "용어"])
        a = sf["tables"]["문서요약"]
        self.assertEqual((a["size"], a["inside_margin"], a["header_cells"]), ([3, 2], [538, 538, 0, 0], False))
        self.assertEqual(a["cells"][0][0], {"L": K, "R": N, "T": K, "B": K, "fill": GRAY, "style": "05_도표내용_항목제목",
                                            "header": False})
        self.assertEqual(a["col_ratio"], [round(30.0 / 140.0, 4), round(110.0 / 140.0, 4)])
        self.assertEqual(a["classes"]["head_bottom"], K)
        self.assertEqual(a["classes"]["inner_h"], N)
        b = sf["tables"]["용어"]
        self.assertEqual((b["header_cells"], b["classes"]["inner_v"], b["inside_margin"]), (True, D, [141, 141, 141, 141]))
        self.assertEqual(b["cells"][0][0]["L"], K)                       # 0xFF000000 색은 버린다
        with self.assertRaises(ValueError):
            ts.from_poc(poc_report(ref_doc()), "참고.hwpx", default="없는 표", sections=("s1.",))
        with self.assertRaises(ValueError):
            ts.from_poc(poc_report(ref_doc()), "참고.hwpx", alias={"약어": "없는 표"}, sections=("s1.",))
        self.assertEqual(ts.from_poc(poc_report(ref_doc()), "x", sections=("s2.",))["tables"], {})


class TestPlan(unittest.TestCase):
    def setUp(self):
        self.sf = ts.from_poc(poc_report(ref_doc()), "참고.hwpx", alias={"약어": "용어"}, default="용어", sections=("s1.",))

    def test_exact_when_same_size(self):
        p = ts.plan_table(self.sf, "문서요약", [["장", "내용"], ["1", "개요"], ["2", "관련문서"]])
        self.assertEqual((p["ref"], p["mode"], p["by_default"]), ("문서요약", "exact", False))
        self.assertEqual(p["cells"][2][1]["B"], K)
        self.assertNotIn("col_ratio", p)                                   # 칸 너비는 칸 글자에 맞춘다(P-041) — 참고 비율 안 씀

    def test_class_when_size_differs(self):
        rows = [["장", "내용"]] + [[str(i), "x"] for i in range(1, 6)]
        p = ts.plan_table(self.sf, "문서요약", rows)                    # 6×2 — 참고 표는 3×2
        self.assertEqual(p["mode"], "class")
        c = p["cells"]
        self.assertEqual((c[0][0]["B"], c[1][0]["T"], c[2][0]["T"], c[3][1]["B"], c[5][1]["B"], c[3][0]["L"], c[3][0]["R"]),
                         (K, K, N, N, K, K, N))
        self.assertEqual((c[0][1]["fill"], c[3][1]["fill"], c[3][1]["style"]), (GRAY, None, "07_도표내용_본문혼합"))

    def test_default_and_alias(self):
        p = ts.plan_table(self.sf, "약어", [["약어", "설명"], ["UAV", "무인기"]])
        self.assertEqual((p["ref"], p["by_default"]), ("용어", False))
        p = ts.plan_table(self.sf, "다른 표", [["가", "나", "다"], ["MBS", "짧은 글", "아주 긴 설명 글이 들어가는 칸입니다 길게"]])
        self.assertEqual((p["ref"], p["by_default"], p["mode"]), ("용어", True, "exact"))
        self.assertEqual([x["style"] for x in p["cells"][1]], ["06_도표내용_본문중앙", "06_도표내용_본문중앙",
                                                               "07_도표내용_본문혼합"])
        self.assertTrue(all(x["header"] for x in p["cells"][0]))
        self.assertIsNone(ts.plan_table({"tables": {}, "default": None}, "x", [["a"]]))

    def test_default_table_width(self):
        pd = ('<SECDEF><PAGEDEF GutterType="%s" Height="84188" Landscape="%s" Width="59528"><PAGEMARGIN Gutter="1417" '
              'Left="7087" Right="7087"/></PAGEDEF></SECDEF>')
        x = lambda body: doc([], body)                                         # noqa: E731
        p = lambda gt="LeftOnly", ls="0": '<P><TEXT>%s</TEXT></P>' % (pd % (gt, ls))   # noqa: E731
        self.assertEqual(ts.default_table_width(x(p()), 1), 43370)            # 실측 G1 = 59528-7087-7087-1417-567
        self.assertEqual(ts.default_table_width(x(p("TopBottom")), 1), 43370 + 1417)
        self.assertEqual(ts.default_table_width(x(p(ls="1")), 1), 84188 - 7087 - 7087 - 1417 - 567)
        self.assertIsNone(ts.default_table_width(x("<P><TEXT><SECDEF/></TEXT></P>"), 1))
        self.assertIsNone(ts.default_table_width(x(p()), 5))
        self.assertIsNone(ts.default_table_width("깨진 글", 1))

    def test_select_caption_forms(self):
        """공백이 달라도, 서식 파일 캡션이 PoC 보고에서 30자로 잘려 '…'로 끝나도 고른다(검토 P-040 11)."""
        sf = {"tables": {"문서 요약": {"size": [1, 1]}, "아주 긴 캡션이 서른 글자를 넘어서 잘린 참고 표의 이름…": {"size": [1, 1]}},
              "alias": {"약  어": "문서 요약"}, "default": "문서 요약"}
        self.assertEqual(ts.select(sf, " 문서  요약 ")[0:3:2], ("문서 요약", False))
        self.assertEqual(ts.select(sf, "아주 긴 캡션이 서른 글자를 넘어서 잘린 참고 표의 이름 끝부분")[0],
                         "아주 긴 캡션이 서른 글자를 넘어서 잘린 참고 표의 이름…")
        self.assertEqual(ts.select(sf, "약어 ")[0:3:2], ("문서 요약", True))      # 별칭 '약  어' ≠ '약어' → 기본
        self.assertEqual(ts.select(sf, "약 어")[0:3:2], ("문서 요약", False))     # 공백 하나로 보면 별칭
        self.assertEqual(ts.select(sf, None)[2], True)

    def test_explicit_no_fill_kept(self):
        """참고 표 첫 칸 배경이 '없음'이면 본문 배경으로 채우지 않는다 — '배경 없음'은 '없는 자리'가 아니다(검토 P-040 10)."""
        st = {"size": [3, 3], "cells": None, "classes": {"top": K, "bottom": K, "left": K, "right": K, "inner_h": N,
                                                         "inner_v": N, "head_bottom": K},
              "fills": {"head_first": None, "head": GRAY, "first": None, "body": [255, 255, 200]},
              "styles": {"head": "05_도표내용_항목제목", "body": "06_도표내용_본문중앙"}, "header_cells": True}
        self.assertIsNone(ts.cell_format(st, 0, 0, 4, 3)["fill"])
        self.assertIsNone(ts.cell_format(st, 2, 0, 4, 3)["fill"])
        self.assertEqual(ts.cell_format(st, 2, 1, 4, 3)["fill"], [255, 255, 200])
        self.assertEqual(ts.cell_format(st, 0, 0, 4, 3)["style"], "05_도표내용_항목제목")   # 스타일 자리 없음 → 다음 자리

    def test_no_header_first_row_is_body(self):
        rows = [["가", "나"], ["다", "라"], ["마", "바"]]
        p = ts.plan_table(self.sf, "용어", rows, header=False)                  # 2×3 참고와 크기가 달라 자리별
        self.assertEqual(p["mode"], "class")
        c = p["cells"]
        self.assertEqual([x["header"] for x in c[0]], [False, False])
        self.assertEqual((c[0][0]["T"], c[0][0]["B"], c[1][0]["T"]), (K, D, D))   # 참고 2줄 표라 안 가로선 → 안 세로선(0.15)
        self.assertEqual({x["style"] for x in c[0]}, {"06_도표내용_본문중앙"})
        h = ts.plan_table(self.sf, "용어", rows)                                  # 제목 줄 있음 → 제목 셀·아래 굵은 선
        self.assertEqual(([x["header"] for x in h["cells"][0]], h["cells"][0][0]["B"]), ([True, True], K))

    def test_shared_edges(self):
        """이웃 칸이 함께 쓰는 변(P-045, F-155): 두 값이 다르면 더 굵은 선을 두 칸에 — 보이는 선이 안 보이는 선(None)보다,
        같은 굵기면 위·왼쪽 칸 값. 한쪽 값이 없으면 그대로."""
        Z, Dh = ["None", "0.5mm"], ["Dash", "0.4mm"]
        cells = [[{"L": K, "R": D, "T": K, "B": K}, {"L": N, "R": K, "T": K, "B": K}],
                 [{"L": K, "R": Z, "T": D, "B": K}, {"L": D, "R": K, "T": Dh, "B": K}]]
        self.assertEqual(ts.shared_edges(cells), 4)
        self.assertEqual((cells[0][0]["R"], cells[0][1]["L"]), (D, D))          # 0.15 > 0.12
        self.assertEqual((cells[0][0]["B"], cells[1][0]["T"]), (K, K))          # 머리 줄 아래 0.4 > 둘째 줄 위 0.15(참고본 표 6·7)
        self.assertEqual((cells[0][1]["B"], cells[1][1]["T"]), (K, K))          # 같은 굵기(실선·점선 0.4) → 위 칸 값
        self.assertEqual((cells[1][0]["R"], cells[1][1]["L"]), (D, D))          # 안 보이는 선(더 굵어도)보다 보이는 선
        self.assertEqual((cells[0][0]["L"], cells[0][0]["T"], cells[1][1]["B"]), (K, K, K))   # 바깥 변은 그대로
        right = [[{"R": N}, {"L": K}]]
        self.assertEqual((ts.shared_edges(right), right), (1, [[{"R": K}, {"L": K}]]))   # 오른쪽 칸이 굵으면 그 값
        one = [[{"B": K}], [{"T": None}]]                                         # 한쪽이 없으면 다른 쪽 값을 두 칸에 —
        self.assertEqual((ts.shared_edges(one), one), (1, [[{"B": K}], [{"T": K}]]))   # 안 입힌 변이 기본값으로 덮지 않게
        other = [[{"R": None}, {"L": D}]]
        self.assertEqual((ts.shared_edges(other), other), (1, [[{"R": D}, {"L": D}]]))
        self.assertEqual(ts.shared_edges([[{"R": K}, {"L": K}]]), 0)              # 같으면 세지 않는다
        self.assertEqual(ts.shared_edges([[{"B": None}], [{}]]), 0)               # 둘 다 없으면 그대로

    def test_plan_shared_edges(self):
        """칸마다 그대로(exact)인 참고 표도 맞닿은 변이 다르면 계획에서 맞춘다 — 서식 파일은 그대로(P-045, 참고본 표 6·7 꼴)."""
        sf = json.loads(json.dumps(self.sf))
        g = sf["tables"]["문서요약"]["cells"]
        g[1][0]["T"] = g[1][1]["T"] = D                                         # 머리 줄 아래 0.4mm · 둘째 줄 위 0.15mm
        before = json.dumps(sf, sort_keys=True)
        rows = [["장", "내용"], ["1", "개요"], ["2", "관련문서"]]
        p = ts.plan_table(sf, "문서요약", rows)
        self.assertEqual((p["mode"], p["shared_edges"]), ("exact", 2))
        self.assertEqual([(p["cells"][0][c]["B"], p["cells"][1][c]["T"]) for c in range(2)], [(K, K)] * 2)
        self.assertEqual(json.dumps(sf, sort_keys=True), before)                  # 서식 파일(참고 칸)은 바꾸지 않는다
        self.assertEqual(ts.plan_table(self.sf, "문서요약", rows)["shared_edges"], 0)

    def test_validate(self):
        self.assertEqual(ts.validate(self.sf), [])
        self.assertTrue(ts.validate({"default": "x"}))
        bad = ts.validate({"tables": {"a": {"size": [2, 2], "cells": [[{}, {}]], "inside_margin": [1, 2]}},
                           "default": "b", "alias": {"c": "d"}})
        self.assertEqual(len(bad), 4, bad)

    def test_text_width(self):
        self.assertEqual((ts.text_width("MBS"), ts.text_width("장비"), ts.text_width("PC 망")), (3, 4, 5))

    def test_pad_margin(self):
        """안 여백 위·아래 = 표 칸 스타일 중 가장 큰 글자 크기의 절반, 왼·오는 계획 값 또는 한/글 기본(사용자 지시 P-048)."""
        m = {"05": {"height": 1300}, "06": {"height": 1000}, "07": {"height": 1050}}
        self.assertEqual(ts.CELL_PAD_EM, 0.5)
        self.assertEqual(ts.pad_margin([538, 538, 0, 0], [["06", "06"], ["06", "06"]], m), [538, 538, 500, 500])
        self.assertEqual(ts.pad_margin([141, 141, 141, 141], [["05", "05"], ["07", "06"]], m), [141, 141, 650, 650])
        self.assertEqual(ts.pad_margin([141, 141, 141, 141], [["07"]], m), [141, 141, 525, 525])
        self.assertEqual(ts.pad_margin(None, [["06"]], m), [510, 510, 500, 500])          # 서식 계획 없음 — 한/글 기본 왼·오
        self.assertEqual(ts.pad_margin(None, [["없는 스타일"]], m), [510, 510, 500, 500])   # 글자 크기를 모르면 1000(기본)
        self.assertEqual(ts.pad_margin(["538", "538", "0", "0"], [["06"]], m), [538, 538, 500, 500])   # 숫자 글자도
        self.assertEqual(ts.pad_margin(["538.5", 538.9, "0", "0"], [["06"]], m), [538, 538, 500, 500])  # 손으로 고친 값
        self.assertEqual(ts.pad_margin([None, "x", 0, 0], [["06"]], m), [510, 510, 500, 500])   # 못 읽으면 한/글 기본
        for bad in ("nan", "inf", float("nan"), float("-inf"), -538, "-1", 10 ** 400):    # 못 쓰는 값도(검토 P-049 D1F-02·D1G-N01)
            self.assertEqual(ts.pad_margin([bad, 538, 0, 0], [["06"]], m), [510, 538, 500, 500], bad)
        self.assertEqual(ts.pad_margin([0, 0, 0, 0], [["06"]], m), [0, 0, 500, 500])        # 0 은 쓸 수 있는 값
        im = [538, 538, 0, 0]
        ts.pad_margin(im, [["06"]], m)
        self.assertEqual(im, [538, 538, 0, 0])                               # 서식 파일 값은 그대로(새 목록)


class TestFit(unittest.TestCase):
    """칸 너비를 칸 글자 폭에 맞춤(P-041, D-044) — 글자 폭 어림·재기, 여유, 본문 폭 넘을 때 긴 칸만 줄이기."""
    M = dict(ts.DEFAULT_METRICS, hangul="한글체", latin="라틴체")

    def test_style_metrics(self):
        d = [{"name": "06", "char": {"height": "1000", "ratio": "95", "spacing": "-5", "bold": True, "hangul": "가",
                                     "latin": "A"}, "para": {"m_Left": "200", "m_Right": "0", "m_Indent": "-300"}},
             {"name": "빈", "char": {}, "para": {}},
             {"name": "글자", "char": {"font_space": True},
              "para": {"BreakNonLatinWord": "true", "BreakLatinWord": "BreakWord", "m_Indent": "300"}},
             {"name": "어절", "char": {}, "para": {"BreakNonLatinWord": "false", "BreakLatinWord": "KeepWord"}}]
        m = ts.style_metrics(d)
        self.assertEqual(m["06"], {"height": 1000, "ratio": 95.0, "spacing": -5.0, "bold": True, "hangul": "가",
                                   "latin": "A", "font_space": False, "break_hangul": False, "break_latin": False,
                                   "para_lr": 200, "m_left": 200, "m_right": 0,
                                   "m_indent": -300})                      # 내어쓰기(음수)는 첫 줄을 좁히지 않는다
        self.assertEqual(m["빈"], ts.DEFAULT_METRICS)
        self.assertEqual({k: m["글자"][k] for k in ("font_space", "break_hangul", "break_latin", "para_lr")},
                         {"font_space": True, "break_hangul": True, "break_latin": True, "para_lr": 300})   # 들여쓰기는 더함
        self.assertEqual((m["어절"]["break_hangul"], m["어절"]["break_latin"]), (False, False))

    def test_style_metrics_from_hwpml(self):
        """템플릿 HWPML → hwpml_parse.style_defs → style_metrics: 글꼴(한글·라틴)·장평·자간·진하게·글꼴 빈칸·줄 나눔 기준·여백,
        언어별 글꼴·글꼴 종류·장평·자간·상대 크기(slots, P-045) — 빠진 언어·값은 한글 값."""
        import xml.etree.ElementTree as ET
        x = ('<HWPML><HEAD><MAPPINGTABLE><FACENAMELIST><FONTFACE Lang="Hangul"><FONT Id="0" Name="한글체" Type="hft"/>'
             '</FONTFACE><FONTFACE Lang="Latin"><FONT Id="0" Name="라틴체" Type="ttf"/></FONTFACE><FONTFACE Lang="Symbol">'
             '<FONT Id="0" Name="기호체" Type="ttf"/></FONTFACE></FACENAMELIST><CHARSHAPELIST>'
             '<CHARSHAPE Id="0" Height="900" UseFontSpace="true"><FONTID Hangul="0" Latin="0" Symbol="0"/>'
             '<RATIO Hangul="95" Latin="100" Symbol="90"/><CHARSPACING Hangul="-5" Latin="0"/>'
             '<RELSIZE Hangul="100" Symbol="120"/><BOLD/></CHARSHAPE><CHARSHAPE Id="1" Height="1000" UseFontSpace="false"/>'
             '</CHARSHAPELIST><PARASHAPELIST><PARASHAPE Id="0" Align="Center" BreakLatinWord="BreakWord" '
             'BreakNonLatinWord="true"><PARAMARGIN Left="200" Right="100" Indent="-300"/></PARASHAPE>'
             '<PARASHAPE Id="1" Align="Justify" BreakLatinWord="KeepWord" BreakNonLatinWord="false"/></PARASHAPELIST>'
             '<STYLELIST><STYLE Id="0" Name="05" ParaShape="0" CharShape="0"/><STYLE Id="1" Name="06" ParaShape="1" '
             'CharShape="1"/></STYLELIST></MAPPINGTABLE></HEAD></HWPML>')
        m = ts.style_metrics(ts.hp.style_defs(ET.fromstring(x)))
        slots = m["05"].pop("slots")
        self.assertEqual(m["05"], {"height": 900, "ratio": 95.0, "spacing": -5.0, "bold": True, "hangul": "한글체",
                                   "latin": "라틴체", "font_space": True, "break_hangul": True, "break_latin": True,
                                   "para_lr": 300, "m_left": 200, "m_right": 100, "m_indent": -300})
        hangul = {"face": "한글체", "type": "hft", "ratio": 95.0, "spacing": -5.0, "relsize": 100.0}
        self.assertEqual(slots, {"hangul": hangul, "latin": {"face": "라틴체", "type": "ttf", "ratio": 100.0, "spacing": 0.0,
                                                             "relsize": 100.0},
                                 "symbol": {"face": "기호체", "type": "ttf", "ratio": 90.0, "spacing": -5.0, "relsize": 120.0},
                                 "hanja": hangul, "japanese": hangul, "other": hangul, "user": hangul})
        self.assertEqual({k: m["06"][k] for k in ("font_space", "break_hangul", "break_latin", "para_lr")},
                         {"font_space": False, "break_hangul": False, "break_latin": False, "para_lr": 0})
        self.assertNotIn("slots", m["06"])                                   # 언어별 값이 없으면 넣지 않는다(옛 셈)

    def test_unbreakable(self):
        m = dict(self.M)                                                     # 한글 어절 단위(기본) — 낱말 통째
        self.assertEqual(ts.unbreakable("LAH유무인", m), ["LAH유무인"])
        g = dict(m, break_hangul=True)                                       # 한글 글자 단위 — 라틴 낱말만 통째
        self.assertEqual(ts.unbreakable("문서LAHZZ0005번호", g), ["문", "서", "LAHZZ0005", "번", "호"])
        self.assertEqual(ts.unbreakable("192.168.10.151", g), ["192.168.10.151"])
        self.assertEqual(ts.unbreakable("AB가", dict(g, break_latin=True)), ["A", "B", "가"])   # 영어도 글자 단위
        self.assertEqual(ts.unbreakable("LAH유무인", dict(m, break_latin=True)), ["L", "A", "H", "유무인"])  # 어절+영어 글자
        for t in ("“LAHZZ0005”", "user’s", "₩1,000,000"):  # 따옴표·통화 기호는 라틴 낱말에 붙는다
            self.assertEqual(ts.unbreakable(t, g), [t])
        self.assertEqual(ts.unbreakable("ＬＡ", g), ["Ｌ", "Ａ"])  # 전각 글자는 한글 쪽(글자 단위)
        w = ts.cell_need("유무인복합 LAHZZ0005", g, 0)[1]                     # 낱말 너비 = 가장 긴 조각(라틴 낱말)
        self.assertEqual(w, ts.cell_need("LAHZZ0005", g, 0)[1])
        self.assertGreater(ts.cell_need("유무인복합 LAH", m, 0)[1], ts.cell_need("유무인복합 LAH", g, 0)[1])

    def test_script_runs(self):
        L, H = ("latin",), ("hangul",)
        self.assertEqual(ts.script_runs("MBS 유무인 복합 192.168.10.1"), [(L, "MBS "), (H, "유무인 복합 "), (L, "192.168.10.1")])
        self.assertEqual(ts.script_runs(" 가"), [(H, " 가")])
        self.assertEqual(ts.script_runs("  "), [(H, "  ")])                    # 공백뿐이면 한글
        self.assertEqual(ts.script_runs(""), [])
        self.assertEqual(ts.script_runs("시험·평가 → 漢"),                      # 언어 후보가 같은 글자끼리(P-045)
                         [(H, "시험"), (ts.UNSURE, "·"), (H, "평가 "), (ts.UNSURE, "→ "), (("hanja",), "漢")])
        import unicodedata
        self.assertEqual(ts.text_hu(unicodedata.normalize("NFD", "가나"), dict(self.M))[0], 2000.0)   # 풀어쓴 한글도 글자 둘

    def test_estimate_and_ratio_spacing(self):
        m = dict(self.M, height=1000)
        self.assertEqual(ts.text_hu("장비명", m), (3000.0, "estimate"))       # 한글 1em
        self.assertAlmostEqual(ts.text_hu("MBS", m)[0], 2100.0)              # 대문자 0.7em
        w = ts.text_hu("장비", dict(m, ratio=90.0, spacing=-5.0))[0]           # 장평 90% · 자간 -5% → 글자마다 0.85em
        self.assertAlmostEqual(w, 1700.0)
        self.assertAlmostEqual(ts.text_hu("가", dict(m, bold=True))[0], 1050.0)

    def test_char_langs(self):
        """글자 → 한/글이 그 글자를 그리는 언어 후보(P-045): 정해진 범위는 하나, 기호·외국 글자 등은 후보 여럿(UNSURE)."""
        for ch, want in (("A", ("latin",)), ("~", ("latin",)), ("\x7f", ("latin",)), ("가", ("hangul",)),
                         ("ㄱ", ("hangul",)), ("\u1100", ("hangul",)), ("\ud7a3", ("hangul",)), ("ﾡ", ("hangul",)),
                         ("\ua960", ("hangul",)), ("\u31f0", ("japanese",)),
                         ("漢", ("hanja",)), ("\u3400", ("hanja",)), ("\uf900", ("hanja",)), ("\U00020000", ("hanja",)),
                         ("カ", ("japanese",)), ("ぁ", ("japanese",)), ("ｶ", ("japanese",)), ("\ue000", ("user", "symbol"))):
            self.assertEqual(ts.char_langs(ch), want, repr(ch))
        for ch in "\x80·×°éαЖ“”→①※「ＡⅠ€\u2e80\U0001f600":
            self.assertEqual(ts.char_langs(ch), ts.UNSURE, repr(ch))
        self.assertEqual(sorted(ts.UNSURE), ["hangul", "latin", "other", "symbol"])
        self.assertEqual(ts.LANGS, ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user"))

    def test_language_values_estimate(self):
        """언어별 글자 모양(P-045, F-152) — 글자마다 그 언어의 장평·자간·상대 크기로. 언어가 정해지지 않은 글자는 후보 언어
        중 가장 넓은 값 — 어림에서 라틴은 글자 종류별, 그 밖 언어는 전각(1em)."""
        one = {"face": None, "type": None, "ratio": 100.0, "spacing": 0.0, "relsize": 100.0}
        slots = {k: dict(one) for k in ts.LANGS}
        slots["hangul"].update(ratio=80.0, spacing=-10.0)
        slots["latin"].update(relsize=110.0)
        m = dict(self.M, slots=slots)
        self.assertAlmostEqual(ts.text_hu("가", m)[0], 1000 * 0.8 - 100)        # 한글: 1em × 장평 80% + 자간 -10%
        self.assertAlmostEqual(ts.text_hu("A", m)[0], 0.70 * 1100)              # 라틴: 대문자 0.7em × 상대 크기 110%
        self.assertAlmostEqual(ts.text_hu("가A", m)[0], 700 + 770)
        self.assertAlmostEqual(ts.text_hu("·", m)[0], 1000.0)                   # 라틴 0.45×1100 · 한글 700 · 기호 1000 → 1000
        self.assertAlmostEqual(ts.text_hu("··", m)[0], 2000.0)                  # 한 글자씩
        self.assertAlmostEqual(ts.text_hu("가 나", m)[0], 2 * 700 + 0.5 * 800 - 100)   # 빈칸은 붙은 쪽(한글) 값 — 고정 폭 0.5em
        slots["symbol"].update(relsize=150.0, spacing=-20.0)
        self.assertAlmostEqual(ts.text_hu("※", m)[0], 1500 - 300)               # 가장 넓은 후보(기호 1.5em - 자간)
        self.assertEqual(ts.text_hu("가·", dict(self.M))[0], 2000.0)             # 언어별 값이 없으면 한글·라틴 값(옛 셈) — '·'도 1em

    def test_language_fonts_measured(self):
        """글꼴로 잴 때(GDI) 글자마다 그 언어 글꼴로 — 언어가 정해지지 않은 글자는 후보 언어 글꼴마다 재어 가장 넓게. 후보 중
        하나라도 못 재면 그 언어는 어림(전각)이고 재기 방법은 estimate."""
        one = {"type": None, "ratio": 100.0, "spacing": 0.0, "relsize": 100.0}
        slots = {k: dict(one, face="F-" + k) for k in ts.LANGS}
        widths = {"F-latin": 0.3, "F-symbol": 0.6, "F-other": 0.4, "F-hangul": 0.5}
        calls = []

        def measure(text, face, bold):
            calls.append((text, face))
            return widths.get(face, 1.0) * len(text)
        w, how = ts.text_hu("A·B", dict(self.M, slots=slots), measure)
        self.assertEqual((w, how), ((0.3 + 0.6 + 0.3) * 1000, "gdi"))
        self.assertEqual(calls, [("A", "F-latin"), ("·", "F-latin"), ("·", "F-symbol"), ("·", "F-other"),
                                 ("·", "F-hangul"), ("B", "F-latin")])
        w, how = ts.text_hu("·", dict(self.M, slots=slots), lambda t, f, b: None if f == "F-other" else 0.2)
        self.assertEqual((w, how), (1000.0, "estimate"))                     # 외국어 글꼴을 못 잼 → 전각 어림이 가장 넓다
        per = {("·", "F-symbol"): 0.6, ("→", "F-latin"): 0.9}               # 글자마다 가장 넓은 언어가 다르다
        w, _ = ts.text_hu("·→", dict(self.M, slots=slots), lambda t, f, b: sum(per.get((ch, f), 0.2) for ch in t))
        self.assertAlmostEqual(w, (0.6 + 0.9) * 1000)                        # 한 글자씩(묶어 재면 라틴 1.1·기호 0.8 → 1.1)
        per = {("\ue000", "F-user"): 0.9, ("\ue001", "F-symbol"): 0.8}     # 사용자 영역(후보 사용자·기호)도 한 글자씩
        w, _ = ts.text_hu("\ue000\ue001", dict(self.M, slots=slots), lambda t, f, b: sum(per.get((ch, f), 0.1) for ch in t))
        self.assertAlmostEqual(w, (0.9 + 0.8) * 1000)

    def test_space_by_language(self):
        """빈칸 폭은 언어마다 다르다(P-045): 낱말 사이 빈칸은 붙은 글자 언어로(gap_hu — text_hu 와 같게), 칸 여유(빈칸 2칸)는
        칸 글자에 쓰인 언어 중 가장 넓은 빈칸으로(space_hu). 라틴 빈칸이 한글보다 넓은 스타일에서 라틴 칸 줄 수를 적게,
        한글 칸 줄 수를 넉넉히 어림하지 않게(검토 D1-①-01·D1F-01)."""
        one = {"face": None, "type": None, "ratio": 85.0, "spacing": -3.0, "relsize": 100.0}
        slots = {k: dict(one) for k in ts.LANGS}
        slots["latin"].update(ratio=100.0, spacing=0.0)
        m = dict(self.M, slots=slots)
        self.assertEqual([ts.space_hu(m, text=t)[0] for t in ("A", "가", "가 A", "", " ", "·")],
                         [500.0, 395.0, 500.0, 395.0, 395.0, 500.0])          # 라틴 0.5em = 500 · 한글 425 - 30 = 395
        self.assertEqual((ts.gap_hu("  ", "A", m), ts.gap_hu(" ", "가", m), ts.gap_hu(" ", "·", m), ts.gap_hu("", "A", m)),
                         (1000.0, 395.0, 500.0, 0.0))
        self.assertEqual([ts.space_hu(m, text=t)[0] for t in ("가\n나", "가\nA")], [395.0, 500.0])   # 칸 안 줄 모두, 줄바꿈은 빼고
        text = "TCP UDP HTTP FTP SSH DNS NTP SNMP LDAP SMTP IMAP POP3 RTSP"
        cell = ts.cell_layout(text, m, 1020)
        self.assertEqual(({g for g, _ in cell["lines"][0][1:]}, cell["pad"]), ({500.0}, 2 * 500 + 1020))
        self.assertEqual(cell["need"], ts.cell_need(text, m, 1020)[0])
        a = ts.text_hu("A", m)[0]                                             # 칸 여유 = 칸 글자 언어 빈칸 2칸
        self.assertEqual(ts.cell_need("A", m, 1020)[0], int(__import__("math").ceil(a * ts.SAFETY["estimate"] + 2 * 500 + 1020)))
        b = ts.text_hu("가 A", m)[0]                                          # 칸 안 언어 중 가장 넓은 빈칸(라틴) — 첫 글자가 아니라
        self.assertEqual(ts.cell_need("가 A", m, 0)[0], int(__import__("math").ceil(b * ts.SAFETY["estimate"] + 2 * 500)))
        self.assertEqual(ts.cell_layout("가 A", m, 0)["pad"], 1000.0)
        self.assertEqual(ts.lines_at(cell, 22505), 3)                         # 한글 빈칸(395)으로 세면 2줄로 적게 어림
        han = ts.cell_layout("가나 다라 마바", m, 0)                            # 글자 820 · 낱말 1640 · 한글 빈칸 395
        self.assertEqual((han["lines"], han["pad"]), ([[(0.0, [1640.0]), (395.0, [1640.0]), (395.0, [1640.0])]], 790.0))
        self.assertEqual(ts.lines_at(han, 3675, True), 2)                      # 1640 + 395 + 1640 — 라틴 빈칸(500)으로 세면 3줄
        self.assertEqual(ts.lines_at(han, 3674, True), 3)
        mix = ts.cell_layout("AB 가 ·", m, 0)                                   # 빈칸은 앞 글자 언어 — 라틴·한글
        self.assertEqual([g for g, _ in mix["lines"][0]], [0.0, 500.0, 395.0])
        self.assertEqual([g for g, _ in ts.cell_layout("IP를 설정 SW로 시험", m, 0)["lines"][0]],
                         [0.0, 395.0, 395.0, 395.0])                          # 앞 낱말의 끝 글자(를·정·로 — 한글)
        self.assertEqual(sum(g + sum(ps) for g, ps in mix["lines"][0]), ts.text_hu("AB 가 ·", m)[0])   # text_hu 와 같은 폭
        lead = ts.cell_layout("  가", m, 0)                                    # 줄 첫머리 빈칸은 뒤 글자 언어
        self.assertEqual(lead["lines"], [[(790.0, [820.0])]])
        self.assertEqual(ts.cell_layout("  A", m, 0)["lines"][0][0][0], 1000.0)
        self.assertEqual(ts.cell_layout("  IP를", m, 0)["lines"][0][0][0], 1000.0)   # 뒤 낱말의 첫 글자(I) — 끝 글자(를)가 아니라
        self.assertEqual([ln[0][0] for ln in ts.cell_layout("가\n  A", m, 0)["lines"]], [0.0, 1000.0])   # 칸 안 줄마다 처음부터
        wide = {k: dict(v) for k, v in slots.items()}
        wide["symbol"].update(ratio=100.0, spacing=0.0, relsize=120.0)
        self.assertEqual(ts.gap_hu(" ", "·", dict(m, slots=wide)), 600.0)    # 후보 중 가장 넓은 언어(기호 1.2배)
        self.assertEqual(ts.space_hu(dict(m, slots=wide), text="·"), (600.0, "gdi"))
        neg = {k: dict(one, ratio=100.0, spacing=0.0) for k in ts.LANGS}
        neg["hangul"].update(ratio=85.0, spacing=-45.0)                     # 빈칸 425 - 450 = -25 — 여유는 0 아래로 안 내림
        mneg = dict(self.M, slots=neg)
        self.assertEqual(ts.space_hu(mneg, text="가"), (0.0, "gdi"))
        lay = ts.cell_layout("가", mneg, 1020)
        self.assertEqual(lay["pad"], 1020)
        self.assertGreaterEqual(lay["need"], lay["need_real"])                # 보수 어림 ≥ 실제 어림(검토 D2-①-01)
        w, how = ts.space_hu(dict(self.M, font_space=True), lambda t, f, b: {"한글체": 0.3, "라틴체": 0.4}.get(f), "가A")
        self.assertEqual((w, how), (400.0, "gdi"))                            # 글꼴 빈칸: 칸 글자 언어 글꼴마다 재어 가장 넓게

    def test_font_space_absent_language_not_measured(self):
        """'글꼴에 어울리는 빈칸'을 켠 스타일: 칸에 없는 언어의 글꼴은 재지 않는다 — 못 재는 글꼴(HFT) 하나 때문에 칸 전체가
        어림이 되지 않게(검토 P-045 D1F-02)."""
        one = {"type": None, "ratio": 100.0, "spacing": 0.0, "relsize": 100.0}
        slots = {k: dict(one, face="F-" + k) for k in ts.LANGS}
        tried = set()

        def measure(text, face, bold):
            tried.add(face)
            return None if face == "F-user" else 0.5 * len(text)
        m = dict(self.M, slots=slots, font_space=True)
        self.assertEqual(ts.cell_need("가나다라 ABCD", m, 0, measure)[2], "gdi")
        self.assertEqual(ts.cell_layout("가나다라 ABCD", m, 0, measure)["k"], ts.SAFETY["gdi"])
        self.assertEqual(tried, {"F-hangul", "F-latin"})

    def test_space_estimate_in_any_language(self):
        """'글꼴에 어울리는 빈칸'을 켠 스타일을 어림할 때 빈칸은 어느 언어 쪽이든 빈칸 폭(전각이 아님)."""
        m = dict(self.M, font_space=True)
        self.assertAlmostEqual(ts.text_hu("가 나", m)[0], (2 + ts.EST_EM["space"]) * 1000)
        self.assertAlmostEqual(ts.text_hu("A B", m)[0], (2 * 0.70 + ts.EST_EM["space"]) * 1000)

    def test_measure_used_per_script(self):
        calls = []

        def measure(text, face, bold):
            calls.append((text, face))
            return 0.5 * len(text) if face == "라틴체" else 1.0 * len(text)
        w, how = ts.text_hu("MBS 장비", self.M, measure)
        self.assertEqual((w, how), ((0.5 * 3 + ts.HWP_SPACE_EM + 2.0) * 1000, "gdi"))   # 빈칸은 한/글 고정 폭(글꼴 빈칸 끔)
        self.assertEqual(calls, [("MBS", "라틴체"), ("장비", "한글체")])
        calls.clear()
        w, _ = ts.text_hu("MBS 장비", dict(self.M, font_space=True), measure)              # '글꼴에 어울리는 빈칸' — 글꼴로
        self.assertEqual((w, calls), ((0.5 * 4 + 2.0) * 1000, [("MBS ", "라틴체"), ("장비", "한글체")]))
        w, how = ts.text_hu("MBS 장비", self.M, lambda t, f, b: None)            # 글꼴을 못 잼 → 어림
        self.assertEqual(how, "estimate")

    def test_cell_need_slack_and_margins(self):
        m = dict(self.M)
        full, word, how = ts.cell_need("가나 다라마\n바", m, 1076)
        sp = ts.HWP_SPACE_EM * 1000                                           # 한/글 빈칸 = 글자 크기 절반
        self.assertEqual(full, int(__import__("math").ceil((5 + ts.HWP_SPACE_EM) * 1000 * ts.SAFETY["estimate"]
                                                           + ts.SLACK_SPACES * sp + 1076)))
        self.assertEqual(word, int(__import__("math").ceil(3000 * ts.SAFETY["estimate"] + ts.SLACK_SPACES * sp + 1076)))
        g = ts.cell_need("가나", m, 0, lambda t, f, b: 1.0 * len(t))          # 잰 폭: 덧붙임 1.02, 여유 = 빈칸 2칸(0.5em씩)
        self.assertEqual(g, (int(__import__("math").ceil(2000 * 1.02 + 1000)), int(__import__("math").ceil(2000 * 1.02 + 1000)),
                             "gdi"))
        self.assertEqual(ts.cell_need("가나", m, 0, lambda t, f, b: 1 / 0)[2], "estimate")   # 재다가 오류 → 어림

    def test_fit_table_how_ignores_blank_cells(self):
        """빈 칸은 잰 것도 어림한 것도 없다 — 표의 재기 방법(how)에 넣지 않는다(검토 P-045 D1-②-03: 빈 칸 때문에 'mixed')."""
        styles = [["06", "06"], ["06", "06"]]
        self.assertEqual(ts.fit_table([["가", ""], [" ", "나"]], styles, {}, 43370)["how"], "estimate")
        self.assertEqual(ts.fit_table([["A", ""], ["", "B"]], styles, {"06": {"latin": "라틴체"}}, 43370,
                                      measure=lambda t, f, b: 0.5 * len(t) if f else None)["how"], "gdi")
        self.assertEqual(ts.fit_table([["", ""]], [["06", "06"]], {}, 43370)["how"], "estimate")   # 모두 비면 어림으로
        self.assertEqual(ts.fit_table([["A", "가"]], [["06", "06"]], {"06": {"latin": "라틴체"}}, 43370,
                                      measure=lambda t, f, b: 0.5 * len(t) if f == "라틴체" else None)["how"], "mixed")

    def test_fit_columns(self):
        self.assertEqual(ts.fit_columns([8000, 9000], [5000, 6000], 43370), ([8000, 9000], False))   # 좁은 표 그대로
        w, capped = ts.fit_columns([8000, 9000, 60000], [5000, 6000, 9000], 43370)
        self.assertEqual((w, capped), ([8000, 9000, 26370], True))           # 짧은 칸은 그대로, 긴 글 칸만 줄어 줄바꿈
        w, _ = ts.fit_columns([8000, 40000, 30000], [5000, 9000, 9000], 43370)  # 긴 칸 둘 — 같은 너비 T 로 줄임
        self.assertEqual(w, [8000, 17685, 17685])
        w, _ = ts.fit_columns([8000, 40000, 30000], [5000, 9000, 20000], 43370)  # T 가 낱말 너비보다 작으면 낱말 너비
        self.assertEqual(w, [8000, 15370, 20000])
        w, _ = ts.fit_columns([8000, 20000, 30000], [5000, 9000, 9000], 43370)   # T(17685) 넘는 칸 둘 — 같은 너비
        self.assertEqual(w, [8000, 17685, 17685])
        w, _ = ts.fit_columns([8000, 15000, 60000], [5000, 9000, 9000], 43370)   # 덜 긴 칸(15000)은 T 아래 — 그대로
        self.assertEqual(w, [8000, 15000, 20370])
        w, _ = ts.fit_columns([6396, 8319, 61207, 4236, 7973, 12768], [6396, 8319, 12282, 4236, 7973, 12768], 43370)
        self.assertEqual(w, [6396, 8319, 8223, 4236, 7973, 8223])            # SUM 비정부문서(가짜 SUM P-041): 문서번호
        # LAHZZ0005(8319)는 낱말 그대로(앞 방식은 2503 으로 눌렀다). 하한 모두는 합이 넘치고, 12768 만 버리면 발행처 칸이
        # 4164(T0 8255 의 80% 아래)로 눌려 12282 도 버린다 → T 8223
        w, _ = ts.fit_columns([8319, 200000, 9000, 9000, 9000, 9000], [8319, 60000, 3156, 3156, 3156, 3156], 43370)
        self.assertEqual(w, [8319, 7011, 7010, 7010, 7010, 7010])            # 검토 P-041 2차 4 — 앞 방식은 첫 칸 1476
        w, _ = ts.fit_columns([34228, 40000, 40000], [34228, 3100, 3100], 43370)   # 긴 경로(낱말 하나) 칸이 설명 칸을
        self.assertEqual(w, [14457, 14457, 14456])                           # 누르지 않는다(검토 P-041 2차 1 — 앞: 4571)
        w, _ = ts.fit_columns([5316, 16000, 60000, 30000, 30000], [5316, 13838, 42000, 3000, 3000], 43370)
        self.assertEqual(w, [5316, 13838, 8072, 8072, 8072])                 # 못 지킬 경로 하한만 버리고 IP 주소 하한은 지킴
        w, _ = ts.fit_columns([12000, 30000], [8000, 12000], 20000)           # 하한 합 = 상한, T = T0×0.8 — 낱말 너비 그대로
        self.assertEqual(w, [8000, 12000])
        w, _ = ts.fit_columns([12000, 30000], [6000, 14000], 20000)           # 지키면 T 6000 < T0(10000)×0.8 — 하한 버림
        self.assertEqual(w, [10000, 10000])
        w, _ = ts.fit_columns([30000, 12000], [6000, 11000], 20000)           # 낱말 하한(11000)은 지키고 나머지를 긴 칸에
        self.assertEqual(w, [9000, 11000])
        w, capped = ts.fit_columns([14169, 14601, 14601], [9000, 9000, 9000], 43370)   # 가장 긴 칸이 같고 1 넘침(검토 P-041 M1)
        self.assertEqual((w, capped), ([14169, 14601, 14600], True))
        w, _ = ts.fit_columns([2600, 9000, 60000, 3500], [2600, 9000, 58000, 3500], 43370)  # 긴 낱말(경로) — 짧은 칸은 그대로
        self.assertEqual(w, [2600, 9000, 28270, 3500])
        w, _ = ts.fit_columns([3000, 40000, 40000], [3000, 38000, 38000], 43370)   # 긴 낱말 칸 둘 — 낱말 아래로 나눠 줄임
        self.assertEqual(w, [3000, 20185, 20185])
        w, _ = ts.fit_columns([30000, 30000], [30000, 20000], 43370)          # 하한 합이 넘침 → 30000 버림, 20000 은 T 아래
        self.assertEqual(w, [21685, 21685])
        w, _ = ts.fit_columns([5000, 20000, 20000, 20000], [5000, 15000, 15000, 15000], 43370)   # 같은 칸 셋 — 같은 하한은
        self.assertEqual(w, [5000, 12790, 12790, 12790])                     # 함께 버린다(하나만 버리면 그 칸만 8370)
        w, _ = ts.fit_columns([5000, 20000, 20000, 20000], [5000, 15001, 15000, 15000], 43370)   # 거의 같으면: 15001 을
        self.assertEqual(w, [5000, 12790, 12790, 12790])                     # 버려도 T 8370 < 80% → 15000 들도 버림
        self.assertEqual(ts.fit_columns([], [], 100), ([], False))
        w, _ = ts.fit_columns([20000] * 3, [2000, 1300, 1300], 3700)         # 하한을 지켜도 MIN_CELL 아래로는 안 줄임(검토 P-041 3차 3)
        self.assertEqual((w, min(w) >= ts.MIN_CELL - 1), ([1234, 1233, 1233], True))
        import subprocess                                                    # 음수 상한 — 끝난다(검토 3차 4). 안 끝나면
        code = ("import sys; sys.path.insert(0, %r); import table_style as ts; "  # 시험이 멈추지 않고 실패하게 따로 돌린다
                "print(ts.fit_columns([5000, 6000], [100, 100], -10))" % str(Path(ts.__file__).resolve().parent))
        try:
            got = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30).stdout.strip()
        except subprocess.TimeoutExpired:
            got = "시간초과(끝나지 않음)"
        self.assertEqual(got, "([0, 0], True)")

    def test_fit_columns_properties(self):
        """여러 입력에서: 합 = 상한, 필요한 너비 넘지 않음. 지킨 하한 = 어떤 값 이하 모두(큰 하한부터 버림)이고 그 칸은 하한
        이상, T 는 T0 의 FLOOR_KEEP 이상. 하한 없으면: 필요한 너비가 큰 칸이 작은 칸보다 좁지 않고 줄인 칸끼리 같은 너비
        (1 차이까지). 필요한 너비·하한이 같은 칸은 같은 너비(1 차이까지)."""
        import random
        rnd = random.Random(41)
        for k in range(600):
            n = rnd.randint(1, 7)
            maxw = [rnd.randint(1500, 90000) for _ in range(n)]
            minw = [rnd.randint(1200, x) for x in maxw] if k % 3 else [1] * n
            if n > 2 and k % 5 == 0:                                         # 같은 칸 둘
                maxw[1], minw[1] = maxw[0], minw[0]
            avail = rnd.randint(1200 * n, 60000)
            w, capped = ts.fit_columns(maxw, minw, avail)
            info = (maxw, minw, avail, w)
            self.assertEqual(capped, sum(maxw) > avail)
            self.assertEqual(sum(w), sum(maxw) if not capped else avail)
            self.assertTrue(all(0 <= a <= x for a, x in zip(w, maxw)), info)
            for i in range(n):
                for j in range(n):
                    if maxw[i] == maxw[j] and minw[i] == minw[j]:
                        self.assertLessEqual(abs(w[i] - w[j]), 1, info)
            if not capped:
                continue
            t0 = ts.level(maxw, [0] * n, avail)
            kept = [i for i in range(n) if w[i] >= minw[i]]
            dropped = [i for i in range(n) if w[i] < minw[i]]
            if dropped:                                                      # 버린 하한은 지킨 하한보다 작지 않다
                self.assertGreaterEqual(min(minw[i] for i in dropped), max([minw[i] for i in kept] or [0]), info)
            free = [i for i in range(n) if w[i] < maxw[i] and (w[i] > minw[i] + 1 or i in dropped)]
            if free:                                                         # 하한에 걸리지 않고 줄인 칸 = T
                t = min(w[i] for i in free)
                self.assertLessEqual(max(w[i] for i in free) - t, 1, info)
                self.assertGreaterEqual(t, ts.FLOOR_KEEP * t0 - 2, info)
                for j in range(n):                                           # 줄이지 않은 칸(하한 칸 빼고)은 T 보다 넓지 않다
                    if j not in free and not (w[j] <= minw[j] + 1 and j not in dropped):
                        self.assertLessEqual(w[j], t + 1, info)
            if minw == [1] * n:
                for i in range(n):
                    for j in range(n):
                        if maxw[i] >= maxw[j]:
                            self.assertGreaterEqual(w[i], w[j] - 1, info)

    def test_lines_at(self):
        """줄 수 어림 — 보수(빈칸 2칸 남김·덧붙임) / 실제(칸 안을 다 채움). 낱말 사이 빈칸(여럿이면 그 폭), 줄 넘김 뒤 첫머리
        빈칸은 버림, 한 줄보다 긴 조각은 글자로 끊김, 칸 안 줄(<br>), 한 줄 너비 아래면 적어도 한 줄 더(검토 P-041 3차 2)."""
        cell = {"lines": [[(0, [3000]), (500, [3000]), (500, [3000])]], "k": 1.0, "pad": 1000, "margins": 0,
                "need": 11000, "need_real": 10000}
        self.assertEqual([ts.lines_at(cell, w) for w in (11000, 10999, 7500, 7499, 4000, 3999, 1000)],
                         [1, 2, 2, 3, 3, 6, 10 ** 6])
        self.assertEqual([ts.lines_at(cell, w, True) for w in (10000, 9999, 6500, 6499, 3000, 2999)], [1, 2, 2, 3, 3, 6])
        k2 = dict(cell, k=2.0, need=22000)                                    # 덧붙임은 보수 어림에만
        self.assertEqual((ts.lines_at(k2, 13000), ts.lines_at(k2, 13000, True)), (3, 1))
        self.assertEqual((ts.lines_at(k2, 13500), ts.lines_at(k2, 14000)), (3, 2))   # 빈칸 폭에도 덧붙임(6000+1000+6000)
        lead2 = {"lines": [[(1000, [3000]), (500, [1000])]], "k": 2.0, "pad": 0, "margins": 0, "need": 99999,
                 "need_real": 99999}                                         # 줄 첫머리 빈칸에도 덧붙임: 2000 + 6000 > 7500
        self.assertEqual(ts.lines_at(lead2, 7500), 3)
        self.assertEqual(ts.lines_at(lead2, 4000, True), 2)                  # 실제 어림은 덧붙임 없이: 1000 + 3000 | 500 + 1000
        gaps = {"lines": [[(0, [1000]), (3000, [1000])]], "k": 1.0, "pad": 0, "margins": 0, "need": 5000,
                "need_real": 5000}                                            # 빈칸 여섯 — 그 폭대로, 줄 넘기면 버림
        self.assertEqual((ts.lines_at(gaps, 5000), ts.lines_at(gaps, 4999), ts.lines_at(gaps, 2000)), (1, 2, 2))
        one = {"lines": [[(0, [10000])]], "k": 1.0, "pad": 0, "margins": 0, "need": 10000, "need_real": 10000}
        self.assertEqual(ts.lines_at(one, 4000), 3)                           # 한 줄보다 긴 조각은 글자로 끊김
        two = {"lines": [[(0, [1000])], [(0, [1000])]], "k": 1.0, "pad": 0, "margins": 0, "need": 1000,
               "need_real": 1000}
        self.assertEqual((ts.lines_at(two, 1000), ts.lines_at(two, 999)), (2, 4))   # <br> 둘 = 두 줄
        self.assertEqual(ts.lines_at({"lines": [[]], "k": 1.0, "pad": 0, "margins": 0, "need": 0,
                                      "need_real": 0}, 3), 1)                 # 빈 칸
        glued = {"lines": [[(0, [1000, 1000, 1000])]], "k": 1.0, "pad": 0, "margins": 0, "need": 3000,
                 "need_real": 3000}                                           # 한 낱말의 조각 셋(글자 단위) — 사이 빈칸 없음
        self.assertEqual(ts.lines_at(glued, 2000), 2)
        self.assertEqual(ts.lines_at(dict(glued, lines=[[(0, [1000]), (500, [1000]), (500, [1000])]], need=4000), 2000), 3)
        self.assertEqual((ts.min_width(cell, 2, 1000, 11000), ts.min_width(cell, 1, 1000, 11000),
                          ts.min_width(cell, 3, 1000, 11000), ts.min_width(cell, 3, 5000, 11000),
                          ts.min_width(cell, 2, 1000, 10000, True)), (7500, 11000, 4000, 5000, 6500))
        m = dict(self.M)
        lay = ts.cell_layout("가나 다라\n마", m, 1020)                    # cell_need 와 같은 기준
        self.assertEqual(lay["need"], ts.cell_need("가나 다라\n마", m, 1020)[0])
        self.assertEqual((lay["lines"], lay["k"], lay["pad"], lay["margins"], lay["need_real"]),
                         ([[(0, [2000.0]), (500.0, [2000.0])], [(0, [1000.0])]], 1.08, 2020.0, 1020, 5520))
        self.assertEqual((ts.lines_at(lay, lay["need"]), ts.lines_at(lay, lay["need"] - 1)), (2, 3))
        self.assertEqual((ts.lines_at(lay, lay["need_real"], True), ts.lines_at(lay, lay["need_real"] - 1, True)), (2, 3))
        import unicodedata
        nfd = ts.cell_layout(unicodedata.normalize("NFD", "가나"), dict(m, break_hangul=True), 0)
        self.assertEqual(nfd["lines"], [[(0, [1000.0, 1000.0])]])            # 풀어쓴 한글도 글자 둘(검토 P-041 3차 2)
        self.assertEqual(ts.cell_need(unicodedata.normalize("NFD", "가나"), dict(m, break_hangul=True), 0)[1],
                         ts.cell_need("가나", dict(m, break_hangul=True), 0)[1])
        sp6 = ts.cell_layout("성      명", m, 0)                              # 빈칸 여섯(검토 P-041 3차 2)
        self.assertEqual(sp6["lines"], [[(0, [1000.0]), (3000.0, [1000.0])]])
        self.assertEqual(ts.lines_at(sp6, sp6["need"] - 1), 2)
        lead = ts.cell_layout("가\n  바H 나", dict(m, break_hangul=True), 1020)   # 칸 안 줄 첫머리 빈칸 — 너비가 늘면 줄 수는
        for real in (False, True):                                           # 줄거나 같다(검토 P-041 4차)
            got = [ts.lines_at(lead, x, real) for x in range(1100, 8000)]
            self.assertTrue(all(a >= b for a, b in zip(got, got[1:])), real)
        tail = ts.cell_layout("가나 ", m, 0)                                  # 끝 빈칸은 조각이 없지만 한 줄 너비(need)에는 든다 —
        self.assertEqual(ts.lines_at(tail, tail["need"] - 1), 2)              # 그 아래면 적어도 한 줄 더(보수, 어림이 서로 맞게)

    def test_refine_lines(self):
        """긴 칸끼리 같은 너비(max-min) → 줄 높이를 정하지 않는 칸을 좁혀(그 줄 높이 - 1 줄까지) 가장 긴 칸을 넓힌다."""
        C = lambda words, need, pad=0: {"lines": [[(0, [x]) for x in words]], "k": 1.0, "pad": pad,
                                        "margins": 0, "need": need + pad, "need_real": need}
        cells = [[C([2000], 2000), C([2000], 2000)], [C([3000] * 3, 9000), C([3000] * 8, 24000)]]
        self.assertEqual(ts.table_height(cells, [6000, 6000]), 5)            # 1 + 4(둘째 칸 여덟 낱말 → 네 줄)
        self.assertEqual(ts.refine_lines(cells, [6000, 6000], [9000, 24000], [0, 0], 12000),
                         ([3000, 9000], {"before": [5, 5], "after": [4, 4]}))
        head = [[C([4000], 4000), C([2000], 2000)], cells[1]]                # 한 줄짜리 제목 줄은 그대로 — 첫 칸 4000 아래로 못 줄임
        self.assertEqual(ts.refine_lines(head, [6000, 6000], [9000, 24000], [0, 0], 12000)[0], [6000, 6000])
        self.assertEqual(ts.refine_lines(cells, [6000, 6000], [9000, 24000], [4500, 0], 12000)[0], [6000, 6000])  # 낱말 하한
        three = [[C([1000], 1000)] * 3, [C([3000] * 2, 6000), C([3000] * 3, 9000), C([3000] * 9, 27000)]]
        w, h = ts.refine_lines(three, [6000, 7000, 7000], [6000, 9000, 27000], [0, 0, 0], 20000)
        self.assertEqual((w[0], sum(w), h["before"][0], h["after"][0]), (6000, 20000, 6, 4))   # 줄바꿈 없는 칸은 그대로
        br = [[C([1000], 1000), C([1000], 1000)],
              [dict(C([3000], 3000), lines=[[(0, [3000])]] * 4), C([3000] * 8, 24000)]]   # <br> 넷 — 넷 아래로 못 줄임
        w, h = ts.refine_lines(br, [3000, 12000], [3000, 24000], [0, 0], 15000)   # 둘째 칸을 좁혀도 쓸 데가 없다
        self.assertEqual((w, h["before"], h["after"]), ([3000, 12000], [5, 5], [5, 5]))
        dead = [[C([1000], 1000, 2000), C([1000], 1000, 2000)],              # 보수 어림의 '그대로'인 구간(빈칸 2칸 남김) 안으로
                [C([3000] * 7, 21000, 2000), C([3000] * 20, 60000, 2000)]]   # 좁히면 실제 줄이 는다 — 두 어림 다 지킴
        w, h = ts.refine_lines(dead, [12000, 12000], [23000, 62000], [0, 0], 24000)
        rows = lambda ws, real: [max(ts.lines_at(cl, x, real) for cl, x in zip(row, ws)) for row in dead]
        for real in (False, True):
            self.assertTrue(all(a <= b for a, b in zip(rows(w, real), rows([12000, 12000], real))), (w, real))

    def test_fit_table_refines_rows(self):
        """SUM 표 9 꼴 — 다듬으면 표 높이가 줄고, 어느 줄도 높아지지 않으며, 제목 줄은 한 줄, 합 = 상한."""
        rows = [["구분", "이름", "화면"],
                ["원격 관리 시스템(HW·SW 실행·종료)", "BattleFieldSW, OTW, UAV1, UAV2, UAV3, LAH, PFD1, PFD2", "초기 화면(그림 5)"],
                ["SW 연결 상태 표시 대상", "전장 환경 모의기, LAH 지휘기, OTW, UAV1, UAV2, UAV3", "시나리오 생성&모의 화면(그림 12)"],
                ["초기 화면에서 여는 SW", "시험운용 분석 SW(단위 1), 시험운용 분석 SW(단위 2)", "초기 화면(그림 5)"]]
        for brk in (False, True):
            m = dict(self.M, break_hangul=brk)
            f = ts.fit_table(rows, [["s"] * 3] * 4, {"s": m}, 43370, 1020)
            cells = [[ts.cell_layout(x, m, 1020) for x in row] for row in rows]
            for real in (False, True):
                before = [max(ts.lines_at(cl, x, real) for cl, x in zip(row, f["maxmin"])) for row in cells]
                after = [max(ts.lines_at(cl, x, real) for cl, x in zip(row, f["widths"])) for row in cells]
                self.assertEqual((f["lines"]["before"][real], f["lines"]["after"][real]), (sum(before), sum(after)))
                self.assertTrue(all(a <= b for a, b in zip(after, before)), (before, after))
                self.assertEqual(after[0], 1)
            self.assertTrue(f["capped"])
            self.assertLess(f["lines"]["after"][0], f["lines"]["before"][0])
            self.assertEqual(sum(f["widths"]), 43370)
            self.assertTrue(all(x <= y for x, y in zip(f["widths"], f["need"])))
        self.assertEqual(ts.fit_table([["가", "나"]], [["s", "s"]], {"s": dict(self.M)}, 43370, 1020)["lines"], None)

    def test_refine_random_tables(self):
        """여러 꼴 표(제목 줄·<br>·빈 칸·긴 영문·두 줄 나눔 기준·좁은 상한)에서: 두 어림 모두 어느 줄도 높아지지 않고,
        줄바꿈 없는 칸은 그대로, 합 = 상한, 필요한 너비 이하, MIN_CELL 이상(검토 P-041 3차 1·3)."""
        import random
        import time
        rnd = random.Random(413)
        words = ["시험", "운용", "통제", "시스템", "유무인", "복합", "전장환경", "모의기", "LAH", "BattleFieldSW", "UAV1",
                 "192.168.10.151", "PFD", "시나리오", "생성&모의", "화면(그림", "5)", "-", "설정·편집", "C:\\LMV\\config\\a.ini"]
        cell = lambda k: "\n".join(" ".join(rnd.choice(words) for _ in range(rnd.randint(1, k)))
                                   for _ in range(1 if rnd.random() < .8 else rnd.randint(2, 4))) if rnd.random() > .05 else ""
        t0, n = time.process_time(), 0          # CPU 시간 — 병렬·바쁜 PC 의 벽시계에 흔들리지 않게(검토 P-051 D2-③-N07)
        for k in range(160):
            nc, nr = rnd.randint(2, 6), rnd.randint(2, 9)
            rows = [[rnd.choice(words) for _ in range(nc)]] + [[cell(rnd.choice((2, 4, 12))) for _ in range(nc)]
                                                               for _ in range(nr - 1)]
            m = dict(self.M, break_hangul=bool(k % 2), break_latin=(k % 7 == 0))
            avail = rnd.choice((43370, 30000, ts.MIN_CELL * nc + rnd.randint(0, 3000)))
            f = ts.fit_table(rows, [["s"] * nc] * nr, {"s": m}, avail, 1020)
            if not f["capped"]:
                continue
            n += 1
            cells = [[ts.cell_layout(x, m, 1020) for x in row] for row in rows]
            for real in (False, True):
                before = [max(ts.lines_at(cl, x, real) for cl, x in zip(row, f["maxmin"])) for row in cells]
                after = [max(ts.lines_at(cl, x, real) for cl, x in zip(row, f["widths"])) for row in cells]
                self.assertTrue(all(a <= b for a, b in zip(after, before)), (k, real, before, after))
            self.assertEqual(sum(f["widths"]), max(avail, ts.MIN_CELL * nc))
            for c in range(nc):
                self.assertLessEqual(f["widths"][c], f["need"][c])
                self.assertGreaterEqual(f["widths"][c], ts.MIN_CELL - 1, (k, f["widths"]))
                if f["maxmin"][c] >= f["need"][c]:
                    self.assertEqual(f["widths"][c], f["need"][c])
        self.assertGreater(n, 60)
        self.assertLess(time.process_time() - t0, 20)

    def test_fit_table(self):
        rows = [["식별자", "장비명"], ["MBS", "유무인 복합 전장환경 모의기"]]
        st = [["05", "05"], ["06", "07"]]
        f = ts.fit_table(rows, st, {"05": dict(self.M), "06": dict(self.M), "07": dict(self.M)}, 43370, 1076)
        self.assertEqual((f["how"], f["capped"]), ("estimate", False))
        self.assertEqual(f["widths"], f["need"])
        self.assertLess(sum(f["widths"]), 43370)                             # 본문 폭보다 좁은 표
        self.assertGreater(f["widths"][1], f["widths"][0])
        e = ts.fit_table([["", "가"]], [["06", "06"]], {"06": dict(self.M)}, 43370, 0)
        self.assertEqual(e["widths"][0], ts.MIN_CELL)                            # 빈 칸도 하한(ColWidth 가 0 이 되지 않게)



class _Fn:
    def __init__(self, impl):
        self.impl, self.restype, self.argtypes = impl, None, None

    def __call__(self, *a):
        assert self.argtypes is not None and len(a) == len(self.argtypes), (self.impl.__name__, len(a))
        return self.impl(*a)


class FakeGdi:
    """gdi32 흉내 — installed 글꼴만 그 이름, 없는 이름은 굵기마다 대체 글꼴(fallback·fallback_bold). 글자 폭: 글꼴별 em."""
    def __init__(self, installed, fallback, fallback_bold=None, em=None):
        self.installed, self.fb, self.fbb = installed, fallback, fallback_bold or fallback
        self.em = em or {}
        self.objs, self.next, self.sel, self.deleted, self.calls = {}, 100, {}, [], []
        for n in ("CreateCompatibleDC", "CreateFontW", "SelectObject", "GetTextExtentPoint32W", "GetTextFaceW",
                  "DeleteObject", "DeleteDC"):
            setattr(self, n, _Fn(getattr(self, "_" + n)))

    def _new(self, v):
        self.next += 1
        self.objs[self.next] = v
        return self.next

    def _CreateCompatibleDC(self, h):
        return self._new("dc")

    def _CreateFontW(self, h, w, e, o, weight, it, ul, so, cs, op, cp, q, pf, face):
        self.calls.append(("CreateFontW", h, weight, face))
        real = face if face in self.installed else (self.fbb if weight >= 700 else self.fb)
        return self._new(("font", real, h))

    def _SelectObject(self, dc, obj):
        old = self.sel.get(dc, 1)
        self.sel[dc] = obj
        return old

    def _GetTextFaceW(self, dc, n, buf):
        f = self.objs.get(self.sel.get(dc))
        buf.value = f[1] if isinstance(f, tuple) else "System"
        return len(buf.value)

    def _GetTextExtentPoint32W(self, dc, text, n, psize):
        f = self.objs.get(self.sel.get(dc))
        self.calls.append(("Extent", text, n, f[1]))
        psize._obj.cx, psize._obj.cy = int(self.em.get(f[1], 0.5) * 1000 * n), 1300
        return 1

    def _DeleteObject(self, h):
        self.deleted.append(h)
        return 1

    def _DeleteDC(self, h):
        self.deleted.append(h)
        return 1


class TestGdiMeasure(unittest.TestCase):
    """GdiMeasure 의 파이썬 쪽 논리(Windows GDI 동작이 아님) — 글자 크기 -1000(글자 높이), 폭 = cx, 없는 글꼴 찾기(굵기마다),
    UTF-16 길이, 닫기(검토 P-041 M5·L1·L2)."""

    def test_measured_and_missing(self):
        g = FakeGdi({"함초롬돋움"}, "굴림", em={"함초롬돋움": 1.0})
        m = ts.GdiMeasure(gdi=g)
        self.assertEqual(m("가나", "함초롬돋움"), 2.0)
        self.assertIsNone(m("가나", "없는글꼴"))                                # 대체 글꼴(굴림)로 바뀜 → 못 잼
        self.assertEqual(m("", "함초롬돋움"), 0.0)
        self.assertEqual({c[1] for c in g.calls if c[0] == "CreateFontW"}, {-1000})   # 글자 높이(음수)로 만든다
        self.assertEqual(m.faces, {"함초롬돋움": True, "없는글꼴": False})
        self.assertEqual(m("굴림 글꼴", "굴림"), 2.5)                            # 대체 글꼴 이름 그대로면 그 글꼴은 있다 — 잰다
        m.close()
        self.assertIsNone(m.dc)
        made = [i for i, v in g.objs.items() if isinstance(v, tuple)]
        self.assertTrue(set(made) <= set(g.deleted))                           # 만든 글꼴(찾기용 포함)·DC 모두 지움

    def test_bold_fallback_probed_per_weight(self):
        g = FakeGdi({"함초롬돋움"}, "굴림", fallback_bold="Arial")
        m = ts.GdiMeasure(gdi=g)
        self.assertIsNone(m("가", "없는글꼴", True))                           # 진하게 대체 글꼴이 달라도 없는 글꼴로 본다
        self.assertEqual(m.faces, {"없는글꼴 (진하게)": False})

    def test_utf16_length(self):
        g = FakeGdi({"함초롬돋움"}, "굴림")
        m = ts.GdiMeasure(gdi=g)
        m("A\U00020000B", "함초롬돋움")
        self.assertEqual([c[2] for c in g.calls if c[0] == "Extent"], [4])     # BMP 밖 글자는 UTF-16 두 단위

    def test_not_on_linux(self):
        if sys.platform != "win32":
            self.assertIsNone(ts.gdi_measure())


class TestCheck(unittest.TestCase):
    def written(self, wrong_bf=None, header=False, width=None, margin=(538, 538, 0, 0), style=3):
        b = [bf(1, N, N, N, N), bf(10, K, N, K, K, 14079702), bf(11, N, K, K, K, 14079702), bf(12, K, N, K, K),
             bf(13, N, K, K, K)]
        cells = [cell(0, 0, 10, width or 8504, 1, header), cell(0, 1, 11, 31181, 1, header),
                 cell(1, 0, wrong_bf or 12, 8504, style), cell(1, 1, 13, 31181, style)]
        return doc(b, table(["<ROW>%s%s</ROW>" % tuple(cells[:2]), "<ROW>%s%s</ROW>" % tuple(cells[2:])], 2, 2,
                            margin=margin))

    def plan(self):
        cf = lambda L, R, T, B, fill, style: {"L": L, "R": R, "T": T, "B": B, "fill": fill, "style": style,  # noqa
                                              "header": False}
        return {"cells": [[cf(K, N, K, K, GRAY, "05_도표내용_항목제목"), cf(N, K, K, K, GRAY, "05_도표내용_항목제목")],
                          [cf(K, N, K, K, None, "07_도표내용_본문혼합"), cf(N, K, K, K, None, "07_도표내용_본문혼합")]],
                "inside_margin": [538, 538, 0, 0], "col_hu": [8504, 31181]}

    def test_match(self):
        self.assertEqual(ts.check_tables(self.written(), [("s1.t0", self.plan())]), [])

    def test_center_checked(self):
        """표가 든 문단 정렬 — 가운데가 아니면 알린다(P-041)."""
        x = self.written()
        plan = dict(self.plan(), center=True)
        got = ts.check_tables(x, [("s1.t0", plan)])
        self.assertEqual([(g["what"], g["got"]) for g in got], [("가운데 정렬", None)])
        x = x.replace('<STYLELIST>', '<PARASHAPELIST><PARASHAPE Id="7" Align="Center"/></PARASHAPELIST><STYLELIST>', 1)
        x = x.replace('<P ParaShape="0" Style="0"><TEXT CharShape="0"><TABLE', '<P ParaShape="7" Style="0"><TEXT CharShape="0"><TABLE', 1)
        self.assertEqual(ts.check_tables(x, [("s1.t0", plan)]), [])
        self.assertEqual(ts.check_tables(self.written(), [("s1.t0", dict(plan, done={"center": "off"}))]), [])
        y = x.replace('<PARASHAPE Id="7" Align="Center"/>', '<PARASHAPE Id="7" Align="Center"><PARAMARGIN Left="2000" '
                      'Right="0" Indent="0"/></PARASHAPE>', 1)
        got = ts.check_tables(y, [("s1.t0", dict(plan, anchor_reset=True))])    # 표 문단 여백을 0 으로 못 했다
        self.assertEqual([(g["what"], g["got"]) for g in got], [("표 문단 여백", {"Left": "2000"})])
        self.assertEqual(ts.check_tables(y, [("s1.t0", plan)]), [])             # 여백 0 을 하지 않았으면 보지 않는다
        z = x.replace('RowCount="2">', 'RowCount="2"><SHAPEOBJECT><POSITION TreatAsChar="false"/></SHAPEOBJECT>', 1)
        self.assertEqual([g["what"] for g in ts.check_tables(z, [("s1.t0", plan)])], ["글자처럼 취급"])  # 떠 있는 표는 문단 정렬을 안 따른다

    def test_only_done_kinds_checked(self):
        """입힌(True)·입힐 것 없던(None) 종류만 대조 — 실패·꺼진 종류는 '입히지 못한 곳'으로 이미 알렸다(검토 P-040 2)."""
        x = self.written(wrong_bf=13, header=True, width=20000, margin=(510, 510, 141, 141))
        plan = dict(self.plan(), label="표 3", done={"border": False, "header": "off", "width": False, "margin": False})
        self.assertEqual(ts.check_tables(x, [("s1.t0", plan)]), [])
        plan["done"] = {"border": True, "header": None, "width": True, "margin": True}
        got = ts.check_tables(x, [("s1.t0", plan)])
        self.assertEqual({g["table"] for g in got}, {"표 3"})
        self.assertEqual({g["what"] for g in got} >= {"L", "제목 셀", "너비", "안 여백"}, True)

    def test_fit_plan_checks_style_and_width_only(self):
        """칸 너비 맞춤만 하는 표(작성기 fit_plan — 칸 서식에 스타일만)는 선·배경·제목 셀을 보지 않는다(P-045): 한/글 기본 그대로."""
        plan = {"cells": [[{"style": "05_도표내용_항목제목"}] * 2, [{"style": "07_도표내용_본문혼합"}] * 2],
                "col_hu": [8504, 31181]}
        self.assertEqual(ts.check_tables(self.written(wrong_bf=13, header=True), [("s1.t0", plan)]), [])
        got = ts.check_tables(self.written(style=2, width=20000), [("s1.t0", plan)])
        self.assertEqual({g["what"] for g in got}, {"스타일", "너비"})

    def test_detects(self):
        got = ts.check_tables(self.written(wrong_bf=13, header=True, width=20000, margin=(510, 510, 141, 141), style=2),
                              [("s1.t0", self.plan())])
        what = {(tuple(x["at"]) if isinstance(x["at"], list) else x["at"], x["what"]) for x in got}
        self.assertIn(("표", "안 여백"), what)
        self.assertIn(((1, 0), "L"), what)
        self.assertIn(((0, 0), "제목 셀"), what)
        self.assertIn(((0, 0), "너비"), what)
        self.assertIn(((1, 1), "스타일"), what)
        self.assertEqual(ts.check_tables(self.written(), [("s9.t9", self.plan())])[0]["what"], "표 없음")


if __name__ == "__main__":
    unittest.main()
