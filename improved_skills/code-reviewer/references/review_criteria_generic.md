## Generic-Layer Review Criteria

Applies when `review_layer == generic` — used for arbitrary code with no linked UF
Block or IF Block. This is the legacy / fallback mode, preserved for code reviews
outside the core-engineering pipeline.

> **Generic layer is NOT a Critic in the §2.3 sense** — there is no adversarial stance
> against a named producer, no alternatives mandate, no forbidden-input list. Generic
> layer is a plain Verifier that still honors:
> - §2.1 **Independence** — runs in a fresh sub-agent, no shared state with upstream.
> - Finding format from §3 — What / Why / Fix / Affected.
> - Verdict enum `APPROVE / REQUEST_CHANGES / BLOCK`.

---

## Lens 1 — (N/A for generic)

Generic review has no spec to check against. Skip this lens.

If a UF Block or IF Block is actually available for the reviewed code, **stop and
re-dispatch** as `uf_layer` or `if_layer`. Do not produce a generic review when a
spec-linked layer is applicable.

---

## Lens 2 — Logic Correctness

- [ ] Off-by-one errors: loop bounds, slice indices, range ends.
- [ ] Null / None / undefined: all nullable inputs guarded before dereference.
- [ ] Type coercion: no implicit conversions that lose data (int → float, wide → narrow).
- [ ] Branching completeness: every logical state handled; no implicit fall-through.
- [ ] Error propagation: exceptions caught at the appropriate level — not swallowed,
      not over-broad.
- [ ] Mutation safety: shared state not mutated across call boundaries unless declared.
- [ ] Async/await: promises / awaitables not dropped.
- [ ] Resource lifecycle: files / sockets / locks released on all paths, including
      exceptions.
- [ ] Concurrency: shared mutable state protected or documented as single-threaded.
- [ ] Numeric stability: no silent overflow / underflow on expected input ranges.

**Severity guidance:**
| Issue | Severity |
|---|---|
| Logic error producing wrong results on known input | CRITICAL |
| Unhandled exception crashing in production | CRITICAL |
| Resource leak on error path | CRITICAL |
| Silent error-swallow | WARN |
| Mutation-across-boundary not documented | WARN |
| Off-by-one in non-critical path | WARN |

---

## Lens 3 — Code Quality

- [ ] Names represent what, not how (e.g., `user_ids` vs `array1`).
- [ ] Single responsibility per function — one level of abstraction per body.
- [ ] No copy-pasted logic ≥ 5 lines (extract or parameterize).
- [ ] Magic numbers / strings extracted to named constants.
- [ ] Comments on non-obvious logic; no commented-out dead code.
- [ ] Public API documented (types, raises, returns).
- [ ] Function length ≤ 60 lines (soft limit).
- [ ] Nesting depth ≤ 4 levels (flatten with early returns or helpers).

**Severity guidance:**
| Issue | Severity |
|---|---|
| Missing docstring on public function | WARN |
| Copy-paste ≥ 5 lines | WARN |
| Magic number in critical logic | WARN |
| Style inconsistency / short duplication | SUGGEST |
| Function > 60 lines | SUGGEST |

---

## Lens 4 — Test Coverage

- [ ] Tests exist for the reviewed module/file.
- [ ] Tests assert specific outputs (not just "no exception raised").
- [ ] Negative tests cover expected error paths.
- [ ] Fixtures are deterministic (seeded randomness).
- [ ] Coverage of the reviewed file ≥ 80% lines (soft target for generic).

**Severity guidance:**
| Issue | Severity |
|---|---|
| Assertion that always passes (e.g., `assert x is not None` only) | CRITICAL |
| No tests for reviewed file | CRITICAL when public-facing, WARN when internal |
| Flaky / nondeterministic test | WARN |
| Missing negative test for declared error path | WARN |
| Coverage 60–80% | SUGGEST |
| Coverage < 60% | WARN |

---

## Lens 5 — Security

Applies when the reviewed code handles external input, user data, or trust boundaries.

- [ ] No raw SQL or shell command built by string concatenation with external input.
- [ ] No secrets hardcoded (API keys, tokens, passwords, connection strings).
- [ ] External inputs sanitized / validated before use.
- [ ] File-path inputs restricted to allowed directories (path traversal guard).
- [ ] Deserialization of untrusted input uses safe loaders (`yaml.safe_load`, not
      `yaml.load`; avoid `pickle` on untrusted data).
- [ ] Cryptographic primitives use library defaults, not hand-rolled.

**Severity guidance:**
| Issue | Severity |
|---|---|
| Injection risk (SQL, shell, path) on external input path | CRITICAL |
| Hardcoded secret | CRITICAL |
| Unsafe deserialization on external input | CRITICAL |
| Missing input sanitization | WARN |
| Hand-rolled crypto / hashing | WARN |

---

## Finding-ID Format for Generic Layer

`FIND-GEN-<file-slug>-<N>` where `<file-slug>` is the reviewed filename with path
separators replaced by hyphens and extension dropped, and `<N>` is sequential.

Examples:
- `FIND-GEN-utils-parser-01` for `utils/parser.py`.
- `FIND-GEN-api-handlers-auth-03` for `api/handlers/auth.py`.

---

## Verdict Computation (Generic-layer override of SKILL.md §Phase D)

```
critical_count = count(findings where severity == CRITICAL)
warn_count     = count(findings where severity == WARN)

if critical_count >= 1:   verdict = BLOCK
elif warn_count >= 5:     verdict = REQUEST_CHANGES
elif warn_count >= 1:     verdict = REQUEST_CHANGES when scope_is_single_file
                                    else APPROVE with findings
else:                     verdict = APPROVE
```

Generic layer is more lenient on WARN counts than UF/IF layers because there is no
spec to anchor findings.

---

## Known Limits of Generic Layer

- Cannot check contract compliance (no contract).
- Cannot verify completeness of behavior (no acceptance criteria).
- Cannot rank criticality of edge cases (no declared edge-case list).
- Produces weaker guidance than `uf_layer` or `if_layer`.

If the reviewed code is pipeline-produced (by `uf-implementor` or `if-integrator`),
the orchestrator should route to the layered variant instead. Generic is reserved for
legacy code, third-party integration points, or exploratory scripts.
