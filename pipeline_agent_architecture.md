# 설계/구현 파이프라인 — 메인/서브에이전트 전환 분석 및 제안

**작성일:** 2026-04-24
**대상 스킬군:** core-engineering, req-elicitor, if-designer, uf-designer, uf-chain-validator, uf-implementor, if-integrator, eval-planner, eval-runner, code-reviewer, cursor-task-formatter, repo-doc-writer, uf-if-debug-mapper, ci-evidence-automation, project-summarizer (+ 도메인 감사 스킬: gpu-hpc-guard, sim-physics-auditor, rag-data-quality)

---

## 1. 결론 요약 (TL;DR)

| 질문 | 답 |
|---|---|
| 메인/서브에이전트 패턴이 적합한가? | **예, 매우 적합** |
| 지금 바로 전환 가능한가? | 부분적으로 가능. 명세 표준화와 핸드오프 포맷 정규화가 선행되어야 함 |
| 가장 큰 이득은 무엇인가? | 컨텍스트 격리(토큰 절감), 병렬 팬아웃(UF/IF 단위), 검증-구현 분리, 실패 국지화 |
| 가장 큰 장애물은 무엇인가? | Human-in-the-loop 단계(req-elicitor Phase B, eval-planner Step 3), 비표준 I/O 선언, 검증 스크립트 출력이 사람 전용 |
| 무엇부터 고쳐야 하는가? | (1) 모든 파이프라인 스킬에 `pipeline:` 프런트매터 추가, (2) 핸드오프 메시지를 JSON으로 표준화, (3) `agent-orchestration` 스킬 신설, (4) 검증 스크립트 JSON 이중 출력 |

---

## 2. 현재 파이프라인 구조 (정방향 흐름)

```
[User Problem]
    ↓
 req-elicitor  ──▶  problem_statement.md, clarification_log.md,
    │                assumptions_and_constraints.md, requirements.md
    ↓
 if-designer   ──▶  if_list.md, if_decomposition.md
    ↓
 uf-designer   ──▶  uf.md
    ↓
 uf-chain-validator ──▶ uf_if_coverage_review.md   (Stage 7.5, gate)
    ↓
 uf-implementor ──▶ src/uf/*.py, tests/unit/*.py, uf_impl_report.md
    ↓
 if-integrator ──▶ src/if/*.py, tests/integration/*.py, if_integration_report.md
    ↓
 eval-planner  ──▶ evaluation_plan.md
    ↓
 eval-runner   ──▶ scripts/eval/*.py, reports/eval/*.md, evidence_pack/metrics.yaml
```

**사이드 체인 (병렬/선택적):**

- `repo-doc-writer`   : 설계 산출물 → `docs/ai/overview.md`, `docs/ai/tasks/<UF_ID>.md`, `docs/ai/architecture.md` (Cursor용 컨텍스트)
- `cursor-task-formatter` : `uf.md` 또는 리뷰 파인딩 → Cursor Composer 프롬프트(UF별/파인딩별)
- `code-reviewer`      : 구현 코드 → 리뷰 파인딩 리포트
- `uf-if-debug-mapper` : UF/IF + 리포 트리 → `docs/uf_if_debug_map.md`
- `ci-evidence-automation` : 테스트 결과 → Evidence Pack
- 도메인 감사 3종(`gpu-hpc-guard`, `sim-physics-auditor`, `rag-data-quality`) : 각 단계 산출물에 오버레이

---

## 3. 메인/서브에이전트 패턴 적합성 분석

### 3.1 적합한 이유

**① 강한 I/O 계약 (Strong Contracts).**
각 스킬은 "읽는 파일 목록"과 "쓰는 파일 목록"이 이미 선언되어 있음. `req-elicitor → if-designer → uf-designer → uf-implementor` 체인은 산출물-인자 짝이 빡빡하게 매칭되며, 이는 에이전트 분해의 전제조건이다.

