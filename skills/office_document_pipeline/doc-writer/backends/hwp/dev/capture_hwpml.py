#!/usr/bin/env python3
"""HWPML 스키마 채취 (설계 §7 단계 1) — 사용자 PC에서 한 번 실행한다.

1) 합성 문서: 내용을 아는 문서를 COM으로 만들어(제목·줄바꿈·탭·누름틀·각주·메모·표·셀 필드·
   셀 안 여러 문단·중첩 표·가로/세로 병합·머리말·꼬리말) HWPML2X를 그대로 채취한다.
   → tests/fixtures/synthetic_hwpml.md  (파서 시험의 정답지. 실문서 내용 없음)
   → _drmtest/syn_fixture.hwpx          (한/글이 저장 — DocuRay 적용. 이후 fill/replace 실측용)
2) 실제 템플릿: 요소·속성 이름과 개수, 짧은 영숫자 속성값 분포, 스타일 이름만 채취한다.
   본문 글자(CHAR)·필드 이름·그림 데이터는 기록하지 않는다. 원본은 열기만 하고 저장하지 않는다.
   → tests/fixtures/template_vocab.md

    python tools/hwpx-drm/dev/capture_hwpml.py
    python tools/hwpx-drm/dev/capture_hwpml.py --skip-vocab
    python tools/hwpx-drm/dev/capture_hwpml.py --vocab reference/template.hwpx

종료코드: 0 전부 성공 / 1 일부 단계 실패(결과 .md 참고) / 2 사전조건 / 5 시간초과 / 6 COM 생성 실패
"""
import argparse
import datetime
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = next((p for p in SKILL.parents if (p / "tools" / "hwpx-drm").resolve() == SKILL),
            Path.cwd())
sys.path.insert(0, str(SKILL / "scripts"))
import hwp_session as hs                     # noqa: E402

FIXTURES = SKILL / "tests" / "fixtures"
FENCE = "````"


# ------------------------------------------------------------------ 한/글 동작 보조

def act(s, name, setid=None, **items):
    """setid 가 없으면 Run(name) - 반환값 없음(void). 있으면 HAction 실행(BOOL, SetItem 대체 포함)."""
    if setid is None:
        return s.run(name)
    return s.action(name, setid, **items)


def text(s, t):
    return act(s, "InsertText", "InsertText", Text=t)


def table(s, rows, cols):
    return act(s, "TableCreate", "TableCreation", Rows=rows, Cols=cols, WidthType=0, HeightType=0)


def style(s, index):
    return act(s, "Style", "Style", Apply=index)


# ------------------------------------------------------------------ 1) 합성 문서

