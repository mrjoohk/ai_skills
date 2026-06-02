# 제작자–비판자(Producer–Critic) 역할 분리 검토

**작성일:** 2026-04-24
**선행 문서:** `pipeline_agent_architecture.md`, `agents.md`
**초점:** 설계/구현 검증 단계에서 산출물을 만드는 에이전트(Producer)와, 그것을 **독립 컨텍스트**에서 비판·평가하는 에이전트(Critic)의 짝이 필요한 지점은 어디인가.

---

## 1. Producer–Critic 패턴의 조건

제작자-비판자 분리는 단순 Verifier 1회 통과보다 강한 보증이 필요할 때만 값을 한다. 세 조건이 모두 성립해야 도입 가치가 있다.

1. **자기편향 리스크가 구조적이다.** 산출물을 만든 에이전트가 같은 컨텍스트에서 자기 결과를 검토하면 "합리화"한다. 설계 의사결정처럼 해답이 여러 개인 문제일수록 큼.
2. **기계적 검증만으로는 부족하다.** `validate_*.py`가 잡는 것은 필드 누락·형식 위반 수준. 의미론적 품질(경계 결정, 임계값 현실성, 예외 누락)은 독립적 판단이 필요.
3. **하류로 전파되면 되돌리기 비싸다.** 잘못된 REQ는 IF·UF·코드·평가까지 오염시킨다. 상류일수록 비판자 비용 대비 이득이 큼.

이 세 조건을 현재 14개 스킬에 적용해 4개 구간으로 나눠 본다.

---

## 2. 현재 파이프라인에서의 검증 포인트 지도

```
 단계                   Producer 스킬            현재 검증                      자기편향 리스크   기계검증으로 충분?   전파비용
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 [Design]
  Stage 1-4 (REQ)       req-elicitor            validate_requirements.py     HIGH             NO                  매우 큼
  Stage 5-6 (IF)        if-designer             validate_if_design.py        HIGH             NO                  큼
  Stage 7   (UF)        uf-designer             validate_uf_design.py +       HIGH             PARTIAL             큼
                                                uf-chain-validator
  Stage 8-plan (eval)   eval-planner            validate_eval_plan.py        HIGH             NO                  큼

 [Implementation]
  impl      (UF code)   uf-implementor          code-reviewer +               MEDIUM           PARTIAL             중간
                                                validate_uf_impl.py
  integrate (IF code)   if-integrator           code-reviewer (공용)          MEDIUM           PARTIAL             중간
  docs      (Cursor)    repo-doc-writer         validate_docs.sh             LOW              YES                 낮음
  prompt    (Cursor)    cursor-task-formatter   (없음)                        LOW              YES                 매우 낮음

 [Run]
  Stage 8-run (metric)  eval-runner             validate_eval_report.py      HIGH             NO                  매우 큼

 [Meta/Side]
  debug                 uf-if-debug-mapper      (자체가 verifier)            LOW              —                   —
  CI                    ci-evidence-automation  (자체가 verifier)            LOW              —                   —
  domain audits         gpu-hpc/sim-physics/rag-data-quality                 LOW              —                   —
```

**판독:**

- **High-bias / 기계검증 부족 / 고전파비용** 조건이 전부 성립하는 지점: **req-elicitor, if-designer, uf-designer, eval-planner, eval-runner**. 이 5개가 Producer–Critic 분리의 1급 대상.
- `code-reviewer`는 이미 critic 포지션을 갖고 있으나, UF 코드용과 IF 통합 코드용을 구분하지 않으며 "리뷰어 서브가 별도 인스턴스"라는 **독립 컨텍스트 보장**이 규정되어 있지 않다. 부분 커버.
- `uf-chain-validator`는 Stage 7.5에 있으나 커버리지/체인 연속성 같은 기계 점검에 머문다. UF 설계의 **의미론적 품질**(알고리즘 선택, 예외 누락, 단위/좌표계 타당성)은 검증하지 않는다.
- `repo-doc-writer`·`cursor-task-formatter`는 입력을 변환만 하는 비의사결정 작업이라 critic이 필요 없다(구조 검증으로 충분).

