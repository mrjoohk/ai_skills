"""Nested HWPML definitions retain semantics during fake COM editing."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fake_hwp import FakeHwp

PARA = '<PARASHAPE Id="0" HeadingType="Outline" Level="0" Align="Left"><PARAMARGIN LeftMargin="1200"/><DETAIL Level="6" Type="child"/></PARASHAPE>'
CHAR = '<CHARSHAPE Id="0" Height="1100"><FONTID Hangul="2" Latin="3"/><BOLD/><DETAIL Height="2200" Id="99"/></CHARSHAPE>'
STYLE = '<STYLE Id="0" Name="가 &amp; 나 &gt; style" ParaShape="0" CharShape="0"><DETAIL Name="child" CharShape="77"/></STYLE>'


def document(style=STYLE, para=PARA, char=CHAR):
    return ('<HWPML><HEAD><MAPPINGTABLE><STYLELIST>' + style + '</STYLELIST><PARASHAPELIST>' + para +
            '</PARASHAPELIST><CHARSHAPELIST>' + char + '</CHARSHAPELIST></MAPPINGTABLE></HEAD><BODY><SECTION>'
            '<P ParaShape="0" Style="0"><TEXT CharShape="0"><CHAR>제목</CHAR></TEXT></P></SECTION></BODY></HWPML>')


class TestNestedHead(unittest.TestCase):
    def test_reader_handles_paired_elements_and_ignores_nested_attributes(self):
        fake = FakeHwp(hwpml=document())
        self.assertEqual(fake._head_items(fake.hwpml, "PARASHAPE")["0"], PARA)
        self.assertEqual(fake._head_items(fake.hwpml, "CHARSHAPE")["0"], CHAR)
        self.assertEqual(fake._parashape_attrs(fake.hwpml, "0")["Level"], "0")
        self.assertEqual(fake._charshape_attrs("0")["Height"], "1100")
        self.assertEqual(fake._attr(STYLE, "Name"), "가 & 나 > style")
        self.assertEqual(fake._attr(STYLE, "CharShape"), "0")
        self.assertEqual(fake.GetHeadingString(), "1.")

    def test_reader_preserves_empty_elements_and_does_not_read_comment_decoys(self):
        xml = '<HEAD><!-- <PARASHAPE Id="8"/> --><PARASHAPELIST><PARASHAPE Id="0"/>' + PARA.replace('Id="0"', 'Id="1"', 1) + '</PARASHAPELIST></HEAD>'
        items = FakeHwp._head_items(xml, "PARASHAPE")
        self.assertEqual(set(items), {"0", "1"})
        self.assertEqual(items["0"], '<PARASHAPE Id="0"/>')

    def test_parent_attribute_edit_preserves_child_bytes_and_values(self):
        fake = FakeHwp(hwpml=document())
        before_children = PARA[PARA.index(">") + 1:]
        fake._set_head_attr("PARASHAPE", "0", "Level", "2")
        updated = fake._head_items(fake.hwpml, "PARASHAPE")["0"]
        self.assertEqual(updated[updated.index(">") + 1:], before_children)
        node = ET.fromstring(updated)
        self.assertEqual(node.get("Level"), "2")
        self.assertEqual(node.find("DETAIL").get("Level"), "6")
        fake._set_head_attr("STYLE", "0", "Name", '새 이름 & "value"')
        updated_style = ET.fromstring(fake._head_items(fake.hwpml, "STYLE")["0"])
        self.assertEqual(updated_style.get("Name"), '새 이름 & "value"')
        self.assertEqual(updated_style.find("DETAIL").get("Name"), "child")

    def test_alignment_and_font_size_clones_keep_nested_formatting(self):
        fake = FakeHwp(hwpml=document())
        fake.Run("ParagraphShapeAlignRight")
        fake._char_height(1400)
        root = ET.fromstring(fake.hwpml)
        paragraph = root.find("BODY/SECTION/P")
        pid, cid = paragraph.get("ParaShape"), paragraph.find("TEXT").get("CharShape")
        para = ET.fromstring(fake._head_items(fake.hwpml, "PARASHAPE")[pid])
        char = ET.fromstring(fake._head_items(fake.hwpml, "CHARSHAPE")[cid])
        self.assertEqual(para.get("Align"), "Right")
        self.assertEqual(para.find("PARAMARGIN").get("LeftMargin"), "1200")
        self.assertEqual(para.get("Level"), "0")
        self.assertEqual(char.get("Height"), "1400")
        self.assertEqual(char.find("FONTID").attrib, {"Hangul": "2", "Latin": "3"})
        self.assertIsNotNone(char.find("BOLD"))
        self.assertEqual(char.find("DETAIL").get("Height"), "2200")
        self.assertEqual(fake.GetHeadingString(), "1.")

    def test_style_removal_removes_the_whole_paired_definition(self):
        fake = FakeHwp(hwpml=document(style=STYLE + '<STYLE Id="1" Name="unused"><DETAIL Name="orphan"/></STYLE>'))
        self.assertTrue(fake._style_delete(1, 0))
        self.assertEqual(set(fake._head_items(fake.hwpml, "STYLE")), {"0"})
        self.assertNotIn("orphan", fake.hwpml)

    def test_insert_file_preserves_imported_paragraph_and_character_definitions(self):
        source = document(style=STYLE.replace('가 &amp; 나 &gt; style', 'imported'))
        fake = FakeHwp(hwpml=document(style='<STYLE Id="0" Name="existing" ParaShape="0" CharShape="0"/>'), docs={"seed.hwpx": source})
        self.assertTrue(fake._insert_file("seed.hwpx", 0))
        imported = next(ET.fromstring(v) for v in fake._head_items(fake.hwpml, "STYLE").values()
                        if fake._attr(v, "Name") == "imported")
        para = ET.fromstring(fake._head_items(fake.hwpml, "PARASHAPE")[imported.get("ParaShape")])
        char = ET.fromstring(fake._head_items(fake.hwpml, "CHARSHAPE")[imported.get("CharShape")])
        self.assertEqual(para.find("PARAMARGIN").get("LeftMargin"), "1200")
        self.assertEqual(char.get("Height"), "1100")
        self.assertEqual(char.find("FONTID").get("Hangul"), "2")
        self.assertIsNotNone(char.find("BOLD"))


if __name__ == "__main__":
    unittest.main()
