# CLAUDE.md
## Execution Instructions for Claude Code

You are tasked with implementing a Defense-domain sLLM Agent System according to requirements.md.

You MUST follow the exact execution order below.

---

# PART 1 — CODING BEHAVIOR PRINCIPLES

> These principles apply to **all implementation tasks** regardless of skill or domain.
> Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

# PART 2 — WORKFLOW RULES

### Rule 1 — Review Before Creating Output
> Before creating any final deliverable (document, file), first share the analysis/investigation summary with the user and wait for approval.

**Flow**: Start task → Perform analysis → Present findings to user → Await approval → Create output

### Rule 2 — Preserve Analysis as MD Files
> Save all analysis/investigation content created during tasks as MD files for reuse in future tasks.
> **Exception**: Review documents that contain diagrams (block diagrams, flowcharts, system structure, etc.) must be saved as `.html` instead, so the diagrams render properly (see Rule 5 and Rule 6).

**Filename convention**: `YYMMDD_HHMM_[description].md` (or `.html` for diagram-bearing review docs)
Example: `260318_1430_uf_status_analysis.md`, `260318_1430_uf_architecture.html`

### Rule 3 — State Judgment Rationale
> Every decision, choice, or recommendation must include the rationale (판단 근거).

**Apply**: Include a "판단 근거:" section in all analysis MD files and user reports.

### Rule 4 — File Creation Log
> All files created in the working folder must be logged in `0.FilesUpdate.xlsx`.
> **If `0.FilesUpdate.xlsx` does not exist, create it first, then record the entry.**

> **[Encoding Rule]** Always write xlsx files using the `openpyxl` library directly.
> Never generate xlsx via intermediate paths (CSV conversion, subprocess, print redirection, etc.).
> `openpyxl` natively handles UTF-8 Unicode, preventing silent `?` substitution of non-ASCII characters.

| Column | Content |
|--------|---------|
| 일시 | YYYY-MM-DD HH:MM |
| 파일명 | Created filename |
| 요청 요약 | Core content of user's request |

### Rule 5 — Output Format Standard
> Deliverables containing tables or figures must be created as `.docx`.
> **Review documents containing diagrams must be created as `.html`** (see Rule 6) so that block diagrams, flowcharts, and system structures render correctly. Use a self-contained single HTML file (embed CSS/JS; Mermaid or inline SVG recommended for diagrams).

| Condition | Format |
|-----------|--------|
| Review/analysis doc containing a diagram | `.html` |
| Contains table or figure (non-diagram deliverable) | `.docx` |
| Text-focused analysis/memo | `.md` |
| Data/numeric-focused | `.xlsx` |
| Slide presentation | `.pptx` |

### Rule 6 — Directory for Review Documents
> All files (html, docx, ppt, xlsx, md) created during analysis/investigation phases must be saved in the `review_docs` directory.
> **If `review_docs` does not exist, create it first.**
> **Diagram representation**: When a review document includes a diagram (block diagram, flowchart, system configuration, R&D concept, etc.), author it as `.html` rather than `.md` so the diagram renders properly. Keep it as a single self-contained HTML file. Use `.md` only for text-focused review docs without diagrams.

**Apply to**: Any file produced during analysis, review, or investigation steps (before user approval).

### Rule 7 — Directory for Output Documents
> All files (docx, ppt, xlsx, md) created as final responses, results, or action outputs must be saved in the `output_docs` directory.
> **If `output_docs` does not exist, create it first.**

**Apply to**: Any file produced as a deliverable, response, or remediation result (after user approval).

### Rule 8 — Prompt & Response Log
> Every user request prompt and the agent's corresponding response/result must be recorded in order in `1.PromptsUpdate.xlsx`.
> **If `1.PromptsUpdate.xlsx` does not exist, create it first.**

> **[Encoding Rule]** Same as Rule 4: always use `openpyxl` directly to prevent `?` corruption of non-ASCII text.

| Column | Content |
|--------|---------|
| 일시 | YYYY-MM-DD HH:MM |
| 요청 프롬프트 | Full text of the user's request |
| 응답/결과/대처 | Summary of the agent's response or action taken |

### Rule 9 — Directory for Design Artifacts
> All design documents produced by design/engineering skills must be saved in the `rd` directory.
> **If `rd` does not exist, create it first.**

**Applies to** the following artifacts (and any others generated by design/engineering skills):
- `requirements.md`
- `problem_statement.md`
- `assumptions_and_constraints.md`
- `clarification_log.md`
- `if_list.md`
- `if_decomposition.md`
- `uf.md`
- `uf_split/` (directory and its contents)
- `uf_if_coverage_review.md`
- `evaluation_plan.md` (Stage 8 canonical output — replaces the legacy name `verification_plan.md`)
- `domain_metrics.md` (domain auditor → eval-planner handoff)
- theory-decomposer artifacts: `source_survey.md`, `theory_statement.md`, `theory_tree.md`, `eq.md`, `eq_coverage_review.md`

> **Note**: These files must NOT be placed in `review_docs/` or `output_docs/`. The `rd/` directory is the single canonical location for all design artifacts.

### Rule 10 — Directory for Implementation & Audit Reports
> Machine-generated implementation, integration, audit, and evaluation reports produced by pipeline skills are saved under `reports/`:
> `reports/impl/` (uf-implementor, if-integrator), `reports/eval/` (eval-runner), `reports/physics/` (sim-physics-auditor), `reports/rag/`, `reports/gpu/`.
> **If `reports/` does not exist, create it first.**

**Distinction**: `reports/` holds skill-generated evidence artifacts consumed by downstream skills; `review_docs/` (Rule 6) holds human-facing analysis documents awaiting user review. Do not mix the two.

### Workflow Summary
```
Receive request
  → [Rule 8] Log user prompt to 1.PromptsUpdate.xlsx
  → Perform analysis/investigation
  → [Rule 3] Summarize with judgment rationale
  → [Rule 6] Save analysis files to review_docs/ (use .html when the doc contains a diagram)
  → [Rule 9] Save design artifacts (requirements, if_list, uf, etc.) to rd/
  → [Rule 1] Present to user for review → Await approval
  → Create output
  → [Rule 7] Save output files to output_docs/
  → [Rule 2] Save analysis as MD (yymmdd_hhmm_*.md), or .html for diagram-bearing review docs
  → [Rule 4] Update 0.FilesUpdate.xlsx
  → [Rule 8] Log agent response to 1.PromptsUpdate.xlsx
```