**② 컨텍스트 격리 수요.**
`uf-implementor`는 `uf.md`만 있으면 되고, `clarification_log.md`·`problem_statement.md`를 전혀 읽을 필요가 없다. 현재 메인 에이전트가 전부 들고 있는 컨텍스트를 서브에이전트로 국지화하면 토큰 사용량과 노이즈가 모두 줄어든다.

**③ 자연스러운 팬아웃.**
- `uf-implementor`: IF별 또는 UF 묶음별 병렬 실행 가능
- `cursor-task-formatter`: UF Block 하나당 프롬프트 하나 → 전형적인 map-parallel
- `code-reviewer`: 파일 단위 병렬 리뷰
- `repo-doc-writer`: UF별 task 파일 생성 병렬화

**④ 기존 스킬이 이미 암시하고 있음.**
- `core-engineering/SKILL.md`의 "Skill Integration" 표 마지막 행에 `agent-orchestration` 스킬이 언급되어 있으나 구현되어 있지 않음.
- `uf-if-debug-mapper/SKILL.md`는 "Agent-1 (Architect) / Agent-2 (Builder) / Agent-3 (Verifier)" 3역할 모델을 이미 언급.
- 즉 이 스킬 수트는 처음부터 멀티에이전트 운용을 전제로 설계되었으나 오케스트레이션 레이어만 빠진 상태이다.

**⑤ 재시도·실패 국지화.**
서브에이전트가 실패하면 해당 단계만 재시도하면 되며, 메인 에이전트의 대화 맥락은 보존된다. 현재 모놀리식 흐름에서는 파이프라인 중간 실패 시 전체 맥락이 오염된다.

### 3.2 순수 서브에이전트화가 **부적합한 지점**

| 단계 | 이유 | 처리 방식 |
|---|---|---|
| `req-elicitor` **Phase B (Clarification)** | 사용자에게 4–8개 질문을 던지고 답을 기다려야 함 | `human_in_loop: true`로 플래그, 메인에이전트가 직접 처리 후 답변을 Phase C로 위임 |
| `eval-planner` **Step 3 (Threshold Target 확정)** | Baseline은 자동, Target은 사용자 확인 필요 | 동일 — 메인에이전트에서 `[NOTE: confirm]` 수집 후 위임 재개 |
| 설계 단계의 **설계 의사결정 충돌** | IF 경계를 어떻게 자를지 등은 사용자 의견 필요 | Clarification escalation 프로토콜 필요 |

### 3.3 정량적 기대 효과 (추정)

| 지표 | 현재 (모놀리식) | 제안 (메인/서브) | 비고 |
|---|---:|---:|---:|
| 평균 컨텍스트 크기 | 전체 산출물 누적 | 단계별 필요 파일만 | 30–70% 감축 예상 |
| UF 구현 시간 (5 IF × 4 UF 기준) | 순차 | IF 단위 병렬 | 3–4배 단축 |
| 실패 재시도 비용 | 전체 재실행 위험 | 실패 서브만 | 큼 |
| 리뷰 정확도 | 설계자=리뷰어 (편향) | 역할 분리 (verifier 독립) | 정성적 개선 |

---

## 4. 에이전트 역할 모델 (3-Role Architecture)

`uf-if-debug-mapper`가 이미 힌트한 3역할 모델을 전체 파이프라인에 일반화한다.

### Architect (설계자)
**책임:** 사용자 문제 → 기계 판독 가능한 설계 산출물(.md)을 생성.
**소속 스킬:** `req-elicitor`, `if-designer`, `uf-designer`, `eval-planner`
**특성:** 쓰기 권한 제한(설계 문서 경로만). Human-in-loop 지점을 가질 수 있음. 출력은 항상 마크다운 + 검증 스크립트 결과.

