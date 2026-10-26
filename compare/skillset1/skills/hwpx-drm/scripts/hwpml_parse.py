#!/usr/bin/env python3
"""HWPML2X 문자열 → 문서 모델 (설계 rd/hwpx_drm_design.md UF-03, §6).

기준(정답지): tests/fixtures/synthetic_hwpml.md — 한/글 13.0이 만든 합성 문서의 실제 HWPML.
요소 이름은 아래 표에만 둔다(설계 §8). 모르는 요소 안의 문단도 버리지 않고 'other'로 모으고,
파싱한 P·TABLE·CELL 수를 원문 태그 수와 맞춰 본다(coverage) — 빠뜨린 내용이 있으면 드러난다.

위치 ID (같은 문서를 다시 읽으면 같은 ID):
  s0.p12            구역 0의 12번째 최상위 문단(빈 문단 포함 순번)
  s0.t3             구역 0의 3번째 최상위 표          s0.t3.r2c1      그 표의 2행 1열 셀(병합 셀은 왼쪽 위 칸)
  s0.t3.r2c1.t0     그 셀 안 첫 번째 중첩 표
  s0.hd0 s0.ft0     머리말·꼬리말        s0.fn0 s0.en0   각주·미주        s0.m0  메모
  <상위>.x0 <상위>.c0   글상자·(표 아닌 개체의) 캡션
"""
import re
import xml.etree.ElementTree as ET

# ------------------------------------------------------------------ 요소 이름 표 (픽스처·어휘에서 확인)

LIST_OWNER_KIND = {          # PARALIST 를 직접 가진 요소 → 종류
    "CELL": "cell",
    "HEADER": "header", "FOOTER": "footer",
    "FOOTNOTE": "footnote", "ENDNOTE": "endnote",
    "CAPTION": "caption", "DRAWTEXT": "textbox",
    "FIELDBEGIN": "memo",    # 실측: 메모 내용은 FIELDBEGIN(Type=Memo) > PARALIST
}
INLINE_CHARS = {"LINEBREAK": "\n", "TAB": "\t", "NBSPACE": " ", "FWSPACE": " ", "HYPEN": "-", "HYPHEN": "-"}
NOTE_NUMBER_TYPES = ("Footnote", "Endnote")
PAGE_NUMBER_TYPES = ("Page", "TotalPage")
ID_PREFIX = {"header": "hd", "footer": "ft", "footnote": "fn", "endnote": "en", "memo": "m",
             "textbox": "x", "caption": "c", "other": "o"}

_BIN = re.compile(r"<BINDATASTORAGE\b.*?</BINDATASTORAGE>", re.S)
_BAD_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
_SURR = re.compile("[\ud800-\udfff]")
_WSTR = re.compile(r"(\w+):wstring:(\d+):")
# 번호 글자 제목: '1 개요', '1.1 적용범위', '2.1.1.1. 미군사 규격서' (날짜 '2024. 10. 12', 목차 '…\t3', 문장 '…다.' 제외)
_NUMHEAD = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,3}){0,6})\.?[ \u3000]+([^\d\s][^\t\n]{0,98})$")


class ParseError(Exception):
    code = 1


def clean(x):
    """파싱 전 정리: 그림 데이터 제거(메모리), 단독 서러게이트·XML 금지 문자 제거. (정리한 문자열, 보고)"""
    rep = {"bindata_blocks": 0, "lone_surrogates": 0, "bad_xml_chars": 0}
    if not x:
        raise ParseError("HWPML 이 비어 있다 - 내보내기 실패")
    x, rep["bindata_blocks"] = _BIN.subn("<BINDATASTORAGE/>", x)
    x, rep["lone_surrogates"] = _SURR.subn("\ufffd", x)
    x, rep["bad_xml_chars"] = _BAD_XML.subn("", x)
    return x, rep


