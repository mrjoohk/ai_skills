import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_docs.py"
spec = importlib.util.spec_from_file_location("repo_docs_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

TASK = """# UF-01-01: Parse a record

**Parent IF:** IF-01
**Status:** TODO

## Goal
Parse one record and preserve leading zeroes.

## Signature
```python
def parse_record(text: str) -> dict[str, str]:
```

## Input / Output Contract
| | Description | Type/Shape | Constraints |
|---|---|---|---|
| Input | record text | str | UTF-8 |
| Output | parsed fields | dict[str, str] | preserves identifiers |

## Edge Cases
- Empty input: raise ValueError.

## Verification
- [ ] Identifier 001 remains a string.
"""
OVERVIEW = """# Example
## Purpose
Parse records.
## Integration Functions
IF-01 parses a record.
## Key Constraints
Keep identifiers as text.
"""
ARCHITECTURE = "# Architecture\n## Dependency Graph\n```mermaid\ngraph TD\n  IF01[Parse]\n```\n"


class Validation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.docs = self.root / "handoff" / "agent-context"
        (self.docs / "tasks").mkdir(parents=True)
        (self.docs / "overview.md").write_text(OVERVIEW, encoding="utf-8")
        (self.docs / "architecture.md").write_text(ARCHITECTURE, encoding="utf-8")
        self.task = self.docs / "tasks" / "UF-01-01.md"
        self.task.write_text(TASK, encoding="utf-8")
        self.uf = self.root / "selected-design.md"
        self.uf.write_text("- UF-ID: UF-01-01\n- Goal: Parse.\nReferences UF-99-99 as an example only.\n", encoding="utf-8")

    def check(self, partial=False):
        return validator.validate(self.root, Path("handoff/agent-context"), self.uf, partial)

    def codes(self, result):
        return {x["code"] for x in result["findings"]}

    def test_custom_paths_and_implementation_todo_status_are_valid(self):
        result = self.check()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["complete"])
        self.assertEqual(result["coverage"]["expected"], ["UF-01-01"])

    def test_missing_tasks_fail_even_with_valid_overview_and_architecture(self):
        self.task.unlink()
        result = self.check()
        self.assertFalse(result["passed"])
        self.assertIn("UNCOVERED_UF", self.codes(result))

    def test_empty_task_is_not_counted_as_coverage(self):
        self.task.write_text("\n", encoding="utf-8")
        result = self.check()
        self.assertIn("EMPTY_FILE", self.codes(result))
        self.assertIn("UNCOVERED_UF", self.codes(result))

    def test_missing_io_type_is_rejected(self):
        self.task.write_text(TASK.replace("| str | UTF-8 |", "| | UTF-8 |"), encoding="utf-8")
        result = self.check()
        self.assertFalse(result["passed"])
        self.assertIn("INCOMPLETE_IO_CONTRACT", self.codes(result))

    def test_extra_and_missing_ufs_are_reported(self):
        self.uf.write_text("- UF-ID: UF-02-01\n", encoding="utf-8")
        self.assertEqual(self.codes(self.check()), {"UNCOVERED_UF", "UNKNOWN_UF"})

    def test_duplicate_tasks_are_rejected(self):
        (self.docs / "tasks" / "copy.md").write_text(TASK, encoding="utf-8")
        self.assertIn("DUPLICATE_TASK", self.codes(self.check()))

    def test_partial_draft_is_explicit_not_complete(self):
        self.task.write_text(TASK.replace("Identifier 001 remains a string.", "TODO: add criteria"), encoding="utf-8")
        self.assertFalse(self.check()["passed"])
        result = self.check(partial=True)
        self.assertTrue(result["passed"])
        self.assertFalse(result["complete"])
        self.assertEqual(result["findings"][0]["severity"], "warning")

    def test_placeholders_are_rejected(self):
        self.task.write_text(TASK.replace("Empty input: raise ValueError.", "{{EDGE_CASE}}"), encoding="utf-8")
        self.assertIn("UNFILLED_TEMPLATE", self.codes(self.check()))

    def test_language_type_parameters_are_not_template_placeholders(self):
        self.task.write_text(TASK.replace("dict[str, str]", "std::vector<T>"), encoding="utf-8")
        self.assertTrue(self.check()["passed"])

    def test_ambiguous_auto_discovery_does_not_select_a_source(self):
        (self.root / "rd").mkdir()
        (self.root / "uf.md").write_text("- UF-ID: UF-01-01\n", encoding="utf-8")
        (self.root / "rd" / "uf.md").write_text("- UF-ID: UF-02-01\n", encoding="utf-8")
        result = validator.validate(self.root, self.docs)
        self.assertIn("AMBIGUOUS_UF_SOURCE", self.codes(result))

    def test_fenced_template_uf_ids_are_not_real_declarations(self):
        text = "```markdown\n- UF-ID: UF-88-01\n```\n- UF-ID: UF-01-01\n"
        self.assertEqual(validator.uf_ids(text), {"UF-01-01"})

    def test_cli_reports_contract_result_and_failure_exit(self):
        command = [sys.executable, "-X", "utf8", str(SCRIPT), "--root", str(self.root),
                   "--docs-dir", "handoff/agent-context", "--uf", str(self.uf)]
        good = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(good.returncode, 0, good.stderr)
        result = json.loads(good.stdout.removeprefix("RESULT_JSON="))
        self.assertTrue(result["passed"])
        self.task.unlink()
        bad = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(bad.returncode, 1)
        self.assertFalse(json.loads(bad.stdout.removeprefix("RESULT_JSON="))["passed"])


if __name__ == "__main__":
    unittest.main()
