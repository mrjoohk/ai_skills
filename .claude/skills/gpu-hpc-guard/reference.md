# Reference: GPU/HPC Audit Outputs

## VRAM Estimate Table
| Component | Shape | dtype | bytes | peak? |
|----------|-------|-------|------:|:-----:|

bytes = prod(shape) * dtype_size

## Complexity Estimate
- Identify primary loops and dimensions (na, nf, nx, ny, nz)
- Provide Big-O and dominant constant factors
- Note memory bandwidth vs compute bound

## Mitigation Playbook
- Chunking: choose chunk axis and size
- Streaming: pipeline stages, overlap compute/transfer
- Offload: GPU->RAM points (with correctness checks)
- Fusing: reduce intermediate allocations
- Multi-GPU: distribute by pulses, tiles, or frequencies

## Acceptance
- Peak VRAM <= X GB
- Runtime <= Y sec for reference scenario
- Numeric error <= eps vs baseline
