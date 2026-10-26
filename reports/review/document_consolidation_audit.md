# 문서 작성 스킬 병합·범용화 독립 검토

- 검토일: 2026-10-25
- 범위: `office_document_pipeline` 5개, `repo-doc-writer`, `project-summarizer`, `proposal_pipeline` 12개 스킬과 해당 실행 코드·참조 문서·설치 정의
- 방법: 소스 읽기와 역할·입출력·경로 계약 비교. 원본 스킬을 수정하지 않았으며 Office/HWP COM, 실제 문서 판독·작성, 테스트를 실행하지 않았다.
- 판정: **조건부 병합 가능**. 공통 작성 절차와 템플릿은 통합할 수 있다. 도메인 계약과 실행 백엔드까지 단일 작성기로 합치면 안 된다.

## 1. 병합 경계

| 대상 | 실제 책임과 계약 | 합칠 수 있는 부분 | 유지할 경계 |
|---|---|---|---|
| office-com-reader | MS Office의 값·텍스트·구조 판독, 포맷 판정, 선택적 평문 덤프 | writer와 세션 안내·COM 오류 처리·보호 판정 등의 공용 모듈 | 읽기 CLI와 쓰기 CLI의 부작용·종료코드 계약 |
| office-com-writer | Office protect/replace/fill, 저장 후 보호 서명 확인 | reader와 공용 유틸리티 및 상위 Office 라우터 | 콘텐츠 설계와 분리. 신규 내용은 python-docx/openpyxl/python-pptx 등이 생성하고 이 백엔드는 저장·보호를 담당 |
| hwpx-drm | HWP COM 판독·필드 채우기·치환·그림 추출 | Office와 환경 탐지·보호 결과 보고 형식 | HWPML 모델·누름틀·HWP 세션·종료코드는 MS Office와 별도 |
| doc-writer | Markdown 명세 → HWP 본문 조판, 기존 문서 끼워 넣기, 보호 그림 꾸러미 | hwpx-drm의 세션·파서·API 재사용, 공통 작성 명세·프로필 관리 | 내용 명세 조판과 필드 치환은 다른 작업. 전체 생성과 끼워 넣기에는 보존 검사도 다름 |
| office-drm-bridge | Linux 요청을 Windows 실행기로 전달, 경로·지문·선행 검색·격리·감사 검증 | 모든 Office/HWP 실행의 호출 인터페이스 | 문서 작성기와 합치지 않음. 정책·배포·수명 관리 계층이며 콘텐츠를 설계하지 않음 |
| repo-doc-writer | REQ/IF/UF → `docs/ai`의 구현 문맥·계약·검증 기준 | 출처 탐색·누락 표시·Markdown 템플릿 관리 | UF별 구현 계약은 회고 요약이나 HWP 조판 명세와 다름 |
| project-summarizer | 진행 사실·결정 이유·문제·교훈 → 기존 요약에 증분 병합 | 출처 탐색·사실성·누락 표시·템플릿 관리 | 기존 이력 보존과 회고 목적. 태스크 생성이나 기술문서 조판과 합치지 않음 |
| 제안서 5개 섹션 스킬 | 동일한 prep/KPI 정본을 읽고 장별 콘텐츠와 PPTX/MD 생성 | **공통 section writer + 5개 섹션 템플릿/프로필**의 최우선 후보 | 장별 목차·필수 항목·정본 소유권·검증 기준은 프로필로 보존 |
| proposal-prep / kpi-benchmark | 조사·요구사항·TRL·KPI 근거 생성 | 출처 카드·문서 포장·스타일 | 섹션 작성 전에 근거를 만드는 작업이므로 문장 작성기로 흡수하지 않음 |
| rfp-generator | 외부 조사 → 합성 RFP, 합성 태그·검증되지 않은 수치 표시 | 문서 출력·시각 스타일·공통 출처 관리 | 실제 RFP와 구별하는 태그·가정 계약 보존 |
| diagram / wbs-tbs | 도식과 WBS/TBS·일정 시각화·xlsx | 디자인 토큰·출력 포장 | 기술 분석의 표 서술, 연구 계획의 일정 서술과 역할 구분 유지 |
| execution-manual | 스킬 실행 순서와 입출력·점검 카드 → 매뉴얼 | Docx 템플릿·스타일·런타임 탐색 | 실제 제안서 본문이 아니라 작업 가이드. 입출력 지도는 파이프라인 변경과 함께 갱신 |
| proposal-assembler | 장 병합 전 수치 일관성 검사, 통합본 생성 | 출력 경로·디자인 정규화·패키징 | 정본 수치를 직접 수정하지 않는 독립 게이트 유지 |

