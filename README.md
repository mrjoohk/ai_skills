# Engineering Skills Pack

A collection of **15 reusable Claude skills** that cover the full research & engineering lifecycle:
from problem definition through design, implementation, evaluation, and CI automation.

Skills are composable — each skill's output artifacts serve as inputs to the next.
See [`Skill_Combination_Usage_Guide.md`](./Skill_Combination_Usage_Guide.md) for end-to-end workflow examples.

---

## Install

Copy the `.claude/` directory and the global rules file into your project root:

```bash
cp -r .claude/ <your-project>/
cp GLOBAL_RULES.md <your-project>/
cp -r tools/ <your-project>/        # Rule 4/8 worklog validator, Rule 14 graph_checks
```

For a **new** project, start from [`PROJECT_TEMPLATE/`](./PROJECT_TEMPLATE/) instead — it ships
`GLOBAL_RULES.md`, the `PROJECT_RULES.md` skeleton (Rule 10), the ledger (`graph/edges.csv`),
the append-only worklogs (`logs/*.jsonl`), and both checkers already wired together.

**Canonical source & sync:** `all_skills/`가 모든 스킬의 **정본**이며 `.claude/skills/`는 설치본이다.
스킬 수정은 항상 `all_skills/`에서 하고, 아래 스크립트로 드리프트 검사·동기화한다
(공용 스킬의 폴더 간 사본도 함께 검사; `context-engineering`은 파이프라인별 의도적 분기로 제외):

```bash
python scripts/check_skill_sync.py          # 검사만
python scripts/check_skill_sync.py --apply  # 정본 → 사본/설치본 동기화
```

Invoke any skill using a slash command in your Claude session:

```
/core-engineering Design the following system: [problem description]
/eval-planner Read requirements.md and design an evaluation plan.
/uf-implementor Implement all UFs from uf.md.
```

---

## Skill Overview

### Design Foundation

| Skill | Role | Key Outputs |
|---|---|---|
| [`core-engineering`](.claude/skills/core-engineering/) | 8-stage design process from problem to verified UF blocks | `requirements.md`, `if_list.md`, `if_decomposition.md`, `uf.md`, `uf_if_coverage_review.md`, `verification_plan.md` |
| [`theory-decomposer`](all_skills/core-engineering_pipeline_skills/theory-decomposer/) | Theory-level front-end: source availability check (T0) → recursive decomposition with stop criteria (S1–S4, `max_depth`) → EQ Blocks → merge-readiness gate | `rd/source_survey.md`, `rd/theory_statement.md`, `rd/theory_tree.md`, `rd/eq.md`, `rd/eq_coverage_review.md` |

**8-Stage Design Process:**
```
1. Problem Definition          → problem_statement.md
2. Problem Review & Clarification → clarification_log.md
3. Problem Elaboration         → assumptions_and_constraints.md
4. Requirements Elicitation    → requirements.md  (REQ blocks)
5. IF Identification           → if_list.md       (IF blocks)
6. IF Decomposition            → if_decomposition.md
7. UF Definition               → uf.md            (UF blocks)
7.5 UF→IF Coverage Review      → uf_if_coverage_review.md
8. Verification & Evidence Planning → verification_plan.md
```

---

### Implementation

| Skill | Role | Key Outputs |
|---|---|---|
| [`uf-implementor`](.claude/skills/uf-implementor/) | Converts UF Block definitions into production code + unit tests | `src/uf/*.py`, `tests/unit/`, `uf_impl_report.md` |
| [`if-integrator`](.claude/skills/if-integrator/) | Assembles UF implementations into IF-level API modules + integration tests | `src/if/*.py`, `tests/integration/`, `if_integration_report.md` |

**Entry conditions:**
- `uf-implementor`: requires `uf.md` with Stage 7.5 coverage review passed (no `UNCOVERED` gaps)
- `if-integrator`: requires `src/uf/` files with `IMPLEMENTED` status

---

### Validation & Debugging

| Skill | Role | Key Outputs |
|---|---|---|
| [`uf-chain-validator`](.claude/skills/uf-chain-validator/) | Validates UF-chain I/O contracts, test coverage, and evidence linkage | Chain validation report |
| [`uf-if-debug-mapper`](.claude/skills/uf-if-debug-mapper/) | Maps failure symptoms to root cause UF/IF code locations | `docs/uf_if_debug_map.md` with ranked hypotheses |
| [`fresh-eyes-auditor`](all_skills/core-engineering_pipeline_skills/fresh-eyes-auditor/) | Spawns a context-free agent to audit for ambiguity/forced-logic/errors/hallucination, then triages findings by citation check (advisory) | `review_docs/*_fresh_eyes_audit.md` |

