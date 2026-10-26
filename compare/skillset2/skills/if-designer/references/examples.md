# Examples: if-designer

## Example Input (requirements.md excerpt)

```
### REQ-001 — Real-time Object Detection
  Inputs:  frame: ndarray, uint8, H×W×3
  Outputs: detections: List[BoundingBox]
  Acceptance Criteria: Given 720p frame @ 30fps, Then latency ≤ 80ms

### REQ-002 — Detection Accuracy
  Acceptance Criteria: Then mAP@0.5 ≥ 0.82

### REQ-010 — Battery Consumption
  Acceptance Criteria: Then avg power draw ≤ 3.5W
```

---

## Example if_list.md Output

```markdown
# Integration Function List

## IF-01 — Frame Ingestion and Preprocessing
- IF-ID: IF-01
- Title: Ingest raw camera frames and normalize for inference
- Producer: Camera driver (V4L2)
- Consumer: Inference engine (IF-02)
- Input Contract:
    raw_frame: ndarray, uint8, shape=(H, W, 3), H∈[480,1080]
    timestamp: float64, seconds
- Output Contract:
    normalized_frame: ndarray, float32, shape=(416, 416, 3), range=[0.0, 1.0]
- Constraints:
    Processing time ≤ 10ms per frame
    Must preserve aspect ratio via letterboxing
- Failure Modes:
    - Dropped frame: propagate None, skip inference cycle
    - Shape mismatch: raise ValueError, log and continue
- Linked REQs: REQ-001

---

## IF-02 — Object Detection Inference
- IF-ID: IF-02
- Title: Run model inference and produce raw bounding box predictions
- Producer: Preprocessing engine (IF-01)
- Consumer: Postprocessing engine (IF-03)
- Input Contract:
    normalized_frame: ndarray, float32, shape=(416, 416, 3)
- Output Contract:
    raw_predictions: ndarray, float32, shape=(N, 85)
    inference_ms: float32, milliseconds
- Constraints:
    Inference latency ≤ 60ms on ARM Cortex-A78
    Model size ≤ 50MB
- Failure Modes:
    - OOM: log + return empty predictions
    - Shape mismatch: raise ValueError
- Linked REQs: REQ-001, REQ-002

---

## REQ→IF Coverage Matrix

| REQ ID | IF Coverage | Status |
|--------|-------------|--------|
| REQ-001 | IF-01, IF-02, IF-03 | ✅ Covered |
| REQ-002 | IF-02, IF-03 | ✅ Covered |
| REQ-010 | IF-01, IF-02 | ✅ Covered |
```

---

## Example if_decomposition.md Output

```markdown
# IF Decomposition

## IF-01: Frame Ingestion and Preprocessing

Input:  raw_frame (ndarray, uint8, H×W×3)
Output: normalized_frame (ndarray, float32, 416×416×3)

[→ sequential]

├── UF-01-01: capture_frame
│     Input:  device_handle → Output: raw_frame (ndarray, uint8)
│     Note: wraps V4L2 read(), drops corrupted frames
│
├── UF-01-02: letterbox_resize          [depends on UF-01-01]
│     Input:  raw_frame → Output: resized_frame (ndarray, uint8, 416×416×3)
│     Note: aspect-ratio-preserving resize with gray padding
│
└── UF-01-03: normalize_to_float        [depends on UF-01-02]
      Input:  resized_frame (uint8) → Output: normalized_frame (float32, 0–1)
      Note: divide by 255.0

---

## IF-02: Object Detection Inference

Input:  normalized_frame (ndarray, float32, 416×416×3)
Output: raw_predictions (ndarray, float32, N×85)

[→ sequential]

├── UF-02-01: load_model_to_device
│     Input:  model_path (str) → Output: session (OrtSession)
│     Note: singleton; skip if already loaded
│
└── UF-02-02: run_onnx_inference        [depends on UF-02-01]
      Input:  normalized_frame, session → Output: raw_predictions (float32, N×85)
      Note: wraps ort.InferenceSession.run()
```

---

## Common Mistakes to Avoid

| Mistake | Why it's a problem | Fix |
|---|---|---|
| IF with no linked REQ | Orphan — might be unnecessary scope creep | Link to existing REQ or remove |
| REQ not covered by any IF | The system won't satisfy this requirement | Add an IF or extend existing IF's scope |
| IF whose output ≠ next IF's input | I/O chain breaks at integration time | Fix the output contract on one side |
| UF candidate with "and" in name | Violates SRP — split into two | Split: "parse_and_validate" → parse + validate |
| Leaf node too large | Not implementable as a single function | Decompose one more level |
