# agents.md — Core Engineering Pipeline Orchestration Manifest

> **Version:** 1.0-draft
> **Owner:** `agent-orchestration` skill (main agent가 이 파일을 로드)
> **Purpose:** 설계/구현 파이프라인의 모든 스킬을 Architect / Builder / Verifier 세 역할로 묶고,
> 각 서브에이전트의 입력·출력·권한·팬아웃·트리거 조건을 선언적으로 정의한다.
> 서브에이전트 호출 방식: main agent가 이 파일을 읽고, `current_stage` → `downstream.next` 규칙에 따라
> 해당 스킬을 서브에이전트로 위임(또는 human-in-loop 구간은 직접 실행).

---

## Global Config

```yaml
context_bundle: .pipeline/context.json
handoff_format: json-block-trailing     # 모든 서브는 stdout 끝에 JSON 블록을 남긴다
validator_contract:
  json_line_prefix: "RESULT_JSON="
  required_fields: [passed, findings]
failure_policy:
  default: pause_and_request_user
  retry_limit: 2
logging:
  skill_handoffs: .pipeline/handoffs/<timestamp>_<skill>.json
```

---

## Roles

```yaml
roles:
  - id: architect
    description: "사용자 문제 → 기계 판독 가능한 설계 산출물 생성"
    write_scope: ["*.md", "docs/design/**"]
    can_fanout: false            # 기본적으로 단일 인스턴스, 일부 예외 있음
    human_in_loop_allowed: true

  - id: builder
    description: "설계 산출물 → 코드·문서·프롬프트 변환"
    write_scope: ["src/**", "tests/**", "docs/ai/**", "prompts/**"]
    can_fanout: true
    human_in_loop_allowed: false

  - id: verifier
    description: "산출물 검증·리뷰·측정. 독립 컨텍스트로 실행"
    write_scope: ["reports/**", "evidence_pack/**", ".pipeline/validations/**"]
    can_fanout: true
    human_in_loop_allowed: false
```

---

## Agents

### architect/req-elicitor

```yaml
skill: req-elicitor
role: architect
stage: "1-4"

inputs:
  required:
    - source: user_message            # 문제 서술(자연어)
  optional: []

outputs:
  files:
    - path: problem_statement.md
      kind: design
    - path: clarification_log.md
      kind: design
    - path: assumptions_and_constraints.md
      kind: design
    - path: requirements.md
      kind: design

human_in_loop:
  required: true
  phases: ["Phase B — Clarification"]
  protocol: |
    1. main agent가 Phase A(문제 정의)만 먼저 서브로 실행
    2. Phase A 종료 시 unresolved에 질문 4–8개 포함
    3. main agent가 AskUserQuestion으로 질문을 사용자에게 제시
    4. 답변을 clarification_log.md에 기록 후 Phase C–E를 서브로 재위임

execution_modes:
  - phase_a_only
  - phase_cde_after_clarification
  - full             # human-in-loop 스킵 승인 시만

fanout: none

validator:
  script: "<skill_dir>/scripts/validate_requirements.py"
  args: ["requirements.md"]

downstream:
  - next: architect/if-designer
    when: "status == COMPLETE && unresolved.empty"
```

---

### architect/if-designer

```yaml
skill: if-designer
role: architect
stage: "5-6"

inputs:
  required:
    - path: requirements.md
      producer: req-elicitor
  optional: []

outputs:
  files:
    - path: if_list.md
      kind: design
    - path: if_decomposition.md
      kind: design

human_in_loop:
  required: false

fanout: none

validator:
  script: "<skill_dir>/scripts/validate_if_design.py"
  args: ["if_list.md", "if_decomposition.md"]

downstream:
  - next: architect/uf-designer
    when: "status == COMPLETE"
```

---

### architect/uf-designer

```yaml
skill: uf-designer
role: architect
stage: "7"

inputs:
  required:
    - path: if_decomposition.md
      producer: if-designer
  optional:
    - path: if_list.md
      producer: if-designer

outputs:
  files:
    - path: uf.md
      kind: design

human_in_loop:
  required: false

fanout: none

validator:
  script: "<skill_dir>/scripts/validate_uf_design.py"
  args: ["uf.md"]

downstream:
  - next: verifier/uf-chain-validator
    when: "status == COMPLETE"
```

---

### verifier/uf-chain-validator