**Typical debug flow:**
```
uf-if-debug-mapper  →  uf-chain-validator  →  uf-implementor (fix)
```

---

### Evaluation

| Skill | Role | Key Outputs |
|---|---|---|
| [`eval-planner`](.claude/skills/eval-planner/) | Selects domain-appropriate metrics and sets Baseline/Target/Stretch thresholds | `rd/evaluation_plan.md` |
| [`exp-runner`](all_skills/core-engineering_pipeline_skills/exp-runner/) | Executes the evaluation plan: fixes seeds/env, runs experiments, records provenance | `evidence_pack/runs.yaml`, `evidence_pack/env.yaml`, `results/<exp_id>/` |
| [`eval-runner`](.claude/skills/eval-runner/) | Generates metric calculation scripts and comparison reports from experiment results | `scripts/eval/*.py`, `reports/eval/*.md`, `evidence_pack/metrics.yaml` |

**Supported domains:** ML/DL classification & regression, Audio/Speech (SI-SDR, PESQ, WER, DER), NLP (BLEU, BERTScore, ROUGE-L)

---

### Domain-Specific Auditors

| Skill | Domain | What it checks |
|---|---|---|
| [`gpu-hpc-guard`](.claude/skills/gpu-hpc-guard/) | GPU / HPC workloads (PyTorch, TF, NumPy) | Memory footprint, compute complexity, chunking/streaming strategies |
| [`sim-physics-auditor`](.claude/skills/sim-physics-auditor/) | Physics simulation | Unit consistency, coordinate frames, Nyquist/timestep criteria, numerical stability |
| [`rag-data-quality`](.claude/skills/rag-data-quality/) | RAG / vector retrieval | Chunking quality, metadata coverage, deduplication, recall@k |

These auditors connect to `eval-planner` by enriching it with domain-specific metrics.

---

### CI / Evidence

| Skill | Role | Key Outputs |
|---|---|---|
| [`ci-evidence-automation`](.claude/skills/ci-evidence-automation/) | Automates CI checks, coverage gates, evidence packs, and regression reporting | CI config, coverage reports, evidence_pack/ |

---

### Multi-Agent Orchestration

| Skill | Role | Key Outputs |
|---|---|---|
| [`agent-orchestration`](.claude/skills/agent-orchestration/) | Designs multi-agent workflows and generates structured role description files | `agents/orchestration_plan.md`, `agents/agent-N-role.md` |
| [`agent-executor`](.claude/skills/agent-executor/) | Reads role files and actually spawns subagents in parallel | Integrated orchestration report |

**ag-platform variants** (file-based message passing, no subagent spawn):
- [`ag-orchestration`](.claude/skills/ag-orchestration/) — orchestrator session
- [`ag-agent-executor`](.claude/skills/ag-agent-executor/) — individual agent session

---

## Key Artifact Reference

| Artifact | Produced by | Consumed by |
|---|---|---|
| `requirements.md` | `core-engineering` | `eval-planner`, `uf-implementor` |
| `if_list.md` | `core-engineering` | `if-integrator`, `agent-orchestration`, `uf-if-debug-mapper` |
| `if_decomposition.md` | `core-engineering` | `if-integrator`, `uf-if-debug-mapper` |
| `uf.md` | `core-engineering` | `uf-implementor`, `uf-chain-validator`, `eval-planner` |
| `uf_if_coverage_review.md` | `core-engineering` (Stage 7.5) | `uf-implementor` (gate check) |
| `rd/evaluation_plan.md` | `eval-planner` | `exp-runner`, `eval-runner` |
| `evidence_pack/runs.yaml`, `env.yaml` | `exp-runner` | `eval-runner`, `ci-evidence-automation` |
| `rd/domain_metrics.md` | `gpu-hpc-guard`, `sim-physics-auditor`, `rag-data-quality` | `eval-planner` |
| `evidence_pack/metrics.yaml` | `eval-runner` | `ci-evidence-automation` |
| `src/uf/*.py` | `uf-implementor` | `if-integrator`, `uf-chain-validator` |
| `src/if/*.py` | `if-integrator` | `eval-runner`, `ci-evidence-automation` |
| `agents/orchestration_plan.md` | `agent-orchestration` | `agent-executor` |
| `docs/uf_if_debug_map.md` | `uf-if-debug-mapper` | `uf-chain-validator`, `uf-implementor` |
| `rd/eq.md` | `theory-decomposer` | `uf-implementor` (uf.md-compatible EQ Blocks) |
| `rd/theory_tree.md` | `theory-decomposer` | `if-integrator` (if_decomposition.md-compatible) |
| `rd/source_survey.md` | `theory-decomposer` (T0) | `eval-planner`, `eval-runner` (verification oracle) |

