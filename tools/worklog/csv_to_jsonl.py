#!/usr/bin/env python3
"""DRM xlsx 에서 덤프한 CSV 를 작업 로그 JSONL 로 옮긴다.

    python csv_to_jsonl.py --kind files   "덤프.csv" > files.jsonl
    python csv_to_jsonl.py --kind prompts "덤프.csv" > prompts.jsonl

덤프는 office-com-reader 로 만든다:
    Read-OfficeDoc.ps1 -Path 0.FilesUpdate.xlsx -Dump -OutDir <폴더>

주의 — 날짜가 숫자로 온다.
    Read-OfficeDoc.ps1 은 속도를 위해 `UsedRange.Value2` 로 값을 한 번에 받는데,
    Value2 는 날짜를 표시 문자열이 아니라 **OLE 자동화 일련번호**(1899-12-30 기준 일수)로
    돌려준다. 그래서 `일시` 칸에 `46265.4375` 같은 값이 들어온다.
    이 스크립트가 그 숫자를 날짜로 되돌린다.
"""
import argparse
import csv
import datetime as dt
import json
import re
import sys

# 한글 컬럼명 -> JSON 키. 부분 일치로 찾는다 (앞뒤 공백·줄바꿈이 섞여 있는 경우가 많다).
FILES_COLS = [
    ("일시", "ts", False),
    ("파일명", "files", True),
    ("요청 요약", "summary", False),
    ("요청 ID", "req_id", False),
    ("근거 ID", "basis_ids", True),
    ("검증", "verify", False),
    ("커밋", "commit", False),
]
PROMPTS_COLS = [
    ("일시", "ts", False),
    ("요청 프롬프트", "prompt", False),
    ("응답", "response", False),
    ("요청 ID", "req_id", False),
    ("산출물", "outputs", True),
]

EXCEL_EPOCH = dt.datetime(1899, 12, 30)


