"""Protection policy regression tests using injected fake COM only."""
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_cli import CliBase, FakeHwp, api, SYN_FIELDS


class TestProtection(CliBase):
    def plain(self):
        self.src.write_bytes(b"PK\x03\x04plain source")
        self.use(FakeHwp(fields=SYN_FIELDS, save_head=b"PK\x03\x04"))

    def test_plain_cli_preserves_plain_output(self):
        self.plain()
        mapping = self.mapfile({"SYN_FIELD_A": "new"})
        self.assertEqual(self.main("fill", self.src, "--map", mapping), 0, self.out)
        self.assertEqual(api.hs.head_kind(self.src.with_name(self.src.stem + "_out.hwpx")), "PLAIN_ZIP")

    def test_required_rejects_plain_output(self):
        self.plain()
        mapping = self.mapfile({"SYN_FIELD_A": "new"})
        self.assertEqual(self.main("fill", self.src, "--map", mapping, "--protection", "required"), 3)

    def test_legacy_api_default_remains_required(self):
        self.plain()
        with api.HwpxSession() as session:
            session.open(self.src)
            with self.assertRaises(api.PlaintextSaved):
                session.save()

    def test_protected_preserve_cannot_downgrade_or_replace_source(self):
        original = self.src.read_bytes()
        self.use(FakeHwp(save_head=b"PK\x03\x04"))
        with api.HwpxSession() as session:
            session.open(self.src)
            with self.assertRaises(api.PlaintextSaved):
                session.save(overwrite=True, protection="preserve")
        self.assertEqual(self.src.read_bytes(), original)

    def test_plain_preserve_can_replace_after_verification(self):
        self.plain()
        with api.HwpxSession() as session:
            session.open(self.src)
            result = session.save(overwrite=True, protection="preserve")
        self.assertFalse(result["protection_required"])
        self.assertFalse(result["protected"])
        self.assertTrue(result["reopen"])
        self.assertTrue(Path(result["backup"]).exists())

    def test_unknown_output_is_not_accepted(self):
        self.plain()
        self.fake.save_head = b"invalid"
        with api.HwpxSession() as session:
            session.open(self.src)
            with self.assertRaises(api.SaveFailed):
                session.save(protection="preserve")

    def test_package_zip_is_opened_as_hwpx(self):
        package = self.tmp / "template.package.zip"
        package.write_bytes(b"PK\x03\x04package")
        self.use(FakeHwp())
        with api.HwpxSession() as session:
            session.open(package)
        self.assertIn(("Open", package.name, "HWPX", api.hs.OPEN_ARG), self.fake.log)


if __name__ == "__main__":
    unittest.main()
