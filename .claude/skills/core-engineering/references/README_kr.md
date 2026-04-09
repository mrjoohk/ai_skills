# Core Engineering 스킬

## 스킬 개요

모든 엔지니어링 설계의 기반을 정의하는 글로벌 스킬입니다. 문제 정의부터 단위기능(UF) 도출, 검증 계획까지 8단계 체계적 설계 프로세스를 제공하며, 요구사항 명확화, 시스템 인터페이스 정의, 증거 기반의 검증을 보장합니다.

## 언제 사용하는가

- 새로운 기능이나 모듈 개발을 시작할 때
- 요구사항이 불명확하거나 이해관계자 간 의견이 불일치할 때
- 시스템 아키텍처 설계 또는 리팩토링 시
- 테스트 및 검증 전략을 수립해야 할 때
- 모든 후속 스킬(uf-chain-validator, uf-if-debug-mapper, ci-evidence-automation 등)을 사용하기 전에

## 입력

- 문제 설명 또는 기능 요청
- 기존 요구사항 문서 (보유 시)
- 이해관계자 입력 및 제약 조건
- 기술적/비기능적 제약사항

## 출력물

| 단계 | 파일 | 설명 |
|:---:|---|---|
| 1 | `problem_statement.md` | 문제 배경, 발생 맥락, 영향 범위 기술 |
| 2 | `clarification_log.md` | 모호성 해결을 위한 Q&A 목록 |
| 3 | `assumptions_and_constraints.md` | 제약 조건, 경계 조건, 가정 기록 |
| 4 | `requirements.md` | 기능/비기능 요구사항 (REQ 블록 형식) |
| 5 | `if_list.md` | 통합기능(IF) 목록 및 시스템 경계 다이어그램 |
| 6 | `if_decomposition.md` | IF별 서브기능 분해 및 의존성 그래프 |
| 7 | `uf.md` | 단위기능(UF) 상세 정의 (I/O 컨트랙트 포함) |
| 8 | `verification_plan.md` | 테스트 계획, 커버리지 목표, 회귀 임계값 |
| 8 | `evidence_pack/` | 증거 팩 디렉토리 구조 제안 |

## 슬래시 명령 예시

### 1. 문제 정의에서 요구사항까지 (Stage 1-4)
```
/core-engineering
"실시간 이미지 처리 파이프라인에서 프레임 드롭이 발생하고 있다.
Stage 1~4를 수행하여 problem_statement.md, clarification_log.md,
assumptions_and_constraints.md, requirements.md를 작성하라.
REQ 블록에는 수치 수락 기준(Given/When/Then + 임계값)을 포함하라."
```

### 2. IF 도출에서 UF 분해까지 (Stage 5-7)
```
/core-engineering
"requirements.md를 입력으로, Stage 5~7을 수행하라.
통합기능(IF) 목록과 IF→UF 분해 결과를 작성하고,
각 UF 블록에 I/O 컨트랙트와 검증 계획을 포함하라."
```

### 3. 검증 계획 수립 (Stage 8)
```
/core-engineering
"uf.md를 기반으로 Stage 8을 수행하라.
unit/integration/e2e 테스트 계획과 evidence_pack/ 구조를 제안하라.
회귀 임계값을 수치로 명시하라."
```

### 4. 최소 차이(Minimal Diff) 리팩토링
```
/core-engineering
"src/pipeline/processor.py의 중복 할당을 제거하라.
동작은 변경하지 말고, 패치(diff) 형식으로만 출력하라.
출력이 동일함을 보장하는 단위 테스트를 추가하라."
```

## 다른 스킬과의 연결

- **uf-chain-validator**: Stage 7 완료 후 UF 체인 검증
- **uf-if-debug-mapper**: Stage 6~7 완료 후 디버그 맵 생성
- **ci-evidence-automation**: Stage 8 완료 후 증거 팩 자동화
- **agent-orchestration**: 전 단계에서 에이전트 역할 분담

### 전형적인 플로우
1. core-engineering: Stage 1~8 완료 → 설계 산출물 생성
2. uf-chain-validator: UF 간 의존성 검증
3. uf-if-debug-mapper: 디버그 매핑 및 추적성 확보
4. ci-evidence-automation: 자동화된 증거 팩 생성

## 8단계 설계 프로세스 상세

### Stage 1 — 문제 정의 (Problem Definition)
문제의 배경과 발생 맥락을 1~3문장으로 명확히 기술하고, 영향 범위를 파악합니다.

### Stage 2 — 문제 검토 & 명확화 (Problem Review & Clarification)
모호한 용어, 경계 조건, 이해관계자 요구사항을 명확히 합니다. Q&A 형태로 기록하여 추후 참조할 수 있도록 합니다.

### Stage 3 — 문제 상세화 (Problem Elaboration)
제약 조건 (성능, 메모리, 정확도), 경계 조건 (입력 범위, 극단값), 가정 (명시적 기록, 나중에 검증)을 정의합니다.

### Stage 4 — 요구사항 도출 (Requirements Elicitation)
기능 요구사항과 비기능 요구사항을 REQ 블록 형식으로 작성합니다. 각 요구사항은 테스트 가능한 수락 기준을 포함해야 합니다.

