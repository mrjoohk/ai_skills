- UF-ID: UF-##-##
- Parent IF: IF-##
- Goal: <single verb phrase: e.g., "normalize input frame to float32 range [0, 1]">
- I/O Contract:
    Input:  <name>: <type>, <unit/shape>, <range>
    Output: <name>: <type>, <unit/shape>, <range>
- Algorithm Summary:
    <1–3 lines: algorithm name + core logic — no code, pseudocode is fine>
- Edge Cases:
    - <scenario>: <expected behavior — raise / return / log>
    - <scenario>: <expected behavior>
    - <scenario>: <expected behavior>
- Verification Plan:
    Unit:        tests/unit/test_<uf_name>.py::<test_func>
    Integration: tests/integration/test_<if_name>.py::<test_func>
    Coverage:    >= 90%
- Evidence Pack Fields: scenario_id, run_id, metrics, environment, commit_sha

---
<!-- Copy the block above for each UF. Replace all <...> placeholders. -->
<!-- UF-IDs follow the pattern UF-[parent_IF_num]-[seq]: UF-01-01, UF-01-02, UF-02-01, ... -->
