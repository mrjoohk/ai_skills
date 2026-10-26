#!/usr/bin/env python3
"""표 서식 — 참고 문서 표의 테두리·배경·제목 셀·안 여백·칸 너비·칸 스타일을 서식 파일(JSON)로 두고, 작성기가 표를 만들 때
입힌다(P-040, D-042). 이 파일은 한/글 없이 시험할 수 있는 부분 — HWPML 풀이, 서식 파일 만들기, 칸 서식 계산, 쓴 뒤 대조.
한/글 동작은 write_doc.py 가 부른다 — 칸 너비는 표를 만들 때(TableCreate ColWidth), 칸마다 테두리/배경(CellBorderFill)·
제목 셀(TablePropertyDialog, 셀 블록)은 글자를 쓴 뒤, 안 여백은 마지막 칸 뒤(PoC P-038 A1~A3 실측 차례, U-25·U-26).
칸 너비(P-041, D-044): 칸 글자 폭 + 공백 2칸 여유 + 칸 안 여백 — 본문 폭을 넘으면 긴 칸만 같은 너비로 줄여 줄바꿈
(짧은 칸은 그대로, 줄 나눔 기준으로 끊을 수 없는 낱말 너비 아래로는 줄이지 않음 — fit_columns), 이어 칸 줄 수 어림으로
어느 줄(행)도 높아지지 않게 줄바꿈 칸끼리 너비를 다시 나눠 표 높이를 줄인다(refine_lines). fit_table 이 둘을 부른다.
글자 폭은 Windows 에서 템플릿 스타일 글꼴로 잰다(GdiMeasure — GDI), 못 재면 글자 종류로 어림(em_estimate).
글자마다 한/글이 그 글자를 그리는 언어(한글·라틴·한자·일어·외국어·기호·사용자)의 글꼴·장평·자간·상대 크기로 잰다 —
어느 언어로 그리는지 정해지지 않은 기호 등은 후보 언어 중 가장 넓은 값(P-045, char_langs).

    python tools\\doc-writer\\table_style.py from-poc <PoC 보고.md> <서식.json> --source <참고 문서>
                                             [--alias 우리 캡션=참고 캡션 ...] [--default 참고 캡션]

서식 파일: {"source", "default": 참고 캡션, "alias": {우리 캡션: 참고 캡션}, "tables": {참고 캡션: 표 서식}}
  표 서식 = {"ref_id", "size": [줄, 칸], "cells": [[칸 서식]] | null(병합 칸이 있으면), "classes": 자리별 선, "fills"/"styles": 자리별,
             "header_cells": bool, "inside_margin": [왼, 오, 위, 아래](HWPUNIT), "col_ratio": [칸 너비 비율], "width_mm"}
  칸 서식 = {"L"/"R"/"T"/"B": [선 종류, 굵기] | null, "fill": [R, G, B] | null, "style": 스타일 이름, "header": bool}
고르기(plan_table): 우리 표 캡션 → alias → 참고 캡션이 서식 파일에 있으면 그 표, 없으면 default.
  칸 서식: 줄·칸 수가 참고 표와 같으면 칸마다 그대로(exact), 다르면 자리(바깥 위·아래·왼쪽·오른쪽, 첫 줄 아래, 안 가로·세로 /
  첫 줄 첫 칸·첫 줄·첫 칸·나머지)별(class). default 로 고른 표의 본문 칸 스타일은 칸 글자 길이로 — 짧으면 본문중앙, 길면 본문혼합.
  자리별에서 명세 표에 제목 줄이 없으면(header=False) 첫 줄도 본문 줄.
  이웃 칸이 함께 쓰는 변은 한 값으로(더 굵은 선 — shared_edges): 한/글은 나중에 입힌 칸 값으로 그 변을 덮는다(P-045).
  칸 너비는 계획에 넣지 않는다 — 작성기가 칸 스타일 글자 모양으로 fit_table 을 부른다. 표 너비 상한은 템플릿 쪽 설정으로 셈
  (default_table_width — '단에 맞춤'과 같은 값).
  안 여백 위·아래는 참고 표 값 대신 칸 글자 크기의 절반(CELL_PAD_EM — 사용자 지시 P-048, 모든 표): 작성기가 템플릿 칸 스타일
  글자 크기로 pad_margin 을 부른다. 왼·오는 참고 표 값(서식 계획이 없는 표는 한/글 기본 510·510).
"""
import argparse
import json
import math
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "backends" / "hwp" / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "hwpx-drm" / "scripts"))
import hwpml_parse as hp        # noqa: E402
import template_profiles as profiles

HU_PER_MM = 7200 / 25.4                       # HWPUNIT = 1/7200 인치
SIDES = (("L", "LEFTBORDER", "Left"), ("R", "RIGHTBORDER", "Right"), ("T", "TOPBORDER", "Top"),
         ("B", "BOTTOMBORDER", "Bottom"))
NO_FILL = "없음"
_PRESET = profiles.load_profile(root=ROOT)
HEAD = _PRESET["styles"]["th"]
_TABLE_PRESET = json.loads((Path(_PRESET["_path"]).parent / _PRESET["table_style"]).read_text(encoding="utf-8"))
CENTER, MIXED = (_TABLE_PRESET["body_styles"][k] for k in ("center", "mixed"))
LONG_TEXT = 30                                # 표시 폭(한글 2·그 밖 1)이 이보다 긴 글자가 있는 칸 → 본문혼합(양쪽 정렬)
WIDTH_TOL = 0.02                              # 칸 너비 대조 허용(비율)


# ------------------------------------------------------------------ HWPML → 표 서식 (PoC P-038 에서 옮김)

def _color(v):
    """한/글 색(0x00BBGGRR) → 'rgb(r,g,b)'. 맨 윗 바이트가 있으면(투명·자동 등) 16진 그대로."""
    if v in (None, ""):
        return None
    c = int(v)
    if c >> 24:
        return "0x%08X" % c
    return "rgb(%d,%d,%d)" % (c & 255, (c >> 8) & 255, (c >> 16) & 255)


def _line(el):
    if el is None:
        return "-"
    t = el.get("Type") or "?"
    if t == "None":
        return "없음"
    s = "%s %s" % (t, el.get("Width") or "?")
    c = _color(el.get("Color"))
    return s + (" " + c if c and c != "rgb(0,0,0)" else "")


def _fill(bf):
    fb = bf.find("FILLBRUSH")
    if fb is None:
        return NO_FILL
    wb = fb.find("WINDOWBRUSH")
    if wb is not None:
        face = _color(wb.get("FaceColor"))
        hatch = wb.get("HatchStyle")
        if face == "0xFFFFFFFF" and hatch in (None, "-1"):
            return NO_FILL                                   # 색 없음(투명)
        return "%s%s" % (face, " 무늬 %s" % hatch if hatch not in (None, "-1") else "")
    if fb.find("GRADATION") is not None:
        return "그러데이션"
    if fb.find("IMAGEBRUSH") is not None:
        return "그림"
    return "?"


def border_fills(root):
    """BORDERFILL Id → {"L","R","T","B": 선, "fill": 배경[, "diag": 대각선]}."""
    out = {}
    for bf in root.iter("BORDERFILL"):
        d = {k: _line(bf.find(tag)) for k, tag, _ in SIDES}
        d["fill"] = _fill(bf)
        diag = [n for n in ("Slash", "BackSlash", "CrookedSlash", "CounterSlash", "CounterBackSlash", "CenterLine")
                if bf.get(n) not in (None, "0")]
        if diag:
            d["diag"] = diag
        out[bf.get("Id")] = d
    return out


def shapes(root):
    para = {p.get("Id"): p.get("Align") for p in root.iter("PARASHAPE")}
    char = {c.get("Id"): {"h": c.get("Height"), "bold": c.find("BOLD") is not None, "color": _color(c.get("TextColor"))}
            for c in root.iter("CHARSHAPE")}
    style = {s.get("Id"): s.get("Name") for s in root.iter("STYLE")}
    return para, char, style


class _Rec(hp._Parser):
    """hwpml_parse 와 같은 위치 ID(s2.t3 …)로 표 요소를 함께 모은다 — 검사 보고(inspect)·작성기 모델과 같은 ID."""
    def parse_table(self, tbl, tid, sec):
        i = len(self.elems)                                      # 바깥 표가 셀 안 표보다 먼저(문서 차례)
        self.elems.append(None)
        t = super().parse_table(tbl, tid, sec)
        self.elems[i] = (tid, tbl, t)
        return t


def load(x):
    """HWPML2X 문자열 → (뿌리 요소, 문서 모델, [(표 ID, 표 요소, 표 모델)] — 문서 차례)."""
    x, _ = hp.clean(x)
    x = re.sub("^﻿?\\s*<\\?xml[^>]*\\?>", "", x, count=1)
    root = ET.fromstring(x)
    p = _Rec(root)
    p.elems = []
    return root, p.model(), p.elems


def _mm(v):
    try:
        return round(int(v) / HU_PER_MM, 1)
    except (TypeError, ValueError):
        return None


def _margins(el):
    return None if el is None else "/".join(el.get(k, "?") for k in ("Left", "Right", "Top", "Bottom"))


def _short(t, n=20):
    t = " ".join((t or "").split())
    return t[:n] + ("…" if len(t) > n else "")


