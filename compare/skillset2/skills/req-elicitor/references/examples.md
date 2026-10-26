# Examples: req-elicitor

## Example Problem Description (Input)

> "실시간 객체 탐지 시스템을 모바일 엣지 디바이스에서 동작시켜야 한다.
>  현재 서버 기반 모델은 너무 느리고 배터리를 많이 소모한다.
>  드론 탑재 카메라 영상을 처리해야 하고 인터넷 연결이 없는 환경에서도 동작해야 한다."

---

## Example Clarification Questions (Stage 2 output)

1. 탐지해야 하는 객체 종류는 무엇인가요? (사람, 차량, 특정 물체 등)
2. 허용 가능한 추론 지연 시간(latency)은 얼마인가요? (예: 100ms? 50ms?)
3. 목표 정확도(mAP 등)는 어떻게 정의하나요? 허용 가능한 최소 임계값은?
4. 타깃 디바이스의 사양은? (CPU 코어 수, RAM 크기, 가용 배터리 용량)
5. 카메라 해상도 및 프레임레이트는 얼마인가요? (예: 720p @ 30fps)
6. 배터리 소모 허용 한계는? (예: 시간당 소모량 목표)
7. 오프라인 환경에서의 모델 업데이트 방식은? (USB, 사전 탑재만 허용?)
8. 동시 탐지해야 하는 객체의 최대 수는?

---

## Example requirements.md (Stage 4 output)

```markdown
# Requirements

## Functional Requirements

### REQ-001 — Real-time Object Detection
- ID: REQ-001
- Title: Real-time object detection on edge device
- Context: Drone-mounted camera must detect objects locally without cloud dependency.
- Inputs:
    frame: ndarray, uint8, shape=(H, W, 3), H∈[480,1080], W∈[640,1920]
    timestamp: float64, seconds, range=[0, ∞)
- Outputs:
    detections: List[BoundingBox], each with (x, y, w, h, class_id, confidence)
    inference_time_ms: float32, milliseconds
- Constraints:
    Inference latency ≤ 80 ms per frame (single frame, CPU-only)
    Model size ≤ 50 MB (flash storage limit)
    RAM usage ≤ 512 MB during inference
- Acceptance Criteria:
    Given a 720p video frame at 30fps,
    When the detection model runs on the target edge device (ARM Cortex-A78),
    Then inference latency ≤ 80 ms at 95th percentile across 1000 consecutive frames
- Tests:
    Unit:        tests/unit/test_detector.py::test_single_frame_latency
    Integration: tests/integration/test_video_stream_throughput.py
    E2E:         tests/e2e/test_drone_field_scenario.py
- Evidence:
    reports/latency/latency_histogram.png
    evidence_pack/req001/metrics.yaml

---

### REQ-002 — Detection Accuracy
- ID: REQ-002
- Title: Minimum detection accuracy on target object classes
- Context: False negatives in object detection have operational consequences.
- Inputs:
    image_batch: ndarray, uint8, shape=(N, H, W, 3)
    ground_truth: List[Annotation]
- Outputs:
    mAP_50: float32, dimensionless, range=[0.0, 1.0]
    recall_per_class: Dict[str, float32]
- Constraints:
    Evaluated on held-out validation set of ≥ 2,000 annotated images
- Acceptance Criteria:
    Given the validation dataset (2,000 images, 5 object classes),
    When the model runs inference without post-processing time limit,
    Then mAP@IoU=0.50 ≥ 0.82
    And per-class recall ≥ 0.75 for all target classes
- Tests:
    Unit:        tests/unit/test_accuracy.py::test_map_calculation
    Integration: tests/integration/test_validation_pipeline.py
    E2E:         tests/e2e/test_accuracy_full_dataset.py
- Evidence:
    reports/accuracy/confusion_matrix.png
    evidence_pack/req002/metrics.yaml

---

## Non-Functional Requirements

### REQ-010 — Battery Consumption
- ID: REQ-010
- Title: Maximum power draw during continuous inference
- Context: Drone battery life directly limits mission duration.
- Inputs:
    power_log: TimeSeries[float32], watts, sampled at 1Hz
- Outputs:
    avg_power_draw_W: float32, watts
    mission_duration_minutes: float32
- Constraints:
    Measured under full load (continuous 30fps inference, 30-minute window)
- Acceptance Criteria:
    Given continuous object detection at 30fps for 30 minutes,
    When measured on the target device with a 5000mAh battery,
    Then average power draw ≤ 3.5W
    And estimated flight time reduction ≤ 15% compared to idle baseline
- Tests:
    Unit:        tests/unit/test_power_mock.py
    Integration: tests/integration/test_power_extended_run.py
    E2E:         tests/e2e/test_field_battery_benchmark.py
- Evidence:
    reports/power/power_trace_30min.csv
    evidence_pack/req010/metrics.yaml
```

---

## Quality Checklist (before handing off to if-designer)

- [x] All REQs have numeric thresholds in Given/When/Then
- [x] All I/O types have type + unit + range
- [x] All assumptions are listed as `Unvalidated` in assumptions_and_constraints.md
- [x] REQ IDs are sequential and unique
- [x] No acceptance criterion says only "fast", "accurate", or "low memory"
