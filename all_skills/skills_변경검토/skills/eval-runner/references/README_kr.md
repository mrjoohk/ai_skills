# eval-runner 스킬 가이드

## 스킬 개요

**eval-runner**는 `evaluation_plan.md` 또는 지표 목록을 입력받아 **계산 함수를 자동 생성**하고 실험 결과를 **정량적인 리포트로 변환**하는 스킬입니다. eval-planner의 출력물을 이어받아 core-engineering Stage 8의 **실행 단계**를 담당하며, 계산 함수 재사용성과 CI 통합을 지원합니다.

---

## 언제 사용하는가

**트리거 조건:**
- `eval-planner`가 생성한 `evaluation_plan.md`가 있을 때 (권장)
- 지표 이름과 데이터 경로만 있어도 됨 (evaluation_plan 없이도 동작)
- 여러 실험 결과를 비교 테이블로 정리하고 싶을 때
- CI 파이프라인에 지표 계산 스크립트를 추가하고 싶을 때
- 실험 결과 수치를 직접 입력하여 빠르게 평가하고 싶을 때

**선행 조건:**
- 실험 결과 데이터 (파일 또는 수치)
- evaluation_plan.md (선택사항, 있으면 더 정확)

---

## 입력

eval-runner는 다음 형태의 입력을 받습니다:

### 입력 1: evaluation_plan.md (권장)
```
/eval-runner evaluation_plan.md를 읽고
실험 결과 데이터를 바탕으로 계산 함수와 리포트를 생성해줘.
```

### 입력 2: 지표 이름 + 임계값 직접 지정
```
/eval-runner 다음 지표를 계산해줘.
Primary: SI-SDR (Target: >= 12.0 dB)
Secondary: PESQ (Target: >= 2.8), WER (Target: <= 15%)
입력: pred/baseline/, ref/clean/
```

### 입력 3: 수치 직접 입력
```
/eval-runner 다음 결과를 비교해줘.
Exp-01: SI-SDR=9.2, PESQ=2.3, WER=18.2%
Exp-02: SI-SDR=12.8, PESQ=2.9, WER=14.1%
Target: SI-SDR >= 12.0, WER <= 15%
```

### 실험 결과 데이터 형식

- **파일 경로** — `pred/<exp_name>/*.wav`, `ref/clean/*.wav` 등
- **배열/리스트** — `[9.2, 12.8, 11.4]` (점수 배열)
- **수치 직접 입력** — `SI-SDR=12.8 dB`

---

## 출력물

### 생성 파일

| 파일명 | 설명 |
|---|---|
| `scripts/eval/<task>_eval.py` | 재사용 가능한 계산 함수 모음 (2차 실행 용) |
| `reports/eval/<task>_<timestamp>.md` | 포맷된 결과 리포트 (비교 테이블 + 판정) |
| `evidence_pack/metrics.yaml` | CI 연동용 구조화된 수치 기록 |

### 1. 계산 스크립트 (`scripts/eval/<task>_eval.py`)

**특징:**
- 재사용 가능한 순수 Python 함수
- 의존성 명시 (pip 설치 가능)
- 배치 처리 및 단일 샘플 처리 모두 지원
- CLI 인터페이스 제공 (`--pred`, `--ref`, `--out` 옵션)

**사용 예시:**
```bash
python scripts/eval/separation_eval.py \
  --pred pred/proposed/output/ \
  --ref ref/clean/reference/ \
  --out evidence_pack/metrics.yaml
```

### 2. 결과 리포트 (`reports/eval/<task>_<timestamp>.md`)

**포함 내용:**
- 결과 요약 테이블 (비교, Delta, Target 대비 판정)
- Primary Metric 분석
- 수락 기준 판정 (PASS/FAIL)
- Evidence 섹션 (스크립트, 데이터셋, 샘플 수)

**예시:**

