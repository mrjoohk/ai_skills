# Examples: UF/IF Debug Mapper

## Test Prompt 1: Generate the Map from Existing Docs
"Generate `docs/uf_if_debug_map.md` by scanning `docs/uf/` (UF-01..UF-27) and `docs/if/` (IF-01..IF-10). For each UF/IF, map to the most likely code entry points under `src/` and list invariants and debug hooks."

## Test Prompt 2: Runtime Symptom Triage
"We see occasional OOM during backprojection and phase-history generation. Update `docs/uf_if_debug_map.md` to include symptom→root-cause mapping and specify where to set breakpoints and what logs to add. Keep recommendations minimal and actionable."

## Test Prompt 3: IF Contract Failure
"Packets are received but parsed values are corrupted. Update the IF section to include ABI/packing alignment checks, endian checks, and list the precise decode functions to inspect. Provide a minimal reproduction checklist."

## Test Prompt 4: 120 Hz Jitter
"The 120 Hz loop sometimes misses deadlines. Update the map with a jitter playbook: timing probes, buffering strategy checks, and first places to inspect in scheduler/IPC code."

## Expected Output Checklist
- UF→code table includes entry points with `path::symbol`
- IF→code table includes producer/consumer + contract summary
- Symptom table includes 3–10 concrete debug targets
- Playbooks include commands + artifact paths
- Evidence outputs defined
