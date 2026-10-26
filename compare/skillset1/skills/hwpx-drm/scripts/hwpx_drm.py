#!/usr/bin/env python3
"""hwpx-drm 명령줄 (설계 IF-1). DocuRay DRM hwpx 를 한/글(COM)로 열어 읽고, 필드를 채우고, 자리표시를 바꾸고, HWPX 로 저장한다.

    python hwpx_drm.py inspect  <파일> [--json]
    python hwpx_drm.py outline  <파일> [--json]
    python hwpx_drm.py tables   <파일> [--table s0.t3] [--json]
    python hwpx_drm.py fields   <파일> [--json]
    python hwpx_drm.py search   <파일> --pattern 키1,키2 [--json]   (검색어 안의 쉼표는 \\, — 예: "가\\, 나,다" = '가, 나'·'다')
    python hwpx_drm.py fill     <파일> --map 값.json  [--out 파일 | --overwrite] [--force]
    python hwpx_drm.py replace  <파일> --map 바꿀말.json [--out 파일 | --overwrite] [--force]
    python hwpx_drm.py verify   <파일>
    python hwpx_drm.py images   <파일> --out-dir <새 폴더> [--json]   (문서에 포함된 그림을 평문 파일로 — D-062)
공통: --timeout 180  --allow-running  --md-dir hwpx_md  --log 기록.md

읽기 명령은 결과를 항상 <md-dir>/<파일이름>.<명령>.md 로 남긴다(D-012, DRM 미보호 평문 고지 포함).
종료코드: 0 성공 / 1 검증 실패(없는 필드·남은 자리표시·저장 실패) / 2 사전조건(파일 없음·한/글 실행 중·출력 존재·값 파일 오류)
          / 3 저장 결과가 평문 / 4 열기 실패 / 5 시간초과 / 6 pywin32·COM 생성 실패
"""
import argparse
import datetime
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hwp_session as hs        # noqa: E402
import hwpml_parse as hp        # noqa: E402
import hwpx_api as api          # noqa: E402
import render_md as rm          # noqa: E402
import images as im             # noqa: E402

READ_CMDS = ("inspect", "outline", "tables", "fields", "search")
WRITE_CMDS = ("fill", "replace")


def split_patterns(text):
    """검색어 글 → 검색어 목록. 쉼표(,)가 구분자이고, 검색어 안의 쉼표는 '\\,' 로 쓴다('\\\\' = 역슬래시 하나).
    그 밖의 역슬래시는 그대로 둔다(경로 등). 앞뒤 빈칸은 지우고 빈 검색어는 뺀다(P-052).
    office-drm-bridge(bridge_core.split_patterns)와 같은 규칙이어야 한다 — 브리지 replace 선행조건이 이 목록과 맞춘다."""
    out, cur, i = [], [], 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] in ",\\":
            cur.append(text[i + 1])
            i += 2
            continue
        if c == ",":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur))
    return [p for p in (x.strip() for x in out) if p]