```yaml
skill: uf-chain-validator
role: verifier
stage: "7.5"

inputs:
  required:
    - path: uf.md
      producer: uf-designer
    - path: if_list.md
      producer: if-designer
  optional:
    - path: src/uf/
      producer: uf-implementor        # 구현 이후 재실행 시 쓰임
    - path: tests/
      producer: uf-implementor

outputs:
  files:
    - path: uf_if_coverage_review.md
      kind: report

human_in_loop:
  required: false

fanout: none

gate: true        # FAIL이면 다음 단계로 진행 불가

downstream:
  - next: builder/uf-implementor
    when: "status == COMPLETE && validator.passed"
  - next: architect/uf-designer            # 커버리지 갭 시 반복
    when: "validator.findings.has('UNCOVERED')"
  - next: architect/if-designer
    when: "validator.findings.has('REDUNDANT_IF')"
```

---

### architect/eval-planner

```yaml
skill: eval-planner
role: architect
stage: "8-plan"

inputs:
  required:
    - path: uf.md
      producer: uf-designer
  optional:
    - path: requirements.md
    - path: if_list.md

outputs:
  files:
    - path: evaluation_plan.md
      kind: design

human_in_loop:
  required: true
  phases: ["Step 3 — Threshold Target 확정"]
  protocol: |
    Baseline/Stretch는 자동, Target은 사용자 확인 질문으로 승격.
    서브는 Target 미지정 상태로 "[NOTE: confirm]" 플레이스홀더를 두고 종료.
    main agent가 질문 후 파일을 인플레이스 편집.

fanout: none

validator:
  script: "<skill_dir>/scripts/validate_eval_plan.py"

downstream:
  - next: builder/uf-implementor      # 병렬 브랜치
    when: "status == COMPLETE"
  - next: verifier/eval-runner        # 구현 이후
    when: "builder.uf-implementor.status == COMPLETE"
```

---

### builder/uf-implementor

```yaml
skill: uf-implementor
role: builder
stage: "impl"

inputs:
  required:
    - path: uf.md
      producer: uf-designer
  optional:
    - path: uf_if_coverage_review.md
      producer: uf-chain-validator
    - path: requirements.md

outputs:
  files:
    - path: src/uf/<module>.py
      kind: code
      scope_var: <module>
    - path: tests/unit/test_<module>.py
      kind: test
      scope_var: <module>
    - path: reports/impl/uf_impl_report_<timestamp>.md
      kind: report

human_in_loop:
  required: false

fanout:
  strategy: per-if
  scope_key: parent_if
  max_parallel: 4
  write_scope_template: "src/uf/if_<IF-ID>_*.py, tests/unit/test_if_<IF-ID>_*.py"

validator:
  script: "<skill_dir>/scripts/validate_uf_impl.py"
  args: ["<project_root>"]

downstream:
  - next: verifier/code-reviewer
    when: "status == COMPLETE"
  - next: builder/if-integrator
    when: "verifier/code-reviewer.status == COMPLETE && no_critical"
```

---

### builder/if-integrator

```yaml
skill: if-integrator
role: builder
stage: "integrate"

inputs:
  required:
    - path: if_list.md
      producer: if-designer
    - path: if_decomposition.md
      producer: if-designer
    - path: src/uf/
      producer: uf-implementor
  optional:
    - path: uf_if_coverage_review.md
    - path: reports/impl/uf_impl_report_*.md

outputs:
  files:
    - path: src/if/<module>.py
      kind: code
    - path: tests/integration/test_<module>.py
      kind: test
    - path: reports/impl/if_integration_report_<timestamp>.md
      kind: report

human_in_loop:
  required: false

fanout:
  strategy: per-if
  max_parallel: 4

downstream:
  - next: verifier/eval-runner
    when: "status == COMPLETE && evaluation_plan.md exists"
  - next: verifier/code-reviewer
    when: "status == COMPLETE"
```

---

### verifier/code-reviewer

```yaml
skill: code-reviewer
role: verifier
stage: "review"

inputs:
  required:
    - path: src/**
      producer: uf-implementor | if-integrator
  optional:
    - path: uf.md
    - path: docs/ai/tasks/*.md
    - path: requirements.md

outputs:
  files:
    - path: reports/review/<timestamp>_review.md
      kind: report

human_in_loop:
  required: false

fanout:
  strategy: per-file
  max_parallel: 6
  merge_protocol: |
    각 서브 파인딩은 FINDING-<FILE>-<N> 네임스페이스로 생성.
    오케스트레이터가 마지막에 severity 순서로 병합.

downstream:
  - next: builder/cursor-task-formatter
    when: "findings.length > 0"
  - next: architect/eval-planner
    when: "findings.length == 0 && evaluation_plan.md not exists"
```

---

### verifier/eval-runner

