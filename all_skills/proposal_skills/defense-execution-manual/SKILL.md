---
name: defense-execution-manual
description: >
  방산 연구 제안서 스킬 수트의 실행 매뉴얼을 자동 생성하는 스킬.
  연구 주제(과제명)를 입력하면, 9개 스킬(defense-proposal-prep, defense-kpi-benchmark,
  defense-proposal-overview/rd-plan/tech-analysis/research-plan/detail-plan,
  defense-diagram, defense-wbs-tbs)을 어떤 순서로, 어떤 입력값으로 실행해야 하는지
  단계별 실행 매뉴얼 Word 문서(.docx)를 생성한다.
  MANDATORY TRIGGERS: "실행 매뉴얼 만들어줘", "매뉴얼 작성", "스킬 사용 방법",
  "어떻게 쓰면 돼", "how to use skills", "execution manual", "스킬 실행 순서",
  "제안서 작성 가이드", "주제 넣고 매뉴얼". 연구 주제를 주고 제안서 작성 절차를
  안내받고 싶을 때 반드시 이 스킬을 사용할 것.
---

# Defense Execution Manual 스킬

연구 주제를 입력받아 **방산 제안서 스킬 수트 9개를 어떻게 실행할지** 알려주는
단계별 실행 매뉴얼 Word 문서(.docx)를 생성한다.

이 스킬은 매뉴얼 생성에 특화되어 있으며, 실제 제안서 콘텐츠를 작성하지는 않는다.
대신 각 스킬에 **무엇을 입력해야 하는지**, **어떤 결과가 나오는지**를 주제에 맞게 구체화한다.

> 📖 **참조 파일**:
> - `references/manual-template.md` — 매뉴얼 docx 구조 및 섹션별 작성 지침
> - `references/skill-io-map.md` — 9개 스킬의 입출력 스펙 정의

---

## 전체 워크플로우

```
[입력] 연구 주제 (과제명 + 분야 + 기간/예산 선택)
    ↓
Step 1. 주제 분석 — 기술 도메인, 군 운용 요구, 핵심 기술 키워드 추출
    ↓
Step 2. 유사 프로그램 파악 — 웹 검색으로 참조 사례 5~7개 수집
    ↓
Step 3. 스킬별 입출력 구체화 — 9개 스킬 × 이 주제에 맞는 입력값·샘플 콘텐츠
    ↓
Step 4. KPI 목표치 초안 — 유사 프로그램 기반 8~10개 KPI
    ↓
Step 5. Docx 생성 — references/manual-template.md 구조 사용
    ↓
[출력] YYMMDD_HHMM_execution_manual_[주제약어].docx
        YYMMDD_HHMM_execution_manual_[주제약어].md (요약본)
```

---

## Step 1. 주제 분석

사용자의 입력에서 아래 항목을 추출한다.
RFP 문서가 없는 경우 defense-rfp-generator 스킬로 먼저 RFP를 생성해도 좋으나,
간략한 과제명만으로도 이 스킬은 동작한다.

| 추출 항목 | 방법 | 예시 |
|-----------|------|------|
| 기술 도메인 | 핵심 기술 단어 분류 (AI, 무인기, 레이더, 추진 등) | AI·자율, 무인기 편대 |
| 군 운용 요구 | 작전 목적 파악 (공대공, ISR, 지뢰 탐지 등) | 공대지·공대공 자율 임무 |
| 개발 목표물 | 소프트웨어/하드웨어/시스템 분류 | 학습 환경(소프트웨어) |
| 연구 기간 | 없으면 3년 기본값 사용 | 3년 |
| TRL 범위 | 없으면 TRL 3→6 기본값 사용 | TRL 2→6 |

---

## Step 2. 유사 프로그램 파악

웹 검색으로 유사 국내외 프로그램 5~7개를 수집한다.
아래 검색 쿼리를 참고하되, 주제에 맞게 키워드를 조정한다.