def parse_clickhere_command(cmd):
    """'Clickhere:set:59:Direction:wstring:9:안내문 HelpState:wstring:8:메모  ' → {'Direction':..,'HelpState':..}"""
    out, i = {}, 0
    while True:
        m = _WSTR.search(cmd or "", i)
        if not m:
            return out
        n = int(m.group(2))
        out[m.group(1)] = cmd[m.end():m.end() + n]
        i = m.end() + n


def _int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


class _Parser:
    def __init__(self, root):
        self.root = root
        self.styles = {s.get("Id"): s.get("Name") for s in root.iter("STYLE")}
        self.parashapes = {p.get("Id"): (p.get("HeadingType"), _int(p.get("Level"))) for p in root.iter("PARASHAPE")}
        self.aligns = {p.get("Id"): p.get("Align") for p in root.iter("PARASHAPE")}
        self.heights = {c.get("Id"): c.get("Height") for c in root.iter("CHARSHAPE")}   # 글자 모양 → 글자 크기(P-031)
        self.ctrls = []                        # 문단 TEXT 안의 조판 개체(구역 정의·쪽 번호·머리말 등) — 위치 ID 와 속성
        self.counters = {}
        self.fields, self.headers, self.footers, self.footnotes, self.endnotes, self.memos = [], [], [], [], [], []
        self.unknown = {}
        self.n = {"P": 0, "TABLE": 0, "CELL": 0, "PARALIST": 0, "empty_para": 0, "grid_bad": 0}

    def next_id(self, prefix, kind):
        key = (prefix, kind)
        k = self.counters.get(key, 0)
        self.counters[key] = k + 1
        return "%s.%s%d" % (prefix, kind, k)

    # -------------------------------------------------------------- 목록(PARALIST/SECTION) → 블록들

    def parse_list(self, container, prefix, anchor=None, sec=None):
        """container 의 직계 P 들을 블록 목록으로. anchor: 각주·메모가 가리킬 위치 ID(없으면 문단 ID)."""
        if container is None:
            return []
        if container.tag == "PARALIST":
            self.n["PARALIST"] += 1
        blocks = []
        open_fields = []                       # 문단을 넘는 필드 대비 - 목록 단위 스택
        for i, p in enumerate(container.findall("P")):
            pid = "%s.p%d" % (prefix, i)
            blocks += self.parse_para(p, pid, prefix, anchor or pid, sec, open_fields)
        return blocks

    def parse_para(self, p, pid, prefix, anchor, sec, open_fields):
        self.n["P"] += 1
        parts, inline = [], []
        marks = []                             # 글자가 아닌 개체의 자리 [글자 위치, 태그] - 캐럿 편집이 피해 갈 곳 (P-025)

        def cur():
            return "".join(parts)

        for t in p.findall("TEXT"):
            for el in t:
                tag = el.tag
                if tag == "CHAR":                  # 글자 + 줄바꿈·탭 같은 글자 요소. 그 밖의 하위 요소(제목 차례 표시 등)는 marks 로
                    parts.append(el.text or "")
                    for ch in el:
                        if ch.tag in INLINE_CHARS:
                            parts.append(INLINE_CHARS[ch.tag])
                        else:
                            marks.append([len(cur()), ch.tag])
                        parts.append(ch.tail or "")
                    continue
                if tag in INLINE_CHARS:
                    parts.append(INLINE_CHARS[tag])
                    continue
                marks.append([len(cur()), tag])
                if tag == "AUTONUM":
                    if el.get("NumberType") not in NOTE_NUMBER_TYPES:
                        parts.append(el.get("Number") or "")
                elif tag == "FIELDBEGIN":
                    rec = {"type": el.get("Type") or "", "name": el.get("Name"), "start": len(cur()), "el": el,
                           "at": anchor}                 # 위치는 필드가 시작한 곳 (여러 문단 필드도 같은 ID)
                    if el.find("PARALIST") is not None:            # 메모 - 내용은 따로, 본문 글자에 넣지 않는다
                        rec["memo_id"] = self.next_id(sec, "m")
                        rec["memo_text"] = flatten(self.parse_list(el.find("PARALIST"), rec["memo_id"], sec=sec))
                    open_fields.append(rec)
                elif tag == "FIELDEND":
                    self.close_field(el.get("Type") or "", open_fields, cur(), anchor)
                elif tag == "TABLE":
                    inline.append(self.parse_table(el, self.next_id(prefix, "t"), sec))
                else:
                    rec = {"at": pid, "tag": tag, "attrs": dict(el.attrib), "offset": len(cur()),
                           "children": {c.tag: dict(c.attrib) for c in el if c.tag != "PARALIST"}}
                    self.ctrls.append(rec)
                    made = self.parse_control(el, prefix, anchor, sec)
                    if made:
                        rec["blocks"] = [x["id"] for x in made]          # 이 개체가 만든 블록(캡션·글상자 등)
                    inline += made
        text = cur()
        heights = set()                        # 글자가 있는 TEXT 의 글자 크기(HWPUNIT) — 본문 글자 크기 맞추기 확인(P-031)
        for t in p.findall("TEXT"):
            if "".join("".join(c.itertext()) for c in t.findall("CHAR")).strip() and self.heights.get(t.get("CharShape")):
                heights.add(self.heights[t.get("CharShape")])
        for f in open_fields:                  # 이 문단에서 안 닫힌 필드: 다음 문단 글자 위치는 새로 센다
            f["carry"] = f.get("carry", "") + text[f["start"]:] + "\n"
            f["start"] = 0
        out = []
        if text.strip():
            heading, level = self.parashapes.get(p.get("ParaShape"), (None, 0))
            b = {"id": pid, "type": "para", "text": text, "style": self.styles.get(p.get("Style")),
                 "align": self.aligns.get(p.get("ParaShape"))}
            if marks:
                b["marks"] = marks
            if heights:
                b["heights"] = sorted(heights, key=_int)
            if heading == "Outline":
                b["level"] = level + 1
                b["level_src"] = "outline"
            out.append(b)
        elif not inline:
            self.n["empty_para"] += 1
        return out + inline

    def close_field(self, ftype, open_fields, text, anchor):
        idx = next((i for i in range(len(open_fields) - 1, -1, -1) if open_fields[i]["type"] == ftype), None)
        if idx is None:
            return
        f = open_fields.pop(idx)
        value = f.get("carry", "") + text[f["start"]:]
        el = f["el"]
        anchor = f.get("at", anchor)
        if f["type"] == "Memo":
            self.memos.append({"id": f["memo_id"], "at": anchor, "anchor_text": value, "text": f["memo_text"]})
            return
        rec = {"name": f["name"], "kind": f["type"].lower() or "field", "at": anchor, "value": value}
        if f["type"] == "Clickhere":
            c = parse_clickhere_command(el.get("Command"))
            rec["guide"], rec["help"] = c.get("Direction", ""), c.get("HelpState", "")
        elif f["type"] == "Formula":
            rec["command"] = el.get("Command")
        self.fields.append(rec)

    # -------------------------------------------------------------- 개체(표 아닌 것)

    def find_lists(self, el, skip=()):
        """el 아래에서 가장 가까운 PARALIST 들 → (주인 요소, PARALIST). 중첩 PARALIST 는 재귀 파싱이 맡는다."""
        for ch in el:
            if ch.tag in skip:
                continue
            if ch.tag == "PARALIST":
                yield el, ch
            elif ch.tag == "TABLE":
                continue                       # 개체 안 표는 parse_control 이 따로 처리
            else:
                yield from self.find_lists(ch, skip)

    def parse_control(self, el, prefix, anchor, sec):
        blocks = []
        for owner, plist in self.find_lists(el):
            kind = LIST_OWNER_KIND.get(owner.tag, "other")
            if kind in ("header", "footer", "footnote", "endnote"):
                nid = self.next_id(sec, ID_PREFIX[kind])
                rec = {"id": nid, "at": anchor, "text": flatten(self.parse_list(plist, nid, sec=sec)).strip()}
                if kind in ("header", "footer"):
                    rec["apply"] = owner.get("ApplyPageType")
                    del rec["at"]
                    if any(a.get("NumberType") in PAGE_NUMBER_TYPES for a in plist.iter("AUTONUM")):
                        rec["page_number"] = True          # 쪽 번호 필드가 든 머리말·꼬리말 (P-025 본문 앞 쪽 번호 검사)
                else:
                    num = next((a.get("Number") for a in plist.iter("AUTONUM")
                                if a.get("NumberType") in NOTE_NUMBER_TYPES), None)
                    rec["number"] = _int(num, None)
                {"header": self.headers, "footer": self.footers,
                 "footnote": self.footnotes, "endnote": self.endnotes}[kind].append(rec)
            else:
                if kind == "other":
                    self.unknown[owner.tag] = self.unknown.get(owner.tag, 0) + 1
                nid = self.next_id(prefix, ID_PREFIX.get(kind, "o"))
                inner = self.parse_list(plist, nid, anchor=anchor, sec=sec)
                b = {"id": nid, "type": kind, "owner": el.tag,       # 글자에는 표를 넣지 않는다 - 표는 따로(이중 계상 방지)
                     "text": flatten([x for x in inner if x["type"] != "table"])}
                tables = [x for x in inner if x["type"] == "table"]
                if tables:
                    b["tables"] = tables
                blocks.append(b)
        for t in self.find_tables(el):         # 개체 안이지만 PARALIST 밖에 있는 표 - 드묾
            blocks.append(self.parse_table(t, self.next_id(prefix, "t"), sec))
        return blocks

    def find_tables(self, el):
        for ch in el:
            if ch.tag == "TABLE":
                yield ch
            elif ch.tag != "PARALIST":
                yield from self.find_tables(ch)

    # -------------------------------------------------------------- 표

    def parse_table(self, tbl, tid, sec):
        self.n["TABLE"] += 1
        rows, cols = _int(tbl.get("RowCount")), _int(tbl.get("ColCount"))
        t = {"id": tid, "type": "table", "rows": rows, "cols": cols, "caption": None, "cells": []}
        caps = [flatten(self.parse_list(pl, tid + ".cap", sec=sec)) for o, pl in self.find_lists(tbl, skip=("ROW",))
                if o.tag == "CAPTION"]
        if caps:
            t["caption"] = "\n".join(caps)
        for row in tbl.findall("ROW"):
            for cell in row.findall("CELL"):
                self.n["CELL"] += 1
                r, c = _int(cell.get("RowAddr")), _int(cell.get("ColAddr"))
                cid = "%s.r%dc%d" % (tid, r, c)
                inner = self.parse_list(cell.find("PARALIST"), cid, anchor=cid, sec=sec)
                nested = [b for b in inner if b["type"] == "table"]
                own = [b for b in inner if b["type"] != "table"]   # 셀 글자 = 셀 자신의 문단만 (중첩 표 글자는 표 쪽에)
                cd = {"id": cid, "row": r, "col": c, "rowspan": _int(cell.get("RowSpan"), 1),
                      "colspan": _int(cell.get("ColSpan"), 1), "text": flatten(own)}
                if cell.get("Header") == "true":
                    cd["header"] = True
                if cell.get("Name"):
                    cd["field"] = cell.get("Name")
                    self.fields.append({"name": cell.get("Name"), "kind": "cell", "at": cid, "value": flatten(own)})
                if nested:
                    cd["tables"] = nested
                t["cells"].append(cd)
        t["grid_ok"], t["grid_note"] = grid_check(t)
        if not t["grid_ok"]:
            self.n["grid_bad"] += 1
        return t

    # -------------------------------------------------------------- 문서

    def model(self):
        root = self.root
        body, sections = [], root.find("BODY")
        secs = sections.findall("SECTION") if sections is not None else []
        for si, sec in enumerate(secs):
            prefix = "s%d" % si
            body += self.parse_list(sec, prefix, sec=prefix)
        heading_src, headings = numbered_headings(body)
        raw = {tag: sum(1 for _ in root.iter(tag)) for tag in ("P", "TABLE", "CELL", "PARALIST")}
        coverage = {tag: (self.n[tag], raw[tag]) for tag in raw if self.n[tag] != raw[tag]}
        summary = root.find("HEAD/DOCSUMMARY")
        meta = {}
        if summary is not None:
            for k in ("TITLE", "SUBJECT", "AUTHOR", "DATE", "KEYWORDS"):
                e = summary.find(k)
                if e is not None and (e.text or "").strip():
                    meta[k.lower()] = e.text.strip()
        kinds = {}
        for f in self.fields:
            kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
        stats = {"sections": len(secs), "section_paras": [len(sec.findall("P")) for sec in secs],
                 "p_elements": self.n["P"], "tables": self.n["TABLE"], "cells": self.n["CELL"],
                 "empty_paragraphs": self.n["empty_para"], "grid_bad_tables": self.n["grid_bad"],
                 "headers": len(self.headers), "footers": len(self.footers), "footnotes": len(self.footnotes),
                 "endnotes": len(self.endnotes), "memos": len(self.memos), "fields": kinds,
                 "textboxes": sum(1 for _ in iter_blocks(body) if _["type"] == "textbox"),
                 "headings": headings, "heading_source": heading_src,
                 "unknown_list_owners": self.unknown}
        stats["bindata_items"] = sum(1 for _ in root.iter("BINITEM"))
        return {"hwpml_version": root.get("Version"), "meta": meta, "stats": stats, "coverage_mismatch": coverage,
                "fields": self.fields, "body": body, "headers": self.headers, "footers": self.footers,
                "footnotes": self.footnotes, "endnotes": self.endnotes, "memos": self.memos,
                "ctrls": self.ctrls, "styledefs": style_defs(root), "numberings": numberings(root),
                "roots": [{"id": "s%d.p%d" % (si, pi), "kind": root_kind(p)}
                          for si, sec in enumerate(secs) for pi, p in enumerate(sec.findall("P"))]}