def table_info(tid, tbl, t, bfs, para, char, style):
    so = tbl.find("SHAPEOBJECT")
    size = so.find("SIZE") if so is not None else None
    pos = so.find("POSITION") if so is not None else None
    g = lambda el, k: el.get(k) if el is not None else None     # noqa: E731
    info = {"id": tid, "size": [t["rows"], t["cols"]], "caption": _short(t.get("caption"), 30),
            "head": [_short(c["text"]) for c in t["cells"] if c["row"] == 0],
            "table": {"BorderFill": tbl.get("BorderFill"), "border": bfs.get(tbl.get("BorderFill")),
                      "PageBreak": tbl.get("PageBreak"), "RepeatHeader": tbl.get("RepeatHeader"),
                      "CellSpacing": tbl.get("CellSpacing"), "TextWrap": g(so, "TextWrap"),
                      "TreatAsChar": g(pos, "TreatAsChar"), "HorzRelTo": g(pos, "HorzRelTo"),
                      "HorzAlign": g(pos, "HorzAlign"), "HorzOffset": g(pos, "HorzOffset"),
                      "width_mm": _mm(g(size, "Width")), "WidthRelTo": g(size, "WidthRelTo"),
                      "outside_margin": _margins(so.find("OUTSIDEMARGIN") if so is not None else None),
                      "inside_margin": _margins(tbl.find("INSIDEMARGIN"))},
            "cells": []}
    for row in tbl.findall("ROW"):
        for cell in row.findall("CELL"):
            pl = cell.find("PARALIST")
            p0 = pl.find("P") if pl is not None else None
            tx = p0.find("TEXT") if p0 is not None else None
            info["cells"].append({
                "at": [hp._int(cell.get("RowAddr")), hp._int(cell.get("ColAddr"))],
                "span": [hp._int(cell.get("RowSpan"), 1), hp._int(cell.get("ColSpan"), 1)],
                "w_mm": _mm(cell.get("Width")), "h_mm": _mm(cell.get("Height")),
                "bf": cell.get("BorderFill"), "header": cell.get("Header") == "true",
                "margin": _margins(cell.find("CELLMARGIN")) if cell.get("HasMargin") == "true" else None,
                "valign": g(pl, "VertAlign"),
                "style": style.get(p0.get("Style")) if p0 is not None else None,
                "align": para.get(p0.get("ParaShape")) if p0 is not None else None,
                "char": char.get(tx.get("CharShape")) if tx is not None else None})   # 칸 글자는 넣지 않는다(DRM 평문 최소화)
    info["profile"] = profile(info, bfs)
    return info


def _edges(info, bfs):
    """셀 변 → 자리(바깥 위·아래·왼쪽·오른쪽, 첫 줄 아래, 안 가로·세로)별 선 개수."""
    nr, nc = info["size"]
    out = {k: Counter() for k in ("바깥 위", "바깥 아래", "바깥 왼쪽", "바깥 오른쪽", "첫 줄 아래", "안 가로", "안 세로")}
    for c in info["cells"]:
        b = bfs.get(c["bf"]) or {}
        r0, c0 = c["at"]
        r1, c1 = r0 + c["span"][0] - 1, c0 + c["span"][1] - 1
        out["바깥 위" if r0 == 0 else ("첫 줄 아래" if r0 == 1 else "안 가로")][b.get("T")] += 1
        out["바깥 아래" if r1 == nr - 1 else ("첫 줄 아래" if r1 == 0 else "안 가로")][b.get("B")] += 1
        out["바깥 왼쪽" if c0 == 0 else "안 세로"][b.get("L")] += 1
        out["바깥 오른쪽" if c1 == nc - 1 else "안 세로"][b.get("R")] += 1
    return {k: dict(v) for k, v in out.items() if v}


def _regions(info, bfs):
    """자리(첫 줄 · 첫 칸(둘째 줄부터) · 나머지)별 배경·정렬·세로 정렬·스타일·글자·제목 셀 개수."""
    out = {}
    for c in info["cells"]:
        r0, c0 = c["at"]
        reg = "첫 줄" if r0 == 0 else ("첫 칸" if c0 == 0 else "나머지")
        d = out.setdefault(reg, {k: Counter() for k in ("fill", "align", "valign", "style", "char", "header")})
        d["fill"][(bfs.get(c["bf"]) or {}).get("fill")] += 1
        d["align"][c["align"]] += 1
        d["valign"][c["valign"]] += 1
        d["style"][c["style"]] += 1
        ch = c["char"] or {}
        d["char"]["%s%s" % (ch.get("h"), " 진하게" if ch.get("bold") else "")] += 1
        d["header"][c["header"]] += 1
    return {k: {kk: dict(vv) for kk, vv in v.items()} for k, v in out.items()}


def _top(d):
    return max(d, key=lambda k: (d[k], str(k))) if d else None


def profile(info, bfs):
    e, g = _edges(info, bfs), _regions(info, bfs)
    sig = {"바깥": sorted({_top(e[k]) for k in ("바깥 위", "바깥 아래", "바깥 왼쪽", "바깥 오른쪽") if k in e}),
           "안": sorted({_top(e[k]) for k in ("안 가로", "안 세로") if k in e}),
           "첫 줄 아래": _top(e.get("첫 줄 아래", {})),
           "첫 줄 배경": _top((g.get("첫 줄") or {}).get("fill", {})),
           "첫 칸 배경": _top((g.get("첫 칸") or {}).get("fill", {})),
           "나머지 배경": _top((g.get("나머지") or {}).get("fill", {})),
           "글자처럼": info["table"]["TreatAsChar"]}
    return {"edges": e, "regions": g, "sig": sig}


def group_profiles(infos):
    groups = {}
    for i in infos:
        k = json.dumps(i["profile"]["sig"], ensure_ascii=False, sort_keys=True)
        groups.setdefault(k, []).append(i["id"])
    return [{"sig": json.loads(k), "tables": v} for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))]


def formats(x):
    root, _, elems = load(x)
    bfs = border_fills(root)
    para, char, style = shapes(root)
    infos = [table_info(tid, tbl, t, bfs, para, char, style) for tid, tbl, t in elems]
    used = {c["bf"] for i in infos for c in i["cells"]} | {i["table"]["BorderFill"] for i in infos}
    return {"tables": infos, "groups": group_profiles(infos),
            "borderfills_used": {k: bfs[k] for k in sorted(used, key=lambda v: hp._int(v)) if k in bfs}}


# ------------------------------------------------------------------ 참고 표 → 표 서식 (서식 파일)

def parse_line(s):
    """'Solid 0.4mm 0xFF000000' → ['Solid', '0.4mm'] (색은 버린다 — 참고본의 0xFF000000 은 자동(검정)), '없음' → ['None', '0.1mm']."""
    if not s or s in ("-", "?"):
        return None
    if s == NO_FILL:
        return ["None", "0.1mm"]
    parts = s.split()
    return parts[:2] if len(parts) >= 2 else None


def parse_fill(s):
    m = re.match(r"rgb\((\d+),(\d+),(\d+)\)$", (s or "").strip())
    return [int(m.group(i)) for i in (1, 2, 3)] if m else None


def line_text(v):
    if not v:
        return None
    return NO_FILL if v[0] == "None" else "%s %s" % (v[0], v[1])


def fill_text(v):
    return "rgb(%d,%d,%d)" % tuple(v) if v else NO_FILL


def _most(ctr):
    return json.loads(max(ctr, key=lambda k: (ctr[k], k))) if ctr else None


def _region(r, c):
    return "head_first" if (r, c) == (0, 0) else "head" if r == 0 else "first" if c == 0 else "body"


def classes_of(cells):
    """칸 서식 격자 → 자리별 대표 값(가장 많은 것) — 선 7자리, 배경·스타일 4자리."""
    nr, nc = len(cells), len(cells[0])
    lines = {k: Counter() for k in ("top", "bottom", "left", "right", "inner_h", "inner_v", "head_bottom")}
    fills = {k: Counter() for k in ("head_first", "head", "first", "body")}
    styles = {k: Counter() for k in ("head_first", "head", "first", "body")}
    for r in range(nr):
        for c in range(nc):
            x = cells[r][c]
            lines["top" if r == 0 else ("head_bottom" if r == 1 else "inner_h")][json.dumps(x["T"])] += 1
            lines["bottom" if r == nr - 1 else ("head_bottom" if r == 0 else "inner_h")][json.dumps(x["B"])] += 1
            lines["left" if c == 0 else "inner_v"][json.dumps(x["L"])] += 1
            lines["right" if c == nc - 1 else "inner_v"][json.dumps(x["R"])] += 1
            reg = _region(r, c)
            fills[reg][json.dumps(x["fill"])] += 1
            styles[reg][json.dumps(x["style"])] += 1
    return ({k: _most(v) for k, v in lines.items()}, {k: _most(v) for k, v in fills.items() if v},
            {k: _most(v) for k, v in styles.items() if v})


