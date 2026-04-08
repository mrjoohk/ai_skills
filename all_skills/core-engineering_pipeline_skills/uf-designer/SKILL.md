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

Also carry forward the `Verification Owner` declared in `if_decomposition.md` for each leaf node.
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

**Verification Plan** — classify by ownership, then name concrete artifacts:

Every UF Block must declare three sub-fields:

```
Verification Plan:
  Ownership: <UF-local | guard-rail+chain | IF-acceptance>
  Unit Verification:
    - <test path or "N/A — ownership: guard-rail+chain|IF-acceptance">
    - Coverage target: >= 90% (UF-local only; omit or mark N/A for others)
  Chain Verification:
    - <IF-level test path that validates this UF's behavior, or "N/A — ownership: UF-local">
```

**Ownership rules:**

| Ownership | Unit Verification | Chain Verification |
|---|---|---|
| `UF-local` | Required — name standalone test path(s), coverage >= 90% | N/A |
| `guard-rail+chain` | Guard-rail tests only (input/output type guards, sentinel checks) | Required — name IF-chain test path |
| `IF-acceptance` | N/A | Required — name IF-acceptance test path |

> Do not default to `UF-local` for assembly, packaging, or merge nodes. Their behavioral
> correctness is only meaningful inside the chain, so forcing standalone tests creates
> false precision and documentation drift.

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

### Phase E — Generate per-IF Companion Documents (uf_split/)

After `uf.md` is complete and validated, split it into per-IF companion files.
Create one file per IF under `uf_split/`:

```
uf_split/
  uf_if01.md   ← all UF blocks whose parent IF is IF-01
  uf_if02.md   ← all UF blocks whose parent IF is IF-02
  uf_if03.md   ← all UF blocks whose parent IF is IF-03
  ...
```

Each companion file contains:
- A header: `# UF Blocks — IF-NN (IF name)` 
- The full UF Blocks for that IF, copied verbatim from `uf.md`
- A summary table at the top: `UF-ID | Name | Verification Owner`

> `uf.md` remains the single canonical source. The `uf_split/` files are read-only
> derived views — they are regenerated whenever `uf.md` changes.

**Output:** `uf_split/uf_if01.md`, `uf_split/uf_if02.md`, … (one per IF)

---

## Downstream Handoff

```
✅ Stage 7 complete.
  - uf.md                  (canonical UF Blocks — all IFs)
  - uf_split/uf_if01.md    (per-IF companion view, IF-01)
  - uf_split/uf_if02.md    (per-IF companion view, IF-02)
  - ...                    (one file per IF)

Two options for next steps:
  A. Validate design first  → run /uf-chain-validator with uf.md + if_list.md
  B. Start implementing     → run /uf-implementor with uf.md (or per-IF uf_split/ file)
```

---

## Quality Checklist

- [ ] Every UF has a single-verb Goal statement
- [ ] I/O Contract specifies type + unit/shape + range (no vague "tensor" or "data")
- [ ] Algorithm Summary is 1–3 lines and names a concrete algorithm
- [ ] At least 3 Edge Cases per UF (empty, out-of-range, shape mismatch)
- [ ] Every UF Verification Plan declares `Ownership`, `Unit Verification`, and `Chain Verification`
- [ ] `UF-local` UFs name a concrete standalone test path and coverage target
- [ ] `guard-rail+chain` UFs name guard-rail tests AND the IF-chain test path
- [ ] `IF-acceptance` UFs name the IF-acceptance test path (no standalone test required)
- [ ] No assembly/packaging/merge node is assigned `UF-local` without explicit justification
- [ ] I/O chain is continuous across all UFs within each IF
- [ ] UF-IDs follow `UF-[parent_IF_num]-[seq]` format
- [ ] `uf_split/` companion files exist for every IF and match `uf.md`
