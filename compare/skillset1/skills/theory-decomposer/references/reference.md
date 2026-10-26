# theory-decomposer — Reference

Templates and lookup tables. Copy → fill. Do not paste full derivations into blocks;
store them as separate files and reference the path.

---

## 1. Source Survey Template (`rd/source_survey.md`)

```markdown
# Source Survey — <theory name>
Date: <YYYY-MM-DD>
Searched: <queries used, per source type>

## Open-Source Implementations
| Candidate | Link | Coverage of our scope | License | Usable as oracle? |
|---|---|---|---|---|
| <repo> | <url> | full / partial / none | <license> | yes / no + why |

## Benchmarks / Published Values
| Source | What it provides | Values usable as eval metrics |
|---|---|---|
| <paper/textbook> | <test case, tolerance> | <metric, threshold> |

## Authoritative Derivations
| Source | Equations covered | Citation format for EQ Blocks |
|---|---|---|
| <textbook> | <chapters/eq numbers> | <Author, Title, ed., Eq. (x.y)> |

## Verdict (exactly one)
**FOUND-CODE | FOUND-BENCH | NONE**

판단 근거: <why this verdict; what was searched and not found>

## Routed Verification Mode
- FOUND-CODE  → eval-runner cross-checks merged dynamics against <reference> on <scenarios>
- FOUND-BENCH → eval-planner registers: <metric ↔ published value ± tolerance>
- NONE        → oracle set: conservation laws + limiting cases + dimensional + symmetry (see §5)
```

---

## 1.5 Theory Statement Template (`rd/theory_statement.md`)

```markdown
# Theory Statement — <theory name>
- Governing phenomena: <1–3 sentences>
- Original dynamics (target of reconstruction): state vector x = <...>, inputs u = <...>, outputs y = <...>
- Scope IN: <e.g., rigid body, SI units>   /  Scope OUT: <e.g., aeroelasticity>
- Frames: <name: definition, e.g., inertial NED / body FRD>
- Notation table: | symbol | meaning | unit | frame |
```

---

## 2. EQ Block Template (superset of UF Block — `rd/eq.md`)

```markdown
- EQ-ID: EQ-01-01
- Parent Theory: TH-01 (<sub-theory name>)
- Goal: <single phenomenon, single sentence, starts with a verb>
- Equation:
    <LaTeX or ASCII, final form only. Derivation → derivations/<EQ-ID>.md>
- I/O Contract:
    Input:  <var>: <type>, <unit>, <frame>, <range>
    Input:  <param>: <type>, <unit>, — , <range>          # constants: frame = —
    Output: <var>: <type>, <unit>, <frame>, <range>
- Assumptions:
    - A1: <e.g., rigid body>
    - A2: <e.g., constant mass>
- Validity Domain: <numeric ranges, e.g., |α| < 10°, Re < 2300>
- Source: <Author, Title, ed., Eq. (x.y)> or <paper, DOI, Eq. (n)>   # REQUIRED
- Edge Cases / Singularities:
    - <θ = ±90° gimbal lock → behavior>
    - <denominator → 0 when ... → behavior>
- Verification Plan:
    Dimensional: <LHS dims = RHS dims, shown once>
    Limiting cases: <e.g., ω→0 reduces to Eq. X; drag→0 gives free fall>
    Oracle (per T0): <reference sim scenario / benchmark value / conservation check>
- Evidence Pack Fields: scenario_id, run_id, metrics, environment, commit_sha
```

**uf-implementor compatibility:** `Goal`, `I/O Contract`, `Edge Cases`, `Verification Plan`
match the UF Block fields 1:1. The extra fields (`Equation`, `Assumptions`,
`Validity Domain`, `Source`) become the implementation's docstring + runtime guard
(validity-domain check) + citation comment.

---

## 3. Theory Tree Format (`rd/theory_tree.md`, if_decomposition.md-compatible)

```markdown
# Theory Decomposition — <theory name>
max_depth: 4

TH-00 <original theory>                          [state vector: x = ...]
├── TH-01 <sub-theory>                           [couples to TH-02 via: <var, unit, frame>]
│   ├── EQ-01-01 <leaf>    ATOMIC (S1✓ S2✓ S3✓ S4✓)
│   └── EQ-01-02 <leaf>    ATOMIC (S1✓ S2✓ S3✓ S4✓)
├── TH-02 <sub-theory>
│   └── EQ-02-01 <leaf>    ATOMIC (S1✓ S2✓ S3✓ S4✓)
└── EQ-00-01 <coupling block added by T3.5>      ATOMIC — origin: UNCOVERED fix

## Coupling Edges (data flow for merge — if-integrator reads this)
| From | To | Variable | Unit | Frame | Transform needed? |
|---|---|---|---|---|---|
| EQ-01-01 | EQ-02-01 | <var> | <unit> | body→inertial | yes: EQ-00-02 (rotation) |

## Stop Verdicts Log
| Node | S1 | S2 | S3 | S4 | Verdict | Note |
|---|---|---|---|---|---|---|
| TH-01 | ✗ | — | — | — | SPLIT | two distinct phenomena |
| EQ-01-01 | ✓ | ✓ | ✓ | ✓ | ATOMIC | — |
```

