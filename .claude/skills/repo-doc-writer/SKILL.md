---
name: repo-doc-writer
description: >
  Converts core-engineering design artifacts (requirements.md, if_list.md, if_decomposition.md,
  uf.md) into structured /docs/ai/*.md files that Cursor Composer can use as implementation
  context. This is the bridge between Claude's design phase and Cursor's implementation phase.
  Trigger when the user says "docs 써줘", "Cursor용 문서 만들어줘", "repo에 문서 저장해줘",
  "/docs/ai 업데이트", "설계 문서 레포에 반영해줘", "task 문서 만들어줘", or after
  req-elicitor / if-designer / uf-designer has produced artifacts and the user wants
  to prepare the repo for Cursor to start coding. Also trigger when the user mentions
  "docs/ai" or wants to sync design artifacts into the repository.
---

# Repo-Doc-Writer

Reads design artifacts and writes structured markdown files into `/docs/ai/` so Cursor
Composer can pick them up as implementation context without needing to re-read raw design files.

> **Read `references/format.md`** before writing any file — it defines the exact structure
> each output doc must follow.
> **Use templates in `assets/`** — copy and fill rather than writing from scratch.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/format.md` | Output doc formats for each doc type |
| `assets/overview_template.md` | Template for `docs/ai/overview.md` |
| `assets/task_template.md` | Template for individual `docs/ai/tasks/<name>.md` |
| `scripts/validate_docs.sh` | Run after writing to check file structure |

---

## Input → Output Map

| Source artifact | Produces |
|---|---|
| `requirements.md` + `if_list.md` | `docs/ai/overview.md` — system summary + IF list |
| `uf.md` (one UF Block) | `docs/ai/tasks/<uf_id>.md` — Cursor task file |
| `if_decomposition.md` | `docs/ai/architecture.md` — dependency graph in mermaid |

If any source artifact is missing, note the gap and write partial docs from what is available.

---

## Execution

### Step 1 — Scan available artifacts

Look for these files in the project (check current dir and common subdirs like `docs/`, `design/`):
- `requirements.md`
- `if_list.md`
- `if_decomposition.md`
- `uf.md`

Report which ones exist before proceeding.

### Step 2 — Write `docs/ai/overview.md`

Use `assets/overview_template.md`. Populate:
- **System purpose** — 2–3 sentences from `problem_statement.md` or `requirements.md` header
- **Integration Functions** — table from `if_list.md` (IF ID, name, responsibility, I/O summary)
- **Key constraints** — from `assumptions_and_constraints.md` if present

### Step 3 — Write `docs/ai/architecture.md`

Convert `if_decomposition.md` tree into a mermaid diagram + plain-English dependency notes.
Keep it under 60 lines — Cursor reads the whole file as context.

### Step 4 — Write task files from `uf.md`

For each UF Block in `uf.md`, write one `docs/ai/tasks/<UF_ID>.md`.
Use `assets/task_template.md`. Each task file must include:
- What to implement (clear 1-sentence goal)
- Input/output contract (exact types / shapes)
- Edge cases to handle
- Verification criteria (what passing looks like)

Keep each task file under 80 lines. Cursor performs best with focused, self-contained context.

### Step 5 — Validate

Run `scripts/validate_docs.sh` to confirm all expected files exist and are non-empty.
Print the file list on completion so the user can verify.

---

## Rules

- Write docs relative to the **project root** (not the design artifact directory).
- Never duplicate information across files — cross-reference with relative links.
- Task files are Cursor's primary input — be concrete and unambiguous. Avoid design rationale
  unless it directly constrains the implementation.
- If a UF has no acceptance criteria yet, mark the section `TODO: add criteria` rather than
  fabricating them.
