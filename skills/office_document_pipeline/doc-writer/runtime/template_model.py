"""Deterministically project a restricted HWPX template into the fake COM HWPML model.

Not an HWPX-to-HWPML document converter. Only the subset enumerated by SCOPE is
supported; no HWP/COM is invoked. Unknown document objects or unsupported numbering
semantics fail closed. Remaining layout fields are explicitly listed as unmodeled.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as E
import zipfile

N = {k: f"http://www.hancom.co.kr/hwpml/2011/{v}" for k, v in
     (("hh", "head"), ("hp", "paragraph"), ("hc", "core"), ("hs", "section"))}
LANGS = ("Hangul", "Latin", "Hanja", "Japanese", "Other", "Symbol", "User")
SCOPE = {
    "styles": ["id", "name", "engName", "type", "nextStyleIDRef", "paraPrIDRef", "charPrIDRef"],
    "paragraphs": ["id", "horizontal alignment", "heading type/id/level", "break Latin/non-Latin", "keepWithNext", "pageBreakBefore", "margins", "lineSpacing"],
    "characters": ["id", "height", "textColor", "bold", "italic", "useFontSpace", "fontRef", "ratio", "spacing", "relSz"],
    "fonts": ["language", "id", "name", "type"],
    "pages": ["width", "height", "landscape", "gutterType", "all page margins"],
    "numbering": ["header beginNum", "section startNum", "outlineShapeIDRef", "numbering id/start", "paraHead level/start/format/text"],
    "body": ["one section", "plain paragraph style/para/char references", "plain text"],
}
UNMODELED = [
    "font glyph metrics/GDI, fallback and kerning; no layout renderer",
    "text shade/underline/strikeout/shadow/character offsets and decorative borders",
    "paragraph vertical baseline/grid/autospacing/text direction details",
    "tab stop layout, section grid, columns, visibility, notes, page border fills",
    "style language/lock fields, metadata, caret, package preview and compatibility options",
    "actual HWP heading-string formatting and page rendering; fake COM supports standard decimal starts only",
]


class Unsupported(ValueError):
    pass


def el(parent, tag, **attrs):
    return E.SubElement(parent, tag, {k: str(v) for k, v in attrs.items() if v is not None})


def title(v):
    return "".join(x.capitalize() for x in v.split("_"))


def boolean(v):
    return "true" if v in ("1", "true") else "false"


def colorref(value):
    """HWPX #RRGGBB to legacy HWPML's decimal Windows COLORREF (BGR)."""
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value or ""):
        raise Unsupported("Only explicit RGB text colors are modeled")
    r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
    return str(r | (g << 8) | (b << 16))


