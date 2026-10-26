## UF-Layer Review Criteria

Applies when `review_layer == uf_layer`. Every finding in this layer is anchored to a UF
Block in `uf.md`. If no UF Block can be located for a reviewed function, emit a
`BLOCK` finding (`missing_spec_reference`) and stop — do not fall back to generic review.

> **Read `../_shared/critic_contract.md` §2.1–2.3 first.**
> **Do NOT open `.pipeline/handoffs/*uf-implementor*.json` or any producer impl report.**

---

## Lens 1 — Contract Compliance (the UF-layer discriminator)

For each function under review, locate its UF Block in `uf.md`. If the filename pattern
is `src/uf/if_<IF-N>_<slug>.py` and the function name is `uf_<IF-N>_<K>_<slug>`, resolve
to `UF-<IF-N>-<K>`.

### 1.1 Signature Match

- [ ] Parameter names match the UF Block's `Inputs` field (order and spelling).
- [ ] Parameter types match exactly — `np.ndarray` when spec says `ndarray`, `float32`
      when spec says `float32`.
- [ ] Return type matches the UF Block's `Outputs` field.
- [ ] Default values match the UF Block's stated defaults (or: no defaults if spec
      specifies none).

**Signature drift → CRITICAL.** Silent parameter rename or type relaxation breaks
downstream callers.

### 1.2 Input Validation

- [ ] Every input precondition listed in the UF Block is enforced at function entry
      (type check, shape check, range check).
- [ ] Validation failures raise the exception type named in the spec (e.g.,
      `ValueError`, `TypeError`) — not a bare `Exception`.
- [ ] Validation happens before any side effect (logging, I/O, mutation).

**Missing declared precondition → CRITICAL.** Wrong exception type → WARN.

### 1.3 Output Contract

- [ ] Output shape matches spec dimensions exactly (e.g., spec says `(N, 80)` → not
      `(N, 85)` with "we'll slice later").
- [ ] Output dtype matches spec (no implicit `float64` when spec says `float32`).
- [ ] Output value range matches spec range (e.g., `[0, 1]` normalized — not `[0, 255]`).
- [ ] Output units / coordinate frame / encoding match spec declarations.

**Output contract mismatch → CRITICAL.**

### 1.4 Edge Cases

For every edge case listed in the UF Block's `Edge Cases` field:

- [ ] The corresponding branch / guard / handler is present in the code.
- [ ] The behavior matches what the spec states (e.g., "return empty array on empty
      input" — not raise).
- [ ] At least one test exists in `tests/unit/test_<uf_id>.py` covering that case.

**Mandated edge case not handled → CRITICAL.**
**Mandated edge case handled but not tested → WARN.**

### 1.5 No Undocumented Side Effects

- [ ] No global state mutation that isn't declared in the UF Block.
- [ ] No filesystem writes outside those declared in `Outputs` or side-effect notes.
- [ ] No network I/O unless spec declares it.
- [ ] No stdout/stderr prints (use structured logging if needed and declare in spec).

**Undocumented side effect → CRITICAL** when observable from caller; **WARN** when purely
internal (e.g., debug log).

### 1.6 Algorithm Fidelity

If the UF Block's `Algorithm Summary` names a specific algorithm:

- [ ] The code implements that algorithm — not a substitute (e.g., spec says "bilinear
      resize", code uses `cv2.INTER_NEAREST`).
- [ ] Numerical parameters (window size, epsilon, threshold) match the spec where
      declared.
- [ ] If the code uses a library call, the library's algorithm matches the named spec
      algorithm (and the version is pinned).

**Algorithm substitution without spec update → CRITICAL.**

---

## Lens 2 — Logic Correctness (UF-layer emphasis)

Standard logic checks (off-by-one, null guards, etc. — see SKILL.md §Lens 2) plus
UF-specific:

- [ ] Numerical stability: no silent overflow/underflow on declared input ranges.
- [ ] Division/log-of-zero guards match the spec's declared behavior (propagate NaN,
      raise, or return default).
- [ ] Shape operations preserve the declared output shape on all code paths.
- [ ] Vectorized operations have equivalent scalar fallback (or spec declares
      vectorization mandatory).

---

## Lens 3 — Code Quality (UF-layer emphasis)

Standard quality checks plus:

- [ ] Docstring references the UF-ID (e.g., `"""UF-01-03: resize with letterbox pad."""`).
- [ ] Docstring I/O section matches the UF Block verbatim where possible.
- [ ] Function length ≤ 50 lines (UFs are by definition unit-scope). Longer → SUGGEST
      split or move to a helper.

---

## Lens 4 — Test Coverage (UF-layer)

- [ ] One test file per UF: `tests/unit/test_<uf_id>.py`.
- [ ] One test function per acceptance criterion from the UF Block's `Verification Plan`.
- [ ] One negative test per declared edge case.
- [ ] Fixtures match those named in the Verification Plan; regenerable or checked in.
- [ ] Coverage ≥ the UF Block's stated target (default 90%); measured by line coverage
      on the UF's source file specifically.

**Missing acceptance-criterion test → CRITICAL** (cannot validate spec compliance).
**Missing edge-case negative test → WARN.**
**Coverage below target → WARN.**

---

## Lens 5 — Security (UF-layer)

Usually minimal for unit functions. Flag only:

- [ ] Hardcoded paths outside the scope (e.g., `/etc/passwd`, absolute home paths).
- [ ] Deserialization of untrusted input (pickle, yaml.load without SafeLoader).
- [ ] Shell invocations with unchecked input.

---

## Finding-ID Format for UF Layer

`FIND-UF-<UF-ID>-<N>` where `<N>` is sequential within the reviewed file.

Examples:
- `FIND-UF-01-03-01` — first finding on UF-01-03.
- `FIND-UF-02-01-04` — fourth finding on UF-02-01.

---

## Severity Summary (UF Layer)

| Violation | Severity |
|---|---|
| Signature drift from UF Block | CRITICAL |
| Output type / shape / range mismatch | CRITICAL |
| Missing declared precondition check | CRITICAL |
| Mandated edge case not implemented | CRITICAL |
| Algorithm substitution | CRITICAL |
| Missing acceptance-criterion test | CRITICAL |
| Assertion that always passes | CRITICAL |
| Undocumented observable side effect | CRITICAL |
| Wrong exception type on validation failure | WARN |
| Mandated edge case untested | WARN |
| Coverage below declared target | WARN |
| Missing UF-ID in docstring | WARN |
| Function > 50 lines | SUGGEST |
| Style / duplication < 5 lines | SUGGEST |

---

## Verdict Computation (UF-layer override of SKILL.md §Phase D)

```
critical_count = count(findings where severity == CRITICAL)
warn_count     = count(findings where severity == WARN)

if forbidden_exposure or missing_spec_reference: verdict = BLOCK
elif critical_count >= 1:                         verdict = BLOCK
elif warn_count >= 3:                             verdict = REQUEST_CHANGES
elif warn_count in (1, 2) and scope_is_single_file: verdict = REQUEST_CHANGES
else:                                             verdict = APPROVE
```