근거:

- `office-com-writer/SKILL.md:65-74`는 protect/replace/fill과 신규 콘텐츠 생성을 구분한다. 실제 CLI도 `scripts/write_office_doc.py:442`와 reader의 `scripts/read_office_doc.py:482`로 독립되어 있다.
- HWP 세션은 `hwpx-drm/scripts/hwp_session.py:22,97,137,155`에서 등록 모듈·HWP 프로세스·COM 세션을 관리한다. MS Office와 같은 저장 엔진이 아니다.
- bridge는 `office-drm-bridge/scripts/bridge_worker.py:24-28`에서 형제 스킬별 스크립트를 선택하며 `bridge_core.py:21,39-48,227,237-294`에서 경로·검색 결과 해시·지문을 검사한다.
- `repo-doc-writer/SKILL.md:41-47,77-85`는 UF별 계약과 검증 기준을 출력한다. `project-summarizer/SKILL.md:36-45`는 기존 요약에 추가/변경분만 병합한다.
- 제안서 5개 섹션 스킬의 `SKILL.md:12`는 같은 Gate G6를 반복한다. 기술 분석 `:23`, 연구 계획 `:23`, 세부 연구 계획 `:23`에는 서로 다른 정본 소유권이 이미 선언되어 있다.
- `defense-proposal-assembler/SKILL.md:44-60,84`는 정본 기준 대조와 불일치 반송을 수행하고 수치를 직접 고치지 않는다.

## 2. 의존성 분류

### A. 프로젝트 전용 경로·운영 규칙 — 설정 또는 예시로 이동

| 발견 | 분류와 조치 | 근거 |
|---|---|---|
| `K:\01.workspace\AI_workspace\hmumt_scheduler` ↔ `$HOME/mnt/hmumt_scheduler` | 특정 프로젝트 마운트. `<project_root>`/연결 폴더 탐색으로 대체 | `office-com-reader/SKILL.md:58` |
| `tools/office-com-reader`가 정본이라는 안내 | 현재 정본은 `skills/<category>/<name>`이며 설치본은 `.claude/skills/<name>`이다. 소스/설치/호환 런타임 경로를 구별 | reader `SKILL.md:12-15`, writer `SKILL.md:12-15`, `skills/pipelines.json:3`, `scripts/install_skills.py:44` |
| PowerShell 판을 삭제했다고 설명하지만 PS 파일은 포함 | 특정 프로젝트의 이력과 배포본 상태가 어긋남. 현재 지원 CLI와 호환 파일 역할을 다시 명시 | reader/writer `SKILL.md:13-14`; 양쪽 `scripts/Read-OfficeDoc.ps1`, `Write-OfficeDoc.ps1` 존재 |
| `output_docs`, `review_docs`, `rd`, `logs/files.jsonl` 및 GLOBAL_RULES Rule 번호 | 이 라이브러리의 작업 관례. 정본 계약으로 의도한 경우 기본값을 유지하되 규칙 파일 부재 시 동작·프로젝트 override를 명시 | `bridge_core.py:21,145`; repo writer `SKILL.md:55-57`; proposal overview `SKILL.md:122-125` |
| `/mnt/proposal`, `/mnt/.skills/skills/docx/...` | 특정 클라우드 실행 환경. 작업 루트와 설치된 문서 스킬을 탐색해 사용 | rfp generator `SKILL.md:189-195`; execution manual `SKILL.md:126,137-143` |
| `tools/doc-writer`와 `tools/hwpx-drm` 상대 경로 | 우연한 프로젝트 경로가 아니라 **실행·배포 계약**. 경로명을 지우면 import와 bridge가 깨짐. 설치 정의 또는 명시적 runtime root 옵션과 함께 변경 | `write_doc.py:74-80`; `bridge_core.py:39-48`; `skills/pipelines.json:178-205` |

### B. 과거 승인·실측 — 현재 권한 또는 현재 검증으로 승격하지 않음