---

## 3. 단계별 상세 판정

### 3.1 `req-elicitor` → **Critic 필수 (신설)**

**왜 기계검증으로 부족한가.** 현재 `validate_requirements.py`는 REQ Block에 Acceptance Criteria가 있는지, 숫자 임계값이 들어갔는지를 본다. 그러나 다음은 못 잡는다:

- Acceptance Criteria의 **현실성/도전성**(너무 느슨하면 PASS해도 가치 없음, 너무 빡빡하면 구현 불가)
- REQ 간 **충돌**(REQ-003 지연시간 목표와 REQ-007 품질 목표가 양립 불가)
- **누락된 NFR**(보안, 규제, 가용성, 관측가능성)
- **테스트 가능성의 실제 여부**(Given 상황을 현실에서 재현 가능한가)

**Critic 요구사항:**

- 독립 컨텍스트에서 `requirements.md` + `problem_statement.md` + `assumptions_and_constraints.md`만 받고 `clarification_log.md`는 주지 않는다(제작자의 추론 경로 차단).
- 출력: `reports/critique/requirements_critique.md` — severity별 파인딩 + 수정 제안.
- 판정: `APPROVE` / `REQUEST_CHANGES` / `BLOCK`.

**제안 스킬명:** `req-critic` (role: verifier, stage: "1-4-review").

### 3.2 `if-designer` → **Critic 필수 (신설)**

**왜 기계검증으로 부족한가.** `validate_if_design.py`는 IF 블록의 필드 존재 여부, REQ→IF 커버리지를 본다. 그러나:

- IF **경계 결정의 적절성** — 3개로 자르는 게 맞는지, 5개가 맞는지는 의미론적 판단
- **Single Responsibility 위반** — 하나의 IF가 실제로 두 개의 역할을 하는지
- **Failure Mode 완전성** — 나열된 3개 실패모드가 실제로 대표적인가
- **IF 입력/출력 계약이 REQ를 실제로 만족하는가** — 구조적 링크만 체크됨, 계약 내용의 적합성은 미체크

**Critic 요구사항:**

- `requirements.md` + `if_list.md` + `if_decomposition.md`만 받는다.
- 출력: `reports/critique/if_design_critique.md`.
- 특수 점검: "같은 IF를 2–3개로 다르게 자르는 대안을 제시하고 현재 선택의 트레이드오프를 명시"를 요구.

**제안 스킬명:** `if-critic` (role: verifier, stage: "5-6-review").

### 3.3 `uf-designer` → **Critic 필요 (부분 존재)**

**기존.** `uf-chain-validator`(Stage 7.5)가 커버리지·체인 연속성·중복성을 점검. 이것만으로는:

- 알고리즘 선택의 타당성(왜 letterbox resize인가? 다른 방법은?)
- Edge Case 3개가 실제로 **대표적**인가(NaN만 있고 Inf는 빠지지 않았는가)
- I/O 계약의 **단위·좌표계 일관성**(부분적으로 `sim-physics-auditor`가 잡지만 비-시뮬 도메인에선 공백)
- Verification Plan의 실현 가능성(테스트 픽스처 현실성)

**선택지 A — 신설:** `uf-critic` (role: verifier, stage: "7-review").
**선택지 B — 확장:** `uf-chain-validator`를 **기계 점검 모드**와 **비판 모드** 두 개로 분리.

**권장: 선택지 B.** 이유는 `uf-chain-validator`가 이미 스킬 슬롯을 점유하고 있고, 두 모드의 입력이 같으므로 중복 스킬을 늘리기보다 모드 플래그로 확장하는 것이 적절.

```yaml
# uf-chain-validator 수정 예시
modes:
  - id: mechanical    # 기존 동작 (커버리지, 체인, 중복)
    role: verifier
    fanout: none
  - id: critique      # 신설
    role: verifier-critic
    fanout: per-if    # IF 단위로 독립 서브 스폰
    inputs:
      required: [uf.md, if_list.md]
      forbidden: [if_decomposition.md]   # 설계 과정 추적 방지
```

