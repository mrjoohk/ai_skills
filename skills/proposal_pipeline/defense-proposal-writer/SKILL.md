---
name: defense-proposal-writer
description: 연구 제안서의 개요·연구개발 방안·기술 분석·연구 계획·세부 계획을 출처와 사용자 양식에 맞춰 작성하거나 수정한다. 제안서 장·절 작성, 연구 목표·일정·예산·시험 계획 본문, 장별 슬라이드 요청에 사용한다. RFP 분석·KPI 조사·최종 문서 병합은 해당 전문 스킬과 연결한다.
---

# Defense Proposal Writer

제안서 섹션을 공통 절차로 작성한다. 기본 제공하는 방산 연구 제안서 목차는 재사용 프리셋이며, 사용자가 제공한 RFP·목차·서식·용도·출력 형식을 우선한다. 프로젝트명이나 특정 기관의 경로·승인 이력을 전제로 하지 않는다.

## 섹션 선택

요청한 섹션의 작성 기준과 템플릿만 읽는다. 여러 장 또는 전체 본문 요청이면 필요한 섹션을 순서대로 작성하고 같은 근거·수치를 재사용한다.

| section | 요청과 기본 항목 | 작성 기준 | 시작 템플릿 |
|---|---|---|---|
| `overview` | 과제 개요, 개념도, 목표·필요성, 범위, 추진계획, 기대효과 | [overview](references/sections/overview.md) | [overview](templates/overview.md) |
| `rd-plan` | 국내외 동향, 연구개발 목표·내용, 추진방안·체계, 혁신성·도전성 | [rd-plan](references/sections/rd-plan.md) | [rd-plan](templates/rd-plan.md) |
| `tech-analysis` | WBS/TBS 서술, 구성품 개발방법, 소요·기확보·미확보 기술 | [tech-analysis](references/sections/tech-analysis.md) | [tech-analysis](templates/tech-analysis.md) |
| `research-plan` | 기간·개략 예산, 일정 서술, 성과평가, 기술 접근, 조직·세부과제 | [research-plan](references/sections/research-plan.md) | [research-plan](templates/research-plan.md) |
| `detail-plan` | 상세 예산·배분, 자원, 성능시험, 안전관리, 성과물 | [detail-plan](references/sections/detail-plan.md) | [detail-plan](templates/detail-plan.md) |
| `custom` | 사용자가 제공한 별도 목차·RFP 항목 | 사용자 목차와 평가 기준 | [custom](templates/custom.md) |

예전 장별 스킬 호출과 1~5장 요청도 위 section으로 해석한다. 예를 들어 “연구 계획 작성”은 `section=research-plan`이다. 장 번호는 RFP가 다르면 RFP를 따른다.

## 공통 작성 흐름

1. **입출력 정하기.** 현재 요청에서 목적·section·출처·대상 파일·형식·서식을 확인한다. 입력 경로는 사용자가 지정한 파일을 우선하고, 미지정이면 현재 작업공간에서 관련 문서를 찾는다. 파일명을 고정 패턴과 맞추기 위해 바꾸지 않는다. 출력은 지정 위치에 쓰며, 위치가 없으면 작업공간의 설명적인 새 이름을 사용한다. 기존 파일 수정 요청이면 그 문서의 구조와 수작업 편집을 보존한다.
2. **근거 묶기.** RFP/요구사항, 제안 전략, KPI 근거, WBS·일정, 기존 장을 읽고 핵심 수치와 근거 위치를 기록한다. `defense-proposal-prep`와 `defense-kpi-benchmark` 산출물은 권장 입력이며, 사용자가 제공한 동등한 자료도 사용할 수 있다. 없는 자료를 만들어 읽었다고 하지 않는다. 자료가 부족해도 초안을 작성할 수 있으면 해당 항목을 `미확정 — 근거 필요`로 남긴다.
3. **정본 유지하기.** KPI·단위·측정 조건은 지정된 KPI 근거를 따른다. 범위·TRL은 RFP/전략 근거, WBS·일정은 사용자가 지정한 기준선, 상세 예산은 `detail-plan`을 정본으로 삼는다. 기준이 충돌하면 임의로 평균·수정하지 말고 근거와 충돌을 기록한다. `[SYNTHETIC-RFP]`는 원 RFP가 교체되기 전까지 관련 본문·메타데이터·최종본에 승계한다. 선행 자료 없이 쓴 초안에는 `PREREQ-SKIPPED`와 누락 자료를 명시한다.
4. **섹션 작성하기.** 해당 템플릿에 출처로 확인한 내용과 표·수치를 채운다. 기본 목차와 사용자 목차가 다르면 사용자 목차에 맞추고, 기존 섹션 기준의 필요한 내용을 그 항목에 대응시킨다. 템플릿의 대괄호·중괄호 자리표시를 실제 내용 또는 명시적인 미확정 표기로 바꾼다. 예시 예산·기간·기관·성능 수치를 사실로 채우지 않는다.
5. **요청한 형식으로 만들기.** Markdown만 요청하면 본문만 작성한다. PPTX·DOCX·HWPX가 요청되면 현재 환경에 설치된 해당 문서 도구/스킬을 사용한다. 텍스트·레이아웃·표·도식은 같은 콘텐츠를 사용하고 사용자 서식이 없을 때만 [presentation-theme.json](templates/presentation-theme.json)과 [diagram 디자인 프리셋](../defense-diagram/references/design-system.md)을 기본값으로 삼는다. 실제 생성 도구가 없으면 작성한 본문·명세와 생성하지 못한 형식을 구별한다.
6. **대조하고 저장하기.** 필수 항목 누락, 장 간 KPI·TRL·기간·예산·세부과제 명칭, 예산 합계·비율, 인력 투입률, 남은 자리표시·미확정 사항을 확인한다. PPTX/DOCX/HWPX는 사용한 도구의 구조 검사·렌더링·재열기 중 가능한 검사를 수행한다. 현재 요청이 허용한 작성·저장은 진행하며, 과거 프로젝트의 승인 절차를 새 조건으로 만들지 않는다. 로그는 대상 프로젝트에 이미 지정된 방식이 있거나 요청된 경우만 남긴다.
7. **보고하기.** 작성·수정한 파일, 적용 section/서식, 실제 검증 결과, 출처와 미확정 항목을 짧게 보고한다. 여러 장의 최종 패키징은 `defense-proposal-assembler`로 연결한다.

출처와 경로를 다음 작업에 넘길 때는 [proposal-metadata.template.json](templates/proposal-metadata.template.json)을 채워 함께 저장할 수 있다. 저장 자체는 필수 조건이 아니며, 이미 같은 정보를 가진 프로젝트 manifest가 있으면 재사용한다.

## 역할 경계

- RFP 요구사항·TRL 분석: `defense-proposal-prep`. 새로운 성능 근거 조사와 목표 제안: `defense-kpi-benchmark`.
- `tech-analysis`는 WBS/TBS 내용·표를 설명한다. 계층도·간트·xlsx 시각화는 `defense-wbs-tbs`, 도식은 `defense-diagram`을 사용한다.
- `research-plan`은 기간·일정 서술·평가 계획·개략 배분을 작성한다. 총괄·세부 예산 정본은 `detail-plan`이며, 성능시험 기준은 같은 KPI 근거를 따른다.
- `defense-proposal-assembler`는 병합 전 일관성 게이트다. 이 작성 스킬이 여러 장을 썼다는 이유로 불일치 검사를 생략하지 않는다.
- 구현 에이전트용 REQ/IF/UF 문서는 `repo-doc-writer`, 진행 이력·결정·회고는 `project-summarizer`의 별도 목적을 유지한다.
