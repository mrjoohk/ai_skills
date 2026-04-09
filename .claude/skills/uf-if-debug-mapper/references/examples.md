# Examples: UF/IF Debug Mapper

## Test Prompt 1: Generate Debug Map from Existing Documents
```
"Scan docs/uf/ (UF-01..UF-20) and docs/if/ (IF-01..IF-08) to
 generate docs/uf_if_debug_map.md. For each UF/IF, map the most
 likely code entry points under src/, and list invariants and
 debug hooks."
```

**Expected output:**
- `docs/uf_if_debug_map.md` (sections 1-6 complete)
- UF→Code mapping table + IF→Code mapping table

---

## Test Prompt 2: Runtime Symptom Triage
```
"Intermittent numerical errors occur in the data processing pipeline.
 Update the Symptom→Root Cause section in docs/uf_if_debug_map.md
 and specify breakpoint locations and logs to add. Keep
 recommendations minimal and actionable."
```

**Expected output:**
- Section 3 (Symptom→Root Cause) updated
- Section 4 (Debug Playbooks) enhanced

---

## Test Prompt 3: IF Contract Failure Debugging
```
"Data arrives on IF-04 interface but parsing values are incorrect.
 Add serialization/endianness checks and decode function verification
 checklist to the debug map's IF section. Include a minimal repro
 checklist."
```

**Expected output:**
- IF-04 row updated (failure modes + debug hooks)
- Repro checklist

---

## Test Prompt 4: Performance Goal Shortfall Triage
```
"Processing time for UF-12 (batch processing) exceeds target (200ms).
 Establish a performance profiling plan and add potential bottleneck
 entry points and metrics to the mapping."
```

**Expected output:**
- UF-12 row updated (symptom + first check location)
- Profiling commands and metrics list
