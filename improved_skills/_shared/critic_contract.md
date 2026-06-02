# Critic Agent Common Contract (v1.0)

> **Status:** Normative. All critic skills in `improved_skills/` must adhere to every rule in this document.
> **Inheritance:** Each critic skill's `SKILL.md` frontmatter declares `critic_contract.inherits: ../_shared/critic_contract.md`.
> **Scope:** Applies to `req-critic`, `if-critic`, `uf-chain-validator` (critique mode), `eval-plan-critic`, `eval-result-critic`, `code-reviewer` (any `review_layer`).

---

## 1. Purpose

Critic agents exist to catch **semantic defects** in producer output that structural validators (`validate_*.py`) cannot detect. They are not a second copy of the producer's review pass — they are an independent adversarial evaluation.

A critic must answer only one question:

> *Given this artifact, should the pipeline proceed, loop back, or halt?*

It does not rewrite the artifact. It does not negotiate with the producer. It renders a verdict with evidence.

---

## 2. Core Principles

### 2.1 Independence of Execution Context

- A critic **must** be spawned as a fresh sub-agent by the orchestrator.
- A critic **must not** share conversation context, working memory, or tool history with the producer.
- A critic **must not** be invoked inline by the producer (no "now review yourself" calls).
- If the same Claude session runs both producer and critic roles in sequence without a sub-agent boundary, the verdict is invalid and must be re-run.

**Why:** Shared context causes the critic to rationalize producer choices and mirror producer assumptions. Independence is the entire reason critics exist.

### 2.2 Input Whitelist

Every critic declares in its SKILL.md frontmatter:

```yaml
critic_contract:
  inputs:
    required: [<artifact paths>]       # final outputs + upstream contracts only
    optional: [<supplementary>]
    forbidden: [<producer reasoning trace>]
```

**Rules:**

