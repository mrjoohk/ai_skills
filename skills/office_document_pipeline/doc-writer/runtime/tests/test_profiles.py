"""Cross-template regression checks for profile-driven generation and insertion."""
import json
import contextlib
import io
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_write as tw
import test_insert as ti
import write_doc as wd
import insert_doc as ins
import template_profiles as profiles
import table_style as ts
import hwpx_api as api
import hwp_session as hs
from fake_hwp import FakeHwp, make_env


class TestProfiles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.styles = dict(wd.STYLES, heading="문서 제목 [{level}]", para="일반 문단", item="일반 문단",
                           need="보충 메모", caption="개체 설명", figure="개체 설명", anchor="일반 문단",
                           th="표 제목", td="표 본문")

    def custom_xml(self, xml):
        for old, new in sorted(zip(wd.STYLES.values(), self.styles.values()), key=lambda x: len(x[0]), reverse=True):
            if old == wd.STYLES["heading"]:
                for level in range(1, 8):
                    xml = xml.replace(old.format(level=level), new.format(level=level))
            else:
                xml = xml.replace(old, new)
        return xml

    def session(self, fake):
        dispatch, pids, killer, _ = make_env(fake)
        return api.HwpxSession(session=hs.HwpSession(dispatch=dispatch, pids=pids, killer=killer, sleep=lambda _: None))

    def test_custom_generation_and_need_location(self):
        template = self.tmp / "tpl.hwpx"
        template.write_bytes(b"BMS DocuRay" + bytes(40))
        fake = FakeHwp(docs={template.name: self.custom_xml(tw.template_sized_hwpml())})
        meta = {"template": "tpl.hwpx", "out": "out/result.hwpx", "styles": self.styles}
        blocks = wd.parse_spec('```json\n'+json.dumps(meta,ensure_ascii=False)+'\n```\n# 개요\n## 새 절\n> 보충할 내용\n')[1]
        with mock.patch.object(wd, "ROOT", self.tmp), self.session(fake) as session:
            result = wd.write(session, meta, blocks, log=lambda _: None)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["needs"][0]["after"], "새 절")
        self.assertIn('Name="문서 제목 [2]"', fake.docs["result.hwpx"])

    def test_custom_insertion_checks_custom_headings(self):
        target = self.tmp / "target.hwpx"
        target.write_bytes(b"BMS DocuRay" + bytes(40))
        fake = FakeHwp(docs={target.name: self.custom_xml(ti.target_doc())})
        blocks = ins.parse_blocks("#### 새 절\n추가 내용")
        with mock.patch.object(ins, "ROOT", self.tmp), self.session(fake) as session:
            result = ins.insert(session, target, blocks, ti.ANCHOR, self.tmp / "out.hwpx",
                                styles=self.styles, log=lambda _: None)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["headings"]["new"], {8: "1.1.1.2."})

    def test_heading_detection_and_literal_regex_characters(self):
        self.assertEqual(profiles.heading_level("문서 제목 [7]", self.styles), 7)
        self.assertIsNone(profiles.heading_level("COMSAF 개요 2", self.styles))
        rows = [("text", "문서 제목 [1]", "한 절"), ("text", "일반 문단", "본문"), ("text", "문서 제목 [2]", "하위")]
        self.assertEqual(ins.heading_levels(rows, self.styles), [(0, 1), (2, 2)])

    def test_profile_errors_before_com(self):
        for heading in ("모든 제목", "{other}", "{level}{level}"):
            with self.subTest(heading=heading), self.assertRaises((ValueError, KeyError)):
                profiles.resolve_styles(overrides={"heading": heading})
        for policy in ("none", "plaintext", True):
            with self.subTest(policy=policy), self.assertRaises(wd.SpecError):
                wd.parse_spec('```json\n'+json.dumps({"template":"t.hwpx","out":"o.hwpx","protection":policy})+'\n```\n# 개요')

    def test_unsafe_profile_id_rejected(self):
        path = self.tmp / "profile.json"
        path.write_text(json.dumps({"id":"../../escape","styles":self.styles}),encoding="utf-8")
        with self.assertRaises(ValueError):
            profiles.load_profile(path)

    def test_invalid_insert_profile_fails_before_starting_com(self):
        target = self.tmp / "target.hwpx"
        target.write_bytes(b"BMS DocuRay"+bytes(40))
        spec = self.tmp / "insert.md"
        spec.write_text("## 새 절\n추가 내용", encoding="utf-8")
        report = self.tmp / "report.md"
        with mock.patch.object(api, "HwpxSession") as session, contextlib.redirect_stdout(io.StringIO()):
            code = ins.main([str(target), "--spec", str(spec), "--before", "끝", "--out", str(self.tmp / "out.hwpx"),
                             "--profile", str(self.tmp / "missing.json"), "--report", str(report)])
        session.assert_not_called()
        self.assertEqual(code, 2)
        text = report.read_text(encoding="utf-8")
        self.assertIn("프로파일을 읽지 못했다", text)
        self.assertNotIn("실행 중", text)

    def test_changed_template_is_not_reported_as_modeled(self):
        import fake_write as fw
        source = Path(profiles.load_profile()["_path"]).parent
        target = self.tmp / "document_templates" / "technical-report"
        shutil.copytree(source, target)
        spec = self.tmp / "spec.md"
        meta = {"template": "document_templates/technical-report/template.package.zip",
                "out": "out/report.hwpx", "profile": "technical-report"}
        spec.write_text('```json\n'+json.dumps(meta)+'\n```\n# 개요\n본문', encoding="utf-8")
        with mock.patch.object(fw, "ROOT", self.tmp):
            baseline = fw.run(spec)
            self.assertTrue(baseline["all_ok"], baseline)
            package = target / "template.package.zip"
            package.write_bytes(package.read_bytes()+b"changed")
            changed = fw.run(spec)
        self.assertFalse(changed["checks"]["spec"]["template_modeled"])
        self.assertFalse(changed["all_ok"])

    def test_changed_model_is_not_reported_as_modeled(self):
        import fake_write as fw
        source = Path(profiles.load_profile()["_path"]).parent
        target = self.tmp / "document_templates" / "technical-report"
        shutil.copytree(source, target)
        model = target / "model.hwpml"
        model.write_text(model.read_text(encoding="utf-8").replace("개 요", "개  요"), encoding="utf-8")
        spec = self.tmp / "spec.md"
        meta = {"template": "document_templates/technical-report/template.package.zip",
                "out": "out/report.hwpx", "profile": "technical-report"}
        spec.write_text('```json\n'+json.dumps(meta)+'\n```\n# 개요\n본문', encoding="utf-8")
        with mock.patch.object(fw, "ROOT", self.tmp):
            result = fw.run(spec)
        self.assertFalse(result["checks"]["spec"]["template_modeled"])
        self.assertFalse(result["all_ok"])

    def test_rehashed_model_drift_still_fails_semantic_check(self):
        import fake_write as fw
        source = Path(profiles.load_profile()["_path"]).parent
        target = self.tmp / "document_templates" / "technical-report"
        shutil.copytree(source, target)
        model = target / "model.hwpml"
        original = model.read_text(encoding="utf-8")
        modified = original.replace('Height="1200"', 'Height="1350"', 1)
        self.assertNotEqual(original, modified)
        model.write_text(modified, encoding="utf-8")
        profile = target / "profile.json"
        config = json.loads(profile.read_text(encoding="utf-8"))
        config["model_sha256"] = hashlib.sha256(model.read_bytes()).hexdigest()
        profile.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        spec = self.tmp / "spec.md"
        meta = {"template": "document_templates/technical-report/template.package.zip",
                "out": "out/report.hwpx", "profile": "technical-report"}
        spec.write_text('```json\n'+json.dumps(meta)+'\n```\n# 개요\n본문', encoding="utf-8")
        with mock.patch.object(fw, "ROOT", self.tmp):
            result = fw.run(spec)
        self.assertFalse(result["model_check"]["passed"])
        self.assertTrue(result["model_check"]["differences"])
        self.assertFalse(result["checks"]["spec"]["template_modeled"])
        self.assertFalse(result["all_ok"])

    def test_custom_table_body_styles(self):
        import test_table_style as fixture
        style = ts.from_poc(fixture.poc_report(fixture.ref_doc()), "synthetic.hwpx",
                            default="용어", sections=("s1.",))
        style["body_styles"] = {"center": "짧은 칸", "mixed": "긴 칸"}
        for table in style["tables"].values():
            for row in table.get("cells") or []:
                for cell in row:
                    if cell.get("style") in (ts.CENTER, ts.MIXED):
                        cell["style"] = "짧은 칸"
            for key, value in table.get("styles", {}).items():
                if value in (ts.CENTER, ts.MIXED):
                    table["styles"][key] = "짧은 칸"
        planned = ts.plan_table(style, "새 캡션", [["제목","제목"],["짧게","매우 긴 한글 문장 "*20]])
        body = [cell["style"] for cell in planned["cells"][1]]
        self.assertEqual(body, ["짧은 칸", "긴 칸"])


if __name__ == "__main__":
    unittest.main()
