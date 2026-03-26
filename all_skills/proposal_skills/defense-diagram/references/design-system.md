# Defense Proposal — Diagram Design System

방산 연구 제안서에 사용되는 모든 다이어그램은 이 디자인 시스템을 반드시 따른다.
하나의 제안서 내 모든 그림이 "같은 손에서 나온 것"처럼 보여야 한다.

---

## 1. 색상 팔레트 (Color Tokens)

| 토큰 이름 | HEX | 용도 |
|---|---|---|
| `COLOR_PRIMARY` | `#1B3A6B` | 주요 박스·헤더·강조 영역 |
| `COLOR_SECONDARY` | `#2E6DA4` | 서브 컴포넌트·화살표·선 |
| `COLOR_ACCENT` | `#C8962E` | 핵심 기술·차별점 강조 |
| `COLOR_NEUTRAL_DARK` | `#3D3D3D` | 일반 텍스트·레이블 |
| `COLOR_NEUTRAL_MID` | `#6B7280` | 보조 설명·부제목 |
| `COLOR_BACKGROUND` | `#F4F7FC` | 박스 내부 배경 |
| `COLOR_WHITE` | `#FFFFFF` | 슬라이드 배경 |
| `COLOR_BORDER` | `#C5D5E8` | 박스 테두리 |
| `COLOR_SUCCESS` | `#2E7D51` | 확보 기술·완료 항목 |
| `COLOR_WARNING` | `#B85C1A` | 미확보 기술·위험 항목 |

### 사용 비율 원칙
- PRIMARY : SECONDARY : ACCENT = 50% : 35% : 15%
- 배경은 항상 WHITE 또는 BACKGROUND, 절대 진한 색 배경 사용 금지

---

## 2. 폰트 규칙 (Typography)

| 역할 | 폰트 | 크기 | 굵기 | 색상 |
|---|---|---|---|---|
| 그림 제목 | Malgun Gothic / NanumGothic | 13pt | Bold | COLOR_PRIMARY |
| 블록 레이블 | Malgun Gothic / NanumGothic | 10–11pt | Bold | WHITE 또는 NEUTRAL_DARK |
| 설명 텍스트 | Malgun Gothic / NanumGothic | 9–10pt | Regular | NEUTRAL_DARK |
| 화살표 레이블 | Malgun Gothic / NanumGothic | 8–9pt | Regular | SECONDARY |
| 캡션 | Malgun Gothic / NanumGothic | 8pt | Regular | NEUTRAL_MID |

---

## 3. 도형 스타일

### 박스/블록
- 모서리 반경: `rx=6` (SVG) / `6pt` (pptx)
- 테두리 두께: `2px` (SVG)
- 그림자: 없음 (flat design)
- 패딩: 텍스트에서 최소 8px 여백

### 화살표/흐름선
- 끝: 솔리드 filled arrowhead (`marker-end: url(#arrowhead)`)
- 선 두께: `2px` (일반), `3px` (주요 흐름)
- 스타일: 직선 또는 L자형 꺾임 — 대각선/곡선 지양
- 양방향 화살표: 인터페이스/상호작용 연결에만 사용

### 계층 표현
- 시스템 → 서브시스템 → 구성요소: 박스 크기 및 색상 depth로 표현
  - 시스템: 큰 테두리 박스, COLOR_PRIMARY 헤더
  - 서브시스템: 중간 박스, COLOR_SECONDARY 헤더
  - 구성요소: 작은 박스, COLOR_BACKGROUND 배경

---

## 4. 다이어그램 유형별 레이아웃 규칙

### (A) 개념도 (Concept Diagram)
```
[배경/환경 컨텍스트] — 연한 회색 영역
  ├── [핵심 기술 블록] — COLOR_PRIMARY, 중앙
  ├── [입력 요소들] — 왼쪽 또는 상단
  └── [출력/효과] — 오른쪽 또는 하단
[범례] — 우측 하단, 소형
```
- 좌→우 또는 상→하 흐름
- 핵심 기술 블록은 다른 블록보다 1.5배 크게
- 기술적 장점은 ACCENT 색상 버블/배지로 표시

### (B) 블록 다이어그램 (Block Diagram)
```
[입력] → [처리 블록 1] → [처리 블록 2] → [출력]
                              ↕
                        [서브 모듈]
```
- 처리 흐름은 엄격하게 좌→우
- 계층 구조는 위→아래로 분기
- 데이터 흐름과 제어 흐름은 선 스타일로 구분 (solid vs dashed)

