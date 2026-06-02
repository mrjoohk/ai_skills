# UF Critique-Mode Criteria (Lenses C-1 through C-4)

This document expands the four critique-mode review lenses from `SKILL.md` into concrete
checklists, domain reference tables, and severity assignments. Use as a per-UF walkthrough.

> **Scope:** This file applies only to `mode: critique`. For mechanical checks see
> `reference.md` (legacy format). For the binding independence/verdict rules, see
> `../_shared/critic_contract.md`.

---

## Lens C-1 — Algorithm Appropriateness

Every UF Block names an algorithm (or describes one in the "Algorithm Summary" field).
This lens asks: is the named algorithm the right tool for the task?

### C-1.1 Algorithm Named

- [ ] `Algorithm Summary` names a concrete algorithm or pattern (not "process the input").
- [ ] The named algorithm is standard/recognizable OR the description is specific enough
      to identify it (e.g., "Viterbi decoding with log-probability accumulation").
- [ ] If novel, the summary cites its origin or inspiration (paper, prior work, repo).

**Fail → WARN** (unnamed algorithm); **CRITICAL** if the UF is Primary-metric-bearing.

### C-1.2 Alternatives Considered

The critic must generate (not accept) ≥ 2 alternative algorithms for the task and state
the trade-off axis. Reference sources:

| Task family | Common alternatives |
|---|---|
| Image resize | bilinear / bicubic / nearest / Lanczos / letterbox + pad |
| Audio resampling | sinc (windowed) / polyphase / spline / linear |
| Speech separation | DPRNN / ConvTasNet / SepFormer / permutation-invariant training |
| Classification head | softmax / sigmoid (multi-label) / ArcFace / margin-loss |
| Sequence decoding | greedy / beam search / Viterbi / sampling (top-k, top-p) |
| Normalization | z-score / min-max / per-channel / LayerNorm / BatchNorm |
| Gradient optimization | SGD / Adam / AdamW / Lion |
| Anomaly detection | isolation forest / autoencoder / OC-SVM / statistical thresholds |

If the task is not in this table, the critic must produce its own alternatives from general
knowledge and flag the reference gap.

### C-1.3 Known Failure Modes Addressed

- [ ] Known failure modes of the chosen algorithm are **listed in Edge Cases** OR
      **mitigated in Algorithm Summary**.
- [ ] Example mappings:
  - Letterbox resize → padding-fill value mismatch with training distribution
  - Beam search → premature pruning with ambiguous tokens
  - BatchNorm → small-batch instability
  - Adam → non-convergence on noisy gradients
  - Sinc resampling → ringing at sharp transitions

**Fail → WARN** (known failure not addressed); **CRITICAL** when the failure mode is common and the UF is production-bound.

### C-1.4 Defensibility Under Constraints

Cross-reference `requirements.md` (if provided) and `if_list.md`:
- [ ] The algorithm satisfies the parent IF's performance/memory constraints.
- [ ] The algorithm is compatible with the deployment target (CPU / GPU / embedded / browser).
- [ ] Licensing compatibility if open-source (e.g., GPL-contaminated algorithm in a BSD codebase).

---

## Lens C-2 — Edge-Case Representativeness

The UF Block's `Edge Cases` field lists ≥ 3 cases. This lens asks: are those cases **the
most likely failures**, or just the easy-to-write ones?

### C-2.1 Universal Edge-Case Floor

Every UF must consider (listed or justified-absent):

- [ ] **Empty input** (zero-length array, None, empty string)
- [ ] **Oversized input** (exceeds memory or time budget)
- [ ] **Malformed input** (wrong type, invalid encoding, corrupted record)
- [ ] **Shape/type mismatch with predecessor UF** (static check + runtime guard)

Missing any → WARN. Missing all → CRITICAL.

### C-2.2 Numeric UFs

When the UF operates on numeric data:

- [ ] **NaN handling** declared (propagate / reject / replace with default)
- [ ] **Infinity handling** declared (positive and negative)
- [ ] **Overflow/underflow** considered (especially for int8, float16 downcasts)
- [ ] **Zero-division / log-of-zero** guarded
- [ ] **Precision loss** declared if mixed precision

Missing any when applicable → WARN.

### C-2.3 Temporal UFs

When the UF operates on time-series or timestamps:

- [ ] **Out-of-order events** handled
- [ ] **Timezone / DST** handled (especially across boundaries)
- [ ] **Clock skew** considered if distributed
- [ ] **Sample-rate mismatch** declared

### C-2.4 Spatial UFs

When the UF operates on images/tensors/maps:

- [ ] **Aspect ratio extremes** (very wide, very tall) handled
- [ ] **Channel count variations** (RGB vs RGBA vs grayscale)
- [ ] **Coordinate origin convention** declared (top-left vs bottom-left)

### C-2.5 Stateful / Concurrent UFs

When the UF is reentrant or holds state:

- [ ] **Concurrent invocation** safe or serialized explicitly
- [ ] **State reset** procedure declared
- [ ] **Partial-failure recovery** declared

### C-2.6 Representativeness Score

Score the UF's Edge Cases list:

| Score | Criterion |
|---|---|
| `has_all`         | Universal floor + domain-specific all present |
| `has_most`        | Universal floor + ≥ 50% domain-specific |
| `has_only_easy`   | Only universal floor or superficial cases |
| `absent`          | Fewer than 3 cases, or placeholders |

- `has_all`: no finding.
- `has_most`: **SUGGEST**.
- `has_only_easy`: **WARN** (representativeness gap).
- `absent`: **CRITICAL**.