```markdown
# Evaluation Report: Speech Separation
Date: 2026-03-19 | Commit: abc123def

## 결과 요약

| 지표 | Baseline | Proposed | Delta | Target | 판정 |
|---|---:|---:|---:|---:|:---:|
| SI-SDR (↑) | 9.2 dB | 12.8 dB | +3.6 | ≥ 12.0 | ✅ PASS |
| PESQ (↑) | 2.3 | 2.9 | +0.6 | ≥ 2.8 | ✅ PASS |
| WER (↓) | 18.2% | 14.1% | -4.1 | ≤ 15% | ✅ PASS |

## Primary Metric: SI-SDR
- 결과: 12.8 dB ✅ (Target: ≥ 12.0 dB)
- 향상: +3.6 dB vs Baseline (+39.1%)

## 수락 기준 판정
Then SI-SDR >= 12.0 dB → **PASS** (실측: 12.8 dB)

## Evidence
- 계산 스크립트: `scripts/eval/separation_eval.py`
- 원시 결과: `evidence_pack/metrics.yaml`
- 데이터셋: WSJ0-2mix (N=3000)
```

### 3. 메트릭 기록 (`evidence_pack/metrics.yaml`)

**용도:**
- CI/CD 파이프라인의 구조화된 입력
- 자동 회귀 테스트 및 성능 추적
- 다른 자동화 도구와의 연동

**스키마:**
```yaml
metrics:
  - metric_id:   si_sdr
    value:        12.8
    unit:         dB
    direction:    higher_is_better
    threshold:    12.0
    comparison:   gte
    status:       PASS
    experiment:   exp-02-proposed
    dataset:      wsj0-2mix-test
    n_samples:    3000
    timestamp:    2026-03-19T10:00:00Z
    commit_sha:   abc123
```

---

## 슬래시 명령 예시

### 예시 1: 평가 계획 → 계산 함수 + 리포트
```
/eval-runner evaluation_plan.md 를 읽고
음원 분리 태스크에 대한 SI-SDR, PESQ, STOI 계산 함수를
scripts/eval/separation_eval.py 에 작성하고,
다음 두 실험 결과를 비교 리포트로 출력해줘.
  Exp-01 (baseline): pred/baseline/, ref/clean/
  Exp-02 (proposed): pred/proposed/, ref/clean/
```

**기대 결과:**
- `scripts/eval/separation_eval.py`
- `reports/eval/separation_<timestamp>.md`
- `evidence_pack/metrics.yaml`

---

### 예시 2: 수치 직접 입력 → 비교 테이블
```
/eval-runner 다음 실험 결과를 비교 테이블로 정리해줘.
Target: SI-SDR >= 12.0, WER <= 15%.
  Exp-01 Baseline:  SI-SDR=9.2, PESQ=2.3, WER=18.2%
  Exp-02 Proposed:  SI-SDR=12.8, PESQ=2.9, WER=14.1%
  Exp-03 Ablation:  SI-SDR=11.4, PESQ=2.7, WER=15.3%
수락 기준 판정(PASS/FAIL)도 포함해줘.
```

**기대 결과:**
- `reports/eval/comparison_<timestamp>.md` (3-way 비교 테이블 + PASS/FAIL 판정)

---

### 예시 3: NLP 지표 계산 스크립트 생성
```
/eval-runner 번역 모델 평가를 위해
BLEU, ROUGE-L, BERTScore 계산 스크립트를 작성해줘.
입력: pred/translations.txt, ref/references.txt
결과를 evidence_pack/metrics.yaml 에 저장하고
CI에서 바로 실행 가능한 형태로 만들어줘.
```

**기대 결과:**
- `scripts/eval/translation_eval.py`
- 실행 명령: `python scripts/eval/translation_eval.py --pred ... --ref ...`

---

## 다른 스킬과의 연결

### eval-planner → eval-runner → ci-evidence-automation 워크플로우