LAYOUT_CTRLS = ("SECDEF", "COLDEF", "PAGENUM", "NEWNUM", "PAGEHIDING", "HEADER", "FOOTER", "BOOKMARK", "FIELDBEGIN",
                "FIELDEND", "FOOTNOTE", "ENDNOTE")


def root_kind(p):
    """최상위 문단 하나의 종류 — text(글자) / table(표만) / object(그림 등 개체만) / empty(빈 문단, 구역 정의·머리말 같은
    조판 개체만 있어도 빈 문단). 작성기가 쓴 뒤 문단 배치를 맞춰 볼 때 쓴다(P-029)."""
    text = table = obj = False
    for t in p.findall("TEXT"):
        for el in t:
            if el.tag == "CHAR":
                s = (el.text or "") + "".join(INLINE_CHARS.get(c.tag, "") + (c.tail or "") for c in el)
                text = text or bool(s.strip())
            elif el.tag == "AUTONUM":
                text = True
            elif el.tag == "TABLE":
                table = True
            elif el.tag not in INLINE_CHARS and el.tag not in LAYOUT_CTRLS:
                obj = True
    return "text" if text else "table" if table else "object" if obj else "empty"


# ------------------------------------------------------------------ 공개 함수

def parse(x):
    """HWPML2X 문자열(선언 교체 전후 무관) → 문서 모델 dict."""
    x, rep = clean(x)
    x = re.sub("^\ufeff?\\s*<\\?xml[^>]*\\?>", "", x, count=1)
    try:
        root = ET.fromstring(x)
    except ET.ParseError as e:
        raise ParseError("HWPML 파싱 실패: %s" % e)
    if root.tag != "HWPML":
        raise ParseError("HWPML 문서가 아니다: <%s>" % root.tag)
    m = _Parser(root).model()
    m["cleaning"] = rep
    return m