def ref_style(info, bfs):
    """참고 표(table_info) + 풀린 BORDERFILL → 표 서식."""
    nr, nc = info["size"]
    cells = [[None] * nc for _ in range(nr)]
    widths = {}
    merged = False
    for c in info["cells"]:
        r0, c0 = c["at"]
        if c["span"] != [1, 1]:
            merged = True
        b = bfs.get(c["bf"]) or {}
        if r0 < nr and c0 < nc:
            cells[r0][c0] = {"L": parse_line(b.get("L")), "R": parse_line(b.get("R")), "T": parse_line(b.get("T")),
                             "B": parse_line(b.get("B")), "fill": parse_fill(b.get("fill")), "style": c["style"],
                             "header": bool(c["header"])}
        if c["span"][1] == 1 and c["w_mm"]:
            widths.setdefault(c0, Counter())[c["w_mm"]] += 1
    grid = None if merged or any(x is None for row in cells for x in row) else cells
    lines, fills, styles = classes_of(grid) if grid else ({}, {}, {})
    cols = [_most(Counter({json.dumps(k): v for k, v in widths[i].items()})) if i in widths else None for i in range(nc)]
    total = sum(w for w in cols if w) if all(cols) else None
    im = [hp._int(v) for v in (info["table"].get("inside_margin") or "").split("/")] \
        if info["table"].get("inside_margin") else None
    return {"ref_id": info["id"], "size": [nr, nc], "cells": grid, "classes": lines, "fills": fills, "styles": styles,
            "header_cells": any(c["header"] for c in info["cells"] if c["at"][0] == 0),
            "inside_margin": im if im and len(im) == 4 else None,
            "col_ratio": [round(w / total, 4) for w in cols] if total else None, "width_mm": info["table"]["width_mm"]}


def ref_caption(caption):
    """'표 1 적용범위식별' → '적용범위식별' (캡션 앞 번호를 뗀다)."""
    return re.sub(r"^\s*표\s*\d+[.\s]*", "", caption or "").strip()


def from_poc(report_text, source, alias=None, default=None, sections=None):
    """PoC(table_style_poc.py) 보고의 T0(참고본 표 서식) → 서식 파일 dict. sections: 본문 표만(표지 표는 빼기)."""
    j = json.loads(report_text.split("```json", 1)[1].rsplit("```", 1)[0])
    t0 = j["T0"]
    bfs = t0["borderfills_used"]
    tables = {}
    for info in t0["tables"]:
        if (sections and not info["id"].startswith(tuple(sections))) or "." in info["id"][len(info["id"].split(".")[0]) + 1:]:
            continue                                     # 셀 안 표는 빼기
        cap = ref_caption(info["caption"])
        if cap:
            tables[cap] = ref_style(info, bfs)
    if default and default not in tables:
        raise ValueError("default 참고 캡션이 없다: %r (있는 것 %s)" % (default, list(tables)))
    for k, v in (alias or {}).items():
        if v not in tables:
            raise ValueError("alias %r → 참고 캡션 %r 이 없다" % (k, v))
    return {"source": source, "default": default, "alias": alias or {}, "tables": tables}


# ------------------------------------------------------------------ 우리 표 → 칸마다 서식 (작성기)

def text_width(t):
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in (t or ""))


def _fallback(d, key, *alts):
    """선: 값이 없으면(None — 참고 표에 그 자리가 없음) 다음 자리로."""
    for k in (key,) + alts:
        if d.get(k):
            return d[k]
    return None


def _fallback_key(d, key, *alts):
    """배경·스타일: 자리가 있으면 값이 None(배경 없음)이어도 그 값 — '배경 없음'을 '없는 자리'로 보지 않는다(검토 P-040 10)."""
    for k in (key,) + alts:
        if k in d:
            return d[k]
    return None


def cell_format(st, r, c, nr, nc, header=True):
    """표 서식 st 로 우리 표(nr×nc)의 칸 (r, c) 서식. 크기가 같으면 참고 칸 그대로(exact — 참고 표가 정한다), 다르면 자리별.
    자리별에서 header=False(명세 표에 제목 줄 없음)면 첫 줄도 본문 줄로 — 제목 배경·스타일·제목 셀·제목 줄 아래선을 쓰지 않는다."""
    if st.get("cells") and st["size"] == [nr, nc]:
        return dict(st["cells"][r][c])
    L, F, S = st.get("classes") or {}, st.get("fills") or {}, st.get("styles") or {}
    inner_h = _fallback(L, "inner_h", "inner_v", "head_bottom", "top")
    inner_v = _fallback(L, "inner_v", "inner_h", "head_bottom", "left")
    head_bottom = _fallback(L, "head_bottom", "inner_h", "inner_v") if header else inner_h
    reg = _region(r, c) if header else ("first" if c == 0 else "body")
    return {"T": L.get("top") if r == 0 else (head_bottom if r == 1 else inner_h),
            "B": L.get("bottom") if r == nr - 1 else (head_bottom if r == 0 else inner_h),
            "L": L.get("left") if c == 0 else inner_v,
            "R": L.get("right") if c == nc - 1 else inner_v,
            "fill": {"head_first": _fallback_key(F, "head_first", "head"), "head": F.get("head"),
                     "first": _fallback_key(F, "first", "body"), "body": F.get("body")}[reg],
            "style": {"head_first": _fallback_key(S, "head_first", "head"), "head": S.get("head"),
                      "first": _fallback_key(S, "first", "body"), "body": S.get("body")}[reg],
            "header": bool(header and st.get("header_cells")) and r == 0}


def default_table_width(x, section):
    """HWPML(템플릿) 구역 section 의 쪽 설정 → '단에 맞춤' 표 너비(HWPUNIT). 본문 폭 = 용지 너비 - 왼쪽·오른쪽 여백 -
    제본 여백(왼쪽·맞쪽 제본일 때), 표 = 본문 폭 - 2mm (실측 P-038 G1: 공통 템플릿 끝에 만든 표 43370 = 59528 - 7087 -
    7087 - 1417 - 567; pyhwpx create_table 과 같은 셈). 못 읽으면 None."""
    try:
        root, _, _ = load(x)
    except Exception:
        return None
    body = root.find("BODY")
    secs = body.findall("SECTION") if body is not None else []
    if not 0 <= section < len(secs):
        return None
    pd = secs[section].find(".//SECDEF/PAGEDEF")
    pm = pd.find("PAGEMARGIN") if pd is not None else None
    if pm is None:
        return None
    w, h = hp._int(pd.get("Width")), hp._int(pd.get("Height"))
    if pd.get("Landscape") not in (None, "0"):
        w = h
    gut = hp._int(pm.get("Gutter")) if pd.get("GutterType") in (None, "LeftOnly", "LeftRight") else 0
    v = w - hp._int(pm.get("Left")) - hp._int(pm.get("Right")) - gut - 567
    return v if 0 < v < w else None


def _key(t):
    return " ".join((t or "").split())


def _find(tables, caption):
    """캡션으로 서식 찾기 — 공백을 하나로 보고, 서식 파일 캡션이 '…'로 잘린 것(PoC 보고 30자 줄임)이면 앞부분으로(검토 P-040 11)."""
    c = _key(caption)
    for k in tables:
        if _key(k) == c:
            return k
    for k in tables:
        kk = _key(k)
        if kk.endswith("…") and len(kk) > 1 and c.startswith(kk[:-1]):
            return k
    return None


def select(style_file, caption):
    """우리 캡션 → (참고 캡션, 표 서식, default 로 골랐나)."""
    tables = style_file["tables"]
    key = _find(tables, caption)
    if key is None:
        alias = style_file.get("alias") or {}
        a = _find(alias, caption)
        key = _find(tables, alias[a]) if a is not None else None
    if key is not None:
        return key, tables[key], False
    d = style_file.get("default")
    return d, tables.get(d), True


def plan_table(style_file, caption, rows, header=True):
    """우리 표(캡션·칸 글자·제목 줄 여부) → 칸마다 서식·안 여백. 서식 파일에 고를 표가 없으면 None.
    이웃 칸이 함께 쓰는 변은 한 값으로 맞춘다(shared_edges — 계획의 "shared_edges" = 맞춘 변 수, P-045)."""
    ref, st, by_default = select(style_file, caption)
    if not st:
        return None
    nr, nc = len(rows), len(rows[0])
    cells = [[cell_format(st, r, c, nr, nc, header) for c in range(nc)] for r in range(nr)]
    body = range(1, nr) if header else range(nr)
    body_styles = style_file.get("body_styles") or {"center": CENTER, "mixed": MIXED}
    center, mixed = body_styles.get("center", CENTER), body_styles.get("mixed", MIXED)
    if by_default:                                   # 기본 서식 표: 본문 칸 스타일은 칸 글자 길이로
        for c in range(nc):
            longest = max((text_width(line) for r in body for line in (rows[r][c] or "").split("\n")), default=0)
            for r in body:
                if cells[r][c].get("style") in (center, mixed):
                    cells[r][c]["style"] = mixed if longest > LONG_TEXT else center
    exact = bool(st.get("cells")) and st["size"] == [nr, nc]
    return {"ref": ref, "ref_id": st.get("ref_id"), "mode": "exact" if exact else "class", "by_default": by_default,
            "cells": cells, "inside_margin": st.get("inside_margin"), "shared_edges": shared_edges(cells)}


def _line_key(v):
    """선 비교 값 — 보이는 선이 안 보이는 선(종류 None)보다, 굵은 선이 가는 선보다 크다."""
    try:
        w = float(str(v[1]).lower().replace("mm", ""))
    except (TypeError, ValueError, IndexError):
        w = 0.0
    return (v[0] != "None", w)


