# AI Skills Library

스킬 **36개**를 파이프라인과 작업 흐름에 따라 **8개 분류 폴더**로 관리합니다.
정본은 `skills/<분류>/<스킬>/`입니다. 같은 스킬을 여러 파이프라인에 복제하지 않습니다.

## 파이프라인별 폴더

| 폴더 | 용도 | 정본 스킬 수 |
|---|---|---:|
| [skills/engineering_pipeline/](skills/engineering_pipeline/README.md) | 엔지니어링 설계·구현·평가 | 15 |
| [skills/coding_agent_pipeline/](skills/coding_agent_pipeline/README.md) | 외부 코딩 에이전트 연계 | 3 |
| [skills/proposal_pipeline/](skills/proposal_pipeline/README.md) | 연구 제안서 작성 | 8 |
| [skills/office_document_pipeline/](skills/office_document_pipeline/README.md) | Office·한글 문서 작업 | 2 |
| [skills/domain_audits/](skills/domain_audits/README.md) | 도메인별 감사 | 3 |
| [skills/agent_orchestration/](skills/agent_orchestration/README.md) | 에이전트 오케스트레이션 | 2 |
| [skills/artifact_workflows/](skills/artifact_workflows/README.md) | HTML 산출물 생성 | 2 |
| [skills/general/](skills/general/README.md) | 범용 문서화 | 1 |

각 분류의 README에 실행 흐름과 공용 스킬 참조를 기록했습니다.
공용 설계·요약 스킬은 [pipelines.json](skills/pipelines.json)에서 필요한 파이프라인에 함께 연결합니다.

## 자료 찾기

- [공통 지침·태스크 분담 개선](docs/global-rules-review-2026-10-26.md): 가벼운 기본 규칙과 선택형 추적, 메인·서브에이전트 운영.

- [문서 스킬 통합·범용화 내역](docs/document-skill-consolidation-2026-10-25.md): 작성 진입점 통합과 선택형 템플릿.
- [스킬 전체 목록](docs/skill-catalog.md): 용도·정본 경로·리소스 수.
- [템플릿 목록](docs/template-catalog.md): 스킬 전용 템플릿과 [프로젝트 시작 팩](templates/project/README.md).
- [프로젝트 스킬 반영 내역](docs/project-skill-update-2026-10-25.md): drmHWP·surak 비교, 작성 도구·시험 배포.
- [이전 비교·최신화 보고서](docs/skill-update-2026-10-25.md): 현재본·skillset1·skillset2 비교와 채택 근거.
- [Engineering 매뉴얼](docs/guides/Engineering_MANUAL.md), [외부 코딩 에이전트 매뉴얼](docs/guides/Pipeline_MANUAL.md), [조합 가이드](docs/guides/Skill_Combination_Usage_Guide.md).
- [초안](drafts/README.md) · [대체 버전](variants/README.md) · [생성 예제](examples/) · [설계 참고](docs/design/) · [기존 검토](review_docs/).

`compare/skillset1`과 `compare/skillset2`는 비교 입력으로 보존했습니다.
사용 스킬과 초안·과거 버전을 함께 자동 설치하지 않습니다.

## 프로젝트에 설치

분류된 정본을 프로젝트의 `.claude/skills/<name>/`로 평탄화하여 설치합니다.
설치본을 고치는 대신 이 저장소의 `skills/`를 수정하고 필요한 프로젝트에 다시 배포합니다.

```powershell
python scripts/install_skills.py --pipeline engineering --project-root <프로젝트_경로> --dry-run
python scripts/install_skills.py --pipeline engineering --project-root <프로젝트_경로>
```

`--pipeline` 선택값: `engineering`, `coding-agent`, `proposal`, `office-documents`,
`domain-audits`, `orchestration`, `artifacts`, `general`, `all`.
`office-documents`와 `all` 설치에는 doc-writer 실행 도구와 한글 모듈·시험의 `tools/`, 번들 서식의 `document_templates/` 배포도 포함됩니다. `--without-project-tools`로 `tools/`와 `document_templates/` 배포 없이 스킬과 전용 리소스만 설치할 수 있습니다.
기존 설치 파일이 다르면 쓰기 전에 중단합니다. 변경을 검토한 뒤 `--overwrite`로 파일을 갱신할 수 있으며, 프로젝트의 추가 파일은 지우지 않습니다.
이전 분리 스킬의 SKILL.md가 있으면 `--migrate-legacy`로 원본과 같은 진입점만 `.claude/retired-skills/`에 보관합니다. 수정된 이전 진입점은 자동 변경하지 않고 사전 검사에서 중단합니다.

`doc-writer`의 실행 도구·가짜 COM 시험은 포함되어 있습니다. 기본 한글 서식·표 스타일은 `doc-writer/templates/technical-report/`에 포함하며, 내용 출처·별도 조직 서식·실제 Windows 앱 환경은 대상 프로젝트에서 제공합니다.
브리지의 `insert`·`figpack`도 대상 도구와 지문이 없으면 거절합니다. [Office 배포 조건](skills/office_document_pipeline/office-drm-bridge/references/deployment.md)을 확인합니다.

새 프로젝트에는 [templates/project/](templates/project/)의 내용물을 프로젝트 루트로 복사합니다.
`GLOBAL_RULES.md`, 프로젝트 규칙 골격, 대장·빈 로그·검증 도구가 함께 있습니다.
MCP 연계 설정은 다음 생성기를 사용합니다.

```powershell
python scripts/generate_mcp_templates.py --project-root <프로젝트_경로>
```

## 관리 원칙

- 스킬의 `assets/`, `references/`, `reference/`, `scripts/`와 templates·backends·runtime은 해당 스킬 안에 유지합니다.
- 파이프라인을 바꾸면 `skills/pipelines.json`과 해당 분류 README도 함께 갱신합니다.
- 비교본에 일부 파일이 없다는 이유로 현재 정본의 검증 도구를 삭제하지 않습니다.
- 배포 지문·과거 승인·검증 이력은 다른 프로젝트에 그대로 적용하지 않습니다.
- 프로젝트 템플릿의 빈 로그·`.gitkeep`은 필요한 구성 요소입니다.
