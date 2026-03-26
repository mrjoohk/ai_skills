#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_output.py — Tab Digest output quality checker

Usage:
    python validate_output.py <output_dir>
    python validate_output.py /sessions/.../mnt/ai_skills/

Checks:
  1. Required files exist (HTML + DOCX)
  2. HTML has proper UTF-8 charset declaration
  3. HTML contains actual Korean characters (not \\uXXXX escape sequences)
  4. HTML has the key structural elements (TL;DR box, filter bar, card grid)
  5. DOCX has reasonable file size (>5KB — empty docs are ~5KB)
  6. No unicode escape sequences in HTML content

Exits with code 0 if all checks pass, 1 if any fail.
"""

import sys
import os
import re
import glob
from pathlib import Path


PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def find_output_files(output_dir: str):
    """Find the most recent tab-digest HTML and DOCX files."""
    base = Path(output_dir)
    html_files = sorted(base.glob("tab-digest*.html"), key=os.path.getmtime, reverse=True)
    docx_files = sorted(base.glob("tab-digest*.docx"), key=os.path.getmtime, reverse=True)
    return html_files[0] if html_files else None, docx_files[0] if docx_files else None


def check_html(html_path: Path) -> list[dict]:
    results = []

    # 1. File exists and is non-empty
    size = html_path.stat().st_size
    results.append({
        "check": "HTML 파일 존재",
        "passed": size > 0,
        "detail": f"{html_path.name} ({size:,} bytes)"
    })

    content = html_path.read_text(encoding="utf-8", errors="replace")

    # 2. UTF-8 charset declaration
    has_charset = bool(re.search(r'<meta\s+charset=["\']UTF-8["\']', content, re.IGNORECASE))
    results.append({
        "check": "HTML charset=UTF-8 선언",
        "passed": has_charset,
        "detail": "charset 메타 태그 있음" if has_charset else "⚠️  <meta charset=\"UTF-8\"> 없음 — 한국어가 깨질 수 있음"
    })

    # 3. No unicode escape sequences in visible content (\\uXXXX pattern)
    # These appear when Python json.dumps() is used with ensure_ascii=True
    escape_matches = re.findall(r'\\u[0-9a-fA-F]{4}', content)
    # Allow some in JS code (e.g., in JSON.stringify or template literals), but flag many
    excessive_escapes = len(escape_matches) > 5
    results.append({
        "check": "유니코드 이스케이프 없음 (\\uXXXX)",
        "passed": not excessive_escapes,
        "detail": f"이스케이프 시퀀스 {len(escape_matches)}개 발견" if escape_matches
                  else "한국어 문자가 올바르게 인코딩됨"
    })

    # 4. Contains actual Korean characters
    korean_chars = re.findall(r'[\uAC00-\uD7A3]', content)
    has_korean = len(korean_chars) >= 20  # at least 20 Korean chars expected
    results.append({
        "check": "한국어 문자 포함",
        "passed": has_korean,
        "detail": f"한국어 문자 {len(korean_chars)}개 발견" if has_korean
                  else f"한국어 문자 {len(korean_chars)}개만 발견 — 내용이 한국어로 작성됐는지 확인 필요"
    })

    # 5. TL;DR box present
    has_tldr = bool(re.search(r'tldr|한 줄 요약|TL;DR', content))
    results.append({
        "check": "TL;DR 박스 포함",
        "passed": has_tldr,
        "detail": "TL;DR 섹션 발견" if has_tldr else "TL;DR 박스 없음"
    })

    # 6. Filter bar present
    has_filter = bool(re.search(r'filter-bar|filterCards|filter-btn', content))
    results.append({
        "check": "카테고리 필터 바 포함",
        "passed": has_filter,
        "detail": "필터 버튼 발견" if has_filter else "필터 바 없음"
    })

    # 7. At least one card present
    card_count = len(re.findall(r'class=["\']card', content))
    results.append({
        "check": "카드 최소 1개 이상",
        "passed": card_count >= 1,
        "detail": f"카드 {card_count}개 발견"
    })

    # 8. Action items section present (if any URL had actionable content)
    has_action = bool(re.search(r'action-items|따라할 단계|실행 명령어|cmd-block', content))
    results.append({
        "check": "액션 아이템 섹션 포함 (있는 경우)",
        "passed": True,  # not mandatory — just informational
        "detail": "액션 아이템 섹션 있음" if has_action else "액션 아이템 없음 (해당 URL에 없을 수 있음)",
        "warning_only": not has_action
    })

    return results


def check_docx(docx_path: Path) -> list[dict]:
    results = []

    size = docx_path.stat().st_size
    # A minimal docx with just a title is ~5-7KB; real content should be >10KB
    is_reasonable_size = size > 8_000
    results.append({
        "check": "DOCX 파일 존재 및 크기 확인",
        "passed": is_reasonable_size,
        "detail": f"{docx_path.name} ({size:,} bytes)" + ("" if is_reasonable_size else " — 너무 작음, 내용이 비어있을 수 있음")
    })

    # Try opening with python-docx if available
    try:
        from docx import Document
        doc = Document(str(docx_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        total_text = "\n".join(paragraphs)
        korean_in_docx = len(re.findall(r'[\uAC00-\uD7A3]', total_text))
        has_korean = korean_in_docx >= 10

        results.append({
            "check": "DOCX 내 한국어 내용 확인",
            "passed": has_korean,
            "detail": f"한국어 문자 {korean_in_docx}개, 단락 {len(paragraphs)}개"
        })

        # Check for unicode escape sequences in DOCX text (shouldn't be there)
        has_raw_escapes = bool(re.search(r'\\u[0-9a-fA-F]{4}', total_text))
        results.append({
            "check": "DOCX에 유니코드 이스케이프 없음",
            "passed": not has_raw_escapes,
            "detail": "DOCX 텍스트 인코딩 정상" if not has_raw_escapes else "DOCX에 \\uXXXX 이스케이프 시퀀스 발견 — Python 인코딩 문제"
        })

    except ImportError:
        results.append({
            "check": "DOCX 내용 검증 (python-docx 필요)",
            "passed": True,
            "detail": "python-docx 미설치 — 파일 크기로만 검증",
            "warning_only": True
        })
    except Exception as e:
        results.append({
            "check": "DOCX 파일 열기",
            "passed": False,
            "detail": f"오류: {e}"
        })

    return results


def print_results(label: str, results: list[dict]) -> int:
    """Print results and return number of failures."""
    print(f"\n{'─'*50}")
    print(f"  {label}")
    print(f"{'─'*50}")
    failures = 0
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
    return failures


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "/sessions/inspiring-dazzling-hawking/mnt/ai_skills"

    print(f"\n{'═'*50}")
    print(f"  Tab Digest 출력 검증")
    print(f"  디렉토리: {output_dir}")
    print(f"{'═'*50}")

    html_path, docx_path = find_output_files(output_dir)
    total_failures = 0

    if html_path:
        html_results = check_html(html_path)
        total_failures += print_results(f"HTML: {html_path.name}", html_results)
    else:
        print(f"\n  {FAIL}  HTML 파일 없음 (tab-digest*.html)")
        total_failures += 1

    if docx_path:
        docx_results = check_docx(docx_path)
        total_failures += print_results(f"DOCX: {docx_path.name}", docx_results)
    else:
        print(f"\n  {FAIL}  DOCX 파일 없음 (tab-digest*.docx)")
        total_failures += 1

    print(f"\n{'═'*50}")
    if total_failures == 0:
        print(f"  {PASS}  모든 검증 통과!")
    else:
        print(f"  {FAIL}  {total_failures}개 항목 실패 — 위 내용 확인 필요")
    print(f"{'═'*50}\n")

    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
