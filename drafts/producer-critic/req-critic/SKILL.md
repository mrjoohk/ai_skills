---
name: req-critic
description: >
  Independent critic agent for requirements.md produced by req-elicitor. Executes
  core-engineering Stage 1-4-review. Reviews REQ Blocks for semantic quality that
  validate_requirements.py cannot catch: acceptance criteria testability, threshold
  realism, cross-REQ conflicts, missing non-functional requirements, and I/O contract
  precision. Must run in an independent sub-agent context (never inline with req-elicitor).
  Trigger after req-elicitor produces requirements.md, or when the user says
  "REQ 리뷰해줘", "요구사항 검토해줘", "requirements 비판해줘", "REQ 감수",
  "REQ 감리", "요구사항 품질 점검", "critique my requirements". Also trigger
  automatically in the pipeline orchestrator when architect/req-elicitor completes.
allowed-tools: Read, Write

pipeline:
  role: verifier
  stage: "1-4-review"
  critic_of: req-elicitor

  inputs:
    required:
      - path: requirements.md
        producer: req-elicitor
      - path: problem_statement.md
        producer: req-elicitor
      - path: assumptions_and_constraints.md
        producer: req-elicitor
    optional:
      - path: domain_reference.md
      - path: public_benchmarks.md
    forbidden:
      - path: clarification_log.md
        reason: "Producer Q&A trace — reading it causes the critic to inherit producer's reasoning path (§2.2 of critic_contract)."
      - path: .pipeline/handoffs/*req-elicitor*.json
        reason: "Producer's own handoff log — produces self-justification loop."

  outputs:
    files:
      - path: "reports/critique/requirements_<timestamp>_critique.md"
        kind: report
    status_enum: [COMPLETE, BLOCKED]

  human_in_loop:
    required: false

  fanout:
    strategy: none

  validator:
    script: "<skill_dir>/scripts/validate_critique.py"
    json_output: true

  downstream:
    - next: architect/if-designer
      when: "verdict == APPROVE"
    - next: architect/req-elicitor
      when: "verdict == REQUEST_CHANGES && iteration < 2"
    - next: user_escalation
      when: "verdict == BLOCK || iteration >= 2"

critic_contract:
  inherits: ../_shared/critic_contract.md
  contract_version: "1.0"
  independence: spawn_in_fresh_subagent
  require_alternatives: true
  require_statistical_rigor: false
  verdict_enum: [APPROVE, REQUEST_CHANGES, BLOCK]
  iteration_limit: 2
---

# Req-Critic — Core Engineering Stage 1–4 Independent Review

This skill reviews `requirements.md` produced by `req-elicitor` for semantic defects that
structural validators cannot detect. It is the first critic in the pipeline and one of the
two P0 critics (the other being `eval-result-critic`) because errors at the REQ stage
propagate to IF, UF, code, and evaluation — the most expensive defect class to fix.

> **Read `../_shared/critic_contract.md` first.** This skill inherits all obligations
> from the common critic contract. If any clause conflicts, the common contract wins.
>
> **Read `references/critic_criteria.md`** for the full lens checklists and severity
> assignment tables.
>
> **Use `assets/req_critique_template.md`** as the output skeleton.

---

## Bundled Resources

| File | When to use |
|---|---|
| `../_shared/critic_contract.md` | Mandatory common contract (independence, input whitelist, verdict, iteration) |
| `references/critic_criteria.md` | REQ-specific lenses: testability, realism, conflict, NFR, I/O precision |
| `assets/req_critique_template.md` | Fill-in template for the critique report |
| `scripts/validate_critique.py` | Self-check: confirms the emitted report has all mandatory sections + valid handoff JSON |

---

## Inputs (strict)

| Status | Path | Purpose |
|---|---|---|
| required | `requirements.md` | Primary artifact under review |
| required | `problem_statement.md` | Upstream context — what problem the REQs must solve |
| required | `assumptions_and_constraints.md` | Upstream constraints — what thresholds are bounded by |
| optional | domain-specific reference docs, public benchmarks | Cross-check material |
| **forbidden** | `clarification_log.md` | Producer's reasoning trace. Do not read. |
| **forbidden** | any `.pipeline/handoffs/*req-elicitor*.json` | Producer's own claim of correctness. Do not read. |

If a forbidden file is present in the working directory, **do not open it**. Note its presence in the report's "Integrity Check" section and continue. If the orchestrator forces it into context, emit `BLOCK` with reason `forbidden_input_exposure`.

---

## Review Lenses

The critic applies **five lenses**, in this order. Each lens has a corresponding checklist
in `references/critic_criteria.md`.

### Lens 1 — Testability

Can a test engineer actually write the acceptance test from the REQ as written?

- The `Given` situation must be reproducible (data available, environment specifiable).
- The `When` action must be a concrete operation, not a state.
- The `Then` result must be measurable with a defined instrument (metric, tool, unit).
- A numeric threshold exists and the measurement procedure can produce that number.

**Fail examples:**
- "Then the system is secure" — no measurement procedure.
- "Given the user clicks fast" — no reproducible condition.
- "Then latency is low" — no threshold.

### Lens 2 — Realism (Baseline vs Target vs Stretch)

Is the Target neither a rubber-stamp nor a fantasy?

- Compare each numeric threshold to a **domain baseline** (public benchmarks, prior art, widely-known defaults).
- Flag `Target ≈ Baseline` as **WARN: no challenge** — the REQ imposes no design pressure.
- Flag `Target > known SoA` without justification as **WARN: aspirational**.
- Flag `Target` without source citation as **SUGGEST: unsourced threshold**.

Consult `references/critic_criteria.md` §Lens-2 for per-domain baseline tables (ML, audio, NLP, CV, distributed systems, embedded).

### Lens 3 — Cross-REQ Conflict

Do any two REQs impose incompatible constraints on the same artifact or flow?

Check pairwise for:
- Latency vs quality conflicts (e.g., REQ-003 "response ≤ 50 ms" ∧ REQ-007 "PESQ ≥ 3.5 on 16 kHz") — is both achievable simultaneously?
- Memory vs throughput conflicts.
- Availability vs consistency conflicts (CAP-class tradeoffs).
- Ordering assumptions (REQ-A depends on REQ-B output but REQ-B not specified to produce it).

Output: matrix of REQ-i × REQ-j with conflict type annotations. Minor conflicts = SUGGEST; hard incompatibilities = CRITICAL.

### Lens 4 — NFR Coverage

Non-functional requirement categories that should have at least one REQ each (absence = finding):

| Category | Minimum expected REQ |
|---|---|
| Performance | at least one latency, throughput, or resource bound |
| Reliability | failure mode, recovery, or uptime target |
| Security | authentication, authorization, or data protection |
| Observability | logging, metrics, or tracing spec |
| Maintainability | test coverage, CI gate, or documentation standard |
| Compliance | regulation, audit, or data-handling (if domain applies) |

Missing category: `WARN: NFR gap — <category>`. Multiple missing: may escalate to CRITICAL in regulated domains.

### Lens 5 — I/O Contract Precision

Every REQ with an I/O contract must specify **type + unit + range** for both input and output. Additionally:

- Coordinate system where spatial (pixel, normalized, world, map)
- Timestamp semantics where temporal (UTC offset, epoch, ISO8601)
- Encoding where textual (UTF-8, ASCII)
- Numerical precision/tolerance where floating-point

Missing any field: `WARN: imprecise I/O — <REQ-ID>`.

---

## Execution Flow

### Phase A — Integrity Check

1. Verify none of the **forbidden inputs** are in scope. If any is present, record in report's Integrity section and emit `BLOCK` with `forbidden_input_exposure`.
2. Verify all **required inputs** are readable. If not, emit `BLOCK` with `missing_required_input`.
3. Hash each required artifact (SHA-256) for the handoff JSON.

### Phase B — Lens Application

For each REQ Block:
1. Apply Lens 1 (testability) — most critical for REQs.
2. Apply Lens 2 (realism) using domain tables in `references/critic_criteria.md`.
3. Apply Lens 5 (I/O precision) — field-level mechanical check augmented with type/unit/range semantic inspection.

Then globally:
4. Apply Lens 3 (cross-REQ conflict) — pairwise matrix.
5. Apply Lens 4 (NFR coverage) — category checklist.

Emit findings using the format in `../_shared/critic_contract.md` §3.

### Phase C — Alternatives Analysis (mandatory for design critics)

Identify the **top-3 most impactful REQs** (by: (a) downstream coverage, (b) Primary metric claim, (c) hardest acceptance criterion). For each:

1. Propose **at least 2 alternative formulations** — a stricter version and a looser version, or two different measurement approaches.
2. State the trade-off axis (e.g., "stricter latency target costs more hardware budget").
3. Declare whether the current formulation is defensible given `assumptions_and_constraints.md`.

Record in the report's **Alternatives Analysis** section. This is not a recommendation to change the REQ — the producer decides — but the producer must see the alternatives before the next stage.

### Phase D — Verdict

Apply the verdict rules:

| Condition | Verdict |
|---|---|
| Any CRITICAL finding | `BLOCK` |
| Any Lens-1 (testability) failure on a functional REQ | `BLOCK` |
| Any hard cross-REQ incompatibility | `BLOCK` |
| `forbidden_input_exposure` or `missing_required_input` | `BLOCK` |
| ≥ 2 WARN findings, OR 1 WARN + NFR gap | `REQUEST_CHANGES` |
| All findings are SUGGEST or none | `APPROVE` |

### Phase E — Report Emission

1. Write `reports/critique/requirements_<timestamp>_critique.md` using `assets/req_critique_template.md`.
2. Emit handoff JSON block at the end (schema in `../_shared/critic_contract.md` §4.2).
3. Run `scripts/validate_critique.py` on the emitted report. If self-validation fails, revise the report — do not emit an invalid critique.

### Phase F — Handoff

Print to stdout:

```
[req-critic] Verdict: <APPROVE|REQUEST_CHANGES|BLOCK>
  CRITICAL: N  WARN: N  SUGGEST: N
  Report: reports/critique/requirements_<timestamp>_critique.md
  Next action: <producer_revise | orchestrator_advance | user_escalate>
```

Followed by the handoff JSON block.

---

## Verdict Rules (canonical)

```
BLOCK              if (CRITICAL ≥ 1)
                  OR (Lens-1 fail on functional REQ)
                  OR (hard REQ-pair incompatibility)
                  OR (forbidden_input_exposure)
                  OR (missing_required_input)

REQUEST_CHANGES    if (WARN ≥ 2)
                  OR (WARN = 1 AND NFR gap exists)

APPROVE            otherwise
```

The verdict is deterministic given the findings. The critic does not exercise "overall judgement" to override these rules.

---

## Rules (critic-specific, in addition to common contract)

1. **Do not propose specific REQ rewrites in the findings.** Fix fields state what a correct REQ *should specify*, not exact text. (Rewriting is producer's job — §6 of common contract.)
2. **Cite external sources for Lens-2 realism judgments.** "I think this is too strict" is not a finding. "Public benchmark X reports baseline 12.0 dB; REQ-003 target of 15.0 dB is +25% SoA without cited method" is a finding.
3. **Pairwise conflict matrix must be exhaustive** — every REQ pair checked, not just pairs that "look related".
4. **NFR gaps are counted once per category**, not per affected REQ.
5. **Alternatives analysis is not optional** even on APPROVE. An APPROVE verdict with no alternatives recorded is an invalid critique (§2.3 violation).

---

## Output Example (abbreviated)

```markdown
# Stage 1-4 Critique Report

**Reviewed artifact(s):** requirements.md, problem_statement.md, assumptions_and_constraints.md
**Critic skill:** req-critic
**Date:** 2026-04-24 14:32 UTC
**Verdict:** REQUEST_CHANGES

## Summary
- CRITICAL: 0
- WARN: 3
- SUGGEST: 2

## Integrity Check
- Forbidden inputs detected: none
- Required inputs present: ✓
- Artifact hashes recorded in handoff JSON

## Findings

### [WARN] CRIT-1-4-01: REQ-003 threshold unsourced
  What:      "Then end-to-end latency ≤ 40 ms" (requirements.md::REQ-003)
  Why:       No citation; public baseline for this task class (Kaldi ASR) is ~80–120 ms.
             Target is 50% of baseline with no stated method for achieving it.
  Fix:       REQ must cite baseline source and justify the reduction method, OR relax threshold.
  Affected:  requirements.md::REQ-003, acceptance criterion
  Alternative:
    - Alt-1: Relax to 80 ms (baseline); trade off: less competitive differentiation.
    - Alt-2: Keep 40 ms but scope to text-only path (strip audio); trade off: narrower feature.

### [WARN] CRIT-1-4-02: No observability NFR
  What:      No REQ mentions logging, metrics, or tracing.
  Why:       Pipeline has external dependencies (§2 of problem_statement.md) whose failures
             cannot be diagnosed without observability signals.
  Fix:       Add NFR REQ specifying log format, metric emission points, trace correlation.
  Affected:  requirements.md (global — NFR category gap)

[... additional findings ...]

## Alternatives Analysis

### Decision 1 — Primary metric choice (REQ-001: SI-SDR)
- Current: SI-SDR ≥ 12.0 dB
- Alt-A: PESQ ≥ 2.8 MOS (perceptual quality, not separation fidelity)
- Alt-B: STOI ≥ 0.88 (intelligibility-focused)
- Trade-off axis: separation fidelity vs perceptual quality vs intelligibility
- Defensibility: SI-SDR is defensible for the separation task per problem_statement.md §1,
  but the REQ should explicitly declare why SI-SDR over PESQ.

[... 2 more decisions ...]

## Verdict Justification
3 WARN findings (1 unsourced threshold + 1 NFR gap + 1 I/O imprecision) trigger
REQUEST_CHANGES per verdict rules. No CRITICAL present.

## Handoff

```json
{"skill": "req-critic", "version": "1.0", "role": "verifier-critic", "status": "COMPLETE", "verdict": "REQUEST_CHANGES", ...}
```
```

---

## Known Limits

- `req-critic` cannot verify that a REQ's domain baseline citation is *accurate* unless the orchestrator supplies the cited source. If citations are absent, the critic can only flag "unsourced" — it cannot verify correctness.
- Cross-REQ conflict detection is heuristic; subtle conflicts through 3+ hops may be missed. This is why `if-critic` re-checks coverage at IF-level.
- NFR category list is a minimum floor; domain-specific NFRs (e.g., real-time deadline determinism for embedded) are not auto-detected. See `references/critic_criteria.md` §Lens-4 for domain extensions.
