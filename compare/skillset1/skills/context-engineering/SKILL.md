---
name: context-engineering
description: >
  새 프로젝트/세션 시작 시 에이전트 설정 파일을 자동 생성하는 스킬.
  가상환경 Python 경로와 API 키를 사용자에게 요청한 뒤, GLOBAL_RULES.md 준수 지시 +
  핵심 아티팩트 경로를 담은 CLAUDE.md / AGENTS.md / GEMINI.md 를 프로젝트 루트에 생성한다.
  긴 작업의 맥락 관리 규칙(요청마다 새 세션 또는 state.md)도 함께 넣는다.
  트리거: "세션 시작", "에이전트 설정", "context setup", "CLAUDE.md 만들어줘",
  "AGENTS.md 만들어줘", "GEMINI.md 만들어줘", "새 프로젝트 시작", "venv 설정",
  "맥락 관리", "state.md".
user-invocable: true
allowed-tools: Read, Write
---

# Context Engineering

에이전트(Claude / Cursor / Codex / Antigravity 등)가 프로젝트 규칙과 아티팩트 경로를
처음부터 올바르게 인식하도록 **에이전트 설정 파일 3종**을 생성한다.

---

## When to Use

- 새 프로젝트를 시작할 때 (저장소 clone 직후)
- 기존 프로젝트에 새 에이전트를 추가할 때
- 에이전트 설정 파일이 없거나 최신 GLOBAL_RULES.md 를 반영하지 못할 때
- 기존 설정 파일에 '긴 작업 규칙(맥락 관리)'이 없을 때 — 그 섹션만 더한다

---

## Step 1 — 사용자에게 정보 요청

다음 두 가지를 순서대로 질문한다.

### 1-A. Python 실행파일 경로 (필수)

```
가상환경의 Python 실행파일 경로를 알려주세요.

예시)
  Linux/macOS : .venv/bin/python
  Windows     : .venv\Scripts\python.exe
  Conda       : /opt/conda/envs/myenv/bin/python
```

### 1-B. API 키 (선택)

```
프로젝트에서 사용하는 API 키가 있다면 알려주세요.
(없으면 Enter — 설정 파일에서 해당 섹션을 생략합니다)

예시)
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  GEMINI_API_KEY=AI...
```

> 수집한 API 키는 에이전트 설정 파일에만 기록하고 다른 용도로 사용하지 않는다.

---

## Step 2 — 에이전트 설정 파일 생성

수집한 정보로 프로젝트 루트에 3개 파일을 생성한다.
세 파일은 동일한 구조를 가지며, 각 에이전트가 자동으로 읽는 관례 파일명을 따른다.

| 파일명 | 대상 에이전트 |
|--------|--------------|
| `CLAUDE.md` | Claude (Anthropic) |
| `AGENTS.md` | Codex / OpenAI Agents, Antigravity, 기타 |
| `GEMINI.md` | Gemini (Google) |

### 파일 템플릿

```markdown
# Agent Configuration

## 핵심 규칙
이 프로젝트의 모든 작업은 **`GLOBAL_RULES.md`의 지침을 따른다**.
작업 시작 전 반드시 `GLOBAL_RULES.md`를 읽을 것.

## 실행 환경
- Python 실행파일: <사용자가 입력한 경로>
- 가상환경 기준 경로: 프로젝트 루트

<!-- API 키가 있는 경우에만 포함 -->
## API 키
<키=값 목록>
<!-- end API 키 섹션 -->

## 핵심 아티팩트 경로 (프로젝트 루트 기준)

### 설계 문서
- 요구사항      : `rd/requirements.md`
- IF 목록        : `rd/if_list.md`
- IF 분해 트리   : `rd/if_decomposition.md`
- UF 명세        : `rd/uf.md`
- UF 분할 파일   : `rd/uf_split/uf_ifXX.md`

### 구현
- UF 구현        : `./src/uf/`
- IF 통합 모듈   : `./src/if/`

### 테스트
- 단위 테스트    : `./tests/unit/`
- 통합 테스트    : `./tests/integration/`

### 증거 및 보고서
- 증거 팩        : `./evidence_pack/`
- 평가/보고서    : `./reports/`
- Cursor용 태스크: `./docs/ai/`

## 파이프라인 순서
req-elicitor → if-designer → uf-designer → uf-implementor
→ if-integrator → uf-chain-validator → eval-planner → eval-runner
→ ci-evidence-automation → project-summarizer

## 긴 작업 규칙 (맥락 관리)
- 요청(P-xxx) 하나가 길어질 것 같으면(설계 갈림길·여러 회차 검토·무거운 증거 실행) **새 세션에서 시작**하는 것을 기본으로 한다.
- 한 세션에서 이어 갈 때는 단계마다 `logs/<P-xxx>_evidence/state.md` 를 갱신한다 — 요청 원문·범위, 결정(D-xxx),
  남은 일, 검토 보고·처분표 경로, 증거 실행 상태. 맥락이 압축된 뒤에는 **이 파일부터** 읽는다.
- 큰 파일 읽기·넓은 검색·탐침은 하위 에이전트에 맡기고, 본 맥락에는 결론과 파일 경로만 남긴다.
- 하위 에이전트(검토자 포함)의 보고는 대화 답이 아니라 **파일**로 남기게 한다 — 압축에도 남는다.
```