```yaml
skill: eval-runner
role: verifier
stage: "8-run"

inputs:
  required:
    - path: evaluation_plan.md
      producer: eval-planner
    - path: src/
      producer: uf-implementor | if-integrator
  optional:
    - experiment_data: paths or inline

outputs:
  files:
    - path: scripts/eval/<task>_eval.py
      kind: code
    - path: reports/eval/<task>_<timestamp>.md
      kind: report
    - path: evidence_pack/metrics.yaml
      kind: report

human_in_loop:
  required: false

fanout:
  strategy: per-task           # evaluation_plan.md 내 task별
  max_parallel: 3

gate: true

downstream:
  - next: verifier/ci-evidence-automation
    when: "status == COMPLETE"
  - next: project-summarizer
    when: "all upstream COMPLETE"
```

---

### builder/repo-doc-writer

```yaml
skill: repo-doc-writer
role: builder
stage: "docs"

inputs:
  required:
    - path: uf.md
      producer: uf-designer
  optional:
    - path: requirements.md
    - path: if_list.md
    - path: if_decomposition.md

outputs:
  files:
    - path: docs/ai/overview.md
      kind: docs
    - path: docs/ai/architecture.md
      kind: docs
    - path: docs/ai/tasks/<UF_ID>.md
      kind: docs

human_in_loop:
  required: false

fanout:
  strategy: per-uf
  scope_key: UF_ID
  max_parallel: 6

validator:
  script: "<skill_dir>/scripts/validate_docs.sh"

# 병렬 브랜치: 파이프라인 아무 시점에서 설계 산출물이 갖춰지면 실행 가능
trigger:
  when: "uf.md exists"
  priority: background

downstream:
  - next: builder/cursor-task-formatter
    when: "status == COMPLETE && config.run_cursor_integration"
```

---

### builder/cursor-task-formatter

```yaml
skill: cursor-task-formatter
role: builder
stage: "prompt"

modes:
  - id: A_implement
    inputs:
      required:
        - path: uf.md | docs/ai/tasks/*.md
    fanout:
      strategy: per-uf
  - id: B_fix
    inputs:
      required:
        - path: reports/review/*.md
          producer: code-reviewer
    fanout:
      strategy: per-finding

outputs:
  files:
    - path: prompts/cursor/<mode>_<id>.md
      kind: prompt

human_in_loop:
  required: false

# 터미널 스킬 — 사용자가 Cursor로 가져감
downstream: []
```

---

### verifier/uf-if-debug-mapper

```yaml
skill: uf-if-debug-mapper
role: verifier
stage: "debug"

inputs:
  required:
    - path: uf.md
    - path: if_list.md
  optional:
    - path: src/
    - error_logs: inline or path

outputs:
  files:
    - path: docs/uf_if_debug_map.md
      kind: docs

human_in_loop:
  required: false

# 트리거 조건이 특수: 사용자 요청 또는 CI 실패 시
trigger:
  when: "user_request || ci.failure || verifier/eval-runner.status == FAIL"

fanout: none

downstream: []
```

---

### verifier/ci-evidence-automation

```yaml
skill: ci-evidence-automation
role: verifier
stage: "ci"

inputs:
  required:
    - path: evidence_pack/metrics.yaml
      producer: eval-runner
    - path: reports/eval/*.md
  optional:
    - path: reports/review/*.md

outputs:
  files:
    - path: evidence_pack/
      kind: report
    - path: .github/coverage_gate.yml
      kind: config

human_in_loop:
  required: false

trigger:
  when: "verifier/eval-runner.status == COMPLETE"

downstream:
  - next: project-summarizer
    when: "all pipeline stages logged"
```

---

### project-summarizer

```yaml
skill: project-summarizer
role: meta        # 어느 역할에도 속하지 않는 종결 스킬
stage: "end"

inputs:
  required:
    - path: .pipeline/context.json
  optional:
    - path: .pipeline/handoffs/*.json
    - path: reports/**

outputs:
  files:
    - path: project_summary.md
      kind: docs

trigger:
  when: "user_request || pipeline_end"

fanout: none
downstream: []
```

---

## Optional Domain Auditors (조건부 훅)

도메인별로 파이프라인 각 단계 산출물에 오버레이되는 verifier들.
`context.json.config.project_type`에 따라 활성화.