def build_synthetic(s):
    """(단계 이름, 함수) 목록. 실패한 단계는 기록하고 다음으로 간다 — 채취가 목적이다."""
    h = s.hwp
    para = lambda: act(s, "BreakPara")            # noqa: E731
    out = lambda: (act(s, "MoveRootList"), act(s, "MoveDocEnd"))  # noqa: E731

    def h1():
        style(s, 2)                                # 기본 스타일 목록의 '개요 1' 위치 (실제 이름은 HWPML 에서 확인)
        text(s, "SYN_H1 개요 제목")
        para()
        style(s, 0)                                # 바탕글

    def p1():
        text(s, "SYN_P1 본문 첫 문단")
        act(s, "BreakLine")
        text(s, "SYN_P1_LINE2\tSYN_P1_TAB")
        para()

    def clickhere():
        text(s, "SYN_P2 누름틀: ")
        ok = s.call("CreateField", h.CreateField, "SYN_GUIDE", "SYN_MEMO", "SYN_FIELD_A")
        act(s, "MoveDocEnd")
        para()
        return ok

    def footnote():
        text(s, "SYN_P3 각주 기준")
        act(s, "InsertFootnote")
        text(s, "SYN_FOOTNOTE")
        act(s, "CloseEx")
        act(s, "MoveDocEnd")
        para()

    def memo():
        text(s, "SYN_P4 메모 기준")
        act(s, "InsertFieldMemo")
        text(s, "SYN_MEMO_TEXT")
        act(s, "CloseEx")
        act(s, "MoveDocEnd")
        para()

    def table_a():
        # 3x3: (0,2) 셀 필드, (1,0) 셀 안 두 문단, (2,0) 셀 안 중첩 표 1x2
        text(s, "SYN_TA 표 A 앞 문단")
        para()
        table(s, 3, 3)
        right = lambda: act(s, "TableRightCell")   # noqa: E731
        text(s, "SYN_A_R0C0"); right()
        text(s, "SYN_A_R0C1"); right()
        s.call("SetCurFieldName", h.SetCurFieldName, "SYN_CELL_02", 1, "", "")
        text(s, "SYN_A_R0C2"); right()
        text(s, "SYN_A_R1C0"); para(); text(s, "SYN_A_R1C0_P2"); right()
        text(s, "SYN_A_R1C1"); right()
        text(s, "SYN_A_R1C2"); right()
        text(s, "SYN_A_R2C0"); para()
        table(s, 1, 2)
        text(s, "SYN_N_R0C0"); right()
        text(s, "SYN_N_R0C1")
        act(s, "MoveParentList")                   # 중첩 표 밖(바깥 셀)으로
        right()
        text(s, "SYN_A_R2C1"); right()
        text(s, "SYN_A_R2C2")
        out()
        para()

    def table_b():
        # 3x3 채운 뒤 병합: (0,0)+(0,1) 가로, (1,2)+(2,2) 세로
        text(s, "SYN_TB 표 B 앞 문단")
        para()
        table(s, 3, 3)
        for r in range(3):
            for c in range(3):
                text(s, "SYN_B_R%dC%d" % (r, c))
                if (r, c) != (2, 2):
                    act(s, "TableRightCell")
        act(s, "TableUpperCell"); act(s, "TableUpperCell")
        act(s, "TableLeftCell"); act(s, "TableLeftCell")          # (0,0)
        act(s, "TableCellBlock"); act(s, "TableCellBlockExtend"); act(s, "TableRightCell")
        act(s, "TableMergeCell"); act(s, "Cancel")
        act(s, "TableRightCell"); act(s, "TableLowerCell")          # (1,2)
        act(s, "TableCellBlock"); act(s, "TableCellBlockExtend"); act(s, "TableLowerCell")
        act(s, "TableMergeCell"); act(s, "Cancel")
        out()
        para()                                     # 병합 성공 여부는 Run 반환값이 아니라 HWPML 구조로 본다 (F-062)

    def header_footer():
        # HHeaderFooter 래퍼에 HeaderFooterCtrlType 속성이 없다 -> s.action 이 HSet.SetItem 으로 넣는다 (F-063)
        res = {}
        for kind, label in ((0, "SYN_HEADER"), (1, "SYN_FOOTER")):
            ok = act(s, "HeaderFooter", "HeaderFooter", HeaderFooterCtrlType=kind, Type=0)
            res[label] = ok
            if ok:                                 # 실패했는데 쓰면 표지 글자가 본문에 들어간다
                text(s, label)
                act(s, "CloseEx")
            act(s, "MoveDocEnd")
        res["setitem"] = list(s.setitem_used)
        return res

    def end():
        text(s, "SYN_END 마지막 문단")
        s.call("PutFieldText", h.PutFieldText, "SYN_FIELD_A", "SYN_FIELD_A_VALUE")

    return [("h1_style", h1), ("p1_linebreak_tab", p1), ("clickhere_field", clickhere),
            ("footnote", footnote), ("memo", memo), ("table_a_nested_cellfield", table_a),
            ("table_b_merge", table_b), ("header_footer", header_footer), ("end_putfield", end)]


EXPECT = {   # 합성 문서가 정말 그 구조로 만들어졌는지 - 동작 반환값이 아니라 HWPML 로 확인 (F-062)
    "clickhere_named": "FIELDBEGIN Type=Clickhere Name=SYN_FIELD_A",
    "cell_field_named": "CELL Name=SYN_CELL_02",
    "footnote": "FOOTNOTE 안에 SYN_FOOTNOTE",
    "memo": "FIELDBEGIN Type=Memo 안에 SYN_MEMO_TEXT",
    "nested_table": "CELL 안 TABLE 안에 SYN_N_R0C0",
    "merge_h": "ColSpan=2 셀에 SYN_B_R0C0",
    "merge_v": "RowSpan=2 셀에 SYN_B_R1C2",
    "header": "HEADER 안에 SYN_HEADER",
    "footer": "FOOTER 안에 SYN_FOOTER",
}


