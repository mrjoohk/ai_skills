# Req-Critic Checklist — Lens-by-Lens Criteria

This document expands the five review lenses in `SKILL.md` into concrete checklists and
severity assignments. Use it as a per-REQ walkthrough, not as reading material.

---

## Lens 1 — Testability

Apply to every REQ Block. A REQ fails this lens if a test engineer cannot write the
acceptance test from the REQ text alone.

### 1.1 Given Reproducibility

- [ ] Required input data is named and available (dataset path, fixture, or generation procedure specified).
- [ ] Environmental preconditions are stated (hardware, OS, software versions, or "any" if truly hardware-agnostic).
- [ ] Concurrency/load context is specified if relevant (e.g., "under 100 concurrent users").
- [ ] Initial state of the system is defined (cold start? warm cache? fresh DB?).

**Fail → WARN** (if 1 field missing) or **CRITICAL** (if multiple fields missing on a functional REQ).

### 1.2 When Concreteness

- [ ] "When" clause names a concrete operation (API call, user action, system event).
- [ ] Operation arguments/parameters are specified or bound.
- [ ] No states disguised as actions ("When the system is running" fails; "When `process()` is invoked" passes).

**Fail → WARN**.

### 1.3 Then Measurability

- [ ] Named metric or observable (latency, PESQ, error rate, memory residency).
- [ ] Measurement instrument/tool is named or implied by the metric's standard definition.
- [ ] Numeric threshold present with unit (ms, dB, %, MB).
- [ ] Comparison operator present (`≤`, `≥`, `=`, `∈ [a, b]`).
- [ ] Statistical qualifier if noisy (percentile, mean, p-value threshold, sample size).

**Fail → CRITICAL** if threshold or unit missing; **WARN** if statistical qualifier missing on noisy metrics.

### 1.4 Instrument Feasibility

- [ ] The named instrument/tool is available in the project stack (no "we need to invent a tool to measure this").
- [ ] The measurement can be automated (manual inspection is not testable in CI).

**Fail → WARN**; **CRITICAL** if CI gating is claimed.

---

## Lens 2 — Realism (Baseline / Target / Stretch)

For every numeric threshold, cross-check against domain baselines.

### 2.1 Baseline Reference Tables

Use these as first-pass comparisons. If the REQ's domain is not listed, require the producer to supply domain references before judging.

#### ML / Deep Learning

| Task | Metric | Typical Baseline | SoA (2024) | Unit |
|---|---|---|---|---|
| ImageNet classification | Top-1 accuracy | 76% (ResNet-50) | ≈ 91% | % |
| COCO object detection | mAP@0.5 | 40–50% | ≈ 65% | % |
| GLUE (NLP) | avg score | 70–80 | ≈ 90 | — |
| BLEU (translation) | BLEU | 25–30 | 35–45 | — |

#### Audio / Speech

| Task | Metric | Baseline | SoA | Unit |
|---|---|---|---|---|
| Speech separation (WSJ0-2mix) | SI-SDRi | 8.9 | 16+ | dB |
| Speech enhancement (DNS) | PESQ | 2.0 | 3.3+ | MOS |
| ASR (LibriSpeech clean) | WER | 10% | < 2% | % |
| STOI | STOI | 0.75 | 0.93+ | — |

#### Computer Vision

| Task | Metric | Baseline | SoA | Unit |
|---|---|---|---|---|
| Semantic segmentation (Cityscapes) | mIoU | 65% | 85%+ | % |
| Depth estimation (KITTI) | abs rel err | 0.12 | 0.045 | — |

#### Distributed / Systems

| Property | Baseline | Tight | Unit |
|---|---|---|---|
| API p95 latency (internal) | 150 | 30 | ms |
| API p99 latency (external) | 500 | 100 | ms |
| DB query p50 | 20 | 2 | ms |
| Queue throughput (single node) | 10k | 100k+ | msg/s |

#### Embedded / Real-Time

| Property | Baseline | Tight | Unit |
|---|---|---|---|
| Control loop period | 10 | 1 | ms |
| ADC sampling | 1 | 100 | kHz |
| Task jitter | 1 | 0.1 | ms |

### 2.2 Realism Rules

- [ ] Every numeric threshold is cited (source named) OR falls within a baseline-table range.
- [ ] Target < Baseline (easier than baseline): **WARN: no challenge**.
- [ ] Target ≈ Baseline (within 10%): **WARN: no design pressure**.
- [ ] Target between Baseline and SoA: acceptable.
- [ ] Target > SoA without justification: **WARN: aspirational, cite method**.
- [ ] Target > 2× SoA: **CRITICAL: unrealistic without novel method claim**.

### 2.3 Stretch vs Target

