# CI Evidence Automation 스킬

## 스킬 개요

CI 파이프라인에서 증거 팩(Evidence Pack)을 자동으로 생성하고, 커버리지 게이트를 적용하며, 회귀(Regression)를 감지하는 스킬입니다. 각 CI 실행 시 runs.yaml, metrics.yaml, env.yaml, scenarios.yaml 등의 메타데이터를 수집하여 증거 기반의 검증을 가능하게 합니다.

## 언제 사용하는가

- UF(Unit Function) 모듈을 새로 도입할 때
- CI 파이프라인이 불안정하거나 진단 정보가 부족할 때
- 실험(Exp-01 등)의 일관된 증거 아티팩트가 필요할 때
- 벤치마크 회귀를 자동으로 감지하고 알림을 받고 싶을 때

## 입력

- CI 설정 파일 (`.github/workflows/*.yml`)
- 테스트 실행 명령어
- 증거 팩 스키마 정의 (`evidence_pack/*`)
- 성능 기준(baseline) 메트릭

## 출력물

| 파일/디렉토리 | 설명 |
|---|---|
| `.github/workflows/ci.yml` | 린트, 테스트, 커버리지, 아티팩트 업로드 단계가 포함된 CI 워크플로 |
| `evidence_pack/runs.yaml` | 실행 ID, 타임스탬프, 커밋 SHA, 브랜치, 트리거 타입 등 메타데이터 |
| `evidence_pack/metrics.yaml` | 측정된 수치, 임계값, pass/fail 상태 |
| `evidence_pack/env.yaml` | OS, 언어 버전, 라이브러리 버전, GPU 정보 등 환경 정보 |
| `evidence_pack/scenarios.yaml` | 테스트 시나리오 정의 및 입력 파라미터 |
| `evidence_pack/artifacts/logs/` | 각 단계별 실행 로그 |
| `evidence_pack/artifacts/plots/` | 성능/결과 그래프 |
| `evidence_pack/artifacts/coverage/` | 커버리지 리포트 (coverage.xml 등) |
| 회귀 알림 페이로드 | Webhook 형식의 REGRESSION/FAILURE/COVERAGE_LOW 알림 |

## 슬래시 명령 예시

### 1. 커버리지 게이트 설정
```
/ci-evidence-automation
".github/workflows/ci.yml을 업데이트하여 커버리지 >= 85% 게이트를 적용하고
coverage.xml을 아티팩트로 업로드하라. 최소 diff 형식으로 제공하라."
```

### 2. Evidence Pack 생성 단계 추가
```
/ci-evidence-automation
"각 CI 실행 시 evidence_pack/ 스키마를 작성하는 단계를 추가하라.
runs.yaml과 env.yaml을 자동으로 생성하고, 실행 후 아티팩트로 업로드하라."
```

### 3. 회귀 감지 및 알림
```
/ci-evidence-automation
"벤치마크 메트릭을 baseline과 비교하여 회귀가 5%를 초과하면
Webhook 알림을 트리거하는 CI 단계를 추가하라."
```

## 다른 스킬과의 연결

- **core-engineering**: Stage 8 (검증 & 증거 계획) 이후에 ci-evidence-automation을 호출하여 evidence_pack 구조를 자동으로 생성
- **uf-chain-validator**: UF 체인 검증이 완료된 후, CI 파이프라인에 자동 테스트 및 증거 수집 단계 추가
- **agent-orchestration**: CI 파이프라인 구성 및 실행 시 에이전트 역할 분담

### 전형적인 플로우
1. core-engineering: Stage 1~8을 통해 requirements.md, uf.md, verification_plan.md 생성
2. ci-evidence-automation: verification_plan.md를 기반으로 evidence_pack 스키마 및 CI 워크플로 생성
3. 각 CI 실행 시 자동으로 runs.yaml, metrics.yaml, env.yaml 생성 및 업로드
4. 회귀 감지 시 webhook 알림 발송

## 주요 개념

### CI 파이프라인 단계 (권장 순서)
1. **린트 (Lint)** - 코드 스타일 검사
2. **타입 체크** - 정적 타입 검증
3. **단위 테스트** - pytest, jest 등
4. **커버리지 게이트** - 임계값 이상 검증
5. **통합 테스트** - 시나리오 기반 테스트
6. **벤치마크** - 성능 메트릭 측정
7. **아티팩트 업로드** - 증거 팩 저장

### Evidence Pack 디렉토리 구조
```
evidence_pack/
  runs.yaml       # 실행 메타데이터
  metrics.yaml    # 수치 결과
  env.yaml        # 환경 정보
  scenarios.yaml  # 시나리오 정의
  artifacts/
    logs/         # 실행 로그
    plots/        # 그래프
    profiles/     # 성능 프로파일
    coverage/     # 커버리지 리포트
```

### 회귀(Regression) 정책
- 핵심 지표의 baseline 값을 저장하고 임계값을 정의
- 현재 값이 기준을 초과하면 CI를 실패시킴
- 계산식: `(current - baseline) / baseline <= threshold%`
- 예: 성능이 baseline 대비 5% 이상 저하되면 실패 처리