### state.md 템플릿 (긴 작업 규칙)

`logs/<P-xxx>_evidence/state.md` — 단계가 끝날 때마다 덮어쓴다(지난 내용은 결정·검토 절에 누적).

```markdown
# <P-xxx> 상태 — <요청 한 줄>   (갱신: YYYY-MM-DD HH:MM)

## 요청
- 원문: "<사용자 요청 그대로>"
- 범위: <할 일 / 하지 않을 일 — 범위 확인 결과>

## 결정
- D-xxx: <결정 한 줄> — 근거 <비교표·데이터 경로>

## 진행
- [x] <끝난 단계>
- [ ] <남은 단계>  ← 지금

## 검토
- round<n>: 보고 <경로> · 처분표 <경로> · 열린 지적 <ID 목록>

## 증거 실행
- 변이: 명세 <경로> · 결과 <경로> · 남은 것 <수 / 이어 갈 명령>
- 시험: <명령> → <결과 요약>

## 다음에 읽을 것
- <파일:줄 — 왜>
```

판단 근거: 한 세션에서 여러 요청을 이어 하다 맥락이 압축되면, 대화에만 있던 검토 보고·결정 근거가 사라져 같은 지적이
다시 나온다(판례 drmHWP P-041 — P-036~P-041 을 한 세션에서 이어 하다 788K 토큰에서 압축, 1차 검토 보고 원문이 맥락에서
빠져 다음 회차 전에 대조하지 못함). 파일은 압축과 세션을 넘어 남는다.

---

## Step 3 — 검증

생성 후 다음을 확인한다.

```
□ CLAUDE.md  — 프로젝트 루트에 존재
□ AGENTS.md  — 프로젝트 루트에 존재
□ GEMINI.md  — 프로젝트 루트에 존재
□ 세 파일 모두 동일한 Python 경로와 API 키를 포함
□ GLOBAL_RULES.md 참조 지시문이 각 파일 상단에 위치
□ '긴 작업 규칙 (맥락 관리)' 섹션이 세 파일에 모두 있음
□ GLOBAL_RULES.md 파일 자체가 프로젝트 루트에 존재하는지 확인
  → 없으면 사용자에게 알리고 core-engineering 파이프라인 시작 전 생성 요청
```

---

## 출력 요약

```
생성 완료:
  ./CLAUDE.md
  ./AGENTS.md
  ./GEMINI.md

Python 경로 : <입력값>
API 키      : <있음 / 없음>
GLOBAL_RULES.md : <존재 / 없음 — 생성 필요>
```

---

## 주의

- 이 스킬은 **GLOBAL_RULES.md를 생성하지 않는다**.
  GLOBAL_RULES.md 작성은 core-engineering 파이프라인의 req-elicitor 또는
  별도 수동 작업으로 처리한다.
- API 키는 `.gitignore`에 추가할 것을 사용자에게 권고한다.
  (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md` 모두 버전 관리에서 제외 권장)
