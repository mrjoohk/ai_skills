"""Office writer policy tests with a fake runner; never dispatches COM."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

_HERE = Path(__file__).resolve()
_CANDIDATES = [_HERE.parents[2] / "office-writer" / "scripts" / "write_office_doc.py"]
_CANDIDATES += [p / ".claude" / "skills" / "doc-writer" / "backends" / "office-writer" / "scripts" / "write_office_doc.py"
                for p in _HERE.parents]
SCRIPT = next((p for p in _CANDIDATES if p.is_file()), _CANDIDATES[0])
spec = importlib.util.spec_from_file_location("office_policy_under_test", SCRIPT)
office = importlib.util.module_from_spec(spec)
spec.loader.exec_module(office)


class TestOfficeProtection(unittest.TestCase):
    def exercise(self, source_head=b"PK\x03\x04", output_head=b"PK\x03\x04", mode="replace", overwrite=False, policy=None):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "source.xlsx"
            original = source_head + b"source"
            src.write_bytes(original)
            def runner(create, full, dest, options, out):
                Path(dest).write_bytes(output_head + b"result")
            args = [str(src), "--mode", mode, "--map", str(src)]
            if overwrite:
                args += ["--overwrite"]
            if policy:
                args += ["--protection", policy]
            with mock.patch.object(office, "run_excel", runner), contextlib.redirect_stdout(io.StringIO()):
                code = office.main(args, create=lambda *a: None)
            return code, src.read_bytes(), original, (Path(str(src) + ".bak").exists())

    def test_plain_preserve(self):
        self.assertEqual(self.exercise()[0], 0)

    def test_protect_and_required_still_require_protection(self):
        self.assertEqual(self.exercise(mode="protect")[0], 3)
        self.assertEqual(self.exercise(policy="required")[0], 3)

    def test_protected_source_never_downgrades(self):
        self.assertEqual(self.exercise(source_head=b"BMS DocuRay")[0], 3)

    def test_failed_overwrite_preserves_protected_original(self):
        code, after, original, backup = self.exercise(source_head=b"BMS DocuRay", overwrite=True)
        self.assertEqual(code, 3)
        self.assertEqual(after, original)
        self.assertTrue(backup)

    def test_plain_overwrite_commits_verified_result(self):
        code, after, original, backup = self.exercise(overwrite=True)
        self.assertEqual(code, 0)
        self.assertNotEqual(after, original)
        self.assertTrue(backup)