- [ ] Stretch is strictly harder than Target (otherwise it's redundant).
- [ ] Stretch is plausible within the stated timeline (assumptions_and_constraints.md).
- [ ] Stretch does not silently become the Target through mission creep — flag if Stretch appears as gating criterion anywhere.

---

## Lens 3 — Cross-REQ Conflict

Produce a pairwise matrix. For N REQs, this is N*(N-1)/2 pairs. For N > 20, check only pairs sharing at least one referenced subsystem, metric, or interface.

### 3.1 Conflict Types

| Type | Example | Severity |
|---|---|---|
| **Hard incompatibility** | REQ-A: "p99 ≤ 10 ms under 10k QPS" ∧ REQ-B: "single-thread execution only" | CRITICAL |
| **Soft tension** | REQ-A latency target ∧ REQ-B quality target on the same pipeline | WARN |
| **Ordering gap** | REQ-A consumes output of REQ-B but REQ-B does not specify producing it | WARN |
| **Resource over-commit** | sum of memory budgets exceeds platform constraint in assumptions_and_constraints.md | CRITICAL |
| **Unit mismatch** | REQ-A produces "meters" but REQ-B consumes "millimeters" (implicit conversion) | WARN |

### 3.2 Matrix Format

```
| REQ \ REQ | REQ-001 | REQ-002 | REQ-003 | ...
| REQ-001   |    —    | OK      | TENSION:perf-quality |
| REQ-002   |         | —       | OK      |
| REQ-003   |         |         | —       |
```

Record only cells with non-OK annotations in the findings.

---

## Lens 4 — NFR Coverage

### 4.1 Minimum NFR Categories

Every project requires coverage in these categories. Count one REQ per category minimum.

- [ ] **Performance** — latency, throughput, resource bound, or SLA
- [ ] **Reliability** — failure mode, recovery, uptime, or MTTR
- [ ] **Security** — authN, authZ, encryption, data protection, or supply-chain
- [ ] **Observability** — logging, metrics, tracing, or health checks
- [ ] **Maintainability** — test coverage target, CI gate, or documentation standard

**Missing category → WARN** per gap.
**Missing 2+ categories → CRITICAL** (indicates the REQ set is incomplete).

### 4.2 Domain-Specific NFRs

Enable these based on `problem_statement.md` or `assumptions_and_constraints.md` domain tags:

| Domain | Additional NFRs |
|---|---|
| Embedded / real-time | deadline determinism, jitter, hard-real-time vs soft-real-time declared |
| ML / production inference | model versioning, dataset provenance, drift detection |
| Regulated (health, finance) | audit trail, data residency, consent management, compliance citation |
| Multi-tenant SaaS | isolation boundary, rate-limit policy, noisy-neighbor handling |
| Safety-critical | hazard analysis reference, fail-safe behavior, redundancy policy |

Domain NFR missing → same severity as Lens 4.1.

---

## Lens 5 — I/O Contract Precision

For every REQ that declares Inputs or Outputs:

### 5.1 Mandatory Fields

- [ ] **Type** (e.g., `float32`, `str`, `UserRecord`, `ndarray`, `bytes`)
- [ ] **Unit/Shape** (e.g., `seconds`, `(N, 3)` for tensor, `UTF-8` encoding, `ISO8601 UTC`)
- [ ] **Range** (numeric: min/max; string: regex or length bound; structured: schema ref)

Missing any one: **WARN: imprecise I/O**.

### 5.2 Conditional Fields

Apply when the input/output has the relevant semantics:

| Condition | Required extra field |
|---|---|
| Spatial data | coordinate system (pixel / normalized / world / map) |
| Temporal data | timezone/epoch convention (UTC / ISO8601 / seconds-since-epoch) |
| Textual data | encoding (UTF-8 / ASCII / Latin-1) |
| Floating-point | tolerance/precision or explicit "exact" |
| Binary data | endianness, alignment |
| User-supplied | sanitization/validation rule |

Missing conditional field where required: **WARN**.

### 5.3 Cross-REQ I/O Chain

- [ ] If REQ-A output feeds REQ-B input, the type+unit+shape must match exactly.
- [ ] Implicit conversions (int32 → int64, meters → millimeters) are **WARN: implicit conversion**; explicit conversion is fine.

---

## Severity Assignment Summary

| Finding type | Base severity | Escalate to CRITICAL when |
|---|---|---|
| Testability: threshold missing | CRITICAL | (always) |
| Testability: instrument infeasible | WARN | CI gating claimed |
| Realism: unsourced threshold | SUGGEST | used in gating criterion |
| Realism: target > 2× SoA | CRITICAL | (always) |
| Realism: target ≤ baseline | WARN | (stays WARN) |
| Conflict: hard incompatibility | CRITICAL | (always) |
| Conflict: soft tension | WARN | on Primary-metric-bearing REQ |
| NFR gap | WARN | 2+ categories missing |
| I/O imprecision | WARN | on REQ at IF-level boundary |
| I/O implicit conversion | WARN | (stays WARN) |

---

## Verdict Computation (reference only — source of truth is SKILL.md §Verdict Rules)

```
critical_count = count(findings where severity == CRITICAL)
warn_count     = count(findings where severity == WARN)
nfr_gap        = any NFR category missing

if critical_count >= 1:            verdict = BLOCK
elif warn_count >= 2:              verdict = REQUEST_CHANGES
elif warn_count == 1 and nfr_gap:  verdict = REQUEST_CHANGES
else:                              verdict = APPROVE
```
