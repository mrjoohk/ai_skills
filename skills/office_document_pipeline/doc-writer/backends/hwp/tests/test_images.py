"""그림 꺼내기(images 명령, P-052 D-062) 시험 — 합성 HWPML(BINDATA Base64·압축)과 가짜 COM."""
import base64
import json
import sys
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import images as im               # noqa: E402
import hwpml_parse as hp          # noqa: E402
from fake_hwp import FakeHwp, DECL16   # noqa: E402
from test_cli import CliBase      # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"png-body" * 4
JPG = b"\xff\xd8\xff\xe0" + b"jpg-body" * 8
EMF = b"\x01\x00\x00\x00" + b"\x00" * 36 + b" EMF" + b"emf-body"


def deflate(b):
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    return c.compress(b) + c.flush()


def pic(binitem, title, w=14600, h=8760):
    cap = ('<CAPTION Side="Bottom"><PARALIST><P ParaShape="0" Style="0"><TEXT CharShape="0"><CHAR>그림 </CHAR>'
           '<AUTONUM Number="1" NumberType="Figure"/><CHAR> %s</CHAR></TEXT></P></PARALIST></CAPTION>' % title) if title else ""
    return ('<PICTURE><SHAPEOBJECT NumberingType="Figure"><SIZE Width="%d" Height="%d"/>%s</SHAPEOBJECT>'
            '<IMAGE BinItem="%s"/></PICTURE>' % (w, h, cap, binitem))


def P(inner):
    return '<P ParaShape="0" Style="0"><TEXT CharShape="0">%s</TEXT></P>' % inner


def doc():
    items = ('<BINDATALIST Count="5"><BINITEM BinData="1" Format="PNG" Type="Embedding"/>'
             '<BINITEM BinData="2" Format="JPG" Type="Embedding"/><BINITEM Format="bmp" Type="Link" APath="C:/x.bmp"/>'
             '<BINITEM BinData="4" Format="PNG" Type="Embedding"/><BINITEM BinData="5" Format="EMF" Type="Embedding"/>'
             '</BINDATALIST>')
    store = ('<BINDATASTORAGE><BINDATA Id="1" Encoding="Base64" Size="%d">%s</BINDATA>'
             '<BINDATA Id="2" Encoding="Base64" Compress="true">%s</BINDATA>'
             '<BINDATA Id="4" Encoding="Base64">%s</BINDATA><BINDATA Id="5" Encoding="Base64">%s</BINDATA></BINDATASTORAGE>'
             % (len(PNG), base64.b64encode(PNG).decode(), base64.b64encode(deflate(JPG)).decode(),
                base64.b64encode(b"not an image").decode(), base64.b64encode(zlib.compress(EMF)).decode()))
    table = ('<TABLE ColCount="1" RowCount="1"><ROW><CELL ColAddr="0" RowAddr="0" RowSpan="1" ColSpan="1"><PARALIST>%s'
             '</PARALIST></CELL></ROW></TABLE>' % P(pic(5, "표 안 그림")))
    body = [P("<CHAR>제목</CHAR>"), P(pic(1, "첫 그림")), P(pic(2, "둘째 그림", 28346, 14173)), P(pic(3, "연결 그림")),
            P(table), P(pic(4, "깨진 그림")), P(pic(9, ""))]
    return (DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="1"><MAPPINGTABLE>%s<STYLELIST><STYLE Id="0" Name="바탕글"/>'
            '</STYLELIST></MAPPINGTABLE></HEAD><BODY><SECTION Id="0">%s</SECTION></BODY><TAIL>%s</TAIL></HWPML>'
            % (items, "".join(body), store))


class TestPure(unittest.TestCase):
    def test_extract(self):
        x = doc()
        recs, blobs = im.extract(x, hp.clean(x)[0])
        self.assertEqual([r["k"] for r in recs], [1, 2, 3, 4, 5, 6])
        self.assertEqual(blobs[0], PNG)
        self.assertEqual((recs[0]["file"], recs[0]["how"], recs[0]["title"], recs[0]["where"]), ("fig01.png", "raw", "첫 그림", "s0.p1"))
        self.assertEqual((blobs[1], recs[1]["file"], recs[1]["how"], recs[1]["size_mm"]), (JPG, "fig02.jpg", "deflate", [100.0, 50.0]))
        self.assertIn("포함된 그림이 아니다", recs[2]["skip"])
        self.assertEqual((blobs[3], recs[3]["file"], recs[3]["how"], recs[3]["where"]), (EMF, "fig04.emf", "zlib", "s0.p4+"))
        self.assertIn("형식을 알 수 없다", recs[4]["skip"])
        self.assertIn("그림 항목", recs[5]["skip"])
        self.assertIsNone(blobs[2])
        self.assertEqual(recs[0]["sha256"], __import__("hashlib").sha256(PNG).hexdigest())

    def test_missing_bindata(self):
        x = doc().replace('<BINDATA Id="4" Encoding="Base64">', '<BINDATA Id="44" Encoding="Base64">')
        recs, blobs = im.extract(x, hp.clean(x)[0])
        self.assertIn("그림 데이터", recs[4]["skip"])
        self.assertIsNone(blobs[4])

    def test_kind(self):
        self.assertEqual(im.kind_of(b"GIF89a.."), "gif")
        self.assertEqual(im.kind_of(b"BM...."), "bmp")
        self.assertIsNone(im.kind_of(b"\x00\x01"))


class TestCli(CliBase):
    def test_images_command(self):
        self.use(FakeHwp(hwpml=doc()))
        out = self.tmp / "img"
        self.assertEqual(self.main("images", self.src, "--out-dir", out), 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["fig01.png", "fig02.jpg", "fig04.emf", "images.json", "images.md"])
        self.assertEqual((out / "fig02.jpg").read_bytes(), JPG)
        self.assertIn("그림 6개 · 꺼냄 3 · 건너뜀 3", self.out)
        md = (out / "images.md").read_text(encoding="utf-8")
        self.assertIn("평문 그림", md)
        self.assertIn("둘째 그림", md)
        self.assertEqual(len(json.loads((out / "images.json").read_text(encoding="utf-8"))), 6)
        self.assertEqual(self.src.read_bytes()[:11], b"BMS DocuRay")            # 원본은 그대로

    def test_out_dir_exists(self):
        self.use(FakeHwp(hwpml=doc()))
        (self.tmp / "img").mkdir()
        self.assertEqual(self.main("images", self.src, "--out-dir", self.tmp / "img"), 2)
        self.assertEqual(list((self.tmp / "img").iterdir()), [])

    def test_none_extracted_is_code1(self):
        x = doc().replace('Type="Embedding"', 'Type="Link"')
        self.use(FakeHwp(hwpml=x))
        self.assertEqual(self.main("images", self.src, "--out-dir", self.tmp / "img"), 1)


if __name__ == "__main__":
    unittest.main()
