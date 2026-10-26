"""실측 드라이버(tools/test_hwpx/hwpx_drm_e2e.py)의 판정 보조 함수 시험. 실측 자체는 사용자 PC에서."""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import hwp_session  # noqa: E402,F401  (드라이버가 import 하는 모듈을 먼저 올려 둔다)

CANDIDATES = [HERE.parents[1] / "test_hwpx" / "hwpx_drm_e2e.py",   # 정본 배치: tools/hwpx-drm/tests -> tools/test_hwpx
              HERE.parent / "e2e" / "hwpx_drm_e2e.py"]             # 작업용 사본 배치


def load_driver():
    for c in CANDIDATES:
        if c.exists():
            spec = importlib.util.spec_from_file_location("hwpx_drm_e2e_under_test", c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise unittest.SkipTest("드라이버 파일 없음")


class TestSnapshot(unittest.TestCase):                     # F-082
    def setUp(self):
        self.e = load_driver()
        self.tmp = Path(tempfile.mkdtemp())
        self.orig = (self.e.ROOT, self.e.TPL, self.e.SKILL, self.e.HERE)
        self.e.ROOT = self.tmp
        self.e.TPL = self.tmp / "reference" / "template_backup"
        self.e.SKILL = self.tmp / "tools" / "hwpx-drm"
        self.e.HERE = self.tmp / "tools" / "test_hwpx"
        for d in (self.e.TPL, self.e.SKILL, self.e.HERE, self.tmp / "logs"):
            d.mkdir(parents=True)

    def tearDown(self):
        self.e.ROOT, self.e.TPL, self.e.SKILL, self.e.HERE = self.orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_other_workstream_files_ignored(self):
        before = self.e.snapshot()
        (self.tmp / "logs" / "P-099_other.md").write_text("x")       # 다른 세션의 기록
        self.assertEqual(self.e.snapshot() - before, set())

    def test_files_next_to_source_or_root_detected(self):         # 음성대조: 스킬이 만들면 잡힌다
        before = self.e.snapshot()
        (self.e.TPL / "SDP.inspect.md").write_text("x")
        (self.tmp / "hwpx_md.md").write_text("x")
        (self.e.SKILL / "scripts").mkdir()
        (self.e.SKILL / "scripts" / "leak.md").write_text("x")
        self.assertEqual({p.name for p in self.e.snapshot() - before}, {"SDP.inspect.md", "hwpx_md.md", "leak.md"})


if __name__ == "__main__":
    unittest.main()