def shared_edges(cells):
    """이웃 칸이 함께 쓰는 변(위 칸 아래 = 아래 칸 위, 왼 칸 오른쪽 = 오른 칸 왼쪽)을 한 값으로 맞춘다 → 맞춘 변 수.
    한/글은 칸 테두리를 입힐 때 맞닿은 변을 이웃 칸과 함께 바꿔 나중에 입힌 칸이 이긴다(실측 P-045: 참고본 표 6·7 의
    머리 줄 아래 0.4mm 가 둘째 줄 위 0.15mm 로 덮였다, F-155). 두 값이 다르면 더 굵은 선(보이는 선이 안 보이는 선보다,
    같으면 위·왼쪽 칸 값)을 두 칸 모두에. 한쪽 값이 없으면(참고 표에 그 변이 없음) 다른 쪽 값을 두 칸에 — 값이 없는 변은
    입히지 않아 한/글 기본값으로 덮일 수 있다(검토 P-045 D1-②-04)."""
    n = 0
    for r, row in enumerate(cells):
        for c, cf in enumerate(row):
            for nb, mine, theirs in ((cells[r + 1][c] if r + 1 < len(cells) else None, "B", "T"),
                                     (row[c + 1] if c + 1 < len(row) else None, "R", "L")):
                if nb is None:
                    continue
                a, b = cf.get(mine), nb.get(theirs)
                if a == b:
                    continue
                if not a:
                    win = b
                elif not b:
                    win = a
                else:
                    win = b if _line_key(b) > _line_key(a) else a
                cf[mine] = nb[theirs] = win
                n += 1
    return n


def validate(style_file):
    """서식 파일 모양 확인 → 문제 목록(빈 목록이면 됨) — 작성기가 손대기 전에 명세 오류로 멈추게(검토 P-040 9)."""
    bad = []
    if not isinstance(style_file, dict) or not isinstance(style_file.get("tables"), dict) or not style_file["tables"]:
        return ["'tables'(참고 캡션 → 표 서식)가 없다"]
    bs = style_file.get("body_styles")
    if bs is not None and (not isinstance(bs, dict) or not all(isinstance(bs.get(k), str) and bs[k] for k in ("center", "mixed"))):
        bad.append("body_styles must define nonempty center and mixed style names")
    for k, st in style_file["tables"].items():
        if not isinstance(st, dict) or not isinstance(st.get("size"), list) or len(st["size"]) != 2:
            bad.append("표 서식 %r: size 가 없다" % k)
            continue
        cells = st.get("cells")
        if cells is not None and (len(cells) != st["size"][0] or any(len(row) != st["size"][1] for row in cells)):
            bad.append("표 서식 %r: cells 가 size 와 다르다" % k)
        im = st.get("inside_margin")
        if im is not None and (not isinstance(im, list) or len(im) != 4):
            bad.append("표 서식 %r: inside_margin 은 [왼, 오, 위, 아래]" % k)
    d = style_file.get("default")
    if d is not None and d not in style_file["tables"]:
        bad.append("default %r 가 tables 에 없다" % d)
    for a, v in (style_file.get("alias") or {}).items():
        if v not in style_file["tables"]:
            bad.append("alias %r → %r 가 tables 에 없다" % (a, v))
    return bad


def styles_used(plans):
    return sorted({c["style"] for p in plans if p for row in p["cells"] for c in row if c.get("style")})


# ------------------------------------------------------------------ 칸 너비 — 칸 글자 폭에 맞춤 (P-041, D-044)
# 사용자 지시 P-041: 표는 본문 폭을 다 채우지 않고 칸마다 글자 폭에 공백 1~2칸 정도 여유를 두며, 가운데 정렬한다(write_doc).

SLACK_SPACES = 2                    # 칸마다 여유 — 공백 2칸(지시의 '1~2칸' 위쪽: 잰 폭과 한/글 배치의 작은 차이를 덮는다)
SAFETY = {"gdi": 1.02, "estimate": 1.08}    # 글자 폭에 곱함 — 글꼴로 잼(gdi) / 글자 종류로 어림(estimate, 더 넉넉히)
EST_EM = {"hangul": 1.0, "upper": 0.70, "lower": 0.56, "digit": 0.57, "space": 0.35, "narrow": 0.30, "mid": 0.45,
          "wide": 0.85, "other": 0.60}    # 어림 글자 폭(em) — 흔한 한글 글꼴보다 조금 넉넉히
HWP_SPACE_EM = 0.5                  # 한/글 빈칸 폭 — '글꼴에 어울리는 빈칸'을 끄면(템플릿 기본) 글자 크기의 절반(실측 전, U-26)
DEFAULT_INSIDE_LR = 1020            # 표를 만들 때 칸 안 좌우 여백(510+510, 실측 G1)
CELL_PAD_EM = 0.5                   # 칸 안 여백 위·아래 = 칸 글자 크기 × 0.5 — 반 칸 여유(사용자 지시 P-048: 모든 표)
MIN_CELL = DEFAULT_INSIDE_LR + 200  # 칸 너비 하한 — ColWidth(칸 너비 - 1020)가 0 이하가 되지 않게
FLOOR_KEEP = 0.8                    # 낱말 하한을 지키느라 다른 긴 칸이 줄어드는 한도 — 하한 없이 나눈 너비(T0)의 80% 까지
LATIN_LIKE = "\u0000-\u10ff\u2000-\u206f\u20a0-\u20cf"   # 라틴 쪽 글자(U+1100 앞) + 일반 문장부호(따옴표 등)·통화 기호
LANGS = tuple(k for _, k in hp.LANGS)        # 한/글 글자 모양 언어 — 한글·라틴(영문)·한자·일어·외국어·기호·사용자
# 글자 → 한/글이 그 글자를 그리는 언어(후보, P-045 F-152). 한 언어로 정해진 범위만 적는다. 나머지(라틴 확장 기호 · × °,
# 그리스·키릴 문자, 따옴표·화살표·도형·전각 글자 등)는 한/글이 어느 언어로 그리는지 알려져 있지 않아(U-29) UNSURE 후보
# 언어마다 재어 가장 넓은 값을 쓴다 — 칸이 좁게 잡혀 줄바꿈되는 쪽을 피한다.
LANG_RANGES = ((0x0000, 0x007F, ("latin",)),                                       # ASCII — 영문·숫자·문장부호
               (0x1100, 0x11FF, ("hangul",)), (0x3130, 0x318F, ("hangul",)), (0xA960, 0xA97F, ("hangul",)),
               (0xAC00, 0xD7FF, ("hangul",)), (0xFFA0, 0xFFDC, ("hangul",)),      # 한글 음절·자모
               (0x3400, 0x4DBF, ("hanja",)), (0x4E00, 0x9FFF, ("hanja",)), (0xF900, 0xFAFF, ("hanja",)),
               (0x20000, 0x3FFFF, ("hanja",)),                                    # 한자
               (0x3040, 0x30FF, ("japanese",)), (0x31F0, 0x31FF, ("japanese",)), (0xFF66, 0xFF9F, ("japanese",)),
               (0xE000, 0xF8FF, ("user", "symbol")))                              # 사용자 영역(한컴 기호도 여기)
UNSURE = ("latin", "symbol", "other", "hangul")
DEFAULT_METRICS = {"height": 1000, "ratio": 100.0, "spacing": 0.0, "bold": False, "hangul": None, "latin": None,
                   "font_space": False, "break_hangul": False, "break_latin": False,
                   "para_lr": 0, "m_left": 0, "m_right": 0, "m_indent": 0}


def _num(v, default):
    try:
        return float(v)
    except (TypeError, ValueError, OverflowError):              # OverflowError: 손으로 적은 아주 큰 정수(검토 P-049 D1G-N01)
        return default


def _lang_metrics(c):
    """글자 모양(hwpml_parse char) → 언어별 {"face", "type", "ratio", "spacing", "relsize"} (P-045). 언어별 값이 없는 옛 꼴은
    None — text_hu 가 한글·라틴 값으로 채운다(_slots). 언어 하나의 값이 빠졌으면 그 값은 한글 값으로."""
    langs = c.get("langs")
    if not langs:
        return None
    out = {}
    for k in LANGS:
        v = dict(langs.get("hangul") or {}, **(langs.get(k) or {}))
        out[k] = {"face": v.get("font") or None, "type": v.get("type") or None,
                  "ratio": _num(v.get("ratio"), 100.0) or 100.0, "spacing": _num(v.get("spacing"), 0.0),
                  "relsize": _num(v.get("relsize"), 100.0) or 100.0}
    return out


