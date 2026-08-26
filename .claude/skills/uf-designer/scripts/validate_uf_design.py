#!/usr/bin/env python3
"""
validate_uf_design.py — uf-designer output validator

Usage:
    python validate_uf_design.py uf.md

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
"""

import re
import sys
from pathlib import Path


def validate_uf_blocks(content: str) -> list[str]:
    failures = []

    if len(content.strip()) < 200:
        return ["uf.md appears too short — likely incomplete"]

    # 1. Must have at least one UF block
    uf_ids = re.findall(r"UF-\d{2}-\d{2}", content)
    if not uf_ids:
        failures.append("No UF-##-## IDs found in uf.md")
        return failures

    # 2. UF-IDs must follow UF-[parent_IF_num]-[seq] pattern and be sequential per IF
    all_ids = re.findall(r"UF-(\d{2})-(\d{2})", content)
    by_if: dict[str, list[int]] = {}
    for if_num, uf_seq in all_ids:
        by_if.setdefault(if_num, []).append(int(uf_seq))
    for if_num, seqs in by_if.items():
        seqs_sorted = sorted(set(seqs))
        expected = list(range(1, len(seqs_sorted) + 1))
        if seqs_sorted != expected:
            failures.append(
                f"UF-{if_num}-XX sequence is not contiguous starting from 01: {seqs_sorted}"
            )

    # 3. Split content into individual UF blocks
    blocks = re.split(r"(?=- UF-ID: UF-\d{2}-\d{2})", content)
    blocks = [b for b in blocks if "- UF-ID:" in b]

    required_fields = [
        "- UF-ID:",
        "- Parent IF:",
        "- Goal:",
        "- I/O Contract:",
        "- Algorithm Summary:",
        "- Edge Cases:",
        "- Verification Plan:",
        "- Evidence Pack Fields:",
    ]

    for block in blocks:
        uf_match = re.search(r"UF-\d{2}-\d{2}", block)
        label = uf_match.group() if uf_match else "UNKNOWN"

        # 4. Required fields
        for field in required_fields:
            if field not in block:
                failures.append(f"{label}: missing field '{field}'")

        # 5. Goal must be a single verb phrase (non-empty, not placeholder)
        goal_match = re.search(r"- Goal:\s*(.+)", block)
        if goal_match:
            goal = goal_match.group(1).strip()
            if not goal or goal.startswith("<"):
                failures.append(f"{label}: Goal is empty or still a placeholder")
        else:
            failures.append(f"{label}: Goal field missing or malformed")

        # 6. I/O Contract must specify Input and Output (not just a blank line)
        io_section = re.search(
            r"- I/O Contract:\s*\n(.*?)(?=\n- Algorithm Summary:)", block, re.DOTALL
        )
        if io_section:
            io_body = io_section.group(1)
            if "Input:" not in io_body:
                failures.append(f"{label}: I/O Contract missing 'Input:' line")
            if "Output:" not in io_body:
                failures.append(f"{label}: I/O Contract missing 'Output:' line")
            # Warn if type/shape/range look like placeholders
            if "<type>" in io_body or "<name>" in io_body:
                failures.append(f"{label}: I/O Contract still contains placeholders")
        else:
            failures.append(f"{label}: I/O Contract section not found")

        # 7. Algorithm Summary: must have content, 1–3 lines
        alg_section = re.search(
            r"- Algorithm Summary:\s*\n(.*?)(?=\n- Edge Cases:)", block, re.DOTALL
        )
        if alg_section:
            alg_body = alg_section.group(1).strip()
            if not alg_body or alg_body.startswith("<"):
                failures.append(f"{label}: Algorithm Summary is empty or placeholder")
            lines = [l for l in alg_body.splitlines() if l.strip()]
            if len(lines) > 3:
                failures.append(
                    f"{label}: Algorithm Summary is {len(lines)} lines — keep to 1–3"
                )
        else:
            failures.append(f"{label}: Algorithm Summary section not found")

        # 8. Edge Cases: must have at least 3 entries
        edge_section = re.search(
            r"- Edge Cases:\s*\n(.*?)(?=\n- Verification Plan:)", block, re.DOTALL
        )
        if edge_section:
            edge_body = edge_section.group(1)
            edge_entries = re.findall(r"^\s*-\s+\S", edge_body, re.MULTILINE)
            if len(edge_entries) < 3:
                failures.append(
                    f"{label}: only {len(edge_entries)} edge case(s) — minimum 3 required"
                )
        else:
            failures.append(f"{label}: Edge Cases section not found")

        # 9. Verification Plan: ownership-aware (v2 format per SKILL.md).
        #    Legacy v1 (Unit:/Coverage:, no Ownership) is accepted for old documents.
        #    (Fixes historical drift: the old check required v1 literals and failed
        #     documents that correctly followed the v2 template.)
        verif_section = re.search(
            r"- Verification Plan:\s*\n(.*?)(?=\n- Evidence Pack Fields:|\Z)",
            block,
            re.DOTALL,
        )
        if verif_section:
            verif_body = verif_section.group(1)
            own_match = re.search(r"Ownership:\s*(\S+)", verif_body)
            if own_match:
                ownership = own_match.group(1)
                has_unit_path = bool(
                    re.search(r"Unit Verification:", verif_body)
                    and re.search(r"(::\w+|tests?/\S+)", verif_body)
                )
                chain_m = re.search(
                    r"Chain Verification:\s*\n?\s*-?\s*(.+)", verif_body
                )
                chain_val = chain_m.group(1).strip() if chain_m else ""
                chain_named = bool(
                    chain_val and not chain_val.upper().startswith("N/A")
                )
                if ownership == "UF-local":
                    if not has_unit_path:
                        failures.append(
                            f"{label}: UF-local requires a concrete Unit Verification test path"
                        )
                    if not re.search(r"Coverage", verif_body):
                        failures.append(
                            f"{label}: UF-local requires a Coverage target"
                        )
                elif ownership in ("guard-rail+chain", "IF-acceptance"):
                    if not chain_named:
                        failures.append(
                            f"{label}: ownership '{ownership}' requires a named Chain Verification path"
                        )
                else:
                    failures.append(
                        f"{label}: unknown Ownership '{ownership}' "
                        "(expected UF-local | guard-rail+chain | IF-acceptance)"
                    )
            else:
                # legacy v1 fallback
                v1_ok = (
                    "Unit:" in verif_body
                    and "::" in verif_body
                    and "Coverage:" in verif_body
                )
                if not v1_ok:
                    failures.append(
                        f"{label}: Verification Plan lacks 'Ownership:' (v2) and is not a "
                        "complete legacy v1 plan (Unit:/path::func/Coverage:)"
                    )
        else:
            failures.append(f"{label}: Verification Plan section not found")

    return failures


