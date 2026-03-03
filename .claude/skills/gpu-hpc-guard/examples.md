# Examples: GPU/HPC Guard

## Test Prompt 1: VRAM Estimation
"Estimate VRAM for phase-history tensor with na=2560, nf=4096, dtype=complex64. Propose chunking to fit within 24GB VRAM."

## Test Prompt 2: OOM Mitigation Plan
"In `src/sar/bp.py::backproject()`, identify allocations that scale with nx*ny*nz. Propose an offload+streaming plan that keeps peak VRAM under 18GB."

## Test Prompt 3: Microbench Setup
"Generate a microbenchmark script that profiles runtime and peak VRAM for chunk sizes [64,128,256]. Store results under `reports/bench/`."

## Expected Output
- VRAM table
- chunking plan
- acceptance thresholds