def check_synthetic(x):
    import xml.etree.ElementTree as ET
    try:
        r = ET.fromstring(x.encode("utf-8"))
    except Exception as e:
        d = {k: False for k in EXPECT}
        d["parse_error"] = type(e).__name__
        return d

    def txt(e):
        return "".join(e.itertext())

    def any_(tag, pred):
        return any(pred(e) for e in r.iter(tag))
    return {
        "clickhere_named": any_("FIELDBEGIN", lambda e: e.get("Type") == "Clickhere" and e.get("Name") == "SYN_FIELD_A"),
        "cell_field_named": any_("CELL", lambda e: e.get("Name") == "SYN_CELL_02"),
        "footnote": any_("FOOTNOTE", lambda e: "SYN_FOOTNOTE" in txt(e)),
        "memo": any_("FIELDBEGIN", lambda e: e.get("Type") == "Memo" and "SYN_MEMO_TEXT" in txt(e)),
        "nested_table": any_("CELL", lambda e: any("SYN_N_R0C0" in txt(t) for t in e.iter("TABLE"))),
        "merge_h": any_("CELL", lambda e: e.get("ColSpan") == "2" and "SYN_B_R0C0" in txt(e)),
        "merge_v": any_("CELL", lambda e: e.get("RowSpan") == "2" and "SYN_B_R1C2" in txt(e)),
        "header": any_("HEADER", lambda e: "SYN_HEADER" in txt(e)),
        "footer": any_("FOOTER", lambda e: "SYN_FOOTER" in txt(e)),
    }


def capture_synthetic(args, log):
    rec = {"steps": [], "ok": False}
    with hs.HwpSession(timeout=args.timeout, allow_running=args.allow_running, log=log) as s:
        rec.update(hwp_version=s.version, module_ok=s.module_ok)
        s.clear()
        for name, fn in build_synthetic(s):
            t = time.time()
            try:
                r = fn()
                rec["steps"].append({"step": name, "ok": True, "result": r if isinstance(r, (bool, dict)) else None,
                                     "sec": round(time.time() - t, 2)})
            except hs.TimeoutKilled:
                raise
            except Exception as e:
                rec["steps"].append({"step": name, "ok": False, "error": ("%s: %s" % (type(e).__name__, e))[:200]})
            log("  [%s] %s" % (name, "OK" if rec["steps"][-1]["ok"] else "FAIL " + rec["steps"][-1].get("error", "")))
        x = s.export_hwpml()
        t = s.export_text()
        rec["checks"] = check_synthetic(x)
        rec["fields"] = {k: [n for n in str(s.call("GetFieldList", s.hwp.GetFieldList, 0, opt) or "").split("\x02") if n]
                         for k, opt in (("all", 0), ("cell", 1), ("clickhere", 2))}
        out = Path(args.work).resolve() / "syn_fixture.hwpx"
        try:
            out.unlink()
        except FileNotFoundError:
            pass
        rec["saved"] = bool(s.call("SaveAs", s.hwp.SaveAs, str(out), "HWPX", ""))
        rec["saved_head"] = hs.head_kind(out)
        rec["saved_path"] = str(out)
        rec["hwpml_len"] = len(x)
        rec["ok"] = bool(x) and all(st["ok"] for st in rec["steps"]) and all(
            rec["checks"].get(k) is True for k in EXPECT)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    md = ["# 합성 문서 HWPML 채취 (정답지)", "",
          "- 채취: %s · 한/글 %s · 보안모듈 %s" % (datetime.datetime.now().isoformat(timespec="seconds"),
                                              rec.get("hwp_version"), rec.get("module_ok")),
          "- 실문서 내용 없음 — 모든 글자는 `SYN_` 표지. 구성은 `dev/capture_hwpml.py` build_synthetic()",
          "- 저장본: `%s` (선두 %s)" % (rec.get("saved_path"), rec.get("saved_head")), "",
          "## 구성 단계", "", "| 단계 | 결과 | 비고 |", "|---|---|---|"]
    for st in rec["steps"]:
        md.append("| %s | %s | %s |" % (st["step"], "OK" if st["ok"] else "FAIL",
                                       json.dumps(st.get("result") or st.get("error") or "", ensure_ascii=False)))
    md += ["", "## 구조 확인 (HWPML 기준)", "", "| 항목 | 기대 | 결과 |", "|---|---|---|"]
    md += ["| %s | %s | %s |" % (k, v, "OK" if rec["checks"].get(k) is True else "MISSING") for k, v in EXPECT.items()]
    md += ["", "## 필드 목록 (GetFieldList)", "", "```json", json.dumps(rec["fields"], ensure_ascii=False), "```", "",
           "## TEXT 내보내기", "", FENCE + "text", t, FENCE, "",
           "## HWPML2X (선언 UTF-8 로 교체됨)", "", FENCE + "xml", x, FENCE, ""]
    (FIXTURES / "synthetic_hwpml.md").write_text("\n".join(md), encoding="utf-8")
    return rec


