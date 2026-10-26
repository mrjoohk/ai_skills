"""Standalone errors must remain readable on a Windows CP949 pipe."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class TestConsole(unittest.TestCase):
    def test_extract_error_on_cp949_pipe(self):
        script = Path(__file__).resolve().parents[1] / "extract_figures.py"
        env = dict(os.environ, PYTHONIOENCODING="cp949", PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "합성-문서.hwpx"
            source.write_bytes(b"BMS DocuRay synthetic fixture")
            destination = Path(directory) / "images"
            direct = [sys.executable, str(script), str(source), str(destination)]
            imported = [
                sys.executable, "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); import extract_figures; "
                "sys.exit(extract_figures.main(sys.argv[2:]))",
                str(script.parent), str(source), str(destination),
            ]
            for command in (direct, imported):
                with self.subTest(invocation=command[1]):
                    result = subprocess.run(
                        command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
                    )
                    output = (result.stdout + result.stderr).decode("utf-8")
                    self.assertEqual(result.returncode, 2, output)
                    self.assertIn("DRM", output)
                    self.assertNotIn("UnicodeEncodeError", output)
                    self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
