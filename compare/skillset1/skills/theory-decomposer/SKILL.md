---
name: theory-decomposer
description: >
  Reconstructs a domain theory's equations and dynamics when no (or partial) open-source
  reference exists: checks source availability first, then recursively decomposes the theory
  into atomic sub-theories using explicit stopping criteria, writes each as an EQ Block
  (UF Block superset with Equation, Assumptions, Validity Domain, Source), and gates the
  merge with unit/dimension/frame/assumption-compatibility and coupling-term coverage checks
  so the existing pipeline (uf-implementor → if-integrator) can implement and merge them
  into the original dynamics. Trigger when the user says "이론 분해해줘", "이론 쪼개줘",
  "수식 유도해줘", "수식 머지", "동역학 만들어줘", "동역학 유도", "지배방정식 도출",
  "theory decomposition", "derive dynamics", "equation merge", or wants to build a
  physics/domain model without a reference implementation. Also trigger when the user has
  a theory or phenomenon description and wants equation-level design artifacts
  (eq.md, theory_tree.md) before implementation.
user-invocable: true
allowed-tools: Read, Write, WebSearch, WebFetch
---

# Theory-Decomposer — Theory → EQ Blocks → Mergeable Dynamics

This skill is the **theory-level front-end** of the core-engineering pipeline.
It applies the same compositional principle the pipeline applies to software
(system → IF → UF → bottom-up integration) to **theories and equations**:

```
원래 이론  →  하위이론 반복 분해  →  최소 이론 단위(EQ Block)  →  연동 검사  →  머지  →  원래 동역학
(Theory)      (theory_tree.md)       (eq.md)                    (gate)      (기존 파이프라인 재사용)
```

Output artifacts are **format-compatible** with the existing pipeline:
- `eq.md` uses the UF Block syntax (superset) → consumed by `uf-implementor` as-is
- `theory_tree.md` uses the `if_decomposition.md` format → consumed by `if-integrator`

> **Read `references/reference.md`** for the EQ Block template, source survey template,
> assumption compatibility matrix, and coupling-term checklists.

Per GLOBAL_RULES Rule 9, all design artifacts produced by this skill go to `rd/`.

---

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `max_depth` | 4 | Maximum decomposition depth. Exceeding it emits `WARN: OVER-DECOMPOSED`. |
| `domain_hint` | none | Optional domain (dynamics / signal processing / thermal / optics / control …) to select coupling checklists. |

---

## Execution Flow

### T0 — Source Availability Check (entry gate, runs FIRST)

Before any decomposition, search for existing domain sources:

1. Open-source reference implementations (GitHub, PyPI, established simulators)
2. Benchmark numbers (papers, textbook worked examples, standard test cases)
3. Authoritative derivations (textbooks with equation numbers, survey papers)

Record everything in `rd/source_survey.md` (template in `references/reference.md`)
and issue exactly one verdict:

| Verdict | Meaning | Verification mode routed downstream |
|---|---|---|
| `FOUND-CODE` | Reference implementation exists | Reconstruction proceeds; reference becomes the **verification oracle** (cross-check in `eval-runner`) |
| `FOUND-BENCH` | Only benchmark numbers / paper values exist | Benchmarks registered as `eval-planner` metrics |
| `NONE` | No code, no benchmarks | **Full reconstruction mode**: oracle = conservation laws + limiting cases + dimensional analysis + symmetry |

> The verdict does NOT stop the pipeline — it decides **how the merged dynamics will be
> verified**. Even under `FOUND-CODE`, decomposition is still valuable (the reference
> validates the merge; the EQ Blocks document the theory).

**Output:** `rd/source_survey.md`

---

### T1 — Theory Definition

- State the theory in 1–3 sentences: governing phenomena, scope, what "the original
  dynamics" means concretely (state vector, inputs, outputs)
- Fix the global conventions once: state variables, units system (SI), coordinate
  frames and their names, notation table
- Record explicit modeling intent: what is IN scope (e.g., rigid body) and OUT
  (e.g., aeroelasticity)

**Output:** `rd/theory_statement.md`

---

### T2 — Recursive Decomposition with Stopping Criteria

Decompose the theory into sub-theories, then sub-sub-theories, recursively.
At **every node**, apply the four stopping criteria:

| # | Stop criterion (node is ATOMIC when ALL hold) | Rationale |
|---|---|---|
| S1 | Expressible as a single equation (or one closed-form coupled set) | SRP analog — 1 EQ Block = 1 equation |
| S2 | Directly citable from ONE source (textbook eq. number / paper) | Splitting further loses the citation → hallucination risk |
| S3 | Independently checkable (dimensional analysis + at least one limiting case) | Testability analog of Stage 6 |
| S4 | Further splitting separates NO new assumption | Decomposition exists to isolate assumptions; no new assumption = no gain |

- Record the stop verdict per leaf: `ATOMIC (S1–S4 ✓)` or keep splitting
- Depth guard: if depth > `max_depth`, emit `WARN: OVER-DECOMPOSED at <node>` and
  justify or re-merge
- Write the tree in **`if_decomposition.md` format** (nodes = sub-theories,
  leaves = EQ candidates, edges = coupling variables)

**Output:** `rd/theory_tree.md`

---

### T3 — EQ Block Authoring