# ------------------------------------------------------------------ 2) 실문서 어휘

_TAG = re.compile(r"<([A-Za-z][A-Za-z0-9_]*)((?:\s+[A-Za-z_][\w.:-]*\s*=\s*\"[^\"]*\")*)\s*/?>")
_ATTR = re.compile(r'([A-Za-z_][\w.:-]*)\s*=\s*"([^"]*)"')
_SHORT = re.compile(r"[A-Za-z0-9_.+-]{0,12}")
_NO_VALUE = {"Name", "Command", "EngName", "InstId", "InstID", "FieldId"}


_TOK = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9_]*)\b[^>]*?(/?)>")


def vocab(x):
    """요소·속성 이름과 개수, 짧은 영숫자 값 분포, 부모>자식 요소 쌍. 본문·이름·그림 데이터는 담지 않는다."""
    elems = Counter()
    attrs = defaultdict(Counter)
    vals = defaultdict(lambda: defaultdict(Counter))
    for m in _TAG.finditer(x):
        tag = m.group(1)
        elems[tag] += 1
        for a, v in _ATTR.findall(m.group(2)):
            attrs[tag][a] += 1
            if a not in _NO_VALUE and _SHORT.fullmatch(v):   # 이름·명령은 짧은 영숫자라도 값을 남기지 않는다
                vals[tag][a][v] += 1
    edges, stack = Counter(), []
    for m in _TOK.finditer(x):               # 요소 이름만 따라간다 (구조 확인용: PARALIST 를 가진 부모 등)
        close, tag, selfclose = m.groups()
        if close:
            if stack and stack[-1] == tag:
                stack.pop()
            continue
        edges["%s>%s" % (stack[-1] if stack else "", tag)] += 1
        if not selfclose:
            stack.append(tag)
    styles = re.findall(r"<STYLE\b[^>]*?\bName=\"([^\"]*)\"", x)
    return elems, attrs, vals, styles, edges


