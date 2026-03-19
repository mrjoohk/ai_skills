# Skill Combination Usage Guide

Skills are most powerful when **chained in sequence** — the output artifacts of one skill become the input of the next.
This guide describes the main combined workflows and the exact slash command sequence for each.

---

## Quick Reference: Skill Chain Map

```
                        ┌─────────────────────────────────────────────────┐
                        │            core-engineering                     │
                        │  (8-stage design process: problem → UF blocks)  │
                        └──────────────────────┬──────────────────────────┘
                                               │
              ┌─────────────────┬──────────────┴──────────────┬──────────────────────┐
              ▼                 ▼                             ▼                      ▼
       agent-orchestration  eval-planner              uf-chain-validator      gpu-hpc-guard
              │                 │                             │               sim-physics-auditor
              ▼                 │                             │               rag-data-quality
       agent-executor           │                             │
                                │                    uf-if-debug-mapper
                                │                             │
                                │              ┌──────────────┘
                                │              ▼
                                │        uf-implementor
                                │              │
                                │              ▼
                                │         if-integrator
                                │              │
                                └──────────────┤
                                               ▼
                                          eval-runner
                                               │
                                               ▼
                                    ci-evidence-automation
```

---

## Workflow A — Full Design-to-Code Pipeline (from scratch)

**Scenario:** No design documents exist. Starting from a problem statement and going all the way to verified, tested code.

**Skills used:** `core-engineering` → `eval-planner` → `uf-implementor` → `if-integrator` → `eval-runner` → `ci-evidence-automation`

### Step 1 — Design (core-engineering)
```
/core-engineering
Define the following problem and produce all design documents through Stage 7.5:

Problem: [문제 설명]

Expected outputs:
- problem_statement.md
- requirements.md (REQ blocks)
- if_list.md (IF blocks)
- if_decomposition.md
- uf.md (UF blocks)
- uf_if_coverage_review.md
```

**Gate:** All IFs in `uf_if_coverage_review.md` must show no `UNCOVERED` gaps before proceeding.

### Step 2 — Evaluation Planning (eval-planner)
```
/eval-planner
Read requirements.md and uf.md.
Detect the domain and design an evaluation plan with:
- 1 primary metric + 2-4 secondary metrics
- Baseline / Target / Stretch thresholds for each metric
- Benchmark dataset specification
Output: evaluation_plan.md
```

### Step 3 — UF Implementation (uf-implementor)
```
/uf-implementor
Read uf.md and uf_if_coverage_review.md.
Implement all UF blocks as Python functions with full unit tests.
Skip any UFs flagged REDUNDANT.
Output to src/uf/ and tests/unit/.
```

### Step 4 — IF Integration (if-integrator)
```
/if-integrator
Read if_list.md, if_decomposition.md, and src/uf/*.py.
Generate IF-level integration modules and integration tests.
Output to src/if/ and tests/integration/.
```

### Step 5 — Run Evaluation (eval-runner)
```
/eval-runner
Read evaluation_plan.md and the test results from tests/.
Generate metric calculation scripts and a formatted comparison report.
Output: scripts/eval/, reports/eval/, evidence_pack/metrics.yaml
```

### Step 6 — CI Automation (ci-evidence-automation)
```
/ci-evidence-automation
Read verification_plan.md and evidence_pack/.
Generate CI configuration and coverage gate checks.
Link test results to evidence artifacts.
```

**Total output artifacts:**
```
problem_statement.md / requirements.md / if_list.md / if_decomposition.md
uf.md / uf_if_coverage_review.md / evaluation_plan.md / verification_plan.md
src/uf/*.py  /  src/if/*.py
tests/unit/  /  tests/integration/
scripts/eval/  /  reports/eval/  /  evidence_pack/
.ci/  (GitHub Actions / CI config)
```

---

## Workflow B — Debug & Fix Failing Integration

**Scenario:** Integration tests are failing. UF or IF behavior is incorrect and the root cause is unknown.

**Skills used:** `uf-if-debug-mapper` → `uf-chain-validator` → `uf-implementor` (targeted fix) → `eval-runner`

### Step 1 — Map the Failure (uf-if-debug-mapper)
```
/uf-if-debug-mapper
The integration test for IF-02 is failing with the following error:
[에러 메시지 또는 증상 설명]

Read if_list.md, if_decomposition.md, and uf.md.
Map the failure symptom to the most likely UF code location.
Produce a debug_map.md with:
- Root cause hypothesis ranked by probability
- Specific file/function locations to inspect
- Step-by-step debug plan
```