- drmHWP D-062 그림 추출 승인과 surak D-028 제한은 프로젝트별 기록이다. `doc-writer/references/project-variants.md:12-13`는 이를 명시적으로 구별한다.
- 현재 배포본은 이 구별을 부분적으로 적용했다. `doc-writer/SKILL.md:23`, `hwpx-drm/SKILL.md:18`, `office-drm-bridge/SKILL.md:9`는 과거 승인을 재사용하지 말라고 한다.
- 그러나 bridge의 연산 표와 세션 안내에는 여전히 `drmHWP 결정 D-062(보안담당자 허락)` 및 `사용자가 ... 허용함`이 현재 운영 설명에 섞여 있다(`office-drm-bridge/SKILL.md:82,95`; `references/session_environment.md:44`). 원본 프로젝트 이력 파일로 이동하고, 운영 본문은 현재 사용자 요청·현재 프로젝트 설정을 참조하는 편이 일관된다.
- D-/P-/F- 번호를 코드 주석에서 일괄 삭제할 필요는 없다. 버그 수정·실측의 출처는 추적 자료로 가치가 있다. 다만 운영 전제와 검증 이력은 분리해야 한다.
- `insert_pin.json`을 다른 프로젝트에서 복사하지 않고 대상 코드를 확인한 뒤 새 지문을 기록하는 계약은 유지한다(`office-drm-bridge/references/deployment.md:22-25,45`). 템플릿을 번들해도 지문 확인을 자동 승인할 이유는 없다.

### C. 템플릿·스타일 의존 — 없애지 말고 재사용 자원으로 묶음

| 의존성 | 현재 상태 | 적절한 범용화 |
|---|---|---|
| COMSAF 제목/본문/캡션/표 스타일 | 기본 스타일은 코드에 있고 `styles` 명세 override는 지원 | `profile.json`으로 기본 스타일·첫 본문 제목·키·표/그림 규칙을 함께 관리. 기본 프로필 이름을 명시 |
| SUM 표 서식·표지 키·이력서 문구 | `new_doc_spec.md` 및 drmHWP profile에 존재하나 실제 HWPX와 table_style.json은 없음 | 프로젝트 업무 문서는 가져오지 않고 합성 재사용 템플릿·표 서식·샘플 명세를 skill 안에 제공하거나 외부 프로필로 명확히 한정 |
| 가짜 작성 모델 | COMSAF 합성 모델과 특정 템플릿 경로를 같은 것으로 간주 | 프로필 ID/구조 계약으로 검증. 다른 템플릿에서 `template_modeled=false`가 나는 현재 한계는 사실대로 보존 |
| 제안서 섹션 목차와 장별 표·슬라이드 순서 | 5개 SKILL 본문에 각각 들어 있음 | 공통 작성 절차 아래 5개 `templates/sections/*.md`로 이동. ID/정본 소유권/태그/필수 표를 함께 유지 |
| 제안서 네이비 색상·폰트·SVG defs | diagram의 `references/design-system.md`가 재사용 기준 | 디자인 토큰을 단일 자원으로 참조. 모든 글 작성 스킬에 색상을 복제하지 않음 |
| RFP·실행 매뉴얼 구조 | 이미 각 skill `references/*-template.md`에 있음 | 좋은 번들 패턴을 유지. 환경 경로만 제거하고 도메인 템플릿을 보존 |
| repo-doc·summary Markdown 템플릿 | 이미 assets/references에 있음 | 도메인 계약은 남기고 경로 탐색·출력 선택만 공통화. 템플릿과 본문 요구사항 동기화 필요 |

핵심 근거: `doc-writer/runtime/write_doc.py:85-87,166-173`(기본 스타일·override), `runtime/samples/new_doc_spec.md:3-17`(SUM 서식과 프로젝트 근거), `runtime/samples/minimal_spec.md:3-5`(외부 실제 템플릿 필요), `runtime/fake_write.py:80,183`(경로 고정 모델), `defense-diagram/references/design-system.md:8-38,132-156`(토큰·SVG), `repo-doc-writer/SKILL.md:22-35`(기존 번들 자원).

## 3. 주요 발견

### DC-01 · P1 · HWP 작성기의 일반 안내와 실제 스타일 의존 범위가 다름

`write_doc.py`는 `styles` override를 받지만, `insert_doc.py:50`은 제목을 `^COMSAF 개요 (\d)$`로 식별하고 `:373`은 `wd.STYLES`를 그대로 복사한다. 제목 수준 검사도 이 정규식에 의존한다(`:163,189,234`). `figure_pack.py:28`은 insert 모듈을 사용하므로 같은 경계의 영향을 받는다. `write_doc.py:1735`의 보고서 절 탐색 역시 `startswith("COMSAF")`에 고정된다.

