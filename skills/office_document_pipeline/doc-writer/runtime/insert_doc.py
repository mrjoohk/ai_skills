#!/usr/bin/env python3
"""끼워 넣기 (P-052) — 이미 있는 문서(.hwpx, 사용자가 손본 판)의 정한 제목 앞에 명세 블록을 넣어 새 파일로 저장한다.

    python tools\\doc-writer\\insert_doc.py <대상.hwpx> --spec <블록 명세.md> --before <제목 글자> --out <새 파일.hwpx>
                                            [--report <보고.md>] [--timeout 180]

작성기(write_doc.py)는 템플릿에 문서 전체를 새로 쓴다 — 사용자가 손본 문서(목차·그림·표를 손으로 고친 판)에는 쓸 수 없다.
이 도구는 그 문서를 열어 '--before' 제목(개요 문단, 글자 정확히 같고 하나뿐) 바로 앞 문단 끝에서 블록을 차례로 넣는다.
대상은 열기만 한다(저장하지 않는다) — 결과는 늘 새 파일(이미 있으면 거절).

블록 명세(.md, UTF-8) — 한 줄 = 한 블록. <!-- … --> 는 메모(넣지 않음):
  #… ####### 제목            → COMSAF 개요 N (N = '#' 수 — 문서의 개요 수준 그대로, 번호는 한/글 자동)
  일반 줄                     → 본문 문단(03_본문_내용) — 단계 '1) …'
  - 항목 / 두 칸 들여 - 항목    → '○ 항목' / '  - 항목'
  ![캡션](hwpx:출처.hwpx#k ["가로x세로"])
                             → 출처 문서(저장소 안 상대 경로, DRM 가능)의 k 번째 그림을 한/글 안에서 옮긴다: 그 자리에서 출처를
                               끼워 넣고(InsertFile KeepStyle 0) 끼운 문단 가운데 k 번째 그림 문단만 남긴다 — 그림 파일을 꺼내지
                               않는다(D-028). 그림 문단 스타일 04, 출처 캡션은 그대로 두고 캡션 문단 스타일 04(캡션 넣기로 들어가
                               입힘). 출처 캡션 제목 = 명세 캡션이어야 한다. 크기를 쓰면 출처 크기와 1mm 넘게 다를 때 경고.
  표·그림 파일·작성 필요(>)·{{…}} 인용은 쓰지 않는다(명세 오류 — 이 도구에서는 실측하지 않았다).
실측 근거: PoC `tools/test_hwpx/insert_poc.py`(21.p052_insert_poc.bat, 10-23 22:53 — `logs/P-052_evidence/insert_poc_report.md`):
DRM 대상에 DRM 출처 InsertFile·앞뒤 문단 그대로·캡션 자동 번호 다시 매김·기존 캡션 안으로 들어가 스타일 — 모두 가정대로.

쓴 뒤 HWPML·한/글로 확인하고 어긋나면 저장하지 않는다(종료코드 1):
  넣은 곳 밖 루트 문단(종류·스타일·글자)·표 칸 글자 = 쓰기 전, 넣은 문단 = 명세(종류·스타일·글자, 그림 문단·캡션 스타일),
  그림 캡션 = 쓰기 전 + 새 그림(번호 차례, 뒤 그림은 번호만 +n)·표 캡션 그대로, 새 번호 조판 수 그대로, 머리말·꼬리말 그대로,
  기존 스타일 정의 그대로(더해진 스타일은 경고), 제목마다 한/글 개요 번호 = 수준 차례로 센 번호(쓰기 전에 이미 다른 제목은 빼고
  경고), DocuRay 저장·다시 열기·대상 바뀌지 않음.
경고만: 더해진 스타일, 번호가 바뀐 제목, 본문 글자 번호('그림 N'·'표 N' — 새 번호 이상, 목차 줄 포함)는 고칠 곳 후보로 보고.

종료코드: 0 성공 / 1 확인 실패·저장 실패 / 2 명세 오류·사전조건 / 3 평문 저장 / 4 열기 실패 / 5 시간초과 / 6 COM 없음
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path, PureWindowsPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import write_doc as wd          # noqa: E402  (hwp_session·hwpx_api·hwpml_parse 경로도 잡는다)
import hwp_session as hs        # noqa: E402
import hwpx_api as api          # noqa: E402
import hwpml_parse as hp        # noqa: E402
import render_md as rm          # noqa: E402

HWPX_FIG = re.compile(r"^hwpx:([^)\"#]+)#(\d{1,3})$")          # 경로에 '#' 없음 — 브리지 검사와 같은 해석(검토 D1-06)
HEADING_STYLE = wd.profiles.heading_pattern(wd.STYLES)  # default preset; helpers accept overrides
SIZE_TOL_MM = 1.0
MM = 283.465                    # HWPUNIT / mm


class SpecError(wd.SpecError):
    code = 2


# ------------------------------------------------------------------ 명세

def parse_blocks(text):
    """블록 명세 → 블록 목록 [{"kind": heading|para|item|figure, …}]. 그림 출처는 {"src": 경로, "k": 번호}."""
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    blocks = []
    for ln in body.splitlines():
        ln = ln.rstrip()
        if not ln.strip():
            continue
        if "{{" in ln:
            raise SpecError("끼워 넣기 명세에는 {{…}} 인용을 쓰지 않는다: %r" % ln.strip())
        h = re.match(r"^(#{1,7})[ \t]+(\S.*)$", ln)
        f = wd.FIG_RX.match(ln)
        if not f and (ln.lstrip().startswith("![") or "](hwpx:" in ln):   # 꼴이 틀린 그림 줄이 본문 글자로 들어가지 않게(D1-02)
            raise SpecError("그림 줄 꼴이 틀렸다(줄 처음 '![캡션](hwpx:경로#번호 \"가로x세로\")', 크기는 점 소수): %r" % ln.strip())
        if not h and ln.lstrip().startswith("#"):
            raise SpecError("제목 줄 꼴이 틀렸다('#' 뒤 빈칸, 줄 처음): %r" % ln.strip())
        if h:
            blocks.append({"kind": "heading", "level": len(h.group(1)), "text": h.group(2).strip()})
        elif f:
            g = HWPX_FIG.match(f.group(2).strip())
            if not g:
                raise SpecError("그림은 'hwpx:출처.hwpx#번호' 만 쓴다(그림 파일은 이 도구에서 쓰지 않는다): %r" % ln.strip())
            src = g.group(1).strip()
            first = (PureWindowsPath(src).parts[:1] or ("",))[0].casefold()
            if wd.outside(src) or Path(src).suffix.lower() not in (".hwpx", ".hwp") or first in ("bridge", ".git"):
                raise SpecError("그림 출처는 저장소 안 상대 경로 .hwpx·.hwp 여야 한다(bridge/·.git 밖): %r" % src)
            if not f.group(1).strip():
                raise SpecError("그림 캡션이 비었다: %r" % ln.strip())
            size = [float(f.group(3)), float(f.group(4))] if f.group(3) else None
            blocks.append({"kind": "figure", "caption": f.group(1).strip(), "src": src, "k": int(g.group(2)),
                           "size": size})
        elif re.match(r"^\s*[-*][ \t]+\S", ln):
            ind = len(ln) - len(ln.lstrip())
            blocks.append({"kind": "item", "level": min(ind // 2, len(wd.BULLETS) - 1),
                           "text": re.sub(r"^\s*[-*][ \t]+", "", ln).strip()})
        elif ln.startswith(">") or ln.startswith("표:") or ln.lstrip().startswith("|"):
            raise SpecError("작성 필요 메모·표는 끼워 넣기에서 쓰지 않는다: %r" % ln.strip())
        else:
            blocks.append({"kind": "para", "text": ln.strip()})
    if not blocks:
        raise SpecError("넣을 블록이 없다")
    if any(b["kind"] == "figure" and b["k"] < 1 for b in blocks):
        raise SpecError("그림 번호는 1부터다")
    for i, b in enumerate(blocks):                  # 실측한 배치만(PoC — 그림 바로 앞은 이번에 넣은 글자 문단, 검토 D1-05)
        if b["kind"] == "figure" and (i == 0 or blocks[i - 1]["kind"] == "figure"):
            raise SpecError("그림 앞에는 이번에 넣는 글자 문단이 있어야 한다(첫 블록 그림·그림 연속은 실측하지 않았다): %r"
                            % b["caption"])
    return blocks


def expected(blocks, styles):
    """블록 → 넣을 루트 문단 기대 [(종류, 스타일, 글자)] — 그림 문단은 ('object', 그림 스타일, '')."""
    out = []
    for b in blocks:
        if b["kind"] == "heading":
            out.append(("text", styles["heading"].format(level=b["level"]), b["text"]))
        elif b["kind"] == "para":
            out.append(("text", styles["para"], b["text"]))
        elif b["kind"] == "item":
            out.append(("text", styles["item"], wd.BULLETS[b["level"]] + b["text"]))
        else:
            out.append(("object", styles["figure"], ""))
    return out


# ------------------------------------------------------------------ 모델 → 비교용 꼴 (한/글 없이 시험한다)

def root_styles(x):
    """HWPML → 루트 문단(구역 차례) 스타일 이름 목록 — 그림만 든 문단은 모델에 문단 블록이 없어 HWPML 에서 읽는다."""
    root = wd_root(x)
    names = {s.get("Id"): s.get("Name") for s in root.iter("STYLE")}
    body = root.find("BODY")
    return [names.get(p.get("Style")) for sec in (body.findall("SECTION") if body is not None else [])
            for p in sec.findall("P")]


def wd_root(x):
    import xml.etree.ElementTree as ET
    x, _ = hp.clean(x)
    return ET.fromstring(re.sub("^﻿?\\s*<\\?xml[^>]*\\?>", "", x, count=1))


def roots(m, styles_by_root=None):
    """루트 문단(MovePos 번호 차례) → [(종류, 스타일, 글자)] — 글자는 공백을 지운 꼴, 스타일은 HWPML(있으면) 또는 모델."""
    paras = {b["id"]: b for b in m["body"] if b["type"] == "para" and wd.TOP.match(b["id"])}
    out = []
    for i, r in enumerate(m["roots"]):
        b = paras.get(r["id"])
        st = styles_by_root[i] if styles_by_root and i < len(styles_by_root) else (b.get("style") if b else None)
        out.append((r["kind"], st, wd._norm(b["text"]) if b else ""))
    return out


def formats(m):
    """루트 문단 → (정렬, 글자 크기들) — 모델이 푼 값(모양 번호가 아니라). 넣은 곳 밖 서식 대조용(검토 D1-04)."""
    paras = {b["id"]: b for b in m["body"] if b["type"] == "para" and wd.TOP.match(b["id"])}
    return [((paras[r["id"]].get("align"), tuple(paras[r["id"]].get("heights") or ())) if r["id"] in paras else None)
            for r in m["roots"]]


def anchor_root(m, text, styles=None):
    hits = [b for b in wd.top_paras(m) if wd._norm(b["text"]) == wd._norm(text)
            and wd.profiles.heading_pattern(styles or wd.STYLES).match(b.get("style") or "")]
    if len(hits) != 1:
        return None, "제목 %r 이 개요 문단에 %d개" % (text, len(hits))
    return wd.root_of(m, hits[0]["id"]), None


def captions(m):
    """캡션(문서 차례) → [(종류 '그림'·'표', 번호, 제목)] — 그림은 캡션 블록, 표는 표 블록의 caption."""
    out = []
    for b in m["body"]:
        if b["type"] == "table" and b.get("caption"):
            t = str(b["caption"])
        elif b["type"] == "caption":
            t = b.get("text") or ""
        else:
            continue
        g = re.match(r"^(그림|표)\s*(\d+)\s*(.*)$", t.strip(), re.S)
        out.append((g.group(1), int(g.group(2)), wd._norm(g.group(3))) if g else ("?", None, wd._norm(t)))
    return out


def figures_before(m, text, styles=None):
    """제목 text 문단 앞(본문 블록 차례)의 그림 캡션 수."""
    n = 0
    for b in m["body"]:
        if b["type"] == "para" and wd.TOP.match(b["id"]) and wd._norm(b["text"]) == wd._norm(text) \
                and wd.profiles.heading_pattern(styles or wd.STYLES).match(b.get("style") or ""):
            return n
        if b["type"] == "caption" and re.match(r"^\s*그림\s*\d", b.get("text") or ""):
            n += 1
    return n


def outside_same(before, after, at, n_new):
    if len(after) != len(before) + n_new:
        return "루트 문단 수 %d → %d (넣은 것 %d)" % (len(before), len(after), n_new)
    for i in range(at):
        if before[i] != after[i]:
            return "앞 루트 %d: %r → %r" % (i, before[i], after[i])
    for i in range(at, len(before)):
        if before[i] != after[i + n_new]:
            return "뒤 루트 %d(→%d): %r → %r" % (i, i + n_new, before[i], after[i + n_new])
    return None


def captions_shift(before, after, first_new, titles):
    k = len(titles)
    fig_b = [c for c in before if c[0] == "그림"]
    fig_a = [c for c in after if c[0] == "그림"]
    problems = []
    if [c for c in after if c[0] != "그림"] != [c for c in before if c[0] != "그림"]:
        problems.append("표 캡션이 바뀜")
    if len(fig_a) != len(fig_b) + k:
        problems.append("그림 캡션 수 %d → %d (넣은 것 %d)" % (len(fig_b), len(fig_a), k))
    else:
        want = (fig_b[:first_new - 1] + [("그림", first_new + i, wd._norm(t)) for i, t in enumerate(titles)]
                + [(g, n + k, t) for g, n, t in fig_b[first_new - 1:]])
        bad = [(i, w, a) for i, (w, a) in enumerate(zip(want, fig_a)) if w != a]
        if bad:
            problems.append("그림 캡션 %d곳 다름, 첫 곳 %r" % (len(bad), bad[0]))
    return problems


def table_texts(m):
    return [[c["text"] for c in t["cells"]] for t in hp.top_tables(m)]


def heading_levels(rows, styles=None):
    """roots() 꼴 → [(루트 번호, 수준)] — COMSAF 개요 N 문단."""
    out = []
    for i, (kind, st, _) in enumerate(rows):
        g = wd.profiles.heading_pattern(styles or wd.STYLES).match(st or "")
        if g and kind == "text":
            out.append((i, int(g.group(1))))
    return out


def numbers(levels):
    """수준 차례 → 개요 번호 글자 '4.3.4.2.6'. 수준을 건너뛰면 빈 자리는 0 이 아니라 1 로(한/글 흉내 아님 — 비교는 그대로)."""
    cnt, out = [0] * 8, []
    for lv in levels:
        cnt[lv] += 1
        for j in range(lv + 1, 8):
            cnt[j] = 0
        out.append(".".join(str(max(cnt[j], 1) if j < lv else cnt[j]) for j in range(1, lv + 1)))
    return out


def digits(v):
    return None if v is None else ".".join(re.findall(r"\d+", str(v))) or ""


def count_newnum(x):
    return len(re.findall(r"<NEWNUM\b", x or ""))


def literal_refs(m, first_new, skip_roots):
    """본문(최상위 문단·표 칸) 글자 '그림 N' (N ≥ first_new) — 새 그림 때문에 낡았을 수 있는 글자 번호. → [(곳, 글자)]."""
    out = []
    for loc, kind, t in hp.iter_locations(m):
        if kind not in ("para", "cell") or (kind == "para" and loc in skip_roots):
            continue
        for g in re.finditer(r"그림\s*(\d+)", t or ""):
            if int(g.group(1)) >= first_new:
                s, e = max(0, g.start() - 12), min(len(t), g.end() + 12)
                out.append((loc, t[s:e].replace("\n", " ")))
    return out


def picture_sizes(x):
    """HWPML → 루트 문단 번호 → [그림 (가로, 세로) mm] (그 문단에 바로 든 그림)."""
    root = wd_root(x)
    body = root.find("BODY")
    out, i = {}, 0
    for sec in (body.findall("SECTION") if body is not None else []):
        for p in sec.findall("P"):
            for pic in (e for t in p.findall("TEXT") for e in t if e.tag == "PICTURE"):
                sz = pic.find("SHAPEOBJECT/SIZE")
                if sz is not None and sz.get("Width", "").isdigit():
                    out.setdefault(i, []).append((round(int(sz.get("Width")) / MM, 1), round(int(sz.get("Height")) / MM, 1)))
            i += 1
    return out


def caption_styles(x):
    """HWPML → 루트 문단 번호 → [그 문단 그림 캡션 첫 문단 스타일 이름]."""
    root = wd_root(x)
    names = {s.get("Id"): s.get("Name") for s in root.iter("STYLE")}
    body = root.find("BODY")
    out, i = {}, 0
    for sec in (body.findall("SECTION") if body is not None else []):
        for p in sec.findall("P"):
            for pic in (e for t in p.findall("TEXT") for e in t if e.tag == "PICTURE"):
                cp = pic.find("SHAPEOBJECT/CAPTION/PARALIST/P")
                out.setdefault(i, []).append(names.get(cp.get("Style")) if cp is not None else None)
            i += 1
    return out


# ------------------------------------------------------------------ 한/글 단계

def move(s, root, pos=0):
    if not s.s.call("MovePos", s.hwp.MovePos, 0, root, pos):
        raise api.EditFailed("MovePos(0,%d,%d) 실패" % (root, pos))


def end_of_para(s):
    s.s.call("MovePos", s.hwp.MovePos, 7, 0, 0)               # moveEndOfPara


def new_para(s, idx, style, text=None):
    """새 문단 + 스타일 두 번(F-109 — 앞 문단의 직접 글자 모양을 지운다, 같은 스타일 다시 입힘 '덮어 쓸까요?'는 자동 '예')."""
    s.s.run("BreakPara")
    wd.apply_style_clean(s, idx, style, False, True)
    if text:
        wd.insert_text(s, text)


def insert_file(s, path):
    return bool(s.s.action("InsertFile", "InsertFile", FileName=str(path), FileFormat="HWPX", FileArg="",
                           KeepSection=0, KeepCharshape=1, KeepParashape=1, KeepStyle=0, MoveNextPos=0))


def keep_only_picture(s, first, last, k):
    """끼운 범위 루트 [first, last] 에서 k 번째 그림 문단만 남긴다(PoC I1 — 가정대로) → (그림 문단 루트, 기록).
    뒤: 그림 문단 끝 → last 끝까지 선택해 지운다(다음 문단 = 앵커 쪽은 그대로). 앞: first-1(앞에 넣은 문단) 끝 → 그림 앞 문단 끝."""
    m = s.model(refresh=True)
    kinds = [r["kind"] for r in m["roots"]]
    pics = [i for i in range(first, last + 1) if kinds[i] == "object"]
    rec = {"range": [first, last], "pictures_at": pics}
    if len(pics) < k:
        raise api.EditFailed("출처를 끼운 범위에 그림 문단이 %d개뿐이다(%d번째가 필요)" % (len(pics), k))
    p = pics[k - 1]
    if p < last:
        move(s, p)
        end_of_para(s)
        for _ in range(last - p):
            s.s.run("MoveSelNextParaBegin")
        s.s.run("MoveSelParaEnd")
        s.s.run("Delete")
    if p > first:
        move(s, first - 1)
        end_of_para(s)
        for _ in range(p - first):
            s.s.run("MoveSelNextParaBegin")
        s.s.run("MoveSelParaEnd")
        s.s.run("Delete")
        p = first
    s._model = None
    return p, rec


def restyle_caption(s, idx, root, style):
    """그림 문단 처음에서 캡션 넣기 → 기존 캡션 안(PoC: 캐럿 목록 ≠ 0) → 캡션 스타일 두 번(F-109) → CloseEx."""
    move(s, root)
    s.s.run("ShapeObjAttachCaption")
    pos = wd.get_pos(s)
    if pos is None or pos[0] == 0:
        raise api.EditFailed("그림 캡션 안으로 들어가지 못했다(GetPos %s)" % (pos,))
    wd.apply_style_clean(s, idx, style, False, True)
    s.s.run("CloseEx")
    return list(pos)


def read_headings(s, rows, styles=None):
    return {i: wd.heading_string(s, i) for i, _ in heading_levels(rows, styles)}


def insert(s, target, blocks, before, out, log=print, styles=None, protection="preserve"):
    """대상을 열어 넣고 확인해 저장 → 기록 dict (rec["ok"])."""
    styles = dict(styles or wd.STYLES)
    if protection not in ("preserve", "required"):
        raise SpecError("protection must be preserve or required")
    if any(b["kind"] == "figure" and hs.head_kind(ROOT / b["src"]) == "DOCURAY" for b in blocks):
        protection = "required"
    rec = {"target": str(target), "out": str(out), "before": before, "ok": False, "warnings": []}
    want = expected(blocks, styles)
    titles = [b["caption"] for b in blocks if b["kind"] == "figure"]
    rec["plan"] = {"blocks": len(blocks), "headings": sum(1 for b in blocks if b["kind"] == "heading"),
                   "figures": len(titles)}
    s.open(target)
    m0 = s.model()
    x0 = s.last_hwpml or ""
    idx = wd.style_index(m0)
    missing = sorted({w[1] for w in want if w[1] not in idx})
    if missing:
        raise SpecError("대상 문서에 스타일이 없다: %s" % missing)
    if styles["caption"] not in idx:
        raise SpecError("대상 문서에 캡션 스타일이 없다: %s" % styles["caption"])
    a0, why = anchor_root(m0, before, styles)
    if a0 is None:
        raise SpecError(why)
    if a0 == 0 or m0["roots"][a0 - 1]["kind"] == "table":
        raise SpecError("앞 문단이 없거나 표다 — 그 자리에 넣는 길은 실측하지 않았다(루트 %d)" % (a0 - 1))
    b0 = roots(m0, root_styles(x0))
    c0 = captions(m0)
    first_new = figures_before(m0, before, styles) + 1
    h0 = read_headings(s, b0, styles)
    rec.update({"anchor_root": a0, "first_new_figure": first_new})
    old = wd.msgbox_mode(s, wd.MSGBOX_YES)                      # 같은 스타일 다시 입힘 '덮어 쓸까요?' → 예 (D-039)
    steps = []
    try:
        move(s, a0 - 1)
        end_of_para(s)
        for b, w in zip(blocks, want):
            if b["kind"] != "figure":
                new_para(s, idx, w[1], w[2])
                continue
            new_para(s, idx, styles["figure"])
            ab, _ = anchor_root(s.model(refresh=True), before, styles)
            ok = insert_file(s, ROOT / b["src"])
            aa, why = anchor_root(s.model(refresh=True), before, styles)
            if not ok or aa is None:
                raise api.EditFailed("출처 끼워 넣기 실패(%s, 반환 %s, %s)" % (b["src"], ok, why))
            p, info = keep_only_picture(s, ab - 1, aa - 1, b["k"])
            move(s, p)
            wd.apply_style_clean(s, idx, styles["figure"], False, True)
            info["caption_pos"] = restyle_caption(s, idx, p, styles["caption"])
            move(s, p)
            end_of_para(s)
            steps.append(dict(info, src=b["src"], k=b["k"], picture_root=p, inserted_roots=aa - ab))
    finally:
        if old is not None:
            wd.msgbox_mode(s, old)
    rec["steps"] = steps
    m = s.model(refresh=True)
    x = s.last_hwpml or ""
    b1 = roots(m, root_styles(x))
    added = len(b1) - len(b0)
    problems = []
    diff = outside_same(b0, b1, a0, len(want))
    if diff:
        problems.append("넣은 곳 밖이 바뀌었다: %s" % diff)
    elif len(b1) == len(b0) + len(want):
        diff = outside_same(formats(m0), formats(m), a0, len(want))
        if diff:
            problems.append("넣은 곳 밖 서식(정렬·글자 크기)이 바뀌었다: %s" % diff)
    new_ids = {r["id"] for r in m["roots"][a0:a0 + len(want)]}
    fmt = [x for x in wd.size_mismatch(m, -1) + wd.align_mismatch(m, -1) if x[0] in new_ids]
    if fmt:
        rec["warnings"].append("넣은 문단 글자 크기·정렬이 스타일과 다르다 %d곳: %r" % (len(fmt), fmt[:3]))
    got = b1[a0:a0 + len(want)]
    norm_want = [(k, st, wd._norm(t)) for k, st, t in want]
    bad = [(i, w, g) for i, (w, g) in enumerate(zip(norm_want, got)) if w != g]
    if bad or added != len(want):
        problems.append("넣은 문단이 명세와 다르다(%d곳, 넣은 수 %d/%d): %r" % (len(bad), added, len(want), bad[:2]))
    cs = caption_styles(x)
    sizes = picture_sizes(x)
    figs = [a0 + i for i, w in enumerate(want) if w[0] == "object"]
    for r, b in zip(figs, (b for b in blocks if b["kind"] == "figure")):
        if cs.get(r) != [styles["caption"]]:
            problems.append("그림 캡션 스타일(루트 %d): %r" % (r, cs.get(r)))
        sz = sizes.get(r) or []
        if b["size"] and sz and max(abs(sz[0][0] - b["size"][0]), abs(sz[0][1] - b["size"][1])) > SIZE_TOL_MM:
            rec["warnings"].append("그림 크기가 명세와 다르다(루트 %d): %s mm, 명세 %s" % (r, sz[0], b["size"]))
    rec["picture_sizes_mm"] = [sizes.get(r) for r in figs]
    c1 = captions(m)
    problems += captions_shift(c0, c1, first_new, titles)
    if table_texts(m) != table_texts(m0):
        problems.append("표 칸 글자가 바뀌었다")
    for kk in ("headers", "footers"):
        if [h.get("text") for h in m[kk]] != [h.get("text") for h in m0[kk]]:
            problems.append("%s 가 바뀌었다" % ("머리말" if kk == "headers" else "꼬리말"))
    n0, n1 = count_newnum(x0), count_newnum(x)
    if n0 != n1:
        problems.append("새 번호 조판 수 %d → %d" % (n0, n1))
    sc = wd.styles_changed(m0, m)
    rec["styles_changed"] = sc
    if [n for n in sc if not n.startswith("+")]:
        problems.append("기존 스타일 정의가 바뀌었다: %s" % [n for n in sc if not n.startswith("+")])
    if [n for n in sc if n.startswith("+")]:
        rec["warnings"].append("스타일이 더해졌다(출처 문서 스타일 — 쓰는 문단 없음): %s" % [n[1:] for n in sc if n.startswith("+")])
    # 제목 개요 번호: 쓰기 전 이미 수준 셈과 다른 제목은 빼고(경고), 나머지는 쓴 뒤 수준 셈과 같아야 한다
    lv0, lv1 = heading_levels(b0, styles), heading_levels(b1, styles)
    exp0 = dict(zip([i for i, _ in lv0], numbers([lv for _, lv in lv0])))
    exp1 = dict(zip([i for i, _ in lv1], numbers([lv for _, lv in lv1])))
    pre = {i for i, v in h0.items() if v is not None and digits(v) != exp0[i]}
    if pre:
        rec["warnings"].append("쓰기 전에 이미 수준 셈과 다른 제목 %d개 — 번호 대조에서 뺐다" % len(pre))
    h1 = read_headings(s, b1, styles)
    shift = lambda i: i if i < a0 else i + len(want)            # noqa: E731 — 쓰기 전 루트 → 쓴 뒤 루트
    skip = {shift(i) for i in pre}
    unread = [i for i, v in h1.items() if v is None]
    mism = [(i, h1[i], exp1[i]) for i in h1 if i not in skip and h1[i] is not None and digits(h1[i]) != exp1[i]]
    rec["headings"] = {"count": len(h1), "unread": len(unread), "mismatch": mism[:5],
                       "new": {i: h1.get(i) for i in range(a0, a0 + len(want)) if i in h1}}
    if mism:
        problems.append("제목 개요 번호가 수준 셈과 다르다 %d곳: %r" % (len(mism), mism[:3]))
    new_unread = [i for i in unread if a0 <= i < a0 + len(want)]
    if new_unread:
        problems.append("넣은 제목의 개요 번호를 읽지 못했다(루트 %s) — 번호 대조 없이 저장하지 않는다" % new_unread)
    if len(unread) > len(new_unread):
        rec["warnings"].append("개요 번호를 못 읽은 제목 %d개(기존 제목)" % (len(unread) - len(new_unread)))
    moved = [(h0[i], h1.get(shift(i))) for i in h0 if i not in pre and h0[i] is not None
             and digits(h0[i]) != digits(h1.get(shift(i)))]
    if moved:
        rec["warnings"].append("번호가 바뀐 제목 %d개 — 본문 글자 절 인용 확인: %r" % (len(moved), moved[:5]))
    lit = literal_refs(m, first_new, {r["id"] for r in m["roots"][a0:a0 + len(want)]})
    rec["literal_refs"] = lit
    if lit:
        rec["warnings"].append("새 그림 번호(%d) 이상을 가리키는 본문 글자 '그림 N' %d곳 — 번호가 %d 밀렸다(목차 줄 포함, 고칠 곳 후보)"
                               % (first_new, len(lit), len(titles)))
    rec["check"] = {"added": added, "first_new_figure": first_new, "captions": [len(c0), len(c1)], "newnum": [n0, n1]}
    if problems:
        rec["error"] = "; ".join(problems)
        return rec
    try:
        sv = s.save(out=out, protection=protection)
    except api.PlaintextSaved as e:
        rec["save"] = e.rec
        rec["error"] = "DRM 미적용으로 저장됐다(%s) — 반출 금지: %s" % (e.rec.get("head"), out)
        rec["code"] = 3
        return rec
    rec["save"] = {k: sv.get(k) for k in ("out", "head", "protected", "reopen", "source_unchanged")}
    if not sv.get("reopen") or sv.get("source_unchanged") is False:
        bad = Path(out).with_name(Path(out).stem + ".unverified.hwpx")
        try:
            Path(out).replace(bad)                              # 확인 안 된 파일을 요청한 이름에 남기지 않는다(D1-07)
            rec["save"]["moved_to"] = str(bad)
        except OSError as e:
            rec["save"]["move_error"] = str(e)
        rec["error"] = "저장 확인 실패 %s" % rec["save"]
        return rec
    rec["ok"] = True
    return rec


def write_report(rec, path, started):
    md = ["# 끼워 넣기 보고", "",
          "- 실행: %s · `tools/doc-writer/insert_doc.py` · 명세 `%s`" % (started.isoformat(timespec="seconds"), rec.get("spec")),
          "- 대상 `%s` → 출력 `%s` · 앞 제목 '%s' · 결과 **%s**" % (
              rec.get("target"), rec.get("out"), rec.get("before"),
              "OK" if rec.get("ok") else "FAIL: " + rm.esc(rec.get("error", ""))),
          "- 블록 %s · 제목 %s · 그림 %s · 새 그림 첫 번호 %s" % tuple(
              [(rec.get("plan") or {}).get(k, "-") for k in ("blocks", "headings", "figures")] + [rec.get("first_new_figure", "-")]),
          ""]
    if rec.get("warnings"):
        md += ["## 경고", ""] + ["- %s" % rm.esc(w) for w in rec["warnings"]] + [""]
    if rec.get("literal_refs"):
        md += ["## 본문 글자 번호 (고칠 곳 후보)", "", "| 곳 | 글자 |", "|---|---|"]
        md += ["| %s | %s |" % (a, rm.esc(b)) for a, b in rec["literal_refs"]] + [""]
    md += ["## 자세히 (JSON)", "", "```json", json.dumps(rec, ensure_ascii=False, indent=1, default=str), "```", ""]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md), encoding="utf-8")
    return path


def build_parser():
    """명령줄 — 브리지(office-drm-bridge insert 연산)가 만드는 명령줄을 시험이 이 파서로 확인한다."""
    ap = argparse.ArgumentParser(description="이미 있는 문서의 정한 제목 앞에 블록 끼워 넣기 → 새 파일(.hwpx)")
    ap.add_argument("target")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--profile", default="technical-report")
    ap.add_argument("--protection", choices=("preserve", "required"), default="preserve")
    return ap


def main(argv=None):
    from _console import configure_console
    configure_console()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    started = datetime.datetime.now()
    target, out = Path(args.target).resolve(), Path(args.out).resolve()
    report = Path(args.report) if args.report else out.with_name(out.stem + ".insert_report.md")
    rec = {"spec": args.spec, "target": str(target), "out": str(out), "before": args.before, "ok": False,
           "error": "실행 중 — 이 보고가 남았으면 끝나지 않았다(콘솔의 오류를 본다)"}
    write_report(rec, report, started)
    code = 2
    try:
        if not target.is_file():
            raise SpecError("대상이 없다: %s" % target)
        if out.suffix.lower() != ".hwpx" or out == target:
            raise SpecError("출력은 대상과 다른 .hwpx 여야 한다: %s" % out)
        if out.exists():
            raise SpecError("출력 파일이 이미 있다 — 덮어쓰지 않는다: %s" % out)
        try:
            text = Path(args.spec).read_bytes().decode("utf-8-sig")
        except (OSError, UnicodeDecodeError) as e:
            raise SpecError("명세를 읽지 못했다(UTF-8): %s" % e)
        blocks = parse_blocks(text)
        try:
            selected_styles = wd.profiles.resolve_styles(args.profile, root=ROOT)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise SpecError("프로파일을 읽지 못했다: %s" % exc) from exc
        for b in blocks:
            if b["kind"] == "figure" and not (ROOT / b["src"]).is_file():
                raise SpecError("그림 출처가 없다: %s" % b["src"])
        rec.pop("error")
        with api.HwpxSession(timeout=args.timeout, log=print) as s:
            rec = insert(s, target, blocks, args.before, out, log=print,
                         styles=selected_styles, protection=args.protection)
            rec["spec"] = args.spec
            code = 0 if rec["ok"] else rec.get("code", 1)
    except hs.HwpError as e:
        rec["error"] = "%s: %s" % (type(e).__name__, e)
        code = e.code
    print("%s — %s" % ("OK" if rec.get("ok") else "FAIL", rec.get("error", rec.get("out"))))
    print("보고: %s" % write_report(rec, report, started))
    return code


if __name__ == "__main__":
    sys.exit(main())
