# exp-runner — 한국어 사용 가이드

## 왜 필요한가

기존 파이프라인은 eval-planner(계획 수립)와 eval-runner(지표 계산·리포트) 사이에
**실험을 실제로 실행하는 주체가 없었다.** eval-runner의 입력인 "실험 결과 데이터"를
누가 만드는지 미정이었고, 재현성 규칙(동일 데이터셋·스플릿·시드)을 강제하는 스킬도
없었다. exp-runner가 그 공백을 메운다.

```
eval-planner → exp-runner → eval-runner → ci-evidence-automation
 (계획)        (실행+기록)     (지표·리포트)     (CI·회귀)
```

## 하는 일

1. `rd/evaluation_plan.md`를 읽어 실행 매트릭스 구성 (실험 × 데이터셋 × 시드)
2. 실행 전 환경 동결: `evidence_pack/env.yaml` (버전·하드웨어·commit_sha)
3. 시나리오별 실행, 원시 산출물을 `results/<exp_id>/`에 보존 (실패도 기록)
4. 실행 이력(provenance)을 `evidence_pack/runs.yaml`에 기록
5. eval-runner로 핸드오프 (FAILED 런은 집계 제외)

## 진입 게이트

- `rd/evaluation_plan.md` 없으면 실행 거부 → eval-planner 먼저 (무계획 실행은 eval-runner의 UNPLANNED 모드 소관)
- 통합 리포트에 `INTERFACE_ERROR`/`PARTIAL` 있으면 실행 거부 (Gate G3) → 디버그 먼저

## 사용법

```
/exp-runner
rd/evaluation_plan.md 기준으로 baseline과 proposed를 시드 3개로 실행하고
runs.yaml에 기록해줘. 진입점은 src/if/pipeline.py.
```

## 핵심 규칙

시드·데이터셋·커맨드는 그대로(verbatim) 기록, run_id 재사용 금지(재실행은 Exp-01b),
비교 실험 간 시드 셋 불일치 시 실행 거부, 실패도 증거로 보존.