### Builder (구현자)
**책임:** 설계 산출물 → 코드/문서/프롬프트로 변환.
**소속 스킬:** `uf-implementor`, `if-integrator`, `repo-doc-writer`, `cursor-task-formatter`
**특성:** 팬아웃 가능(IF/UF/파일 단위). 쓰기 권한은 `src/`, `tests/`, `docs/ai/` 등 구현 경로. Human-in-loop 없음.

### Verifier (검증자)
**책임:** 산출물(설계/코드/결과)의 일관성·커버리지·계약 준수 점검.
**소속 스킬:** `uf-chain-validator`, `code-reviewer`, `eval-runner`, `uf-if-debug-mapper`, `ci-evidence-automation`
**특성:** 읽기 전용 또는 리포트 경로로만 쓰기. 결과는 PASS/FAIL + 파인딩 리스트. Architect/Builder와 독립적인 서브에이전트로 돌려야 리뷰 편향을 차단.

**도메인 감사 스킬** (`gpu-hpc-guard`, `sim-physics-auditor`, `rag-data-quality`)은 Verifier의 서브타입이며, 프로젝트 유형에 따라 선택적으로 훅.

**주관자(Orchestrator) = 메인에이전트**는 별도 스킬 `agent-orchestration`(신설 제안)이 담당하며, `agents.md`를 읽어 라우팅.

---

## 5. 표준 명세 (Standardized Spec)

모든 파이프라인 스킬이 `SKILL.md` 프런트매터에 아래 `pipeline:` 블록을 추가해야 오케스트레이션이 기계적으로 가능하다.

```yaml
---
name: <skill-name>
description: "<기존 설명 유지>"
allowed-tools: Read, Write

pipeline:
  role: architect | builder | verifier
  stage: "<stage-id, 예: 1-4, 5-6, 7, 7.5, 8, impl, integrate, review, docs, prompt>"

  inputs:
    required:
      - path: "<파일 경로 또는 glob>"
        producer: "<선행 스킬 이름>"
    optional:
      - path: "<파일 경로>"
        producer: "<선행 스킬>"

  outputs:
    files:
      - path: "<상대 경로>"
        kind: "design | code | test | report | prompt"
    status_enum: [COMPLETE, PARTIAL, BLOCKED]

  human_in_loop:
    required: true | false
    phases: ["<Phase B>", ...]   # true일 때만

  fanout:
    strategy: none | per-uf | per-if | per-file | per-finding
    max_parallel: <정수>

  validator:
    script: "<skill_dir>/scripts/validate_*.py"
    json_output: true   # 아래 §6 참조

  downstream:
    - next: "<스킬 이름>"
      when: "status == COMPLETE && no_blockers"
---
```

**핵심 규칙 5가지:**

1. **`inputs.required`에 적힌 파일이 없으면 스킬은 즉시 `BLOCKED` 상태로 종료하며, 메인에이전트에게 선행 스킬 실행을 요청한다.** 암묵적 생성 금지.
2. **모든 출력 파일은 선언된 경로에만 생성.** 경로 밖 쓰기는 에러.
3. **Human-in-loop이 `true`인 스킬은 서브에이전트로 직접 위임 불가.** 메인에이전트가 해당 Phase만 실행하고 이후 단계를 서브에이전트로 위임.
4. **검증 스크립트는 사람용 출력 외에 `stdout` 마지막 라인에 `RESULT_JSON={...}` 한 줄을 추가.** 오케스트레이터는 이 라인만 파싱.
5. **`downstream.next`가 여러 개면 조건절(`when`)이 필수.** 라우팅 결정을 기계적으로.

---

## 6. 핸드오프 포맷 표준화

### 6.1 현재 문제

- `req-elicitor`는 마지막에 "✅ Stages 1–4 complete. Output files: ..." 같은 자연어 메시지로 끝남.
- `uf-implementor`는 타임스탬프 파일명(`uf_impl_report_<timestamp>.md`)을 쓰는데 오케스트레이터가 어떻게 찾을지 불명확.
- 검증 스크립트들은 사람용 출력만 생성.

### 6.2 표준 핸드오프 블록

