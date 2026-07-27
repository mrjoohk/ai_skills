# Reference: UF Chain Validation Report

## Report Header
```
- Project:           <project name>
- Commit:            <commit_sha>
- Date:              <YYYY-MM-DD>
- Validator Version: <version>
- UF Scope:          UF-01 .. UF-XX
- IF Scope:          IF-01 .. IF-XX
```

---

## Summary
```
- PASS count:           N
- WARN count:           N
- FAIL count:           N
- Overall coverage:     XX%
- Priority fixes:       (summary of FAIL items)
```

---

## Findings Table
```
| UF-ID | Status | Issue Type | Location (path::symbol) | Evidence Link | Fix Proposal |
|------:|:----:|---------|----------------|---------|--------|
| UF-03 | FAIL | Missing I/O contract | docs/uf/uf03.md | —  | Add type·unit·shape |
| UF-07 | WARN | No unit test        | tests/              | —  | Add pytest test     |
```

---

## Check Items

| # | Check Item | PASS Criteria |
|---|---------|---------|
| 1 | UF-ID continuity and uniqueness | No duplicate or missing numbers |
| 2 | I/O contract exists | Type·unit·shape all specified |
| 3 | Test mapping exists | Unit/integration tests linked to UF |
| 4 | Meaningful acceptance criteria (Assert) | More than just smoke test |
| 5 | Evidence pack reference exists | Path and schema documented |
| 6 | CI gate matches local expected values | Coverage thresholds match |
| 7 | IF → UF linkage completeness | All UFs have parent IF |

---

## Minimal Fix Guide
- Specify target file path + section title
- Provide code and document changes in patch (diff) format
- Keep refactoring and behavior changes in separate commits
