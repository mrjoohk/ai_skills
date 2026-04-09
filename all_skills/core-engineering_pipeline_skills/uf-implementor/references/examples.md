# Examples: UF Implementor

## Test Prompt 1: Implement All UFs from uf.md

```
/uf-implementor Read uf.md and generate implementation code for all UF blocks.
Output implementation files to src/uf/ and test files to tests/unit/.
```

**Expected outputs:**
- `src/uf/<module>.py` (implementation functions)
- `tests/unit/test_<module>.py` (unit tests)
- `reports/impl/uf_impl_report_<timestamp>.md`

---

## Test Prompt 2: Implement Specific UF by ID

```
/uf-implementor Implement UF-03 from uf.md.
The project uses PyTorch. Output to src/uf/processing.py.
```

**Expected outputs:**
- `src/uf/processing.py` (containing `uf_03_<name>` function)
- `tests/unit/test_processing.py` (test for UF-03 only)

---

## Test Prompt 3: Implement with Coverage Review Check

```
/uf-implementor Read uf.md and uf_if_coverage_review.md.
Skip any UFs flagged REDUNDANT.
Generate all remaining UF implementations with tests.
```

**Expected behavior:**
- Claude reads `uf_if_coverage_review.md` to identify REDUNDANT UFs
- Skips flagged UFs and notes them in the report as `SKIPPED`
- Implements all remaining UFs

---

## Example UF Block → Implementation Mapping

**Input (from uf.md):**
```
- UF-ID: UF-02
- Parent IF: IF-01
- Goal: Normalize input signal to unit L2-norm
- I/O Contract:
    Input:  signal: np.ndarray, shape=(N,), dtype=float32, range=[-1e3, 1e3]
    Output: normalized: np.ndarray, shape=(N,), dtype=float32, L2-norm=1.0
- Algorithm Summary: divide signal by its L2-norm with epsilon floor
- Edge Cases: zero signal (all zeros → output zeros, no divide-by-zero), NaN values → raise ValueError
- Verification Plan: pytest test_normalize_unit_norm, test_zero_signal, test_nan_rejection
```

**Generated Output (`src/uf/preprocessing.py`):**
```python
def uf_02_normalize(signal: np.ndarray) -> np.ndarray:
    """Normalize input signal to unit L2-norm.

    Args:
        signal: Input signal. Shape: (N,). dtype: float32. Range: [-1e3, 1e3].

    Returns:
        normalized: L2-normalized signal. Shape: (N,). dtype: float32. L2-norm ≈ 1.0.

    Raises:
        ValueError: if signal contains NaN values.

    Example:
        >>> x = np.array([3.0, 4.0], dtype=np.float32)
        >>> y = uf_02_normalize(x)
        >>> assert abs(np.linalg.norm(y) - 1.0) < 1e-6
    """
    if np.any(np.isnan(signal)):
        raise ValueError(f"signal must not contain NaN; got {np.sum(np.isnan(signal))} NaN values")

    norm = np.linalg.norm(signal)
    eps = 1e-8
    if norm < eps:
        return np.zeros_like(signal)
    return signal / norm
```

**Generated Test (`tests/unit/test_preprocessing.py`):**
```python
def test_uf_02_unit_norm(nominal_signal):
    result = uf_02_normalize(nominal_signal)
    assert abs(np.linalg.norm(result) - 1.0) < 1e-6

def test_uf_02_zero_signal():
    result = uf_02_normalize(np.zeros(64, dtype=np.float32))
    assert np.all(result == 0.0)

def test_uf_02_rejects_nan():
    with pytest.raises(ValueError, match="NaN"):
        uf_02_normalize(np.array([np.nan, 1.0], dtype=np.float32))
```
