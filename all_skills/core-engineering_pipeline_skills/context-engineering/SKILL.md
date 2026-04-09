---
name: context-engineering
description: >
  에이전트(Claude/Cursor)에게 올바른 컨텍스트를 올바른 시점에 공급하는 메타 스킬.
  세션 시작, 파이프라인 단계 전환, 에이전트 출력 품질 저하, 새 프로젝트 설정 시 실행.
  트리거: "컨텍스트 정리해줘", "세션 시작", "Cursor 규칙 만들어줘", "GLOBAL_RULES 업데이트",
  "에이전트가 엉뚱한 걸 만들어", "출력 품질이 낮아졌어", "파이프라인 다음 단계 시작",
  "context setup", "rules file 만들어줘", "CLAUDE.md 업데이트".
user-invocable: true
allowed-tools: Read, Write
---

# Context Engineering

에이전트(Claude, Cursor)가 올바른 결과를 내려면 **올바른 정보를 올바른 시점에** 가져야 한다.
컨텍스트 부족 → 환각(hallucination). 컨텍스트 과잉 → 집중력 분산. 이 스킬은 파이프라인 전반에서
에이전트 컨텍스트를 의도적으로 설계하고 유지하는 방법을 정의한다.

---

## When to Use

| 상황 | 설명 |
|------|------|
| **새 프로젝트/세션 시작** | GLOBAL_RULES.md, .cursorrules 초기 설정 |
| **파이프라인 단계 전환** | req→IF→UF→구현 등 단계 바뀔 때 관련 아티팩트만 재로드 |
| **에이전트 출력 품질 저하** | 잘못된 패턴, 존재하지 않는 API 참조, 컨벤션 무시 |
| **Cursor 구현 세션 시작** | .cursorrules + /docs/ai 문서 최신화 확인 |
| **긴 대화 후 컨텍스트 오염** | 오래된 컨텍스트 정리, 세션 요약 후 재시작 |

---

## 컨텍스트 계층 구조

가장 지속적인 것 → 가장 일시적인 것 순서로 구성:

```
┌──────────────────────────────────────────┐
│ 1. Rules Files                           │ ← 항상 로드 (프로젝트 전역)
│    GLOBAL_RULES.md / .cursorrules        │
├──────────────────────────────────────────┤
│ 2. 설계 아티팩트 (단계별 선택 로드)       │ ← 현재 단계 관련 파일만
│    requirements.md / if_list.md / uf.md  │
├──────────────────────────────────────────┤
│ 3. 관련 소스 파일                        │ ← 현재 태스크 관련만
│    src/uf/<module>.py / tests/unit/...   │
├──────────────────────────────────────────┤
│ 4. 에러 출력 / 테스트 결과               │ ← 반복마다 갱신
│    실패 로그, pytest 출력                │
├──────────────────────────────────────────┤
│ 5. 대화 히스토리                         │ ← 누적, 주기적 정리
└──────────────────────────────────────────┘
```

---

## Phase A — Rules Files 설정

### GLOBAL_RULES.md (Claude용)

프로젝트 루트에 위치. 모든 Claude 세션에서 참조하는 최우선 컨텍스트.

```markdown
# GLOBAL_RULES.md

## 프로젝트 개요
- 프로젝트명: [프로젝트명]
- 기술 스택: [Python 3.11, numpy, torch, ...]
- 주요 도메인: [SAR / 신호처리 / 머신러닝 / ...]

## 파이프라인 스킬 규칙
- 설계는 core-engineering 파이프라인을 따른다: req → IF → UF → 구현
- 모든 UF는 uf.md에 정의된 I/O Contract를 반드시 따른다
- 테스트는 acceptance criteria(Given/When/Then)에서 직접 파생된다

## 코드 컨벤션
- 언어: Python (기본값)
- 함수명: uf_<id>_<동작>_<대상> 형식
- 타입 힌트 필수, Google-style docstring
- 테스트명: test_uf_<id>_<동작>_<조건> 형식

## 핵심 경로
- 설계 아티팩트: requirements.md, if_list.md, if_decomposition.md, uf.md
- 구현: src/uf/*.py, src/if/*.py
- 테스트: tests/unit/, tests/integration/
- 증거: evidence_pack/

## 경계 규칙
- uf.md에 없는 UF는 구현하지 않는다
- I/O Contract 없이 UF 함수를 만들지 않는다
- 라이브러리 추가 시 반드시 사용자에게 확인
```

