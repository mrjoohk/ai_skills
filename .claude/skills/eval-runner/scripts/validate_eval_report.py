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
  8. No coexistence of a PASS verdict with untagged MANUAL_PENDING phrases
     (pending metrics excluded from the verdict must carry an explicit
      [EXCLUDED-FROM-VERDICT: reason] / [판정제외: 사유] tag on the same line)
  9. (optional) runs.yaml cross-check: pass a runs.yaml path as 2nd argument —
     a PASS verdict with unresolved MANUAL_PENDING entries in runs.yaml and no
     exclusion tags in the report is a FAIL (report and evidence pack must move together)

Usage:
    python validate_eval_report.py <report.md> [evidence_pack/runs.yaml]

Exits with code 0 if all pass, 1 if any fail.
"""

import sys
import re
from pathlib import Path

# verdict line: "판정: PASS" / "종합 판정: PASS" / "Overall: PASS" / template arrow "→ **PASS**"
# (keyword must be immediately followed by a colon — lines like "판정 기준: PASS는 ..."
#  describe criteria and must NOT count as a verdict)
VERDICT_RE = re.compile(
    r"(?im)^.{0,60}?\b(?:overall|verdict|(?:최종|종합)?\s*판정)\s*[:：]\s*\**\s*(?:✅\s*)?(?:pass|통과)\b"
    r"|→\s*\**\s*(?:PASS|통과)\**"
)
PENDING_RE = re.compile(r"MANUAL[-_ ]?PENDING|확인 시 (?:본 보고서 )?갱신|사용자 확인 대기")
EXCLUDE_TAG_RE = re.compile(r"EXCLUDED[-_ ]?FROM[-_ ]?VERDICT|판정\s*제외", re.IGNORECASE)

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def check_eval_report(report_path: str, runs_path: str | None = None) -> int:
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

    # 8. PASS verdict must not coexist with UNTAGGED pending phrases (hard FAIL).
    #    Exemption is structural (line-level [EXCLUDED-FROM-VERDICT]/[판정제외] tag),
    #    never inferred from prose — natural-language exemption heuristics both leak
    #    (incidental phrases mask real violations) and misfire.
    verdict_pass = bool(VERDICT_RE.search(content))
    untagged_pending = [
        ln.strip() for ln in content.splitlines()
        if PENDING_RE.search(ln) and not EXCLUDE_TAG_RE.search(ln)
    ]
    coexist = verdict_pass and len(untagged_pending) > 0
    results.append({
        "check": "PASS 판정·미태그 PENDING 공존 없음",
        "passed": not coexist,
        "detail": "공존 없음" if not coexist else (
            f"PASS 판정인데 태그 없는 PENDING 문구 {len(untagged_pending)}건 — "
            "해소하거나 [EXCLUDED-FROM-VERDICT: 사유] 태그를 달 것 (수동 지표 수명주기 참조): "
            + " | ".join(untagged_pending[:3])
        ),
        "warning_only": False
    })

    # 9. Optional runs.yaml cross-check — report and evidence pack must move together.
    if runs_path:
        rp = Path(runs_path)
        if not rp.exists():
            results.append({
                "check": "runs.yaml 교차 검사",
                "passed": False,
                "detail": f"runs.yaml 없음: {runs_path}",
                "warning_only": True
            })
        else:
            runs_text = rp.read_text(encoding="utf-8", errors="replace")
            runs_pending = len(re.findall(r'MANUAL[-_ ]?PENDING', runs_text))
            report_has_tags = bool(EXCLUDE_TAG_RE.search(content))
            runs_bad = verdict_pass and runs_pending > 0 and not report_has_tags
            results.append({
                "check": "runs.yaml 교차 검사 (미해소 MANUAL_PENDING)",
                "passed": not runs_bad,
                "detail": (
                    f"runs.yaml pending {runs_pending}건, 보고서와 정합" if not runs_bad else
                    f"PASS 판정인데 runs.yaml에 미해소 MANUAL_PENDING {runs_pending}건 — "
                    "4개소 원자 반입(수명주기 2단계) 미완료"
                ),
                "warning_only": False
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
    runs_path = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(check_eval_report(report_path, runs_path))