```yaml
domain_auditors:
  - skill: gpu-hpc-guard
    role: verifier
    activate_when: "project_type in ['ml', 'simulation', 'hpc']"
    hook_after: [builder/uf-implementor, builder/if-integrator]
    outputs:
      files:
        - path: reports/audit/gpu_<timestamp>.md

  - skill: sim-physics-auditor
    role: verifier
    activate_when: "project_type == 'simulation'"
    hook_after: [architect/uf-designer, builder/uf-implementor]
    outputs:
      files:
        - path: reports/audit/physics_<timestamp>.md

  - skill: rag-data-quality
    role: verifier
    activate_when: "project_type == 'rag'"
    hook_after: [builder/uf-implementor]
    outputs:
      files:
        - path: reports/audit/rag_<timestamp>.md
```

---

## Pipeline State Machine (요약)

```
START
  → architect/req-elicitor          (human-in-loop: Phase B)
  → architect/if-designer
  → architect/uf-designer
  → verifier/uf-chain-validator     (gate)
        FAIL: loop back to uf-designer or if-designer
        PASS:
        ├─▶ builder/uf-implementor           (fanout per-if)
        │      → verifier/code-reviewer      (fanout per-file)
        │      → builder/if-integrator        (fanout per-if)
        │
        └─▶ architect/eval-planner            (human-in-loop: Step 3, 병렬 가능)
               → verifier/eval-runner         (gate, 구현 완료 후)
               → verifier/ci-evidence-automation
               → project-summarizer

  (배경 브랜치, 설계 완료 시점에 언제든)
  → builder/repo-doc-writer          (fanout per-uf)
  → builder/cursor-task-formatter    (Mode A / Mode B)

  (이벤트 트리거)
  → verifier/uf-if-debug-mapper      (CI fail 또는 user request 시)
  → verifier/domain_auditors[*]      (project_type 매칭 시)
```

---

## Skill-to-File Mapping Reference

| 스킬 | 역할 | 읽는 파일 | 쓰는 파일 |
|---|---|---|---|
| req-elicitor | architect | (user) | problem_statement.md, clarification_log.md, assumptions_and_constraints.md, requirements.md |
| if-designer | architect | requirements.md | if_list.md, if_decomposition.md |
| uf-designer | architect | if_decomposition.md, (if_list.md) | uf.md |
| uf-chain-validator | verifier | uf.md, if_list.md, src/, tests/ | uf_if_coverage_review.md |
| eval-planner | architect | uf.md, (requirements.md) | evaluation_plan.md |
| uf-implementor | builder | uf.md, (coverage review) | src/uf/**, tests/unit/**, reports/impl/uf_impl_report_*.md |
| if-integrator | builder | if_list.md, if_decomposition.md, src/uf/ | src/if/**, tests/integration/**, reports/impl/if_integration_report_*.md |
| code-reviewer | verifier | src/**, uf.md | reports/review/*.md |
| eval-runner | verifier | evaluation_plan.md, src/, exp data | scripts/eval/**, reports/eval/**, evidence_pack/metrics.yaml |
| repo-doc-writer | builder | requirements.md, if_list.md, if_decomposition.md, uf.md | docs/ai/overview.md, docs/ai/architecture.md, docs/ai/tasks/*.md |
| cursor-task-formatter | builder | uf.md or reports/review/*.md | prompts/cursor/*.md |
| uf-if-debug-mapper | verifier | uf.md, if_list.md, src/ | docs/uf_if_debug_map.md |
| ci-evidence-automation | verifier | evidence_pack/, reports/** | evidence_pack/**, .github/** |
| project-summarizer | meta | .pipeline/**, reports/** | project_summary.md |

---

## 사용 예시 (메인에이전트의 라우팅 의사코드)

```python
# Pseudo-code; agent-orchestration 스킬이 내부적으로 수행
def orchestrate():
    manifest = load("agents.md")
    ctx = load(".pipeline/context.json")

    while True:
        next_agent = pick_next(manifest, ctx)
        if not next_agent:
            break

        if next_agent.human_in_loop.required:
            main_agent_handle_inline(next_agent)
        else:
            if next_agent.fanout.strategy != "none":
                scopes = split_scope(ctx, next_agent.fanout)
                results = spawn_parallel([
                    spawn(next_agent, scope=s) for s in scopes
                ])
                handoff = merge(results, next_agent.fanout.merge_protocol)
            else:
                handoff = spawn(next_agent)

        validate_and_update_context(handoff, ctx)
        persist(ctx)
```

---

**TODO (v1.1 후속):**

- `include:` 지시자 도입 — 역할별 `.pipeline/agents/<role>.md`로 분할
- `resume_token` 기반 중단 지점 재개 규격
- 서브에이전트 권한 강제(쓰기 스코프 샌드박싱) — 현재는 문서적 선언만