### Step 2 — Validate Chain Integrity (uf-chain-validator)
```
/uf-chain-validator
Read uf.md and src/uf/*.py.
Validate I/O chain integrity for the UFs listed in debug_map.md.
Report: type mismatches, shape errors, missing edge case handling.
```

### Step 3 — Fix the UF (uf-implementor)
```
/uf-implementor
Fix UF-05 based on the findings in debug_map.md and the uf-chain-validator report.
Re-implement the function and update its unit tests.
Output updated src/uf/analysis.py and tests/unit/test_analysis.py.
```

### Step 4 — Re-evaluate (eval-runner)
```
/eval-runner
Read evaluation_plan.md.
Compare the new test results against the previous baseline in evidence_pack/metrics.yaml.
Generate a delta comparison report.
```

---

## Workflow C — Multi-Agent Parallel Design

**Scenario:** A large design task is split across multiple parallel agents — e.g., one agent per system layer or domain.

**Skills used:** `core-engineering` → `agent-orchestration` → `agent-executor`

### Step 1 — Initial Design (core-engineering)
```
/core-engineering
Run Stages 1–5 for the following system:
[시스템 설명]

Produce: problem_statement.md, requirements.md, if_list.md
(Stop before IF decomposition — that will be distributed to agents.)
```

### Step 2 — Plan Agent Roles (agent-orchestration)
```
/agent-orchestration
Read if_list.md (5 IFs total).
Design a 3-agent orchestration plan:
- Agent 1: IF-01, IF-02 (signal pipeline)
- Agent 2: IF-03, IF-04 (feature extraction)
- Agent 3: IF-05 (output formatting)
Each agent should run core-engineering Stages 6–7 for its assigned IFs.
Generate: agents/orchestration_plan.md, agents/agent-1-role.md ~ agent-3-role.md
```

### Step 3 — Execute Agents (agent-executor)
```
/agent-executor
Read agents/orchestration_plan.md.
Spawn all agents in parallel for execution group 1.
Collect outputs: if_decomposition.md, uf.md per agent.
Generate: agents/orchestration_report.md
```

### Step 4 — Merge and Continue (core-engineering)
```
/core-engineering
Merge the uf.md files from agents/agent-1-role.md ~ agent-3-role.md output.
Run Stage 7.5 (UF→IF Coverage Review) across all merged UFs.
Output: uf_if_coverage_review.md
```

---

## Workflow D — GPU/HPC Compute-Intensive Pipeline

**Scenario:** A compute-heavy pipeline (training, inference, large-batch processing) needs memory and latency validation before implementation.

**Skills used:** `core-engineering` → `gpu-hpc-guard` → `eval-planner` → `eval-runner`

### Step 1 — Design (core-engineering)
```
/core-engineering
Run full design process for the following GPU-heavy workload:
[파이프라인 설명 — e.g., batch size, model architecture, data dimensions]

Output through Stage 7: uf.md
```

### Step 2 — Memory & Complexity Audit (gpu-hpc-guard)
```
/gpu-hpc-guard
Read uf.md and the following code files: src/uf/*.py
Audit memory footprint and compute complexity for each UF.
Flag any UF that exceeds:
- GPU memory: 8 GB
- Per-batch latency: 100ms
Propose chunking or streaming strategies for flagged UFs.
```

### Step 3 — Evaluation Planning (eval-planner)
```
/eval-planner
Read requirements.md and the gpu-hpc-guard audit report.
Add GPU throughput and memory efficiency as secondary metrics.
Output: evaluation_plan.md
```

### Step 4 — Run & Report (eval-runner)
```
/eval-runner
Read evaluation_plan.md and profiling results from scripts/profile/.
Compute all metrics and generate a benchmark comparison report.
Output: reports/eval/gpu_benchmark_<timestamp>.md
```

---

## Workflow E — RAG System Development

**Scenario:** Building or auditing a Retrieval-Augmented Generation system.

**Skills used:** `core-engineering` → `rag-data-quality` → `eval-planner` → `eval-runner` → `ci-evidence-automation`

### Step 1 — Design (core-engineering)
```
/core-engineering
Design a RAG system for the following use case:
[RAG 사용 사례 설명 — domain, corpus size, query type]

Output: requirements.md, if_list.md, uf.md
(Focus on retrieval, reranking, and generation UFs)
```

