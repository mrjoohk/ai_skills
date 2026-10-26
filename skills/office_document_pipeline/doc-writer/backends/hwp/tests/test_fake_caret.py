"""가짜 한/글의 캐럿 편집 흉내(P-025) — 템플릿 생성기 시험이 기대는 가정을 고정한다.

실측 근거: _drmtest/template_poc/poc_report.md (S1 끼워 넣기 후 지우기, S3 번호 글자 지우기, S4 정렬, S5 쪽 번호 위치).
실측 전 가정(개체 하나 = 캐럿 한 칸, 개요 번호 '1.2.1.' 꼴)은 생성기가 HWPML 로 결과를 확인해 잡는다.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import hwpml_parse as hp                  # noqa: E402
from fake_hwp import FakeHwp, DECL16      # noqa: E402


def doc(paras, styles=(("바탕글", "0"), ("COMSAF 개요 1", "1"), ("COMSAF 개요 2", "2"))):
    st = "".join('<STYLE Id="%d" Name="%s" ParaShape="%s"/>' % (i, n, ps) for i, (n, ps) in enumerate(styles))
    return (DECL16 + '<HWPML Version="2.91"><HEAD><MAPPINGTABLE><STYLELIST>%s</STYLELIST><PARASHAPELIST>'
            '<PARASHAPE Id="0" HeadingType="None" Level="0"/><PARASHAPE Id="1" HeadingType="Outline" Level="0"/>'
            '<PARASHAPE Id="2" HeadingType="Outline" Level="1"/></PARASHAPELIST></MAPPINGTABLE></HEAD><BODY>'
            '<SECTION Id="0">%s</SECTION></BODY></HWPML>' % (st, "".join(paras)))


def P(inner, style=0, ps=0):
    return '<P ParaShape="%d" Style="%d"><TEXT CharShape="0">%s</TEXT></P>' % (ps, style, inner)


class TestFakeCaret(unittest.TestCase):
    def texts(self, h):
        return [b["text"] for b in hp.parse(h.hwpml)["body"] if b["type"] == "para"]

    def test_delete_prefix_from_end(self):
        h = FakeHwp(hwpml=doc([P('<SECDEF/><CHAR>1.1<TAB/>적용범위</CHAR>')]))
        h.MovePos(0, 0, 0)
        h.MovePos(7, 0, 0)                                  # 문단 끝
        for _ in range(4):
            h.Run("MoveLeft")
        for _ in range(4):
            h.Run("MoveSelLeft")
        h.Run("Delete")
        m = hp.parse(h.hwpml)
        self.assertEqual(m["body"][0]["text"], "적용범위")
        self.assertEqual([c["tag"] for c in m["ctrls"]], ["SECDEF"])     # 앞 개체는 그대로

    def test_break_style_insert_text(self):
        h = FakeHwp(hwpml=doc([P('<CHAR>본문</CHAR>')]))
        h.Run("MoveDocEnd")
        h.Run("BreakPara")
        h.HParameterSet.HStyle.Apply = 2
        self.assertTrue(h.HAction.Execute("Style", None))
        h.HParameterSet.HInsertText.Text = "새 제목"
        h.HAction.Execute("InsertText", None)
        b = hp.parse(h.hwpml)["body"]
        self.assertEqual([(x["text"], x["style"], x.get("level")) for x in b], [("본문", "바탕글", None),
                                                                               ("새 제목", "COMSAF 개요 2", 2)])

    def test_insert_file_imports_only_used_missing_styles(self):
        seed = doc([P('<HEADER ApplyPageType="Both"><PARALIST>%s</PARALIST></HEADER><CHAR>씨앗 첫 문단</CHAR>'
                      % P("<CHAR>씨앗 머리말</CHAR>")), P("<CHAR>표시 1</CHAR>", 1, 1)],
                   styles=(("바탕글", "0"), ("COMSAF 개요 1", "1"), ("안 쓰는 스타일", "0")))
        h = FakeHwp(hwpml=doc([P("<CHAR>끝 문단</CHAR>")], styles=(("바탕글", "0"),)), docs={"seed.hwpx": seed})
        h.Run("MoveDocEnd")
        h.Run("BreakPara")
        h.HParameterSet.HInsertFile.FileName = "C:/x/seed.hwpx"
        self.assertTrue(h.HAction.Execute("InsertFile", None))
        m = hp.parse(h.hwpml)
        self.assertEqual([s["name"] for s in m["styledefs"]], ["바탕글", "COMSAF 개요 1"])   # 쓰인 것 중 없던 것만
        self.assertEqual(self.texts(h), ["끝 문단", "씨앗 첫 문단", "표시 1"])
        self.assertEqual([x["text"] for x in m["headers"]], ["씨앗 머리말"])
        h.MovePos(0, 1, 0)                                  # 넣은 내용 지우기: 넣은 첫 문단 처음 → 문서 끝
        h.Run("MoveSelDocEnd")
        h.Run("Delete")
        self.assertEqual(len(hp.parse(h.hwpml)["headers"]), 1)          # 빈 문단 그릇에 넣은 첫 문단의 개체가 남는다
        h.MovePos(0, 0, 0)                                  # 앞 문단 끝 → 문서 끝: 그 빈 문단까지 사라진다
        h.MovePos(7, 0, 0)
        h.Run("MoveSelDocEnd")
        h.Run("Delete")
        m = hp.parse(h.hwpml)
        self.assertEqual((self.texts(h), m["headers"], m["stats"]["section_paras"]), (["끝 문단"], [], [1]))

    def test_heading_string_and_pagenum_props(self):
        h = FakeHwp(hwpml=doc([P('<PAGENUM Pos="BottomCenter"/><CHAR>표지</CHAR>'), P("<CHAR>가</CHAR>", 1, 1),
                               P("<CHAR>나</CHAR>", 2, 2), P("<CHAR>다</CHAR>", 2, 2), P("<CHAR>라</CHAR>", 1, 1)]))
        got = []
        for i in range(5):
            h.MovePos(0, i, 0)
            got.append(h.GetHeadingString())
        self.assertEqual(got, ["", "1.", "1.1.", "1.2.", "2."])
        c = h.HeadCtrl
        self.assertEqual((c.CtrlID, c.GetAnchorPos(2).Item("Para"), c.Next), ("pgnp", 0, None))
        ps = c.Properties
        self.assertEqual(ps.Item("DrawPos"), 5)
        ps.SetItem("DrawPos", 0)
        c.Properties = ps
        self.assertEqual([x["attrs"]["Pos"] for x in hp.parse(h.hwpml)["ctrls"]], ["None"])

    def test_align_right_selected_paragraph(self):
        h = FakeHwp(hwpml=doc([P("<CHAR>문서번호 : X</CHAR>"), P("<CHAR>다음</CHAR>")]))
        h.MovePos(0, 0, 0)
        h.Run("MoveSelParaEnd")
        h.Run("ParagraphShapeAlignRight")
        h.Run("Cancel")
        self.assertEqual([b["align"] for b in hp.parse(h.hwpml)["body"]], ["Right", None])


if __name__ == "__main__":
    unittest.main()
