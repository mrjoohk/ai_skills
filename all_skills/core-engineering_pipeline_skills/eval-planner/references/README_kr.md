# eval-planner 스킬 가이드

## 스킬 개요

**eval-planner**는 REQ 블록, UF 블록, 설계 문서를 분석하여 도메인에 적합한 평가 지표, 임계값, 벤치마크 계획을 설계하는 스킬입니다. core-engineering의 **Stage 8 (검증 & 증거 계획)**의 전용 진입점으로, 평가 기준을 정량화하여 모델 검증을 위한 체계적인 기반을 마련합니다.

---

## 언제 사용하는가

**트리거 조건:**
- `uf.md`, `requirements.md`, 설계 문서가 준비되어 있을 때
- 평가 지표와 수락 기준을 명확히 정의해야 할 때
- 도메인별 표준 지표와 임계값을 빠르게 도출해야 할 때
- `eval-runner`로 실험 결과를 평가하기 전에 평가 계획이 필요할 때

**선행 조건:**
- REQ 블록 또는 UF 블록이 정의되어 있음
- 모델의 도메인 (ML, 오디오, NLP 등)이 파악되어 있음

---

## 입력

eval-planner는 다음 우선순위로 입력을 받습니다:

1. **`uf.md`** — UF 블록 (Goal, I/O Contract, Acceptance Criteria)
2. **`requirements.md`** — REQ 블록
3. **설계 문서** — WBS, design doc 등
4. **도메인 힌트** — 지정하지 않으면 문서에서 자동 추론

입력은 파일 경로 또는 직접 텍스트로 제공할 수 있습니다.

---

## 출력물

### 생성 파일

| 파일명 | 설명 |
|---|---|
| `evaluation_plan.md` | 지표별 임계값 테이블, 수락 기준, REQ/UF 매핑 |
| 선택사항: 추가 분석 문서 | 임계값 설정 근거, 도메인 표준 참고문헌 |

### 평가 계획의 주요 요소

1. **Primary Metric 1개** — 모델 선택의 기준이 되는 핵심 지표
2. **Secondary Metrics 2~4개** — 트레이드오프 및 품질 보조 지표
3. **Baseline / Target / Stretch** — 수치 임계값 3단계
4. **수락 기준 (Given/When/Then)** — 검증 가능한 형식의 기준
5. **벤치마크 데이터셋** — 평가에 사용할 데이터 명시

---

## 슬래시 명령 예시

### 예시 1: 설계 문서로부터 평가 계획 생성
```
/eval-planner W400000_Downstream_Validation_Design.md 를 읽고
각 다운스트림 태스크(음원 분리 / ASR / 화자 분리 / 위치 추정)별로
평가 지표, 임계값(Baseline·Target·Stretch), 벤치마크 데이터셋을 정의하고
evaluation_plan.md 를 작성해줘.
```

**기대 결과:**
- `evaluation_plan.md` (태스크별 지표 테이블 + 수락 기준 + REQ 연결)

---

### 예시 2: REQ 블록 분석 → 평가 계획
```
/eval-planner requirements.md 의 REQ-001 ~ REQ-010 을 분석해서
각 요구사항에 대응하는 평가 지표와 수락 기준을 설계해줘.
Primary metric 1개와 Secondary metrics 2~3개를 명시하고
임계값은 Papers with Code 기준 SOTA를 Baseline으로 설정해줘.
```

**기대 결과:**
- `evaluation_plan.md` (REQ별 지표 매핑 포함)

---

### 예시 3: UF 블록 → 단위 평가 계획
```
/eval-planner uf.md 의 UF-01 ~ UF-15 중
직접 측정 가능한 UF들을 식별하고
각 UF의 Verification Plan에 연결할 지표와 임계값을 정의해줘.
NLP 도메인 모델이고 번역 태스크야.
```

**기대 결과:**
- `evaluation_plan.md` (UF별 지표 + 계산 방법)

---

## 다른 스킬과의 연결

### eval-planner → eval-runner 워크플로우

```
[1] eval-planner 실행
    ↓
    evaluation_plan.md 생성
    ├─ Primary metric
    ├─ Secondary metrics
    └─ 수락 기준
    ↓
[2] eval-runner 실행
    ↓
    scripts/eval/<task>_eval.py (계산 함수)
    reports/eval/<task>_*.md (결과 리포트)
    evidence_pack/metrics.yaml (수치 기록)
    ↓
[3] ci-evidence-automation (선택사항)
    ↓
    CI 파이프라인에 자동 통합
```

### 각 스킬의 역할

| 스킬 | 역할 | 입력 | 출력 |
|---|---|---|---|
| **eval-planner** | 평가 기준 설계 | REQ/UF 문서 | evaluation_plan.md |
| **eval-runner** | 지표 계산 & 리포트 생성 | evaluation_plan.md + 실험 결과 | 계산 스크립트 + 리포트 |
| **ci-evidence-automation** | CI 자동화 | metrics.yaml | 자동 증거 기록 |

---

## 지원 도메인 및 지표

### 지원 도메인

- **ML/딥러닝** — 분류, 회귀, 생성 모델
- **오디오/음성** — 음원 분리, ASR, 음성 품질, 화자 분리, 위치 추정
- **NLP** — 번역, 요약, QA, 추론
- **컴퓨터비전** — 객체 감지, 분할, 분류 등

### 각 도메인의 Primary Metric 예시

| 도메인 | 태스크 | Primary Metric |
|---|---|---|
| 오디오 | 음원 분리 | SI-SDR |
| 오디오 | 음성 품질 | PESQ |
| 오디오 | ASR | WER |
| NLP | 번역 | BLEU 또는 BERTScore |
| NLP | 요약 | ROUGE-L |
| ML | 분류 | Accuracy 또는 F1-score |

### 지표 조회

자세한 지표 목록 및 선택 기준은 `reference.md`를 참조하세요.

---

## 주요 규칙

1. **Primary metric은 1개만** — 모델 선택 기준이 흔들리지 않도록
2. **임계값은 반드시 수치** — "높을수록 좋다"는 사용 금지
3. **방향 표시** — 지표마다 ↑ (높을수록 좋음) 또는 ↓ (낮을수록 좋음) 명시
4. **Baseline 출처 명시** — 논문, 공개 벤치마크 등 근거 기재
5. **데이터셋 명시** — 평가에 사용할 데이터셋과 분할 범위 명시

---

## 다음 단계

평가 계획이 완성되면:

```
/eval-runner evaluation_plan.md를 읽고
실험 결과를 바탕으로 계산 함수와 리포트를 생성해줘.
```

을 실행하여 실험 결과를 정량적으로 평가합니다.
