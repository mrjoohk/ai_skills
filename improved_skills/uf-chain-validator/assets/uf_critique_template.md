# UF Design Critique Report (Stage 7-review)

**Reviewed artifact(s):** uf.md, if_list.md{{, requirements.md if used}}
**Scope:** {{all UFs | parent_if=IF-XX}}
**Critic skill:** uf-chain-validator (mode: critique, v1.0)
**Date:** {{YYYY-MM-DD HH:MM UTC}}
**Iteration:** {{1 | 2}}
**Verdict:** {{APPROVE | REQUEST_CHANGES | BLOCK}}

---

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | {{N}} |
| WARN | {{N}} |
| SUGGEST | {{N}} |

UFs in scope: {{count}} / Total UFs: {{count}}

---

## Integrity Check

- [ ] Forbidden inputs detected: {{none | list (triggers BLOCK)}}
  - `if_decomposition.md`: {{not opened}}
  - `.pipeline/handoffs/*uf-designer*.json`: {{not opened}}
- [ ] Required inputs present: {{✓ | ✗}}
- [ ] Parent-IF contracts cross-checked from `if_list.md`: {{✓}}
- [ ] Artifact SHA-256 hashes recorded in handoff JSON: {{✓}}

---

## Findings

> Sort by severity (CRITICAL first), then by UF-ID. Use the format from
> `../_shared/critic_contract.md` §3. Every finding has What / Why / Fix / Affected +
> Alternative (for design findings).

### [CRITICAL] CRIT-7-{{N}}: {{summary}}
- **What:** {{observation, anchored to UF-ID and field}}
- **Why:** {{problem, citing external reference or rule}}
- **Fix:** {{what the block should specify}}
- **Affected:** `uf.md::{{UF-ID}}::{{field}}`
- **Alternative:** {{≥ 1 alternative with trade-off axis}}

### [WARN] CRIT-7-{{N}}: {{summary}}
- **What:** ...
- **Why:** ...
- **Fix:** ...
- **Affected:** ...
- **Alternative:** ...

### [SUGGEST] CRIT-7-{{N}}: {{summary}}
- **What:** ...
- **Why:** ...
- **Fix:** ...
- **Affected:** ...

---

## Edge-Case Representativeness Matrix

| UF-ID | Score | Missing universal floor | Missing domain-specific |
|---|:---:|---|---|
| UF-01-01 | has_all | — | — |
| UF-01-02 | has_most | — | NaN handling |
| UF-02-01 | has_only_easy | oversized input | NaN, shape mismatch with UF-01-03 |
| ...

---

## Parent-IF Contract Matching Table

| UF-ID | Output type/shape | Parent IF expected input | Match | Notes |
|---|---|---|:---:|---|
| UF-01-03 | `float32(N, 80)` | `float32(N, 80)` | ✓ | — |
| UF-02-02 | `list[dict]` | `ndarray` | ✗ | CRITICAL: contract mismatch |
| ...

---

## Alternatives Analysis

> Mandatory for every verdict. Pick the top-3 most impactful UFs in scope and propose
> ≥ 2 alternatives each.

### Decision 1 — {{UF-ID, field}}
- **Current:** {{algorithm/approach as stated}}
- **Alt-A:** {{alternative algorithm}}
  - Trade-off axis: {{e.g., accuracy vs compute}}
- **Alt-B:** {{alternative algorithm}}
  - Trade-off axis: {{e.g., memory vs latency}}
- **Defensibility:** {{"defensible given parent IF constraint X" or "Alt-A is strictly better because..."}}

### Decision 2 — {{UF-ID, field}}
...

### Decision 3 — {{UF-ID, field}}
...

---

## Verdict Justification

{{One paragraph tying the verdict to specific findings.}}

Example:
> 1 CRITICAL (UF-02-02 output type does not match parent IF-02 input contract) and
> 1 WARN (UF-03-01 letterbox resize without padding-value rationale) triggered BLOCK
> per SKILL.md §Phase E. The contract mismatch is not silently convertible — explicit
> reshape or schema change required in `uf.md` before re-submission.

---

## Next Action

- [ ] If `APPROVE`: orchestrator proceeds to `mechanical` mode for final coverage check,
      then to `builder/uf-implementor`.
- [ ] If `REQUEST_CHANGES`: producer revises `uf.md` addressing findings; re-spawn
      `uf-chain-validator --mode critique` for iteration {{next}}.
- [ ] If `BLOCK`: halt pipeline; user escalation.

---

## Known Limits (report instance)

{{List any domain gaps, unknowable judgments, or parts of the artifact not reviewed
and why. Example: "Task family 'custom-protocol-parsing' not in reference tables;
Lens C-1 alternatives generated from general knowledge only."}}

---

## Handoff

```json
{
  "skill": "uf-chain-validator",
  "mode": "critique",
  "version": "1.0",
  "role": "verifier-critic",
  "status": "COMPLETE",
  "verdict": "{{APPROVE | REQUEST_CHANGES | BLOCK}}",
  "reviewed_artifacts": [
    {"path": "uf.md", "sha256": "{{hash}}"},
    {"path": "if_list.md", "sha256": "{{hash}}"}
  ],
  "scope": {
    "parent_if": "{{IF-XX | all}}",
    "uf_count_in_scope": {{N}},
    "uf_count_total": {{N}}
  },
  "outputs": [
    {"path": "reports/critique/uf_design_{{timestamp}}_critique.md", "kind": "report"}
  ],
  "findings_summary": {
    "critical": 0,
    "warn": 0,
    "suggest": 0
  },
  "findings": [
    {
      "id": "CRIT-7-01",
      "severity": "WARN",
      "summary": "...",
      "affected": "uf.md::UF-03-01::edge_cases"
    }
  ],
  "edge_case_scores": {
    "UF-01-01": "has_all",
    "UF-01-02": "has_most",
    "UF-02-01": "has_only_easy"
  },
  "parent_if_mismatches": [
    {"uf_id": "UF-02-02", "type": "contract_mismatch", "detail": "..."}
  ],
  "alternatives_analyzed": 3,
  "iteration": 1,
  "next_action": "{{producer_revise | orchestrator_advance | user_escalate}}"
}
```
