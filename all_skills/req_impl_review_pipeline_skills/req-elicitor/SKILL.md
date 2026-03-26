---
name: req-elicitor
description: >
  Executes core-engineering Stages 1–4: transforms a natural-language problem description
  into four structured design artifacts — problem_statement.md, clarification_log.md,
  assumptions_and_constraints.md, and requirements.md (REQ Blocks with numeric
  Given/When/Then acceptance criteria). This is the mandatory entry point for every
  new core-engineering project. Trigger whenever the user describes a problem they want
  to design or engineer, says things like "문제 정의해줘", "요구사항 뽑아줘", "REQ 써줘",
  "requirements 만들어줘", "프로젝트 시작", "설계 시작", or provides a problem background
  and wants to proceed with structured engineering. Also trigger before running
  if-designer or uf-implementor when no requirements.md exists yet.
---

# Req-Elicitor — Core Engineering Stages 1–4

This skill converts a problem description into four machine-readable design artifacts
that downstream skills (`if-designer`, `uf-implementor`, etc.) depend on.

> **Read `references/reference.md`** for all output templates before writing any file.
> **Copy templates from `assets/`** — fill in the blanks rather than writing from scratch.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/reference.md` | Full templates for all 4 output documents + REQ Block format |
| `references/examples.md` | Worked example of a complete requirements.md |
| `assets/problem_statement_template.md` | Copy → fill for Stage 1 output |
| `assets/clarification_log_template.md` | Copy → fill for Stage 2 output |
| `assets/assumptions_constraints_template.md` | Copy → fill for Stage 3 output |
| `assets/requirements_template.md` | Copy → fill for Stage 4 output (one block per REQ) |
| `scripts/validate_requirements.py` | Run after generating requirements.md to verify completeness |

---

## Execution Flow

### Phase A — Stage 1: Problem Definition (autonomous)

Read the user's problem description and write `problem_statement.md`.
Use the template in `assets/problem_statement_template.md`.

- Keep the background to 1–3 sentences.
- Identify the system, team/stakeholders, and timeline impact.
- List any constraints that are already explicit in the user's description.

**Output:** `problem_statement.md`

---

### Phase B — Stage 2: Clarification (interactive — ask the user)

Before writing any further artifacts, surface ambiguities.

Generate 4–8 targeted questions focused on:
- **Numeric thresholds** not yet stated ("what latency is acceptable?", "how large is the dataset?")
- **Boundary conditions** ("what happens if input is empty / malformed?")
- **Stakeholder constraints** ("is there a hard deadline?", "GPU available?")
- **Scope boundaries** ("is X in scope or out?")

Present the questions clearly and **wait for the user's answers** before continuing.
Draft `clarification_log.md` using `assets/clarification_log_template.md` once answers are received.
Mark unanswered items as `[UNRESOLVED]`.

**Output:** `clarification_log.md`

---

### Phase C — Stage 3: Problem Elaboration (autonomous after Phase B)

Synthesize the clarification answers into `assumptions_and_constraints.md`.
Use `assets/assumptions_constraints_template.md`.

- Constraints: performance, memory, accuracy, regulations — each with a numeric bound.
- Boundary Conditions: min/max input ranges, extreme cases.
- Assumptions: anything assumed but not confirmed → mark as `Unvalidated`.

**Output:** `assumptions_and_constraints.md`

---

### Phase D — Stage 4: Requirements Elicitation (autonomous after Phase C)

Write `requirements.md` containing one REQ Block per distinct functional or non-functional requirement.

**Critical rules for REQ blocks:**
- Every Acceptance Criterion must be **Given / When / Then** format with a **numeric threshold**.
  - Bad: "Then the response is fast"
  - Good: "Then response time ≤ 200 ms at the 95th percentile under 100 concurrent users"
- I/O contracts must specify **type, unit, and range**.
- Tests field must name concrete test types (unit / integration / E2E) with placeholder paths.
- Start numbering at REQ-001 and increment sequentially.
- Separate functional REQs from non-functional REQs with a section heading.

Use the template in `assets/requirements_template.md` for each block.

**Output:** `requirements.md`

---

### Phase E — Validation

After writing `requirements.md`, run the validation script:

```bash
python <skill_dir>/scripts/validate_requirements.py requirements.md
```

Fix any failures before handing off to the next skill.

---

## Downstream Handoff

Once all four files exist and validation passes, tell the user:

```
✅ Stages 1–4 complete. Output files:
  - problem_statement.md
  - clarification_log.md
  - assumptions_and_constraints.md
  - requirements.md (REQ-001 ~ REQ-N)

Next step → run /if-designer with requirements.md as input (Stage 5–6).
```

---

## Quality Checklist

Before finishing, verify:
- [ ] Every REQ has a numeric threshold in its acceptance criteria
- [ ] All I/O types are named with type + unit + range
- [ ] All assumptions are listed as `Unvalidated`
- [ ] No REQ is ambiguous about what "done" looks like
- [ ] REQ IDs are sequential and unique
