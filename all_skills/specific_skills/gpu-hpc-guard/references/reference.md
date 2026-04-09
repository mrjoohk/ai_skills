# Reference: GPU/HPC Guard Audit Outputs

## VRAM / RAM Estimation Table
```
| Component (Tensor/Buffer Name) | Shape | dtype | Bytes | Peak? |
|--------------------------------|-------|-------|------:|:-----:|
| Example: feature_map           | (B, C, H, W) | float32 | B*C*H*W*4 | ✓ |
```

**Calculation formula:**
```
bytes = prod(shape) × dtype_size
  float32 = 4 bytes
  float16 = 2 bytes
  int8    = 1 byte
  complex64 = 8 bytes
```

Peak memory estimation = Σ(concurrent tensor bytes) + framework overhead (~10~20%)

---

## Complexity Estimation

| Item | Technique |
|---|---|
| Big-O | Based on main loop dimensions (e.g., O(B × C × H × W)) |
| Dominant constant | Number of repeated operations, memory access patterns |
| Bound type | Memory-bound / Compute-bound distinction |
| Bottleneck point | Function path::symbol reference |

---

## Mitigation Strategy Playbook

| Strategy | Application Condition | Method |
|---|---|---|
| **Chunking** | Single tensor exceeds VRAM limit | Partition by batch or spatial dimensions |
| **Streaming** | Sequential stages in pipeline | Overlap computation/transfer |
| **Offload** | VRAM shortage, RAM available | Specify GPU→CPU offload points |
| **Kernel Fusion** | Repeated intermediate tensor generation | Merge consecutive operations into single kernel |
| **Mixed Precision** | Full float32 not needed | Identify layers convertible to fp16/bf16 |
| **Multi-GPU Distribution** | Single GPU capacity exceeded | Choose data/model/pipeline parallelism |

---

## Acceptance Criteria Template
```
- Peak VRAM:  <= X GB  (e.g., <= 16 GB)
- Peak RAM:   <= Y GB  (e.g., <= 64 GB)
- Processing time:  <= Z sec (baseline scenario)
- Numerical error:  <= eps   (vs. baseline output)
- Coverage:   >= N%    (includes chunking variants)
```

---

## Microbenchmark Setup Guide
```
1. Isolate target function (reproducible with minimal input)
2. Define chunk size / batch size variant list
3. Warmups: >= 3, Measurements: >= 5
4. Metrics: average time, peak VRAM, peak RAM
5. Store results: reports/bench/<timestamp>/results.csv
```
