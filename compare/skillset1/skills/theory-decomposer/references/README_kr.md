# theory-decomposer — 한국어 사용 가이드

## 무엇을 하는 스킬인가

도메인 오픈소스 코드가 없어도(또는 있는지 불확실해도) 이론을 작은 이론으로 반복
분해하고, 각 하위이론의 수식을 EQ Block으로 작성한 뒤 연동·머지하여 **원래 이론의
수식·동역학을 재구성**하는 스킬. core-engineering 파이프라인의 소프트웨어 분해 원리
(시스템→IF→UF→상향 통합)를 이론·수식 수준에 적용한 프론트엔드다.

```
T0 소스 가용성 검사 → T1 이론 정의 → T2 깊이 기준 분해 → T3 EQ Block → T3.5 연동 게이트
→ (기존 파이프라인) uf-implementor → if-integrator → sim-physics-auditor → eval-runner
```

## 핵심 설계 3가지

1. **T0가 맨 앞** — 오픈소스·벤치마크 존재 여부를 먼저 검색해 verdict
   (`FOUND-CODE` / `FOUND-BENCH` / `NONE`)를 내리고, 이 판정이 최종 검증 방식을 결정한다.
   `NONE`이어도 진행 가능: 보존법칙·극한케이스·차원분석·대칭성이 오라클이 된다.
2. **분해 깊이 기준 S1~S4** — ① 단일 수식, ② 출처 1건 인용 가능, ③ 단독 검증 가능,
   ④ 추가 분해로 새 가정이 분리되지 않음 — 4개 모두 만족 시 정지(ATOMIC).
   기본 깊이 상한 `max_depth=4`, 초과 시 과분해 경고.
3. **T3.5 연동 게이트** — 단위·차원·좌표계 연속성, 가정 호환성 매트릭스,
   결합항 커버리지(보존법칙·극한케이스로 누락 교차항 탐지), 유효범위 교집합.
   `UNCOVERED`/`INCOMPATIBLE`이 남아 있으면 구현 단계 진입 금지.

## 사용법

```
/theory-decomposer
이론: [이론/현상 설명, 상태변수와 입력]
domain_hint: dynamics   (선택)
max_depth: 4            (선택)
```

산출물 (GLOBAL_RULES Rule 9에 따라 `rd/`에 저장):

| 파일 | 내용 | 소비 스킬 |
|---|---|---|
| `rd/source_survey.md` | T0 검색 증거 + verdict | eval-planner/runner (오라클 정의) |
| `rd/theory_statement.md` | 이론 범위, 표기·단위·좌표계 규약 | — |
| `rd/theory_tree.md` | 분해 트리 + 정지 판정 + 결합 엣지 | if-integrator |
| `rd/eq.md` | EQ Block (UF Block 확장: 수식·가정·유효범위·출처) | uf-implementor |
| `rd/eq_coverage_review.md` | 연동 게이트 결과 (PASS 필요) | uf-implementor 진입 게이트 |

## 왜 그냥 머지하면 안 되는가 (이 스킬이 막는 3가지 함정)

1. **가정 비호환**: 타입·단위가 맞아도 가정이 충돌하면(강체 vs 유연체) 결과가 조용히
   틀림 → 가정 호환성 매트릭스.
2. **결합항 누락**: 상향 머지는 하위이론 어디에도 없는 교차항(Coriolis, ω×Jω,
   다물리 연성)을 놓침 → 보존법칙·극한케이스 커버리지 검사.
3. **수식 환각**: 출처 없는 수식 생성 위험 → 모든 EQ Block에 Source 필수(S2),
   출처가 사라질 만큼 잘게 쪼개는 것 자체를 금지.

## 기존 스킬과의 연동

- `eq.md`는 UF Block 문법의 상위집합 → `uf-implementor`가 수정 없이 소비
  (수식 1개 → 함수 1개 + 유효범위 가드 + 검증 계획 기반 단위 테스트)
- `theory_tree.md`는 `if_decomposition.md` 포맷 → `if-integrator`가 결합 엣지를
  호출 그래프로 읽어 동역학 모듈로 머지
- EQ Block의 수식·가정·파라미터 범위는 `sim-physics-auditor`의 입력 형식과 일치
- 전체 체인: theory-decomposer → uf-implementor → if-integrator →
  sim-physics-auditor + uf-chain-validator → eval-planner → eval-runner →
  ci-evidence-automation (워크플로 G)
