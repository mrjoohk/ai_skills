# Reference: req-elicitor Output Templates

## Stage Output Summary

| Stage | Output File | Key Contents |
|:---:|---|---|
| 1 | `problem_statement.md` | Background, scope, initial constraints |
| 2 | `clarification_log.md` | Q&A pairs, resolved/unresolved items |
| 3 | `assumptions_and_constraints.md` | Numeric bounds, boundary conditions, assumptions |
| 4 | `requirements.md` | REQ Blocks (functional + non-functional) |

---

## problem_statement.md Template

```markdown
# Problem Statement

## Problem Background
(1–3 sentences: what is broken or missing, and why it matters)

## Scope of Impact
- System: (which system / service / component)
- Team / Stakeholders: (who is affected)
- Schedule Impact: (deadline or urgency level)

## Initial Constraints
(Known constraints from the problem description — add more in Stage 3)
- ...
```

---

## clarification_log.md Template

```markdown
# Clarification Log

## Q&A

| # | Question | Answer | Source | Date |
|---|----------|--------|--------|------|
| 1 | ... | ... | User | YYYY-MM-DD |

## Resolved Ambiguities
- ...

## Unresolved Items [UNRESOLVED]
- ...
```

---

## assumptions_and_constraints.md Template

```markdown
# Assumptions and Constraints

## Constraints
- Performance: (e.g., processing time ≤ X ms at 95th percentile)
- Memory: (e.g., peak RAM ≤ Y GB)
- Accuracy: (e.g., error rate ≤ Z%)
- Throughput: (e.g., N requests/sec)
- Regulations / Compliance: ...

## Boundary Conditions
- Input minimum: ...
- Input maximum: ...
- Extreme scenarios: (empty input, null, max load, malformed data)

## Assumptions — to be validated

| # | Assumption | Validation Method | Status |
|---|-----------|-------------------|--------|
| A1 | ... | ... | Unvalidated |
| A2 | ... | ... | Unvalidated |
```

---

## REQ Block Template (requirements.md)

```markdown
- ID: REQ-###
- Title: (one-line summary)
- Context: (why this requirement exists — 1–2 sentences)
- Inputs:
    <name>: <type>, <unit>, <range>
- Outputs:
    <name>: <type>, <unit>, <range>
- Constraints:
    (performance / memory / accuracy / determinism constraints with numeric bounds)
- Acceptance Criteria:
    Given <precondition>,
    When  <action or event>,
    Then  <measurable result with numeric threshold>
    (Add multiple Given/When/Then if needed)
- Tests:
    Unit:        tests/unit/test_<name>.py
    Integration: tests/integration/test_<name>_integration.py
    E2E:         tests/e2e/test_<name>_e2e.py
- Evidence:
    reports/<name>/
    evidence_pack/<name>/
```

### Acceptance Criteria — good vs bad

| Bad (untestable) | Good (testable) |
|---|---|
| "The system responds quickly" | "Then latency ≤ 200 ms at 95th percentile under 100 concurrent users" |
| "The model is accurate" | "Then mAP ≥ 0.85 on the validation set of 5,000 images" |
| "Memory usage is reasonable" | "Then peak RAM ≤ 4 GB during a 60-minute run" |
| "Output is correct" | "Then output JSON matches schema with 0 validation errors" |

---

## Requirements Structure

```markdown
# Requirements

## Functional Requirements

### REQ-001 — <title>
...

### REQ-002 — <title>
...

## Non-Functional Requirements

### REQ-010 — <title> (Performance)
...

### REQ-011 — <title> (Reliability)
...
```

---

## Clarifying Questions — Useful Prompts

When generating Stage 2 questions, cover these categories:

**Numeric thresholds** (almost always missing from initial descriptions)
- "What is the acceptable latency / throughput / accuracy threshold?"
- "How large is the dataset / input?"

**Boundary conditions**
- "What should happen when input is empty / null / malformed?"
- "What is the maximum expected load?"

**Environment / Platform**
- "What hardware is available? (CPU-only, GPU, memory limit)"
- "What OS / runtime / language is required?"

**Scope**
- "Is X in scope for this phase, or deferred?"
- "Are there existing systems this must integrate with?"

**Deadline / Priority**
- "Is there a hard deadline? Which requirements are P0 vs P1?"
