# Reference: uf-designer

## UF Block Template

```markdown
- UF-ID: UF-##-##
- Parent IF: IF-##
- Goal: <single verb phrase: "normalize input frame to float32 range [0, 1]">
- I/O Contract:
    Input:  <name>: <type>, <unit/shape>, <range>
    Output: <name>: <type>, <unit/shape>, <range>
- Algorithm Summary:
    (1–3 lines: algorithm name + core logic, no code)
- Edge Cases:
    - <scenario>: <expected behavior (raise/return/log)>
    - <scenario>: <expected behavior>
    - <scenario>: <expected behavior>
- Verification Plan:
    Unit:        tests/unit/test_<uf_name>.py::<test_func>
    Integration: tests/integration/test_<if_name>.py::<test_func>
    Coverage:    >= 90%
- Evidence Pack Fields: scenario_id, run_id, metrics, environment, commit_sha
```

---

## Algorithm Summary Patterns

| UF Type | Good Algorithm Summary |
|---|---|
| Preprocessing | "Letterbox resize: compute uniform scale to fit 416×416, pad shorter dimension with value 114" |
| Normalization | "Divide each channel by 255.0 (uint8→float32); result range [0.0, 1.0]" |
| Inference | "Forward pass through ONNX session; return output tensor at index 0" |
| NMS | "Greedy NMS: sort by confidence desc, suppress boxes with IoU > threshold" |
| Parsing | "Split fixed-width binary header into named fields using struct.unpack" |

---

## Edge Case Taxonomy

Cover at least one from each applicable category:

**Null / empty input**
- `input is None` → raise `ValueError("input cannot be None")`
- `len(input) == 0` → return empty output of correct type

**Shape / type mismatch**
- `input.shape != expected_shape` → raise `ValueError(f"expected {expected}, got {actual}")`
- `input.dtype != expected_dtype` → cast or raise, document which

**Out-of-range values**
- `input contains NaN` → raise or replace with 0.0, document
- `input contains Inf` → clip to float32 max, log warning
- `input < min_valid` or `input > max_valid` → clip and log

**Resource limits**
- OOM on large input → raise `MemoryError`, do not suppress
- Disk full → propagate `IOError`

**Boundary conditions**
- Single-element input (N=1)
- Maximum-size input (stress test values)
- All-zero input

---

## I/O Chain Continuity Rules

For a sequence UF-A → UF-B → UF-C within an IF:

```
UF-A Output type == UF-B Input type   ✅
UF-A Output shape == UF-B Input shape ✅ (or transformation is explicit)
```

Common chain break patterns to watch for:
- `uint8` → function expects `float32`
- `(H, W, C)` → function expects `(C, H, W)` (channel-first vs channel-last)
- `List[dict]` → function expects `ndarray`
- Coordinate system: pixel vs normalized vs world

When a chain break is unavoidable, create an explicit conversion UF between them.

---

## Verification Plan Format

```
Unit:        tests/unit/test_normalize_frame.py::test_output_range_is_01
             tests/unit/test_normalize_frame.py::test_none_input_raises
             tests/unit/test_normalize_frame.py::test_zero_input
Integration: tests/integration/test_if01_pipeline.py::test_full_preprocessing_chain
Coverage:    >= 90%
```

Each unit test name should describe the scenario being tested, not just the function name.