**권고:** 문서만 일반화하지 말고 COMSAF profile을 명시하거나, 동일 프로필 객체를 write/insert/figpack/검증/보고 전체에 전달한다. 임의 스타일 이름에서 생성만 성공하고 보존 검사가 다른 제목 집합을 보게 되는 상황을 피해야 한다.

### DC-02 · P1 · 재사용 가능한 실제 문서 템플릿은 아직 번들되어 있지 않음

현재 `minimal_spec.md`조차 `output_docs/templates/00_공통_기술문서_템플릿.hwpx`를 전제한다. `new_doc_spec.md`는 외부 SUM 표 서식과 문서 작성 지침 경로까지 요구한다. 파일 목록상 doc-writer의 바이너리 자산은 자리표시 그림이며 실제 `.hwpx` 템플릿은 없다. `fake_write.py`의 COMSAF 합성 모델은 실제 Office/HWP 문서 템플릿이 아니다.

**권고:** 사용자 요청의 “템플릿 종속이면 스킬 안에 재사용 템플릿”을 완료하려면 (a) 업무 데이터가 없는 합성 실제 HWPX + 표 서식 + 대응 명세를 만들고 새 프로필로 검증하거나, (b) 실제 HWPX를 현재 환경에서 만들 수 없다면 완전한 템플릿 생성기/프로필 계약과 검증 한계를 함께 제공해야 한다. 스타일 JSON만 추가하고 실제 문서 생성까지 범용화됐다고 보고하면 안 된다.

### DC-03 · P2 · 과거 프로젝트 운영 상태가 현재 안내에 남음

reader의 특정 hmumt_scheduler 마운트, reader/writer의 오래된 정본·삭제된 PS 판 설명, bridge의 D-062 허락과 평문 허용 문장이 현재 안내와 혼재한다. 반면 일부 상위 스킬은 이미 “과거 승인은 현재 승인이 아니다”라는 경계를 도입했다.

**권고:** `references/history/drmHWP.md` 같은 출처 기록과 현재 배포 안내를 분리한다. 현재 사용자 요청이 이미 허용한 작업은 재승인을 요구하지 않고, 실제로 새 권한이 필요한 경우만 질문한다. 보안·보존 검증 계약은 삭제하지 않는다.

### DC-04 · P2 · 제안서 5개 섹션은 공통 절차 병합 효과가 큼

모든 섹션이 Gate G6·prep/KPI 파일 소비·SYNTHETIC-RFP 승계·PREREQ-SKIPPED·PPTX/MD·저장/로그를 반복한다. 개요 `:12-21,96-125`, 연구개발 방안 `:12-22,121-145`, 기술 분석 `:12-22,165-191`, 연구 계획 `:12-22,150-170`, 세부 계획 `:12-22,183-203`에서 확인된다.

**권고:** 공통 작성기 하나와 5개 섹션 템플릿을 두되 기존 이름은 라우팅 별칭으로 보존하면 설치·호출·실행 매뉴얼의 참조를 안정적으로 이전할 수 있다. 기술 분석의 WBS 표 서술, wbs-tbs의 시각화, 4장의 개략 예산, 5장의 예산 정본, assembler의 일관성 게이트는 유지한다. 기술 주제·기관·예산의 예시는 자리표시로 취급한다.

### DC-05 · P2 · 외부 GLOBAL_RULES·Docx 경로가 이식성을 막음

RFP/실행 매뉴얼은 `/mnt`와 특정 docx 스킬 설치 경로를 직접 호출한다. 여러 제안서 스킬은 Rule 1/2/4의 존재를 전제한다. repo-doc도 Rule 9를 canonical 위치 근거로 사용한다.

**권고:** 실행 환경·프로젝트 정책과 콘텐츠 템플릿을 분리한다. 사용 가능한 문서 스킬/도구를 탐색하고 프로젝트 경로·규칙이 있으면 읽는다. 규칙이 없을 때는 공통 기본 저장·로그 동작을 명시한다. 프로젝트별 승인 관례를 모든 새 프로젝트에 자동 강제하지 않는다.

### DC-06 · P2 · 기존 Markdown 템플릿·검증도 계약 동기화가 필요함