def excel_serial_to_ts(value):
    """Value2 가 돌려준 일련번호를 'YYYY-MM-DD HH:MM' 으로. 아니면 None."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not (1 < num < 200000):          # 날짜로 보기 어려운 범위
        return None
    return (EXCEL_EPOCH + dt.timedelta(days=num)).strftime("%Y-%m-%d %H:%M")


def normalize_ts(raw):
    raw = (raw or "").strip()
    if not raw:
        return ""
    serial = excel_serial_to_ts(raw)
    if serial:
        return serial
    # 이미 문자열 날짜인 경우 — 흔한 표기들을 정규화한다
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})[ T]*(\d{1,2})?:?(\d{2})?", raw)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        h = int(m.group(4) or 0)
        mi = int(m.group(5) or 0)
        return f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}"
    return raw


def split_list(raw):
    if not raw:
        return []
    parts = re.split(r"[,\n;]+", raw)
    return [p.strip() for p in parts if p.strip()]


def normalize_paths(items):
    """디렉터리 와일드카드를 디렉터리 표기로 바꾼다.

    `logs/P-007_tick_evidence/*` 는 "그 폴더 전체" 라는 뜻이고
    `logs/P-007_tick_evidence/` 와 의미가 같다. 뜻을 바꾸지 않으면서
    Rule 4 의 와일드카드 금지를 만족시킨다.

    파일명 접두사 패턴(`260715_0030*.md`)은 폴더가 아니므로 그대로 둔다 —
    그런 항목이 남으면 호출자가 legacy_note 를 붙인다.
    """
    out = []
    for it in items:
        m = re.match(r"^(.*/)\*\s*(\(.*\))?$", it)
        if m:
            note = (" " + m.group(2)) if m.group(2) else ""
            out.append(m.group(1) + note)
        else:
            out.append(it)
    return out


def find_header(rows, cols):
    """헤더 행 번호와 {json키: 열번호} 를 찾는다. 제목 행이 위에 있을 수 있다."""
    names = [c[0] for c in cols]
    for i, row in enumerate(rows[:30]):
        cells = [(c or "").strip() for c in row]
        hits = sum(1 for n in names if any(n in c for c in cells))
        if hits >= max(3, len(names) - 2):
            mapping = {}
            for kor, key, _ in cols:
                for j, c in enumerate(cells):
                    if kor in c:
                        mapping[key] = j
                        break
            return i, mapping
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="덤프 CSV -> 작업로그 JSONL")
    ap.add_argument("csv_path")
    ap.add_argument("--kind", choices=["files", "prompts"], required=True)
    args = ap.parse_args(argv)

    cols = FILES_COLS if args.kind == "files" else PROMPTS_COLS

    with open(args.csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    hdr, mapping = find_header(rows, cols)
    if hdr is None:
        sys.stderr.write(
            "헤더 행을 못 찾았다. 기대한 컬럼: " + ", ".join(c[0] for c in cols) + "\n"
            "덤프 CSV 상단 몇 줄을 확인하고 --kind 가 맞는지 본다.\n"
        )
        return 2
    missing = [kor for kor, key, _ in cols if key not in mapping]
    if missing:
        sys.stderr.write(f"경고: 못 찾은 컬럼 {missing} — 해당 필드는 빈 값으로 둔다\n")

    written = skipped = 0
    for row in rows[hdr + 1:]:
        rec = {}
        for kor, key, is_list in cols:
            idx = mapping.get(key)
            raw = row[idx] if (idx is not None and idx < len(row)) else ""
            raw = (raw or "").strip()
            if key == "ts":
                rec[key] = normalize_ts(raw)
            elif is_list:
                rec[key] = split_list(raw)
            else:
                rec[key] = raw

        # 전부 빈 행은 버린다
        if not any(v for v in rec.values()):
            skipped += 1
            continue
        # v2 스키마(요청 ID·근거 ID·검증·커밋 ID) 도입 전 기록은 그 칸이 비어 있다.
        # 없는 요청 ID 를 지어내지 않는다 — 존재한 적 없는 provenance 를 만드는 일이다.
        # 대신 schema 로 표시해 검증기가 과거 기록에 v2 규칙을 들이대지 않게 한다.
        rec["schema"] = "v2" if rec.get("req_id") else "v1"

        if args.kind == "files":
            rec["files"] = normalize_paths(rec.get("files", []))
            leftover = [p for p in rec["files"] if "*" in p]
            if leftover:
                # 폴더로 환원되지 않는 와일드카드. 당시 대상 파일을 지금 복원할 수 없으므로
                # 지어내지 않고, 예외임을 명시적으로 남긴다.
                rec["legacy_note"] = (
                    "원본 대장에 와일드카드로 기록됨 " + ", ".join(repr(p) for p in leftover)
                    + " — 당시 대상 파일 목록을 복원할 수 없어 그대로 이관"
                )

        if args.kind == "files" and rec["schema"] == "v2":
            # v2 행에만 규칙이 요구하는 명시적 값을 채운다
            if not rec.get("verify"):
                rec["verify"] = "검증 없음"
            if not rec.get("commit"):
                rec["commit"] = "미커밋"

        rid = rec.get("req_id", "")
        if args.kind == "files" and "," in rid:
            # 한 행이 두 요청을 함께 기록한 경우. 요청별 귀속이 질의의 전제이므로 나눈다.
            ids = [x.strip() for x in rid.split(",") if x.strip()]
            note = f"원본 대장 1행이 요청 {', '.join(ids)} 를 함께 기록 — 이관 시 요청별로 분리"
            for one in ids:
                sub = dict(rec)
                sub["req_id"] = one
                sub["legacy_note"] = (rec.get("legacy_note", "") + " / " + note).strip(" /")
                print(json.dumps(sub, ensure_ascii=False))
                written += 1
            continue

        print(json.dumps(rec, ensure_ascii=False))
        written += 1

    sys.stderr.write(f"헤더 {hdr + 1}행 · 변환 {written}건 · 빈 행 {skipped}건 건너뜀\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
