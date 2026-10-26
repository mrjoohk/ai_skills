"""Image extraction tests using synthetic HWPML; no documents or COM are opened."""
import base64
import hashlib
from pathlib import Path
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import images

PNG = b"\x89PNG\r\n\x1a\nsynthetic-image"


def document(binitem="1", item_type="Embedding", nested=False):
    picture = (
        '<PICTURE><SHAPEOBJECT><SIZE Width="28346" Height="14173"/>'
        '<CAPTION><P><TEXT><CHAR>그림 시험</CHAR></TEXT></P></CAPTION>'
        '</SHAPEOBJECT><IMAGE BinItem="%s"/></PICTURE>' % binitem
    )
    if nested:
        picture = '<TABLE><ROW><CELL><P><TEXT>' + picture + '</TEXT></P></CELL></ROW></TABLE>'
    return (
        '<HWPML><HEAD><BINDATALIST><BINITEM Type="%s" BinData="b1" Format="png"/>'
        '</BINDATALIST></HEAD><BODY><SECTION><P><TEXT>%s</TEXT></P></SECTION></BODY>'
        '<TAIL><BINDATA Id="b1">%s</BINDATA></TAIL></HWPML>'
        % (item_type, picture, base64.b64encode(PNG).decode("ascii"))
    )


class TestImages(unittest.TestCase):
    def test_raw_image_bytes_and_manifest(self):
        xml = document()
        records, blobs = images.extract(xml, xml)
        self.assertEqual(blobs, [PNG])
        self.assertEqual(records[0]["file"], "fig01.png")
        self.assertEqual(records[0]["sha256"], hashlib.sha256(PNG).hexdigest())
        self.assertEqual(records[0]["title"], "시험")
        self.assertEqual(records[0]["size_mm"], [100.0, 50.0])

    def test_zlib_compressed_image(self):
        decoded, kind, _ = images.decode(base64.b64encode(zlib.compress(PNG)).decode("ascii"))
        self.assertEqual((decoded, kind), (PNG, "png"))

    def test_raw_deflate_image(self):
        compressor = zlib.compressobj(wbits=-15)
        compressed = compressor.compress(PNG) + compressor.flush()
        decoded, kind, _ = images.decode(base64.b64encode(compressed).decode("ascii"))
        self.assertEqual((decoded, kind), (PNG, "png"))

    def test_unknown_format_is_not_written(self):
        decoded, kind, reason = images.decode(base64.b64encode(b"not-an-image").decode("ascii"))
        self.assertIsNone(decoded)
        self.assertIsNone(kind)
        self.assertTrue(reason)

    def test_linked_picture_is_skipped(self):
        xml = document(item_type="Link")
        records, blobs = images.extract(xml, xml)
        self.assertEqual(blobs, [None])
        self.assertIn("skip", records[0])
        self.assertNotIn("file", records[0])

    def test_invalid_item_id_never_selects_another_image(self):
        for binitem in ("0", "-1", "2", "bad"):
            with self.subTest(binitem=binitem):
                xml = document(binitem=binitem)
                records, blobs = images.extract(xml, xml)
                self.assertEqual(blobs, [None])
                self.assertIn("skip", records[0])

    def test_nested_picture_keeps_document_location(self):
        xml = document(nested=True)
        records, blobs = images.extract(xml, xml)
        self.assertEqual(blobs, [PNG])
        self.assertEqual(records[0]["where"], "s0.p0+")

    def test_document_without_body_has_no_images(self):
        self.assertEqual(images.extract("<HWPML/>", "<HWPML/>"), ([], []))


if __name__ == "__main__":
    unittest.main()
