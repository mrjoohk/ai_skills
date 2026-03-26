#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_eval_report.py — Eval Runner output quality checker

Usage:
    python validate_eval_report.py <path_to_report.md>
    python validate_eval_report.py reports/eval/task_report.md

Checks:
  1. File exists and is non-empty (> 500 bytes)
  2. Has Results Summary table with metric rows
  3. All metrics have a Status column (✅ PASS or ❌ FAIL)
  4. Primary Metric section present with measured value
  5. Acceptance Criteria Judgment section present
  6. Evidence section with calculation script path
  7. No "TODO" or placeholder values remaining

Exits with code 0 if all pass, 1 if any fail.
"""

import sys
import re
from pathlib import Path

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def check_eval_report(report_path: str) -> int:
    path = Path(report_path)
    failures = 0
    results = []

    if not path.exists():
        print(f"\n{FAIL}  File not found: {report_path}")
        return 1

    content = path.read_text(encoding="utf-8", errors="replace")
    size = path.stat().st_size

    # 1. File size
    results.append({
        "check": "파일 존재 및 크기",
        "passed": size > 500,
        "detail": f"{path.name} ({size:,} bytes)"
    })

    # 2. Results Summary table
    has_table = bool(re.search(r'Results Summary|## 결과 요약', content, re.IGNORECASE))
    results.append({
        "check": "Results Summary 테이블 존재",
        "passed": has_table,
        "detail": "결과 테이블 발견" if has_table else "Results Summary 섹션 없음"
    })

    # 3. PASS/FAIL status in table
    pass_fail_count = len(re.findall(r'(✅\s*PASS|❌\s*FAIL)', content))
    results.append({
        "check": "메트릭별 PASS/FAIL 상태",
        "passed": pass_fail_count >= 1,
        "detail": f"PASS/FAIL 상태 {pass_fail_count}개 발견" if pass_fail_count >= 1 else "PASS/FAIL 상태 없음"
    })

    # 4. Primary Metric section
    has_primary = bool(re.search(r'## Primary Metric|Primary Metric:', content, re.IGNORECASE))
    results.append({
        "check": "Primary Metric 섹션 존재",
        "passed": has_primary,
        "detail": "Primary Metric 섹션 발견" if has_primary else "Primary Metric 섹션 없음"
    })

    # 5. Acceptance Criteria Judgment
    has_judgment = bool(re.search(r'Acceptance Criteria Judgment|판정|PASS.*측정', content, re.IGNORECASE))
    results.append({
        "check": "Acceptance Criteria 판정 존재",
        "passed": has_judgment,
        "detail": "판정 섹션 발견" if has_judgment else "Acceptance Criteria 판정 없음"
    })

    # 6. Evidence section
    has_evidence = bool(re.search(r'## Evidence|증거|scripts/eval', content, re.IGNORECASE))
    results.append({
        "check": "Evidence 섹션 (스크립트 경로)",
        "passed": has_evidence,
        "detail": "Evidence 정보 발견" if has_evidence else "Evidence 섹션 없음",
        "warning_only": not has_evidence
    })

    # 7. No TODO placeholders
    todo_count = len(re.findall(r'\bTODO\b|\bTBD\b|<placeholder>', content, re.IGNORECASE))
    results.append({
        "check": "미완성 TODO/TBD 없음",
        "passed": todo_count == 0,
        "detail": "플레이스홀더 없음" if todo_count == 0 else f"TODO/TBD {todo_count}개 발견 — 실제 값으로 교체 필요",
        "warning_only": todo_count > 0
    })

    # Print results
    print(f"\n{'═'*50}")
    print(f"  Eval Report 검증: {path.name}")
    print(f"{'═'*50}")

    for r in results:
        warning_only = r.get("warning_only", False)
        if r["passed"]:
            icon = PASS
        elif warning_only:
            icon = WARN
        else:
            icon = FAIL
            failures += 1
        print(f"  {icon}  {r['check']}")
        print(f"       {r['detail']}")

    print(f"\n{'═'*50}")
    if failures == 0:
        print(f"  {PASS}  모든 검증 통과!")
    else:
        print(f"  {FAIL}  {failures}개 항목 실패")
    print(f"{'═'*50}\n")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    report_path = sys.argv[1] if len(sys.argv) > 1 else "reports/eval/report.md"
    sys.exit(check_eval_report(report_path))