LANGS = (("Hangul", "hangul"), ("Latin", "latin"), ("Hanja", "hanja"), ("Japanese", "japanese"), ("Other", "other"),
         ("Symbol", "symbol"), ("User", "user"))          # 글자 모양 언어 7가지 — HWPML 속성 이름 → 키


def style_defs(root):
    """스타일 정의 — 이름별 문단 모양(정렬·개요 수준·여백)과 글자 모양(크기·굵게·글꼴). 본문 글자는 없다.
    글자 모양의 언어별 값(P-045): langs = {언어 키: {"font": 글꼴 이름, "type": 글꼴 종류(ttf·hft), "ratio": 장평,
    "spacing": 자간, "relsize": 상대 크기}} — 한/글은 글자를 그 글자 언어의 글꼴·값으로 그린다(칸 너비 재기, F-152)."""
    fonts, types = {}, {}
    for ff in root.iter("FONTFACE"):
        fonts[ff.get("Lang")] = {f.get("Id"): f.get("Name") for f in ff.findall("FONT")}
        types[ff.get("Lang")] = {f.get("Id"): f.get("Type") for f in ff.findall("FONT")}
    chars = {}
    for c in root.iter("CHARSHAPE"):
        d = {"height": c.get("Height"), "color": c.get("TextColor"), "bold": c.find("BOLD") is not None,
             "italic": c.find("ITALIC") is not None,
             "font_space": c.get("UseFontSpace") == "true"}          # '글꼴에 어울리는 빈칸' — 끄면 빈칸 폭이 고정(P-041)
        fid = c.find("FONTID")
        if fid is not None:
            d["hangul"] = fonts.get("Hangul", {}).get(fid.get("Hangul"))
            d["latin"] = fonts.get("Latin", {}).get(fid.get("Latin"))
        for tag, key in (("RATIO", "ratio"), ("CHARSPACING", "spacing")):
            e = c.find(tag)
            if e is not None:
                d[key] = e.get("Hangul")
        langs = {}
        for lang, k in LANGS:
            v = {}
            if fid is not None and fid.get(lang) is not None:
                v["font"] = fonts.get(lang, {}).get(fid.get(lang))
                v["type"] = types.get(lang, {}).get(fid.get(lang))
            for tag, key in (("RATIO", "ratio"), ("CHARSPACING", "spacing"), ("RELSIZE", "relsize")):
                e = c.find(tag)
                if e is not None and e.get(lang) is not None:
                    v[key] = e.get(lang)
            if v:
                langs[k] = v
        if langs:
            d["langs"] = langs
        chars[c.get("Id")] = d
    paras = {}
    for p in root.iter("PARASHAPE"):
        d = {k: p.get(k) for k in ("Align", "HeadingType", "Heading", "Level", "PageBreakBefore", "KeepWithNext",
                                   "BreakLatinWord", "BreakNonLatinWord") if p.get(k)}    # 줄 나눔 기준(P-041 칸 너비)
        m = p.find("PARAMARGIN")
        if m is not None:
            d.update({"m_" + k: v for k, v in m.attrib.items()})
        paras[p.get("Id")] = d
    return [{"id": s.get("Id"), "name": s.get("Name"), "eng": s.get("EngName"), "type": s.get("Type"),
             "next": s.get("NextStyle"), "para": paras.get(s.get("ParaShape"), {}), "char": chars.get(s.get("CharShape"), {})}
            for s in root.iter("STYLE")]


