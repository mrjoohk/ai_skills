---
name: uf-implementor
description: "Implements Unit Functions (UFs) as production-ready code from UF Block definitions. Generates implementation stubs, docstrings, unit tests, and verifies against I/O contracts and acceptance criteria. Trigger when the user says 'implement UF', 'write code for unit function', 'generate UF implementation', or 'code up the UF blocks'."
user-invocable: true
allowed-tools: Read, Write
---

# UF Implementor

Takes `uf.md` (UF Block definitions, output of Stage 7) as input and generates **production-ready implementation code** with unit tests for each Unit Function.
This skill bridges the design phase and the coding phase.

---

## When to Use
- After Stage 7.5 (UF→IF Coverage Review) has been approved and `uf_if_coverage_review.md` shows no `UNCOVERED` gaps
- When you want to translate UF Block definitions into actual runnable code
- When you need unit test scaffolding generated from acceptance criteria

---

## Inputs
- `uf.md` — UF Block definitions (required)
- `uf_if_coverage_review.md` — coverage review result (recommended; skip if unavailable)
- `requirements.md` — for cross-referencing non-functional constraints (optional)

---

## Execution Steps

### Step 1 — Load and Parse UF Blocks
- Read `uf.md` and extract all UF Blocks
- For each UF, capture: UF-ID, Parent IF, Goal, I/O Contract, Algorithm Summary, Edge Cases, Verification Plan
- If `uf_if_coverage_review.md` exists, skip any UFs flagged `REDUNDANT` unless explicitly requested
- Detect implementation language from project context (Python default; check for existing source files)

### Step 2 — Generate Implementation Stub per UF
For each UF, produce a function with:
- Correct signature matching the I/O Contract (types, shapes, units in docstring)
- Google-style docstring with Args, Returns, Raises, and Example sections
- Core algorithm body (concrete implementation, not placeholder `pass`)
- Input validation guards (type check, shape check, range check)
- Edge case handling from the Edge Cases field

```python
# Example structure
def uf_<id>_<snake_name>(
    <input_name>: <type>,  # <unit/shape>, <range>
) -> <output_type>:
    """<Goal statement>

    Args:
        <input_name>: <description>. Shape: <shape>. Unit: <unit>.
    Returns:
        <output_name>: <description>. Shape: <shape>. Unit: <unit>.
    Raises:
        ValueError: if <edge case condition>
    Example:
        >>> result = uf_<id>_<name>(...)
        >>> assert result.shape == (...)
    """
    # Input validation
    ...
    # Core algorithm
    ...
    return result
```

### Step 3 — Generate Unit Tests per UF
For each UF, produce a test file with:
- Happy-path test: nominal input → expected output with numeric tolerance
- Edge-case tests: one test per Edge Case listed in UF Block
- Acceptance criteria test: directly maps Given/When/Then to a `pytest` test function
- Fixture definitions for reusable inputs

```python
# Example test structure
def test_uf_<id>_<name>_nominal():
    """Given <situation>, When <action>, Then <result>."""
    ...
    assert result == pytest.approx(expected, rel=1e-4)

def test_uf_<id>_<name>_edge_<case>():
    with pytest.raises(ValueError):
        uf_<id>_<name>(<invalid_input>)
```

### Step 4 — Validate and Emit Coverage Report
- Run a static I/O chain check: output type/shape of UF-N must match input type/shape of its consumer UF
- Record each UF implementation status: `IMPLEMENTED` / `STUB` / `BLOCKED`
- Emit `reports/impl/uf_impl_report_<timestamp>.md`

---

## Output Files

| File | Description |
|---|---|
| `src/uf/<module_name>.py` | Implementation code, one file per IF group |
| `tests/unit/test_<module_name>.py` | Unit test file per IF group |
| `reports/impl/uf_impl_report_<timestamp>.md` | Implementation status report |

---

## Output Template — `uf_impl_report_<timestamp>.md`

```markdown
# UF Implementation Report
Date: <date>

## Implementation Status

| UF-ID | Function Name | Status | Test Coverage | Notes |
|---|---|:---:|:---:|---|
| UF-01 | uf_01_load_signal | IMPLEMENTED | nominal + 2 edge | — |
| UF-02 | uf_02_normalize | IMPLEMENTED | nominal + 1 edge | — |
| UF-03 | uf_03_transform  | STUB        | —               | algorithm TBD |

## I/O Chain Validation

| UF-N → UF-M | Output Type | Input Type | Match |
|---|---|---|:---:|
| UF-01 → UF-02 | np.ndarray(float32) | np.ndarray(float32) | ✅ |
| UF-02 → UF-03 | np.ndarray(float32) | torch.Tensor        | ❌ type mismatch |

## Action Items
- [ ] UF-03: finalize algorithm; resolve tensor type mismatch with UF-02
```

---

## Rules
1. Never leave a function body as `pass` or `raise NotImplementedError` without at least a partial algorithm outline
2. Every numeric threshold from the acceptance criteria must appear verbatim in the test assert
3. If the algorithm is underdetermined by the UF Block, note `# CLARIFICATION NEEDED: <question>` inline and flag as `STUB`
4. Do not import libraries not listed in `requirements.md` or `reference.md` without noting the addition

See `reference.md` for language-specific templates and library recommendations.
