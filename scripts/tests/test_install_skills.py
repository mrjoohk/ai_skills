"""Installer integration checks use isolated projects and never modify a real project."""
import hashlib
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("skill_installer", ROOT / "scripts/install_skills.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class TestInstall(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.project = self.tmp / "project"

    def install(self, *args):
        return installer.main(["--project-root", str(self.project), "--pipeline", "office-documents", *args])

    def legacy(self, name="office-com-reader"):
        entry = self.project / ".claude/skills" / name / "SKILL.md"
        entry.parent.mkdir(parents=True)
        source = ROOT / "archive/document-skills-2026-10-25" / (name + ".SKILL.md")
        entry.write_bytes(source.read_bytes())
        return entry

    def test_catalog_has_unique_merged_entrypoints(self):
        catalog, paths = installer.load_catalog()
        self.assertEqual(len(paths), 36)
        self.assertFalse(set(catalog["skill_aliases"]) & set(paths))
        for name, alias in catalog["skill_aliases"].items():
            self.assertIn(alias["skill"], paths)

    def test_fresh_installs_template_and_tools(self):
        self.assertEqual(self.install(), 0)
        self.assertTrue((self.project / "tools/doc-writer/template_profiles.py").is_file())
        self.assertTrue((self.project / "document_templates/technical-report/template.package.zip").is_file())
        self.assertTrue((self.project / ".claude/skills/doc-writer/backends/hwp/scripts/hwpx_api.py").is_file())
        self.assertFalse((self.project / ".claude/skills/office-com-reader").exists())

    def test_without_tools_is_self_contained_skill(self):
        self.assertEqual(self.install("--without-project-tools"), 0)
        self.assertTrue((self.project / ".claude/skills/doc-writer/templates/technical-report/profile.json").is_file())
        self.assertFalse((self.project / "tools").exists())
        self.assertFalse((self.project / "document_templates").exists())

    def test_conflict_is_checked_before_any_copy(self):
        target = self.project / ".claude/skills/doc-writer/SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("local edit", encoding="utf-8")
        self.assertEqual(self.install(), 1)
        self.assertEqual(target.read_text(), "local edit")
        self.assertFalse((self.project / "tools").exists())

    def test_legacy_requires_explicit_migration(self):
        entry = self.legacy()
        with self.assertRaises(SystemExit):
            self.install()
        self.assertTrue(entry.is_file())
        self.assertFalse((self.project / "tools").exists())

    def test_migration_archives_only_known_entrypoint_preserving_extras(self):
        entry = self.legacy()
        extra = entry.parent / "custom.txt"
        extra.write_text("keep")
        self.assertEqual(self.install("--migrate-legacy"), 0)
        archived = list((self.project / ".claude/retired-skills/office-com-reader").glob("SKILL.*.md"))
        self.assertEqual(len(archived), 1)
        self.assertFalse(entry.exists())
        self.assertEqual(extra.read_text(), "keep")
        self.assertEqual(self.install("--migrate-legacy"), 0)

    def test_customized_legacy_blocks_migration_without_writes(self):
        entry = self.legacy()
        entry.write_text(entry.read_text(encoding="utf-8")+"\ncustom", encoding="utf-8")
        before = hashlib.sha256(entry.read_bytes()).digest()
        with self.assertRaises(SystemExit):
            self.install("--migrate-legacy", "--overwrite")
        self.assertEqual(hashlib.sha256(entry.read_bytes()).digest(), before)
        self.assertFalse((self.project / "tools").exists())

    def test_dry_run_never_moves_legacy(self):
        entry = self.legacy()
        self.assertEqual(self.install("--migrate-legacy", "--dry-run"), 0)
        self.assertTrue(entry.exists())
        self.assertFalse((self.project / "tools").exists())

    def test_required_resource_is_checked_before_any_copy(self):
        catalog, paths = installer.load_catalog()
        catalog["project_resources"][0]["required_files"].append("__missing_writer__.py")
        with mock.patch.object(installer, "load_catalog", return_value=(catalog, paths)):
            with self.assertRaises(SystemExit):
                self.install()
        self.assertFalse(self.project.exists())


if __name__ == "__main__":
    unittest.main()

