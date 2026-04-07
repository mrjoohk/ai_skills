# Proposal Skills — 스킬 연동 사용 매뉴얼

> **디렉토리 목적:** 방산 연구 제안서 작성 전 주기 지원. RFP 확보부터 각 섹션 작성, 시각 자료 제작,
> KPI 설정까지 일관된 품질의 제안서를 체계적으로 완성하는 스킬 묶음.

---

## 포함 스킬 목록

| 스킬 | 역할 | 주요 출력 |
|------|------|-----------|
| `defense-rfp-generator` | RFP 없을 때 합성 RFP 자동 생성 | synthetic_RFP.docx + .md |
| `defense-proposal-prep` | RFP 분석 → 제안 전략 문서 | 제안 전략 문서 (전 섹션 소스 자료) |
| `defense-kpi-benchmark` | 구성 기술별 KPI·목표치 도출 | KPI 벤치마크 문서 |
| `defense-proposal-overview` | 과제 개요 섹션 (1장) 작성 + PPTX | 1장 슬라이드 |
| `defense-proposal-rd-plan` | 연구개발 방안 섹션 (2장) 작성 + PPTX | 2장 슬라이드 |
| `defense-proposal-tech-analysis` | 기술 현황 분석 섹션 (3장) 작성 + PPTX | 3장 슬라이드 |
| `defense-proposal-research-plan` | 연구 계획 섹션 (4장) 작성 + PPTX | 4장 슬라이드 |
| `defense-proposal-detail-plan` | 세부 연구 계획 섹션 (5장) 작성 + PPTX | 5장 슬라이드 |
| `defense-diagram` | 개념도·블록다이어그램·구성도 생성 | SVG / HTML 다이어그램 |
| `defense-wbs-tbs` | WBS·TBS·간트차트·마일스톤 생성 | xlsx + SVG + PPTX |
| `defense-execution-manual` | 스킬 실행 순서 매뉴얼 자동 생성 | 맞춤형 실행 매뉴얼 Word 문서 |
| `project-summarizer` | 제안서 작성 과정 요약 문서 생성/갱신 | project_summary.md |

---

## 전체 파이프라인 흐름

### 경로 A — RFP가 없는 경우 (과제명만 있는 경우)

```
[연구 주제 / 과제명]
        ↓
① defense-rfp-generator ────────────────────────────────
   유사 국내외 프로그램 5~7개 조사
   → synthetic_RFP.docx + .md
        ↓
② defense-proposal-prep (합성 RFP를 입력으로 사용) ─────
   RFP 분석 + 요구사항 도출 + 갭 분석 + 전략 문서
        ↓
   (이후 경로 B와 동일)
```

### 경로 B — RFP가 있는 경우

```
[RFP 문서]
        ↓
② defense-proposal-prep ────────────────────────────────
   RFP 분석 → 제안 전략 문서 (이후 모든 섹션의 소스)
        ↓
③ defense-kpi-benchmark ────────────────────────────────
   구성 기술별 SoA 조사 → KPI 목표치 도출
        ↓
④ 섹션별 작성 (병렬 진행 가능) ────────────────────────
   ┌─ defense-proposal-overview   (1장: 과제 개요)
   ├─ defense-proposal-rd-plan    (2장: 연구개발 방안)
   ├─ defense-proposal-tech-analysis (3장: 기술 현황 분석)
   ├─ defense-proposal-research-plan (4장: 연구 계획)
   └─ defense-proposal-detail-plan   (5장: 세부 연구 계획)
        ↓
⑤ 시각 자료 제작 (섹션 작성과 병렬 진행 가능) ─────────
   ┌─ defense-diagram    (개념도 / 블록다이어그램 / 구성도)
   └─ defense-wbs-tbs   (WBS / TBS / 간트차트 / 마일스톤)
        ↓
⑥ project-summarizer ──────────────────────────────────
   제안서 작성 전 과정 회고 + 인수인계 문서 생성
```

---

## 단계별 사용 방법

### ① defense-rfp-generator — 합성 RFP 생성

**언제:** RFP(공모 문서)가 없고 과제명만 있을 때. `defense-proposal-prep` **이전**에 실행.

**트리거 예시:**
- "RFP 만들어줘", "공모 문서 없어, 만들어줘"
- "유사 프로그램 찾아줘", "모의 RFP 생성해줘"
- "주제만 있는데 어떻게 시작해?"

**입력 → 출력:**
```
과제명 (+ 선택: 분야, 기간, 예산)
  → 유사 프로그램 5~7개 웹 조사
  → synthetic_RFP_[주제약어].docx (방위사업청 형식 7섹션)
  → synthetic_RFP_[주제약어].md (분석 요약)
```

**주의:** 생성된 RFP는 유사 프로그램 합성 문서다. 실제 공모 기준이 공개되면 그 문서로 교체한다.

---

### ② defense-proposal-prep — RFP 분석 & 제안 전략 수립

**언제:** RFP(실제 또는 합성) 확보 후 제안서 작성 전 반드시 실행.
         이 스킬의 출력이 이후 모든 섹션 스킬의 소스 자료가 된다.

**트리거 예시:**
- "RFP 분석해줘", "제안 전략 잡아줘"
- "요구사항 뽑아줘", "벤치마킹 조사해줘"

**입력 → 출력:**
```
RFP 문서
  → 요구사항 분석
  → 기능·TRL 갭 분석
  → 최신 기술 벤치마킹
  → 혁신성·도전성 포지셔닝
  → 제안 전략 문서 (전 섹션 작성의 근거 자료)
```