def numberings(root):
    """번호 모양(개요 번호 포함) — {Id: [{level, numformat, text(서식 문자열), start}]}."""
    return {n.get("Id"): [{"level": h.get("Level"), "numformat": h.get("NumFormat"), "text": (h.text or ""),
                           "start": h.get("Start")} for h in n.findall("PARAHEAD")] for n in root.iter("NUMBERING")}


def grid_check(t):
    """병합 셀까지 포함해 셀들이 행×열 격자를 겹침 없이 정확히 덮는지 (REQ-002)."""
    rows, cols = t["rows"], t["cols"]
    if rows <= 0 or cols <= 0:
        return False, "행·열 수 없음"
    grid = [[None] * cols for _ in range(rows)]
    for c in t["cells"]:
        for r in range(c["row"], c["row"] + c["rowspan"]):
            for k in range(c["col"], c["col"] + c["colspan"]):
                if r >= rows or k >= cols:
                    return False, "%s 가 격자 밖(%d,%d)" % (c["id"], r, k)
                if grid[r][k] is not None:
                    return False, "(%d,%d) 겹침: %s, %s" % (r, k, grid[r][k], c["id"])
                grid[r][k] = c["id"]
    holes = [(r, k) for r in range(rows) for k in range(cols) if grid[r][k] is None]
    if holes:
        return False, "빈 칸 %d개, 첫 칸 %s" % (len(holes), holes[0])
    return True, ""