---

## 4. Assumption Compatibility Matrix (part of `rd/eq_coverage_review.md`)

```markdown
## Assumption Compatibility (pairwise, merged blocks only)
| | EQ-01-01 | EQ-01-02 | EQ-02-01 |
|---|---|---|---|
| EQ-01-01 | — | OK | OK |
| EQ-01-02 | | — | INCOMPATIBLE: A2(rigid) vs A1(flexible) |
| EQ-02-01 | | | — |

INCOMPATIBLE resolution options (pick one, record 판단 근거):
1. Narrow scope (drop one assumption's block, shrink validity domain)
2. Add bridging EQ Block (e.g., flexible-mode correction term with its own Source)
3. Split the merged model into two validity regimes
```

Common contradiction pairs to scan for:
rigid↔flexible · incompressible↔compressible · inviscid↔viscous ·
small-angle↔large-angle · point-mass↔distributed-mass · linear↔saturating ·
quasi-static↔transient · lumped↔distributed(PDE) · isothermal↔adiabatic

---

## 5. Coupling-Term Coverage Checklist (T3.5 check 3)

Bottom-up merge misses terms that live "between" sub-theories. Check by domain:

**Universal (always run):**
- [ ] Dimensional analysis of the merged equation set (every additive term, same dims)
- [ ] Conservation: energy / momentum / angular momentum / mass / charge —
      does the merged set conserve what the original theory conserves (or dissipate correctly)?
- [ ] Limiting cases: set each sub-theory's effect → 0; does the rest reduce to a known result?
- [ ] Symmetry: invariances of the original theory (translation, rotation, time) preserved?

**Mechanics / dynamics (`domain_hint: dynamics`):**
- [ ] Rotating frame terms: Coriolis −2m(ω×v), centrifugal −m(ω×(ω×r)), Euler −m(ω̇×r)
- [ ] Gyroscopic coupling: ω × Jω in Euler's equations
- [ ] Frame mixing: translation in inertial frame vs. rotation in body frame → rotation matrix R blocks

**Control / signal (`domain_hint: control|signal`):**
- [ ] Loop coupling: closed-loop poles ≠ union of open-loop poles — check merged characteristic equation
- [ ] Sampling: merged discrete model respects Nyquist for the fastest sub-dynamics
- [ ] Impedance/loading: connecting two-port models changes both (no naive cascade)

**Multi-physics (`domain_hint: thermal|fluid|em`):**
- [ ] Two-way coupling terms (e.g., temperature→viscosity→dissipation→temperature)
- [ ] Shared-boundary conditions consistent across sub-models

Every finding → `UNCOVERED` row in the coverage matrix + a new coupling EQ Block
(EQ-00-xx, with its own Source).

---

## 6. Coverage Review Template (`rd/eq_coverage_review.md`)

```markdown
# EQ Coverage Review — <theory name>
Date: <date>   Gate: <PASS | BLOCKED>

## 1. Chain Continuity
| Edge | Symbol | Type | Unit | Dim | Frame | Status |
|---|---|---|---|---|---|---|
| EQ-01-01→EQ-02-01 | v | vec3 | m/s | LT⁻¹ | body | PASS |
| EQ-01-02→EQ-02-01 | F | vec3 | N | MLT⁻² | inertial vs body | CHAIN BREAK → add EQ-00-02 (R) |

## 2. Assumption Compatibility  → §4 matrix

## 3. Coupling Coverage
| Known behavior of original theory | Produced by merged set? | Status | Fix |
|---|---|---|---|
| <gyroscopic precession under yaw+pitch> | no | UNCOVERED | add EQ-00-03: ω×Jω |
| <energy conservation, no damping> | yes | PASS | — |

## 4. Validity Intersection
Merged validity domain: <intersection>   → <OK | WARN: narrow>

## Gate Decision
<PASS: proceed to uf-implementor | BLOCKED: resolve rows above>
판단 근거: <...>
```

---

## 7. Downstream Consumption Map

| Artifact | Consumed by | As |
|---|---|---|
| `rd/eq.md` | `uf-implementor` | uf.md (1 EQ Block → 1 function + validity-domain guard + unit test from Verification Plan) |
| `rd/theory_tree.md` | `if-integrator` | if_decomposition.md (coupling edges = call graph) |
| `rd/eq_coverage_review.md` | `uf-implementor` gate | uf_if_coverage_review.md analog |
| `rd/source_survey.md` | `eval-planner` / `eval-runner` | oracle & metric definitions |
| EQ `Assumptions`+`Validity Domain` | `sim-physics-auditor` | audit inputs (equations, assumptions, parameter ranges) |