def style_metrics(styledefs):
    """템플릿 스타일 정의(hwpml_parse styledefs) → 이름별 글자 모양 — 크기(HWPUNIT)·장평(%)·자간(%)·진하게·글꼴(한글·라틴)·
    글꼴 빈칸 여부, 줄 나눔 기준(한글 글자 단위 BreakNonLatinWord · 영어 글자 단위 BreakLatinWord=BreakWord),
    문단 여백(왼쪽·오른쪽·첫 줄, HWPUNIT)과 칸 너비에 더할 문단 좌우 여백(첫 줄 들여쓰기는 양수만).
    HWPML 에 언어별 글자 모양이 있으면 "slots": 언어별 글꼴·글꼴 종류·장평·자간·상대 크기(_lang_metrics, P-045)."""
    out = {}
    for d in styledefs or []:
        c, p = d.get("char") or {}, d.get("para") or {}
        ml, mr, mi = (int(_num(p.get(k), 0)) for k in ("m_Left", "m_Right", "m_Indent"))
        out[d.get("name")] = {
            "height": int(_num(c.get("height"), 1000)) or 1000, "ratio": _num(c.get("ratio"), 100.0) or 100.0,
            "spacing": _num(c.get("spacing"), 0.0), "bold": bool(c.get("bold")),
            "hangul": c.get("hangul") or None, "latin": c.get("latin") or None, "font_space": bool(c.get("font_space")),
            "break_hangul": p.get("BreakNonLatinWord") == "true", "break_latin": p.get("BreakLatinWord") == "BreakWord",
            "para_lr": max(0, ml) + max(0, mr) + max(0, mi), "m_left": ml, "m_right": mr, "m_indent": mi}
        slots = _lang_metrics(c)
        if slots:
            out[d.get("name")]["slots"] = slots
    return out


