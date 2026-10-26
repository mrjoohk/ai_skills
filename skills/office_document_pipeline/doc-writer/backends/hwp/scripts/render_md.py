#!/usr/bin/env python3
"""문서 모델 → 에이전트용 .md (설계 UF-04, D-012). 읽기 명령은 결과를 항상 .md 로 남긴다.

.md 는 DRM 보호를 받지 않는 평문이다 — 파일 머리에 고지하고, 정해진 폴더(--md-dir, 기본 hwpx_md)에만 쓴다.
"""
import datetime
import re
from pathlib import Path

import hwpml_parse as hp

NOTICE = ("> **DRM 미보호 평문** — 이 파일은 한/글 문서에서 읽은 내용이며 원본의 보호 여부와 관계없이 평문이다. "
          "원본에 적용되는 현재 프로젝트의 보관·취급 규칙을 따른다.")
COVERED_H, COVERED_V = "◀", "▲"


def esc(s):
    return (s or "").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def head(model, command, extra=None):
    st = model.get("stats", {})
    lines = ["# HWPX 읽기 결과 — %s" % Path(model.get("file") or "?").name, "", NOTICE, "",
             "- 원본: `%s` (선두 %s)" % (model.get("file"), model.get("head")),
             "- 읽은 시각: %s · 한/글 %s · HWPML %s · 명령 `%s`" % (
                 datetime.datetime.now().isoformat(timespec="seconds"), model.get("hwp_version"),
                 model.get("hwpml_version"), command)]
    if extra:
        lines += ["- %s" % e for e in extra]
    if model.get("coverage_mismatch"):
        lines.append("- **경고: 파싱 누락 의심** (파싱 수, 원문 태그 수) %s — 이 결과에 빠진 내용이 있을 수 있다"
                     % model["coverage_mismatch"])
    if st.get("unknown_list_owners"):
        lines.append("- 참고: 모르는 개체 안 문단 %s — `기타 개체`로 넣었다" % st["unknown_list_owners"])
    return lines + [""]


def summary(model):
    st = model["stats"]
    f = st.get("fields", {})
    rows = [("구역", st["sections"]), ("문단(P, 셀·각주 안 포함)", st["p_elements"]), ("표(중첩 포함)", st["tables"]),
            ("셀", st["cells"]), ("격자 불일치 표", st["grid_bad_tables"]), ("머리말 / 꼬리말", "%d / %d" % (st["headers"], st["footers"])),
            ("각주 / 미주", "%d / %d" % (st["footnotes"], st["endnotes"])), ("메모", st["memos"]),
            ("글상자", st["textboxes"]), ("입력 필드(누름틀 / 셀)", "%d / %d" % (f.get("clickhere", 0), f.get("cell", 0))),
            ("기타 필드", ", ".join("%s %d" % kv for kv in f.items() if kv[0] not in ("clickhere", "cell")) or "0")]
    return ["## 요약", "", "| 항목 | 값 |", "|---|---|"] + ["| %s | %s |" % r for r in rows] + [""]


def outline_lines(model):
    out = ["## 개요 (개요 문단)", ""]
    items = hp.outline(model)
    src = model.get("stats", {}).get("heading_source")
    if src == "number":
        out += ["기준: **번호 글자** — 문단 모양이 '개요'인 문단이 없어 '1.1 제목'처럼 번호로 시작하는 짧은 문단을 제목으로 봤다"
                " (수준 = 번호 마디 수).", ""]
    elif src == "outline":
        out += ["기준: 문단 모양 '개요'. 자동 번호(1., 1.1.)는 글자에 없어 표시하지 않는다.", ""]
    if not items:
        out.append("제목으로 볼 문단이 없다. 제목은 스타일 이름으로 찾는다(아래 본문의 `스타일`).")
    for b in items:
        out.append("%s- %s `%s`" % ("  " * (b["level"] - 1), esc(b["text"]), b["id"]))
    return out + [""]