### .cursorrules (Cursor용)

프로젝트 루트에 위치. Cursor Composer 세션에서 자동 로드.

```
# Cursor Rules — [프로젝트명]

## Architecture
- core-engineering pipeline: REQ → IF → UF → Implementation
- All UF specs in uf.md. Implementation follows I/O contracts exactly.
- Test files mirror src structure: src/uf/foo.py → tests/unit/test_foo.py

## Code Style
- Python, Google-style docstrings, type hints mandatory
- Function naming: uf_<id>_<verb>_<noun>
- Test naming: test_uf_<id>_<behavior>_<condition>

## Key Files (read before editing)
- /docs/ai/overview.md — system architecture
- /docs/ai/tasks/*.md — UF-level implementation context
- uf.md — UF Block specs (source of truth for I/O contracts)

## Implementation Rules
- Write tests FIRST from acceptance criteria, confirm FAIL, then implement
- No mock unless at system boundary (file I/O, network, hardware)
- No new libraries without user confirmation
```

---

## Phase B — 단계별 컨텍스트 로딩

파이프라인 단계마다 필요한 아티팩트만 선택적으로 로드한다.
**전체 스펙을 한 번에 넘기지 말 것** — 현재 작업과 무관한 컨텍스트는 집중력을 분산시킨다.

| 파이프라인 단계 | Claude에 로드할 컨텍스트 | Cursor에 로드할 컨텍스트 |
|----------------|------------------------|------------------------|
| req-elicitor | 문제 설명 자연어 | — |
| if-designer | requirements.md | — |
| uf-designer | if_decomposition.md | — |
| uf-implementor | uf.md (해당 IF 섹션만) | /docs/ai/tasks/uf_ifXX.md |
| if-integrator | if_list.md + src/uf/ 관련 파일 | /docs/ai/overview.md |
| uf-chain-validator | uf.md + tests/ 경로 | — |
| uf-if-debug-mapper | 에러 로그 + 관련 UF/IF 섹션 | — |

### 효율적 컨텍스트 블록 형식

```
[파이프라인 단계 전환 시 Claude에게 전달]

현재 단계: uf-implementor (UF-03 ~ UF-05)
관련 아티팩트:
  - uf.md의 IF-02 섹션 (UF-03, UF-04, UF-05 블록)
  - 기존 구현 참고: src/uf/if01_module.py (패턴 참조용)
제약:
  - numpy 배열 기반, torch 미사용
  - 120Hz 루프 내 실행, 타임아웃 8ms
완료 기준: uf-chain-validator Gate 1 PASS
```

---

## Phase C — 혼동 관리 (Confusion Management)

에이전트가 모호함을 조용히 추측하면 비용이 크다. 명확하게 표면화하고 확인받는다.

### 컨텍스트 충돌 시

```
[CONFUSION]
requirements.md: 실시간 처리 (≤8ms) 요구
uf.md UF-05: 배치 처리 알고리즘 명시

선택지:
A) uf.md 우선 — UF-05를 스트리밍으로 재설계
B) 실시간 요구 완화 — 사용자에게 허용 지연 재확인

→ 어느 방향으로 진행할까요?
```

### 요구사항 공백 시

uf.md에 없는 동작은 구현하지 않는다. 멈추고 확인한다:

```
[MISSING REQUIREMENT]
UF-07의 엣지케이스: 빈 입력 배열 처리가 명세에 없음

선택지:
A) ValueError 발생 (엄격)
B) 빈 배열 그대로 반환 (관대)

→ 어떻게 처리할까요?
```