**REQ 블록 구조:**
- ID: 고유 식별자 (REQ-001, REQ-002, ...)
- Context: 배경 및 동기
- Inputs/Outputs: 타입, 단위, 범위 명시
- Constraints: 성능, 메모리, 정확도 등
- Acceptance Criteria: Given/When/Then + 수치 임계값
- Tests: 단위/통합/E2E 테스트 계획
- Evidence: 증거 아티팩트 경로

### Stage 5 — 통합기능(IF) 도출 (Integration Function Identification)
시스템 경계를 정의하고, 외부 인터페이스 (API, HW 인터페이스)를 명시합니다. 각 IF에 대해 입력·출력·제약·연관 REQ를 기술합니다.

### Stage 6 — 통합기능 분해 (IF Decomposition)
각 IF를 서브기능으로 분해하여 의존성 그래프를 작성합니다. 분해 기준은 단일 책임 원칙(SRP)과 테스트 가능성입니다.

### Stage 7 — 단위기능(UF) 도출 (Unit Function Definition)
각 UF를 UF 블록 형식으로 정의합니다. I/O 컨트랙트에 타입, 단위, 형태(shape)를 명시하고, 엣지 케이스 및 실패 모드를 나열합니다.

**UF 블록 구조:**
- UF-ID: 고유 식별자 (UF-001, UF-002, ...)
- Parent IF: 상위 IF 참조
- Goal: 단일 책임을 한 줄로 기술
- I/O Contract: 입력/출력 형식, 단위, 범위
- Algorithm Summary: 핵심 알고리즘 1~3줄
- Edge Cases: 극단값, null, overflow 등
- Verification Plan: 테스트 명령, 커버리지 목표
- Evidence Pack Fields: 수집할 메타데이터

### Stage 8 — 검증 & 증거 계획 (Verification & Evidence Planning)
단위/통합/E2E 테스트 계획을 작성하고, 증거 팩(Evidence Pack) 구조를 정의합니다. 회귀 임계값을 수치로 설정합니다.

## 핵심 개념

### REQ 블록 (Requirements Block)
기능 요구사항 또는 비기능 요구사항을 체계적으로 정의하는 템플릿입니다. 각 REQ는 반드시 테스트 가능한 수락 기준을 포함해야 합니다.

**예시:**
```
- ID: REQ-001
- Context: 이미지 파이프라인의 프레임 드롭 현상을 해결하기 위함
- Inputs: 카메라 프레임 (720p, 30fps)
- Outputs: 처리된 프레임 (720p, 30fps)
- Constraints: 지연 시간 <= 33ms (95th percentile)
- Acceptance Criteria: Given 연속 30초 스트림, When 처리 실행, Then 프레임 드롭 < 1%
- Tests: unit, integration, e2e
- Evidence: reports/performance.csv, evidence_pack/runs.yaml
```

### IF 블록 (Integration Function Block)
시스템 인터페이스를 정의하는 템플릿입니다. Producer와 Consumer 간의 계약을 명시합니다.

### UF 블록 (Unit Function Block)
개별 기능 단위를 정의하는 템플릿입니다. I/O 컨트랙트를 명시적으로 정의하여 통합과 테스트를 용이하게 합니다.

## 실행 규칙

1. **테스트 가능성**: 모든 수락 기준은 테스트 가능하고 수치로 측정 가능해야 함
2. **I/O 명시성**: 모든 I/O 컨트랙트는 타입, 단위, 형태(shape)를 명시해야 함
3. **토큰 절약**: 파일 경로와 심볼 참조를 우선; 대용량 코드 블록 금지
4. **증거 기반**: 모든 주장에는 증거 아티팩트(테스트 결과, 로그, 플롯) 필요
5. **가정 명시**: 가정(Assumptions)은 반드시 명시적으로 기록하고 나중에 검증

## 설계 프로세스 요약표

| Stage | 단계명 | 담당 스킬 | 주요 출력물 |
|:---:|---|---|---|
| 1 | 문제 정의 | core-engineering | problem_statement.md |
| 2 | 문제 명확화 | core-engineering | clarification_log.md |
| 3 | 상세화 | core-engineering | assumptions_and_constraints.md |
| 4 | 요구사항 도출 | core-engineering | requirements.md (REQ 블록) |
| 5 | IF 도출 | core-engineering | if_list.md |
| 6 | IF 분해 | core-engineering | if_decomposition.md |
| 7 | UF 도출 | core-engineering | uf.md (UF 블록) |
| 8 | 검증 계획 | core-engineering + ci-evidence-automation | verification_plan.md, evidence_pack/ |

## 품질 검증 체크리스트

- [ ] 모든 요구사항에 수치 수락 기준(Given/When/Then)이 있는가?
- [ ] 모든 I/O 컨트랙트에 타입·단위·형태(shape)가 명시되어 있는가?
- [ ] 모든 가정(Assumption)이 명시적으로 기록되어 있는가?
- [ ] UF-ID와 IF-ID의 연결 관계가 명확한가?
- [ ] 증거 아티팩트 경로가 정의되어 있는가?