```
"[핵심기술] DARPA program"
"[핵심기술] AFRL research"
"[핵심기술] defense RFP requirements"
"[핵심기술] NATO research program"
"[핵심기술] 방위사업청 과제" OR "[핵심기술] ADD 연구"
"[핵심기술] performance metrics military"
```

각 프로그램에서 수집할 정보:
- 프로그램명, 주관 기관, 기간
- 핵심 목표 및 달성 수치 (KPI 기준으로 활용)
- 학습 환경·알고리즘·시스템 구성 (있는 경우)
- 관련 문서 링크

---

## Step 3. 스킬별 입출력 구체화

references/skill-io-map.md를 읽고 9개 스킬 각각에 대해 아래를 작성한다.

각 스킬 카드에 포함할 내용:
1. **스텝 번호 & 스킬명**
2. **INPUT** — 이 주제에서 실제로 입력할 내용 (구체적인 예시값)
3. **OUTPUT** — 기대 산출물 목록
4. **호출 명령어** — 실제 사용할 한국어 명령 예시
5. **이 주제 전용 샘플 콘텐츠** — 혁신 서사 초안, WBS 계층, 기확보/미확보 기술 구분표 등

주제별로 달라지는 핵심 요소:
- STEP 1 (prep): 혁신성 4막 서사 초안 (이 주제에 맞게)
- STEP 2 (kpi-benchmark): 구성 기술 목록 × KPI 후보 표
- STEP 5 (tech-analysis): 기확보/미확보 기술 구분 예시
- STEP 6 (research-plan): 연도별 마일스톤 계획
- STEP 9 (wbs-tbs): WBS 1~2계층 구조

---

## Step 4. KPI 목표치 초안

Step 2에서 수집한 유사 프로그램 데이터를 기반으로
KPI 표를 작성한다.

표 구조:
| KPI 항목 | 단위 | 국내 SoA | 해외 SoA (상위 프로그램 수준) | 제안 목표치 |

KPI 목표치 설정 원칙:
- 해외 SoA가 있으면: 해외 수준 × 0.8 ~ 해외 수준을 기준으로 설정
- 해외 SoA가 없으면: 국내 SoA 대비 30~50% 향상 목표
- 8~12개 KPI가 적정 (너무 많으면 핵심 5개를 강조)

---

## Step 5. Docx 생성

references/manual-template.md를 읽어 문서 구조를 확인한 뒤,
docx 스킬(SKILL.md: /mnt/.skills/skills/docx/SKILL.md)의 docx-js 방식으로 생성한다.

### 색상 테마 (design-system.md와 동일)
- PRIMARY: `#1B3A6B` (네이비 블루) — 제목, 헤더
- SECONDARY: `#2E6DA4` (스틸 블루) — 소제목, 강조
- ACCENT: `#C8962E` (골드) — 스텝 번호, 중요 수치
- BACKGROUND: `#F4F7FC` — 표 배경
- SUCCESS: `#2E7D51` — 기확보 기술
- WARNING: `#B85C1A` — 미확보 기술

### 파일 저장
- 경로: `/mnt/proposal/YYMMDD_HHMM_execution_manual_[주제약어].docx`
- 요약 md: `/mnt/proposal/YYMMDD_HHMM_execution_manual_[주제약어].md`
- 0.FilesUpdate.xlsx에 두 파일 모두 로그 추가 (GLOBAL_RULES Rule 4)

### 생성 후 검증
```bash
python /mnt/.skills/skills/docx/scripts/office/validate.py [파일경로]
```
"All validations PASSED" 확인 후 사용자에게 링크 제공.

---

## 출력 품질 체크리스트

- [ ] 9개 스킬 전부 커버됨
- [ ] 각 스킬 INPUT이 이 주제에 맞게 구체화됨 (generic하지 않음)
- [ ] KPI 표에 해외 SoA 수치 포함
- [ ] 혁신성 4막 서사 초안 포함
- [ ] WBS 1~2계층 예시 포함
- [ ] 기확보/미확보 기술 구분 예시 포함
- [ ] docx 검증 통과
- [ ] 파일 로그 갱신
