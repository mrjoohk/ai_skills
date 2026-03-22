---
name: defense-diagram
description: >
  방산 연구 제안서용 개념도·블록다이어그램·시스템 구성도·연구개발 개념도를 일관된 디자인으로 생성한다.
  MANDATORY TRIGGERS: "개념도 그려줘", "블락다이어그램", "시스템 구성도", "R&D 개념도", "다이어그램 만들어줘",
  "그림 만들어줘", "diagram", "block diagram", "concept figure", "연구개발 개념도", "기술 구조도",
  제안서 그림이 언급될 때마다 이 스킬을 사용할 것.
  모든 출력 그림은 반드시 design-system.md의 색상·폰트·스타일을 따른다.
---

# Defense Diagram Skill

방산 연구 제안서에 들어가는 모든 시각 자료를 **일관된 디자인 언어**로 생성하는 스킬.
하나의 제안서 내 다이어그램들이 통일된 느낌을 주도록, 모든 생성은 동일한 디자인 시스템을 따른다.

> 📖 **디자인 시스템**: 시작 전 반드시 `references/design-system.md`를 읽어 색상 토큰, 폰트 규칙, 레이아웃 가이드를 숙지할 것.

---

## Step 0 — 디자인 시스템 로드

작업 시작 시 `references/design-system.md`를 읽는다. 이 파일의 색상 팔레트, 폰트, SVG defs 헤더, AI 프롬프트 템플릿을 이 세션 전체에서 적용한다.

---

## Step 1 — 다이어그램 유형 및 내용 파악

사용자 요청에서 다음을 추출한다:

1. **다이어그램 유형** — 아래 중 하나를 선택:
   - `(A) 개념도` — 기술의 개념/원리를 시각화
   - `(B) 블록다이어그램` — 신호·데이터·처리 흐름
   - `(C) 시스템 구성도` — 구성요소 간 관계 및 인터페이스
   - `(D) 연구개발 개념도` — 연구 배경/목표/접근법을 한 장에 요약
   - `(E) 기술 비교도` — 기존 기술 vs 제안 기술 대비
   - `(F) 일반 플로우차트` — 프로세스 흐름 / 절차도

2. **핵심 요소** — 그림에 반드시 포함되어야 할 블록/모듈/개념 목록
3. **흐름 방향** — 좌→우 (기본) / 상→하 / 중앙 방사형
4. **강조할 기술/차별점** — ACCENT 색상을 적용할 요소
5. **제안서 내 번호** — `그림 N.` 캡션에 사용

정보가 불충분하면 핵심 3가지만 질문하고, 나머지는 합리적으로 판단해 진행한다.

---

## Step 2 — 출력 방식 결정

### 기본: SVG 직접 생성
대부분의 블록/플로우 다이어그램은 SVG로 직접 생성한다.

**SVG 생성 원칙:**
- `references/design-system.md`의 "SVG 공통 헤더 템플릿" defs 블록을 모든 SVG 파일 상단에 포함
- 캔버스 크기: 가로 900px × 세로 600px (기본), 복잡한 경우 1100×700
- 한국어 텍스트는 `<text>` 태그에 직접 삽입 (foreignObject 금지)
- 파일명: `fig_N_[유형]_[제목약어].svg`

### 기술 개념 강조가 필요한 경우: AI 이미지 생성 프롬프트 제공
구성요소의 물리적 형태나 운용 개념(무기체계, 센서, 플랫폼 등)을 시각화할 때는
직접 SVG 대신 **AI 이미지 생성 프롬프트**를 제공한다.

→ `references/design-system.md`의 "AI 이미지 생성용 프롬프트 템플릿"을 기반으로 작성.
→ NotebookLM, 나노바나나2, 또는 기타 AI 이미지 도구에 붙여넣을 수 있도록 상세하게 작성.
→ 스타일 토큰(색상, 폰트, 레이아웃)을 프롬프트에 명시적으로 포함.

---

## Step 3 — SVG 생성 절차

### 3-1. 레이아웃 스케치 (텍스트)
코드를 작성하기 전에 아래 형식으로 레이아웃을 먼저 정리한다:

```
[블록명 | 색상 | 크기(W×H) | 위치(x,y)]
→ 화살표 →
[블록명 | 색상 | 크기(W×H) | 위치(x,y)]
```

### 3-2. SVG 코드 작성