- **Required** = the final artifact under review + upstream contracts needed to interpret it.
- **Forbidden** = any file that captures the producer's reasoning path. Concrete examples:
  - `clarification_log.md` (producer's Q&A with user — forbidden for `req-critic`)
  - `if_decomposition.md` (producer's decomposition rationale — forbidden for `uf-chain-validator` critique mode)
  - Producer sub-agent transcripts, draft files, `.pipeline/handoffs/*.json` of the reviewed producer
- **Optional** = domain references, public benchmarks, the skill's own `references/` bundle.

If a forbidden file is somehow present in the critic's scope, the critic must refuse to read it and emit `BLOCK` with reason `forbidden_input_exposure`.

### 2.3 Alternative Enforcement (Design Critics Only)

Applies to: `req-critic`, `if-critic`, `uf-chain-validator` (critique mode), `eval-plan-critic`.
Does **not** apply to: `code-reviewer`, `eval-result-critic` (these review facts, not design choices).

Design critics must:

1. Identify the **top-3 most impactful design decisions** in the artifact.
2. For each, propose **at least 2 alternatives**.
3. State the trade-off axis of the current choice versus alternatives (e.g., "latency vs memory", "generality vs specialization", "coupling vs cohesion").
4. Declare whether the current choice is defensible **given** the stated constraints, or whether an alternative is strictly better.

The producer is **not required** to adopt alternatives — the critic's job is to ensure the choice was made with eyes open, not to re-design.

### 2.4 Verdict Taxonomy

Every critic output carries exactly one verdict from this closed set:

| Verdict | Meaning | Orchestrator action |
|---|---|---|
| `APPROVE` | All findings are SUGGEST or none. Pipeline advances. | Move to next stage. |
| `REQUEST_CHANGES` | ≥ 1 WARN or the severity rules below escalate. Producer revises. | Loop back to producer with findings. Re-critic on resubmit. |
| `BLOCK` | ≥ 1 CRITICAL, or independence/input violation, or user-intervention-required defect. | Halt pipeline. Escalate to user. |

No other verdicts. No "conditional approve". No "pass with notes".

### 2.5 No Self-Justification

A critic must not accept the producer's stated rationale as evidence. Specifically:

- "The spec says Primary = SI-SDR because it's standard" is **not** a valid dismissal of a finding. The critic must cross-check against `references/` or external benchmarks.
- "Edge case list is exhaustive because the producer said so" is **not** acceptable. The critic must generate its own edge case list for that domain and compare.
- Quoting producer prose in a finding's justification is forbidden. Findings cite **artifact fields** + **external sources** only.

---

## 3. Finding Format (Mandatory)

Every finding in a critique report uses this exact structure:

```
[SEVERITY] CRIT-<STAGE>-<N>: <one-line summary>
  What:      <concrete observation, anchored to artifact field or line>
  Why:       <why this is a problem — cite external source or rule, not producer rationale>
  Fix:       <what a correct artifact looks like — no prescriptive design>
  Affected:  <artifact path + field/section/line>
  Alternative: <if design critic: >= 1 alternative, with trade-off axis>
```

**Severity:**

| Level | When to use | Verdict impact |
|---|---|---|
| `CRITICAL` | Invariant violation, testability impossibility, known-unsafe choice, statistical rigor absent | Triggers `BLOCK` |
| `WARN` | Design gap, missing coverage, unrealistic threshold, bias risk | Triggers `REQUEST_CHANGES` |
| `SUGGEST` | Clarification, readability, non-blocking polish | Does not trigger verdict change |

**ID scheme:** `CRIT-<stage>-<N>` where `<stage>` matches the critic's `pipeline.stage` value (e.g., `CRIT-1-4-01`, `CRIT-8-run-07`). IDs are sequential within a single report.

---

## 4. Output Contract

### 4.1 File Output

- Path: `reports/critique/<stage>_<timestamp>_critique.md`
- Encoding: UTF-8
- Structure:

```markdown
# <Stage> Critique Report

**Reviewed artifact(s):** <paths>
**Critic skill:** <skill name>
**Date:** <YYYY-MM-DD HH:MM UTC>
**Verdict:** <APPROVE | REQUEST_CHANGES | BLOCK>

## Summary
- CRITICAL: N
- WARN: N
- SUGGEST: N

## Findings
[... findings in the format above ...]

## Alternatives Analysis (design critics only)
[... top-3 decisions with ≥ 2 alternatives each ...]

## Verdict Justification
<1 paragraph tying the verdict to specific findings>

## Handoff
[... JSON block (§4.2) ...]
```

### 4.2 Handoff JSON

Emitted at end of critic execution in a fenced ```json block:

```json
{
  "skill": "<critic-skill-name>",
  "version": "1.0",
  "role": "verifier-critic",
  "status": "COMPLETE",
  "verdict": "APPROVE | REQUEST_CHANGES | BLOCK",
  "reviewed_artifacts": [
    {"path": "<path>", "sha256": "<hash>"}
  ],
  "outputs": [
    {"path": "reports/critique/...", "kind": "report"}
  ],
  "findings_summary": {
    "critical": 0, "warn": 0, "suggest": 0
  },
  "findings": [
    {
      "id": "CRIT-1-4-01",
      "severity": "WARN",
      "summary": "...",
      "affected": "requirements.md::REQ-004"
    }
  ],
  "alternatives_analyzed": <count, null for fact-based critics>,
  "iteration": 1,
  "next_action": "producer_revise | orchestrator_advance | user_escalate"
}
```

Orchestrator parses only this JSON; the markdown is for human readers.

---

## 5. Iteration Protocol

### 5.1 Normal Loop

```
Producer emits COMPLETE → Critic spawned → Verdict
  APPROVE           → orchestrator advances to next stage
  REQUEST_CHANGES   → orchestrator re-spawns Producer with findings attached
                      → Producer emits COMPLETE v2
                      → Critic re-spawned (fresh context, iteration=2)
                      → Verdict again
  BLOCK             → orchestrator halts, user escalation
```

### 5.2 Iteration Limit

- Maximum **2 critic rounds** per artifact.
- On iteration 3 attempt: auto-escalate to user with the pair (v1 critique, v2 critique).
- Rationale: if two independent critic runs cannot agree on APPROVE, the disagreement is substantive, not mechanical — human judgement required.

### 5.3 BLOCK Handling

- BLOCK verdicts do not iterate. Pipeline halts immediately.
- Orchestrator must surface the BLOCK reason, the specific CRITICAL findings, and — if the producer can address them — offer the user the option to explicitly override (with warning) or restart the stage.

---

## 6. Anti-Patterns (All Forbidden)

| Anti-pattern | Why it breaks the contract |
|---|---|
| **Producer-in-critic's-clothing** — critic writes revised artifact | Critic must not perform producer's role; rewrites are producer's job. Critic output lives in `reports/critique/` only. |
| **Critic of critic** — reviewing a critique report | Recursive review adds noise without signal; disagreements belong in user escalation. |
| **Rubber-stamp APPROVE** — verdict with no substantive findings attempted | Critic must list what it checked even on APPROVE (show "4 lenses applied, 0 findings"). |
| **Nitpick floor** — only SUGGEST findings | If a critic consistently finds only SUGGEST across multiple runs, its criteria file is too weak — treat as a critic-skill bug. |
| **Citing producer prose** — "REQ-004 looks reasonable because the comment says so" | §2.5 violation. Cite artifact fields + external sources only. |
| **Shared-context re-run** — producer and critic in same session | §2.1 violation. Verdict is invalid. |
| **Partial forbidden-input exposure** — reading a couple of lines from `clarification_log.md` | §2.2 violation. Immediate BLOCK with `forbidden_input_exposure`. |

---

## 7. Tooling Contract

Every critic skill ships with:

1. `SKILL.md` — declares `critic_contract.inherits` and stage-specific inputs/forbidden lists.
2. `references/<name>_criteria.md` — the stage-specific checklist (what lenses, what severity assignments).
3. `assets/<name>_critique_template.md` — a fill-in template matching §4.1.
4. (Optional) `scripts/validate_critique.py` — self-check that the emitted report has all mandatory sections and a valid JSON handoff.

---

## 8. Integration with `agents.md`

Critic entries in `agents.md` use:

```yaml
- skill: <critic>
  role: verifier
  critic_of: <producer-skill>
  hook_after: "<producer>.status == COMPLETE"
  blocks_downstream: true | false
  iteration_limit: 2
  extras:
    inherits_contract: _shared/critic_contract.md
```

Orchestrator enforces:

- `blocks_downstream: true` + `BLOCK` or `REQUEST_CHANGES` → downstream producers remain blocked.
- `blocks_downstream: false` (e.g., `eval-plan-critic` on optional path) → critic output is informational; downstream can proceed with a warning.
- `iteration_limit` exceeded → user escalation.

---

## 9. Versioning

This contract is versioned (currently **v1.0**). Critic skills declare compatibility:

```yaml
critic_contract:
  inherits: ../_shared/critic_contract.md
  contract_version: "1.0"
```

Breaking changes bump the major version. Each critic skill must re-verify compatibility on bump.

---

## 10. Summary Invariants

If any of the following fail, the critique is invalid and must be discarded:

1. Critic ran in a separate sub-agent from producer. [§2.1]
2. No forbidden input was read. [§2.2]
3. (Design critics) At least 2 alternatives analyzed for top-3 decisions. [§2.3]
4. Verdict is exactly one of `APPROVE | REQUEST_CHANGES | BLOCK`. [§2.4]
5. Every finding has What / Why / Fix / Affected (+ Alternative for design critics). [§3]
6. Handoff JSON present and schema-valid. [§4.2]
7. No recursive critic calls. [§6]
