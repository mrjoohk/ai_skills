#!/usr/bin/env python3
"""
validate_test_paths.py — Gate 2 기계화: 설계 문서 선언 경로·함수의 실존 전수 대조 (2026-07-27)

Usage:
    python validate_test_paths.py [--root <repo_root>] [--strict]

대상 문서(선언의 원천만): rd/uf.md, rd/requirements.md, rd/uf_split/*.md
  (uf_if_coverage_review.md·review_docs/ 등 사료성 문서는 과거 기록이므로 제외)

버킷:
  OK         — 파일(및 함수) 실존
  GHOST_FUNC — 파일은 있는데 함수 없음 → 항상 FAIL ('거짓 선언')
  MISSING    — 파일 없음 → 기본 리포트만, --strict 시 FAIL
               (미구현 마일스톤의 계획 경로일 수 있음. 게이트 정책:
                완료 선언된 IF/REQ 범위의 MISSING은 FAIL로 취급할 것)

검사 방향은 반드시 선언→실물이다. 실물 목록에서 존재를 확인하는 역방향 검사 금지.
Exit: GHOST_FUNC>0 → 1 / --strict이고 MISSING>0 → 1 / 그 외 0
"""
import argparse
import re
import signal
import sys
from pathlib import Path

try:  # head 등 파이프 조기 종료 시 traceback 방지
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass


def line_of(text: str, pos: int) -> str:
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    return text[a:b if b != -1 else len(text)]

DOC_GLOBS = ["rd/uf.md", "rd/requirements.md", "rd/uf_split/*.md"]
PATH_RE = re.compile(r"\b((?:tests|scripts)/[A-Za-z0-9_\-./]*\.(?:py|cpp|hpp|sh|md|scn))\b")
FUNC_RE = re.compile(r"\b([A-Za-z0-9_\-./]+\.(?:py|cpp))::([A-Za-z_]\w*)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    docs = []
    for g in DOC_GLOBS:
        docs.extend(sorted(root.glob(g)))
    if not docs:
        print(f"no design docs found under {root}")
        sys.exit(1)

    rows, seen = [], set()
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for m in PATH_RE.finditer(text):
            p = m.group(1)
            key = (doc.name, p, "")
            if key in seen:
                continue
            seen.add(key)
            rows.append((doc.name, p, "OK" if (root / p).exists() else "MISSING", ""))
        for m in FUNC_RE.finditer(text):
            f, fn = m.group(1), m.group(2)
            key = (doc.name, f, fn)
            if key in seen:
                continue
            seen.add(key)
            fp = root / f
            if not fp.exists():
                rows.append((doc.name, f"{f}::{fn}", "MISSING", "파일 없음"))
                continue
            body = fp.read_text(encoding="utf-8", errors="replace")
            found = (f"def {fn}" in body) if f.endswith(".py") else (fn in body)
            if found:
                bucket, note = "OK", ""
            elif "예정" in line_of(text, m.start()):
                bucket, note = "PLANNED", "선언 라인에 '예정' 마커 — 미구현 계획"
            else:
                bucket, note = "GHOST_FUNC", "파일은 있으나 함수 없음"
            rows.append((doc.name, f"{f}::{fn}", bucket, note))

    ghost = [r for r in rows if r[2] == "GHOST_FUNC"]
    missing = [r for r in rows if r[2] == "MISSING"]
    planned = [r for r in rows if r[2] == "PLANNED"]
    ok_n = sum(1 for r in rows if r[2] == "OK")

    print(f"declared tokens: {len(rows)}  (OK {ok_n} / PLANNED {len(planned)} / MISSING {len(missing)} / GHOST_FUNC {len(ghost)})")
    for name, bucket in (("GHOST_FUNC (항상 FAIL)", ghost), ("PLANNED (예정 마커 — 정보)", planned), ("MISSING (계획 경로 가능 — 완료 범위면 FAIL)", missing)):
        if bucket:
            print(f"\n[{name}]")
            for d, t, _, note in bucket:
                print(f"  {d}: {t}" + (f"  ({note})" if note else ""))

    sys.exit(1 if (ghost or (args.strict and missing)) else 0)


if __name__ == "__main__":
    main()
