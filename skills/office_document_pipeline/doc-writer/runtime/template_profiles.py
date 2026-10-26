"""Template presets shared by generation, insertion and validation."""
import json
from pathlib import Path
import re

DEFAULT_ID = "technical-report"


def profile_path(profile=None, root=None):
    if profile and (str(profile).endswith(".json") or Path(profile).is_absolute()):
        path = Path(profile)
        return path if path.is_absolute() else Path(root or Path.cwd()) / path
    name = profile or DEFAULT_ID
    if not re.fullmatch(r"[a-z0-9-]+", str(name)):
        raise ValueError("Invalid template profile: " + str(name))
    here = Path(__file__).resolve().parent
    candidates = [
        Path(root or here.parents[1]) / "document_templates" / name / "profile.json",
        here.parents[1] / "document_templates" / name / "profile.json",
        here.parent / "templates" / name / "profile.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("Template profile not installed: " + str(name))


def load_profile(profile=None, root=None):
    path = profile_path(profile, root).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not re.fullmatch(r"[a-z0-9-]+", str(data.get("id", ""))):
        raise ValueError("Template profile needs a safe id")
    styles = data.get("styles")
    required = {"heading", "para", "item", "need", "caption", "th", "td", "anchor", "figure"}
    if not isinstance(styles, dict) or not required <= styles.keys():
        raise ValueError("Template profile is missing style roles")
    if not all(isinstance(value, str) and value for value in styles.values()):
        raise ValueError("Template styles must be nonempty strings")
    heading_pattern(styles)
    data["_path"] = str(path)
    return data


def resolve_styles(profile=None, overrides=None, root=None):
    styles = dict(load_profile(profile, root)["styles"])
    styles.update(overrides or {})
    if not all(isinstance(value, str) and value for value in styles.values()):
        raise ValueError("Template styles must be nonempty strings")
    heading_pattern(styles)
    return styles


def heading_pattern(styles):
    template = styles["heading"]
    if template.count("{level}") != 1:
        raise ValueError("Heading style must contain one {level} placeholder")
    # Other replacement fields are not supported by the heading-level contract.
    template.format(level=1)
    return re.compile("^" + re.escape(template).replace(re.escape("{level}"), "([1-7])") + "$")


def heading_level(style, styles):
    match = heading_pattern(styles).fullmatch(style or "")
    return int(match.group(1)) if match else None