### 3.4 `eval-planner` → **Critic 필수 (신설)**

**자기편향이 특히 위험한 지점.** eval-planner는 스스로 Primary metric을 고르고 Target 임계값을 제안한다. 같은 에이전트가 이걸 검토하면 "내가 정한 값은 합리적"이라는 결론에 수렴. 예시 실패 모드:

- Primary가 **구현 편의** 기준으로 선정됨(계산 쉬운 metric). Domain validity는 낮음.
- Target이 Baseline과 비슷해 **과제의 난이도 은폐**.
- **데이터 누수 리스크** 미점검(같은 코퍼스에서 train/test split).
- **Diagnostic metric 누락**으로 실패 원인 분석 불가.

**Critic 요구사항:**

- `evaluation_plan.md` + `requirements.md` + `uf.md`를 입력.
- 도메인 기본 metric 레퍼런스(`eval-planner/references/reference.md`)와 **독립적으로** 교차 비교.
- 출력: 각 metric에 대해 `KEEP / REPLACE / ADD / REMOVE` 판정.
- 통계 검정력 분석(N 필요량, p-value 기준, 효과크기)을 별도 섹션으로 요구.

**제안 스킬명:** `eval-plan-critic` (role: verifier, stage: "8-plan-review").

### 3.5 `uf-implementor` + `if-integrator` → **Critic 존재 (code-reviewer), 분화 필요**

**현재.** `code-reviewer`가 범용 critic으로 작동. 3-lens(Contract Compliance, Logic Correctness, Code Quality)로 본다.

**문제:**

- UF-level과 IF-level 리뷰 기준이 다름에도 같은 스킬이 커버
  - UF: 단일 책임, I/O 계약 엄격 준수, 엣지 케이스
  - IF: 오케스트레이션 정확성, 후조건 보장, 예외 전파, REQ 충족
- **독립 컨텍스트 보장 조항이 없다.** 서브에이전트로 돌리는 것이 스킬 규격에 적혀 있지 않다.
- 파인딩 병합 프로토콜 부재(파일별 팬아웃 시 ID 충돌 가능).

**수정안:**

- `code-reviewer`에 **`review_layer`** 필드 추가(`uf` | `if` | `generic`). 레이어별 체크리스트를 `references/review_criteria_<layer>.md`로 분리.
- **독립성 계약**(§5)을 SKILL.md 규칙 절에 명시.
- IF-레이어 리뷰 시 `if_list.md`의 acceptance criteria를 추가 입력으로 요구.

별도 스킬(`uf-code-critic`, `if-code-critic`)로 쪼개는 것은 과설계. 단일 스킬 + 모드로 충분.

### 3.6 `eval-runner` → **Critic 필수 (신설, 최우선)**

**Producer–Critic 분리가 가장 중요한 지점.** eval-runner는 "성공/실패"를 선언한다. 같은 에이전트가 결과 해석까지 맡으면 다음이 발생:

- 계산 오류 자기검출 실패(단위 환산 누락, aggregation 평균/중앙값 혼용)
- **통계적 취약점 누락**(샘플 n=10 기반 결론, CI 미계산)
- **confound 무시**(seed 고정 안 함, 하이퍼파라미터 차이 누락)
- **승/패 편향 해석**(목표값에 근접한 값을 "달성"으로 처리)

**Critic 요구사항:**

- `reports/eval/<task>_<timestamp>.md` + `evidence_pack/metrics.yaml` + `evaluation_plan.md` + `scripts/eval/*.py` 를 독립 서브로 받는다.
- 점검 항목: (1) 계산 스크립트와 metric 정의 일치성 재확인, (2) 통계 유의성 계산, (3) confound 체크리스트, (4) 임계값 대비 PASS/FAIL의 재판정.
- 출력: `reports/critique/eval_result_critique.md` — 각 metric에 대한 "측정값/통계유의성/판정" 독립 재판정.

**제안 스킬명:** `eval-result-critic` (role: verifier, stage: "8-run-review").

### 3.7 `repo-doc-writer`, `cursor-task-formatter` → **Critic 불필요**