모든 파이프라인 스킬이 실행 종료 시 아래 JSON 블록을 출력한다(사람용 요약 뒤에 펜스 코드 블록으로):

```json
{
  "skill": "req-elicitor",
  "version": "1.0",
  "status": "COMPLETE",
  "outputs": [
    {"path": "problem_statement.md", "kind": "design", "sha256": "..."},
    {"path": "requirements.md", "kind": "design", "sha256": "..."}
  ],
  "metrics": {
    "req_count": 12,
    "unresolved_count": 0
  },
  "unresolved": [],
  "next_candidates": ["if-designer"],
  "validator": {
    "script": "scripts/validate_requirements.py",
    "passed": true,
    "findings": []
  },
  "resume_token": "<opaque id — 재시작 시 이 토큰으로 복구>"
}
```

`status`가 `PARTIAL`인 경우 `unresolved`에 구체적 차단 사유(예: `"REQ-004 missing acceptance threshold"`)와 에스컬레이션 대상(`"ask_user"` 또는 `"retry:uf-designer"`)을 명시.

### 6.3 Context Bundle (공유 상태)

프로젝트 루트에 `.pipeline/context.json`을 두어 메인/서브가 공유:

```json
{
  "project_root": ".",
  "current_stage": "uf-implementor",
  "completed_stages": ["req-elicitor", "if-designer", "uf-designer", "uf-chain-validator"],
  "artifacts": {
    "requirements.md": {"sha256": "...", "produced_by": "req-elicitor"},
    "uf.md": {"sha256": "...", "produced_by": "uf-designer"}
  },
  "open_issues": [
    {"id": "UF-02-03", "status": "STUB", "blocking": true}
  ],
  "config": {
    "language": "ko",
    "impl_lang": "python",
    "run_cursor_integration": true
  }
}
```

서브에이전트는 호출 시 이 파일을 **가장 먼저** 읽고, 종료 시 자신이 만든 산출물을 `artifacts`에 append. 오케스트레이터가 `current_stage` 전이를 담당.

---

## 7. 프로세스: agents.md → 다음 단계 스킬 위임

### 7.1 실행 루프

```
┌─────────────────────────────────────────────────────────┐
│ Main Agent (Orchestrator, using agent-orchestration)    │
│                                                          │
│  1. Load agents.md                                      │
│  2. Load .pipeline/context.json                         │
│  3. Determine next skill via context.current_stage      │
│     + downstream rules                                  │
│  4. If skill.human_in_loop: execute Phase inline        │
│     Else: spawn sub-agent with:                         │
│        - Skill SKILL.md                                 │
│        - Declared inputs.required files                 │
│        - Context bundle (read-only)                     │
│        - Assigned outputs.files paths (write-scope)     │
│  5. Parse handoff JSON from sub-agent                   │
│  6. Validate artifacts (hash, validator script JSON)    │
│  7. Update .pipeline/context.json                       │
│  8. Loop 3–7 until pipeline ends or user intervention   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 팬아웃 예시 (uf-implementor, per-IF 병렬)

```
Orchestrator reads uf.md
  → splits UFs by parent IF (IF-01, IF-02, IF-03)
  → spawns 3 builder sub-agents in parallel:
     sub-1: uf-implementor(scope=IF-01) → src/uf/if_01_*.py
     sub-2: uf-implementor(scope=IF-02) → src/uf/if_02_*.py
     sub-3: uf-implementor(scope=IF-03) → src/uf/if_03_*.py
  → collects 3 handoff JSONs
  → merges into aggregate uf_impl_report
  → spawns verifier sub-agent: uf-chain-validator(inputs=[uf.md, src/uf/])
  → on PASS: transitions to if-integrator
```

### 7.3 Human-in-loop 우회 프로토콜

```
req-elicitor.Phase_B (Clarification) 진입
  ↓
Orchestrator pauses sub-agent spawn
  ↓
