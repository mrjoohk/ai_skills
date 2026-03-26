---
name: defense-wbs-tbs
description: >
  방산 연구 제안서용 WBS(작업분류체계), TBS(기술분류체계), 추진 일정(간트차트), 마일스톤 표를 생성하고 PPTX 슬라이드 및 xlsx로 만든다.
  MANDATORY TRIGGERS: "WBS 만들어줘", "TBS 만들어줘", "간트차트", "추진 일정", "마일스톤",
  "작업분류체계", "기술분류체계", "일정 계획 표", "연구 일정", "WBS 다이어그램".
  방산 제안서에서 WBS, TBS, 간트차트, 일정 표가 언급되면 이 스킬을 사용할 것.
---

# Defense WBS/TBS 스킬

방산 연구 제안서에 필요한 **WBS, TBS, 추진 일정 계획** 시각 자료를 생성한다.
xlsx(데이터) + SVG(계층 다이어그램) + PPTX(슬라이드) 형태로 일관된 출력을 제공한다.

---

## Step 1 — 기본 구조 정보 수집

필요 정보:
- 연구 과제명 및 체계 구성 (구성품 목록)
- 연구 기간 (시작년월 ~ 종료년월)
- 단계 구분 (예: 1단계 2년 + 2단계 3년)
- 세부과제 수 및 명칭
- 주요 기술 분야

---

## Step 2 — WBS 생성

### WBS 설계 원칙

```
WBS 코드 체계: 1.0 > 1.1 > 1.1.1 > 1.1.1.1
분해 원칙:
  - 100% 규칙: 상위 항목 = 하위 항목의 합
  - 상호 배타적: 항목 간 중복 없음
  - 완전 포괄적: 연구 범위 내 모든 작업 포함
  - 최하위 수준: 1–2개월 단위의 작업 패키지
```

### WBS 계층 다이어그램 (SVG)

**defense-diagram 스킬**로 계층 트리 생성:
- 최상위(L0): COLOR_PRIMARY 큰 박스
- L1: COLOR_SECONDARY 박스
- L2: COLOR_BACKGROUND 박스, 테두리 COLOR_BORDER
- 연결선: 직선, COLOR_NEUTRAL_MID

**SVG 레이아웃**: 좌→우 방향 트리 또는 상→하 트리
- L2까지만 다이어그램 표현 (L3는 표로 처리)

### WBS 상세 표 (xlsx)

다음 Python 코드를 실행하여 xlsx 생성:

```python
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

# WBS 데이터 구조
wbs_data = [
    # (코드, 항목명, 레벨, 담당, 기간, 예산, 비고)
]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "WBS"

# 헤더
headers = ["WBS 코드", "항목명", "수준", "담당기관", "기간", "예산(백만원)", "비고"]
header_fill = PatternFill(start_color="1B3A6B", end_color="1B3A6B", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF", name="맑은 고딕")

for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

# L1 행: SECONDARY 색상
l1_fill = PatternFill(start_color="2E6DA4", end_color="2E6DA4", fill_type="solid")
l1_font = Font(bold=True, color="FFFFFF", name="맑은 고딕")

# L2 행: BACKGROUND 색상
l2_fill = PatternFill(start_color="F4F7FC", end_color="F4F7FC", fill_type="solid")

wb.save("WBS.xlsx")
```

실제 데이터로 채워서 실행하고 파일을 저장한다.

---

## Step 3 — TBS 생성

### TBS 설계 원칙

```
TBS 코드 체계: T1 > T1.1 > T1.1.1
분류 기준:
  - 기능별 그룹핑 (탐지/처리/통신/구동 등)
  - WBS와 크로스 매핑 가능한 구조
  - TRL 수준 추적 가능
```

### TBS 계층 다이어그램 (SVG)

