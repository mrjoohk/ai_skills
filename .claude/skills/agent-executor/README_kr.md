# Agent Executor 스킬 가이드

## 스킬 개요

이 스킬은 `agent-orchestration`이 생성한 역할 설명 파일들(`agents/orchestration_plan.md`, `agents/agent-*.md`)을 읽어, **현재 대화 세션이 오케스트레이터 역할**을 하며 Agent tool을 통해 서브에이전트들을 실제로 스폰합니다. 각 서브에이전트의 작업 결과를 수집하고 검증한 후, 최종 통합 리포트를 생성합니다.

**핵심:** 이 스킬은 문서화 아닌 **실행**을 담당합니다.

---

## 언제 사용하는가

### 트리거 조건
- `agents/orchestration_plan.md`가 존재하고, 사용자가 "에이전트들을 실행해줘", "지금 돌려줘" 등의 실행 요청을 할 때
- 설계한 다중 에이전트 워크플로우를 실제로 동작시키고 싶을 때

### 선행 조건
- ✅ `agent-orchestration` 스킬을 먼저 실행한 상태
- ✅ `agents/orchestration_plan.md` 파일이 존재
- ✅ `agents/agent-1-*.md`, `agents/agent-2-*.md` 등 역할 파일 완성

---

## 입력

### 필수 입력

1. **`agents/orchestration_plan.md`**
   - 에이전트 목록과 역할
   - 실행 그룹 정의 (병렬/순차)
   - 최종 리포트 저장 위치

2. **`agents/agent-<N>-<role>.md` 파일들**
   - 각 에이전트의 task_prompt
   - inputs (읽을 파일 목록)
   - outputs (생성할 파일 목록)
   - dependencies (의존성)
   - acceptance_criteria (수락 기준)
   - skills_to_use (사용할 스킬)

### 선택 입력
- 에이전트들이 읽어야 할 설계 문서, UF 목록 등
  (이들은 role 파일의 inputs 필드에 명시되어야 함)

---

## 출력물

### 생성되는 파일 목록

1. **`reports/orchestration_report_<timestamp>.md`** ⭐ (핵심)
   - 전체 실행 요약
   - 각 에이전트별 실행 결과 (상태, 소요 시간, 출력물)
   - 최종 성공/실패 판단
   - 생성된 파일 목록
   - 다음 단계 제안

2. **각 에이전트가 생성하는 파일들**
   - Agent-1 (Architect): `uf.md`, `requirements.md`, `if_list.md` 등
   - Agent-2 (Builder): `src/` 수정 파일들, `git diff` 등
   - Agent-3 (Verifier): `reports/validation.md`, `coverage_report.json` 등
   - (구체적 경로는 각 agent 파일의 outputs 필드 참조)

### 출력 예시
```
reports/
  orchestration_report_2026-03-19T10-30-45.md    ← 통합 리포트

agents/
  orchestration_plan.md                          ← 입력 (agent-orchestration 생성)
  agent-1-architect.md
  agent-2-builder.md
  agent-3-verifier.md

uf.md, requirements.md                           ← Agent-1 출력
src/pipeline/encoder.py (수정)                   ← Agent-2 출력
reports/validation.md, coverage_report.json      ← Agent-3 출력
```

---

## 슬래시 명령 예시

### 예시 1: 기본 실행
```
/agent-executor 오케스트레이션 계획을 읽고 모든 에이전트를 실행해줘.
agents/orchestration_plan.md를 기반으로 병렬/순차 실행을 자동으로 판단하고
각 에이전트의 작업을 진행시켜줘.
```

**실행 흐름:**
1. `agents/orchestration_plan.md` 존재 확인
2. Group 1 에이전트들 병렬 스폰 → 완료 대기
3. Group 1 완료 검증 → Group 2 스폰
4. ... (모든 그룹 순차 진행)
5. `reports/orchestration_report_<timestamp>.md` 생성

**생성 결과:**
- 모든 에이전트의 출력 파일
- 최종 통합 리포트

---

### 예시 2: 특정 에이전트만 재실행
```
/agent-executor Agent-2 (Builder)를 다시 실행해줘.
Agent-1 (Architect)의 출력 파일(uf.md, requirements.md)은 이미 완성됐어.

inputs:
  - uf.md
  - requirements.md

outputs:
  - src/pipeline/ 하위 파일들
```

**실행 흐름:**
1. Agent-1 존재 확인 (스킵)
2. Agent-2만 스폰
3. 결과 검증
4. 리포트 재생성

---

### 예시 3: 결과 확인 후 리포트만 재생성
```
/agent-executor 모든 에이전트 작업은 이미 완료됐어.
agents/ 파일들과 생성된 출력물들을 읽고
orchestration_report.md만 다시 정리해줘.
```

**실행 흐름:**
1. 각 agent 파일의 outputs에 명시된 파일들이 실제로 존재하는지 확인
2. acceptance_criteria 충족 여부 검증
3. `reports/orchestration_report_<timestamp>.md` 재생성

---

### 예시 4: 병렬 실행 그룹 확인
```
/agent-executor orchestration_plan.md의 실행 그룹을 읽고,
어떤 에이전트들이 병렬로 실행되는지 보여줘.
```

