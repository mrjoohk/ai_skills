# CI Evidence Automation 스킬

## 스킬 개요

CI 파이프라인에서 증거 팩(Evidence Pack)을 자동으로 생성하고, 커버리지 게이트를 적용하며, 회귀(Regression)를 감지하는 스킬입니다. 각 CI 실행 시 runs.yaml, metrics.yaml, env.yaml, scenarios.yaml 등의 메타데이터를 수집하여 증거 기반의 검증을 가능하게 합니다.

## 언제 사용하는가

- UF(Unit Function) 모듈을 새로 도입할 때
- CI 파이프라인이 불안정하거나 진단 정보가 부족할 때
- 실험(Exp-01 등)의 일관된 증거 아티팩트가 필요할 때
- 벤치마크 회귀를 자동으로 감지하고 알림을 받고 싶을 때
- 변경에 음성 대조(when required by the verification plan) 증거가 필요할 때 — 변이 실행기(`scripts/mutation_runner.py`)

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

## 변이 실행기 (`scripts/mutation_runner.py`)

변이 하나 = 파일 고치기(원래 글 → 바꾼 글) 하나 이상. 변이마다 코드를 임시 폴더에 새로 복사해 고치고 시험을 돌려, 시험이
실패(잡힘)하는지 본다. 작업 트리는 건드리지 않는다. 명세·옵션·결과 파일은 `references/mutation_runner.md`.
명령은 한 줄(cmd·셸 공통), `R` = `.claude/skills/ci-evidence-automation/scripts/mutation_runner.py`.

| 언제 | 명령 |
|---|---|
| 코드를 고칠 때마다 — 패턴이 아직 맞는가(시험 없이 몇 초) | `python R SPEC --root . --check` |
| 반복 중 — 바뀐 함수의 변이만 | `python R SPEC --root . --changed 스냅숏 --jobs 2 --out RES.json` |
| 한 영역만 | `python R SPEC --root . --only R0*,F05 --jobs 2` |
| 마지막 증거 — 전체 한 번 | `python R SPEC --root . --jobs <코어 수> --out logs/<P>_evidence/mutation.json` |
| 호출당 시간 제한이 있는 호스트 | `python R SPEC --root . --out RES.json --budget 100 --timeout 60` — 종료 코드 3 이면 같은 명령 반복 |
| 마지막 관문(합친 결과로) | `python R SPEC --root . --out RES.json --summary --strict` |

1. **작게 반복, 전체는 한 번**: 고칠 때마다 `--check`, 반복 중에는 `--changed`/`--only`, 전체는 끝에 한 번 `--jobs` = 코어 수.
   한 벌만 띄울 수 있는 프로그램(COM·한/글)을 쓰는 시험은 `--jobs 1`.
2. **어디든 시간 제한**: 변이마다 `--timeout`(프로세스 트리째 끔, POSIX 는 감시 프로세스가 실행기가 죽으면 매달린 시험도 — 바쁜 고리든 막힌 대기든 — 끝냄).
   timeout 은 가장 느린 변이의 1.5배 이상(실행기가 경고). 끝나지 않을 수 있는 경로는 **시험 안에서** 따로 돈 프로세스 + 시간 제한으로.
3. **호스트 호출 제한**(예: 원격 셸 호출당 180초·백그라운드 불가): `--budget` ≈ 제한 − timeout − 20초 + `--out` —
   같은 명령이 멈춘 곳부터 잇는다(종료 코드 3 = 다시). 한 호스트에서는 호출을 **차례로** — 동시에 보내면 경합.
4. **패턴은 함수에 묶는다**(`"func": "이름"` 또는 `"클래스.메서드"`) — 파일이 커져도 하나로 남는다. `pattern` 결과는 통과가
   아니라 고장 난 변이 — 다른 수치를 보기 전에 명세부터 고친다.
5. **관문**: survived·pattern·invalid·error 는 늘 실패, `--strict`(마지막 관문)는 timeout·stale(결과 뒤 코드·변이 바뀜)·
   not run·unverified(이 코드로 바탕 시험 없음)도 실패. 종료 코드 0 통과 · 1 실패 · 2 준비 오류 · 3 미완.
   error 는 `--resume` 이 다시 돌리지 않는다 — 고친 뒤 `--only` 로.
6. **준비의 음성 대조**: 변이 전에 시험 명령마다(전역·변이별) 고치지 않은 사본에서 통과하고 실제로 시험이 도는지 먼저 본다
   (아니면 모든 변이가 '잡힘'으로 보임). 결과 파일 하나에 실행기는 하나만(한 번에 한 호스트), `--out`·`--tmp` 는 `--copy` 경로 밖에.
7. **git 이 없으면** 전체 실행 뒤 `--snapshot 폴더` — 다음 `--changed` 의 기준.

판례: drmHWP P-041 은 변이 106개 전체를 차례로 10번 넘게 다시 돌렸고(회당 5~9분) 호스트 제한으로 15~20분을 잃었다.
P-043 에서 같은 106개를 `--jobs 2` 로 약 2배 빠르게, 결과·잡은 시험 모두 같게 돌렸고, 180초 호스트에서는 손 조각 없이 `--budget` 호출로 끝냈다.

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
1. core-engineering: Stage 1~8을 통해 requirements.md, uf.md, evaluation_plan.md 생성
2. ci-evidence-automation: evaluation_plan.md를 기반으로 evidence_pack 스키마 및 CI 워크플로 생성
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
