# Examples: IF Integrator

## Test Prompt 1: Integrate All IFs from if_list.md

```
/if-integrator Read if_list.md and if_decomposition.md.
Generate integration modules for all IFs using the UF implementations in src/uf/.
Output to src/if/ and tests/integration/.
```

**Expected outputs:**
- `src/if/<module>.py` (integration module per IF)
- `tests/integration/test_<module>.py` (integration tests per IF)
- `reports/impl/if_integration_report_<timestamp>.md`

---

## Test Prompt 2: Integrate a Specific IF

```
/if-integrator Integrate IF-02 only.
Read if_list.md for the IF definition, if_decomposition.md for the UF call graph,
and src/uf/analysis.py for the UF implementations.
Output integration module to src/if/analysis_if.py.
```

**Expected behavior:**
- Reads IF-02 definition and its UF chain (e.g., UF-04 → UF-05)
- Generates `src/if/analysis_if.py` with `if_02_analyze()` entry point
- Generates `tests/integration/test_analysis_if.py`

---

## Test Prompt 3: Full Pipeline (uf-implementor → if-integrator)

```
# Step 1 (already done with uf-implementor):
# src/uf/preprocessing.py and src/uf/feature_extraction.py exist

/if-integrator Read if_list.md, if_decomposition.md, and src/uf/*.py.
Check uf_impl_report_*.md for any STUB or BLOCKED UFs.
Generate integration modules for IFs whose UFs are all IMPLEMENTED.
Skip IFs with STUB/BLOCKED UFs and list them in the report.
```

**Expected behavior:**
- Reads impl report to identify ready UFs
- Generates integration modules only for fully-IMPLEMENTED IFs
- Reports BLOCKED IFs with action items

---

## Example IF Definition → Integration Module Mapping

**Input (from if_list.md):**
```
- IF-ID: IF-01
- Goal: Signal preprocessing pipeline — normalize, window, and frame input audio
- Inputs:  raw_audio: np.ndarray, shape=(N,), dtype=float32, range=[-1, 1]
- Outputs: frames: np.ndarray, shape=(T, W), dtype=float32
- Constraints: max latency 20ms per chunk; no in-place modification of input
- Acceptance Criteria:
    Given raw audio of length N=16000 (1s at 16kHz),
    When if_01_preprocess() runs,
    Then output shape is (T, 512) where T = N // hop_length
- Linked REQs: REQ-01, REQ-02
```

**Input (from if_decomposition.md):**
```
IF-01 decomposition:
  UF-01 (normalize) → UF-02 (apply_window) → UF-03 (frame)
```

**Generated Output (`src/if/preprocessing_if.py`):**
```python
from src.uf.preprocessing import uf_01_normalize, uf_02_apply_window, uf_03_frame

def if_01_preprocess(
    raw_audio: np.ndarray,   # shape=(N,), dtype=float32, range=[-1, 1]
    hop_length: int = 160,
    window_size: int = 512,
) -> np.ndarray:             # shape=(T, 512), dtype=float32
    """Signal preprocessing pipeline — normalize, window, and frame input audio.

    Integration sequence: UF-01 (normalize) → UF-02 (apply_window) → UF-03 (frame)
    REQ links: REQ-01, REQ-02

    Args:
        raw_audio: Input audio signal. Shape: (N,). dtype: float32. Range: [-1, 1].
        hop_length: Frame shift in samples. Default: 160.
        window_size: Frame size in samples. Default: 512.

    Returns:
        frames: Windowed frames. Shape: (T, 512). dtype: float32.

    Raises:
        IntegrationError: if output shape does not satisfy REQ-01.
    """
    normed = uf_01_normalize(raw_audio)
    windowed = uf_02_apply_window(normed, window_size=window_size)
    frames = uf_03_frame(windowed, hop_length=hop_length)

    expected_T = len(raw_audio) // hop_length
    if frames.shape != (expected_T, window_size):
        raise IntegrationError(
            f"IF-01 postcondition failed: expected shape ({expected_T}, {window_size}), "
            f"got {frames.shape}"
        )
    return frames
```

**Generated Test (`tests/integration/test_preprocessing_if.py`):**
```python
def test_if_01_output_shape():
    """Given 1s audio at 16kHz, When if_01_preprocess() runs,
    Then output shape is (T, 512)."""
    audio = np.random.rand(16000).astype(np.float32) * 2 - 1
    frames = if_01_preprocess(audio, hop_length=160, window_size=512)
    assert frames.shape == (100, 512)

def test_if_01_does_not_modify_input():
    audio = np.random.rand(16000).astype(np.float32)
    original = audio.copy()
    if_01_preprocess(audio)
    np.testing.assert_array_equal(audio, original)
```
