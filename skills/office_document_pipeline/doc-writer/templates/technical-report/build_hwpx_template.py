#!/usr/bin/env python3
"""Generate synthetic reusable HWPX packages without HWP, COM, or project documents.

This is an independently authored, limited technical-report preset based on the
public Hancom OWPML model and structural observations of installed vendor files.
No vendor document XML, binary template, image, or business text is copied.
Package/XML/reference checks do not establish application compatibility or DRM.

본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
NS = {
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hv": "http://www.hancom.co.kr/hwpml/2011/version",
    "ha": "http://www.hancom.co.kr/hwpml/2011/app",
    "opf": "http://www.idpf.org/2007/opf/",
    "ocf": "urn:oasis:names:tc:opendocument:xmlns:container",
    "odf": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

STYLE_NAMES = ["바탕글", "03_본문_내용"] + [f"COMSAF 개요 {n}" for n in range(1, 8)] + [
    "04_도표그림_제목", "05_도표내용_항목제목", "07_도표내용_본문혼합", "06_도표내용_본문중앙", "14_도움말_파란색",
]
STYLE_CHAR = [0, 0] + [1] * 7 + [2, 3, 0, 0, 4]
STYLES = {
    "heading": "COMSAF 개요 {level}", "para": "03_본문_내용", "item": "03_본문_내용",
    "anchor": "03_본문_내용", "need": "14_도움말_파란색", "caption": "04_도표그림_제목",
    "figure": "04_도표그림_제목", "th": "05_도표내용_항목제목", "td": "07_도표내용_본문혼합",
}
LANGS = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
LANG_ATTRS = tuple(x.lower() for x in LANGS)
PAGE_WIDTH, PAGE_HEIGHT, BODY_WIDTH = 59528, 84186, 45354


def node(tag: str, parent: ET.Element | None = None, text: str | None = None, **attrs) -> ET.Element:
    prefix, name = tag.split(":")
    e = ET.Element(f"{{{NS[prefix]}}}{name}", {k: str(v) for k, v in attrs.items()})
    if text is not None:
        e.text = text
    if parent is not None:
        parent.append(e)
    return e


def xml(e: ET.Element) -> bytes:
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(e, encoding="utf-8")


def margins(parent, prefix="hp", **values):
    return node(prefix + ":margin", parent, **values)


def header() -> ET.Element:
    h = node("hh:head", version="1.5", secCnt=1)
    node("hh:beginNum", h, page=1, footnote=1, endnote=1, pic=1, tbl=1, equation=1)
    refs = node("hh:refList", h)
    fonts = node("hh:fontfaces", refs, itemCnt=7)
    for lang in LANGS:
        face = node("hh:fontface", fonts, lang=lang, fontCnt=1)
        node("hh:font", face, id=0, face="맑은 고딕", type="TTF", isEmbedded=0)
    borders = node("hh:borderFills", refs, itemCnt=2)
    for identity, line in ((1, "NONE"), (2, "SOLID")):
        b = node("hh:borderFill", borders, id=identity, threeD=0, shadow=0, centerLine="NONE", breakCellSeparateLine=0)
        node("hh:slash", b, type="NONE", Crooked=0, isCounter=0)
        node("hh:backSlash", b, type="NONE", Crooked=0, isCounter=0)
        for side in ("leftBorder", "rightBorder", "topBorder", "bottomBorder"):
            node("hh:" + side, b, type=line, width="0.12 mm", color="#000000")
        node("hh:diagonal", b, type="NONE", width="0.12 mm", color="#000000")
    chars = node("hh:charProperties", refs, itemCnt=5)
    for identity, height, bold, color in ((0, 1000, False, "#000000"), (1, 1200, True, "#000000"),
                                         (2, 900, False, "#000000"), (3, 1000, True, "#000000"),
                                         (4, 900, False, "#0000FF")):
        c = node("hh:charPr", chars, id=identity, height=height, textColor=color, shadeColor="none",
                 useFontSpace=0, useKerning=0, symMark="NONE", borderFillIDRef=1)
        for group, value in (("fontRef", 0), ("ratio", 100), ("spacing", 0), ("relSz", 100), ("offset", 0)):
            node("hh:" + group, c, **dict.fromkeys(LANG_ATTRS, value))
        if bold:
            node("hh:bold", c)
        node("hh:underline", c, type="NONE", shape="SOLID", color="#000000")
        node("hh:strikeout", c, shape="NONE", color="#000000")
        node("hh:outline", c, type="NONE")
        node("hh:shadow", c, type="NONE", color="#C0C0C0", offsetX=0, offsetY=0)
    tabs = node("hh:tabProperties", refs, itemCnt=1)
    node("hh:tabPr", tabs, id=0, autoTabLeft=0, autoTabRight=0)
    nums = node("hh:numberings", refs, itemCnt=1)
    numbering = node("hh:numbering", nums, id=1, start=0)
    for level in range(1, 11):
        text = ".".join(f"^{n}" for n in range(1, level + 1)) + "."
        node("hh:paraHead", numbering, text=text, start=1, level=level, align="LEFT", useInstWidth=1,
             autoIndent=1, widthAdjust=0, textOffsetType="PERCENT", textOffset=50,
             numFormat="DIGIT", charPrIDRef=4294967295, checkable=0)
    paragraphs = node("hh:paraProperties", refs, itemCnt=len(STYLE_NAMES))
    for identity in range(len(STYLE_NAMES)):
        p = node("hh:paraPr", paragraphs, id=identity, tabPrIDRef=0, condense=0,
                 fontLineHeight=0, snapToGrid=1, suppressLineNumbers=0, checked=0, textDir="LTR")
        outline = 2 <= identity <= 8
        center = identity in (9, 10, 12)
        node("hh:align", p, horizontal="CENTER" if center else "LEFT", vertical="BASELINE")
        # OUTLINE idRef=0 selects the section outline numbering, as in vendor output.
        node("hh:heading", p, type="OUTLINE" if outline else "NONE", idRef=0, level=identity - 2 if outline else 0)
        node("hh:breakSetting", p, breakLatinWord="KEEP_WORD", breakNonLatinWord="KEEP_WORD", widowOrphan=0,
             keepWithNext=1 if outline else 0, keepLines=0, pageBreakBefore=0, lineWrap="BREAK")
        node("hh:autoSpacing", p, eAsianEng=0, eAsianNum=0)
        margin = node("hh:margin", p)
        for kind in ("intent", "left", "right", "prev", "next"):
            node("hc:" + kind, margin, value=0, unit="HWPUNIT")
        node("hh:lineSpacing", p, type="PERCENT", value=160, unit="HWPUNIT")
        node("hh:border", p, borderFillIDRef=1, offsetLeft=0, offsetRight=0, offsetTop=0, offsetBottom=0,
             connect=0, ignoreMargin=0)
    styles = node("hh:styles", refs, itemCnt=len(STYLE_NAMES))
    for identity, (name, charid) in enumerate(zip(STYLE_NAMES, STYLE_CHAR)):
        node("hh:style", styles, id=identity, type="PARA", name=name,
             engName=(f"Outline {identity - 1}" if 2 <= identity <= 8 else f"Preset Style {identity}"),
             paraPrIDRef=identity, charPrIDRef=charid, nextStyleIDRef=1 if 2 <= identity <= 8 else identity,
             langID=1042, lockForm=0)
    node("hh:compatibleDocument", h, targetProgram="HWP201X")
    options = node("hh:docOption", h)
    node("hh:linkinfo", options, path="", pageInherit=0, footnoteInherit=0)
    return h


def section_properties(run: ET.Element):
    sec = node("hp:secPr", run, id="", textDirection="HORIZONTAL", spaceColumns=1134, tabStop=8000,
               tabStopVal=4000, tabStopUnit="HWPUNIT", outlineShapeIDRef=1, memoShapeIDRef=0,
               textVerticalWidthHead=0, masterPageCnt=0)
    node("hp:grid", sec, lineGrid=0, charGrid=0, wonggojiFormat=0)
    node("hp:startNum", sec, pageStartsOn="BOTH", page=0, pic=0, tbl=0, equation=0)
    node("hp:visibility", sec, hideFirstHeader=0, hideFirstFooter=0, hideFirstMasterPage=0,
         border="SHOW_ALL", fill="SHOW_ALL", hideFirstPageNum=0, hideFirstEmptyLine=0, showLineNumber=0)
    node("hp:lineNumberShape", sec, restartType=0, countBy=0, distance=0, startNumber=0)
    page = node("hp:pagePr", sec, landscape="WIDELY", width=PAGE_WIDTH, height=PAGE_HEIGHT, gutterType="LEFT_ONLY")
    margins(page, header=2835, footer=2835, gutter=0, left=7087, right=7087, top=5669, bottom=4252)
    for kind, placement in (("footNotePr", "EACH_COLUMN"), ("endNotePr", "END_OF_DOCUMENT")):
        note = node("hp:" + kind, sec)
        node("hp:autoNumFormat", note, type="DIGIT", userChar="", prefixChar="", suffixChar=")", supscript=0)
        node("hp:noteLine", note, length=-1, type="SOLID", width="0.12 mm", color="#000000")
        node("hp:noteSpacing", note, betweenNotes=283, belowLine=567, aboveLine=850)
        node("hp:numbering", note, type="CONTINUOUS", newNum=1)
        node("hp:placement", note, place=placement, beneathText=0)
    for kind in ("BOTH", "EVEN", "ODD"):
        border = node("hp:pageBorderFill", sec, type=kind, borderFillIDRef=1, textBorder="PAPER",
                      headerInside=0, footerInside=0, fillArea="PAPER")
        node("hp:offset", border, left=0, right=0, top=0, bottom=0)
    ctrl = node("hp:ctrl", run)
    node("hp:colPr", ctrl, id="", type="NEWSPAPER", layout="LEFT", colCount=1, sameSz=1, sameGap=0)


def paragraph(parent, ids, styleid=1, text="", first=False):
    p = node("hp:p", parent, id=next(ids), paraPrIDRef=styleid, styleIDRef=styleid,
             pageBreak=0, columnBreak=0, merged=0)
    r = node("hp:run", p, charPrIDRef=STYLE_CHAR[styleid])
    if first:
        section_properties(r)
    node("hp:t", r, text=text)
    # No synthetic linesegarray: line layout must be recalculated by the consumer.
    return p


def sublist(parent):
    return node("hp:subList", parent, id="", textDirection="HORIZONTAL", lineWrap="BREAK", vertAlign="CENTER",
                linkListIDRef=0, linkListNextIDRef=0, textWidth=0, textHeight=0, hasTextRef=0, hasNumRef=0)


def table(parent, ids):
    p = paragraph(parent, ids, styleid=1)
    r = node("hp:run", p, charPrIDRef=0)
    t = node("hp:tbl", r, id=1000, zOrder=0, numberingType="TABLE", textWrap="TOP_AND_BOTTOM",
             textFlow="BOTH_SIDES", lock=0, dropcapstyle="None", pageBreak="CELL", repeatHeader=1,
             rowCnt=2, colCnt=2, cellSpacing=0, borderFillIDRef=2, noAdjust=0)
    node("hp:sz", t, width=BODY_WIDTH, widthRelTo="ABSOLUTE", height=6000, heightRelTo="ABSOLUTE", protect=0)
    node("hp:pos", t, treatAsChar=1, affectLSpacing=0, flowWithText=1, allowOverlap=0, holdAnchorAndSO=0,
         vertRelTo="PARA", horzRelTo="PARA", vertAlign="TOP", horzAlign="CENTER", vertOffset=0, horzOffset=0)
    node("hp:outMargin", t, left=0, right=0, top=283, bottom=283)
    caption = node("hp:caption", t, side="TOP", fullSz=0, width=BODY_WIDTH, gap=850, lastWidth=BODY_WIDTH)
    cp = paragraph(sublist(caption), ids, styleid=9, text="표 ")
    cr = node("hp:run", cp, charPrIDRef=2)
    auto = node("hp:autoNum", node("hp:ctrl", cr), num=1, numType="TABLE")
    node("hp:autoNumFormat", auto, type="DIGIT", userChar="", prefixChar="", suffixChar="", supscript=0)
    node("hp:t", cr, text=" 합성 표")
    node("hp:inMargin", t, left=283, right=283, top=141, bottom=141)
    for rowid, values in enumerate((("항목", "값"), ("예시", "작성 필요"))):
        row = node("hp:tr", t)
        for colid, text in enumerate(values):
            c = node("hp:tc", row, name="", header=1 if rowid == 0 else 0, hasMargin=0,
                     protect=0, editable=0, dirty=0, borderFillIDRef=2)
            paragraph(sublist(c), ids, styleid=10 if rowid == 0 else 11, text=text)
            node("hp:cellAddr", c, colAddr=colid, rowAddr=rowid)
            node("hp:cellSpan", c, colSpan=1, rowSpan=1)
            node("hp:cellSz", c, width=BODY_WIDTH // 2, height=3000)
            node("hp:cellMargin", c, left=283, right=283, top=141, bottom=141)
    node("hp:t", r)


def section(specimen=False):
    s = node("hs:sec")
    ids = itertools.count(0)
    paragraph(s, ids, styleid=2, text="개 요", first=True)
    if specimen:
        paragraph(s, ids, text="업무 내용이 없는 합성 서식 견본입니다.")
        for level in range(2, 8):
            paragraph(s, ids, styleid=level + 1, text=f"수준 {level} 제목")
        paragraph(s, ids, styleid=13, text="※ 작성 필요: 출처에 근거하여 내용을 작성합니다.")
        table(s, ids)
    return s


def package_xml(specimen=False):
    package = node("opf:package", version="", id="", **{"unique-identifier": ""})
    meta = node("opf:metadata", package)
    node("opf:title", meta, text="Technical Report Preset" + (" Specimen" if specimen else " Template"))
    node("opf:language", meta, text="ko")
    # Generic metadata only. No author/organization, historical date, business file path or approval.
    for name in ("creator", "subject", "description", "keyword"):
        node("opf:meta", meta, name=name, content="text")
    manifest = node("opf:manifest", package)
    for identity, href in (("header", "Contents/header.xml"), ("section0", "Contents/section0.xml"), ("settings", "settings.xml")):
        node("opf:item", manifest, id=identity, href=href, **{"media-type": "application/xml"})
    spine = node("opf:spine", package)
    for identity in ("header", "section0"):
        node("opf:itemref", spine, idref=identity, linear="yes")
    container = node("ocf:container")
    roots = node("ocf:rootfiles", container)
    node("ocf:rootfile", roots, **{"full-path": "Contents/content.hpf", "media-type": "application/hwpml-package+xml"})
    node("ocf:rootfile", roots, **{"full-path": "Preview/PrvText.txt", "media-type": "text/plain"})
    version = node("hv:HCFVersion", tagetApplication="WORDPROCESSOR", major=5, minor=1, micro=1,
                   buildNumber=0, os=1, xmlVersion="1.5", application="Synthetic HWPX Generator", appVersion="1.0")
    settings = node("ha:HWPApplicationSetting")
    node("ha:CaretPosition", settings, listIDRef=0, paraIDRef=0, pos=0)
    return package, container, version, settings


def members(specimen=False):
    package, container, version, settings = package_xml(specimen)
    sec = section(specimen)
    preview = "\n".join(e.text or "" for e in sec.iter(f"{{{NS['hp']}}}t")) + "\n"
    return {
        "mimetype": b"application/hwp+zip",
        "version.xml": xml(version),
        "Contents/header.xml": xml(header()),
        "Contents/section0.xml": xml(sec),
        "Contents/content.hpf": xml(package),
        "settings.xml": xml(settings),
        "Preview/PrvText.txt": preview.encode("utf-8"),
        "META-INF/container.xml": xml(container),
        "META-INF/manifest.xml": xml(node("odf:manifest")),
    }


def package_bytes(specimen=False) -> bytes:
    """Return deterministic logical HWPX bytes; no filesystem or COM access."""
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w") as z:
        for name, data in members(specimen).items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            z.writestr(info, data)
    return memory.getvalue()


def build(output: Path, write_hwpx=False):
    output.mkdir(parents=True, exist_ok=True)
    names = []
    for kind, specimen in (("template", False), ("specimen", True)):
        stem = "technical_report_" + kind
        destination = output / (stem + ".hwpx")
        payload = members(specimen)
        # Compose self-authored synthetic bytes in memory. The local document
        # security agent may wrap .hwpx on write; never unwrap that output.
        logical_bytes = package_bytes(specimen)
        if write_hwpx:
            destination.write_bytes(logical_bytes)
        # This archive is independently generated from our own XML, not copied
        # from/decrypted out of the protected .hwpx. It enables structural QA.
        (output / (stem + ".package.zip")).write_bytes(logical_bytes)
        for name, data in payload.items():
            target = output / (stem + "_xml") / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        names.append(str(destination if write_hwpx else output / (stem + ".package.zip")))
    profile = {
        "profile_id": "technical-report", "template": "technical_report_template.hwpx",
        "first_heading": "개 요", "styles": STYLES, "additional_styles": ["06_도표내용_본문중앙"],
        "scope": "Reusable synthetic preset; not a project policy or an approval",
        "validation": {"zip_xml_references": "run validate_hwpx_template.py", "application_open": "UNVERIFIED", "drm": "UNVERIFIED"},
    }
    (output / "technical_report_profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "technical_report_spec.md").write_text(
        '# Technical report preset smoke specification\n\n'
        '```json\n' + json.dumps({"template": "templates/technical_report_template.hwpx", "out": "output_docs/technical_report_out.hwpx",
                                    "table_style": None, "keys": {}, "styles": STYLES}, ensure_ascii=False, indent=2)
        + '\n```\n\n# 개 요\n> 문서의 목적과 적용 범위를 출처에 근거하여 작성합니다.\n', encoding="utf-8")
    (output / "generation_manifest.json").write_text(json.dumps({
        "generator": "build_hwpx_template.py", "project_documents_used": False,
        "vendor_binary_or_xml_copied": False, "com_used": False,
        "packages": [{"name": kind, "source_package_sha256": hashlib.sha256((output / ("technical_report_" + kind + ".package.zip")).read_bytes()).hexdigest()}
                     for kind in ("template", "specimen")],
    }, indent=2) + "\n", encoding="utf-8")
    return names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=HERE / "generated")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--package-only", action="store_true", help="Write portable packages/XML only (default)")
    choice.add_argument("--write-hwpx", action="store_true", help="Also write .hwpx; the environment may automatically protect it")
    opts = parser.parse_args()
    print(json.dumps({"generated": build(opts.out_dir, write_hwpx=opts.write_hwpx)}, ensure_ascii=True))