---

### ③ defense-kpi-benchmark — KPI & 성능 목표치 도출

**언제:** 제안 전략 문서 완성 후, 섹션 작성 전. 성능 수치 근거가 필요할 때.

**트리거 예시:**
- "KPI 도출해줘", "성능 목표 설정해줘"
- "국내외 성능 비교해줘", "SoA 조사해줘"

**입력 → 출력:**
```
제안 전략 문서 + 구성 기술 목록
  → 국내외 연구동향 조사
  → 기술별 KPI + 정량적 목표치 (근거 포함)
  → KPI 벤치마크 문서
```

---

### ④ 섹션별 작성 스킬

각 섹션 스킬은 `defense-proposal-prep`의 제안 전략 문서와 `defense-kpi-benchmark` 결과를
소스로 사용한다. 섹션 간 순서 의존성은 낮으므로 병렬 진행이 가능하다.

#### 1장 — defense-proposal-overview (과제 개요)

**트리거:** "과제 개요 작성", "1장 써줘", "연구 목표 써줘"

**포함 항목:** 연구개발 목표 / 필요성 / 추진계획 / 기대성과 등 6개 항목 + PPTX 슬라이드

---

#### 2장 — defense-proposal-rd-plan (연구개발 방안)

**트리거:** "연구개발 방안 작성", "2장 써줘", "국내외 동향 써줘"

**포함 항목:** 국내외 동향 / 연구개발 목표 상세 / 추진체계 / 혁신성·도전성 등 4개 항목 + PPTX

---

#### 3장 — defense-proposal-tech-analysis (기술 현황 분석)

**트리거:** "기술 현황 분석", "3장 써줘", "WBS 작성", "소요기술 써줘"

**포함 항목:** WBS / 구성품 개발방법 / TBS / 소요기술 분석 / 기확보·미확보 기술 등 7개 항목 + PPTX

---

#### 4장 — defense-proposal-research-plan (연구 계획)

**트리거:** "연구 계획 작성", "4장 써줘", "추진 일정 계획"

**포함 항목:** 연구기간·예산 / 추진 일정 / 성과평가 / 기술적 접근방법 / 세부과제 계획 등 6개 항목 + PPTX

---

#### 5장 — defense-proposal-detail-plan (세부 연구 계획)

**트리거:** "세부 연구 계획", "5장 써줘", "소요예산 작성"

**포함 항목:** 소요예산 / 세부예산 총괄 / 소요자원 / 성능시험 계획 / 안전관리 / 연구성과물 등 6개 항목 + PPTX

---

### ⑤ 시각 자료 제작

#### defense-diagram — 개념도·다이어그램

**트리거:** "개념도 그려줘", "블록다이어그램 만들어줘", "시스템 구성도"

```
텍스트 설명 or 기존 섹션 내용
  → SVG / HTML 다이어그램 (제안서 디자인 시스템 준수)
```

**주의:** 한 제안서 내 모든 다이어그램은 동일한 디자인 시스템(색상·폰트·스타일)을 따른다.
섹션 작성 중 "그림 필요" 표시가 있을 때마다 이 스킬을 호출한다.

---

#### defense-wbs-tbs — WBS·TBS·간트차트

**트리거:** "WBS 만들어줘", "간트차트 그려줘", "추진 일정 표 만들어줘"

```
연구 기간 + 세부과제 목록
  → xlsx (데이터)
  → SVG (계층 다이어그램)
  → PPTX (슬라이드)
```

**주의:** 3장(`defense-proposal-tech-analysis`)과 4장(`defense-proposal-research-plan`)
작성 시 함께 실행하는 것을 권장한다.

---

### ⑥ project-summarizer — 제안서 작성 과정 정리

**언제:** 제안서 전체 완성 후, 또는 작성 중간 점검 시.

**트리거 예시:**
- "제안서 작성 과정 정리해줘", "지금까지 한 일 요약해줘"
- "제안서 회고 문서 만들어줘", "인수인계용 정리해줘"

**입력 → 출력:**
```
대화 히스토리 + 작성된 섹션들
  → project_summary.md (작성 배경 / 전략 결정 / 섹션별 핵심 내용 / 이슈 & 해결 / 개선점)
```

---

## 맞춤형 실행 매뉴얼 자동 생성 — defense-execution-manual

과제명을 입력하면 9개 스킬을 어떤 순서로 어떤 입력값으로 실행해야 하는지
**맞춤형 Word 실행 매뉴얼**을 자동 생성한다.

**트리거 예시:**
- "실행 매뉴얼 만들어줘", "스킬 실행 순서 알려줘"
- "[과제명] 제안서 어떻게 시작해?"

이 매뉴얼은 위 단계별 가이드를 과제 특성에 맞게 구체화한 문서다.

---

## 스킬 선택 빠른 가이드

| 상황 | 사용할 스킬 |
|------|-------------|
| RFP가 없고 과제명만 있다 | `defense-rfp-generator` → `defense-proposal-prep` |
| RFP가 있고 제안서 작성을 시작한다 | `defense-proposal-prep` |
| 성능 목표 수치가 필요하다 | `defense-kpi-benchmark` |
| 특정 섹션을 작성하고 싶다 | 해당 섹션 스킬 직접 호출 |
| 그림·다이어그램이 필요하다 | `defense-diagram` |
| WBS/간트차트가 필요하다 | `defense-wbs-tbs` |
| 전체 진행 순서가 헷갈린다 | `defense-execution-manual` |
| 작성 과정을 기록·정리하고 싶다 | `project-summarizer` |
