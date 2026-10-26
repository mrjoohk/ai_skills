---
name: gpu-hpc-guard
description: "Audits GPU/HPC memory footprint, complexity hotspots, and proposes chunking/streaming strategies for any compute-intensive workload."
user-invocable: true
allowed-tools: Read, Write
---

# GPU/HPC Guard

Audits GPU and HPC resource risks for any compute-intensive workload:
- Memory usage estimation (VRAM / RAM)
- Computational complexity hotspot analysis
- OOM risk pattern detection (nested loops, large intermediate tensors, inefficient allocation)
- Chunking / Streaming / Offload strategy proposals

---

## When to Use
- Large tensor operations (NumPy, CuPy, PyTorch, TensorFlow, CUDA kernels)
- Batch processing, matrix operations, image·signal·point cloud processing
- Multi-GPU scaling planning
- Any compute-intensive module where memory budget warnings occur

---

## Inputs
- Target function or module to analyze (path + symbol reference)
- Expected data dimensions (batch size, tensor shape, data type)
- Hardware constraints: VRAM/GPU count, PCIe bandwidth, RAM limit

---

## Output
- **VRAM/RAM estimation table** (based on dtype·shape)
- **Complexity estimation** (Big-O + approximate constants)
- **Mitigation plan:** chunk sizes, streaming stages, kernel fusion, offload points
- **Acceptance criteria:** max memory, max time per UF, accuracy validation checks

---

## Pipeline Insertion & Input Source
- **When:** in an engineering pipeline, audit the available UF design or implementation before its metrics are adopted by `eval-planner` (Stage 8). Recheck the affected scope after batch size / model size / hardware changes. A standalone audit can use the supplied module and dimensions without creating UF documents.
- **Input source:** extract shape / dtype / batch dimensions from the project's canonical UF `I/O Contract`, code, and configuration. Inspect available hardware information first; ask only for missing constraints needed for the audit.
- **Paths:** honor user-specified outputs and existing canonical locations. `rd/uf.md`, `rd/domain_metrics.md`, and `reports/gpu/` are optional defaults for a new project, not prerequisites.

## Downstream Handoff — eval wiring
Return audit-derived metrics and proposed thresholds to main in the following form. Label estimates and unmeasured values explicitly; measured baselines cite their source evidence.

```
| Metric | Direction | Baseline | Target | Unit | Rationale | Auditor |
|---|---|---|---|---|---|---|
| peak_vram | ↓ | <measured> | ≤ <budget> | GB | OOM guard for UF-## | gpu-hpc-guard |
| uf_latency_p95 | ↓ | <measured> | ≤ <req> | ms | REQ-## constraint | gpu-hpc-guard |
```

Main verifies the results and is the single writer that merges accepted metrics into the project's canonical `domain_metrics.md` for `eval-planner`. Parallel workers return messages or write only to an assigned unique fragment, for example `reports/gpu/<task-id>/domain_metrics.md`; they must not append to the shared canonical file. Reuse approved thresholds and mark new proposals as proposals. If this audit is used as a required gate, dependent work waits until its required criteria pass.

## Runtime Integration
- Use available execution/profiling tools for authorized microbenchmarks and hardware snapshots.
- Use available file tools only for the assigned output scope. A concise standalone audit can be returned in the conversation; persist details when requested or needed for resumption.
- Use configured notification tools only when the user has authorized notifications.

---

## Token Saving
- Request only shape data at kernel launch sites and major allocation points.
- Return concise tables; when persistence is needed, use the project's report location and assigned unique task path.

See `references/reference.md` and `references/examples.md`.