---

## Lens C-3 — I/O Contract Precision (Critique Perspective)

Mechanical mode checks field presence. Critique mode checks semantic correctness.

### C-3.1 Type + Unit + Shape + Range

- [ ] Types are concrete (`float32(N, 85)` not `tensor`; `UserRecord` not `object`).
- [ ] Units are declared where applicable (ms, dB, pixels, normalized [0, 1]).
- [ ] Shape is symbolic with named dimensions (`(B, C, H, W)` with `B` = batch etc.).
- [ ] Range is declared (`[0, 1]` for normalized, `[0, 255]` for uint8, `[-∞, +∞]` for unconstrained).

**Fail → WARN** per missing field.

### C-3.2 Coordinate / Frame / Encoding Declarations

Where applicable:

- [ ] **Coordinate system** for spatial data (pixel / normalized / world / image / camera).
- [ ] **Time epoch** for timestamps (UTC / local / monotonic).
- [ ] **String encoding** for text (UTF-8 / ASCII / latin-1).
- [ ] **Endianness / alignment** for binary blobs.

Missing when applicable → WARN.

### C-3.3 Parent-IF Contract Matching

Cross-check each leaf UF against `if_list.md`:

- [ ] The UF's output type matches or is convertible to the parent IF's expected output.
- [ ] The convertibility, if non-identity, is explicit in the Algorithm Summary.
- [ ] No silent reshaping (e.g., `(N, 85)` → `(N, 80)` by dropping columns) is hidden inside the UF.

**Fail → CRITICAL** (contract mismatch).

### C-3.4 Inter-UF Chain Continuity (Critique Perspective)

Mechanical mode checks type equality. Critique mode also checks:

- [ ] Value-range compatibility (UF-N outputs [0, 255]; UF-M expects [0, 1] — must be normalized).
- [ ] Unit compatibility (UF-N outputs meters; UF-M expects pixels — needs camera matrix).
- [ ] Precision compatibility (UF-N outputs float64; UF-M expects float32 — implicit downcast).

Implicit conversion → WARN. Silent precision loss on Primary-metric path → CRITICAL.

---

## Lens C-4 — Verification Plan Realism

The UF Block's `Verification Plan` field names test function paths and coverage targets.
This lens asks: can the plan actually be executed in this repo?

### C-4.1 Test Path Plausibility

- [ ] Named test path follows a recognizable pattern (`tests/unit/test_<uf_id>.py::test_<scenario>`).
- [ ] Path is unique (no two UFs declaring the same test file without distinguishing scenarios).
- [ ] Naming matches repo convention if inferable from `if_list.md` or `requirements.md`.

### C-4.2 Fixture Buildability

For each named fixture:
- [ ] Fixture is either (a) a standard public dataset, (b) a generatable synthetic, or (c) a repo-internal file with a declared source.
- [ ] If generatable, the generation procedure is specified or inferable.
- [ ] If external, the dataset is accessible under project licensing constraints.

**Unbuildable fixture → CRITICAL**. Ambiguous buildability → WARN.

### C-4.3 Coverage Target Justification

Default coverage goal is `>= 90%`. Flag when:

- [ ] Target stated as `>= 90%` with no justification and the UF has trivial logic → SUGGEST (inflated target).
- [ ] Target stated as `< 90%` with no justification → WARN (weak gate).
- [ ] Target > 95% on a UF with complex branching → SUGGEST (may be unachievable; justification needed).

### C-4.4 Performance / Resource Benchmarks

If the UF is on a performance-critical path (declared in parent IF constraints or
`requirements.md` NFRs):

- [ ] At least one benchmark is named (e.g., "latency ≤ 5 ms per call at batch=1").
- [ ] Benchmark tooling is specified (pytest-benchmark, custom harness, external profiler).
- [ ] Benchmark fixture distinct from correctness fixture.

**Missing benchmark on perf-critical path → WARN**. No benchmark path on Primary-metric-bearing UF → CRITICAL.

### C-4.5 Negative Tests

- [ ] Verification Plan includes at least one negative test per declared edge case
      (not just positive tests).
- [ ] Negative tests use `pytest.raises` (or equivalent) or assert error messages.

Missing negative tests → WARN.

---

## Verdict Computation (reference only — source of truth is SKILL.md §Phase E)

```
critical_count = count(findings where severity == CRITICAL)
warn_count     = count(findings where severity == WARN)

# Per-IF scope (if fanout active)
no_edge_cases_at_all      = any UF in scope with < 3 edge cases
unresolved_type_mismatch  = any UF output type != parent IF input without explicit conversion
forbidden_exposure        = if_decomposition.md or producer handoff was read

if forbidden_exposure:                                 verdict = BLOCK
elif missing_required_input:                           verdict = BLOCK
elif critical_count >= 1:                              verdict = BLOCK
elif no_edge_cases_at_all:                             verdict = BLOCK
elif unresolved_type_mismatch:                         verdict = BLOCK
elif warn_count >= 2:                                  verdict = REQUEST_CHANGES
elif warn_count == 1 and lens_c1_algorithm_unjustified:verdict = REQUEST_CHANGES
else:                                                  verdict = APPROVE
```

---

## Domain Reference Gaps

The reference tables in §C-1.2 are not exhaustive. When the UF's task family is not listed,
the critic must:

1. Generate alternatives from general knowledge.
2. Explicitly flag the reference-gap in the report's "Known Limits" section.
3. Record the unfamiliar task family so that future revisions of this criteria file can include it.

This is not a finding against the producer — it's a note for the skill maintainers.