def capture_vocab(args, log):
    files = [Path(p) for p in args.vocab] if args.vocab else sorted(
        (ROOT / "reference" / "template_backup").glob("*.hwpx"), key=lambda p: p.stat().st_size)
    per, U_e, U_a, U_v, styles_all, failed = [], Counter(), defaultdict(Counter), defaultdict(lambda: defaultdict(Counter)), {}, 0
    U_ed = Counter()
    s = None                                   # 한 세션으로 모든 문서를 연다 - 세션을 매번 새로 띄우면
    try:                                       # 앞 세션의 Hwp.exe 가 끝나기 전에 다음이 시작돼 거부된다 (F-061)
        for f in files:
            row = {"file": f.name, "size": f.stat().st_size if f.exists() else None}
            try:
                if s is None:
                    s = hs.HwpSession(timeout=args.timeout, allow_running=args.allow_running, log=log).start()
                s.clear()                      # 앞 문서 버림 (원본은 저장하지 않는다)
                t = time.time(); s.open(f); row["t_open"] = round(time.time() - t, 2)
                t = time.time(); x = s.export_hwpml(); row["t_export"] = round(time.time() - t, 2)
                row["hwpml_len"] = len(x)
                t = time.time()
                e, a, v, st, ed = vocab(x)
                del x
                row["t_vocab"] = round(time.time() - t, 2)
                row.update(TABLE=e.get("TABLE", 0), ROW=e.get("ROW", 0), CELL=e.get("CELL", 0), P=e.get("P", 0),
                           SECTION=e.get("SECTION", 0), elements=len(e))
                U_e.update(e)
                for tag in a:
                    U_a[tag].update(a[tag])
                    for at in v[tag]:
                        U_v[tag][at].update(v[tag][at])
                styles_all[f.name] = st
                U_ed.update(ed)
                row["ok"] = True
            except hs.HwpError as e:
                row.update(ok=False, error="%s: %s" % (type(e).__name__, e), code=e.code)
                failed += 1
                if isinstance(e, hs.TimeoutKilled) and s is not None:
                    s.close()                  # 죽은 세션은 버리고 다음 문서에서 새로 띄운다
                    s = None
            except Exception as e:
                row.update(ok=False, error="%s: %s" % (type(e).__name__, str(e)[:200]))
                failed += 1
            per.append(row)
            log("  [vocab] %s %s" % (f.name, "OK" if row.get("ok") else "FAIL " + row.get("error", "")))
    finally:
        if s is not None:
            s.close()
    union = {tag: {"count": U_e[tag],
                   "attrs": {at: {"count": c, "top_values": dict(U_v[tag][at].most_common(8)) or None}
                             for at, c in sorted(U_a[tag].items())}}
             for tag in sorted(U_e)}
    cols = ["file", "size", "t_open", "t_export", "t_vocab", "hwpml_len", "SECTION", "P", "TABLE", "ROW", "CELL", "elements", "ok"]
    md = ["# 실제 템플릿 HWPML 어휘 (본문 없음)", "",
          "- 채취: %s · 원본은 열기만 하고 저장하지 않음" % datetime.datetime.now().isoformat(timespec="seconds"),
          "- 담은 것: 요소·속성 이름과 개수, 12자 이하 영숫자 속성값 분포(상위 8), 부모>자식 요소 쌍, STYLE 이름. 담지 않은 것: 본문 글자, 필드 이름, 그림 데이터", "",
          "## 문서별", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in per:
        cells = [("OK" if r.get("ok") else "FAIL: " + r.get("error", "")) if c == "ok" else str(r.get(c, "")) for c in cols]
        md.append("| " + " | ".join(x.replace("|", "/") for x in cells) + " |")
    md += ["", "## 스타일 이름 (문서별)", "", "```json", json.dumps(styles_all, ensure_ascii=False, indent=1), "```", "",
           "## 부모>자식 요소 쌍 (구조)", "", "```json", json.dumps(dict(sorted(U_ed.items())), ensure_ascii=False, indent=0), "```", "",
           "## 합친 어휘", "", "```json", json.dumps(union, ensure_ascii=False, indent=1), "```", ""]
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / "template_vocab.md").write_text("\n".join(md), encoding="utf-8")
    return per, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description="HWPML 스키마 채취 (합성 문서 + 실제 템플릿 어휘)")
    ap.add_argument("--vocab", nargs="*", help="어휘를 채취할 hwpx (기본: reference/template_backup/*.hwpx 전부, 작은 것부터)")
    ap.add_argument("--skip-synthetic", action="store_true")
    ap.add_argument("--skip-vocab", action="store_true")
    ap.add_argument("--work", default=str(ROOT / "_drmtest"))
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--allow-running", action="store_true")
    args = ap.parse_args(argv)
    Path(args.work).mkdir(parents=True, exist_ok=True)
    log = print
    code = 0
    try:
        if not args.skip_synthetic:
            log("[synthetic] 합성 문서 구성·채취")
            rec = capture_synthetic(args, log)
            log("[synthetic] %s  hwpml %s자, 저장 %s (%s)" % ("OK" if rec["ok"] else "PARTIAL", rec.get("hwpml_len"),
                                                        rec.get("saved"), rec.get("saved_head")))
            if not rec["ok"]:
                code = 1
        if not args.skip_vocab:
            log("[vocab] 실제 템플릿 어휘 채취")
            per, failed = capture_vocab(args, log)
            log("[vocab] %d개 중 실패 %d" % (len(per), failed))
            if failed:
                code = 1
    except hs.HwpError as e:
        log("중단: %s" % e)
        return e.code
    log("결과: %s" % FIXTURES)
    return code


if __name__ == "__main__":
    sys.exit(main())