**출력 예:**
```
Group 1 (병렬 실행):
  - Agent-1a (Architect - UF-10)
  - Agent-1b (Architect - UF-20)

Group 2 (Group 1 완료 후):
  - Agent-2 (Builder)

Group 3 (Group 2 완료 후):
  - Agent-3 (Verifier)
```

---

## 핵심 개념

### 1. 오케스트레이터 역할
```
현재 대화 세션 = 오케스트레이터
 ↓
 ├─ Agent tool 호출 → Agent-1 스폰 (독립 컨텍스트)
 │   └─ Agent-1이 작업 수행 및 파일 생성
 │
 ├─ Agent tool 호출 → Agent-2 스폰 (독립 컨텍스트)
 │   └─ Agent-2가 Agent-1의 파일을 읽고 작업 수행
 │
 └─ 최종 결과 수집 및 리포트 작성
```

### 2. 병렬 실행 vs 순차 실행

**병렬 실행 (같은 그룹):**
```
단일 응답 메시지 내에서 여러 Agent tool 호출
→ 모두 동시에 실행 가능

Group 1:
  [Agent tool 호출] → Agent-1a 스폰
  [Agent tool 호출] → Agent-1b 스폰
  (두 에이전트 동시 실행)
```

**순차 실행 (다른 그룹):**
```
이전 그룹의 모든 에이전트가 완료될 때까지 대기 후 다음 실행

Group 1 완료 ✅
   ↓
Group 2 시작 → Agent-2 스폰
```

### 3. 파일을 통한 결과 공유
```
Agent-1 (독립 컨텍스트)
  → uf.md 파일 생성
  → 오케스트레이터가 파일 읽음
     ↓
Agent-2 (독립 컨텍스트)
  → uf.md를 입력으로 읽음
  → 구현 파일 생성
  → 오케스트레이터가 파일 읽음
```

---

## 다른 스킬과의 연결

### 선행 스킬: `agent-orchestration` 🔗 (반드시 먼저 실행)

```
Step 1: agent-orchestration 실행
        (역할 설계, 파일 생성)
             ↓
        agents/orchestration_plan.md
        agents/agent-1-architect.md
        agents/agent-2-builder.md
        agents/agent-3-verifier.md 생성
             ↓
Step 2: agent-executor 실행
        (서브에이전트 스폰 및 실행)
             ↓
        reports/orchestration_report_<timestamp>.md 생성
```

### 함께 사용되는 스킬

각 서브에이전트의 task_prompt에 지정:

```yaml
# Agent-1 task_prompt 내:
"다음 스킬을 사용하여 작업해줘:
 - uf-generator: UF 도출
 - requirement-analyzer: 요구사항 분석
 생성 파일: uf.md, requirements.md"

# Agent-2 task_prompt 내:
"code-implementer 스킬을 사용하여 최소 diff 구현해줘"

# Agent-3 task_prompt 내:
"ci-evidence-automation 스킬로 증거 팩을 생성해줘"
```

---

## 실행 흐름 상세

```
[agent-executor 시작]
     ↓
[Step 1] 사전 확인
  - agents/orchestration_plan.md 존재? → 없으면 에러
  - agent-*.md 파일들 존재? → 없으면 에러
  - 의존성 파악 및 그룹 결정
     ↓
[Step 2] 그룹별 스폰
  Group 1 (병렬):
    Agent tool (Agent-1 task_prompt)
    Agent tool (Agent-2 task_prompt)   ← 단일 메시지에서 동시 호출
     ↓
  Group 1 완료 대기
     ↓
  Group 1 결과 검증
    - STATUS 확인
    - 출력 파일 존재 확인
    - acceptance_criteria 충족 확인
     ↓
  Group 2 (순차):
    Agent tool (Agent-3 task_prompt)
     ↓
[Step 3] 최종 결과 검증
  - 모든 에이전트 상태 정리
  - 생성 파일 목록 수집
  - 전체 성공/실패 판정
     ↓
[Step 4] 리포트 생성
  reports/orchestration_report_<timestamp>.md
     ↓
[agent-executor 완료]
```

---

## 주의사항

1. **agent-orchestration 선행 필수**
   - agent-executor 실행 전에 반드시 agent-orchestration을 먼저 실행하세요
   - 없으면 "agents/orchestration_plan.md 생성 후 다시 실행해주세요" 메시지 표시

2. **서브에이전트 독립성**
   - 각 서브에이전트는 독립적인 컨텍스트에서 실행됩니다
   - 오케스트레이터는 중간 과정에 개입하지 않습니다
   - 모든 정보는 파일을 통해 전달되어야 합니다

3. **task_prompt 작성**
   - 자기 완결적(self-contained)이어야 합니다
   - 외부 변수나 컨텍스트에 의존하면 안 됩니다
   - 파일 경로, 입력, 출력을 명확히 명시

4. **오류 처리**
   - FAIL 상태 에이전트의 의존 에이전트는 실행되지 않습니다
   - 독립적인 에이전트는 다른 에이전트 실패에 영향받지 않습니다
   - 오케스트레이터가 재시도 여부를 판단합니다

5. **결과 보고 형식**
   - 각 서브에이전트는 다음 형식으로 반드시 보고해야 합니다:
   ```
   STATUS: PASS | FAIL
   OUTPUTS: <파일 경로 목록>
   SUMMARY: <한 줄 요약>
   ISSUES: <문제 사항>
   ```