def pad_margin(inside_margin, cell_styles, metrics):
    """표 안 여백 [왼, 오, 위, 아래](HWPUNIT) — 왼·오는 계획 값(참고 표 서식), 없으면 한/글 기본(510·510). 위·아래는 표 칸
    스타일(cell_styles 격자의 스타일 이름) 중 가장 큰 글자 크기의 CELL_PAD_EM 배 — 칸 글자 위아래에 반 칸 여유(사용자 지시
    P-048 '셀 위아래도 0.5 칸 정도 여유': 참고 표 값 대신, 서식 계획이 없는 표도). metrics = style_metrics(템플릿)."""
    h = max(int(_num((metrics.get(n) or {}).get("height"), DEFAULT_METRICS["height"]))
            for row in cell_styles for n in row)
    pad = int(round(h * CELL_PAD_EM))
    lr = [_side(v) for v in inside_margin[:2]] if inside_margin else [DEFAULT_INSIDE_LR // 2] * 2
    return lr + [pad, pad]


def _side(v):
    """서식 파일 안 여백 왼·오 값 하나 → HWPUNIT 정수. 손으로 고친 파일의 '538.5'(버림)·null·글자·nan·inf·음수도 쓰기를 멈추지
    않게 — 못 쓰는 값은 한/글 기본 510(검토 P-049 D1-①-01·D1F-02)."""
    x = _num(v, DEFAULT_INSIDE_LR // 2)
    return int(x) if math.isfinite(x) and x >= 0 else DEFAULT_INSIDE_LR // 2


def em_estimate(ch, lang):
    """글자 하나의 폭 어림(em) — 글꼴로 못 잴 때. 라틴(영문) 언어로 그리는 글자는 종류별(조금 넉넉히), 그 밖 언어(한글·
    한자·일어·기호·외국어·사용자)로 그리는 글자는 1em — 한글 글꼴은 기호·외국 글자도 전각으로 그린다(P-045)."""
    if ch == " ":
        return EST_EM["space"]
    if lang != "latin":
        return EST_EM["hangul"]
    o = ord(ch)
    if o < 0x80:
        if ch.isdigit():
            return EST_EM["digit"]
        if ch.isupper():
            return EST_EM["upper"]
        if ch.islower():
            return EST_EM["lower"]
        if ch in ".,:;'`!|":
            return EST_EM["narrow"]
        if ch in "()[]{}-/\\\"_*":
            return EST_EM["mid"]
        return EST_EM["wide"]
    if ch == "·":
        return EST_EM["mid"]
    if o < 0x1100:
        return EST_EM["other"]
    return EST_EM["hangul"]


def char_langs(ch):
    """글자 → 한/글이 그 글자를 그리는 언어 후보(LANG_RANGES — 없으면 UNSURE)."""
    o = ord(ch)
    for a, b, langs in LANG_RANGES:
        if a <= o <= b:
            return langs
    return UNSURE


def script_runs(text):
    """글자 → [(언어 후보, 이어진 글자)] — 언어 후보(char_langs)가 같은 글자끼리. 한/글은 언어마다 글꼴·장평·자간·상대
    크기가 다르다(글자 모양의 언어별 값). 공백은 앞 글자 쪽(맨 앞이면 뒤 글자 쪽, 공백뿐이면 한글). 한글은 NFC 로 모아 센다."""
    out = []
    for ch in unicodedata.normalize("NFC", text or ""):
        k = None if ch == " " else char_langs(ch)
        if k is None or (out and out[-1][0] == k):
            if out:
                out[-1][1].append(ch)
            else:
                out.append([None, [ch]])
            continue
        if out and out[-1][0] is None:
            out[-1][0] = k
            out[-1][1].append(ch)
        else:
            out.append([k, [ch]])
    return [(k or ("hangul",), "".join(cs)) for k, cs in out]


def _measure(measure, text, face, bold):
    if not (measure and face and text):
        return None
    try:
        return measure(text, face, bold)
    except Exception:                                # 잴 수 없으면 어림(쓰기를 멈추지 않는다)
        return None


def _slots(m):
    """언어별 글자 모양 — m["slots"](style_metrics), 없으면(언어별 값이 없는 옛 꼴) 라틴은 라틴 글꼴·나머지는 한글 글꼴,
    장평·자간은 모두 한글 값, 상대 크기 100%(P-041 까지와 같은 셈)."""
    if m.get("slots"):
        return m["slots"]
    base = {"face": m.get("hangul"), "ratio": m["ratio"], "spacing": m["spacing"], "relsize": 100.0}
    return {k: dict(base, face=m.get("latin")) if k == "latin" else base for k in LANGS}


def _lang_hu(text, m, lang, measure):
    """글자들을 한 언어(lang)의 글자 모양으로 그린 폭(HWPUNIT) → (폭, 글꼴로 쟀나). 글자 크기 = 크기 × 상대 크기, 폭 =
    글자 폭(em) × 그 크기 × 장평 + 글자 수 × 그 크기 × 자간. 빈칸: '글꼴에 어울리는 빈칸'이 꺼져 있으면(m["font_space"]
    False — 템플릿 기본) 한/글 고정 폭 HWP_SPACE_EM 으로 센다."""
    v = _slots(m)[lang]
    body = text if m.get("font_space") else text.replace(" ", "")
    em = _measure(measure, body, v["face"], m["bold"]) if body else 0.0
    ok = em is not None
    if em is None:
        em = sum(em_estimate(c, lang) for c in body) * (1.05 if m["bold"] else 1.0)
    if not m.get("font_space"):
        em += text.count(" ") * HWP_SPACE_EM
    size = m["height"] * v["relsize"] / 100.0
    return em * size * v["ratio"] / 100.0 + len(text) * size * v["spacing"] / 100.0, ok


def space_hu(m, measure=None, text=""):
    """칸 여유(빈칸 SLACK_SPACES 칸)에 쓸 빈칸 하나의 폭(HWPUNIT) → (폭, 'gdi'|'estimate') — 빈칸 폭은 언어마다 다를 수
    있어(장평·자간·상대 크기, '글꼴에 어울리는 빈칸'이면 글꼴) 칸 글자(text)에 쓰인 언어 후보 중 가장 넓은 값(글자가 없으면
    한글). 칸에 없는 언어는 보지 않는다(P-045 검토 D1-①-01·D1F-02). 자간이 아주 좁아 빈칸 폭이 음수여도 여유는 0 아래로
    내리지 않는다(검토 D2-①-01 — 보수 어림이 실제 어림보다 좁아지지 않게)."""
    used = {k for langs, run in script_runs(text) if run.strip() for k in langs}
    widths, how = [], "gdi"
    for lang in [k for k in LANGS if k in used] or ["hangul"]:
        w, ok = _lang_hu(" ", m, lang, measure)
        widths.append(w)
        how = how if ok else "estimate"
    return max(0.0, max(widths)), how


def gap_hu(gap, near, m, measure=None):
    """낱말 사이 빈칸(gap)의 폭(HWPUNIT) — text_hu 처럼 붙은 글자(near: 앞 글자, 줄 첫머리면 뒤 글자)의 언어로, 후보가
    여럿이면 가장 넓게. 줄 수 어림의 빈칸이 칸 글자 폭 셈과 같은 폭이 되게 한다(P-045 검토 D1F-01). 잰 방법은 따로 세지
    않는다 — 붙은 글자의 언어 글꼴은 그 낱말을 잴 때 이미 쟀다(검토 D2-③-N01)."""
    return max(_lang_hu(gap, m, lang, measure)[0] for lang in char_langs(near)) if gap else 0.0


def text_hu(text, m, measure=None):
    """한 줄 글자 폭(HWPUNIT) → (폭, 'gdi'|'estimate'). m = style_metrics 값. measure(글자, 글꼴, 진하게) → em 폭 | None.
    글자마다 한/글이 그 글자를 그리는 언어의 글꼴·장평·자간·상대 크기로 잰다(P-045, F-152). 언어가 정해지지 않은 글자
    (후보 여럿 — UNSURE 등)는 한 글자씩 후보 언어마다 재어 가장 넓은 값으로."""
    total, how = 0.0, "gdi"
    for langs, run in script_runs(text):
        for part in ([run] if len(langs) == 1 else run):
            widths = []
            for lang in langs:
                w, ok = _lang_hu(part, m, lang, measure)
                widths.append(w)
                how = how if ok else "estimate"
            total += max(widths)
    return total, how


def unbreakable(token, m):
    """공백 없는 낱말 → 줄을 나눌 수 없는 조각들 — 한/글 줄 나눔 기준대로. 한글 '어절'·영어 '단어'(기본)면 낱말 통째.
    아니면 라틴 쪽 이어진 글자(따옴표·통화 기호 포함, LATIN_LIKE)와 그 밖(한글 등) 이어진 글자로 나눠, 영어 '글자'
    (BreakLatinWord=BreakWord)면 라틴 쪽을 한 글자씩, 한글 '글자'(BreakNonLatinWord)면 그 밖을 한 글자씩."""
    bh, bl = m.get("break_hangul"), m.get("break_latin")
    if not (bh or bl):
        return [token]
    out = []
    for part in re.findall("[%s]+|[^%s]+" % (LATIN_LIKE, LATIN_LIKE), token):
        latin = re.match("[%s]" % LATIN_LIKE, part) is not None
        out.extend(part if (bl if latin else bh) else [part])
    return out


def cell_need(text, m, inside_lr, measure=None):
    """칸 하나 → (줄바꿈 없이 필요한 너비, 나눌 수 없는 가장 긴 조각만 들어갈 너비, 잰 방법) HWPUNIT. 너비 = 글자 폭 ×
    덧붙임 + 공백 SLACK_SPACES 칸 + 칸 안 좌우 여백 + 문단 좌우 여백. 칸 안 줄(<br>)은 줄마다."""
    full, word, how = 0.0, 0.0, "gdi"
    for line in unicodedata.normalize("NFC", text or "").split("\n"):      # 풀어쓴 한글도 글자 단위로(검토 P-041 3차 2)
        w, hw = text_hu(line, m, measure)
        full = max(full, w)
        how = "estimate" if hw == "estimate" else how
        for x in line.split() or [line]:
            for part in unbreakable(x, m):
                word = max(word, text_hu(part, m, measure)[0])
    sp, hs = space_hu(m, measure, text)
    how = "estimate" if hs == "estimate" else how
    pad = SLACK_SPACES * sp + inside_lr + m.get("para_lr", 0)
    k = SAFETY[how]
    return int(math.ceil(full * k + pad)), int(math.ceil(word * k + pad)), how


def level(maxw, floor, avail):
    """sum(min(필요, max(T, 하한))) <= avail 인 가장 큰 T (이분 탐색 60번). 하한 합이 avail 이하여야 한다."""
    lo, hi = 0.0, float(max(maxw))
    for _ in range(60):
        t = (lo + hi) / 2
        if sum(min(x, max(t, y)) for x, y in zip(maxw, floor)) > avail:
            hi = t
        else:
            lo = t
    return lo


def _spread(out, cap, avail):
    """반올림 나머지(칸 수 아래 HWPUNIT) — 합이 avail 이 될 때까지 cap 보다 좁은 칸에 하나씩 더한다."""
    cut = [i for i in range(len(out)) if out[i] < cap[i]]    # 합 < avail < sum(cap) 이면 반드시 있다
    k = 0
    while sum(out) < avail:
        out[cut[k % len(cut)]] += 1
        k += 1
    return out


def _fit_columns(maxw, minw, avail):
    """fit_columns 본체 → (칸 너비, 지킨 낱말 하한(버린 칸은 0), 줄였나)."""
    n = len(maxw)
    if not n:
        return [], [], False
    maxw = [max(int(x), 1) for x in maxw]
    minw = [min(max(int(y), 1), x) for x, y in zip(maxw, minw)]
    avail = max(int(avail), 0)                         # 음수 상한이면 하한을 다 버려도 끝나지 않는다(검토 P-041 3차 4)
    if sum(maxw) <= avail:
        return maxw, minw, False
    t0 = level(maxw, [0] * n, avail)
    keep = max(FLOOR_KEEP * t0, min(MIN_CELL, t0)) - 1   # T 하한 — 줄인 칸이 MIN_CELL 아래로 가지 않게(검토 P-041 3차 3)
    floor = list(minw)
    while True:
        if sum(floor) <= avail:                        # (합이 넘치면 level 이 0 — 아래 조건에서도 버려진다)
            t = level(maxw, floor, avail)
            if t >= keep:                              # 하한이 모두 0 이면 t = t0 — 반드시 끝난다
                break
        top = max(floor)
        floor = [0 if y == top else y for y in floor]
    out = [min(x, max(int(t), y)) for x, y in zip(maxw, floor)]
    return _spread(out, maxw, avail), floor, True


def fit_columns(maxw, minw, avail):
    """칸마다 (줄바꿈 없이 필요한 너비, 나눌 수 없는 조각 너비) → 칸 너비. 합이 avail 이하면 그대로(표가 본문 폭보다 좁다).
    넘으면 합 = avail: 기준 너비 T 를 찾아 필요한 너비가 T 이하인 칸은 그대로(줄바꿈 없음), 넘는 칸은 T 로 줄인다(긴 칸끼리
    같은 너비 — 필요한 너비가 큰 칸이 작은 칸보다 좁아지지 않는다). 줄인 칸도 나눌 수 없는 조각(낱말) 너비 아래로는 안
    줄인다 — 단, 하한을 지키느라 T 가 하한 없이 나눈 T0 의 FLOOR_KEEP(80%) 아래로 내려가거나 하한 합이 넘치면 큰 하한부터
    (같은 값은 함께) 버린다(긴 경로 같은 낱말 하나가 다른 칸을 누르지 않게 — 버린 낱말은 한/글이 끊는다). → (칸 너비, 줄였나)
    표 칸 글자로 줄 수까지 어림해 다듬는 것은 fit_table(refine_lines)."""
    out, _, capped = _fit_columns(maxw, minw, avail)
    return out, capped


def cell_layout(text, m, inside_lr, measure=None):
    """칸 하나의 줄 수 어림 재료 — {"lines": 칸 안 줄(<br>)마다 [(앞 빈칸 폭, [나눌 수 없는 조각 폭])], "k": 덧붙임(SAFETY),
    "pad": 보수 어림 여백(빈칸 SLACK_SPACES 칸 + 칸 안·문단 좌우 여백), "margins": 칸 안·문단 좌우 여백,
    "need": 보수 어림 한 줄 너비(cell_need 와 같음), "need_real": 실제 어림 한 줄 너비(글자 폭 + 여백)}. 폭은 HWPUNIT.
    빈칸 폭은 붙은 글자 언어로(gap_hu — text_hu 와 같게, P-045). 보수 어림 = 줄마다 빈칸 2칸 남기고 글자 폭에 덧붙임
    (cell_need 와 같은 기준), 실제 어림 = 한/글처럼 칸 안을 다 채움."""
    text = unicodedata.normalize("NFC", text or "")
    need, _, how = cell_need(text, m, inside_lr, measure)
    sp, hs = space_hu(m, measure, text)
    lines, hows, full = [], {how, hs}, 0.0
    for line in text.split("\n"):
        full = max(full, text_hu(line, m, measure)[0])
        words, prev = [], None
        for gap, x in re.findall("( *)([^ ]+)", line):            # 빈칸 여럿·앞 빈칸도 그 폭대로(검토 P-041 3차 2)
            gw = gap_hu(gap, prev or x[0], m, measure)
            ps = []
            for part in unbreakable(x, m):
                w, h = text_hu(part, m, measure)
                ps.append(w)
                hows.add(h)
            words.append((gw, ps))
            prev = x[-1]
        lines.append(words)
    margins = inside_lr + m.get("para_lr", 0)
    return {"lines": lines, "k": SAFETY["estimate" if "estimate" in hows else "gdi"],
            "pad": SLACK_SPACES * sp + margins, "margins": margins, "need": need,
            "need_real": int(math.ceil(full + margins))}


def lines_at(cell, width, real=False):
    """칸 너비 width(HWPUNIT)에서 칸 글자가 몇 줄인지 어림 — 조각(한/글 줄 나눔 기준 단위)을 앞에서부터 줄에 채운다.
    한 줄보다 긴 조각은 글자로 끊겨 여러 줄, 줄을 넘기며 생긴 줄 첫머리 빈칸은 버린다(칸 안 줄 첫머리 빈칸은 둔다).
    real=False 면 보수 어림(빈칸 2칸 남김·덧붙임), True 면 실제 어림(칸 안을 다 채움). 한 줄 너비 이상이면 칸 안 줄(<br>) 수,
    아래면 적어도 그보다 한 줄 더."""
    nl = len(cell["lines"])
    if width >= (cell["need_real"] if real else cell["need"]):
        return nl
    k = 1.0 if real else cell["k"]
    area = width - (cell["margins"] if real else cell["pad"])
    if area <= 0:
        return 10 ** 6
    n = 0
    for words in cell["lines"]:
        n, cur = n + 1, 0.0
        if words:                                     # 줄(<br>) 첫머리 빈칸은 따로 한 덩어리 — 버리지 않는다(뒤 조각이 안
            cur = min(words[0][0] * k, area)          # 들어가면 그 조각만 다음 줄로 — 줄 수가 너비에 따라 늘지 않게, 검토 4차)
        for j, (gap, ps) in enumerate(words):
            for i, w in enumerate(ps):
                w *= k
                lead = gap * k if i == 0 and j > 0 and cur > 0 else 0.0
                if cur + lead + w <= area:
                    cur += lead + w
                    continue
                if cur > 0:
                    n += 1
                extra = int(math.ceil(w / area)) - 1 if w > area else 0
                n += extra
                cur = w - extra * area
    return max(n, nl + 1)


def min_width(cell, n, lo, hi, real=False):
    """lines_at(cell, W, real) <= n 인 가장 작은 W (lo 이상 hi 이하 — hi 에서는 n 줄 이하여야 한다). 줄 수는 너비가 늘면
    줄거나 같다(앞에서부터 채우기)."""
    lo, hi = int(lo), int(hi)
    if lines_at(cell, lo, real) <= n:
        return lo
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if lines_at(cell, mid, real) <= n:
            hi = mid
        else:
            lo = mid
    return hi


def table_height(cells, widths, real=False):
    """표 높이 어림 — 줄마다 가장 많은 칸 줄 수의 합."""
    return sum(max(lines_at(cl, w, real) for cl, w in zip(row, widths)) for row in cells)


REFINE_STEPS = 200                  # 다듬기 2단계 반복 상한 — 아주 큰 표에서도 시간이 한정되게(검토 P-041 3차 5)


def refine_lines(cells, widths, need, floor, total):
    """fit_columns(긴 칸끼리 같은 너비) 결과를 어느 줄(행)도 높아지지 않게 다듬어 표 높이를 줄인다(P-041 2차).
    줄 수는 두 가지로 어림한다 — 보수(빈칸 2칸 남김·덧붙임, cell_need 기준)와 실제(한/글처럼 칸 안을 다 채움). 좁힐 때는
    두 어림 모두에서 줄 높이가 그대로여야 한다(보수 어림만 보면 실제 줄이 늘 수 있다, 검토 P-041 3차 1).
    1) 줄바꿈되는 칸(너비 < 필요)을 좁힌다 — 칸마다, 그 줄 높이를 정하는 칸(가장 긴 칸)은 줄 수 그대로, 나머지 칸은 그 줄
       높이보다 한 줄 적게까지(원래 더 많으면 그대로)만 늘 수 있는 가장 좁은 너비로(지킨 낱말 하한·MIN_CELL 이상).
       한 줄짜리 줄(제목 줄 등)은 그대로 한 줄. 줄바꿈 없는 칸(너비 = 필요)은 손대지 않는다.
    2) 모은 너비로, 넓힌 너비당 표 높이(두 어림 합)가 가장 많이 주는 줄부터 그 줄에서 가장 긴 칸들(보수 어림)을 한 줄 덜
       되게 넓힌다(REFINE_STEPS 번까지).
    3) 남은 너비는 좁은 칸부터 고르게(필요한 너비까지) — 합 = total.
    → (칸 너비, {"before": [보수, 실제] 높이, "after": [보수, 실제] 높이}).
    cells[r][c] = cell_layout, need = 칸마다 줄바꿈 없는 너비, floor = 지킨 낱말 하한(_fit_columns)."""
    nr, nc = len(cells), len(widths)
    memo = {}

    def col(c, x):                                    # 칸 c 를 너비 x 로 — 줄마다 (보수, 실제) 줄 수
        if (c, x) not in memo:
            memo[c, x] = [(lines_at(cells[r][c], x), lines_at(cells[r][c], x, True)) for r in range(nr)]
        return memo[c, x]

    def heights(ws):
        cs = [col(c, ws[c]) for c in range(nc)]
        return [tuple(max(cs[c][r][j] for c in range(nc)) for j in (0, 1)) for r in range(nr)]

    w = [int(x) for x in widths]
    hs = heights(w)
    before = [sum(h[0] for h in hs), sum(h[1] for h in hs)]
    low = [max(int(floor[c]), MIN_CELL) for c in range(nc)]
    new = list(w)
    for c in range(nc):
        if w[c] < need[c]:
            lo, cnt = min(low[c], w[c]), col(c, w[c])
            for r in range(nr):
                for j in (0, 1):
                    got, top = cnt[r][j], hs[r][j]
                    lo = max(lo, min_width(cells[r][c], got if got >= top else max(got, top - 1), lo, w[c], bool(j)))
            new[c] = lo
    w, budget = new, total - sum(new)
    for _ in range(REFINE_STEPS):
        if budget <= 0:
            break
        hs = heights(w)
        h, best = sum(a + b for a, b in hs), None
        for r in range(nr):
            cand, ok = list(w), hs[r][0] > 1
            for c in range(nc):
                if ok and col(c, w[c])[r][0] >= hs[r][0]:
                    if lines_at(cells[r][c], need[c]) > hs[r][0] - 1:    # 칸 안 줄(<br>)이 많아 더 못 줄임
                        ok = False
                    else:
                        cand[c] = min_width(cells[r][c], hs[r][0] - 1, w[c], need[c])
            cost = sum(cand) - sum(w)
            if not ok or cost <= 0 or cost > budget:
                continue
            gain = h - sum(a + b for a, b in heights(cand))
            if gain > 0 and (best is None or (gain / float(cost), -cost) > best[0]):
                best = ((gain / float(cost), -cost), cand, cost)
        if best is None:
            break
        w, budget = best[1], budget - best[2]
    if sum(w) < total:
        t = level(need, w, total)
        w = _spread([min(x, max(int(t), y)) for x, y in zip(need, w)], need, total)
    hs = heights(w)
    return w, {"before": before, "after": [sum(h[0] for h in hs), sum(h[1] for h in hs)]}


def fit_table(rows, cell_styles, metrics, avail, inside_lr=DEFAULT_INSIDE_LR, measure=None):
    """표 칸 글자·칸 스타일 이름 격자 → {"widths": 칸 너비, "need": 줄바꿈 없는 너비, "word": 낱말 너비, "how", "capped",
    "maxmin": 다듬기 전 너비(fit_columns), "lines": 표 높이 어림 {"before"·"after": [보수, 실제] 줄}} — 줄였을 때만
    maxmin·lines(refine_lines).
    metrics = style_metrics(템플릿), avail = 표 너비 상한. 칸 너비는 MIN_CELL 아래로 내리지 않는다."""
    nc = len(rows[0])
    maxw, minw, hows, cells = [MIN_CELL] * nc, [MIN_CELL] * nc, set(), []
    for r, row in enumerate(rows):
        cells.append([])
        for c, text in enumerate(row):
            m = dict(DEFAULT_METRICS, **(metrics.get(cell_styles[r][c]) or {}))
            a, b, how = cell_need(text, m, inside_lr, measure)
            maxw[c], minw[c] = max(maxw[c], a), max(minw[c], b)
            if (text or "").strip():                          # 빈 칸은 잰 것도 어림한 것도 없다(검토 P-045 D1-②-03)
                hows.add(how)
            cells[-1].append(cell_layout(text, m, inside_lr, measure))
    widths, floor, capped = _fit_columns(maxw, minw, max(int(avail), MIN_CELL * nc))
    out = {"widths": widths, "need": maxw, "word": minw, "capped": capped, "maxmin": None, "lines": None,
           "how": "gdi" if hows == {"gdi"} else ("estimate" if hows <= {"estimate"} else "mixed")}
    if capped:
        out["maxmin"] = list(widths)
        out["widths"], out["lines"] = refine_lines(cells, widths, maxw, floor, sum(widths))
    return out


class GdiMeasure:
    """Windows GDI 로 글꼴 글자 폭(em)을 잰다 — 한/글이 그리는 글꼴(템플릿 스타일 글꼴)과 같은 글꼴(P-041). 그 글꼴이 없어
    다른 글꼴로 바뀌면(GetTextFace 가 같은 굵기의 없는 이름 글꼴과 같음) None → 어림. gdi: 시험용 흉내(없으면 gdi32)."""
    EM = 1000

    def __init__(self, gdi=None):
        import ctypes
        from ctypes import wintypes
        self.ct, self.wt = ctypes, wintypes
        g = self.gdi = gdi if gdi is not None else ctypes.WinDLL("gdi32")
        g.CreateCompatibleDC.restype, g.CreateCompatibleDC.argtypes = wintypes.HDC, [wintypes.HDC]
        g.CreateFontW.restype = wintypes.HFONT
        g.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCWSTR]
        g.SelectObject.restype, g.SelectObject.argtypes = wintypes.HGDIOBJ, [wintypes.HDC, wintypes.HGDIOBJ]
        g.GetTextExtentPoint32W.restype = wintypes.BOOL
        g.GetTextExtentPoint32W.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.SIZE)]
        g.GetTextFaceW.restype, g.GetTextFaceW.argtypes = ctypes.c_int, [wintypes.HDC, ctypes.c_int, wintypes.LPWSTR]
        g.DeleteObject.restype, g.DeleteObject.argtypes = wintypes.BOOL, [wintypes.HGDIOBJ]
        g.DeleteDC.restype, g.DeleteDC.argtypes = wintypes.BOOL, [wintypes.HDC]
        self.dc = g.CreateCompatibleDC(None)
        if not self.dc:
            raise OSError("CreateCompatibleDC 실패")
        self.fonts, self.faces, self.fallback = {}, {}, {}

    def _create(self, face, bold):
        return self.gdi.CreateFontW(-self.EM, 0, 0, 0, 700 if bold else 400, 0, 0, 0, 1, 0, 0, 0, 0, face)

    def _face_of(self, hfont):
        if not hfont:
            return None
        old = self.gdi.SelectObject(self.dc, hfont)
        buf = self.ct.create_unicode_buffer(128)
        self.gdi.GetTextFaceW(self.dc, 128, buf)
        self.gdi.SelectObject(self.dc, old)
        return buf.value

    def _fallback(self, bold):
        """없는 이름으로 만든 글꼴의 실제 이름(굵기마다) — GDI 가 대신 고르는 글꼴."""
        if bold not in self.fallback:
            probe = self._create("NoSuchFont-Metrics-Probe", bold)
            self.fallback[bold] = self._face_of(probe)
            if probe:
                self.gdi.DeleteObject(probe)
        return self.fallback[bold]

    def _font(self, face, bold):
        key = (face, bool(bold))
        if key not in self.fonts:
            h = self._create(face, bold)
            got = self._face_of(h)
            ok = bool(h) and bool(got) and (got.lower() == face.lower() or got != self._fallback(bool(bold)))
            if h and not ok:
                self.gdi.DeleteObject(h)
            self.fonts[key] = h if ok else None
            self.faces["%s%s" % (face, " (진하게)" if bold else "")] = ok
        return self.fonts[key]

    def __call__(self, text, face, bold=False):
        f = self._font(face, bold) if face else None
        if f is None:
            return None
        if not text:
            return 0.0
        size = self.wt.SIZE()
        old = self.gdi.SelectObject(self.dc, f)
        n = len(text.encode("utf-16-le")) // 2                 # GDI 는 UTF-16 단위로 센다(BMP 밖 글자는 둘)
        ok = self.gdi.GetTextExtentPoint32W(self.dc, text, n, self.ct.byref(size))
        self.gdi.SelectObject(self.dc, old)
        return size.cx / float(self.EM) if ok else None

    def close(self):
        for h in self.fonts.values():
            if h:
                self.gdi.DeleteObject(h)
        self.fonts = {}
        if self.dc:
            self.gdi.DeleteDC(self.dc)
            self.dc = None


