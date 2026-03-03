# Reference: UF/IF Debug Map Template

Create `docs/uf_if_debug_map.md` with the following sections.

---

## 0. Scope and Assumptions
- Project:
- Commit:
- Date:
- UF Range:
- IF Range:
- Runtime constraints:
- Hardware constraints (GPU/CPU/RAM):

---

## 1. UF → Code Map (Primary Table)

| UF-ID | Goal | Key Modules | Entry Points (path::symbol) | Data In/Out | Invariants | Tests | Evidence |
|------:|------|-------------|-----------------------------|------------|-----------|------|---------|

**Notes:**
- Key Modules: minimal set of files relevant to the UF.
- Entry Points: exact function/class names where execution starts.
- Invariants: things that must remain true (units, shape, monotonic indices, buffer sizes).
- Evidence: report/log paths.

---

## 2. IF → Code Map (Interface/Integration Table)

| IF-ID | Interface Contract | Producer | Consumer | Wire/IPC/ABI | Failure Modes | Debug Hooks |
|------:|--------------------|----------|----------|--------------|--------------|------------|

**Failure Modes Examples**
- schema mismatch (fields missing)
- endian/packing alignment
- timing/latency jitter
- stale shared memory ring buffer
- multicast join/drop issues

---

## 3. Symptom → Likely Root Cause → Where to Debug

| Symptom | Likely Root Causes | First Places to Inspect (paths::symbols) | Quick Checks | Repro Command |
|--------|---------------------|------------------------------------------|-------------|--------------|

Examples of symptoms:
- OOM / VRAM spike
- wrong SAR resolution
- PRF/Nyquist aliasing
- unstable control loop at 120 Hz
- missing RAG grounding/citations
- CI coverage gate failure

---

## 4. Debug Playbooks (Copy/Paste)

### 4.1 Fast Triage (5–10 min)
1. Confirm reproduction steps
2. Collect logs and environment snapshot
3. Identify the UF/IF involved
4. Jump to mapped entry points

### 4.2 Instrumentation (Minimal)
- Add structured logs with keys: uf_id, if_id, shape, dtype, units, frame, timestamps
- Add sanity assertions for invariants (guarded by debug flag)
- Store logs under `reports/debug/<timestamp>/`

### 4.3 Breakpoints and Watchpoints
- List recommended breakpoints by UF/IF:
  - file::function + line hint
- Watch for:
  - shape changes
  - units conversion points
  - buffer/ring indices
  - kernel allocations

### 4.4 Profiling / Performance
- GPU:
  - `nvidia-smi` snapshots
  - optional: Nsight Systems/Nsight Compute
- CPU:
  - cProfile/perf
- Record:
  - peak memory
  - throughput
  - latency/jitter (for 120 Hz loops)

---

## 5. Minimal Fix Patterns
- Fix the smallest surface area first (one module, one contract).
- Prefer patch/diff format.
- Keep refactor-only commits separate from behavior changes.

---

## 6. Evidence Outputs (Required)
- `reports/uf_if_debug_map.md` (or the map itself)
- `reports/debug/<run>/logs.txt`
- `evidence_pack/metrics.yaml` (pass/fail thresholds)
- `coverage.xml` (if tests changed)

---
