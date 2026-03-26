#!/usr/bin/env python3
"""
validate_if_design.py — if-designer output validator

Usage:
    python validate_if_design.py if_list.md if_decomposition.md

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
"""

import re
import sys
from pathlib import Path


def validate_if_list(content: str) -> list[str]:
    failures = []

    if len(content.strip()) < 200:
        return ["if_list.md appears too short — likely incomplete"]

    # 1. Must have at least one IF block
    if_ids = re.findall(r"IF-\d{2}", content)
    if not if_ids:
        failures.append("No IF-## IDs found in if_list.md")
        return failures

    # 2. Unique and sequential IDs
    nums = sorted(int(i.split("-")[1]) for i in set(if_ids))
    if nums != list(range(nums[0], nums[0] + len(nums))):
        failures.append(f"IF IDs are not sequential: {sorted(set(if_ids))}")

    # 3. Required fields in each IF block
    required = ["- IF-ID:", "- Title:", "- Producer:", "- Consumer:",
                "- Input Contract:", "- Output Contract:", "- Failure Modes:", "- Linked REQs:"]
    blocks = re.split(r"(?=- IF-ID: IF-\d{2})", content)
    for block in blocks:
        if "- IF-ID:" not in block:
            continue
        if_id = re.search(r"IF-\d{2}", block)
        label = if_id.group() if if_id else "UNKNOWN"
        for field in required:
            if field not in block:
                failures.append(f"{label}: missing field '{field}'")

    # 4. Input/Output contracts must not be empty
    io_blocks = re.findall(r"- (Input|Output) Contract:\s*\n(.*?)(?=\n-)", content, re.DOTALL)
    for io_name, io_body in io_blocks:
        if not io_body.strip():
            failures.append(f"An '{io_name} Contract' field is empty — add type/unit/shape")

    # 5. Must link to at least one REQ
    linked_reqs = re.findall(r"- Linked REQs:\s*(.+)", content)
    for i, lr in enumerate(linked_reqs):
        if not lr.strip() or lr.strip() in ("-", ""):
            failures.append(f"IF block #{i+1}: Linked REQs is empty")

    # 6. Coverage matrix present
    if "REQ→IF Coverage Matrix" not in content and "Coverage Matrix" not in content:
        failures.append("Missing 'REQ→IF Coverage Matrix' section in if_list.md")

    return failures


def validate_if_decomposition(content: str, if_list_content: str) -> list[str]:
    failures = []

    if len(content.strip()) < 100:
        return ["if_decomposition.md appears too short — likely incomplete"]

    # 1. Each IF in if_list must have a decomposition section
    if_ids_in_list = set(re.findall(r"IF-\d{2}", if_list_content))
    if_ids_in_decomp = set(re.findall(r"IF-\d{2}", content))
    missing = if_ids_in_list - if_ids_in_decomp
    if missing:
        failures.append(f"IFs in if_list.md with no decomposition: {sorted(missing)}")

    # 2. UF candidates must use verb-noun naming (no spaces, has underscore)
    uf_names = re.findall(r"UF-\d{2}-\d{2}:\s*(\S+)", content)
    for name in uf_names:
        if " " in name:
            failures.append(f"UF candidate name '{name}' contains spaces — use verb_noun format")
        if "_" not in name and len(name) > 8:
            failures.append(f"UF candidate name '{name}' should use verb_noun format with underscore")

    # 3. UF candidates must have Input → Output annotation
    uf_blocks = re.findall(r"UF-\d{2}-\d{2}:.*?\n(.*?)(?=\n\s*[├└│]|\n---|\Z)", content, re.DOTALL)
    for i, block in enumerate(uf_blocks):
        if "Input:" not in block and "→" not in block:
            failures.append(f"UF candidate #{i+1}: missing Input→Output annotation")

    # 4. Must have a UF Candidate Summary table
    if "UF Candidate Summary" not in content:
        failures.append("Missing 'UF Candidate Summary' table in if_decomposition.md")

    return failures


def main():
    if len(sys.argv) < 3:
        print("Usage: python validate_if_design.py if_list.md if_decomposition.md")
        sys.exit(1)

    if_list_path, if_decomp_path = sys.argv[1], sys.argv[2]
    all_failures = []

    for path in [if_list_path, if_decomp_path]:
        if not Path(path).exists():
            print(f"❌ File not found: {path}")
            sys.exit(1)

    if_list_content = Path(if_list_path).read_text(encoding="utf-8")
    if_decomp_content = Path(if_decomp_path).read_text(encoding="utf-8")

    list_failures = validate_if_list(if_list_content)
    decomp_failures = validate_if_decomposition(if_decomp_content, if_list_content)

    all_failures = (
        [f"[if_list.md] {f}" for f in list_failures] +
        [f"[if_decomposition.md] {f}" for f in decomp_failures]
    )

    if not all_failures:
        if_count = len(set(re.findall(r"IF-\d{2}", if_list_content)))
        uf_count = len(re.findall(r"UF-\d{2}-\d{2}:", if_decomp_content))
        print(f"✅ IF design passed all checks ({if_count} IFs, {uf_count} UF candidates)")
        sys.exit(0)
    else:
        print(f"❌ {len(all_failures)} issue(s) found:\n")
        for f in all_failures:
            print(f"  ✗ {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