def gdi_measure():
    """GdiMeasure 를 만든다 — Windows 가 아니거나 실패하면 None(어림으로)."""
    if sys.platform != "win32":
        return None
    try:
        return GdiMeasure()
    except Exception:
        return None


# ------------------------------------------------------------------ 쓴 뒤 대조

def _norm_line(s):
    if s in (None, "-"):
        return None
    return NO_FILL if s == NO_FILL else " ".join(s.split()[:2])


def check_tables(x, written):
    """written: [(표 ID, 계획(plan_table · 작성기 fit_plan + "col_hu": [칸 너비] | None, "center": bool, "done": {종류: 결과},
    "label": '표 k'))]
    — 내보낸 HWPML 에서 칸마다 선·배경·제목 셀·스타일·너비, 표 안 여백, 표가 든 문단의 가운데 정렬을 대조
    → 다른 곳 [{"table", "at", "what", "want", "got"}].
    done 이 있으면 입힌(True) 것과 입힐 것이 없던(None) 것만 본다 — 실패·꺼짐은 이미 '입히지 못한 곳'으로 알렸다(검토 P-040 2).
    선·배경·제목 셀·스타일은 계획 칸에 그 값이 있을 때만 — 칸 너비 맞춤만 하는 표(fit_plan)는 한/글 기본 그대로라 보지 않는다."""
    root, _, elems = load(x)
    bfs = border_fills(root)
    para_align, _, style = shapes(root)
    up = {c: p for p in root.iter() for c in p}                # 표 → TEXT → 문단(표가 든 문단의 정렬)
    margins = {ps.get("Id"): (dict(ps.find("PARAMARGIN").attrib) if ps.find("PARAMARGIN") is not None else {})
               for ps in root.iter("PARASHAPE")}
    by = {tid: (tbl, t) for tid, tbl, t in elems}
    out = []
    for tid, plan in written:
        done = plan.get("done")
        see = (lambda k: True) if done is None else (lambda k: done.get(k) in (True, None))   # noqa: E731
        name = plan.get("label") or tid
        if tid not in by:
            out.append({"table": name, "at": "표", "what": "표 없음", "want": None, "got": None})
            continue
        tbl, t = by[tid]
        if see("center") and plan.get("center"):
            p = up.get(up.get(tbl))
            got = para_align.get(p.get("ParaShape")) if p is not None else None
            if got != "Center":
                out.append({"table": name, "at": "표", "what": "가운데 정렬", "want": "Center", "got": got})
            pos = tbl.find("SHAPEOBJECT/POSITION")              # 글자처럼 취급해야 문단 정렬을 따른다
            if pos is not None and pos.get("TreatAsChar") not in (None, "true"):
                out.append({"table": name, "at": "표", "what": "글자처럼 취급", "want": "true", "got": pos.get("TreatAsChar")})
            if plan.get("anchor_reset") and p is not None:         # 표 문단 여백을 0 으로 했으면(가운데가 치우치지 않게)
                mg = margins.get(p.get("ParaShape")) or {}
                left = [k for k in ("Left", "Right", "Indent") if hp._int(mg.get(k)) != 0]
                if left:
                    out.append({"table": name, "at": "표", "what": "표 문단 여백", "want": 0,
                                "got": {k: mg.get(k) for k in left}})
        im = tbl.find("INSIDEMARGIN")
        if see("margin") and plan.get("inside_margin") and im is not None:
            got = [hp._int(im.get(k)) for k in ("Left", "Right", "Top", "Bottom")]
            if got != list(plan["inside_margin"]):
                out.append({"table": name, "at": "표", "what": "안 여백", "want": plan["inside_margin"], "got": got})
        for row in tbl.findall("ROW"):
            for cell in row.findall("CELL"):
                r, c = hp._int(cell.get("RowAddr")), hp._int(cell.get("ColAddr"))
                if r >= len(plan["cells"]) or c >= len(plan["cells"][0]):
                    continue
                want = plan["cells"][r][c]
                got = bfs.get(cell.get("BorderFill")) or {}
                if see("border"):
                    for k in ("L", "R", "T", "B"):
                        if want.get(k) and _norm_line(got.get(k)) != line_text(want[k]):
                            out.append({"table": name, "at": [r, c], "what": k, "want": line_text(want[k]),
                                        "got": got.get(k)})
                    if "fill" in want and (got.get("fill") or NO_FILL) != fill_text(want["fill"]):
                        out.append({"table": name, "at": [r, c], "what": "배경", "want": fill_text(want["fill"]),
                                    "got": got.get("fill")})
                if see("header") and "header" in want and bool(want.get("header")) != (cell.get("Header") == "true"):
                    out.append({"table": name, "at": [r, c], "what": "제목 셀", "want": bool(want.get("header")),
                                "got": cell.get("Header")})
                p0 = cell.find("PARALIST/P")
                sname = style.get(p0.get("Style")) if p0 is not None else None
                if want.get("style") and sname != want["style"]:
                    out.append({"table": name, "at": [r, c], "what": "스타일", "want": want["style"], "got": sname})
                col_hu = plan.get("col_hu")
                if see("width") and col_hu and cell.get("Width") is not None and c < len(col_hu):
                    w = hp._int(cell.get("Width"))
                    if abs(w - col_hu[c]) > max(30, col_hu[c] * WIDTH_TOL):
                        out.append({"table": name, "at": [r, c], "what": "너비", "want": col_hu[c], "got": w})
    return out


