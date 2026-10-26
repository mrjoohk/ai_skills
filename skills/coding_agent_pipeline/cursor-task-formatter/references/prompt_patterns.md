# Cursor Prompt Patterns

## Anatomy of a Good Cursor Prompt

```
[Context — 1-2 lines]
Working on <project/module>. Implement <UF name> in <file path>.

[Spec — what to build]
Function signature: ...
Input: ...
Output: ...
Edge cases: ...

[Constraints — style/patterns to follow]
- Follow existing patterns in <file>
- Use <library/framework> for <concern>

[Verify by:]
- <test or observable outcome>
```

## Length Guide

| Prompt type | Target length |
|---|---|
| Single UF implementation | 100–200 words |
| Grouped UFs (2-3, same IF) | 200–300 words |
| Fix/refactor | 80–150 words |

## Do's

- Specify the exact file path (e.g., `src/processing/parser.py`)
- Use the same variable/type names from the UF spec — Cursor may generate them verbatim
- Include a single concrete verification step ("running `pytest tests/test_parser.py` should pass")
- Reference an existing function as a style example if one exists

## Don'ts

- Don't explain design decisions or why the function exists
- Don't paste entire files as context — just the relevant function signature or ~10 lines
- Don't combine unrelated UFs in one prompt
- Don't ask Cursor to "figure out" the right place to put the code — tell it

---

## Handoff Checklist

Print this after the last prompt:

```
## Handoff Checklist
- [ ] docs/ai/tasks/ files are up to date (run repo-doc-writer if needed)
- [ ] Paste prompts one at a time in order — wait for each to complete
- [ ] After each implementation, run the verify step before moving on
- [ ] When all tasks are done, run code-reviewer on the new code
```
