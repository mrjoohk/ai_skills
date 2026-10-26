# Review Criteria Checklist

## Contract Compliance

- [ ] Function signature matches UF spec (param names, types, return type)
- [ ] All inputs validated against spec constraints
- [ ] Output shape/type matches spec
- [ ] Each documented edge case is handled with correct behavior
- [ ] No undocumented side effects

## Logic Correctness

- [ ] Off-by-one: loop bounds, slice indices, pagination offsets
- [ ] Null/None/undefined: all nullable inputs guarded
- [ ] Type coercion: no implicit conversions that could lose data
- [ ] Branching completeness: if/else covers all logical states
- [ ] Error handling: exceptions caught at the right level (not too broad, not too narrow)
- [ ] Mutation safety: shared state not mutated unexpectedly
- [ ] Async/await: promises not left unhandled

## Code Quality

- [ ] Names: variables and functions named for what they represent, not what they do
- [ ] Single responsibility: each function does one thing
- [ ] Duplication: no logic copy-pasted that should be shared
- [ ] Magic numbers/strings: literals extracted to named constants
- [ ] Comments: complex logic commented; no commented-out dead code
- [ ] Test coverage: each acceptance criterion has at least one test
- [ ] Test quality: tests assert specific outputs, not just "no exception"

## Security (flag if applicable)

- [ ] No raw SQL / command injection risk
- [ ] No secrets or credentials hardcoded
- [ ] External inputs sanitized before use

---

## Severity Assignment Guide

| Situation | Severity |
|---|---|
| Contract violated (wrong output type, missing edge case that spec requires) | CRITICAL |
| Logic error that would produce wrong results in known inputs | CRITICAL |
| Unhandled exception path that crashes in production | CRITICAL |
| Edge case not in spec but clearly possible | WARN |
| Error swallowed silently | WARN |
| Missing test for a covered acceptance criterion | WARN |
| Confusing variable name | SUGGEST |
| Duplicated logic (< 5 lines) | SUGGEST |
| Style inconsistency with surrounding code | SUGGEST |
