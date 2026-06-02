## IF-Layer Review Criteria

Applies when `review_layer == if_layer`. Every finding in this layer is anchored to an
IF Block in `if_list.md`. If no IF Block can be located for a reviewed entry-point,
emit a `BLOCK` finding (`missing_spec_reference`).

> **Read `../_shared/critic_contract.md` §2.1–2.3 first.**
> **Do NOT open `.pipeline/handoffs/*if-integrator*.json`, `if_decomposition.md`, or any
> producer integration report.** Producer reasoning is off-limits.

---

## Lens 1 — Contract Compliance (the IF-layer discriminator)

For each entry-point function under review, locate its IF Block in `if_list.md`.
Filename pattern `src/if/if_<IF-ID>.py` maps to the IF Block whose `id: IF-<IF-ID>`
matches.

### 1.1 IF Entry-Point Signature

- [ ] The public entry point exposes only the IF Block's declared `Inputs` and `Outputs`.
- [ ] Internal UF signatures do not leak (no UF-specific parameters exposed on the IF
      entry point).
- [ ] Return type matches the IF Block's `Outputs` — including nested types (dict
      schema, dataclass fields).

**Signature drift from IF Block → CRITICAL.**
**Internal UF parameter exposed on entry point → CRITICAL** (tight coupling; violates
module boundary).

### 1.2 UF Call Orchestration (inferred from code, not decomposition file)

> **Do not read `if_decomposition.md`.** Infer the expected UF chain from `uf.md` (UF
> IDs under this IF) and the code's call structure.

- [ ] Every UF named in `uf.md` under this IF is invoked somewhere in the IF
      implementation (exactly once, unless the spec declares a loop).
- [ ] UF call order respects data-flow dependencies (no UF consuming an output before
      its producer runs).
- [ ] Intermediate results between UFs are not silently reshaped/retyped (that would
      hide a contract gap at the UF-chain boundary).
- [ ] No "extra" functions performing spec-unnamed transforms between UF calls (they
      should either be new UFs or moved into an existing UF).

**UF in spec but never called → CRITICAL.**
**UF invoked in wrong dependency order → CRITICAL.**
**Silent inter-UF reshape hiding a contract mismatch → CRITICAL.**
**Hidden intermediate transform → WARN** (candidate for UF promotion).

### 1.3 Acceptance-Criterion Postconditions

For every `Given/When/Then` or similar acceptance criterion in the IF Block:

- [ ] A postcondition check (assert, raise, return-type validation) is present on the
      IF entry-point path — not buried inside a UF.
- [ ] The postcondition checks the exact property the criterion states (numeric range,
      shape, cardinality, ordering).
- [ ] The postcondition is enabled in production builds (not behind `if __debug__:` or
      similar), unless the spec declares debug-only.

**Missing postcondition for declared acceptance criterion → CRITICAL.**
**Postcondition checks wrong property → CRITICAL.**
**Postcondition debug-gated when spec requires runtime → WARN.**

### 1.4 Error Handling at IF Boundary

- [ ] Exceptions raised by internal UFs are either re-raised, wrapped in the IF's
      declared exception type, or handled with a fallback declared in the IF Block.
- [ ] The IF does not silently swallow UF exceptions.
- [ ] Error messages at the IF boundary reference the IF-ID and the failing UF, not
      low-level stack frames.

**Silent swallow of UF exception → CRITICAL** (hides upstream contract violations).
**Unlabeled re-raise without IF-ID context → WARN.**

### 1.5 Cross-REQ Linkage

- [ ] Every `traces_to: REQ-XXX` in the IF Block maps to at least one acceptance
      criterion that the implementation enforces.
- [ ] If REQ-XXX is a non-functional requirement (latency, memory), the IF exposes a
      benchmark hook or the requirement is enforced elsewhere (documented).

**REQ traced but not enforced → CRITICAL.**

---

## Lens 2 — Logic Correctness (IF-layer emphasis)

Standard logic checks plus:

- [ ] Partial-failure handling: if UF-N of M succeeds and UF-N+1 fails, the IF either
      rolls back UF-N's effects or leaves a recoverable state documented in the spec.
- [ ] Idempotency declared in the IF Block is actually idempotent (second call with
      same input returns same output without side effects).
