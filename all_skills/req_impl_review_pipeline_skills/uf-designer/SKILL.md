---
name: uf-designer
description: >
  Executes core-engineering Stage 7: reads if_decomposition.md (UF candidate tree
  from if-designer) and produces uf.md — fully specified UF Blocks with I/O contracts,
  algorithm summaries, edge cases, and verification plans. This is the final design
  artifact before implementation begins. Trigger when the user says "UF 설계해줘",
  "UF 블록 만들어줘", "uf.md 작성", "유닛 함수 정의해줘", "UF spec 써줘", or after
  if-designer has produced if_decomposition.md and the user wants to define UF Blocks
  before running uf-implementor or uf-chain-validator. Also trigger when the user has
  a decomposition tree and wants to formalize each leaf node into an implementable spec.
---

# UF-Designer — Core Engineering Stage 7

This skill transforms leaf nodes in `if_decomposition.md` into complete UF Blocks
that `uf-implementor` can directly implement.

> **Read `references/reference.md`** for the UF Block format and edge case taxonomy.
> **Copy the template from `assets/uf_block_template.md`** for each UF.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/reference.md` | UF Block format, algorithm summary patterns, edge case taxonomy, verification plan format |
| `assets/uf_block_template.md` | Copy → fill for each UF Block in uf.md |
| `scripts/validate_uf_design.py` | Run after generating uf.md to verify completeness |

---

## Input

- **Required:** `if_decomposition.md` (produced by `if-designer`)
- **Optional:** `if_list.md` — use to look up parent IF I/O contracts if needed
- If `if_decomposition.md` is missing, stop and ask the user to run `if-designer` first.

---

## Execution Flow

### Phase A — Read and Enumerate UF Candidates

Read `if_decomposition.md` and extract all leaf nodes (UF candidates).
Build a list: `UF-ID | Parent IF | Name | Input | Output`.

Confirm with yourself that each candidate satisfies SRP before writing its block:
- Can it be described in a single sentence starting with a verb?
- Does it have exactly one input data type and one output data type?
- Can it be tested in isolation with a mock of its inputs?

If a candidate is too large, split it and note the new IDs.

---

### Phase B — Write UF Blocks

For each UF candidate, write a full UF Block in `uf.md`.
Use `assets/uf_block_template.md`.

**Critical rules:**

**I/O Contract** — must be as specific as the IF's contract, not more vague:
- If the IF says `float32, shape=(N, 85)`, the UF says the same, not just `tensor`
- Include coordinate system if spatial (pixel, normalized, world)
- Include value range if numeric

**Algorithm Summary** — 1–3 lines maximum:
- State the algorithm name or pattern, not just "process the input"
- Example: "Apply letterbox resize: compute scale factor, pad shorter dimension with gray (114, 114, 114)"
- No code in the algorithm summary — pseudocode is fine

**Edge Cases** — be specific about what goes wrong:
- Empty input (zero-length array, None)
- Out-of-range values (negative, infinity, NaN)
- Shape mismatches between consecutive UFs
- Resource exhaustion (OOM, disk full)
- For each: state the expected behavior (raise, return default, log-and-skip)

**Verification Plan** — name concrete test functions:
- Unit test path: `tests/unit/test_<uf_name>.py::test_<scenario>`
- Coverage target: always `>= 90%` unless justified

**UF-IDs** — use the parent IF ID as prefix: `UF-01-01`, `UF-01-02`, `UF-02-01`, ...

**Output:** `uf.md`

---

### Phase C — I/O Chain Continuity Check

After writing all UF Blocks, verify the chain for each IF:
- Output type of UF-N must match input type of UF-(N+1)
- No implicit type conversions between UFs
- Flag mismatches as `[CHAIN BREAK: UF-XX → UF-YY: output X ≠ input Y]`

---

### Phase D — Validation

```bash
python <skill_dir>/scripts/validate_uf_design.py uf.md
```

Fix all failures before handing off.

---

## Downstream Handoff

```
✅ Stage 7 complete.
  - uf.md (UF-XX-YY blocks, ready for implementation)

Two options for next steps:
  A. Validate design first  → run /uf-chain-validator with uf.md + if_list.md
  B. Start implementing     → run /uf-implementor with uf.md
```

---

## Quality Checklist

- [ ] Every UF has a single-verb Goal statement
- [ ] I/O Contract specifies type + unit/shape + range (no vague "tensor" or "data")
- [ ] Algorithm Summary is 1–3 lines and names a concrete algorithm
- [ ] At least 3 Edge Cases per UF (empty, out-of-range, shape mismatch)
- [ ] Verification Plan names test function paths
- [ ] I/O chain is continuous across all UFs within each IF
- [ ] UF-IDs follow `UF-[parent_IF_num]-[seq]` format