def table_lines(t, depth=0):
    cap = (" · 캡션: %s" % esc(t["caption"])) if t.get("caption") else ""
    grid = "격자 OK" if t["grid_ok"] else "**격자 불일치: %s**" % t["grid_note"]
    hd = "#" * min(4 + depth, 6)
    out = ["%s 표 `%s` — %d×%d%s · %s" % (hd, t["id"], t["rows"], t["cols"], cap, grid), ""]
    rows, cols = t["rows"], t["cols"]
    if rows <= 0 or cols <= 0 or rows * cols > 4000:
        out.append("(격자로 그리지 않음 — 셀 목록)")
        out += ["- `%s` %s%s" % (c["id"], esc(c["text"]), "".join(" [표 %s]" % n["id"] for n in c.get("tables", [])))
                for c in t["cells"]]
        return out + [""]
    grid_txt = [[""] * cols for _ in range(rows)]
    for c in t["cells"]:
        txt = "<br>".join(x for x in [esc(c["text"])] + ["[표 %s]" % n["id"] for n in c.get("tables", [])] if x)
        if c["rowspan"] > 1 or c["colspan"] > 1:
            txt += " ⟨병합 %d×%d⟩" % (c["rowspan"], c["colspan"])
        if c.get("field"):
            txt += " ⟦필드 %s⟧" % esc(c["field"])
        for r in range(c["row"], min(rows, c["row"] + c["rowspan"])):
            for k in range(c["col"], min(cols, c["col"] + c["colspan"])):
                grid_txt[r][k] = COVERED_V if r > c["row"] else COVERED_H
        if c["row"] < rows and c["col"] < cols:
            grid_txt[c["row"]][c["col"]] = txt or " "
    out.append("| r\\c | " + " | ".join("c%d" % k for k in range(cols)) + " |")
    out.append("|---" * (cols + 1) + "|")
    for r in range(rows):
        out.append("| r%d | " % r + " | ".join(grid_txt[r]) + " |")
    out.append("")
    for c in t["cells"]:
        for n in c.get("tables", []):
            out.append("↳ 셀 `%s` 안의 중첩 표" % c["id"])
            out.append("")
            out += table_lines(n, depth + 1)
    return out


def block_lines(b):
    t = b["type"]
    if t == "table":
        return table_lines(b)
    if t == "para":
        if b.get("level"):
            return ["%s %s `%s`" % ("#" * min(2 + b["level"], 6), esc(b["text"]), b["id"]), ""]
        style = (" · %s" % b["style"]) if b.get("style") and b["style"] != "바탕글" else ""
        return ["`%s`%s  %s" % (b["id"], style, esc(b["text"])), ""]
    label = {"textbox": "글상자", "caption": "캡션", "other": "기타 개체"}.get(t, t)
    out = ["> [%s `%s` · %s] %s" % (label, b["id"], b.get("owner", ""), esc(b.get("text", ""))), ""]
    for n in b.get("tables", []):
        out += table_lines(n, 1)
    return out


OBJECT_TAGS = ("PICTURE", "CONTAINER", "OLE", "EQUATION", "CHART", "VIDEO", "TEXTART", "RECTANGLE", "ELLIPSE", "ARC",
               "POLYGON", "CURVE", "LINE", "CONNECTLINE")
_TOP = re.compile(r"^s(\d+)\.p(\d+)$")


def _mm(v):
    try:
        return "%.0f" % (int(v) / 283.465)
    except (TypeError, ValueError):
        return None


def objects_lines(model):
    """그림·도형 개체의 자리 — 본문 글자에는 없다. 위치(개체가 든 문단 ID)·크기·캡션·앞 글(같은 구역에서 그 문단까지의
    마지막 글 문단). 설명서처럼 화면 그림이 많은 문서를 옮겨 쓸 때 그림 자리를 찾는다."""
    objs = [c for c in model.get("ctrls", []) if c["tag"] in OBJECT_TAGS]
    if not objs:
        return []
    blocks = {b["id"]: b for b in hp.iter_blocks(model["body"])}
    paras = {}
    for b in model["body"]:
        m = _TOP.match(b["id"]) if b["type"] == "para" else None
        if m:
            paras.setdefault(int(m.group(1)), []).append((int(m.group(2)), b))
    out = ["## 그림·개체 위치 (%d)" % len(objs), "",
           "본문 글자에 없는 그림·도형. 위치 = 개체가 든 문단(셀 안이면 셀 문단) ID, 앞 글 = 같은 구역에서 그 문단까지의 마지막 글.", "",
           "| # | 종류 | 위치 | 크기(mm) | 캡션 | 앞 글 |", "|---|---|---|---|---|---|"]
    for i, c in enumerate(objs, 1):
        sc = c.get("children", {}).get("SHAPECOMPONENT", {})
        w, h = _mm(sc.get("CurWidth") or sc.get("OriWidth")), _mm(sc.get("CurHeight") or sc.get("OriHeight"))
        cap = " / ".join(blocks[x].get("text", "") for x in c.get("blocks", []) if blocks.get(x, {}).get("type") == "caption")
        m = _TOP.match(c["at"])
        prev = ""
        if m:
            cand = [b for n, b in paras.get(int(m.group(1)), []) if n <= int(m.group(2))]
            if cand:
                prev = "`%s` %s" % (cand[-1]["id"], esc(cand[-1]["text"][:40]))
        out.append("| %d | %s | `%s` | %s | %s | %s |" % (i, c["tag"], c["at"], ("%s×%s" % (w, h)) if w and h else "",
                                                       esc(cap), prev))
    return out + [""]


