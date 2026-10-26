# Stage 1-4 Critique Report

**Reviewed artifact(s):** requirements.md, problem_statement.md, assumptions_and_constraints.md
**Critic skill:** req-critic (v1.0)
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

---

## Integrity Check

- [ ] Forbidden inputs detected: {{none | list}}
  - If any: emit BLOCK with `forbidden_input_exposure` and stop.
- [ ] Required inputs present: {{✓ | ✗}}
- [ ] Artifact SHA-256 hashes recorded in handoff JSON: {{✓}}

---

## Findings

> Use the format from `../_shared/critic_contract.md` §3. Every finding must have
> What / Why / Fix / Affected. Sort by severity (CRITICAL first), then by REQ-ID.

### [CRITICAL] CRIT-1-4-{{N}}: {{one-line summary}}
- **What:** {{concrete observation, anchored to REQ-ID and field}}
- **Why:** {{problem explanation, citing external reference or rule — not producer prose}}
- **Fix:** {{what a correct REQ should specify, not exact text}}
- **Affected:** `requirements.md::{{REQ-ID}}::{{field}}`
- **Alternative:** {{≥1 alternative formulation with trade-off axis}}

### [WARN] CRIT-1-4-{{N}}: {{one-line summary}}
- **What:** ...
- **Why:** ...
- **Fix:** ...
- **Affected:** ...
- **Alternative:** ...

### [SUGGEST] CRIT-1-4-{{N}}: {{one-line summary}}
- **What:** ...
- **Why:** ...
- **Fix:** ...
- **Affected:** ...

---

## Cross-REQ Conflict Matrix

Include only rows/cells with non-OK annotations. Full matrix archived to
`reports/critique/requirements_<timestamp>_matrix.csv`.

```
| REQ \ REQ | REQ-00X | REQ-00Y | ...
| REQ-00X   |   —     | TENSION:perf-quality | ...
| REQ-00Y   |         | —        | ...
```

---

## NFR Coverage Checklist

| Category | Coverage | Referring REQ(s) |
|---|:---:|---|
| Performance      | {{✓ / ✗}} | {{REQ-IDs or "missing"}} |
| Reliability      | {{✓ / ✗}} | {{REQ-IDs or "missing"}} |
| Security         | {{✓ / ✗}} | {{REQ-IDs or "missing"}} |
| Observability    | {{✓ / ✗}} | {{REQ-IDs or "missing"}} |
| Maintainability  | {{✓ / ✗}} | {{REQ-IDs or "missing"}} |
| {{Domain-specific: compliance / determinism / etc.}} | ... | ... |

---

## Alternatives Analysis

> Mandatory for every verdict. List the top-3 most impactful REQs and propose ≥ 2
> alternatives each. This is not a rewrite recommendation — it documents that the
> producer made the choice with eyes open.

### Decision 1 — {{REQ-ID or field}}
- **Current:** {{what the REQ says}}
- **Alt-A:** {{alternative formulation}}
  - Trade-off axis: {{e.g., latency vs quality}}
- **Alt-B:** {{alternative formulation}}
  - Trade-off axis: {{e.g., generality vs specificity}}
- **Defensibility:** {{"defensible given assumptions X and Y" or "Alt-A is strictly better because..."}}

### Decision 2 — {{REQ-ID or field}}
...

### Decision 3 — {{REQ-ID or field}}
...

---

## Verdict Justification

{{One paragraph. Tie the verdict to specific findings from the Summary.}}

Example:
> 2 WARN findings (unsourced threshold on REQ-003, observability NFR gap) trigger
> REQUEST_CHANGES per SKILL.md §Verdict Rules. No CRITICAL present; Lens-1 testability
> check passed on all functional REQs. Iteration 1 of max 2.

---

## Next Action

- [ ] If `APPROVE`: orchestrator advances to `architect/if-designer`.
- [ ] If `REQUEST_CHANGES`: producer revises `requirements.md` addressing findings above;
      re-spawn `req-critic` for iteration {{next}}.
- [ ] If `BLOCK`: pipeline halts; escalate to user with this report.

---

## Handoff

```json
{
  "skill": "req-critic",
  "version": "1.0",
  "role": "verifier-critic",
  "status": "COMPLETE",
  "verdict": "{{APPROVE | REQUEST_CHANGES | BLOCK}}",
  "reviewed_artifacts": [
    {"path": "requirements.md", "sha256": "{{hash}}"},
    {"path": "problem_statement.md", "sha256": "{{hash}}"},
    {"path": "assumptions_and_constraints.md", "sha256": "{{hash}}"}
  ],
  "outputs": [
    {"path": "reports/critique/requirements_{{timestamp}}_critique.md", "kind": "report"}
  ],
  "findings_summary": {
    "critical": 0,
    "warn": 0,
    "suggest": 0
  },
  "findings": [
    {
      "id": "CRIT-1-4-01",
      "severity": "WARN",
      "summary": "...",
      "affected": "requirements.md::REQ-003::acceptance_criterion"
    }
  ],
  "nfr_coverage": {
    "performance": true,
    "reliability": true,
    "security": false,
    "observability": false,
    "maintainability": true
  },
  "alternatives_analyzed": 3,
  "iteration": 1,
  "next_action": "{{producer_revise | orchestrator_advance | user_escalate}}"
}
```
