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

## MCP Integration
- `mcp.shell`: run microbenchmarks, profiling, collect `nvidia-smi` / `htop` snapshots
- `mcp.filesystem`: save benchmark logs and configuration variants
- `mcp.webhook` (optional): send regression notifications

---

## Token Saving
- Request only shape data at kernel launch sites and major allocation points.
- Output results as concise tables and store detailed content in `reports/`.

See `references/reference.md` and `references/examples.md`.
