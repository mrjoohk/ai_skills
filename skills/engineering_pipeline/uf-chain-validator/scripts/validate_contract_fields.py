#!/usr/bin/env python3
"""
validate_contract_fields.py — Gate 1 mechanization: field-level comparison of
IF contract struct field lists (design doc) vs code type declarations.

The contract mapping is PROJECT data and lives in the project, not in this skill:
    rd/contracts.json   (fallback: contracts.json at repo root)
See <skill_dir>/assets/contracts.example.json for the schema.

Schema (list of entries):
    id           — label, e.g. "IF-01.state"
    doc          — design doc path, e.g. "rd/if_list.md"
    doc_pattern  — regex whose group(1) captures the comma-separated field list,
                   e.g. "state:\\s*struct,\\s*\\{([^}]*)\\}"
    code         — code file containing the type declaration
    code_struct  — struct/class name to compare against
    aliases      — optional {contract_field: [accepted code identifiers]}
                   (a field with no alias entry must appear under its own name)

Language-agnostic text comparison: a contract field is satisfied if any of its
accepted identifiers appears as a word inside the struct/class body.
(Presence check only — type/unit correctness stays with human review / Gate 1 runtime.)

Usage: python validate_contract_fields.py [repo_root] [--contracts <path>]
Exit:  0 all satisfied / 1 missing fields or mapping errors / 2 no contracts file (not configured)
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_LOCATIONS = ["rd/contracts.json", "contracts.json"]


def struct_body(text: str, name: str) -> str:
    """Body of `struct|class <name> ... { ... }` with brace matching
    (tolerates final/alignas/inheritance between name and brace)."""
    m = re.search(rf"\b(?:struct|class)\s+{re.escape(name)}\b[^{{;]*\{{", text)
    if not m:
        return ""
    i, depth, j = m.end(), 1, m.end()
    while j < len(text) and depth:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[i:j]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--contracts", default=None,
                    help="contracts JSON path (default: rd/contracts.json, then ./contracts.json)")
    args = ap.parse_args()
    root = Path(args.root)

    cpath = None
    if args.contracts:
        cpath = Path(args.contracts)
        if not cpath.is_absolute():
            cpath = root / cpath
    else:
        for loc in DEFAULT_LOCATIONS:
            if (root / loc).exists():
                cpath = root / loc
                break
    if cpath is None or not cpath.exists():
        print("no contracts file found (rd/contracts.json) — Gate 1 field check NOT CONFIGURED.\n"
              "Create it from <skill_dir>/assets/contracts.example.json to enable this gate.")
        sys.exit(2)

    try:
        contracts = json.loads(cpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL — {cpath} is not valid JSON: {e}")
        sys.exit(1)

    fail = 0
    for c in contracts:
        cid = c.get("id", "?")
        doc_file = root / c["doc"]
        if not doc_file.exists():
            print(f"[{cid}] FAIL — design doc not found: {c['doc']}")
            fail = 1
            continue
        m = re.search(c["doc_pattern"], doc_file.read_text(encoding="utf-8"))
        if not m:
            print(f"[{cid}] FAIL — doc_pattern not found in {c['doc']}")
            fail = 1
            continue
        fields = [f.strip().split()[0].rstrip(",") for f in m.group(1).split(",") if f.strip()]

        code_file = root / c["code"]
        if not code_file.exists():
            print(f"[{cid}] FAIL — code file not found: {c['code']}")
            fail = 1
            continue
        body = struct_body(code_file.read_text(encoding="utf-8", errors="replace"), c["code_struct"])
        if not body:
            print(f"[{cid}] FAIL — struct/class {c['code_struct']} not found in {c['code']}")
            fail = 1
            continue

        aliases = c.get("aliases", {})
        missing = []
        for f in fields:
            accepted = aliases.get(f, [f])
            if not any(re.search(rf"\b{re.escape(a)}\b", body) for a in accepted):
                missing.append(f"{f} (accepted: {accepted})")
        if missing:
            print(f"[{cid}] FAIL — {len(missing)}/{len(fields)} contract fields missing in "
                  f"{c['code']}::{c['code_struct']}: " + ", ".join(missing))
            fail = 1
        else:
            print(f"[{cid}] OK — all {len(fields)} contract fields present in "
                  f"{c['code']}::{c['code_struct']}")
    sys.exit(fail)


if __name__ == "__main__":
    main()
