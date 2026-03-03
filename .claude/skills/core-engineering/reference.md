# Reference: Core Engineering Templates

## Requirement Block (REQ-###)
**ID:** REQ-001  
**Context:**  
**Inputs:** (types, units, coordinate frame, shape)  
**Outputs:** (types, units, shape)  
**Constraints:** (runtime, memory, accuracy, determinism, safety)  
**Acceptance Criteria:**  
- Given … When … Then … (numeric threshold)  
- Example: "Then cross-range resolution error <= 0.5 m"  
**Tests:**  
- Unit: …  
- Integration: …  
- E2E: …  
**Evidence:**  
- `reports/<...>` (plots, logs, metrics)  
- `evidence_pack/<...>` (runs.yaml, metrics.yaml, env.yaml)

## UF Block (UF-##)
**UF-ID:** UF-01  
**Goal:**  
**I/O Contract:**  
**Algorithm Summary:**  
**Edge Cases:**  
**Verification Plan:**  
**Evidence Pack Fields:** scenario_id, run_id, metrics, environment, commit_sha

## Minimal Diff Patch Pattern
- Prefer `git diff` style patches over full-file output.
- Keep refactor-only commits separate from behavior changes.

## Evidence Pack Minimal Schema
- `evidence_pack/runs.yaml`: run metadata (timestamp, commit, params)
- `evidence_pack/metrics.yaml`: numeric results + thresholds + pass/fail
- `evidence_pack/env.yaml`: versions (OS, Python, CUDA, GPU)