For each ATOMIC leaf, write one **EQ Block** in `rd/eq.md`.
EQ Block = UF Block **superset** — same block syntax plus 4 fields:

```
- EQ-ID: EQ-##-##            (parent-theory prefix, like UF-IDs)
- Parent Theory: TH-##
- Goal: (single phenomenon, single sentence)
- Equation: (LaTeX or ASCII math — the actual formula)
- I/O Contract:
    Input:  <var>: <type>, <unit>, <frame>, <range>
    Output: <var>: <type>, <unit>, <frame>, <range>
- Assumptions: (rigid body, small-angle, incompressible, linear region, …)
- Validity Domain: (numeric ranges where the equation holds)
- Source: (textbook + eq. number, or paper + DOI — REQUIRED, no exceptions)
- Edge Cases / Singularities: (division by zero, gimbal lock, resonance, …)
- Verification Plan: (dimensional check + limiting case(s) + oracle per T0 verdict)
```

**Critical rules:**
- **No equation without a Source.** An EQ Block with an uncited equation is invalid (S2).
- Units and frames are part of the contract, not comments.
- The same physical variable must carry the same symbol, unit, and frame across all blocks.

**Output:** `rd/eq.md` (+ optional `rd/eq_split/` per parent theory, mirroring `uf_split/`)

---

### T3.5 — Linkage & Coverage Gate (merge readiness)

Four checks before anything is implemented or merged:

1. **Chain continuity** — for every edge in `theory_tree.md`: output var of EQ-A matches
   input var of EQ-B in symbol, type, **unit, dimension, and frame**.
   Mismatch → `[CHAIN BREAK: EQ-XX → EQ-YY: <what differs>]`
   (frame mismatch is fixable: insert an explicit transform EQ Block, e.g., rotation matrix)
2. **Assumption compatibility matrix** — pairwise over EQ Blocks that will be merged.
   Contradictory assumptions (rigid vs. flexible, incompressible vs. compressible)
   → `INCOMPATIBLE` flag; merging is forbidden until a bridging model is added or scope is narrowed.
3. **Coupling-term coverage** — bottom-up merge can miss cross terms that exist in no
   sub-theory (Coriolis, gyroscopic ω×Jω, multi-physics coupling). Run the domain
   coupling checklist (conservation laws, limiting-case reductions, symmetry) from
   `references/reference.md`. Any known behavior of the original theory not produced
   by the merged set → `UNCOVERED` → add the missing coupling EQ Block.
4. **Validity intersection** — the merged model's validity domain = intersection of all
   EQ validity domains. Empty or impractically narrow intersection → `WARN` + report.

**Output:** `rd/eq_coverage_review.md` (matrix: theory nodes × EQ Blocks,
PASS / UNCOVERED / INCOMPATIBLE / CHAIN BREAK)

**Gate rule (mirrors Stage 7.5):** downstream implementation may start only when the
review shows no `UNCOVERED` and no `INCOMPATIBLE`.

---

## Downstream Handoff

```
✅ theory-decomposer complete.
  rd/source_survey.md        (T0 verdict: FOUND-CODE | FOUND-BENCH | NONE)
  rd/theory_statement.md
  rd/theory_tree.md          (if_decomposition.md-compatible)
  rd/eq.md                   (uf.md-compatible EQ Blocks)
  rd/eq_coverage_review.md   (gate passed)

Next steps:
  A. Implement equations   → /uf-implementor with rd/eq.md   (1 EQ Block → 1 function)
  B. Merge into dynamics   → /if-integrator with rd/theory_tree.md + src/uf/
  C. Physics audit         → /sim-physics-auditor  (units, frames, stability)
  D. Numeric verification  → /eval-planner → /eval-runner
                             (oracle per T0 verdict: reference code / benchmarks /
                              conservation laws + limiting cases)
```

---

## Rules

1. T0 runs first, always. The verdict routes verification — skipping it silently is forbidden.
2. Every EQ Block cites a Source. No source, no block (S2).
3. Never merge across an `INCOMPATIBLE` assumption pair without an explicit bridging EQ Block.
4. Frame conversions are explicit EQ Blocks, never implicit.
5. Token economy: keep full derivations in referenced files; blocks carry only the final equation.
6. All claims about the merged dynamics need evidence artifacts (checks, plots, oracle comparisons).

---

## Quality Checklist

- [ ] `source_survey.md` exists with exactly one verdict and search evidence (queries, links, dates)
- [ ] Notation/frame/unit conventions fixed once in `theory_statement.md`
- [ ] Every leaf in `theory_tree.md` has an S1–S4 stop verdict; depth ≤ `max_depth` or justified
- [ ] Every EQ Block has Equation + Assumptions + Validity Domain + Source (no exceptions)
- [ ] Same physical variable = same symbol/unit/frame across all EQ Blocks
- [ ] Coverage review has no `UNCOVERED` / `INCOMPATIBLE` before handoff
- [ ] Coupling checklist (conservation, limiting cases, symmetry) executed and recorded
- [ ] Verification oracle matches the T0 verdict

---

## Bundled Resources

| Resource | When to use |
|---|---|
| `references/reference.md` | EQ Block template, source survey template, assumption matrix, coupling checklists, output formats |
| `references/examples.md` | Example prompts and abbreviated expected outputs |
| `references/README_kr.md` | 한국어 사용 가이드 |
