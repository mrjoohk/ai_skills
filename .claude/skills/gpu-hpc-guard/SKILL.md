    ---
    name: gpu-hpc-guard
    description: "Flags GPU memory/OOM risks, complexity hotspots, and proposes chunking/streaming."
    user-invocable: true
    allowed-tools: Read, Write
---

# GPU/HPC Guard

Audits GPU/HPC risk early:
- memory footprint estimates (VRAM/RAM)
- complexity hot spots
- OOM risk patterns (N^3 loops, large intermediate tensors)
- proposes chunking/streaming/offload strategies

## When to Use
- SAR phase-history generation, backprojection, tomography
- Large tensor operations (CuPy/CUDA kernels)
- Multi-GPU scaling planning

## Inputs
- Function(s) or modules to analyze
- Expected dimensions: (na, nf, nx, ny, nz, batch sizes)
- GPU constraints: VRAM per GPU, number of GPUs, PCIe constraints

## Output
- VRAM estimate table
- complexity estimate (Big-O + rough constants)
- mitigation plan: chunk sizes, streaming plan, fused kernels, offload points
- acceptance: max memory, max time per UF, correctness checks

## MCP Integration
- `mcp.shell`: run microbenchmarks, profile runs, collect `nvidia-smi` snapshots
- `mcp.filesystem`: store benchmark logs and config variants
- optional `mcp.webhook`: send regression alerts

## Token Saving
- Ask for shapes and key code snippets only (kernel launches, alloc sites).
- Output a concise table; store details into `reports/` files.

See `reference.md` and `examples.md`.