def payload(path):
    with zipfile.ZipFile(path) as z:
        if z.read("mimetype") != b"application/hwp+zip":
            raise Unsupported("Not an HWPX logical package")
        if z.testzip():
            raise Unsupported("Invalid ZIP CRC")
        sectionpaths = [x for x in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", x)]
        if sectionpaths != ["Contents/section0.xml"]:
            raise Unsupported("Only one section is modeled")
        return E.fromstring(z.read("Contents/header.xml")), E.fromstring(z.read(sectionpaths[0]))


def convert(path):
    head, section = payload(path)
    root = E.Element("HWPML", {"Version": "2.91"})
    h = el(root, "HEAD", SecCnt=head.get("secCnt"))
    begin = head.find("hh:beginNum", N)
    if begin is None:
        raise Unsupported("Missing header beginNum")
    if any(begin.get(k) != "1" for k in ("page", "footnote", "endnote", "pic", "tbl", "equation")):
        raise Unsupported("Non-default begin numbers are not simulated")
    el(h, "BEGINNUMBER", **{title(k): v for k, v in begin.attrib.items()})
    m = el(h, "MAPPINGTABLE")
    faces = el(m, "FACENAMELIST")
    for ff in head.findall("hh:refList/hh:fontfaces/hh:fontface", N):
        f = el(faces, "FONTFACE", Lang=title(ff.get("lang")), Count=ff.get("fontCnt"))
        for font in ff:
            if font.get("isEmbedded") != "0":
                raise Unsupported("Embedded fonts are not simulated")
            el(f, "FONT", Id=font.get("id"), Name=font.get("face"), Type=font.get("type"))
    chars = el(m, "CHARSHAPELIST")
    for c in head.findall("hh:refList/hh:charProperties/hh:charPr", N):
        if c.get("shadeColor") not in (None, "none") or c.get("useKerning") not in (None, "0") or c.get("symMark") not in (None, "NONE"):
            raise Unsupported("Active shade, kerning or symbol marks are not modeled")
        for tag, attribute in (("underline", "type"), ("strikeout", "shape"), ("outline", "type"), ("shadow", "type")):
            value = c.find("hh:" + tag, N)
            if value is not None and value.get(attribute) != "NONE":
                raise Unsupported("Active character decoration is not modeled: " + tag)
        offset = c.find("hh:offset", N)
        if offset is not None and any(v != "0" for v in offset.attrib.values()):
            raise Unsupported("Character offsets are not modeled")
        out = el(chars, "CHARSHAPE", Id=c.get("id"), Height=c.get("height"), TextColor=colorref(c.get("textColor")), UseFontSpace=boolean(c.get("useFontSpace")))
        for child in ("bold", "italic"):
            if c.find("hh:" + child, N) is not None:
                el(out, child.upper())
        for source, dest in (("fontRef", "FONTID"), ("ratio", "RATIO"), ("spacing", "CHARSPACING"), ("relSz", "RELSIZE")):
            q = c.find("hh:" + source, N)
            if q is not None:
                el(out, dest, **{lang: q.get(lang.lower()) for lang in LANGS})
    paras = el(m, "PARASHAPELIST")
    for p in head.findall("hh:refList/hh:paraProperties/hh:paraPr", N):
        align, heading, br = (p.find("hh:" + q, N) for q in ("align", "heading", "breakSetting"))
        if align is None or heading is None or br is None:
            raise Unsupported("Paragraph requires alignment, heading and break settings")
        if heading.get("type") not in ("NONE", "OUTLINE"):
            raise Unsupported("Only plain and decimal outline paragraph headings are modeled")
        if heading.get("type") == "OUTLINE" and not 0 <= int(heading.get("level")) <= 6:
            raise Unsupported("Only outline levels 1 through 7 are simulated")
        out = el(paras, "PARASHAPE", Id=p.get("id"), Align=title(align.get("horizontal")), HeadingType=title(heading.get("type")),
                 Heading=heading.get("idRef"), Level=heading.get("level"), PageBreakBefore=boolean(br.get("pageBreakBefore")),
                 KeepWithNext=boolean(br.get("keepWithNext")), BreakLatinWord=title(br.get("breakLatinWord")), BreakNonLatinWord=title(br.get("breakNonLatinWord")))
        margin = p.find("hh:margin", N)
        if margin is None:
            raise Unsupported("Only direct paragraph margins are currently modeled (no hp:switch)")
        vals = {}
        for e in margin:
            if e.get("unit") != "HWPUNIT":
                raise Unsupported("Only HWPUNIT paragraph margins are modeled")
            name = e.tag.rsplit("}", 1)[-1]
            vals[{"intent": "Indent", "left": "Left", "right": "Right", "prev": "Prev", "next": "Next"}[name]] = e.get("value")
        el(out, "PARAMARGIN", **vals)
        space = p.find("hh:lineSpacing", N)
        if space is not None:
            el(out, "LINESPACING", Type=title(space.get("type")), Value=space.get("value"), Unit=space.get("unit"))
    nums = el(m, "NUMBERINGLIST")
    for n in head.findall("hh:refList/hh:numberings/hh:numbering", N):
        if n.get("start") != "0":
            raise Unsupported("Non-default numbering start is not simulated")
        number = el(nums, "NUMBERING", Id=n.get("id"), Start=n.get("start"))
        for p in n:
            lvl = int(p.get("level"))
            expected = ".".join(f"^{i}" for i in range(1, lvl + 1)) + "."
            if p.get("start") != "1" or p.get("numFormat") != "DIGIT" or p.text != expected:
                raise Unsupported("Only standard hierarchical decimal outline with level starts=1 is simulated")
            e = el(number, "PARAHEAD", Level=lvl, Start=1, NumFormat="Digit")
            e.text = p.text
    styles = el(m, "STYLELIST")
    for s in head.findall("hh:refList/hh:styles/hh:style", N):
        el(styles, "STYLE", Id=s.get("id"), Name=s.get("name"), EngName=s.get("engName"), Type=title(s.get("type")),
           NextStyle=s.get("nextStyleIDRef"), ParaShape=s.get("paraPrIDRef"), CharShape=s.get("charPrIDRef"))
    outsec = el(el(root, "BODY"), "SECTION", Id=0)
    for p in section:
        if p.tag != "{" + N["hp"] + "}p":
            raise Unsupported("Only top-level paragraphs are modeled")
        outp = el(outsec, "P", ParaShape=p.get("paraPrIDRef"), Style=p.get("styleIDRef"))
        for run in p:
            if run.tag != "{" + N["hp"] + "}run":
                raise Unsupported("Lines/layout annotations are not converted")
            out = el(outp, "TEXT", CharShape=run.get("charPrIDRef"))
            for child in run:
                tag = child.tag.rsplit("}", 1)[-1]
                if tag == "t":
                    if len(child):
                        raise Unsupported("Complex text controls are not modeled")
                    if child.text:
                        el(out, "CHAR").text = child.text
                elif tag == "secPr":
                    sec = el(out, "SECDEF", OutlineShape=child.get("outlineShapeIDRef"))
                    start = child.find("hp:startNum", N)
                    if start is None or start.get("pageStartsOn") != "BOTH" or any(start.get(k) != "0" for k in ("page", "pic", "tbl", "equation")):
                        raise Unsupported("Section numbering resets are not simulated")
                    # Preserve selected section start metadata, without inventing a NEWNUM control.
                    el(sec, "STARTNUMBER", **{title(k): v for k, v in start.attrib.items()})
                    page = child.find("hp:pagePr", N)
                    if page is None:
                        raise Unsupported("Missing page definition")
                    pd = el(sec, "PAGEDEF", Width=page.get("width"), Height=page.get("height"),
                            Landscape={"WIDELY": "0", "NARROWLY": "1"}[page.get("landscape")], GutterType=title(page.get("gutterType")))
                    pm = page.find("hp:margin", N)
                    if pm is None:
                        raise Unsupported("Missing page margins")
                    el(pd, "PAGEMARGIN", **{title(k): v for k, v in pm.attrib.items()})
                elif tag == "ctrl":
                    # The default preset is single column. This carries no numbering object.
                    cols = child.findall("hp:colPr", N)
                    if len(child) != 1 or len(cols) != 1 or cols[0].get("colCount") != "1":
                        raise Unsupported("Only single-column section controls are modeled")
                else:
                    raise Unsupported("Unsupported body object: " + tag)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + E.tostring(root, encoding="unicode")


def normalized_model(text):
    text = re.sub(r"^\ufeff?\s*<\?xml[^>]*\?>", "", text, count=1)
    root = E.fromstring(text)
    def entry(e):
        return {"tag": e.tag, "attrs": dict(sorted(e.attrib.items())),
                "text": (e.text or "") if e.tag in ("CHAR", "PARAHEAD") else (e.text or "").strip(),
                "children": [entry(c) for c in e]}
    # Compare mapping-table entities by identity, not serializer child order.
    result = {"root": root.attrib, "begin": [entry(e) for e in root.iter("BEGINNUMBER")]}
    for group in ("FONTFACE", "CHARSHAPE", "PARASHAPE", "STYLE", "NUMBERING"):
        result[group] = {e.get("Lang") if group == "FONTFACE" else e.get("Id"): entry(e) for e in root.iter(group)}
    result["BODY"] = [entry(e) for e in root.findall("BODY/SECTION")]
    return result


def compare_model(package, model):
    """Compare every projected field; format-only XML differences do not matter."""
    try:
        want = normalized_model(convert(package))
    except (OSError, Unsupported, KeyError, ValueError, E.ParseError, zipfile.BadZipFile) as exc:
        return {"passed": False, "unsupported": str(exc), "scope": SCOPE, "unmodeled": UNMODELED}
    try:
        have = normalized_model(Path(model).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, E.ParseError) as exc:
        return {"passed": False, "unsupported": "Invalid model: " + str(exc), "scope": SCOPE, "unmodeled": UNMODELED}
    differences = []
    def diff(a, b, path="HWPML"):
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() | b.keys()):
                if key not in a or key not in b:
                    differences.append({"path": path + "/" + key, "expected": a.get(key), "actual": b.get(key)})
                else:
                    diff(a[key], b[key], path + "/" + key)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                differences.append({"path": path + "/length", "expected": len(a), "actual": len(b)})
            for i, (aa, bb) in enumerate(zip(a, b)):
                diff(aa, bb, path + f"/[{i}]")
        elif a != b:
            differences.append({"path": path, "expected": a, "actual": b})
    diff(want, have)
    return {"passed": not differences, "differences": differences, "scope": SCOPE, "unmodeled": UNMODELED,
            "package_sha256": hashlib.sha256(Path(package).read_bytes()).hexdigest(),
            "model_sha256": hashlib.sha256(Path(model).read_bytes()).hexdigest()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("package", type=Path)
    p.add_argument("--out-model", type=Path)
    p.add_argument("--compare", type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    if args.out_model:
        args.out_model.parent.mkdir(parents=True, exist_ok=True)
        args.out_model.write_text(convert(args.package), encoding="utf-8")
    target = args.compare or args.out_model
    if target is None:
        p.error("Use --out-model or --compare")
    report = compare_model(args.package, target)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "differences": len(report.get("differences", [])), "report": str(args.report)}, ensure_ascii=True))
    raise SystemExit(0 if report["passed"] else 1)