Main Agent asks user 4–8 questions (AskUserQuestion tool)
  ↓
Answers written to clarification_log.md
  ↓
Orchestrator resumes: spawns req-elicitor sub-agent with
  clarification_log.md as additional input, limiting scope to Phase C–E
```

---

## 8. 스킬 수정안 (구체적 패치 목록)

우선순위별로 정리. **P0 = 서브에이전트 전환 전에 반드시 필요**, **P1 = 전환 후 즉시 가치**, **P2 = 장기 개선**.

### P0 — 전환 전 필수

| # | 대상 | 변경 내용 |
|---|---|---|
| P0-1 | **모든 파이프라인 스킬** | §5의 `pipeline:` 프런트매터 블록 추가. 현재는 `name`/`description`/`allowed-tools`만 있음 |
| P0-2 | **모든 파이프라인 스킬** | §6.2의 핸드오프 JSON 블록을 실행 말미에 출력하도록 `## Execution`에 단계 추가 |
| P0-3 | **`validate_*.py` 전체** (req-elicitor, if-designer, uf-designer, uf-implementor, eval-planner, eval-runner, repo-doc-writer) | stdout 마지막에 `RESULT_JSON={...}` 한 줄 추가 (passed bool, findings 배열) |
| P0-4 | **`agent-orchestration` 스킬 신설** | `core-engineering`이 이미 참조하나 미구현. `agents.md` 로더 + 서브에이전트 스포너 + context.json 관리 |
| P0-5 | **`req-elicitor`** | Phase B를 명시적으로 `human_in_loop: true` 플래그. Phase A / Phase C–E를 서브에이전트로 쪼갤 수 있도록 `execution_modes: [full, phase_a_only, phase_cde_after_clarification]` 추가 |
| P0-6 | **`eval-planner`** | Step 3 Target 확정 부분을 `human_in_loop: true`로 마킹. Step 1–2, 4–5를 서브에이전트 실행 가능하도록 분리 |

### P1 — 전환 후 즉시 가치

| # | 대상 | 변경 내용 |
|---|---|---|
| P1-1 | **`uf-implementor`** | `fanout: per-if` 선언, IF별 서브에이전트 스폰을 오케스트레이터가 할 수 있도록 `--scope <IF-ID>` 인자 수용 |
| P1-2 | **`cursor-task-formatter`** | `fanout: per-uf`(Mode A) / `fanout: per-finding`(Mode B) 선언 |
| P1-3 | **`code-reviewer`** | `fanout: per-file` 선언, 파인딩 리포트 병합 프로토콜 추가(각 서브의 `FINDING-N`이 충돌 없도록 ID 네임스페이스 분리) |
| P1-4 | **`uf-chain-validator`** | 현재 스킬 명세가 얕음. §5의 `inputs.required` 명시(`uf.md`, `if_list.md`, `src/uf/`, `tests/`), 검증 결과를 `uf_if_coverage_review.md`에 기록. 현재는 "validation report in Markdown"이라고만 적혀 있음 |
| P1-5 | **`if-integrator`** | IF별 팬아웃 선언(`fanout: per-if`), `uf_impl_report.md` 상태가 `STUB`인 UF는 스킵하도록 기계화 |
| P1-6 | **`repo-doc-writer`** | `docs/ai/tasks/<UF_ID>.md`를 UF별 팬아웃으로 생성 가능하도록 `fanout: per-uf` |
| P1-7 | **`uf-if-debug-mapper`** | 이미 3역할 모델 언급. 이를 공식 `pipeline.role: verifier`로 승격하고 `agents.md`에서 verifier 그룹에 편입 |

### P2 — 장기 개선

