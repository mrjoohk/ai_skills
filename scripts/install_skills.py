#!/usr/bin/env python3
"""Install grouped skills and their declared project tools."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "skills"


def load_catalog():
    catalog = json.loads((LIBRARY / "pipelines.json").read_text(encoding="utf-8"))
    paths = {}
    for category, names in catalog["categories"].items():
        if not re.fullmatch(r"[a-z0-9_]+", category):
            raise ValueError("Invalid category: " + category)
        for name in names:
            if not re.fullmatch(r"[a-z0-9-]+", name) or name in paths:
                raise ValueError("Invalid or duplicate skill: " + name)
            folder = LIBRARY / category / name
            if not (folder / "SKILL.md").is_file():
                raise ValueError("Missing skill: " + str(folder))
            for relative in catalog.get("skill_required_files", {}).get(name, []):
                source = (folder / relative).resolve()
                if not source.is_relative_to(folder.resolve()) or not source.is_file():
                    raise ValueError("Missing or invalid required skill resource: " + str(source))
            paths[name] = folder
    return catalog, paths


def main(argv=None):
    catalog, paths = load_catalog()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--pipeline", default="all", choices=["all", *catalog["pipelines"]])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="Replace differing files; preserve extra project files")
    parser.add_argument("--migrate-legacy", action="store_true", help="Archive unchanged retired SKILL.md entrypoints; preserve other legacy files")
    parser.add_argument("--without-project-tools", action="store_true", help="Skip tools/ and document_templates/ deployment; keep skill resources")
    args = parser.parse_args(argv)

    selected = sorted(paths) if args.pipeline == "all" else catalog["pipelines"][args.pipeline]["skills"]
    if len(selected) != len(set(selected)) or any(name not in paths for name in selected):
        parser.error("Pipeline contains duplicate or unknown skills")
    project = args.project_root.resolve()
    destination = project / ".claude" / "skills"
    if not destination.resolve().is_relative_to(project):
        parser.error("Installation directory resolves outside the requested project")
    if destination.resolve().is_relative_to(LIBRARY.resolve()):
        parser.error("Installation directory overlaps canonical skills")

    payload = []
    excludes = catalog.get("skill_install_excludes", {})
    for name in selected:
        for source in sorted(paths[name].rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            relative = source.relative_to(paths[name])
            if any(relative == Path(prefix) or Path(prefix) in relative.parents for prefix in excludes.get(name, [])):
                continue
            payload.append((source, destination / name / relative, destination))

    if not args.without_project_tools:
        for resource in catalog.get("project_resources", []):
            if not set(resource["when_skills"]) & set(selected):
                continue
            source_root = (ROOT / resource["source"]).resolve()
            relative = Path(resource["destination"])
            if (not source_root.is_relative_to(LIBRARY.resolve()) or not source_root.is_dir()
                    or relative.is_absolute() or PureWindowsPath(resource["destination"]).drive
                    or ".." in relative.parts or not relative.parts or relative.parts[0] not in {"tools", "document_templates"}):
                parser.error("Invalid project resource: " + str(resource))
            target_root = project / relative
            for required in resource.get("required_files", []):
                source = (source_root / required).resolve()
                if not source.is_relative_to(source_root) or not source.is_file():
                    parser.error("Missing or invalid required project resource: " + str(source))
            for source in sorted(source_root.rglob("*")):
                if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
                    payload.append((source, target_root / source.relative_to(source_root), target_root))

    pending, conflicts, targets = [], [], set()
    for source, target, boundary in payload:
        if not source.resolve().is_relative_to(LIBRARY.resolve()):
            parser.error("Source resolves outside canonical skills: " + str(source))
        resolved = target.resolve()
        if target in targets:
            parser.error("Duplicate deployment target: " + str(target))
        targets.add(target)
        for parent in target.parents:
            if parent.exists() and not parent.is_dir():
                parser.error("Directory target is a file: " + str(parent))
            if parent == project:
                break
        if not resolved.is_relative_to(project) or not resolved.is_relative_to(boundary.resolve()):
            parser.error("Linked path escapes installation directory: " + str(target))
        if resolved.is_relative_to(LIBRARY.resolve()):
            parser.error("Linked path overlaps canonical skills: " + str(target))
        if target.exists():
            if not target.is_file():
                parser.error("File target is a directory: " + str(target))
            if source.read_bytes() == target.read_bytes():
                continue
            if not args.overwrite:
                conflicts.append(target)
        pending.append((source, target))

    retired = []
    for old, alias in catalog.get("skill_aliases", {}).items():
        if alias["skill"] not in selected:
            continue
        entry = destination / old / "SKILL.md"
        if not entry.exists():
            continue
        if not entry.resolve().is_relative_to(destination.resolve()) or not entry.is_file():
            parser.error("Invalid legacy entrypoint: " + str(entry))
        try:
            old_text = entry.read_text(encoding="utf-8-sig")
        except UnicodeError:
            parser.error("Legacy entrypoint is not UTF-8; manual review required: " + str(entry))
        digest = hashlib.sha256(old_text.replace("\r\n", "\n").encode("utf-8")).hexdigest()
        if digest != catalog.get("retired_entrypoint_hashes", {}).get(old):
            parser.error("Customized retired skill requires manual review; no files written: " + str(entry))
        if not args.migrate_legacy:
            parser.error("Retired entrypoint would duplicate the merged skill. Use --migrate-legacy after review: " + str(entry))
        target = project / ".claude" / "retired-skills" / old / ("SKILL." + digest[:12] + ".md")
        if (not target.resolve().is_relative_to(project)
                or target.resolve().is_relative_to(LIBRARY.resolve()) or target.exists()):
            parser.error("Invalid or existing legacy archive: " + str(target))
        for parent in target.parents:
            if parent.exists() and not parent.is_dir():
                parser.error("Legacy archive parent is a file: " + str(parent))
            if parent == project:
                break
        retired.append((entry, target))

    # Check every conflict before creating any output, preserving local edits.
    if conflicts:
        print("Existing files differ; no files written. Review before using --overwrite:", file=sys.stderr)
        for target in conflicts:
            print(target, file=sys.stderr)
        return 1
    print(f"pipeline={args.pipeline} skills={len(selected)} files_to_copy={len(pending)} retired_entrypoints={len(retired)} target={destination}")
    if args.dry_run:
        return 0
    for source, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for source, target in retired:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
    print("Installed. Canonical sources remain in skills/; extra project files were preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