- 입력을 포맷 변환하는 결정 없는 작업.
- 구조 검증(`validate_docs.sh`) + 사람 눈검으로 충분.
- Critic 도입 시 과설계.

### 3.8 도메인 감사 스킬 3종 → **이미 Critic 성격**

`gpu-hpc-guard`, `sim-physics-auditor`, `rag-data-quality`는 각 도메인의 **전문 critic**. 역할 변경 불필요. 단, 현재 훅 지점이 흐릿하므로 `agents.md`의 `domain_auditors` 절에서 **어느 Producer의 결과를 비판하는지** 1:1 맵을 명시할 것(이미 v1 초안에 `hook_after` 필드로 반영됨).

---

## 4. 종합: 신설/수정 필요 스킬 목록

| 우선순위 | 스킬 | 유형 | 대상 Producer | 단계 |
|:---:|---|---|---|---|
| **P0** | `req-critic` | 신설 | req-elicitor | 1-4-review |
| **P0** | `eval-result-critic` | 신설 | eval-runner | 8-run-review |
| **P1** | `if-critic` | 신설 | if-designer | 5-6-review |
| **P1** | `eval-plan-critic` | 신설 | eval-planner | 8-plan-review |
| **P1** | `uf-chain-validator` | **모드 확장** (mechanical + critique) | uf-designer | 7/7.5 |
| **P1** | `code-reviewer` | **review_layer 필드 추가** | uf-implementor, if-integrator | impl/integrate-review |

**우선순위 근거:**

- **P0 두 건** = 파이프라인의 가장자리(입력 REQ, 최종 결과). 여기 오류가 나면 전체가 뒤집힘.
- **P1 네 건** = 중간 단계. P0만큼 치명적이지 않고 downstream에서 일부 보완 가능.

---

## 5. Critic 에이전트 공통 규격 (신설/확장 스킬 모두 준수)

모든 critic 스킬의 `SKILL.md` 프런트매터에 아래 블록을 추가한다.

```yaml
critic_contract:
  independence:
    isolation: "spawn_in_fresh_subagent"         # 제작자와 다른 컨텍스트로만 실행
    forbidden_inputs:                             # 제작자 추론과정 차단
      - "*.log"
      - "clarification_log.md"                    # req-critic에만 적용
      - "if_decomposition.md"                     # uf-chain-validator critique 모드
    allowed_inputs_summary: "최종 산출물 + 이를 해석하는 데 필요한 상류 계약만"

  judgment:
    verdict_enum: [APPROVE, REQUEST_CHANGES, BLOCK]
    finding_format:
      id: "CRIT-<stage>-<N>"
      severity: [CRITICAL, WARN, SUGGEST]
      fields: [what, why, fix, affected_artifact]

  bias_guards:
    require_alternatives: true                    # "현재 선택 외 2개 대안 제시"
    require_statistical_rigor: false              # eval-* critic만 true
    reject_self_justification: true               # 제작자 근거를 인용하지 말 것

  output:
    path: "reports/critique/<stage>_critique_<timestamp>.md"
    json_trailer: true                            # handoff JSON 표준(§6.2) 준수
```

**핵심 계약 5가지:**

1. **독립 컨텍스트.** Critic 서브에이전트는 Producer와 다른 프로세스/대화에서 호출. 컨텍스트 공유 금지.
2. **입력 화이트리스트.** 최종 산출물 + 상류 계약 문서만. Producer의 중간 결과(로그, 드래프트, Q&A)는 차단.
3. **대안 강제 제출.** Critic은 현재 결정 외 최소 2개의 대안을 제시하고 현 선택의 트레이드오프를 설명해야 한다. (설계 단계 critic 한정)
4. **판정 3단.** `APPROVE`(이대로 진행), `REQUEST_CHANGES`(수정 후 재제출), `BLOCK`(파이프라인 중단·에스컬레이션).
5. **자기정당화 거부.** Producer가 제공한 이유를 그대로 인용해 "타당하다"고 결론 내지 말 것. 외부 레퍼런스(스킬의 `references/`, 공개 벤치마크)와 교차.

