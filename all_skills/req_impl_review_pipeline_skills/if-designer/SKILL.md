---
name: if-designer
description: >
  Executes core-engineering Stages 5–6: reads requirements.md (REQ Blocks) and
  produces if_list.md (Integration Function definitions with I/O contracts) and
  if_decomposition.md (IF→UF candidate tree with dependency graph). This is the
  bridge between requirements and implementation — it translates what the system
  must do into a concrete module boundary design. Trigger when the user says
  "IF 설계해줘", "인터페이스 설계", "if_list 만들어줘", "시스템 경계 설계", "IF 분해해줘",
  "IF decomposition", "모듈 경계 잡아줘", or after req-elicitor has produced
  requirements.md and the user wants to proceed to Stage 5–6. Also trigger when
  the user provides requirements.md and wants to know how to break the system
  into integration functions before implementing UFs.
---

# IF-Designer — Core Engineering Stages 5–6

This skill takes `requirements.md` as input and produces two design artifacts that
`uf-designer` and `uf-implementor` depend on.

> **Read `references/reference.md`** for IF Block and decomposition templates before writing.
> **Copy templates from `assets/`** — fill in rather than writing from scratch.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/reference.md` | IF Block format, decomposition tree syntax, SRP rules |
| `references/examples.md` | Worked example: requirements.md → if_list.md → if_decomposition.md |
| `assets/if_list_template.md` | Copy → fill for Stage 5 output |
| `assets/if_decomposition_template.md` | Copy → fill for Stage 6 output |
| `scripts/validate_if_design.py` | Run after generating both files to verify completeness |

---

## Input

- **Required:** `requirements.md` (produced by `req-elicitor`)
- If `requirements.md` is missing, stop and ask the user to run `req-elicitor` first.

---

## Execution Flow

### Phase A — Stage 5: IF Identification

Read `requirements.md` and identify Integration Functions — the top-level system
boundary modules that fulfill one or more REQs.

**Grouping heuristic:**
- Each IF should have a single clear external interface (one input → one output)
- Group REQs that share the same data producer/consumer chain into one IF
- Separate IFs when the data type, protocol, or processing domain changes significantly
- A typical system has 3–8 IFs; more than 10 suggests too fine-grained decomposition

**For each IF, write an IF Block** (use `assets/if_list_template.md`):
- `IF-ID`: sequential, IF-01, IF-02, …
- `Producer` and `Consumer`: the component or actor on each side
- `Input Contract` and `Output Contract`: type + unit/shape + range (same rigor as REQ I/O)
- `Linked REQs`: which REQ IDs this IF satisfies (at least one per IF)
- `Failure Modes`: what breaks if this interface fails

**Output:** `if_list.md`

---

### Phase B — Stage 6: IF Decomposition

For each IF in `if_list.md`, decompose it into a tree of subfunctions (UF candidates).

**Decomposition rules:**
- Each subfunction must satisfy the Single Responsibility Principle: one clear job
- The output of one subfunction must be the input of the next (chain continuity)
- Depth: prefer 2–3 levels; stop decomposing when a node is "implement in 1 function"
- Name subfunctions with verb-noun format: `parse_frame`, `normalize_audio`, `compute_score`
- **Every leaf node must declare an explicit `Verification Owner`** from one of the three categories below.

**Verification Owner categories (assign exactly one per leaf node):**

| Category | When to assign | What it means |
|---|---|---|
| `UF-local` | The UF's correctness is fully decidable in isolation | Owns a standalone functional test |
| `guard-rail + IF-chain` | The UF is a composition/assembly/merge node | Has guard-rail tests locally; behavioral validation lives in the parent IF-chain test |
| `IF-acceptance` | Correctness only emerges across the full IF span (e.g., end-to-end latency, determinism, schema stability) | No UF-local functional test required; acceptance is validated at IF level |

> **Do NOT default to `UF-local` for every leaf.** Composition-heavy nodes, packaging steps,
> and nodes whose output is only meaningful inside the chain belong to `guard-rail + IF-chain`
> or `IF-acceptance`. Forcing `UF-local` onto these creates false precision and document drift.

**For each IF, write:**
1. A dependency tree showing the subfunction hierarchy
2. For each leaf node (UF candidate): a mini I/O summary (input → output) **and the assigned Verification Owner**
3. Execution order annotation: sequential (→) or parallel (‖)

Use `assets/if_decomposition_template.md` as the structure.

**Output:** `if_decomposition.md`

---

### Phase C — REQ→IF Coverage Check

After writing both files, verify:
- Every REQ-### in `requirements.md` is linked to at least one IF
- Every IF is linked to at least one REQ (no orphan IFs)
- No two IFs have identical responsibilities

List any gaps explicitly as `[UNCOVERED: REQ-###]` or `[ORPHAN: IF-##]`.

---

### Phase D — Validation

Run the validation script:

```bash
python <skill_dir>/scripts/validate_if_design.py if_list.md if_decomposition.md
```

Fix any failures before handing off.

---

## Downstream Handoff

Once validation passes:

```
✅ Stages 5–6 complete. Output files:
  - if_list.md     (IF-01 ~ IF-N, with I/O contracts and linked REQs)
  - if_decomposition.md  (UF candidate tree per IF)

Next step → run /uf-designer with if_decomposition.md as input (Stage 7).
```

---

## Quality Checklist

- [ ] Every IF has an Input Contract and Output Contract with type + unit + range
- [ ] Every IF is linked to at least one REQ
- [ ] Every REQ is covered by at least one IF
- [ ] Leaf nodes in the decomposition tree are concrete enough to implement as single functions
- [ ] I/O chain is continuous: output of each node matches input of the next
- [ ] Failure modes are listed for each IF
- [ ] Every leaf node has an explicit `Verification Owner` declared (`UF-local` / `guard-rail+chain` / `IF-acceptance`)
- [ ] No leaf node is assigned `UF-local` solely by default — composition/assembly nodes use `guard-rail+chain` or `IF-acceptance`
