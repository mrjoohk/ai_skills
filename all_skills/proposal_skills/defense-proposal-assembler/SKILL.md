---
name: defense-proposal-assembler
description: >
  방산 제안서 파이프라인의 마지막 단계. 장별 산출물(1~5장 pptx, figures, WBS/TBS)을
  최종 통합 제안서 1건으로 병합하고, 병합 전 장 간 수치 일관성(KPI·TRL·예산·일정)을
  교차 검사하여 불일치 리포트를 생성한다. MANDATORY TRIGGERS: "제안서 합쳐줘",
  "최종 제안서 만들어줘", "제안서 통합", "장별 슬라이드 병합", "제안서 마무리",
  "assemble proposal", "최종본 만들어줘", "제안서 패키징". 섹션 스킬들이 각 장을
  생성한 뒤 최종본이 언급되면 반드시 이 스킬을 사용할 것.
---

# Defense Proposal Assembler — 최종 병합 + 수치 일관성 게이트

섹션 스킬들은 장별 조각(pptx)만 생성하고 끝난다. 이 스킬이 조각을 **최종 제안서
1건**으로 만들고, 병합 과정에서 장 간 수치 충돌을 잡는다.

```
1~5장 pptx + figures/ + WBS_TBS  →  [수치 교차 검사]  →  통합 pptx (+ 요청 시 docx)
                                        ↓ 불일치 시
                                   consistency_report → 해당 섹션 스킬로 반송
```

---

## 입력 (모두 파일 기준)

| 파일 | 생산 스킬 | 필수 |
|---|---|---|
| `[과제명약어]_과제개요.pptx` | defense-proposal-overview | ✅ |
| `[과제명약어]_연구개발방안.pptx` | defense-proposal-rd-plan | ✅ |
| `[과제명약어]_기술현황분석.pptx` | defense-proposal-tech-analysis | ✅ |
| `[과제명약어]_연구계획.pptx` | defense-proposal-research-plan | ✅ |
| `[과제명약어]_세부연구계획.pptx` | defense-proposal-detail-plan | ✅ |
| `figures/`, `[과제명약어]_WBS_TBS.pptx`/`.xlsx` | defense-diagram / defense-wbs-tbs | 선택 |
| `*_kpi_benchmark_[과제명약어].md` | defense-kpi-benchmark | ✅ (일관성 기준값) |
| `*_proposal_prep_[과제명약어].md` | defense-proposal-prep | 선택 (TRL 기준값) |

누락 장이 있으면 병합을 중단하고 해당 섹션 스킬 실행을 안내한다.

---

## 실행 단계

### Step 1 — 수치 일관성 교차 검사 (병합 전 게이트)

pptx 텍스트를 추출(pptx 스킬 활용)하여 아래 항목을 장 간 대조한다:

| 검사 항목 | 기준(정본) | 대조 대상 |
|---|---|---|
| KPI 항목·목표치 | `*_kpi_benchmark_*.md` 산출표 | 1장 3항, 2장, 4장 성과평가, 5장 성능시험 |
| TRL 현재/목표 | `*_proposal_prep_*.md` | 1장, 3장 |
| 총연구기간·단계 구분 | 1장 추진계획 | 4장 일정, WBS 간트 |
| 총예산·연차 배분 | 5장 예산 총괄 (정본) | 1장 개요, 4장 개략 배분 |
| 세부과제 명칭·개수 | WBS | 4장 세부과제 계획, 5장 |
| `[SYNTHETIC-RFP]` 태그 | RFP/prep 헤더 | 태그 존재 시 최종본 표지에 승계 |

- 불일치 발견 → `[MISMATCH: <항목> — <장A>=<값> vs <장B>=<값>, 정본=<값>]`
- **게이트 규칙**: MISMATCH가 1건이라도 있으면 병합 중단이 기본. 리포트를 제시하고
  해당 섹션 스킬로 수정을 반송한다. 사용자가 "그대로 병합"을 명시하면 진행하되
  최종본 부록에 미해결 불일치 목록을 포함한다.

### Step 2 — 병합

- 슬라이드 순서: 표지 → 목차 → 1장 → 2장 → 3장 → 4장 → 5장 → 부록(WBS/TBS xlsx 요약, figures 인덱스)
- 표지: 과제명, 기관, 날짜, (해당 시) `[SYNTHETIC-RFP]` 태그
- 서식 통일: 폰트·색상은 1장 기준으로 정규화, 슬라이드 번호 재부여
- pptx 병합은 **pptx 스킬**의 방법을 따른다 (직접 XML 조작 금지)

### Step 3 — 산출

| 파일 | 위치 |
|---|---|
| `[과제명약어]_제안서_최종_vN.pptx` | output_docs/ (Rule 7) |
| `YYMMDD_HHMM_consistency_report_[과제명약어].md` | review_docs/ (Rule 6) |
| (요청 시) `[과제명약어]_제안서_최종_vN.docx` | output_docs/ |

GLOBAL_RULES Rule 1(승인 후 출력)·Rule 4(파일 로그) 준수: Step 1 리포트를 먼저
제시하고 승인 후 최종본을 생성한다.

---

## 작업 규칙

- 수치는 절대 이 스킬에서 수정하지 않는다 — 불일치는 원 섹션 스킬로 반송 (수정 주체 유지).
- 버전 관리: 재병합 시 `vN` 증가, 이전 버전 삭제 금지.
- 다과제 안전: 모든 입출력 파일명에 `[과제명약어]` 필수 — 약어 불일치 파일은 병합 대상에서 제외하고 경고.