### (C) 시스템 구성도 (System Architecture)
- 외부 환경/운영 영역: 점선 테두리 박스
- 내부 개발 범위: 실선 테두리 박스
- 인터페이스: 양방향 화살표 + 인터페이스 이름 레이블

### (D) 연구개발 개념도 (R&D Concept)
- 상단: 문제/필요성 영역 (연한 배경)
- 중앙: 제안 기술/솔루션 (강조 영역)
- 하단: 기대 효과/성과 영역
- 좌측: 현재 상태 (Before)
- 우측: 연구 후 상태 (After)

---

## 5. AI 이미지 생성용 프롬프트 템플릿

AI 도구(이미지 생성)로 기술 개념도를 생성할 때는 아래 스타일 토큰을 모든 프롬프트에 포함해야 한다.

### 기본 스타일 토큰 (한국어 제안서용)
```
스타일 지침:
- 배경: 흰색 또는 매우 연한 회색 (#F4F7FC)
- 주색상: 네이비 블루 (#1B3A6B), 스틸 블루 (#2E6DA4)
- 강조색: 골드/암버 (#C8962E) — 핵심 기술 요소에만 사용
- 폰트: 깔끔한 sans-serif, 한국어 지원
- 스타일: 플랫 디자인, 그림자 없음, 전문적·공식적
- 박스 모서리: 약간 둥글게 (round corners)
- 화살표: 직선, 솔리드 필드 헤드
- 절대 금지: 3D 효과, 그라디언트 배경, 클립아트 스타일, 사실적 사진 요소
```

### 영어 프롬프트 (NotebookLM / 기타 AI 도구용)
```
Style: Clean flat design technical diagram, white background,
navy blue (#1B3A6B) primary blocks, steel blue (#2E6DA4) secondary elements,
gold accent (#C8962E) for key technology highlight only.
Typography: Bold sans-serif labels, no decorative fonts.
Layout: Left-to-right flow or top-to-bottom hierarchy.
Arrows: Solid black with filled arrowheads, straight lines.
No shadows, no gradients, no 3D effects. Professional military/defense domain.
Consistent with other diagrams in the same proposal document.
```

---

## 6. SVG 공통 헤더 템플릿

모든 SVG 파일의 상단에 아래 defs 블록을 포함할 것:

```svg
<defs>
  <!-- 화살표 마커 -->
  <marker id="arrowhead" markerWidth="10" markerHeight="7"
          refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#2E6DA4"/>
  </marker>
  <marker id="arrowhead-primary" markerWidth="10" markerHeight="7"
          refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#1B3A6B"/>
  </marker>
  <marker id="arrowhead-accent" markerWidth="10" markerHeight="7"
          refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#C8962E"/>
  </marker>
  <!-- 폰트 -->
  <style>
    text { font-family: 'Malgun Gothic', 'NanumGothic', 'Apple SD Gothic Neo', sans-serif; }
    .label-primary { font-size: 11px; font-weight: bold; fill: #FFFFFF; }
    .label-secondary { font-size: 10px; font-weight: bold; fill: #1B3A6B; }
    .label-desc { font-size: 9px; fill: #3D3D3D; }
    .label-arrow { font-size: 8px; fill: #2E6DA4; }
    .box-primary { fill: #1B3A6B; stroke: #1B3A6B; stroke-width: 2; rx: 6; }
    .box-secondary { fill: #2E6DA4; stroke: #2E6DA4; stroke-width: 2; rx: 6; }
    .box-bg { fill: #F4F7FC; stroke: #C5D5E8; stroke-width: 1.5; rx: 6; }
    .box-accent { fill: #C8962E; stroke: #C8962E; stroke-width: 2; rx: 6; }
  </style>
</defs>
```

---

## 7. 품질 체크리스트

다이어그램 완성 후 아래 항목을 반드시 확인:

- [ ] 색상이 디자인 토큰 팔레트에서만 사용되었는가?
- [ ] 모든 텍스트가 배경과 충분한 대비를 가지는가? (어두운 배경 → 흰 텍스트)
- [ ] 화살표 방향이 흐름/관계를 올바르게 나타내는가?
- [ ] 그림 제목이 좌측 상단 또는 하단 캡션으로 명시되었는가?
- [ ] 같은 제안서의 다른 그림들과 동일한 박스 크기/스타일인가?
- [ ] 번호 표기: `그림 N. [그림 제목]` 형식으로 캡션 작성
