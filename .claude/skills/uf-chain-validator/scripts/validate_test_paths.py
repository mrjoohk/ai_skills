#!/usr/bin/env python3
"""
validate_test_paths.py — Gate 2 mechanization: exhaustive declaration→artifact check
of test/script paths and `::function` tokens declared in design documents.

Usage:
    python validate_test_paths.py [--root <repo_root>] [--strict] [--docs GLOB ...]

Default target documents (sources of declarations only — historical review docs excluded):
    rd/uf.md, rd/requirements.md, rd/uf_split/*.md
    (legacy fallback: uf.md, requirements.md, uf_split/*.md at repo root)

Buckets:
    OK         — file (and function) exists
    PLANNED    — declaration line carries an explicit plan marker (`PLANNED` or `예정`,
                 optionally with milestone tag e.g. `(PLANNED M4)`) — informational, never FAIL
    MISSING    — file absent, no plan marker → report-only; FAIL with --strict
                 (policy: treat as FAIL for any IF/REQ scope declared complete)
    GHOST_FUNC — file exists but declared function does not → ALWAYS FAIL ("false declaration")

Check direction is strictly declaration → artifact. Never enumerate existing files and
confirm presence (reverse direction is a documented cause of false PASS).

Exit: GHOST_FUNC > 0 → 1 / --strict and MISSING > 0 → 1 / otherwise 0
"""
import argparse
import re
import signal
import sys
from pathlib import Path

try:  # avoid traceback when piped into head etc.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

DEFAULT_DOC_GLOBS = [
    "rd/uf.md", "rd/requirements.md", "rd/uf_split/*.md",
    # legacy layouts (project root)
    "uf.md", "requirements.md", "uf_split/*.md",
]
PATH_RE = re.compile(r"\b((?:tests|scripts)/[A-Za-z0-9_\-./]*\.(?:py|cpp|cc|cxx|hpp|hh|sh|md|scn|yaml|json))\b")
FUNC_RE = re.compile(r"\b([A-Za-z0-9_\-./]+\.(?:py|cpp|cc|cxx|hpp|hh))::([A-Za-z_]\w*)")
PLAN_RE = re.compile(r"PLANNED|예정", re.IGNORECASE)
MILESTONE_RE = re.compile(r"\bM\d+\b")

C_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)


def line_of(text: str, pos: int) -> str:
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    return text[a:b if b != -1 else len(text)]


def plan_note(line: str) -> str:
    ms = MILESTONE_RE.search(line)
    return f"plan marker on line{f' ({ms.group(0)})' if ms else ''} — declared not-yet-implemented"


def func_exists(fp: Path, fn: str) -> bool:
    """Function existence with false-OK guards:
    .py  — a real `def <fn>(` at line start (commented-out defs don't match ^\\s*def)
    C/C++ — `<fn>(` as a word after stripping // and /* */ comments
            (a name that only appears in a TODO comment must NOT count)"""
    body = fp.read_text(encoding="utf-8", errors="replace")
    if fp.suffix == ".py":
        return bool(re.search(rf"^\s*def\s+{re.escape(fn)}\s*\(", body, re.MULTILINE))
    stripped = C_COMMENT_RE.sub("", body)
    return bool(re.search(rf"\b{re.escape(fn)}\s*\(", stripped))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true",
                    help="MISSING (without plan marker) also fails")
    ap.add_argument("--docs", nargs="*", default=None,
                    help="override document globs (relative to --root)")
    args = ap.parse_args()
    root = Path(args.root)

    docs = []
    for g in (args.docs or DEFAULT_DOC_GLOBS):
        docs.extend(sorted(root.glob(g)))
    # rd/ takes precedence over identical legacy names
    uniq, names = [], set()
    for d in docs:
        if d.name not in names or "rd" in d.parts:
            if d not in uniq:
                uniq.append(d)
                names.add(d.name)
    docs = [d for d in uniq if d.is_file()]
    if not docs:
        print(f"no design docs found under {root} (looked for: {', '.join(args.docs or DEFAULT_DOC_GLOBS)})")
        sys.exit(1)

    rows, seen = [], set()
    for doc in docs:
        rel = str(doc.relative_to(root)) if root in doc.parents or doc.parent == root else str(doc)
        text = doc.read_text(encoding="utf-8", errors="replace")

        for m in PATH_RE.finditer(text):
            if text[m.end():m.end() + 2] == "::":
                continue  # part of a file::func token — handled below, avoid double count
            p = m.group(1)
            key = (rel, p, "")
            if key in seen:
                continue
            seen.add(key)
            if (root / p).exists():
                rows.append((rel, p, "OK", ""))
            elif PLAN_RE.search(line_of(text, m.start())):
                rows.append((rel, p, "PLANNED", plan_note(line_of(text, m.start()))))
            else:
                rows.append((rel, p, "MISSING", "file not found"))

        for m in FUNC_RE.finditer(text):
            f, fn = m.group(1), m.group(2)
            key = (rel, f, fn)
            if key in seen:
                continue
            seen.add(key)
            line = line_of(text, m.start())
            fp = root / f
            if not fp.exists():
                bucket = "PLANNED" if PLAN_RE.search(line) else "MISSING"
                note = plan_note(line) if bucket == "PLANNED" else "file not found"
                rows.append((rel, f"{f}::{fn}", bucket, note))
                continue
            if func_exists(fp, fn):
                rows.append((rel, f"{f}::{fn}", "OK", ""))
            elif PLAN_RE.search(line):
                rows.append((rel, f"{f}::{fn}", "PLANNED", plan_note(line)))
            else:
                rows.append((rel, f"{f}::{fn}", "GHOST_FUNC",
                             "file exists but function not found — false declaration"))

    ghost = [r for r in rows if r[2] == "GHOST_FUNC"]
    missing = [r for r in rows if r[2] == "MISSING"]
    planned = [r for r in rows if r[2] == "PLANNED"]
    ok_n = sum(1 for r in rows if r[2] == "OK")

    print(f"declared tokens: {len(rows)}  "
          f"(OK {ok_n} / PLANNED {len(planned)} / MISSING {len(missing)} / GHOST_FUNC {len(ghost)})")
    for name, bucket in (
        ("GHOST_FUNC (always FAIL)", ghost),
        ("PLANNED (plan marker — informational)", planned),
        ("MISSING (no marker — FAIL if scope declared complete, or with --strict)", missing),
    ):
        if bucket:
            print(f"\n[{name}]")
            for d, t, _, note in bucket:
                print(f"  {d}: {t}" + (f"  ({note})" if note else ""))

    sys.exit(1 if (ghost or (args.strict and missing)) else 0)


if __name__ == "__main__":
    main()
