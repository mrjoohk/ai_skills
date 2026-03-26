---
name: code-reviewer
description: >
  Performs structured code review against UF/IF contracts, requirements, and coding standards.
  Produces a prioritized finding report that cursor-task-formatter can turn into Cursor fix prompts.
  Trigger when the user says "코드 리뷰해줘", "리뷰 해줘", "구현 검토해줘", "코드 확인해줘",
  "review this code", "PR 리뷰", "버그 찾아줘", "개선점 찾아줘", or after Cursor has
  finished implementing UFs and the user wants to validate the result before merging.
  Also trigger when the user shares code files and asks for quality, correctness, or
  contract compliance checks. Do NOT wait for the user to say "code review" specifically
  — trigger whenever new implementation is ready and the user wants feedback.
---

# Code-Reviewer

Reviews code against three lenses: contract compliance, logic correctness, and code quality.
Outputs a structured finding report that feeds directly into `cursor-task-formatter`.

> **Read `references/review_criteria.md`** for the full checklist before reviewing.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/review_criteria.md` | Full checklist: contract, logic, quality criteria |
| `assets/review_report_template.md` | Template for the output report |

---

## Input

- **Code files** — the implementation to review (required)
- **UF specs / task docs** — `docs/ai/tasks/*.md` or `uf.md` (use as contract reference if available)
- **requirements.md** — for acceptance criteria cross-check (optional)

If no spec is provided, review against general best practices and note that contract compliance
could not be checked.

---

## Review Lenses

### 1. Contract Compliance
Check each reviewed function against its UF spec:
- Does the signature match (param names, types, return type)?
- Are all documented edge cases handled?
- Do outputs match the specified shape/type?

### 2. Logic Correctness
- Off-by-one errors, null/undefined handling, type coercion issues
- Control flow completeness (are all branches handled?)
- Error propagation (are exceptions caught at the right level?)

### 3. Code Quality
- Readability: are variable/function names clear?
- Duplication: is any logic repeated that should be extracted?
- Single responsibility: does each function do exactly one thing?
- Test coverage: are edge cases from the spec covered by tests?

---

## Output Format

Use `assets/review_report_template.md`. Structure findings as:

```
[SEVERITY] FINDING-N: <one-line summary>
File: <path>, Line: <range>
Issue: <what's wrong>
Fix: <what correct code should do>
```

**Severity levels:**
- `[CRITICAL]` — contract violation, data corruption, security issue → must fix before merge
- `[WARN]` — logic gap, missing edge case, poor error handling → should fix
- `[SUGGEST]` — quality improvement, readability, test coverage → nice to have

---

## Execution

1. Read the code files
2. If spec files exist, read them and list the contracts being checked
3. Apply all three review lenses, file by file
4. Write the report using the template
5. At the end, print a **Review Summary** line:
   `Summary: N critical, N warnings, N suggestions — [PASS/NEEDS WORK]`
6. If findings exist, note: "Run cursor-task-formatter on this report to generate Cursor fix prompts."

---

## Rules

- Be specific: cite file, line number, and exact variable/function names.
- Be constructive: every finding must include a "Fix:" that states the correct behavior.
- Don't invent requirements — if a behavior isn't specified, mark it `[SUGGEST]` not `[CRITICAL]`.
- Focus on the diff: if reviewing a PR, only comment on changed lines unless they break existing contracts.
