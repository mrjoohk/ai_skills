# theory-decomposer — Examples

---

## Example 1 — Quadrotor 6-DOF dynamics (verdict: FOUND-CODE)

**Prompt:**
```
/theory-decomposer
이론: 쿼드로터 6-DOF 강체 동역학. 상태벡터 [p, v, R, ω], 입력은 로터 4개 각속도.
domain_hint: dynamics, max_depth: 3
목표: uf-implementor가 바로 구현 가능한 eq.md와 theory_tree.md 생성.
```

**Expected flow (abbreviated):**

- **T0** → `source_survey.md`: PX4/jMAVSim, RotorPy 등 발견 → verdict **FOUND-CODE**
  → 검증 모드: 머지 결과를 참조 시뮬레이터와 교차 검증 (hover, step-yaw 시나리오)
- **T1** → frames 고정: inertial NED / body FRD, SI 단위, 표기표
- **T2** → 분해 + 정지 판정:
  ```
  TH-00 쿼드로터 6-DOF
  ├── TH-01 강체 병진
  │   ├── EQ-01-01 뉴턴 제2법칙 (inertial)      ATOMIC (S1–S4 ✓)
  │   └── EQ-01-02 중력                         ATOMIC
  ├── TH-02 강체 회전
  │   └── EQ-02-01 오일러 방정식 (body)          ATOMIC
  ├── TH-03 로터 모델
  │   ├── EQ-03-01 추력 T = k_f·Ω²               ATOMIC
  │   └── EQ-03-02 반토크 τ = k_m·Ω²             ATOMIC
  └── (T3.5 추가) EQ-00-01 회전행렬 R (body→inertial)   — CHAIN BREAK fix
      (T3.5 추가) EQ-00-02 자이로 항 ω×Jω               — UNCOVERED fix
  ```
- **T3** → 각 leaf를 EQ Block으로. 예: EQ-02-01 Source: "Goldstein, Classical
  Mechanics 3rd ed., Eq. (5.39)"; Assumptions: rigid body, constant J; Edge case: ω×Jω
  singular-free but stiff at high |ω|.
- **T3.5** → 게이트가 두 건 검출:
  1. `CHAIN BREAK`: EQ-03-01 추력은 body frame, EQ-01-01 은 inertial → EQ-00-01 (R) 삽입
  2. `UNCOVERED`: "고속 요잉 중 피치 시 세차 거동"이 어느 하위이론에도 없음 → EQ-00-02 (ω×Jω) 추가
  → 재검사 후 Gate PASS
- **Handoff** → uf-implementor(eq.md) → if-integrator(theory_tree.md) →
  sim-physics-auditor → eval-runner (PX4 교차 검증)

이 예시는 아이디어의 핵심 리스크 2건(프레임 불일치, 결합항 누락)이 게이트에서 실제로
잡히는 것을 보여준다.

---

## Example 2 — Novel coupled system, no reference (verdict: NONE)

**Prompt:**
```
/theory-decomposer
이론: 신규 견인식 소나 배열의 케이블-배열 연성 동역학 (자체 개발 형상, 공개 코드 없음).
domain_hint: dynamics, max_depth: 4
```

**Expected flow (abbreviated):**

- **T0** → 검색 결과 참조 구현·벤치마크 없음 → verdict **NONE**
  → oracle 구성: ① 에너지 보존 (무감쇠 극한), ② 극한 케이스 (케이블 강성→∞ 시 강체
  견인 모델로 환원, 예인속도→0 시 현수선 정적해), ③ 차원 분석, ④ 대칭성
- **T2** → 케이블 동역학(현수선+장력파) / 배열 강체 운동 / 유체 항력 으로 분해,
  각 leaf는 교과서 인용 가능 수준(S2)까지만 분해. depth 4 초과 노드 → WARN 후 재병합
- **T3.5** → `INCOMPATIBLE` 검출 예: 케이블 블록 A1(비신축) vs 장력파 블록 A1(탄성)
  → 해결: bridging 없이 유효범위 분할(저주파 모드=비신축, 고주파=탄성) 선택, 판단 근거 기록
- **eval-planner 연계** → NONE 모드 oracle 4종을 지표로 등록, eval-runner가 수치 검증

---

## Example 3 — Trigger-only smoke test

**Prompt:** "레이더 신호 모델 수식 유도해줘. 오픈소스는 없는 것 같아."

**Expected:** 스킬 트리거 → T0부터 시작 (사용자의 "없는 것 같아"를 그대로 믿지 않고
검색으로 확인 후 verdict 기록) → 이후 T1–T3.5 진행.
