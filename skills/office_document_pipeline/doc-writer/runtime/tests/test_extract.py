"""그림 꺼내기 시험 — 합성 평문 HWPX(ZIP). DRM 문서는 거절해야 한다."""
import json
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import extract_figures as ef      # noqa: E402

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"'


def png(w, h):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def pic(ref, cap_num, cap_text, w=42520, h=23918):
    return ('<hp:pic><hp:curSz width="%d" height="%d"/><hc:img binaryItemIDRef="%s"/><hp:caption><hp:subList><hp:p>'
            '<hp:run><hp:t>그림 </hp:t><hp:ctrl><hp:autoNum num="%d" numType="PICTURE"/></hp:ctrl><hp:t> %s</hp:t>'
            '</hp:run></hp:p></hp:subList></hp:caption></hp:pic>' % (w, h, ref, cap_num, cap_text))


class TestExtract(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "manual.hwpx"
        sec = ('<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" %s>'
               '<hp:p><hp:run><hp:t>첫 문단</hp:t></hp:run></hp:p>'
               '<hp:p><hp:run>%s</hp:run></hp:p>'
               '<hp:p><hp:run>%s%s</hp:run></hp:p></hs:sec>' % (
                   HP, pic("image1", 1, "설정 파일 편집 창"), pic("image2", 2, "실행 창1", 21000, 11900),
                   pic("image3", 3, "실행 창2")))
        hpf = ('<opf:package xmlns:opf="http://www.idpf.org/2007/opf/"><opf:manifest>'
               '<opf:item id="image1" href="BinData/image1.png" media-type="image/png"/>'
               '<opf:item id="image2" href="BinData/image2.png" media-type="image/png"/>'
               '</opf:manifest></opf:package>')
        with zipfile.ZipFile(self.src, "w") as z:
            z.writestr("mimetype", "application/hwp+zip")
            z.writestr("Contents/content.hpf", hpf)
            z.writestr("Contents/section0.xml", sec)
            z.writestr("BinData/image1.png", png(40, 20))
            z.writestr("BinData/image2.png", png(10, 5))
            z.writestr("BinData/image3.png", png(4, 4))                  # 매니페스트에 없는 항목 — 이름으로 찾는다

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_figures_in_order_with_captions(self):
        figs = ef.extract(self.src, self.tmp / "out", max_width=20, log=lambda m: None)
        self.assertEqual([(f["n"], f["caption"], f["para"], f["item"]) for f in figs],
                         [(1, "설정 파일 편집 창", 1, "BinData/image1.png"), (2, "실행 창1", 2, "BinData/image2.png"),
                          (3, "실행 창2", 2, "BinData/image3.png")])
        self.assertEqual((figs[0]["width_mm"], figs[0]["height_mm"]), (150.0, 84.4))
        self.assertTrue(all((self.tmp / "out" / f["file"]).exists() for f in figs))
        try:
            import PIL  # noqa: F401
            self.assertEqual(figs[0]["pixels"], [20, 10])                 # 가로 max_width 로 줄임
            self.assertTrue(figs[0]["file"].endswith(".png"))
        except ImportError:
            self.assertEqual((self.tmp / "out" / figs[0]["file"]).read_bytes()[:4], b"\x89PNG")
        j = json.loads((self.tmp / "out" / "figures.json").read_text(encoding="utf-8"))
        self.assertEqual(len(j["figures"]), 3)
        self.assertIn("| 1 | fig01.", (self.tmp / "out" / "figures.md").read_text(encoding="utf-8"))

    def test_drm_and_non_zip_refused(self):
        drm = self.tmp / "drm.hwpx"
        drm.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 64)
        with self.assertRaises(ef.Refused) as e:
            ef.extract(drm, self.tmp / "o1", log=lambda m: None)
        self.assertIn("DRM", str(e.exception))                          # DRM 이라서 거절했다고 말한다(우회 금지)
        self.assertEqual(ef.main([str(drm), str(self.tmp / "o2")]), 2)
        self.assertFalse((self.tmp / "o2").exists())                     # 거절하면 아무것도 쓰지 않는다
        other = self.tmp / "x.hwp"
        other.write_bytes(b"\xd0\xcf\x11\xe0" + b"\x00" * 64)
        with self.assertRaises(ef.Refused):
            ef.extract(other, self.tmp / "o3", log=lambda m: None)


if __name__ == "__main__":
    unittest.main()
