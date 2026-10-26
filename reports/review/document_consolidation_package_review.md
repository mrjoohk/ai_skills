# 문서 스킬 통합 패키지 감사 — 2026-10-25

최종 패키지 판정: **PASS — 통합으로 인한 미해결 설치·등록·리소스 경로 결함 없음.** 아래 strict validator 호환성 제한과 실제 앱 미검증 범위를 분리해 기록한다. 실제 프로젝트나 Office·한글 COM은 실행·수정하지 않았다.

## 발견 사항과 해결 확인

1. **[해결] 브리지 지문 경로가 실제 배포 경로와 달랐다.** `skills/pipelines.json`은 공통 HWP 모듈을 `tools/hwpx-drm/scripts`에 배포한다. 브리지의 `INSERT_PIN_DIRS`와 일부 운영 안내는 존재하지 않는 `tools/doc-writer/backends/hwp/scripts`를 요구해 새 프로젝트의 insert·figpack 준비를 막을 수 있었다. 담당자의 추가 지시에 따라 브리지 구현·안내·해당 시험과 HWP 운영 안내를 실제 호환 배포 경로로 맞췄다. 최종 새 설치본에서 `tools/doc-writer`와 `tools/hwpx-drm/scripts`가 모두 존재하며 브리지 전체 137개 시험이 통과했다. 근거: `skills/office_document_pipeline/office-drm-bridge/scripts/bridge_core.py:48`, `references/deployment.md:9`, `:40`.
2. **[해결] 설치된 HWP 시험의 Office backend import가 정본 배치에만 맞았다.** `backends/hwp/tests/test_office_protection.py`가 형제 `office-writer`만 찾아 `tools/hwpx-drm/tests` 배포본에서 import 오류가 날 수 있었다. 담당자의 추가 지시에 따라 프로젝트 `.claude/skills/doc-writer/backends/office-writer/scripts/write_office_doc.py` 탐색을 추가했다. 최종 새 설치본의 HWP·Office 정책 시험 **140개 OK, skipped=2**를 실제 실행했다.
3. **[해결] 활성 제안서 가이드가 폐지된 장별 진입점 5개를 호출했다.** `docs/guides/proposal_skills.md`의 스킬 표·흐름도·장별 호출을 확인해 루트 담당자에게 전달했다. 수정 후 활성 guide와 canonical skill 문서에서 과거 8개 이름의 독립 스킬 호출은 남아 있지 않다. `hwpx-drm`은 실제 호환 도구 폴더·파일명으로 남아 있으므로 폐지된 진입점 호출과 구별했다. 과거 비교 기록의 이름은 archive 링크 또는 역사 설명이며 활성 설치 대상으로 취급하지 않는다.

감사는 읽기 전용으로 시작했다. 위 1·2의 배포 오류 수정과 후속 nested fake reader 수정은 담당자가 명시적으로 추가 허용한 범위만 변경했다. 루트 README·docs·installer·registry는 이 감사에서 수정하지 않았다.

## 등록·문법·링크 검토

| 확인 | 실제 결과 |
|---|---|
| canonical 등록 경로 | categories에 36개, 실제 `skills/**/SKILL.md` 36개; 누락·미등록·중첩 별도 진입점 0 |
| 파이프라인·optional skill 참조 | 알려지지 않은 이름 0, 중복 이름 없음; 실제 전체 설치 성공 |
| YAML 이름·설명 | 36개 모두 디렉터리 이름과 name 일치, description 문자열·비어 있지 않음 |
| 공식 quick_validate | **19개 통과, 17개 기존 `user-invocable` 필드의 strict schema 미지원** |
| JSON | 이번 범위의 정본·템플릿·스크립트·docs 내 JSON 9개 파싱 성공; runtime prototype 의미 검토 제외 |
| 로컬 Markdown 문서 링크 | 184개 문서·286개 링크 검사 후 실제 운영 리소스 누락 0; 아래 예외는 수동 분류 |
| 현재 도구·리소스 경로 | Office/HWP backend·장별 section 기준/템플릿·호환 tools·브리지 지문 경로 존재 |

quick_validate의 17건은 모두 같은 원인이다. Codex의 `C:/Users/user/.codex/skills/.system/skill-creator/scripts/quick_validate.py`가 기존 Claude 호환 필드 `user-invocable`을 허용하지 않아 해당 단계에서 종료한다. 내용·로컬 링크의 오류나 이번 통합으로 추가된 실패로 보고하지 않는다. 검증기는 수정하거나 허용 필드를 몰래 제거하지 않았으며, “36개 모두 strict validator 통과”라고 주장하지 않는다.