def build_parser():
    ap = argparse.ArgumentParser(prog="hwpx_drm.py", description="DocuRay DRM hwpx 읽기·쓰기 (한/글 COM)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("file")
    common.add_argument("--timeout", type=int, default=180, help="COM 호출 하나의 제한 초 (넘으면 이 실행의 Hwp.exe 만 종료)")
    common.add_argument("--allow-running", action="store_true", help="이미 떠 있는 한/글이 있어도 진행 (기본: 중단)")
    common.add_argument("--md-dir", default="hwpx_md", help="읽기 결과 .md 폴더 (기본 hwpx_md)")
    common.add_argument("--log", help="실행 기록 .md (본문 없음)")
    for c in READ_CMDS:
        p = sub.add_parser(c, parents=[common])
        p.add_argument("--json", action="store_true", help="결과 JSON 을 표준출력으로")
        if c == "tables":
            p.add_argument("--table", help="표 ID 하나만 (예: s0.t3)")
        if c == "search":
            p.add_argument("--pattern", required=True, help="쉼표로 구분한 검색어 — 검색어 안의 쉼표는 \\, (역슬래시 자체는 \\\\)")
    for c in WRITE_CMDS:
        p = sub.add_parser(c, parents=[common])
        p.add_argument("--map", required=True, help="값 JSON 또는 ```json 블록이 든 .md")
        p.add_argument("--out", help="출력 hwpx (기본 <원본>_out.hwpx)")
        p.add_argument("--overwrite", action="store_true", help="원본에 덮어쓴다 (먼저 <원본>.bak 생성)")
        p.add_argument("--force", action="store_true", help="출력 파일이 이미 있으면 교체")
        p.add_argument("--json", action="store_true", help="결과 JSON 을 표준출력으로")
    sub.add_parser("verify", parents=[common])
    p = sub.add_parser("images", parents=[common])
    p.add_argument("--out-dir", required=True, help="그림을 쓸 새 폴더(이미 있으면 거절) — 평문 그림·목록(images.md·json)")
    p.add_argument("--json", action="store_true", help="결과 JSON 을 표준출력으로")
    return ap


def say(msg=""):
    print(msg, flush=True)


def run(args, sess):
    """명령 실행 → (종료코드, 결과 dict, 만든 파일 목록)."""
    made, result = [], {}
    with sess as s:
        if args.cmd == "verify":
            head = hs.head_kind(Path(args.file)) if Path(args.file).exists() else None
            s.open(args.file)
            m = s.model()
            result = {"file": str(Path(args.file).resolve()), "head": head, "open": True,
                      "tables": m["stats"]["tables"], "paragraphs": m["stats"]["p_elements"], "timing": s.timing}
            say("선두 %s · 열기 성공 · 표 %d · 문단 %d" % (head, result["tables"], result["paragraphs"]))
            return (0 if head == "DOCURAY" else 3), result, made

        if args.cmd == "images":
            return run_images(args, s)
        s.open(args.file)
        if args.cmd in READ_CMDS:
            m = s.model()
            extra = ["소요(초): %s" % json.dumps(s.timing)]
            if args.cmd == "inspect":
                fields = s.fields()
                lines = rm.head(m, "inspect", extra) + rm.summary(m) + rm.outline_lines(m) + rm.fields_lines(fields) \
                    + rm.body_lines(m) + rm.objects_lines(m) + rm.notes_lines(m)
                result = {"stats": m["stats"], "coverage_mismatch": m["coverage_mismatch"], "fields": fields,
                          "timing": s.timing}
                st = m["stats"]
                say("구역 %d · 문단 %d · 표 %d · 셀 %d · 메모 %d · 머리말 %d · 각주 %d · 입력 필드 %d" % (
                    st["sections"], st["p_elements"], st["tables"], st["cells"], st["memos"], st["headers"],
                    st["footnotes"], len(fields["input"])))
                if m["coverage_mismatch"]:
                    say("경고: 파싱 누락 의심 %s" % m["coverage_mismatch"])
            elif args.cmd == "outline":
                items = hp.outline(m)
                lines = rm.head(m, "outline", extra) + rm.outline_lines(m)
                result = {"outline": [{"id": b["id"], "level": b["level"], "text": b["text"]} for b in items]}
                say("개요 문단 %d개" % len(items))
            elif args.cmd == "tables":
                tables = list(hp.top_tables(m))              # 셀 안 중첩 표는 바깥 표 아래에 함께 그린다
                if args.table:
                    t = hp.find_table(m, args.table)
                    if t is None:
                        say("표 %s 가 없다. 표 ID: %s" % (args.table, ", ".join(x["id"] for x in tables[:30])))
                        return 1, {"error": "no such table"}, made
                    tables = [t]
                lines = rm.head(m, "tables", extra)
                for t in tables:
                    lines += rm.table_lines(t)
                bad = [t["id"] for t in tables if not t["grid_ok"]]
                result = {"tables": [{k: t[k] for k in ("id", "rows", "cols", "caption", "grid_ok", "grid_note")}
                                     for t in tables]}
                say("표 %d개 · 격자 불일치 %d%s" % (len(tables), len(bad), (" " + ", ".join(bad[:10])) if bad else ""))
            elif args.cmd == "fields":
                fields = s.fields()
                lines = rm.head(m, "fields", extra) + rm.fields_lines(fields)
                result = fields
                say("입력 필드 %d · 비입력 %d · 메모 %d" % (len(fields["input"]), len(fields["other"]), fields["memos"]))
            else:                                            # search
                pats = split_patterns(args.pattern)
                hits = rm.search(m, pats)
                lines = rm.head(m, "search", extra) + rm.search_lines(hits, pats)
                result = {"hits": hits}
                for p in pats:
                    say("'%s' %d건" % (p, sum(1 for h in hits if h["key"] == p)))
            md = rm.write_md(args.md_dir, args.file, args.cmd, lines)
            made.append(str(md.resolve()))
            return 0, result, made

        # ---- 쓰기
        mapping = api.load_map(args.map)
        if args.cmd == "fill":
            r = s.fill(mapping)
            result["fill"] = r
            say("채움 %d · 없는 필드 %d%s · 불일치 %d" % (len(r["filled"]), len(r["missing"]),
                                                    (" " + ", ".join(r["missing"])) if r["missing"] else "", len(r["mismatch"])))
            code = 1 if (r["missing"] or r["mismatch"]) else 0
            verify = {k: mapping[k] for k in r["filled"]}
        else:
            r = s.replace(mapping)
            result["replace"] = r
            for k, v in r.items():
                warn = " (문서에 없음)" if v["before"] == 0 else ""
                left = " · 남음 %d: %s" % (v["remaining"], ", ".join(v["remaining_at"])) if v["remaining"] else ""
                say("'%s' 전 %d → 후 %d%s%s" % (k, v["before"], v["after"], warn, left))
            code = 1 if any(v["remaining"] for v in r.values()) else 0
            verify = None
        changed = (args.cmd == "fill" and result["fill"]["filled"]) or \
                  (args.cmd == "replace" and any(v["before"] for v in result["replace"].values()))
        if not changed:
            say("바뀐 것이 없어 저장하지 않는다")
            return (code or 1), result, made
        sv = s.save(out=args.out, overwrite=args.overwrite, force=args.force, verify_fields=verify)
        result["save"] = sv
        made.append(sv["out"])
        if sv.get("backup"):
            made.append(sv["backup"])
        say("저장 %s · 선두 %s · 다시 열기 %s%s" % (sv["out"], sv["head"], sv["reopen"],
                                            (" · 원본 불변 %s" % sv["source_unchanged"]) if "source_unchanged" in sv else ""))
        if not sv["reopen"] or sv.get("after_reopen_mismatch"):
            code = code or 1
        return code, result, made


def run_images(args, s):
    """문서에 포함된 그림을 문서 차례로 <out-dir>/figKK.<형식> 평문 파일로 쓴다(P-052, D-062 — 보안담당자 허락).
    목록 images.md·images.json(번호·캡션 제목·크기·위치·형식·sha256). 꺼낸 그림이 하나도 없으면(그림은 있는데) 종료코드 1."""
    out = Path(args.out_dir)
    if out.exists():
        raise hs.PreconditionError("출력 폴더가 이미 있다 — 덮어쓰지 않는다: %s" % out)
    s.open(args.file)
    m = s.model()
    x = s.last_hwpml or ""
    recs, blobs = im.extract(x, hp.clean(x)[0])
    out.mkdir(parents=True)
    made = []
    for r, b in zip(recs, blobs):
        if b is not None:
            (out / r["file"]).write_bytes(b)
            made.append(str((out / r["file"]).resolve()))
    rows = ["| %d | %s | %s | `%s` | %s | %s |" % (r["k"], rm.esc(r["title"]), r["size_mm"], r["where"],
                                                   r.get("file") or "-", r.get("skip") or "%s · %s" % (r["format"], r["how"]))
            for r in recs]
    lines = rm.head(m, "images", ["**평문 그림** — 보안담당자 허락에 따라 꺼냈다(D-062). 원본과 같은 보안 등급으로 다룬다."]) + \
        ["## 그림", "", "| k | 캡션 제목 | 크기(mm) | 위치 | 파일 | 형식·방법 / 건너뜀 |", "|---|---|---|---|---|---|"] + rows
    (out / "images.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "images.json").write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    made += [str((out / "images.md").resolve()), str((out / "images.json").resolve())]
    got = sum(1 for b in blobs if b is not None)
    say("그림 %d개 · 꺼냄 %d · 건너뜀 %d" % (len(recs), got, len(recs) - got))
    return (1 if recs and not got else 0), {"images": recs}, made


def write_log(path, args, code, result, made, started, calls):
    lines = ["# hwpx-drm 실행 기록", "",
             "- 시각: %s · 명령 `%s` · 파일 `%s` · 종료코드 %d · %.1f초" % (
                 started.isoformat(timespec="seconds"), args.cmd, args.file, code,
                 (datetime.datetime.now() - started).total_seconds()),
             "- 만든 파일: %s" % (", ".join("`%s`" % m for m in made if m) or "없음"), "",
             "| COM 호출 | 초 |", "|---|---|"] + ["| %s | %s |" % c for c in calls]
    if "replace" in result:                                  # 건수만 (값 없음)
        lines += ["", "| 자리표시 | 전 | 후 | 남음 |", "|---|---|---|---|"]
        lines += ["| `%s` | %d | %d | %d |" % (k, v["before"], v["after"], v["remaining"]) for k, v in result["replace"].items()]
    if "fill" in result:
        lines += ["", "- 채움 %d · 없는 필드 %s · 불일치 %d" % (
            len(result["fill"]["filled"]), result["fill"]["missing"], len(result["fill"]["mismatch"]))]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):                   # cp949 콘솔에서 표현 못 하는 글자로 죽지 않게 (F-050 교훈)
        sys.stdout.reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    if args.cmd in WRITE_CMDS and args.overwrite and args.out:
        say("--out 과 --overwrite 는 함께 쓸 수 없다")
        return 2
    started, code, result, made = datetime.datetime.now(), 1, {}, []
    sess = api.HwpxSession(timeout=args.timeout, allow_running=args.allow_running, log=say)
    try:
        code, result, made = run(args, sess)
    except hs.HwpError as e:
        code = e.code
        say("중단(종료코드 %d): %s" % (code, e))
        rec = getattr(e, "rec", None)                        # 저장 단계 실패: 남은 파일(결과·원본 사본)을 알린다
        if rec:
            made += [rec[k] for k in ("out", "backup") if rec.get(k)]
            result["save"] = rec
    except hp.ParseError as e:
        code = 1
        say("중단(종료코드 1): %s" % e)
    except Exception as e:                                   # COM 오류·파일 잠금 등 - 그래도 기록은 남긴다
        code = 1
        say("중단(종료코드 1, 예상 못 한 오류): %s: %s" % (type(e).__name__, e))
    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=True, indent=1, default=str))   # cp949 콘솔에서도 글자가 '?' 로 바뀌지 않게
    if made:
        say("만든 파일: " + " , ".join(m for m in made if m))
    if args.log:
        write_log(args.log, args, code, result, made, started, sess.s.calls)
    return code


if __name__ == "__main__":
    sys.exit(main())