- [ ] Concurrency: if the IF Block declares thread-safety or async-safety, shared
      state is protected (locks, immutable data, or single-writer discipline).
- [ ] Resource lifetime: file handles / sockets / GPU memory opened in the IF are
      closed on every exit path, including exceptions.

---

## Lens 3 — Code Quality (IF-layer emphasis)

Standard quality checks plus:

- [ ] Module-level docstring references the IF-ID and summarizes the IF Block's
      purpose.
- [ ] Entry-point function length ≤ 80 lines; if longer, it is orchestration-only
      (the body is primarily UF calls + postcondition checks, no embedded logic).
- [ ] Private helper functions within the IF module are clearly named and scoped
      (not re-exported).

---

## Lens 4 — Test Coverage (IF-layer)

- [ ] Integration test file exists: `tests/integration/test_if_<IF-ID>.py`.
- [ ] One test exercises the full UF chain through the IF entry point (not direct-UF
      calls).
- [ ] One test per acceptance criterion in the IF Block asserts the specific property.
- [ ] At least one test injects a failure into a UF and asserts the IF's declared
      error handling.
- [ ] Integration test fixtures are distinct from unit-test fixtures (covers cross-UF
      interaction, not just individual UF correctness).

**Missing integration test for IF → CRITICAL.**
**Integration test bypasses entry point (calls UFs directly) → CRITICAL** (defeats the
purpose of IF-level testing).
**Missing failure-injection test → WARN.**
**Coverage < 85% of IF source → WARN.**

---

## Lens 5 — Security (IF-layer)

IF modules often cross trust boundaries. Flag:

- [ ] External input reaching the IF is validated at the entry point before any UF call.
- [ ] Authentication / authorization checks (if declared in REQ linkage) are present
      before any state-mutating UF.
- [ ] Logging at the IF level does not leak secrets (tokens, PII) that are acceptable
      in internal UF logs.
- [ ] Rate limiting / quota enforcement (if in REQ) at IF boundary, not inside UFs.

**Auth check missing on mutating path → CRITICAL.**
**Secret leaked to logs/errors → CRITICAL.**
**Validation deferred to inner UF when spec requires boundary validation → WARN.**

---

## Finding-ID Format for IF Layer

`FIND-IF-<IF-ID>-<N>` where `<N>` is sequential within the reviewed IF.

Examples:
- `FIND-IF-01-01` — first finding on IF-01.
- `FIND-IF-03-05` — fifth finding on IF-03.

---

## Severity Summary (IF Layer)

| Violation | Severity |
|---|---|
| IF entry-point signature drift | CRITICAL |
| UF internal param exposed on entry | CRITICAL |
| UF in spec not called | CRITICAL |
| UF call order wrong | CRITICAL |
| Silent inter-UF reshape hiding contract mismatch | CRITICAL |
| Missing postcondition for acceptance criterion | CRITICAL |
| Postcondition checks wrong property | CRITICAL |
| Silent swallow of UF exception | CRITICAL |
| REQ traced but not enforced | CRITICAL |
| Missing integration test | CRITICAL |
| Integration test bypasses entry point | CRITICAL |
| Auth missing on mutating path | CRITICAL |
| Secret leaked to logs | CRITICAL |
| Hidden intermediate transform between UFs | WARN |
| Unlabeled re-raise without IF-ID | WARN |
| Postcondition debug-gated against spec | WARN |
| Missing failure-injection test | WARN |
| Coverage < 85% | WARN |
| Boundary validation deferred to inner UF | WARN |
| Entry-point > 80 lines with embedded logic | SUGGEST |
| Private helper naming unclear | SUGGEST |

---

## Verdict Computation (IF-layer override of SKILL.md §Phase D)

```
critical_count = count(findings where severity == CRITICAL)
warn_count     = count(findings where severity == WARN)

if forbidden_exposure or missing_spec_reference: verdict = BLOCK
elif critical_count >= 1:                         verdict = BLOCK
elif warn_count >= 3:                             verdict = REQUEST_CHANGES
elif warn_count in (1, 2):                        verdict = REQUEST_CHANGES
else:                                             verdict = APPROVE
```

IF-layer is stricter than UF-layer on WARN counts because IF contracts span more code
and each WARN tends to hide systemic issues.