해당 17개: core-engineering, context-engineering, uf-chain-validator, uf-implementor, if-integrator, uf-if-debug-mapper, theory-decomposer, eval-planner, exp-runner, eval-runner, ci-evidence-automation, gpu-hpc-guard, sim-physics-auditor, rag-data-quality, agent-orchestration, agent-executor, travel-planner-html.

링크 검사에서 문서 내용과 생성 위치를 수동 확인한 예외:

- `repo-doc-writer/assets/overview_template.md:17-18`의 `architecture.md`·`tasks/`는 생성될 `docs/ai/` 결과의 형제 링크다. 배포해야 할 원본 리소스의 누락이 아니다.
- `docs/document-skill-consolidation-2026-10-25.md:41-42`의 패키지·종합 감사 보고서 링크는 검사 당시 생성 중이었다. 최종 확인에서는 이 보고서와 `document_consolidation_final_review.md`가 모두 존재한다. 실행 리소스 누락은 아니다.

## 실제 설치·마이그레이션·배포 시험

격리 루트: `C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/package-audit/`.

최종 검증은 앞선 설치본을 재사용하지 않은 `fresh-all-v3`, `without-tools-v3`, `migrate-eight-v3`에서 수행했다. 최종 installer의 `skill_required_files`·`project_resources.required_files` 계약과 `template_model.py` 필수 리소스 조건이 반영된 버전이다.

| 실제 실행·대조 | 결과 |
|---|---|
| `install_skills.py --pipeline all --project-root <fresh-all-v3>` | 종료코드 0; 활성 진입점 36개, tools·HWP 모듈·문서 서식 설치 |
| 같은 all 설치의 `--without-project-tools` | 종료코드 0; 진입점 36개·backend·profile 유지, tools와 document_templates 미생성 |
| `python -m unittest discover -s scripts/tests -v` | **9개 OK**; 필수 writer 누락 거절·수정된 legacy 거절·충돌 전 중단·dry-run·기존 추가 파일 보존 포함 |
| archive의 원본 8개 진입점을 넣고 `--pipeline all --migrate-legacy` | 종료코드 0; 8개 retired archive·36개 활성 진입점·8개 프로젝트 추가 파일 모두 보존 |
| 새 설치본 `python -m unittest discover -s tools/hwpx-drm/tests` | **140개 OK, skipped=2** |
| 새 설치본 `python -W ignore::ResourceWarning -m unittest discover -s .claude/skills/office-drm-bridge/tests` | **137개 OK, skipped=1** |
| 새 설치본의 지문 디렉터리 검사 | `tools/doc-writer`, `tools/hwpx-drm/scripts` 모두 존재 |

HWP 2개 skip은 선택적 실제 드라이버가 배포되지 않은 조건이며, 브리지 1개 skip은 Windows 심볼릭 링크 생성 권한 부족이다. 실제 COM이 필요한 시험을 대신 실행한 것이 아니다. 브리지 경로·파서 대조는 실제 스크립트의 parser만 사용한다.

## 후속 nested fake reader 보강

별도 모형 감사에서 중첩 `PARASHAPE`·`CHARSHAPE`가 빈 요소만 읽는 fake reader에서 누락되는 문제가 추가 전달됐다. 담당자의 요청에 따라 `backends/hwp/tests/fake_hwp.py`를 다음과 같이 보강하고 `test_fake_head.py` 의미 시험 6개를 추가했다.

- Expat의 구조·바이트 경계로 빈 요소와 paired 요소의 정확한 전체 XML 조각을 반환한다.
- `_head_attrs`는 부모 요소 속성만 반환한다. 자식의 Id·Type·Level·Height가 부모 값을 덮어쓰지 않는다.
- 부모 속성 변경은 자식 XML 바이트를 보존한다. 정렬·글자 크기 복제와 InsertFile도 PARAMARGIN·FONTID·BOLD를 보존한다.
- paired STYLE 삭제는 전체 정의를 제거하며 자식 요소를 고아로 남기지 않는다.

의미 시험 6개 OK, 정본 HWP 전체 **140개 OK(2 skip)**, 정본 runtime 회귀 **215개 OK(0 skip)**를 실제 실행했다. 모델 변환기·실제 HWPX 패키지와 가짜 모델의 전체 의미 일치 판정은 별도 감사 범위이며 이 패키지 보고서에서 대신 승인하지 않는다.

실행 근거: [감사 요약 JSON](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/package-audit/audit_results.json), [설치기 9개 시험](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/package-audit/logs/migration_eight_tests.log), [설치본 HWP 시험](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/package-audit/logs/installed_hwp_tests.log), [설치본 브리지 시험](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/package-audit/logs/installed_bridge_tests.log).

RESULT_JSON={"passed":true,"findings":[]}