### Step 2 — Corpus Quality Audit (rag-data-quality)
```
/rag-data-quality
Audit the RAG corpus at data/corpus/.
Check: chunking strategy, metadata coverage, deduplication, domain coverage gaps.
Report: recall@k for top queries, reranker score distribution.
Output: reports/rag/corpus_audit.md
```

### Step 3 — Evaluation Planning (eval-planner)
```
/eval-planner
Read requirements.md and reports/rag/corpus_audit.md.
Design evaluation plan with: Recall@5, MRR, NDCG@10, BERTScore as metrics.
Output: evaluation_plan.md
```

### Step 4 — Run Metrics (eval-runner)
```
/eval-runner
Read evaluation_plan.md and retrieval experiment outputs.
Compute all metrics and compare baseline vs. new chunking strategy.
Output: reports/eval/rag_eval_<timestamp>.md
```

### Step 5 — CI Gate (ci-evidence-automation)
```
/ci-evidence-automation
Read evaluation_plan.md and evidence_pack/metrics.yaml.
Generate a CI gate that blocks merge if Recall@5 < 0.70.
```

---

## Workflow F — Physics Simulation Audit

**Scenario:** A simulation codebase (signal processing, dynamics, optics, thermal) needs physics consistency validation.

**Skills used:** `sim-physics-auditor` → `eval-planner` → `eval-runner`

### Step 1 — Physics Audit (sim-physics-auditor)
```
/sim-physics-auditor
Audit the simulation code in src/sim/.
Check: unit consistency, coordinate frame transforms, Nyquist/timestep criteria,
numerical stability (condition number, round-off accumulation).
Domain: [signal_processing | dynamics_control | optics | thermal_fluid]
Output: reports/sim/physics_audit.md
```

### Step 2 — Evaluation Planning (eval-planner)
```
/eval-planner
Read requirements.md and reports/sim/physics_audit.md.
Select simulation-appropriate metrics: RMSE, conservation error, divergence rate, etc.
Output: evaluation_plan.md
```

### Step 3 — Validate Results (eval-runner)
```
/eval-runner
Read evaluation_plan.md and simulation outputs from results/sim/.
Generate metric calculations and a formatted validation report.
Output: reports/eval/sim_validation_<timestamp>.md
```

---

## Skill Dependency Summary

| Skill | Requires (input from) | Produces (output for) |
|---|---|---|
| `core-engineering` | User prompt | `eval-planner`, `uf-implementor`, `agent-orchestration` |
| `eval-planner` | `requirements.md`, `uf.md` | `eval-runner` |
| `eval-runner` | `evaluation_plan.md` + experiment results | `ci-evidence-automation` |
| `uf-implementor` | `uf.md`, `uf_if_coverage_review.md` | `if-integrator` |
| `if-integrator` | `if_list.md`, `src/uf/` | `eval-runner`, `ci-evidence-automation` |
| `uf-chain-validator` | `uf.md`, `src/uf/` | `uf-implementor` (fix cycle) |
| `uf-if-debug-mapper` | error symptoms, `uf.md`, `if_list.md` | `uf-chain-validator` |
| `agent-orchestration` | `if_list.md`, task description | `agent-executor` |
| `agent-executor` | `agents/*.md` | merged outputs → next skill |
| `gpu-hpc-guard` | `uf.md`, `src/` | `eval-planner` (adds metrics) |
| `sim-physics-auditor` | `src/sim/` | `eval-planner` (adds metrics) |
| `rag-data-quality` | `data/corpus/` | `eval-planner` (adds metrics) |
| `ci-evidence-automation` | `verification_plan.md`, `evidence_pack/` | CI pipeline |

---

## Parallel Execution Opportunities

When multiple skills do not depend on each other, run them in a single agent-executor call (or ask Claude to execute them in one message):

**Can run in parallel:**
- `gpu-hpc-guard` + `sim-physics-auditor` (both audit independent concerns)
- `uf-chain-validator` + `eval-planner` (validation and planning are independent)
- Multiple `uf-implementor` calls for different IF groups

**Must run sequentially:**
- `core-engineering` → anything else (foundation must come first)
- `uf-implementor` → `if-integrator` (UFs must exist before integration)
- `eval-planner` → `eval-runner` (plan must exist before computation)