def check_tally_consistency(content: str) -> list[str]:
    """Four-way tally cross-check: header total / summary table / body blocks /
    ownership distribution. Guards against the amendment-desync defect class
    (blocks added but header/table/distribution left stale → false '+N blocks PASS').

    All four representations are REQUIRED — absence is a failure, not a silent skip
    (a check that can silently skip is a check that cannot fail)."""
    failures = []
    body_ids = re.findall(r"^- UF-ID: (UF-\d{2}-\d{2})", content, re.MULTILINE)
    block_count = len(body_ids)

    # 1) header total: "Total UFs: N" | "UF 총계: N" | legacy "UF N개"
    header_match = re.search(
        r"(?:Total\s+UFs?|UF\s*총계)\s*[:：]\s*(\d+)|UF\s+(\d+)개", content
    )
    if not header_match:
        failures.append(
            "header total declaration not found — uf.md must declare "
            "'Total UFs: <N> (UF-local a / guard-rail+chain b / IF-acceptance c)'"
        )
    else:
        declared_total = int(header_match.group(1) or header_match.group(2))
        if declared_total != block_count:
            failures.append(
                f"header declares {declared_total} UFs but body has {block_count} blocks"
            )

    # 2) summary table: set of UF-IDs in table rows must equal set of body block IDs
    table_ids = set(re.findall(r"^\|\s*(UF-\d{2}-\d{2})\s*\|", content, re.MULTILINE))
    if not table_ids:
        failures.append(
            "summary table not found — uf.md must contain a summary table with one "
            "'| UF-##-## | ... |' row per UF"
        )
    else:
        body_set = set(body_ids)
        if table_ids != body_set:
            only_table = sorted(table_ids - body_set)
            only_body = sorted(body_set - table_ids)
            parts = []
            if only_table:
                parts.append(f"in table only: {only_table}")
            if only_body:
                parts.append(f"in body only: {only_body}")
            failures.append("summary table ≠ body blocks — " + "; ".join(parts))

    # 3) ownership distribution declaration vs actual Ownership: field counts
    own = {"UF-local": 0, "guard-rail+chain": 0, "IF-acceptance": 0}
    for m in re.findall(r"^\s*Ownership:\s*(\S+)", content, re.MULTILINE):
        if m in own:
            own[m] += 1
    decl = re.search(
        r"UF-local\s+(\d+)\s*/\s*guard-rail\+chain\s+(\d+)\s*/\s*IF-acceptance\s+(\d+)",
        content,
    )
    if not decl:
        failures.append(
            "ownership distribution declaration not found — header must include "
            "'(UF-local a / guard-rail+chain b / IF-acceptance c)'"
        )
    elif sum(own.values()) > 0:
        declared = (int(decl.group(1)), int(decl.group(2)), int(decl.group(3)))
        actual = (own["UF-local"], own["guard-rail+chain"], own["IF-acceptance"])
        if declared != actual:
            failures.append(
                f"ownership distribution declared {declared} != counted {actual} "
                f"(UF-local/guard-rail+chain/IF-acceptance)"
            )
    return failures