| # | 대상 | 변경 내용 |
|---|---|---|
| P2-1 | **도메인 감사 스킬 3종** (`gpu-hpc-guard`, `sim-physics-auditor`, `rag-data-quality`) | `pipeline.role: verifier`, `pipeline.triggers` 필드 추가(예: `when artifact_kind == "code" && project_type == "simulation"`), 오케스트레이터가 조건부로 훅 |
| P2-2 | **`ci-evidence-automation`** | Stage 8+ 에 명시적 훅. eval-runner 종료 시 자동 트리거되는 후행 verifier로 배치 |
| P2-3 | **`project-summarizer`** | 파이프라인 완주 시 `context.json` + 전 단계 핸드오프 JSON을 읽어 자동 요약. `fanout: none`, `trigger: on_pipeline_end` |
| P2-4 | **`core-engineering`** | "Skill Integration" 표의 `agent-orchestration` 행을 실제 스킬 링크로 연결, 3-role 매핑 컬럼 추가 |
| P2-5 | **`cursor-task-formatter`** vs **`repo-doc-writer`** | 출력이 겹침(`docs/ai/tasks/*.md` vs cursor prompt 블록). 중복 제거: `repo-doc-writer`가 파일을 쓰고, `cursor-task-formatter`는 파일을 읽어 프롬프트로 압축. 의존성을 명확화 |

### P3 — 선택적

- 모든 스킬의 validator 스크립트에 `--resume` 옵션(실패 후 재개)과 `--dry-run` 옵션(변경 없이 검증만) 추가
- 각 역할(architect/builder/verifier)별 공용 `references/agent_contract.md`를 두어 JSON 스키마 중앙화

---

## 9. 리스크 및 완화

| 리스크 | 완화 |
|---|---|
| 서브에이전트가 context.json을 잘못 갱신하면 파이프라인 전체가 꼬임 | `context.json` 쓰기는 오케스트레이터만 수행. 서브는 핸드오프 JSON만 반환 |
| 팬아웃 서브에이전트 간 파일 쓰기 경합 | 각 서브에 쓰기 스코프를 파일 경로 패턴으로 고정(`scope: src/uf/if_01_*.py`) |
| Human-in-loop 지점에서 에스컬레이션 루프 (사용자가 무응답) | `unresolved.timeout_policy: pause_pipeline_and_save_resume_token` 기본값 |
| 검증자 오탐/미탐 | verifier 결과는 `warning` vs `blocking` 2단계로 구분. `blocking`만 파이프라인 중단 |
| 도메인 감사 스킬 폭주(3개 동시 훅) | `agents.md`에서 프로젝트 type별 감사 선택지 명시 |
| agents.md 자체가 부풀어 오름 | 역할별로 `.pipeline/agents/<role>.md`로 쪼갤 수 있도록 `include:` 지시자 도입(P2) |

---

## 10. 권장 도입 순서

1. **Week 1:** P0-4 (`agent-orchestration` 스킬 신설), P0-1 (모든 스킬 프런트매터 패치)
2. **Week 2:** P0-2, P0-3 (핸드오프 JSON + validator JSON 출력)
3. **Week 3:** P0-5, P0-6 (human-in-loop 명시), `agents.md` v1 배포, 소규모 프로젝트에서 드라이런
4. **Week 4:** P1-1 ~ P1-7 (팬아웃 활성화), 실전 파이프라인 1건 완주
5. **이후:** P2 순차 적용, `core-engineering`의 skill integration 표 공식 업데이트

---

## 11. 다음 단계 제안

- `agents.md` 샘플 매니페스트는 같은 폴더의 `agents.md` 파일로 제공했습니다.
- 먼저 `agent-orchestration` 스킬의 `SKILL.md` 초안과 `context.json` 스키마를 작성할지, 아니면 기존 스킬 중 하나(예: `uf-implementor`)에 P0-1~P0-3 패치를 적용한 **proof-of-concept**를 먼저 만들지 선택해 주세요.
- 도메인 감사 스킬 3종의 훅 조건을 확정하려면 현재 주력 프로젝트 유형(시뮬레이션/ML/RAG 등)이 무엇인지 알려주시면 `agents.md` v1의 기본값을 맞출 수 있습니다.
