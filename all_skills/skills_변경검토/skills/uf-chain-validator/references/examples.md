# Examples: UF Chain Validator

## Test Prompt 1: UF Chain Integrity Verification
```
"Validate UF-01..UF-18 in docs/uf/. Flag missing I/O contracts,
 test mappings, and evidence pack references. Output to
 reports/uf_validation.md."
```

**Expected output:**
- `reports/uf_validation.md` (header + summary + findings table)
- PASS/WARN/FAIL aggregates

---

## Test Prompt 2: Pre-Merge Gate Check
```
"Validate the UF chain on the current branch. Produce a concise
 PASS/FAIL summary suitable for PR comments. Include minimal diffs
 for any required documentation changes."
```

**Expected output:**
- 1-5 line summary (for PR comment)
- Diffs for items needing fixes

---

## Test Prompt 3: Coverage Shortfall Triage
```
"CI reports 71% coverage (<85%). Identify which UF modules lack
 tests and propose the minimal test set needed to reach 85%."
```

**Expected output:**
- List of under-tested UFs (with current coverage)
- Minimal test list to add (path::test name)

---

## Test Prompt 4: IF → UF Linkage Completeness Check
```
"For IF-01..IF-08 in docs/if/, verify that each IF is linked to
 at least one UF. Flag IFs with no links as FAIL and propose UF
 additions."
```

**Expected output:**
- List of linked UFs per IF
- List of unlinked IFs + UF addition proposals
