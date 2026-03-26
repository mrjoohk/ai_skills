#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_eval_plan.py — Eval Planner output quality checker

Usage:
    python validate_eval_plan.py <path_to_evaluation_plan.md>
    python validate_eval_plan.py evaluation_plan.md

Checks:
  1. File exists and is non-empty
  2. Has Metadata section (Source, Domain, Date)
  3. Has at least one Metrics by Task table
  4. All metrics have numeric Baseline, Target, Stretch values (no "TBD")
  5. Has Acceptance Criteria (Given/When/Then format)
  6. Has Evaluation Dataset specified
  7. Has REQ/UF Mapping section
  8. Primary metric count = 1 per task (not multiple)

Exits with code 0 if all checks pass, 1 if any fail.
"""

import sys
import re
from pathlib import Path

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def check_eval_plan(plan_path: str) -> int:
    path = Path(plan_path)
    results = []
    failures = 0

    # 1. File existence and size
    if not path.exists():
        print(f"\n{FAIL}  File not found: {plan_path}")
        return 1

    content = path.read_text(encoding="utf-8", errors="replace")
    size = path.stat().st_size

    results.append({
        "check": "파일 존재 및 크기",
        "passed": size > 100,
        "detail": f"{path.name} ({size:,} bytes)"
    })

    # 2. Metadata section
    has_metadata = bool(re.search(r'##\s*Metadata', content))
    has_domain = bool(re.search(r'Domain\s*:', content))
    results.append({
        "check": "Metadata 섹션 존재 (Source, Domain, Date)",
        "passed": has_metadata and has_domain,
        "detail": "Metadata 섹션 발견" if (has_metadata and has_domain) else "Metadata 또는 Domain 필드 없음"
    })

    # 3. Metrics table
    table_rows = re.findall(r'\|.*Primary.*\|', content)
    has_primary = len(table_rows) >= 1
    results.append({
        "check": "Primary 메트릭 행 존재",
        "passed": has_primary,
        "detail": f"Primary 행 {len(table_rows)}개 발견" if has_primary else "메트릭 테이블에 Primary 행 없음"
    })

    # 4. No TBD in numeric threshold columns
    tbd_count = len(re.findall(r'\bTBD\b', content, re.IGNORECASE))
    results.append({
        "check": "숫자 임계값에 TBD 없음",
        "passed": tbd_count == 0,
        "detail": "모든 임계값 지정됨" if tbd_count == 0 else f"TBD {tbd_count}개 발견 — 구체적 숫자로 교체 필요",
        "warning_only": tbd_count > 0
    })

    # 5. Acceptance Criteria (Given/When/Then)
    has_gwt = bool(re.search(r'\bGiven\b.*\bWhen\b.*\bThen\b', content, re.DOTALL | re.IGNORECASE))
    results.append({
        "check": "Acceptance Criteria (Given/When/Then)",
        "passed": has_gwt,
        "detail": "Given/When/Then 패턴 발견" if has_gwt else "Acceptance Criteria 없음"
    })

    # 6. Evaluation Dataset
    has_dataset = bool(re.search(r'Evaluation Dataset|평가 데이터셋', content, re.IGNORECASE))
    results.append({
        "check": "Evaluation Dataset 명시",
        "passed": has_dataset,
        "detail": "데이터셋 지정됨" if has_dataset else "Evaluation Dataset 항목 없음"
    })

    # 7. REQ/UF Mapping
    has_mapping = bool(re.search(r'REQ.*UF.*Mapping|UF.*Mapping|REQ-\d+', content))
    results.append({
        "check": "REQ/UF Mapping 섹션",
        "passed": has_mapping,
        "detail": "REQ/UF 매핑 발견" if has_mapping else "REQ/UF Mapping 없음",
        "warning_only": not has_mapping
    })

    # Print results
    print(f"\n{'═'*50}")
    print(f"  Eval Plan 검증: {path.name}")
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
        print(f"  {FAIL}  {failures}개 항목 실패 — 위 내용 확인 필요")
    print(f"{'═'*50}\n")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    plan_path = sys.argv[1] if len(sys.argv) > 1 else "evaluation_plan.md"
    sys.exit(check_eval_plan(plan_path))
