# 문서 작성 스킬 통합·범용화 (2026-10-25)

활성 스킬 43개를 36개로 통합했으며 파이프라인 8개 분류를 유지했다. 프로젝트의 사실·경로·과거 승인 이력과 재사용 서식을 분리했다. 원본 drmHWP·surak 프로젝트의 비교 대상 459개 파일은 변경되지 않았다.

## 통합 결과

| 이전 | 현재 | 처리 |
|---|---|---|
| doc-writer + office-com-reader + office-com-writer + hwpx-drm | [doc-writer](../skills/office_document_pipeline/doc-writer/SKILL.md) | 판독·Office 편집·한글 작성의 공통 진입점. 앱별 구현은 backends/에 유지 |
| 제안서 overview·rd-plan·tech-analysis·research-plan·detail-plan | [defense-proposal-writer](../skills/proposal_pipeline/defense-proposal-writer/SKILL.md) | 공통 작성 흐름과 section 선택으로 통합. 장별 내용·슬라이드·품질 기준은 보존 |
| repo-doc-writer | [별도 유지](../skills/coding_agent_pipeline/repo-doc-writer/SKILL.md) | 구현 에이전트용 구조·계약 문서. architecture 템플릿과 UF 대응 검사 보강 |
| project-summarizer | [별도 유지](../skills/general/project-summarizer/SKILL.md) | 진행·결정·검증·회고 기록. Key Decisions 템플릿 보강 |

office-drm-bridge, RFP·KPI 조사, 도식, WBS/TBS 및 제안서 조립은 별도 기능이므로 유지했다.

## 프로젝트 의존 제거

- 고정 프로젝트 경로, 원본 전용 시험, 이전 프로젝트의 승인·실측 기록은 활성 작성 지침에서 제외했다. 보존 자료는 [통합 전 아카이브](../archive/document-skills-2026-10-25/README.md)에 있다.
- 입력·출력·문서명·기관·사람·버전은 현재 요청과 내용 명세에서 지정한다. 특정 이름의 GLOBAL_RULES 또는 /mnt 경로를 요구하지 않는다.
- 제목·본문·표 스타일은 프로파일에서 읽으며 생성·삽입·제목 검증·미작성 위치 보고에 함께 적용한다. 사용자 스타일을 사용한 별도 회귀 시험을 추가했다.
- 일반 문서도 처리하도록 preserve와 required 보호 정책을 분리했다. 보호 원본 또는 보호된 삽입 출처는 보호 출력을 요구한다. 저장 실패·내용 불일치·잘못된 컨테이너는 성공으로 취급하지 않는다.

## 번들 템플릿

- [한글 technical-report](../skills/office_document_pipeline/doc-writer/templates/technical-report/): 자체 작성한 A4 HWPX 논리 패키지(.package.zip), XML 원본, 스타일 프로파일, 합성 표 서식, 생성기·검사기와 시험 모형. 지원 필드는 패키지에서 모형으로 결정적으로 변환·대조하며 해시가 같아도 의미가 달라지면 거부한다.
- [제안서 템플릿](../skills/proposal_pipeline/defense-proposal-writer/templates/): 기본 장별 목차 5종, 사용자 목차, 메타데이터, 선택형 발표 테마.
- [저장소 문서 템플릿](../skills/coding_agent_pipeline/repo-doc-writer/assets/)과 [요약 템플릿](../skills/general/project-summarizer/references/template.md).

이 환경은 .hwpx 확장자에 문서 보호를 자동 적용하므로 재사용 정본은 자체 XML과 .package.zip으로 배포한다. 한글 백엔드는 이 ZIP을 HWPX 형식으로 연다. 이는 실제 앱 열림·조판 성공을 뜻하지 않는다.

## 설치와 이전

scripts/install_skills.py의 office-documents 설치는 스킬 2개와 tools/doc-writer, tools/hwpx-drm, document_templates를 배치한다. --without-project-tools는 프로젝트 실행 도구·서식 배포를 생략하고 스킬 내 리소스는 유지한다.

이전 분리 스킬이 설치된 프로젝트에서는 --migrate-legacy로 알려진 원본과 같은 SKILL.md만 .claude/retired-skills에 보관한다. 사용자 수정이 있는 진입점은 자동 변경하지 않는다. 설치 전 전체 충돌을 검사하며 추가 프로젝트 파일을 삭제하지 않는다. 브리지 지문은 실제 설치한 도구 기준으로 다시 작성해야 한다.

## 검증 범위

새 설치본에서 작성기 215개, 한글·Office 정책 140개, 브리지 137개, 설치기 9개를 합한 501개 시험을 실행했다(498개 성공, 3개 제외). 제외 3개는 선택형 실측 드라이버 부재 2개와 Windows 심볼릭 링크 권한 1개다. 저장소 문서 검사기는 독립 단위·CLI 12개를 통과했다. ZIP/XML 구조와 음성 대조 3개, 템플릿·모형 의미 대조 및 변형 거부도 확인했다. 최종 자동 검증 결과와 독립 검토는 아래 보고서에 기록한다. 문서 템플릿은 구조 검증과 가짜 COM 시험 대상이며 실제 한글 앱은 실행 오류로 열림·렌더링·조판을 검증하지 못했다.

- [내용·템플릿 검토](../reports/review/document_consolidation_final_review.md)
- [설치·문서 패키지 검토](../reports/review/document_consolidation_package_review.md)

기존 엔지니어링 스킬 17개에는 Claude용 user-invocable 메타데이터가 남아 있어 Codex 전용 quick_validate는 그 필드를 지원하지 않는다. 이번에 수정한 문서 스킬과 별개인 기존 호환 속성으로, 통합 과정에서 삭제하지 않았다. 등록된 정본 경로 검사는 전체 36개를 대상으로 한다.