---

## 6. `agents.md` 업데이트 초안

아래 블록을 기존 `agents.md`의 **Pipeline State Machine 직전**에 추가한다.

```yaml
critics:
  - skill: req-critic                     # 신설
    role: verifier
    critic_of: req-elicitor
    hook_after: "architect/req-elicitor.status == COMPLETE"
    blocks_downstream: true               # REQUEST_CHANGES 시 if-designer 진입 금지

  - skill: if-critic                      # 신설
    role: verifier
    critic_of: if-designer
    hook_after: "architect/if-designer.status == COMPLETE"
    blocks_downstream: true

  - skill: uf-chain-validator             # 모드 확장
    role: verifier
    modes: [mechanical, critique]
    critic_of: uf-designer                # critique 모드에 한함
    hook_after: "architect/uf-designer.status == COMPLETE"
    blocks_downstream: true               # critique FAIL 시 구현 진입 금지

  - skill: eval-plan-critic               # 신설
    role: verifier
    critic_of: eval-planner
    hook_after: "architect/eval-planner.status == COMPLETE"
    blocks_downstream: false              # eval은 실행 후 재평가 가능

  - skill: code-reviewer                  # 레이어 필드 추가
    role: verifier
    modes: [uf_layer, if_layer, generic]
    critic_of_map:
      uf_layer: uf-implementor
      if_layer: if-integrator
    hook_after:
      - "builder/uf-implementor.status == COMPLETE → use uf_layer"
      - "builder/if-integrator.status == COMPLETE → use if_layer"
    blocks_downstream: false              # 파인딩은 cursor-task-formatter Mode B로 루프

  - skill: eval-result-critic             # 신설
    role: verifier
    critic_of: eval-runner
    hook_after: "verifier/eval-runner.status == COMPLETE"
    blocks_downstream: true               # 통계적 결함은 성과 선언 차단
    extras:
      require_statistical_rigor: true
```

---

## 7. 우회하지 말아야 할 설계 원칙

Producer–Critic을 도입하면서 실수하기 쉬운 지점:

1. **Critic을 옵션으로 두지 말 것.** `blocks_downstream`이 `true`인 critic은 기본 활성. 꺼야 한다면 `context.json.config`에서 명시적으로 꺼야 한다.
2. **Critic 출력이 Producer에 되먹임되는 경로를 선형으로.** `REQUEST_CHANGES` 시 Producer가 수정 → 다시 Critic, 순환 2회 초과 시 자동 에스컬레이션(사용자 중재).
3. **Critic이 설계를 대신 하지 않게.** Critic이 대안을 제시하되 직접 산출물을 쓰는 것은 금지. 수정은 Producer의 역할. (쓰기 스코프 §4에서 verifier는 `reports/**`만 허용하도록 이미 제한.)
4. **"Critic이 Critic을 만든다" 금지.** Critic 리포트에 대한 2차 리뷰는 하지 않는다. 필요하면 사용자 중재.
5. **모든 Critic은 동일한 handoff JSON 스키마.** `verdict`, `findings[]`, `alternatives[]`, `next_action` 필드 고정.

---

## 8. 즉시 취할 수 있는 다음 행동

선택지 4가지 중 고르면 이어서 진행합니다:

- **A. `req-critic` PoC 작성** — 신설 스킬의 `SKILL.md` + `references/critic_criteria.md` + validation 스크립트 뼈대.
- **B. `uf-chain-validator`의 모드 확장 패치** — 기존 스킬에 `critique` 모드 추가하고 `agents.md` 갱신.
- **C. `code-reviewer`의 `review_layer` 필드 도입** — 기존 스킬 수정 + `references/review_criteria_uf.md`, `_if.md` 분리.
- **D. Critic 공통 계약 문서 작성** — §5를 별도 `references/critic_contract.md`로 추출해 모든 critic 스킬이 참조하게 함.

권장 순서: **D → A → B → C**. 공통 계약(D)을 먼저 못 박고, 가장 고위험(A: REQ 오류), 가장 저비용(B: 모드 확장), 마지막으로 구조 변경(C) 순.
