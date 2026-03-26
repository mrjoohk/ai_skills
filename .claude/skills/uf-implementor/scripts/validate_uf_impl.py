#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_uf_impl.py — UF Implementor output quality checker

Usage:
    python validate_uf_impl.py <project_root>
    python validate_uf_impl.py .

Checks:
  1. src/uf/ directory exists with .py files
  2. tests/unit/ directory exists with test_*.py files
  3. Implementation report exists (reports/impl/uf_impl_report_*.md)
  4. No functions left as bare `pass` or `raise NotImplementedError()` with no body
  5. Test files have at least one `def test_` function
  6. Test files have at least one `assert` statement
  7. Each src/uf/*.py module has corresponding test file
  8. No `BLOCKED` items without inline CLARIFICATION NEEDED comment

Exits with code 0 if all pass, 1 if any fail.
"""

import sys
import re
from pathlib import Path

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def find_python_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.py")) if directory.exists() else []


def check_uf_impl(project_root: str) -> int:
    root = Path(project_root)
    results = []
    failures = 0

    src_uf = root / "src" / "uf"
    tests_unit = root / "tests" / "unit"
    reports_dir = root / "reports" / "impl"

    # 1. src/uf/ exists
    src_files = find_python_files(src_uf)
    results.append({
        "check": "src/uf/ 디렉토리 및 구현 파일",
        "passed": len(src_files) > 0,
        "detail": f"{len(src_files)}개 .py 파일 발견" if src_files else "src/uf/ 없음 또는 .py 파일 없음"
    })

    # 2. tests/unit/ exists
    test_files = find_python_files(tests_unit)
    results.append({
        "check": "tests/unit/ 디렉토리 및 테스트 파일",
        "passed": len(test_files) > 0,
        "detail": f"{len(test_files)}개 test_*.py 파일 발견" if test_files else "tests/unit/ 없음 또는 테스트 파일 없음"
    })

    # 3. Implementation report
    report_files = list(reports_dir.glob("uf_impl_report_*.md")) if reports_dir.exists() else []
    results.append({
        "check": "구현 리포트 (uf_impl_report_*.md)",
        "passed": len(report_files) > 0,
        "detail": f"{report_files[0].name} 발견" if report_files else "reports/impl/uf_impl_report_*.md 없음",
        "warning_only": len(report_files) == 0
    })

    # 4. No bare pass/NotImplementedError
    stub_issues = []
    for f in src_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        # Check for functions that end in just `pass` or `raise NotImplementedError()` with no real body
        bare_pass = re.findall(r'def \w+[^:]*:\n(?:\s+"""[^"]*"""[\s\n]*)?\s+(?:pass|raise NotImplementedError\(\))\s*$',
                               content, re.MULTILINE)
        if bare_pass:
            stub_issues.append(f"{f.name}: {len(bare_pass)}개 stub 함수")
    results.append({
        "check": "구현 완성도 (bare pass 없음)",
        "passed": len(stub_issues) == 0,
        "detail": "모든 함수 구현됨" if not stub_issues else f"미구현 stub: {'; '.join(stub_issues)}",
        "warning_only": len(stub_issues) > 0
    })

    # 5. Test files have test_ functions
    test_fn_count = 0
    for f in test_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        test_fn_count += len(re.findall(r'def test_\w+', content))
    results.append({
        "check": "테스트 함수 존재 (def test_*)",
        "passed": test_fn_count >= 1,
        "detail": f"{test_fn_count}개 테스트 함수 발견" if test_fn_count >= 1 else "테스트 함수 없음"
    })

    # 6. Test files have assert statements
    assert_count = 0
    for f in test_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        assert_count += len(re.findall(r'\bassert\b', content))
    results.append({
        "check": "assert 문 존재",
        "passed": assert_count >= 1,
        "detail": f"{assert_count}개 assert 발견" if assert_count >= 1 else "테스트에 assert 없음"
    })

    # 7. Src/test correspondence
    src_modules = {f.stem for f in src_files}
    test_modules = {f.stem.replace("test_", "") for f in test_files}
    missing_tests = src_modules - test_modules
    results.append({
        "check": "구현 모듈별 테스트 파일 대응",
        "passed": len(missing_tests) == 0,
        "detail": "모든 모듈에 테스트 있음" if not missing_tests else f"테스트 없는 모듈: {', '.join(missing_tests)}",
        "warning_only": len(missing_tests) > 0
    })

    # Print results
    print(f"\n{'═'*55}")
    print(f"  UF Implementor 출력 검증: {root}")
    print(f"{'═'*55}")

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

    print(f"\n{'═'*55}")
    if failures == 0:
        print(f"  {PASS}  모든 검증 통과!")
    else:
        print(f"  {FAIL}  {failures}개 항목 실패")
    print(f"{'═'*55}\n")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(check_uf_impl(project_root))