def flatten(blocks, sep="\n"):
    """블록 목록 → 평문. 표는 행마다 ' | ' 로 셀을 잇고, 셀 안 중첩 표는 그 행 다음 줄에 이어 쓴다."""
    out = []
    for b in blocks:
        if b["type"] == "table":
            for r in sorted({c["row"] for c in b["cells"]}):
                row = [c for c in b["cells"] if c["row"] == r]
                out.append(" | ".join(c["text"].replace("\n", " ") for c in row))
                for c in row:
                    for n in c.get("tables", []):
                        out.append(flatten([n], sep))
        else:
            out.append(b.get("text", ""))
            for n in b.get("tables", []):
                out.append(flatten([n], sep))
    return sep.join(x for x in out if x != "" or len(out) == 1)


def iter_blocks(blocks):
    """본문 블록을 중첩(셀 안 표, 글상자 안 표)까지 차례로."""
    for b in blocks:
        yield b
        if b["type"] == "table":
            for c in b["cells"]:
                yield from iter_blocks(c.get("tables", []))
        else:
            yield from iter_blocks(b.get("tables", []))


def iter_locations(model):
    """글자가 있는 모든 위치 → (위치 ID, 종류, 글자). 검색·바꾸기 건수의 기준."""
    for b in iter_blocks(model["body"]):
        if b["type"] == "table":
            if b.get("caption"):
                yield b["id"] + ".cap", "caption", b["caption"]
            for c in b["cells"]:
                yield c["id"], "cell", c["text"]
        else:
            yield b["id"], b["type"], b.get("text", "")
    for kind in ("headers", "footers", "footnotes", "endnotes"):
        for r in model[kind]:
            yield r["id"], kind[:-1], r["text"]
    for m in model["memos"]:
        yield m["id"], "memo", m["text"]


