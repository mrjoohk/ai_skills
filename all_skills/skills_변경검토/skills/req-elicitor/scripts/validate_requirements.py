#!/usr/bin/env python3
"""
validate_requirements.py — req-elicitor output validator

Usage:
    python validate_requirements.py requirements.md

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
"""

import re
import sys
from pathlib import Path


def validate(path: str) -> list[str]:
    failures = []
    content = Path(path).read_text(encoding="utf-8")

    # 1. File must be non-trivial
    if len(content.strip()) < 300:
        failures.append("requirements.md appears too short (< 300 chars) — likely incomplete")
        return failures  # no point checking further

    # 2. Must contain at least one REQ block
    req_ids = re.findall(r"REQ-\d{3}", content)
    if not req_ids:
        failures.append("No REQ-### IDs found — write at least one REQ block")
    else:
        # 3. IDs must be sequential and unique
        nums = sorted(int(r.split("-")[1]) for r in set(req_ids))
        if nums != list(range(nums[0], nums[0] + len(nums))):
            failures.append(f"REQ IDs are not sequential: {req_ids}")
        if len(req_ids) != len(set(req_ids)):
            duplicates = [r for r in set(req_ids) if req_ids.count(r) > 1]
            failures.append(f"Duplicate REQ IDs: {duplicates}")

    # 4. Every REQ block must have required fields
    req_blocks = re.split(r"(?=- ID: REQ-\d{3})", content)
    required_fields = ["- ID:", "- Title:", "- Context:", "- Inputs:", "- Outputs:",
                       "- Constraints:", "- Acceptance Criteria:", "- Tests:", "- Evidence:"]

    for block in req_blocks:
        if "- ID: REQ-" not in block:
            continue
        req_id = re.search(r"REQ-\d{3}", block)
        req_label = req_id.group() if req_id else "UNKNOWN"
        for field in required_fields:
            if field not in block:
                failures.append(f"{req_label}: missing field '{field}'")

    # 5. Acceptance Criteria must use Given/When/Then
    ac_blocks = re.findall(
        r"- Acceptance Criteria:(.*?)(?=- Tests:)", content, re.DOTALL
    )
    for i, ac in enumerate(ac_blocks):
        ac_clean = ac.strip()
        if not ac_clean:
            failures.append(f"REQ block #{i+1}: Acceptance Criteria is empty")
            continue
        if "Given" not in ac_clean:
            failures.append(f"REQ block #{i+1}: Acceptance Criteria missing 'Given'")
        if "When" not in ac_clean:
            failures.append(f"REQ block #{i+1}: Acceptance Criteria missing 'When'")
        if "Then" not in ac_clean:
            failures.append(f"REQ block #{i+1}: Acceptance Criteria missing 'Then'")

    # 6. Acceptance Criteria must contain at least one numeric threshold
    for i, ac in enumerate(ac_blocks):
        has_number = bool(re.search(r"\d+\s*(%|ms|MB|GB|fps|Hz|W|s\b|sec|minute|hour|req|req/s|rps)", ac))
        has_decimal = bool(re.search(r"[<>≤≥]=?\s*\d+\.?\d*", ac))
        if not has_number and not has_decimal:
            failures.append(
                f"REQ block #{i+1}: Acceptance Criteria has no numeric threshold "
                f"(add e.g. '≤ 200ms', '≥ 0.85', '< 4GB')"
            )

    # 7. Inputs/Outputs must not be empty or just whitespace
    io_fields = re.findall(r"- (Inputs|Outputs):\s*\n(.*?)(?=\n-)", content, re.DOTALL)
    for field_name, field_body in io_fields:
        stripped = field_body.strip()
        if not stripped or stripped.startswith("-"):
            failures.append(f"A '{field_name}' field appears to be empty — add type/unit/range")

    # 8. Tests field must name all three test levels
    test_blocks = re.findall(r"- Tests:(.*?)(?=- Evidence:)", content, re.DOTALL)
    for i, tb in enumerate(test_blocks):
        for level in ["Unit:", "Integration:", "E2E:"]:
            if level not in tb:
                failures.append(f"REQ block #{i+1}: Tests field missing '{level}'")

    # 9. Must have both Functional and Non-Functional sections (warn only)
    if "Functional Requirements" not in content:
        failures.append("Missing '## Functional Requirements' section heading")
    if "Non-Functional Requirements" not in content:
        failures.append("WARNING: No '## Non-Functional Requirements' section — add performance/reliability REQs")

    return failures


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_requirements.py requirements.md")
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    failures = validate(path)

    if not failures:
        req_count = len(re.findall(r"REQ-\d{3}", Path(path).read_text()))
        print(f"✅ requirements.md passed all checks ({req_count} REQ blocks found)")
        sys.exit(0)
    else:
        print(f"❌ {len(failures)} issue(s) found in {path}:\n")
        for f in failures:
            prefix = "⚠️ " if f.startswith("WARNING") else "  ✗ "
            print(f"{prefix}{f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