def body_lines(model):
    out = ["## 본문", ""]
    for b in model["body"]:
        out += block_lines(b)
    return out


def notes_lines(model):
    out = []
    if model["headers"] or model["footers"]:
        out += ["## 머리말·꼬리말", "", "| ID | 종류 | 적용 | 내용 |", "|---|---|---|---|"]
        for kind, rows in (("머리말", model["headers"]), ("꼬리말", model["footers"])):
            out += ["| `%s` | %s | %s | %s |" % (r["id"], kind, r.get("apply"), esc(r["text"])) for r in rows]
        out.append("")
    if model["footnotes"] or model["endnotes"]:
        out += ["## 각주·미주", "", "| ID | 번호 | 위치 | 내용 |", "|---|---|---|---|"]
        for rows in (model["footnotes"], model["endnotes"]):
            out += ["| `%s` | %s | `%s` | %s |" % (r["id"], r.get("number"), r["at"], esc(r["text"])) for r in rows]
        out.append("")
    if model["memos"]:
        out += ["## 메모 (%d)" % len(model["memos"]), "",
                "메모는 작성·검토 과정에서 붙인 의견이다. 성격(검토 의견·작성 안내·할 일)은 내용으로 판단한다.", "",
                "| ID | 위치 | 메모가 붙은 글자 | 메모 |", "|---|---|---|---|"]
        out += ["| `%s` | `%s` | %s | %s |" % (m["id"], m["at"], esc(m["anchor_text"]), esc(m["text"]))
                for m in model["memos"]]
        out.append("")
    return out


def fields_lines(fields):
    out = ["## 필드", ""]
    if not fields["input"]:
        out.append("입력 필드(누름틀·셀 필드)가 없다. 채우기(fill)는 필드가 있어야 한다 — 자리표시 바꾸기(replace)를 쓴다.")
    else:
        out += ["| 이름 | 종류 | 개수 | 위치 | 현재 값 | 안내문 |", "|---|---|---|---|---|---|"]
        for r in fields["input"]:
            out.append("| %s | %s | %d%s | %s | %s | %s |" % (
                esc(r["name"]), r["kind"], r["count"], (" (한/글 %d)" % r["com_count"]) if r.get("com_count") else "",
                " ".join("`%s`" % a for a in r.get("at", [])) or "(한/글 목록에만)",
                esc(" / ".join(r.get("values", []))), esc(r.get("guide", ""))))
    if fields["other"]:
        out += ["", "비입력 필드: " + ", ".join("%s %d" % (r["kind"], r["count"]) for r in fields["other"])]
    return out + [""]


def fields_from_model(model):
    """한/글 없이 모델만으로 필드 표 (inspect 용)."""
    rows = {}
    for f in model["fields"]:
        r = rows.setdefault((f["name"], f["kind"]), {"name": f["name"], "kind": f["kind"], "count": 0, "at": [], "values": []})
        r["count"] += 1
        r["at"].append(f["at"])
        r["values"].append(f.get("value", ""))
        if f.get("guide"):
            r.setdefault("guide", f["guide"])
    rs = list(rows.values())
    return {"input": [r for r in rs if r["kind"] in ("clickhere", "cell")],
            "other": [r for r in rs if r["kind"] not in ("clickhere", "cell")]}


def search(model, patterns, width=60):
    """REQ-003: 키워드별 위치 ID와 앞뒤 문맥(≤120자)."""
    hits = []
    for loc, kind, text in hp.iter_locations(model):
        for p in patterns:
            i = text.find(p)
            while i >= 0:
                a, b = max(0, i - width), min(len(text), i + len(p) + width)
                hits.append({"key": p, "at": loc, "kind": kind,
                             "context": ("…" if a else "") + text[a:b].replace("\n", " ") + ("…" if b < len(text) else "")})
                i = text.find(p, i + len(p))
    return hits


def search_lines(hits, patterns):
    out = ["## 검색", ""]
    for p in patterns:
        hs = [h for h in hits if h["key"] == p]
        out.append("### `%s` — %d건" % (esc(p), len(hs)))
        out.append("")
        out += ["- `%s` (%s) %s" % (h["at"], h["kind"], esc(h["context"])) for h in hs]
        out.append("")
    return out


def write_md(md_dir, src, command, lines):
    d = Path(md_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / ("%s.%s.md" % (Path(src).stem, command))
    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return p