---

## Global Rules

[`GLOBAL_RULES.md`](./GLOBAL_RULES.md) defines project-wide conventions that apply across all skills:

- Coding behavior principles (Part 1) and the per-request workflow (Part 2)
- Append-only worklogs: `logs/files.jsonl` (Rule 4), `logs/prompts.jsonl` (Rule 8),
  validated by `tools/worklog/validate_worklog.py` after every append
- Standard directories: `review_docs/` (Rule 6), `output_docs/` (Rule 7), `rd/` (Rule 9), `reports/` (Rule 16)
- Project binding via `PROJECT_RULES.md` (Rule 10) — GLOBAL_RULES stays project-agnostic
- Ledger and IDs: `F-`/`D-`/`M-` in `graph/edges.csv` (Rule 11), `P-xxx` as the provenance root
- Verification discipline: negative-control tests (Rule 12), evidence citation (Rule 13),
  machine gates via `tools/graph_checks.py` (Rule 14), delta review + context-free audit (Rule 15)

---

## Directory Structure

```
ai_skills/
├── README.md                         ← This file
├── GLOBAL_RULES.md                   ← Project-wide conventions
├── Skill_Combination_Usage_Guide.md  ← Combined workflow examples
├── scripts/
│   └── generate_mcp_templates.py
└── .claude/
    └── skills/
        ├── core-engineering/
        │   ├── SKILL.md
        │   ├── reference.md
        │   ├── examples.md
        │   └── README_kr.md
        ├── uf-implementor/
        ├── if-integrator/
        ├── uf-chain-validator/
        ├── uf-if-debug-mapper/
        ├── eval-planner/
        ├── eval-runner/
        ├── gpu-hpc-guard/
        ├── sim-physics-auditor/
        ├── rag-data-quality/
        ├── ci-evidence-automation/
        ├── agent-orchestration/
        ├── agent-executor/
        ├── ag-orchestration/        ← ag-platform variant
        └── ag-agent-executor/       ← ag-platform variant
```

Each skill folder contains:
- `SKILL.md` — invocation rules, execution steps, output templates
- `reference.md` — code templates, schema definitions, lookup tables
- `examples.md` — test prompts and expected outputs
- `README_kr.md` — Korean usage guide

---

## Combined Workflow Summary

| Workflow | Skills Used | Start Condition |
|---|---|---|
| **A. Full Design-to-Code** | `core-engineering` → `eval-planner` → `uf-implementor` → `if-integrator` → `exp-runner` → `eval-runner` → `ci-evidence-automation` | Problem statement only |
| **B. Debug Failing Integration** | `uf-if-debug-mapper` → `uf-chain-validator` → `uf-implementor` → `eval-runner` | Failing test + existing design docs |
| **C. Multi-Agent Parallel Design** | `core-engineering` → `agent-orchestration` → `agent-executor` | Large system with parallel IF groups |
| **D. GPU/HPC Audit** | `core-engineering` → `gpu-hpc-guard` → `eval-planner` → `eval-runner` | Compute-intensive workload |
| **E. RAG Development** | `core-engineering` → `rag-data-quality` → `eval-planner` → `eval-runner` → `ci-evidence-automation` | RAG system + corpus |
| **F. Physics Simulation** | `sim-physics-auditor` → `eval-planner` → `eval-runner` | Simulation codebase |
| **G. Theory-to-Dynamics Reconstruction** | `theory-decomposer` → `uf-implementor` → `if-integrator` → `sim-physics-auditor` → `eval-planner` → `eval-runner` | Theory/phenomenon description only (T0 verdict routes verification) |

See [`Skill_Combination_Usage_Guide.md`](./Skill_Combination_Usage_Guide.md) for step-by-step slash command sequences for each workflow.
