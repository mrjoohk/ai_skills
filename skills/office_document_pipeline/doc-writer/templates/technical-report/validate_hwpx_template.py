#!/usr/bin/env python3
"""Structural HWPX package/reference validator; not a schema or application validator."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
N = {
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "opf": "http://www.idpf.org/2007/opf/",
    "ocf": "urn:oasis:names:tc:opendocument:xmlns:container",
}
REQUIRED = {"mimetype", "version.xml", "Contents/header.xml", "Contents/section0.xml", "Contents/content.hpf",
            "settings.xml", "Preview/PrvText.txt", "META-INF/container.xml", "META-INF/manifest.xml"}
STYLE_NAMES = {"03_본문_내용", "04_도표그림_제목", "05_도표내용_항목제목", "07_도표내용_본문혼합",
               "06_도표내용_본문중앙", "14_도움말_파란색"} | {f"COMSAF 개요 {i}" for i in range(1, 8)}


def validate_members(payload: dict[str, bytes], kind: str) -> dict:
    checks, errors = [], []

    def check(name, condition, detail=None):
        checks.append({"check": name, "passed": bool(condition), **({"detail": detail} if detail is not None else {})})
        if not condition:
            errors.append(name)

    check("required_members", REQUIRED <= payload.keys(), sorted(REQUIRED - payload.keys()))
    check("mimetype_exact", payload.get("mimetype") == b"application/hwp+zip")
    check("no_absolute_or_parent_paths", all(not PurePosixPath(p).is_absolute() and ".." not in PurePosixPath(p).parts and "\\" not in p for p in payload))
    check("no_embedded_project_or_external_binary", not any(p.startswith(("BinData/", "Scripts/")) for p in payload))
    parsed = {}
    for name, data in payload.items():
        if name.endswith((".xml", ".hpf")):
            try:
                parsed[name] = ET.fromstring(data)
            except ET.ParseError as e:
                errors.append("xml_parse:" + name)
                checks.append({"check": "xml_parse:" + name, "passed": False, "detail": str(e)})
    check("xml_all_well_formed", len(parsed) == sum(p.endswith((".xml", ".hpf")) for p in payload))
    if not {"Contents/header.xml", "Contents/section0.xml", "Contents/content.hpf", "META-INF/container.xml"} <= parsed.keys():
        return {"passed": False, "checks": checks, "errors": errors}
    h, s, p = (parsed[x] for x in ("Contents/header.xml", "Contents/section0.xml", "Contents/content.hpf"))
    check("head_namespace_and_section_count", h.tag == "{" + N["hh"] + "}head" and h.get("secCnt") == "1")
    check("section_namespace", s.tag == "{" + N["hs"] + "}sec")
    groups = {}
    for groupname, tag in (("styles", "style"), ("paraProperties", "paraPr"), ("charProperties", "charPr"),
                           ("borderFills", "borderFill"), ("tabProperties", "tabPr"), ("numberings", "numbering")):
        group = h.find("hh:refList/hh:" + groupname, N)
        values = [] if group is None else group.findall("hh:" + tag, N)
        ids = [x.get("id") for x in values]
        groups[tag] = {x.get("id"): x for x in values}
        check("reference_group:" + groupname, group is not None and group.get("itemCnt") == str(len(values)) and len(ids) == len(set(ids)))
    fonts = h.findall("hh:refList/hh:fontfaces/hh:fontface", N)
    check("seven_language_font_tables", len(fonts) == 7 and {f.get("lang") for f in fonts} == {"HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER"})
    fontmap = {f.get("lang").lower(): {x.get("id") for x in f} for f in fonts}
    check("font_counts", all(f.get("fontCnt") == str(len(f)) for f in fonts))
    check("font_reference_resolution", all(v in fontmap.get(k, set()) for f in h.findall(".//hh:fontRef", N) for k, v in f.attrib.items()))
    styles = groups["style"]
    check("preset_style_names", STYLE_NAMES <= {x.get("name") for x in styles.values()})
    check("style_reference_resolution", all(x.get("paraPrIDRef") in groups["paraPr"] and x.get("charPrIDRef") in groups["charPr"] and x.get("nextStyleIDRef") in styles for x in styles.values()))
    references = {"styleIDRef": "style", "paraPrIDRef": "paraPr", "charPrIDRef": "charPr", "tabPrIDRef": "tabPr", "borderFillIDRef": "borderFill", "outlineShapeIDRef": "numbering"}
    unresolved = []
    for root in (h, s):
        for elem in root.iter():
            for attr, target in references.items():
                value = elem.get(attr)
                if value is not None and value != "4294967295" and value not in groups[target]:
                    unresolved.append({"tag": elem.tag.rsplit("}", 1)[-1], "attr": attr, "value": value})
    check("all_style_shape_and_numbering_references_resolve", not unresolved, unresolved)
    outline_levels = []
    for i in range(1, 8):
        style = next((x for x in styles.values() if x.get("name") == f"COMSAF 개요 {i}"), None)
        para = groups["paraPr"].get(style.get("paraPrIDRef")) if style is not None else None
        heading = para.find("hh:heading", N) if para is not None else None
        outline_levels.append(heading is not None and heading.get("type") == "OUTLINE" and heading.get("level") == str(i - 1))
    check("outline_styles_cover_levels_1_to_7", all(outline_levels))
    numbering = groups["numbering"].get("1")
    check("numbering_defines_levels_1_to_7", numbering is not None and {str(i) for i in range(1, 8)} <= {x.get("level") for x in numbering})
    paragraphs = s.findall(".//hp:p", N)
    paraids = [x.get("id") for x in paragraphs]
    check("paragraph_ids_unique", len(paraids) == len(set(paraids)))
    page = s.find(".//hp:pagePr", N)
    check("a4_portrait", page is not None and page.get("width") == "59528" and page.get("height") == "84186" and int(page.get("width")) < int(page.get("height")))
    check("one_section_definition", len(s.findall(".//hp:secPr", N)) == 1)
    top = s.findall("hp:p", N)
    firsttext = "".join(top[0].itertext()) if top else ""
    check("first_heading_only_text", firsttext == "개 요", firsttext)
    check("first_heading_has_outline_style", bool(top) and top[0].get("styleIDRef") in styles and styles[top[0].get("styleIDRef")].get("name") == "COMSAF 개요 1")
    manifest = p.findall("opf:manifest/opf:item", N)
    manifestids = {x.get("id"): x.get("href") for x in manifest}
    check("manifest_paths_exist", all(x.get("href") in payload for x in manifest))
    check("spine_ids_resolve", all(x.get("idref") in manifestids for x in p.findall("opf:spine/opf:itemref", N)))
    check("container_rootfiles_exist", all(x.get("full-path") in payload for x in parsed["META-INF/container.xml"].findall("ocf:rootfiles/ocf:rootfile", N)))
    check("no_business_project_strings", all(token not in b"\n".join(payload.values()) for token in (b"drmHWP", b"hmumt_scheduler", b"surak", b"output_docs/SUM", b"D-062", b"P-052")))
    tables = s.findall(".//hp:tbl", N)
    if kind == "template":
        check("blank_template_body_is_one_heading", len(top) == 1 and len(paragraphs) == 1 and not tables)
    else:
        check("specimen_contains_table", len(tables) == 1)
        for ti, table in enumerate(tables):
            rows = table.findall("hp:tr", N)
            nrows, ncols = int(table.get("rowCnt")), int(table.get("colCnt"))
            cells = table.findall("hp:tr/hp:tc", N)
            addresses = [(int(a.get("rowAddr")), int(a.get("colAddr"))) for a in table.findall("hp:tr/hp:tc/hp:cellAddr", N)]
            check(f"table_{ti}_grid", len(rows) == nrows and len(cells) == nrows * ncols and set(addresses) == {(r, c) for r in range(nrows) for c in range(ncols)})
            check(f"table_{ti}_caption", table.find("hp:caption/hp:subList/hp:p", N) is not None)
            autonum = table.find(".//hp:autoNum", N)
            check(f"table_{ti}_caption_autonumber", autonum is not None and autonum.get("numType") == "TABLE" and autonum.find("hp:autoNumFormat", N) is not None)
    return {"passed": not errors, "checks": checks, "errors": errors,
            "summary": {"members": len(payload), "xml_documents": len(parsed), "styles": len(styles), "paragraphs": len(paragraphs), "tables": len(tables)},
            "limitations": ["No full OWPML XSD validation", "No Hancom application open/reflow/save validation", "No DRM validation", "No legacy HWPML 2.8 output claimed"]}


def validate_package(path, kind):
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        payload = {x.filename: z.read(x) for x in infos}
        result = validate_members(payload, kind)
        zipchecks = {
            "zip_crc": z.testzip() is None,
            "zip_no_duplicate_members": len(infos) == len(payload),
            "zip_mimetype_first_and_uncompressed": bool(infos) and infos[0].filename == "mimetype" and infos[0].compress_type == zipfile.ZIP_STORED,
            "zip_not_encrypted": all(not (x.flag_bits & 1) for x in infos),
        }
        result["checks"] = [{"check": k, "passed": v} for k, v in zipchecks.items()] + result["checks"]
        result["errors"] += [k for k, v in zipchecks.items() if not v]
        result["passed"] = not result["errors"]
        result["path"] = str(path)
        result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result, payload


def mutation_checks(template, specimen):
    cases = []
    broken = copy.deepcopy(template)
    root = ET.fromstring(broken["Contents/section0.xml"])
    root[0].set("styleIDRef", "9999")
    broken["Contents/section0.xml"] = ET.tostring(root)
    cases.append(("missing_style_reference", broken, "template"))
    broken = copy.deepcopy(template)
    del broken["settings.xml"]
    cases.append(("missing_manifest_target", broken, "template"))
    broken = copy.deepcopy(specimen)
    root = ET.fromstring(broken["Contents/section0.xml"])
    root.find(".//hp:tbl", N).set("rowCnt", "3")
    broken["Contents/section0.xml"] = ET.tostring(root)
    cases.append(("incorrect_table_grid", broken, "specimen"))
    return [{"mutation": name, "rejected": not validate_members(payload, kind)["passed"]} for name, payload, kind in cases]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=HERE / "template.package.zip")
    parser.add_argument("--directory", type=Path, help="Validate a generated template and specimen pair")
    parser.add_argument("--report", type=Path, default=HERE / "validation_report.json")
    opts = parser.parse_args()
    path = opts.directory / "technical_report_template.package.zip" if opts.directory else opts.package
    template_result, template = validate_package(path, "template")
    results = [template_result]
    if opts.directory:
        specimen_result, specimen = validate_package(opts.directory / "technical_report_specimen.package.zip", "specimen")
        results.append(specimen_result)
    else:
        import build_hwpx_template
        specimen = build_hwpx_template.members(True)
    mutations = mutation_checks(template, specimen) if template_result["passed"] else []
    report = {"passed": all(x["passed"] for x in results) and bool(mutations) and all(x["rejected"] for x in mutations),
              "validation_level": "ZIP/XML/references only", "packages": results, "negative_controls": mutations,
              "application_validation": {"status": "UNVERIFIED", "reason": "This validator does not start HWP or render layout"}}
    opts.report.parent.mkdir(parents=True, exist_ok=True)
    opts.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "errors": [x["errors"] for x in results],
                      "negative_controls": mutations, "report": str(opts.report)}, ensure_ascii=True))
    raise SystemExit(0 if report["passed"] else 1)
