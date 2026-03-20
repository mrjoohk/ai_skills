# Examples: Core Engineering

## Test Prompt 1: Problem → Requirements Elicitation
```
"A real-time image processing pipeline is experiencing frame drops.
 Perform Stages 1–4 and write problem_statement.md, clarification_log.md,
 assumptions_and_constraints.md, and requirements.md.
 Include numeric acceptance criteria (Given/When/Then + thresholds) in REQ blocks."
```

**Expected Output:**
- `problem_statement.md` — background and scope of impact
- `clarification_log.md` — ambiguity Q&A
- `assumptions_and_constraints.md` — constraints, boundaries, assumptions
- `requirements.md` — REQ-001 through REQ-N (with numeric acceptance criteria)

---

## Test Prompt 2: IF Identification → UF Decomposition
```
"Using requirements.md as input, perform Stages 5–7.
 Write the Integration Function (IF) list and IF→UF decomposition results.
 Include I/O contracts and verification plans in each UF block."
```

**Expected Output:**
- `if_list.md` — IF-01 through IF-N (with system boundary diagram)
- `if_decomposition.md` — subfunctions tree per IF
- `uf.md` — UF-01 through UF-N (with I/O contracts and verification plans)

---

## Test Prompt 3: Write Verification Plan
```
"Based on uf.md, perform Stage 8.
 Propose unit/integration/e2e test plans and evidence_pack/ structure.
 Specify regression thresholds numerically."
```

**Expected Output:**
- `verification_plan.md` — staged test plan with coverage goals
- Proposed `evidence_pack/` structure

---

## Test Prompt 4: Minimal Diff Refactoring
```
"Remove redundant assignments in src/pipeline/processor.py.
 Do not change behavior; output only in diff format.
 Add unit tests that guarantee output equivalence."
```

**Expected Output:**
- `git diff`-format patch
- Behavioral equivalence unit tests

---

## Output Quality Checklist
- [ ] All requirements have numeric acceptance criteria (Given/When/Then)
- [ ] All I/O contracts specify type, unit, and shape
- [ ] All Assumptions are explicitly recorded
- [ ] UF-ID and IF-ID linkage is clear
- [ ] Evidence artifact paths are defined