def check_io_chain(content: str) -> list[str]:
    """
    Heuristic chain-continuity check: within each IF group, verify that
    the output type token of UF-N appears as the input type token of UF-(N+1).
    Flags known chain-break patterns.
    """
    warnings = []

    known_breaks = [
        ("uint8", "float32"),
        ("(H, W, C)", "(C, H, W)"),
        ("(H,W,C)", "(C,H,W)"),
        ("List[dict]", "ndarray"),
        ("pixel", "normalized"),
    ]

    # Group UF blocks by parent IF
    blocks = re.split(r"(?=- UF-ID: UF-\d{2}-\d{2})", content)
    blocks = [b for b in blocks if "- UF-ID:" in b]

    by_if: dict[str, list[tuple[str, str, str]]] = {}
    for block in blocks:
        uf_match = re.search(r"(UF-(\d{2})-\d{2})", block)
        if not uf_match:
            continue
        uf_id = uf_match.group(1)
        if_num = uf_match.group(2)

        # Extract output type from I/O Contract
        out_match = re.search(r"Output:\s+\S+:\s+(\S+)", block)
        in_match = re.search(r"Input:\s+\S+:\s+(\S+)", block)
        out_type = out_match.group(1).rstrip(",") if out_match else ""
        in_type = in_match.group(1).rstrip(",") if in_match else ""

        by_if.setdefault(if_num, []).append((uf_id, in_type, out_type))

    for if_num, uf_list in by_if.items():
        # Sort by UF sequence number
        uf_list_sorted = sorted(uf_list, key=lambda x: x[0])
        for i in range(len(uf_list_sorted) - 1):
            cur_id, _, cur_out = uf_list_sorted[i]
            nxt_id, nxt_in, _ = uf_list_sorted[i + 1]
            if cur_out and nxt_in and cur_out != nxt_in:
                warnings.append(
                    f"[CHAIN BREAK: {cur_id} → {nxt_id}: output '{cur_out}' ≠ input '{nxt_in}']"
                )
            # Check known problematic patterns
            for bad_out, bad_in in known_breaks:
                if bad_out in cur_out and bad_in in nxt_in:
                    warnings.append(
                        f"[KNOWN ANTI-PATTERN: {cur_id} → {nxt_id}: {bad_out} → {bad_in} — add explicit conversion UF]"
                    )

    return warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_uf_design.py uf.md")
        sys.exit(1)

    uf_path = sys.argv[1]
    if not Path(uf_path).exists():
        print(f"❌ File not found: {uf_path}")
        sys.exit(1)

    content = Path(uf_path).read_text(encoding="utf-8")

    block_failures = validate_uf_blocks(content)
    tally_failures = check_tally_consistency(content)
    chain_warnings = check_io_chain(content)

    all_issues = (
        [f"[structure] {f}" for f in block_failures]
        + [f"[tally]     {f}" for f in tally_failures]
        + [f"[chain]     {w}" for w in chain_warnings]
    )

    if not all_issues:
        # Count blocks by their header line ONLY. Counting every "UF-##-##"
        # occurrence also counts summary-table rows and cross-references —
        # the historical cause of inflated "N blocks PASS" false reports.
        uf_count = len(re.findall(r"^- UF-ID: UF-\d{2}-\d{2}", content, re.MULTILINE))
        print(
            f"✅ UF design passed all checks "
            f"({uf_count} UF blocks validated; header/table/ownership tallies consistent)"
        )
        sys.exit(0)
    else:
        print(f"❌ {len(all_issues)} issue(s) found:\n")
        for issue in all_issues:
            print(f"  ✗ {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
