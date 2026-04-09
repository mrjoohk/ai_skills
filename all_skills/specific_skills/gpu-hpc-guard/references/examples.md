# Examples: GPU/HPC Guard

## Test Prompt 1: VRAM Estimation
```
"Estimate the VRAM usage of a model forward pass with batch size B=32,
 image size (3, 512, 512), intermediate feature channels C=256,
 dtype=float32. Propose the maximum batch size that fits within
 a 24GB VRAM limit."
```

**Expected output:**
- VRAM estimation table (bytes per tensor + peak markers)
- Recommended maximum batch size with justification

---

## Test Prompt 2: OOM Mitigation Plan
```
"An OOM occurs in src/model/decoder.py::decode(). Analyze the major
 tensor allocations in that function and propose a chunking/offload
 plan to keep peak VRAM below 16GB."
```

**Expected output:**
- List of major tensors (path::symbol, shape, dtype)
- Proposed chunking axes and sizes
- Explicit offload points (GPU→CPU)

---

## Test Prompt 3: Microbenchmark Script Design
```
"Design a microbenchmark script that measures processing time and
 peak VRAM for batch sizes [8, 16, 32, 64]. Store results in
 reports/bench/."
```

**Expected output:**
- Benchmark script design (path reference)
- `reports/bench/<timestamp>/results.csv` schema

---

## Test Prompt 4: Multi-GPU Distribution Strategy
```
"Currently training on a single GPU (40GB capacity) with a 35GB model.
 When scaling to a 2-GPU environment, which data/model/pipeline
 parallelism strategy is most suitable? Analyze the tradeoffs."
```

**Expected output:**
- Comparison table of parallelism strategies and conditions
- Recommended strategy with implementation points (path::symbol)