def top_tables(model):
    """표 셀 밖에 있는 표 (본문 최상위 + 글상자·캡션 등 개체 안). 셀 안 중첩 표는 바깥 표가 함께 그린다."""
    for b in model["body"]:
        if b["type"] == "table":
            yield b
        else:
            for t in b.get("tables", []):
                yield t


def find_table(model, tid):
    for b in iter_blocks(model["body"]):
        if b["type"] == "table" and b["id"] == tid:
            return b
    return None


def numbered_headings(body):
    """제목 수준의 출처를 정한다. 문단 모양이 '개요'인 문단이 하나라도 있으면 그것만 쓴다(출처 outline).
    하나도 없으면(실측: SDP·시험평가 계획서) 번호 글자로 시작하는 짧은 최상위 문단을 제목으로 본다(출처 number,
    수준 = 번호 마디 수). 자동 개요 번호는 계산하지 않는다 - 실측에서 목차와 어긋나는 문서가 많다(P-017)."""
    paras = [b for b in body if b["type"] == "para"]
    n = sum(1 for b in paras if b.get("level"))
    if n:
        return "outline", n
    for b in paras:
        m = _NUMHEAD.match(b["text"])
        if not m or b["text"].rstrip().endswith("다."):
            continue
        b["level"] = m.group(1).count(".") + 1
        b["level_src"] = "number"
        n += 1
    return ("number" if n else None), n


def outline(model):
    return [b for b in model["body"] if b["type"] == "para" and b.get("level")]