색상 규칙:
- 주요 기능 블록 헤더: `fill="#1B3A6B"` (PRIMARY), 텍스트 `fill="white"`
- 서브 모듈: `fill="#2E6DA4"` (SECONDARY), 텍스트 `fill="white"`
- 일반 박스: `fill="#F4F7FC"` (BACKGROUND), 테두리 `stroke="#C5D5E8"`
- 핵심 기술/차별점 강조: `fill="#C8962E"` (ACCENT)
- 확보 기술: `stroke="#2E7D51"`, 미확보 기술: `stroke="#B85C1A"`

화살표:
- 일반 흐름: `marker-end="url(#arrowhead)"` (SECONDARY 색상)
- 주요 흐름: `marker-end="url(#arrowhead-primary)"` (PRIMARY 색상)
- 인터페이스: 양방향 화살표

텍스트:
- 블록 레이블: `class="label-primary"` 또는 `class="label-secondary"`
- 설명: `class="label-desc"`
- 화살표 레이블: `class="label-arrow"`

캡션 (하단):
```svg
<text x="[중앙x]" y="[하단y+30]" text-anchor="middle"
      font-size="10" fill="#6B7280" font-style="italic">
  그림 N. [그림 제목]
</text>
```

### 3-3. 완성 후 품질 체크
`references/design-system.md`의 "품질 체크리스트" 7개 항목을 확인한다.

---

## Step 4 — AI 이미지 생성 프롬프트 작성 절차

기술 개념도가 사실적 묘사나 운용 개념 표현이 필요할 때:

1. **기술 요소 목록화**: 그림에 담을 핵심 기술 요소, 플랫폼, 환경을 나열
2. **장면 서술**: "무엇이 어디서 어떻게 작동하는가"를 구체적으로 서술
3. **디자인 토큰 삽입**: `design-system.md`의 스타일 토큰 전체를 프롬프트 말미에 추가
4. **일관성 키워드 강조**: "consistent with previous diagrams in this proposal", "same color scheme"

**프롬프트 출력 형식:**
```
=== AI 이미지 생성 프롬프트 (그림 N. [제목]) ===

[장면 서술 — 한국어]

--- 영어 프롬프트 (NotebookLM / AI 도구용) ---
[영어 프롬프트]

Style tokens (MUST include):
[design-system.md의 영어 스타일 토큰]

Negative prompt: 3D renders, photorealistic, cartoon, gradients, dark background,
clip art, drop shadows, decorative borders
===
```

---

## Step 5 — 파일 저장 및 목록 기록

1. SVG 파일을 `[작업폴더]/figures/` 에 저장
2. AI 프롬프트는 `[작업폴더]/figures/prompts/fig_N_prompt.md` 에 저장
3. `GLOBAL_RULES.md` Rule 4에 따라 `0.FilesUpdate.xlsx`에 로그 기록

---

## 다이어그램 유형별 빠른 참조

| 유형 | 레이아웃 | 주요 색상 | 참고 |
|---|---|---|---|
| (A) 개념도 | 맥락→기술→효과 | PRIMARY 중심 + ACCENT 강조 | design-system.md §4-A |
| (B) 블록다이어그램 | 좌→우 흐름 | PRIMARY + SECONDARY | design-system.md §4-B |
| (C) 시스템 구성도 | 계층 또는 중앙 | SECONDARY 중심 | design-system.md §4-C |
| (D) R&D 개념도 | 문제→기술→효과 | 3단 레이어 | design-system.md §4-D |
| (E) 기술 비교도 | 좌(기존) vs 우(제안) | 기존:NEUTRAL / 제안:PRIMARY | — |
| (F) 플로우차트 | 상→하 | SECONDARY | — |

---

## 예시

**사용자**: "레이더 신호처리 블록다이어그램 그려줘. 안테나→수신기→ADC→DSP→CFAR→목표탐지 순서야."

**처리 흐름**:
1. 유형: (B) 블록다이어그램, 흐름: 좌→우
2. 레이아웃: 안테나(PRIMARY) → 수신기(SECONDARY) → ADC(BG) → DSP(PRIMARY) → CFAR(ACCENT, 핵심기술) → 목표탐지(PRIMARY)
3. SVG 생성, 화살표 SECONDARY 색상, CFAR 블록 ACCENT 강조
4. 그림 캡션: "그림 N. 레이더 신호처리 블록다이어그램"