### 인라인 플랜 패턴 (다단계 태스크 시작 전)

```
[PLAN]
1. uf.md에서 UF-03~05 블록 파싱
2. tests/unit/test_if02.py에 acceptance criteria 테스트 작성 (RED)
3. src/uf/if02_module.py 구현 (GREEN)
4. uf-chain-validator Gate 1 실행
→ 진행합니다.
```

---

## Phase D — 컨텍스트 오염 감지 및 정리

### 오염 징후

| 징후 | 원인 | 조치 |
|------|------|------|
| 존재하지 않는 함수/모듈 참조 | 컨텍스트 starvation 또는 오래된 코드 참조 | rules file 재로드, 실제 파일 확인 |
| 이전 단계 아티팩트 기준으로 작업 | 단계 전환 시 컨텍스트 미정리 | 현재 단계 관련 파일만 재로드 |
| 컨벤션 무시 (naming, docstring 등) | rules file 미반영 | .cursorrules / GLOBAL_RULES 업데이트 |
| 긴 대화 후 품질 저하 | 히스토리 누적 | 세션 요약 → 새 세션 시작 |

### 세션 교체 시 요약 포맷

```
[세션 요약]
완료: UF-01~05 구현, Gate 1 PASS
미완료: UF-06 (알고리즘 미확정), Gate 2 검증
다음 작업: uf.md UF-06 블록 → uf-implementor
핵심 결정: UF-04는 numpy vectorize 사용 (torch보다 8ms 이내 처리 가능)
관련 파일: src/uf/if02_module.py, tests/unit/test_if02.py
```

---

## 안티패턴

| 안티패턴 | 문제 | 해결 |
|---|---|---|
| **컨텍스트 기아** | 에이전트가 API/함수를 환각 | rules file + 관련 소스 파일 로드 |
| **컨텍스트 과잉** | 5,000줄 이상 비관련 파일 → 집중력 분산 | 현재 태스크 관련 파일만 (목표: 2,000줄 이내) |
| **오래된 컨텍스트** | 삭제된 코드, 이전 설계를 참조 | 긴 대화 후 세션 교체 |
| **예시 없는 컨텍스트** | 에이전트가 새 스타일 발명 | 기존 구현 1개를 패턴 참조로 포함 |
| **암묵적 지식** | rules file에 없으면 에이전트에게 없는 것 | GLOBAL_RULES.md에 명시 |
| **조용한 추측** | 모호한 요구를 에이전트가 혼자 결정 | CONFUSION 블록으로 표면화 |

---

## 출력 (실행 결과물)

이 스킬은 다음 중 필요한 것을 생성/업데이트한다:

| 파일 | 설명 | 위치 |
|------|------|------|
| `GLOBAL_RULES.md` | Claude용 프로젝트 전역 규칙 | 프로젝트 루트 |
| `.cursorrules` | Cursor용 구현 규칙 | 프로젝트 루트 |
| `docs/ai/overview.md` | 시스템 아키텍처 요약 (repo-doc-writer와 연계) | /docs/ai/ |
| 세션 요약 블록 | 세션 교체 시 컨텍스트 전달용 | 대화 내 또는 임시 파일 |

> **repo-doc-writer와의 관계:** repo-doc-writer는 설계 아티팩트 → /docs/ai 변환을 담당한다.
> context-engineering은 그 문서를 **언제, 어떻게 에이전트에게 공급할지**를 결정한다.

---

## 실행 체크리스트

```
□ GLOBAL_RULES.md 존재 여부 확인 (없으면 생성)
□ .cursorrules 최신 상태 확인 (uf.md 구조 반영 여부)
□ 현재 파이프라인 단계에 맞는 아티팩트만 로드
□ 에이전트 출력이 실제 파일 경로/함수를 참조하는지 확인
□ 긴 대화 후 세션 교체 필요 여부 판단 (품질 저하 시)
□ 모호한 요구사항은 CONFUSION 블록으로 표면화 후 진행
```
