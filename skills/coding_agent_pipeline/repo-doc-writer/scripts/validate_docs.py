#!/usr/bin/env python3
"""Validate generated coding-agent documents and coverage of declared UF blocks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

UF_ID = r"UF-\d+(?:-\d+)*"
PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}|<(?:UF_ID|IF_ID|Project Name|UF Name)>")
PENDING = re.compile(r"\bTODO\b|근거 필요|미확정|정보 없음", re.I)
TASK_SECTIONS = ("Goal", "Signature", "Input / Output Contract", "Edge Cases", "Verification")


def without_fences(text):
    output, fenced = [], False
    for line in text.splitlines():
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            fenced = not fenced
        elif not fenced:
            output.append(line)
    return "\n".join(output)


def uf_ids(text):
    """Read UF declarations, not incidental references to IDs in prose/contracts."""
    clean = without_fences(re.sub(r"<!--.*?-->", "", text, flags=re.S))
    found = re.findall(r"(?mi)^\s*(?:[-*]\s*)?(?:\*\*)?UF-ID(?:\*\*)?\s*:\s*(?:\*\*)?(" + UF_ID + r")\b", clean)
    if not found:
        found = re.findall(r"(?mi)^#{1,6}\s+(" + UF_ID + r")\b", clean)
    return set(found)


def sections(text):
    """Locate standard H2 sections while preserving fenced signature contents."""
    result, current, fenced = {}, None, False
    for line in text.splitlines():
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            fenced = not fenced
        match = re.match(r"^##\s+(.+?)\s*$", line) if not fenced else None
        if match:
            current = match.group(1)
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return {key: "\n".join(value).strip() for key, value in result.items()}


def validate(root: Path, docs_dir: Path | None = None, uf_path: Path | None = None, allow_partial=False):
    root = root.resolve()
    docs = docs_dir or Path("docs/ai")
    docs = docs.resolve() if docs.is_absolute() else (root / docs).resolve()
    findings, files = [], []

    def issue(code, message, path=None, partial=False):
        findings.append({"code": code, "severity": "warning" if partial and allow_partial else "error",
                         "message": message, **({"path": str(path)} if path else {})})

    def read(path):
        if not path.is_file():
            issue("MISSING_FILE", "Expected generated document is missing", path)
            return None
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            issue("UNREADABLE_FILE", str(exc), path)
            return None
        files.append(str(path))
        if not text.strip():
            issue("EMPTY_FILE", "Generated document is empty", path)
            return None
        if PLACEHOLDER.search(text):
            issue("UNFILLED_TEMPLATE", "Template placeholders remain", path, partial=True)
        # TODO is a normal implementation status, but unfinished contract text is a gap.
        content = "\n".join(line for line in text.splitlines() if not re.match(r"^\*\*Status:\*\*", line))
        if PENDING.search(content):
            issue("UNRESOLVED_CONTENT", "Document explicitly contains unresolved content", path, partial=True)
        return text

    overview = read(docs / "overview.md")
    if overview:
        found = sections(overview)
        for title in ("Purpose", "Integration Functions", "Key Constraints"):
            if not found.get(title):
                issue("MISSING_OVERVIEW_SECTION", f"Missing or empty {title}", docs / "overview.md")
    architecture = read(docs / "architecture.md")
    if architecture and not re.search(r"```mermaid\s+\S", architecture):
        issue("MISSING_DEPENDENCY_GRAPH", "Architecture needs a nonempty Mermaid graph or an explicit partial draft", docs / "architecture.md", partial=True)

    expected = set()
    if uf_path is None:
        candidates = [root / p for p in ("uf.md", "rd/uf.md", "design/uf.md", "docs/uf.md") if (root / p).is_file()]
        if len(candidates) > 1:
            issue("AMBIGUOUS_UF_SOURCE", "Multiple UF sources found; pass --uf explicitly")
        elif candidates:
            uf_path = candidates[0]
        else:
            findings.append({"code": "NO_UF_SOURCE", "severity": "warning", "message": "UF coverage not checked; pass --uf to check it"})
    if uf_path is not None:
        source = uf_path if uf_path.is_absolute() else root / uf_path
        if not source.is_file():
            issue("MISSING_UF_SOURCE", "Specified UF source does not exist", source)
        else:
            try:
                expected = uf_ids(source.read_text(encoding="utf-8-sig"))
                if not expected:
                    issue("NO_UF_DECLARATIONS", "No concrete UF-ID declarations found in source", source, partial=True)
            except (OSError, UnicodeError) as exc:
                issue("UNREADABLE_UF_SOURCE", str(exc), source)

    taskpaths = sorted((docs / "tasks").glob("*.md")) if (docs / "tasks").is_dir() else []
    if not taskpaths:
        issue("NO_TASKS", "No UF task files found", docs / "tasks", partial=not expected)
    actual = set()
    for path in taskpaths:
        text = read(path)
        if text is None:
            continue
        title = re.search(r"(?m)^#\s+(" + UF_ID + r")\b", without_fences(text))
        if title is None:
            issue("MISSING_TASK_ID", "Task title must identify its UF", path)
        else:
            identity = title.group(1)
            if identity in actual:
                issue("DUPLICATE_TASK", f"UF has multiple task files: {identity}", path)
            actual.add(identity)
            if path.stem != identity:
                issue("TASK_FILENAME_ID", f"Expected filename {identity}.md", path)
        if not re.search(r"\*\*Parent IF:\*\*\s+IF-\d+\b", text):
            issue("MISSING_PARENT_IF", "Task needs a concrete parent IF", path, partial=True)
        found = sections(text)
        for title in TASK_SECTIONS:
            if not found.get(title):
                issue("MISSING_TASK_SECTION", f"Missing or empty {title}", path)
        contract = found.get("Input / Output Contract", "")
        for direction in ("Input", "Output"):
            row = re.search(r"(?mi)^\|\s*" + direction + r"\s*\|([^\n]+)$", contract)
            cells = [x.strip() for x in row.group(1).rstrip("|").split("|")] if row else []
            if len(cells) < 3 or not cells[0] or not cells[1]:
                issue("INCOMPLETE_IO_CONTRACT", f"{direction} needs a description and type/shape", path, partial=True)
        if found.get("Verification") and not re.search(r"(?m)^\s*-\s+(?:\[[ xX]\]\s+)?\S", found["Verification"]):
            issue("MISSING_ACCEPTANCE_CRITERIA", "Verification needs observable criteria", path, partial=True)
    for identity in sorted(expected - actual):
        issue("UNCOVERED_UF", f"Missing task for declared {identity}", docs / "tasks" / (identity + ".md"))
    for identity in sorted(actual - expected) if expected else []:
        issue("UNKNOWN_UF", f"Task {identity} is absent from the selected UF source", docs / "tasks" / (identity + ".md"))
    errors = [x for x in findings if x["severity"] == "error"]
    return {"passed": not errors, "complete": not findings, "findings": findings,
            "coverage": {"expected": sorted(expected), "actual": sorted(actual), "checked": bool(expected)}, "files": files}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--docs-dir", type=Path, default=Path("docs/ai"))
    parser.add_argument("--uf", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.root, args.docs_dir, args.uf, args.allow_partial)
    print("RESULT_JSON=" + json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
