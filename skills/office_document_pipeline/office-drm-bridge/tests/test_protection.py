"""Plain input support and protected-source downgrade negative controls."""
import os
from pathlib import Path
import unittest

from test_bridge import Base as OfficeBase, FakeRunner, req
from test_bridge_hwpx import Base as HwpBase, InsertBase, FakeHwpx, FakeInsert, FakePack


class TestOfficePolicy(OfficeBase):
    def test_plain_replace_is_allowed(self):
        res, runner = self.run_req(req("replace", "reference/doc.xlsx", {"map": {"a": "b"}}), FakeRunner(protect=False))
        self.assertEqual(res["status"], "ok", res)
        self.assertFalse(res["protection_required"])
        self.assertIn("--protection=preserve", runner.calls[0])

    def test_protected_replace_downgrade_is_quarantined(self):
        Path(self.root, "reference/doc.xlsx").write_bytes(b"BMS DocuRay source")
        res, runner = self.run_req(req("replace", "reference/doc.xlsx", {"map": {"a": "b"}}), FakeRunner(protect=False))
        self.assertEqual(res["status"], "error", res)
        self.assertTrue(res["protection_required"])
        self.assertIn("--protection=required", runner.calls[0])
        self.assertFalse(Path(self.root, "output_docs/doc_out.xlsx").exists())
        self.assertTrue(any("plaintext_out" in p["path"] for p in res["outputs"]))

    def test_explicit_required_plain_is_rejected(self):
        res, _ = self.run_req(req("replace", "reference/doc.xlsx", {"map": {"a": "b"}, "protection": "required"}), FakeRunner(protect=False))
        self.assertEqual(res["status"], "error")

    def test_failed_office_save_is_quarantined_even_when_protected(self):
        def failed(cmd, timeout):
            FakeRunner()(cmd, timeout)
            return 1, "FAILED: verification"
        res, _ = self.run_req(req("replace", "reference/doc.xlsx", {"map": {"a": "b"}}), failed)
        self.assertEqual(res["status"], "error", res)
        self.assertFalse(Path(self.root, "output_docs/doc_out.xlsx").exists())
        self.assertTrue(any("unverified_out" in p["path"] for p in res["outputs"]))


class TestHwpPolicy(HwpBase):
    def test_plain_fill_is_allowed(self):
        Path(self.root, "reference/form.hwpx").write_bytes(b"PK\x03\x04source")
        res, runner = self.run_req(req("fill", "reference/form.hwpx", {"map": {"a": "b"}}), FakeHwpx(protect=False))
        self.assertEqual(res["status"], "ok", res)
        self.assertIn("--protection=preserve", runner.calls[0])
        self.assertFalse(res["drm_signature"])

    def test_plain_failed_fill_is_still_quarantined(self):
        Path(self.root, "reference/form.hwpx").write_bytes(b"PK\x03\x04source")
        res, _ = self.run_req(req("fill", "reference/form.hwpx", {"map": {"a": "b"}}), FakeHwpx(protect=False, rc=1))
        self.assertEqual(res["status"], "error", res)
        self.assertFalse(Path(self.root, "output_docs/form_out.hwpx").exists())
        self.assertTrue(any("unverified_out" in p["path"] for p in res["outputs"]))

    def test_unknown_container_is_not_plain_success(self):
        Path(self.root, "reference/form.hwpx").write_bytes(b"PK\x03\x04source")
        def corrupted(cmd, timeout):
            FakeHwpx(protect=False)(cmd, timeout)
            output = next(c.split("=", 1)[1] for c in cmd if c.startswith("--out="))
            Path(output).write_bytes(b"corrupted result")
            return 0, "저장 완료"
        res, _ = self.run_req(req("fill", "reference/form.hwpx", {"map": {"a": "b"}}), corrupted)
        self.assertEqual(res["status"], "error", res)
        self.assertFalse(Path(self.root, "output_docs/form_out.hwpx").exists())


class TestInsertSourcePolicy(InsertBase):
    def test_protected_figure_escalates_plain_target(self):
        Path(self.root, "reference/form.hwpx").write_bytes(b"PK\x03\x04source")
        self.spec("output_docs/ins.md", '# 개요\n![그림](hwpx:reference/other.hwpx#1 "80x40")\n')
        res, runner = self.run_req(req("insert", "reference/form.hwpx", self.args()), FakeInsert(protect=False))
        self.assertTrue(res["protection_required"])
        self.assertEqual(res["status"], "error", res)
        self.assertIn("--protection=required", runner.calls[0])

    def test_plain_figpack_is_allowed(self):
        Path(self.root, "reference/form.hwpx").write_bytes(b"PK\x03\x04source")
        Path(self.root, "tools/doc-writer/figure_pack.py").write_text("# fake\n")
        self.write_pin()
        res, _ = self.run_req(req("figpack", "reference/form.hwpx", {"out_dir": "output_docs/pack"}),
                              FakePack(plain=("all.hwpx", "fig01.hwpx", "fig02.hwpx")))
        self.assertEqual(res["status"], "ok", res)
        self.assertFalse(res["drm_signature"])
        self.assertTrue(Path(self.root, "output_docs/pack/all.hwpx").exists())