```
┌─────────────────────────────────────────────┐
│  Stage 8: Verification & Evidence Planning   │
└─────────────────────────────────────────────┘
              ↓
        [1] eval-planner
            (평가 기준 설계)
              ↓
        evaluation_plan.md
        ├─ Primary metric 1개
        ├─ Secondary metrics 2~4개
        ├─ Baseline / Target / Stretch
        └─ 수락 기준 (Given/When/Then)
              ↓
        [2] eval-runner ← YOU ARE HERE
            (지표 계산 & 리포트 생성)
              ↓
        scripts/eval/<task>_eval.py
        reports/eval/<task>_*.md
        evidence_pack/metrics.yaml
              ↓
        [3] ci-evidence-automation (선택)
            (CI 파이프라인 자동화)
              ↓
        GitHub Actions / GitLab CI
        └─ 자동 테스트 & 성능 추적
```

### eval-planner 없이도 사용 가능

eval-runner는 **evaluation_plan.md 없이도 독립적으로 동작**합니다:

```
지표 이름 + 데이터 경로를 직접 제공 → 바로 계산 함수 & 리포트 생성
```

이는 빠른 프로토타이핑이나 임시 평가 시 유용합니다.

---

## 생성되는 산출물 상세

### 1. 계산 함수 스크립트

**특징:**
- Pure Python (최소 의존성)
- 재사용 가능 (여러 실험에 적용 가능)
- 단일 책임 원칙 (함수 1개 = 지표 1개)
- 타입 힌트 및 docstring 포함

**예시 함수 구조:**
```python
def compute_si_sdr(prediction, reference):
    """
    Args:
        prediction: (N, T) or (T,) numpy array or torch tensor
        reference:  (N, T) or (T,) numpy array or torch tensor
    Returns:
        score: float (dB, higher is better)
    """
    # 계산 로직
    return si_sdr_value
```

### 2. 결과 리포트 (Markdown)

**구성:**
1. 메타데이터 (날짜, Commit, 데이터셋)
2. 결과 요약 테이블 (비교, Delta, 판정)
3. Primary Metric 상세 분석
4. 수락 기준 판정
5. Evidence (스크립트 경로, 데이터 경로, 샘플 수)

**특징:**
- 이해관계자와 공유하기 좋은 형식
- Git 저장소에 추적 가능
- 자동 생성되므로 일관성 유지

### 3. metrics.yaml (구조화된 기록)

**용도:**
- 프로그래밍 방식의 데이터 접근
- CI/CD 파이프라인 자동화
- 성능 추적 및 회귀 테스트
- 시계열 모니터링

**예시:**
```yaml
metrics:
  - metric_id: si_sdr
    value: 12.8
    status: PASS
  - metric_id: pesq
    value: 2.9
    status: PASS
```

---

## 주요 규칙

1. **지표 방향 일치** — ↑/↓와 비교 방향 (>=, <=) 일치 확인
2. **동일 조건 확인** — 여러 실험 비교 시 동일한 데이터셋·분할·시드 사용
3. **통계 유의성** — 필요하면 p-value 또는 bootstrap CI 보고
4. **의존성 명시** — 계산 함수의 라이브러리 버전 명시
5. **재현성** — Commit SHA, 타임스탬프, 데이터셋명 모두 기록

---

## eval-planner와의 차이점

| 특징 | eval-planner | eval-runner |
|---|---|---|
| **역할** | 평가 기준 설계 | 지표 계산 실행 |
| **입력** | REQ/UF 문서 | evaluation_plan + 실험 결과 |
| **출력** | evaluation_plan.md | 계산 함수 + 리포트 + metrics.yaml |
| **독립성** | 독립 실행 | 독립 실행 가능 (plan 없이도) |
| **타겟** | 검증 전 계획 단계 | 검증 실행 단계 |

---

## 다음 단계

리포트가 생성되면:

1. **검증** — `reports/eval/<task>_*.md` 리뷰 (PASS/FAIL 확인)
2. **증거 저장** — `evidence_pack/metrics.yaml` 저장소 커밋
3. **자동화** (선택) — `ci-evidence-automation`으로 CI 통합

```
/ci-evidence-automation evidence_pack/metrics.yaml을 읽고
GitHub Actions에 자동 테스트를 추가해줘.
```
