# Code Review Report

**Review layer:** {{uf_layer | if_layer | generic}}
**Reviewed artifact(s):** {{list of source files or scope descriptor}}
**Spec reference:** {{uf.md UF-XX-YY | if_list.md IF-XX | n/a for generic}}
**Critic skill:** code-reviewer (v1.0, layer: {{layer}})
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

Files in scope: {{count}}
{{If fan-out active:}} Fan-out scope: {{parent_if=IF-XX | file=path | n/a}}

---

## Integrity Check

- [ ] Layer: {{uf_layer | if_layer | generic}}
- [ ] Forbidden inputs detected: {{none | list (triggers BLOCK)}}
  - `uf_layer`: `.pipeline/handoffs/*uf-implementor*.json` — {{not opened}}
  - `uf_layer`: `reports/impl/uf_impl_report_*.md` — {{not opened}}
  - `if_layer`: `.pipeline/handoffs/*if-integrator*.json` — {{not opened}}
  - `if_layer`: `if_decomposition.md` — {{not opened}}
  - `if_layer`: `reports/impl/if_integration_report_*.md` — {{not opened}}
  - `generic`: (no forbidden list)
- [ ] Required spec file readable: {{✓ | ✗ (triggers BLOCK)}}
- [ ] Artifact SHA-256 hashes recorded in handoff JSON: {{✓}}

---

## Findings

> Sort by severity (CRITICAL first), then by finding ID.
> Format per `../_shared/critic_contract.md` §3: What / Why / Fix / Affected.
> Finding-ID pattern by layer:
> - `uf_layer`: `FIND-UF-<UF-ID>-<N>`
> - `if_layer`: `FIND-IF-<IF-ID>-<N>`
> - `generic`: `FIND-GEN-<file-slug>-<N>`

### [CRITICAL] {{FIND-ID}}: {{one-line summary}}
- **What:** {{observation anchored to file:line and function/variable name}}
- **Why:** {{citation to UF Block / IF Block clause, or external rule}}
- **Fix:** {{correct behavior — not exact code}}
- **Affected:** `{{path/to/file.py:line}}`

### [WARN] {{FIND-ID}}: {{one-line summary}}
- **What:** ...
- **Why:** ...
- **Fix:** ...
- **Affected:** ...

### [SUGGEST] {{FIND-ID}}: {{one-line summary}}
- **What:** ...
- **Why:** ...
- **Fix:** ...
- **Affected:** ...

---

## Contract Compliance Matrix (uf_layer / if_layer only)

For `uf_layer`:

| UF-ID | Signature | Preconditions | Output contract | Edge cases | Algorithm | Tests |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| UF-01-03 | ✓ | ✓ | ✗ | ✓ | ✓ | partial |
| ... | | | | | | |

For `if_layer`:

| IF-ID | Entry signature | UF call set | UF order | Postconditions | Error handling | Integration tests |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| IF-01 | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| ... | | | | | | |

For `generic`: omit this section.

---

## Test Coverage Summary

| File | Coverage | Target | Status |
|---|---:|---:|:---:|
| src/uf/if_01_resize.py | 92% | 90% | ✓ |
| src/uf/if_01_normalize.py | 78% | 90% | ✗ (WARN) |
| ... | | | |

---

## Verdict Justification

{{One paragraph tying the verdict to specific findings.}}

Example (uf_layer):
> 1 CRITICAL (FIND-UF-01-03-01: output dtype float64 vs spec float32) and 2 WARN
> (missing edge-case test for empty input; coverage 78% below 90% target) triggered
> BLOCK per review_criteria_uf.md §Verdict Computation. Contract mismatch on dtype is
> not silently convertible downstream.

Example (if_layer):
> 0 CRITICAL, 4 WARN (missing failure-injection test, entry-point 95 lines with embedded
> logic, one unlabeled re-raise, coverage 81%) triggered REQUEST_CHANGES. IF-layer gates
> on WARN ≥ 3.

Example (generic):
> 0 CRITICAL, 2 WARN (missing docstring on public handler, copy-paste of 8 lines in
> error-path) — scope is single file → REQUEST_CHANGES.

---

## Next Action

- [ ] If `APPROVE`: orchestrator proceeds downstream (next stage or commit).
- [ ] If `REQUEST_CHANGES`: run `cursor-task-formatter --mode fix` on this report to
      generate Cursor fix prompts. Producer revises; re-spawn `code-reviewer` with the
      same `review_layer` for iteration {{next}}.
- [ ] If `BLOCK`: halt pipeline; escalate to user with this report.

---

## Known Limits (report instance)

{{List any scope gaps, parts of the code not reviewed, or inferential limits. Example:
"Reviewed only changed lines in PR #142; unchanged code not re-audited. Did not
execute tests — coverage numbers extracted from existing report."}}

---

## Handoff

```json
{
  "skill": "code-reviewer",
  "review_layer": "{{uf_layer | if_layer | generic}}",
  "version": "1.0",
  "role": "{{verifier-critic | verifier}}",
  "status": "COMPLETE",
  "verdict": "{{APPROVE | REQUEST_CHANGES | BLOCK}}",
  "critic_of": "{{uf-implementor | if-integrator | null}}",
  "reviewed_artifacts": [
    {"path": "src/uf/if_01_resize.py", "sha256": "{{hash}}"},
    {"path": "uf.md", "sha256": "{{hash}}"}
  ],
  "scope": {
    "layer": "{{uf_layer | if_layer | generic}}",
    "fanout_scope_key": "{{file_path | parent_if | null}}",
    "fanout_scope_value": "{{src/uf/if_01_resize.py | IF-01 | null}}",
    "files_in_scope": {{N}}
  },
  "outputs": [
    {"path": "reports/review/{{layer}}_{{timestamp}}_review.md", "kind": "report"}
  ],
  "findings_summary": {
    "critical": 0,
    "warn": 0,
    "suggest": 0
  },
  "findings": [
    {
      "id": "FIND-UF-01-03-01",
      "severity": "CRITICAL",
      "summary": "Output dtype float64 vs spec float32",
      "affected": "src/uf/if_01_resize.py:47",
      "spec_ref": "uf.md::UF-01-03::Outputs"
    }
  ],
  "contract_compliance": {
    "signature_match": true,
    "output_contract_match": false,
    "edge_cases_complete": true,
    "tests_map_to_acceptance": "partial"
  },
  "iteration": 1,
  "next_action": "{{producer_revise | orchestrator_advance | user_escalate}}"
}
```
