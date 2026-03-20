# Agent Orchestration 스킬 가이드

## 스킬 개요

이 스킬은 복잡한 작업을 에이전트별 역할로 분해하여 **구조화된 역할 설명 파일**을 생성합니다. `agent-executor`가 실제로 서브에이전트를 스폰할 수 있도록 설계 문서, UF 목록, WBS 등을 기반으로 에이전트 간 역할 분담과 의존성을 명시합니다.

**중요:** 이 스킬은 **문서 생성만** 담당합니다. 실제 서브에이전트 실행은 `agent-executor`가 담당합니다.

---

## 언제 사용하는가

### 트리거 조건
- 사용자가 "다중 에이전트로 처리해줘", "병렬로 분배해줘" 등의 요청을 할 때
- `/agent-executor` 실행 전에 역할 설계 파일이 필요할 때
- 복잡한 설계 프로세스(Stage 1~8)를 여러 에이전트에 분산하고 싶을 때

### 선행 조건
- 입력 문서: 설계 문서, UF 목록, WBS, 구현 계획 등
- 병렬 처리 가능한 독립적 작업 단위 파악

---

## 입력

### 필수 입력
1. **설계 문서** (`design.md` 등)
   - 전체 작업 개요
   - Stage별 요구사항

2. **UF/IF 목록** 또는 구현 계획
   - 각 유저 플로우(User Flow) 또는 인터페이스(Interface)의 범위
   - 구현 우선순위

### 선택 입력
- CI/CD 관련 문서
- 성능 기준서(SLA, 벤치마크)
- 테스트 계획

---

## 출력물

### 생성되는 파일 목록

1. **`agents/orchestration_plan.md`** ⭐ (핵심)
   - 전체 오케스트레이션 계획
   - 에이전트 목록과 역할 요약
   - 실행 그룹 정의 (병렬/순차)
   - agent-executor의 진입점

2. **`agents/agent-1-architect.md`**
   - Agent-1의 역할: Stage 1~7 설계 프로세스 수행
   - task_prompt, inputs, outputs, 수락 기준 정의

3. **`agents/agent-2-builder.md`** (필요시)
   - Agent-2의 역할: 최소 diff 구현
   - task_prompt, 입력 파일(Agent-1 출력물), 출력 위치

4. **`agents/agent-3-verifier.md`** (필요시)
   - Agent-3의 역할: Stage 8 검증·테스트·증거 수집
   - 수락 기준, CI 게이트 정의

### 파일 구조 예시
```
agents/
  orchestration_plan.md          ← agent-executor가 먼저 읽는 파일
  agent-1-architect.md           ← Agent-1 역할 정의
  agent-2-builder.md             ← Agent-2 역할 정의
  agent-3-verifier.md            ← Agent-3 역할 정의
```

---

## 슬래시 명령 예시

### 예시 1: 기본 3-에이전트 분배
```
/agent-orchestration 다음 작업을 3-에이전트 구조로 분배해줘:

입력:
- 설계 문서: docs/design.md
- UF 목록: docs/user_flows.md

요구사항:
- Agent-1 (Architect): Stage 1~7 설계 수행 → uf.md, requirements.md 생성
- Agent-2 (Builder): UF 기준 최소 구현 → src/ 파일 수정
- Agent-3 (Verifier): 테스트 및 증거 수집 → reports/validation.md 생성

agents/ 디렉토리에 역할 파일과 orchestration_plan.md를 생성해줘.
```

**생성 결과:**
- `agents/orchestration_plan.md`
- `agents/agent-1-architect.md`
- `agents/agent-2-builder.md`
- `agents/agent-3-verifier.md`

---

### 예시 2: 병렬 실행 그룹 정의
```
/agent-orchestration 다음 2개 UF를 병렬로 처리할 수 있도록 분배해줘:

- UF-10: 사용자 인증 (Agent-1a가 담당)
- UF-20: 데이터 수집 (Agent-1b가 담당)

두 에이전트는 Stage 1~7을 동시에 수행하고,
이후 단일 Builder (Agent-2)가 통합 구현을 진행한다.

실행 그룹:
- Group 1 (병렬): Agent-1a, Agent-1b
- Group 2 (순차): Agent-2 (병렬 완료 후)
```

**생성 결과:**
- `agents/orchestration_plan.md` (Group 1, Group 2 명시)
- `agents/agent-1a-auth-architect.md`
- `agents/agent-1b-data-architect.md`
- `agents/agent-2-builder.md`

---

### 예시 3: 인계 메시지 포함
```
/agent-orchestration Agent-1에서 Agent-2로의 인계 메시지를 포함한
orchestration_plan.md를 생성해줘.

인계 내용:
- UF-01~UF-15 완성
- 수락 기준: 코드 커버리지 >= 90%, 응답 시간 <= 100ms
- 증거 아티팩트: reports/uf_validation.md, coverage_report.json
```

**생성 결과:**
- `agents/orchestration_plan.md` (인계 블록 포함)
- 각 에이전트별 역할 파일

---

## 다른 스킬과의 연결

### 선행 스킬
- 없음 (설계 문서만 있으면 시작 가능)

### 후속 스킬: `agent-executor` 🔗
**반드시 이 스킬 이후에 실행해야 함**

```
Step 1: agent-orchestration 실행
        ↓
        생성: agents/orchestration_plan.md, agent-*.md 파일들
        ↓
Step 2: agent-executor 실행
        ↓
        서브에이전트들이 실제로 작업 수행
        ↓
        생성: reports/orchestration_report_<timestamp>.md
```

### 함께 사용하는 스킬

다른 스킬을 agent-executor에서 **서브에이전트의 task_prompt 내에 지정**할 수 있습니다:

```yaml
# agent-1-architect.md에서:
skills_to_use:
  - uf-generator
  - requirement-analyzer

# agent-2-builder.md에서:
skills_to_use:
  - code-implementer
  - test-writer

# agent-3-verifier.md에서:
skills_to_use:
  - ci-evidence-automation
  - performance-benchmarker
```

---

## 워크플로우 다이어그램

```
입력 문서 (설계, UF, WBS)
        ↓
agent-orchestration 실행
        ↓
[Step 1] 작업 분석
  - 병렬 실행 가능 단위 식별
  - 의존성 파악
        ↓
[Step 2] 에이전트 역할 파일 생성
  - agent-1-architect.md
  - agent-2-builder.md
  - agent-3-verifier.md
        ↓
[Step 3] orchestration_plan.md 생성
  - 실행 그룹 정의
  - 최종 리포트 위치 명시
        ↓
agents/ 디렉토리 완성
        ↓
agent-executor 준비 완료 ✅
```

---

## 주의사항

1. **자기 완결적 task_prompt**
   - 각 에이전트의 task_prompt는 외부 컨텍스트 없이 독립적으로 실행 가능해야 합니다
   - 파일 경로는 절대 경로 또는 명확한 상대 경로로 명시

2. **의존성 명시**
   - 에이전트 간 의존성이 있으면 명확히 `dependencies` 필드에 기술
   - 병렬 실행 가능한 작업만 같은 그룹으로 지정

3. **수락 기준 정의**
   - 각 에이전트의 완료 판단 기준을 명확히 작성
   - 수치 임계값, 파일 존재 여부, 커버리지 등 구체적으로

4. **출력물 명시**
   - outputs 필드에 생성할 파일 경로를 모두 기술
   - agent-executor가 이를 기반으로 검증합니다