project-summarizer 본문은 Key Decisions를 반드시 포함하라고 하지만(`SKILL.md:56-74`) `references/template.md`에는 독립된 Key Decisions 섹션이 없다. repo-doc의 `validate_docs.sh:23-24`는 task 수를 세기만 하며 task 0건·빈 task·UF 수와 누락을 실패 처리하지 않는다. 이 검사는 “모든 기대 파일 구조 검증”이라는 안내보다 좁다.

**권고:** 공통 템플릿을 만들 때 본문·템플릿·검사기의 요구사항을 함께 맞춘다. 요약 템플릿에 결정 표를 넣고, repo-doc 검사는 입력 UF 수와 산출 task 수·비어 있는 계약을 확인하도록 범위를 명시한다. 이 두 스킬을 하나로 합쳐 해결할 문제는 아니다.

## 4. 변경 시 필요한 결합 지점

1. `skills/pipelines.json`의 categories/pipelines와 `project_resources`를 함께 갱신한다. doc-writer의 `runtime`은 설치 스킬에서 제외되고 tools로 별도 복사되는 구조다(`:173-205`). 템플릿을 runtime 아래에 두면 tools로, skill 자원에 두면 `.claude/skills`로 배포된다는 차이를 고려한다.
2. bridge의 형제 스킬 이름·스크립트 경로(`bridge_worker.py:24-28`)와 doc-writer의 tools import(`write_doc.py:75-80`)는 이름 변경만으로 바꾸지 않는다. 호환 엔트리포인트 또는 명시적 경로 해석 계층이 필요하다.
3. section 스킬을 병합하면 `defense-execution-manual/references/skill-io-map.md`, proposal README, catalog·pipeline 문서 및 assembler가 참조하는 생산자 이름을 확인한다.
4. 프로필 범용화는 기존 COMSAF 가짜 시험을 보존하고, 다른 이름의 합성 스타일 프로필을 대상으로 제목 검출·끼워 넣기 보존·그림 꾸러미·보고 위치가 일관되는지 검증해야 한다. 여기서 가짜 시험은 실제 앱의 보호 저장·조판 검증을 대체하지 않는다.
5. 재사용 템플릿에는 업무 내용·기관 실명·과거 승인·실제 문서 추출본을 넣지 않는다. 해당 포맷의 구조, 스타일, 빈 필드, 합성 예시만 제공한다.

## 5. 권장 최종 형태

- **콘텐츠 계층:** repo-doc writer, project summary, proposal content(공통 절차 + 섹션 템플릿). 입력 출처·정본·산출 목적은 각각 유지.
- **템플릿 계층:** 스킬 내부의 재사용 templates/profiles와 디자인 토큰. 프로젝트가 원하면 별도 프로필을 제공.
- **문서 실행 계층:** MS Office read/write, HWP read/edit, HWP 명세 렌더러. 상위 라우터는 하나여도 백엔드 계약은 유지.
- **실행 환경 계층:** Windows 직접 실행 / bridge. 현재 프로젝트 권한·경로·지문·격리·감사 조건을 관리.

`passed=true`는 요청한 정적 조사가 완료됐다는 뜻이다. 발견 항목이 없거나 실제 문서 생성이 검증됐다는 뜻이 아니다.

RESULT_JSON={"passed":true,"findings":[{"id":"DC-01","priority":1,"kind":"template-coupling","summary":"insert/figpack과 일부 보고 로직이 COMSAF 스타일에 고정되어 있다"},{"id":"DC-02","priority":1,"kind":"missing-reusable-template","summary":"실제 HWPX 템플릿과 SUM 표 서식이 외부 프로젝트 의존으로 남아 있다"},{"id":"DC-03","priority":2,"kind":"project-provenance","summary":"특정 프로젝트 경로·과거 승인·실측 안내가 현재 운영 문서에 혼재한다"},{"id":"DC-04","priority":2,"kind":"merge-opportunity","summary":"제안서 5개 섹션의 공통 절차는 통합하고 장별 계약은 템플릿으로 보존할 수 있다"},{"id":"DC-05","priority":2,"kind":"environment-coupling","summary":"GLOBAL_RULES 번호와 /mnt docx 설치 경로를 전제로 한다"},{"id":"DC-06","priority":2,"kind":"template-contract-drift","summary":"요약 결정 섹션과 repo task 검증에 본문·템플릿·검사기 불일치가 있다"}]}
