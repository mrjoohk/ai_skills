# Reference: UF/IF Debug Map Template

Generate `docs/uf_if_debug_map.md` with the following section structure.

---

## 0. Scope & Assumptions
```
- Project:
- Commit:
- Date:
- UF Scope:
- IF Scope:
- Runtime Constraints:
- Hardware Constraints (GPU/CPU/RAM):
```

---

## 1. UF → Code Mapping (Primary Table)

| UF-ID | Goal | Core Modules | Entry Point (path::symbol) | Data In/Out | Invariants | Tests | Evidence |
|------:|------|---------|-----------------|------------|-----------------|------|------|

**Column descriptions:**
- **Core Modules:** Minimal file list related to UF
- **Entry Point:** Exact function/class name where execution starts
- **Invariants:** Conditions that must be maintained (units, shape, monotonic index, buffer size, etc.)
- **Evidence:** Report/log paths

---

## 2. IF → Code Mapping (Interface/Integration Table)

| IF-ID | Interface Contract | Producer | Consumer | Communication (Wire/IPC/ABI) | Failure Modes | Debug Hooks |
|------:|-----------------|----------|----------|----------------------|---------|---------|

**Common failure modes:**
- Schema mismatch (missing fields)
- Serialization alignment/endianness errors
- Timing/latency jitter
- Shared memory ring buffer delays
- Network multicast join/drop

---

## 3. Symptom → Root Cause → Debug Location

| Symptom | Expected Root Cause | First Check Location (path::symbol) | Quick Verification | Repro Command |
|-----|-------------|------------------------|------------|---------|

**Common symptoms:**
- OOM / VRAM spike
- Numerical error or divergence
- Performance degradation (throughput/latency targets missed)
- Interface contract mismatch (schema error, null values)
- Test coverage gate failure
- Non-deterministic output (different results per run)

---

## 4. Debug Playbooks (Copy/Paste)

### 4.1 Quick Triage (5-10 minutes)
1. Verify repro steps
2. Collect logs and environment snapshots
3. Identify related UF/IF
4. Navigate to mapped entry point

### 4.2 Minimal Instrumentation
- Structured log keys: `uf_id, if_id, shape, dtype, units, frame, timestamp`
- Add invariant validation assertions (controlled by debug flag)
- Save logs: `reports/debug/<timestamp>/`

### 4.3 Breakpoints & Watchpoints
- Recommended breakpoints per UF/IF:
  - `file::function` + line hints
- Watch items:
  - Shape change points
  - Unit conversion points
  - Buffer/ring index boundaries

### 4.4 Profiling / Performance Analysis
- **GPU:** `nvidia-smi` snapshots; Nsight Systems/Compute (if needed)
- **CPU:** `cProfile`, `perf`, `py-spy`
- **Memory:** `memory_profiler`, `tracemalloc`
- **Metrics:** peak memory, throughput, latency/jitter

---

## 5. Minimal Fix Patterns
- Fix from narrowest scope first (single module, single contract).
- Provide in patch (diff) format.
- Keep refactoring and behavior changes in separate commits.

---

## 6. Evidence Outputs (Required)
- `reports/uf_if_debug_map.md`
- `reports/debug/<run>/logs.txt`
- `evidence_pack/metrics.yaml` (pass/fail thresholds)
- `coverage.xml` (if test changes made)