# ------------------------------------------------------------------ 명령

def main(argv=None):
    from _console import configure_console
    configure_console()
    ap = argparse.ArgumentParser(description="표 서식 파일 만들기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("from-poc", help="PoC 보고(T0 참고본 표 서식)에서 서식 파일")
    a.add_argument("report")
    a.add_argument("out")
    a.add_argument("--source", required=True)
    a.add_argument("--alias", action="append", default=[], help="우리 캡션=참고 캡션")
    a.add_argument("--default")
    a.add_argument("--sections", default="", help="쉼표로 구분한 구역 ID. 미지정이면 모든 구역의 최상위 표")
    args = ap.parse_args(argv)
    alias = dict(x.split("=", 1) for x in args.alias)
    sf = from_poc(Path(args.report).read_text(encoding="utf-8"), args.source, alias, args.default,
                  tuple(s for s in args.sections.split(",") if s))
    Path(args.out).write_text(json.dumps(sf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("표 서식 %d개 → %s (default %s, alias %s)" % (len(sf["tables"]), args.out, sf["default"], sf["alias"]))
    for k, v in sf["tables"].items():
        print("  %-20s %s %s 칸 서식 %s 비율 %s 안 여백 %s 제목 셀 %s" % (k, v["ref_id"], v["size"], "있음" if v["cells"] else "없음",
                                                                v["col_ratio"], v["inside_margin"], v["header_cells"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