**defense-diagram 스킬**로 계층 트리 생성:
- 기확보 기술: COLOR_SUCCESS(#2E7D51) 테두리
- 미확보 기술: COLOR_WARNING(#B85C1A) 테두리
- TRL 배지: 각 박스 우측 상단에 원형 배지 (숫자)

### TBS 상세 표

| TBS 코드 | 기술명 | 기술 설명 | 현재 TRL | 목표 TRL | 확보 여부 | 비고 |
|---|---|---|---|---|---|---|
| T1 | [기술 그룹 1] | | — | — | — | |
| T1.1 | [단위 기술] | [설명] | 4 | 7 | 미확보 | |

---

## Step 4 — 추진 일정 (간트차트) 생성

### 간트차트 SVG 생성

Python으로 SVG 간트차트 생성:

```python
import xml.etree.ElementTree as ET

# 파라미터
tasks = [
    # (WBS코드, 작업명, 시작월, 기간개월, 담당, 유형)
    # 유형: "task" | "milestone" | "phase"
]

# 레이아웃
ROW_H = 30          # 행 높이
LABEL_W = 200       # 작업명 열 너비
MONTH_W = 35        # 월당 너비
COLORS = {
    "phase":     "#1B3A6B",
    "task":      "#2E6DA4",
    "milestone": "#C8962E",
    "done":      "#2E7D51",
}

# SVG 생성 (각 행에 색상 막대 + 마일스톤 다이아몬드 ◆)
# 헤더: 연도 + 분기(Q1/Q2/Q3/Q4) 또는 월
# 마일스톤: 해당 열에 ◆ 기호
```

**간트차트 스타일:**
- 배경: 흰색, 격자선: 연한 회색 (#E5E7EB)
- Phase 막대: COLOR_PRIMARY (불투명)
- Task 막대: COLOR_SECONDARY (약간 투명하게)
- 마일스톤: ◆ 기호, COLOR_ACCENT
- 완료 항목: COLOR_SUCCESS

### 마일스톤 목록 표

| 번호 | 마일스톤명 | 시점 | 합격 기준 | 평가 방법 |
|---|---|---|---|---|
| M1 | 개념 설계 완료 | 1차년 Q4 | [기준] | 내부 검토 |
| M2 | 시제품 1차 제작 | 2차년 Q2 | [기준] | 기능 시험 |

---

## Step 5 — PPTX 슬라이드 생성

`pptx 스킬`을 사용하여 생성.

**슬라이드 구성:**
```
1. WBS 계층 다이어그램 (SVG 삽입)
2. WBS 상세 표 (핵심 L2까지)
3. TBS 계층 다이어그램 (SVG 삽입)
4. 추진 일정 간트차트 (SVG 삽입, 가로형 레이아웃)
5. 마일스톤 목록 표
```

**슬라이드 레이아웃**: 가로(Landscape) 16:9 — 간트차트는 전체 슬라이드 폭 활용

---

## Step 6 — 파일 저장 및 로그

출력 파일:
- `[작업폴더]/[과제명약어]_WBS_TBS.pptx`
- `[작업폴더]/[과제명약어]_WBS.xlsx`
- `[작업폴더]/figures/gantt_chart.svg`
- `[작업폴더]/figures/wbs_tree.svg`
- `[작업폴더]/figures/tbs_tree.svg`

1. 사용자 검토 승인 (Rule 1)
2. `YYMMDD_HHMM_wbs_tbs.md` 분석 저장 (Rule 2)
3. `0.FilesUpdate.xlsx` 업데이트 (Rule 4)

---

## WBS/TBS 품질 기준

- WBS 100% 규칙: 부모 = 자식의 합 (범위 누락 없음)
- TRL 정확성: 1(기초 원리) ~ 9(실환경 검증) 기준 엄격 적용
- 간트차트: 모든 WBS L2 항목이 일정표에 표시
- 마일스톤: 계약/평가 일정과 연동 가능한 수준의 구체성
- 색상: defense-diagram 스킬의 디자인 시스템 준수
