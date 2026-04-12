---
name: context-engineering
description: >
  새 프로젝트/세션 시작 시 에이전트 설정 파일을 자동 생성하는 스킬.
  가상환경 Python 경로와 API 키를 사용자에게 요청한 뒤, GLOBAL_RULES.md 준수 지시 +
  핵심 아티팩트 경로를 담은 CLAUDE.md / AGENTS.md / GEMINI.md 를 프로젝트 루트에 생성한다.
  트리거: "세션 시작", "에이전트 설정", "context setup", "CLAUDE.md 만들어줘",
  "AGENTS.md 만들어줘", "GEMINI.md 만들어줘", "새 프로젝트 시작", "venv 설정".
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
- 요구사항      : `./requirements.md`
- IF 목록        : `./if_list.md`
- IF 분해 트리   : `./if_decomposition.md`
- UF 명세        : `./uf.md`
- UF 분할 파일   : `./uf_split/uf_ifXX.md`

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
req-elicitor → if-designer → uf-designer → repo-doc-writer
→ cursor-task-formatter (Mode A) → Cursor 구현 → code-reviewer
→ cursor-task-formatter (Mode B) → uf-chain-validator → project-summarizer
```

---

## Step 3 — 검증

생성 후 다음을 확인한다.

```
□ CLAUDE.md  — 프로젝트 루트에 존재
□ AGENTS.md  — 프로젝트 루트에 존재
□ GEMINI.md  — 프로젝트 루트에 존재
□ 세 파일 모두 동일한 Python 경로와 API 키를 포함
□ GLOBAL_RULES.md 참조 지시문이 각 파일 상단에 위치
□ GLOBAL_RULES.md 파일 자체가 프로젝트 루트에 존재하는지 확인
  → 없으면 사용자에게 알리고 파이프라인 시작 전 생성 요청
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
  GLOBAL_RULES.md 작성은 파이프라인의 req-elicitor 또는
  별도 수동 작업으로 처리한다.
- API 키는 `.gitignore`에 추가할 것을 사용자에게 권고한다.
  (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md` 모두 버전 관리에서 제외 권장)
