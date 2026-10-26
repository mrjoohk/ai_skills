# 스킬 비교·최신화 기록 — 2026-10-25

> 이전 비교 작업의 기록입니다. 이후 drmHWP·surak 반영으로 실행 도구를 추가했습니다. 현재 상태는 [프로젝트 반영 내역](project-skill-update-2026-10-25.md)을 참조합니다.

## 결과

- 기존 42개를 비교하여 기능 2개(hwpx-drm·office-drm-bridge)를 갱신하고 doc-writer 1개를 추가했습니다. 최종 정본은 **43개**, 분류 폴더는 **8개**입니다.
- 기능 변경 외에 Office 스킬 4개의 잘못된 YAML 설명 형식과 exp-runner의 설명 표기를 고쳤습니다.
- 정본은 `skills/<분류>/<스킬>/`입니다. 공용 스킬의 실행 구성은 [pipelines.json](../skills/pipelines.json)에 정의하고 분류 간에 복제하지 않습니다.
- `compare/skillset1`, `compare/skillset2`는 비교 입력으로 보존했습니다. Git 스테이징·커밋은 하지 않았습니다.

## 채택 기준

수정 시각 대신 파일 내용을 비교했습니다. 텍스트는 CRLF/LF를 정규화하여 비교하고 Python 캐시는 제외했습니다. 서로 다른 내용은 본문·스크립트·시험·의존 리소스를 함께 확인했습니다.

- skillset1의 engineering 계열은 대부분 현재와 같습니다. hwpx-drm과 office-drm-bridge에 추가된 기능을 채택했습니다.
- skillset2의 ci-evidence-automation·context-engineering·core-engineering·fresh-eyes-auditor는 현재보다 이전 내용 또는 리소스 누락이 있어 현재 정본을 유지했습니다.
- 두 비교본에 없는 UF 계약·테스트 경로 검증 스크립트 2개와 contracts.example.json은 현재 정본에서 유지했습니다.
- uf-implementor의 이전 위치 안내 문서 3개는 다시 가져오지 않았습니다. 실제 문서는 references/에 있습니다.
- skillset1의 insert_pin.json은 특정 프로젝트의 도구 지문이므로 가져오지 않았습니다. 배포 대상의 도구를 확인한 지문이 필요합니다.
- Engineering 매뉴얼은 현재·skillset1의 최신 내용을 유지했고 이전 skillset2로 되돌리지 않았습니다.

## 기능 갱신

### hwpx-drm

문서에 포함된 그림 추출(images), raw·zlib·deflate 그림 데이터 해석, 그림 목록·해시·위치 기록, 검색어의 이스케이프 쉼표 처리를 반영했습니다.
합성 HWPML 시험에서 BinItem 0·음수 값이 다른 그림을 잘못 선택하는 결함을 확인하여 유효 범위 밖 번호는 건너뛰도록 수정했습니다. 원본 코드가 해당 시험에 실패하는 음성 대조도 확인했습니다.

### office-drm-bridge

v1.2의 insert·figpack·images 연산, 같은 규칙의 검색어 분리, 긴 요청 중 하트비트 갱신, 명세·그림 경로 검사, 도구 지문 대조와 보호되지 않은 결과 격리를 반영했습니다.
[배포 조건](../skills/office_document_pipeline/office-drm-bridge/references/deployment.md)에 대상 프로젝트 도구·템플릿·지문 의존성을 명시했습니다.

### doc-writer

기술문서 작성·기존 문서에 절 추가 스킬을 추가했습니다. 원본 프로젝트의 긴 서식·명세 규칙은 references/drmHWP-profile.md에 나누어 필요한 경우만 읽도록 했습니다.
비교본에는 write_doc.py·insert_doc.py·figure_pack.py와 문서 템플릿이 없습니다. 명세 작성·검토는 가능하며 실제 한글 산출물 생성은 해당 프로젝트가 실행 도구와 템플릿을 제공해야 합니다. 과거 승인·실측 이력은 현재 프로젝트의 승인·검증으로 재사용하지 않습니다.

## 스킬별 비교

표의 변경·추가·누락은 **작업 전 현재본에 대한 비교본의 차이**입니다.

| 스킬 | skillset1 | skillset2 | 최종 선택 |
|---|---|---|---|
| [agent-executor](../skills/agent_orchestration/agent-executor/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [agent-orchestration](../skills/agent_orchestration/agent-orchestration/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [ci-evidence-automation](../skills/engineering_pipeline/ci-evidence-automation/SKILL.md) | 동일 | 변경 2 · 누락 3 | 현재 유지 |
| [code-reviewer](../skills/coding_agent_pipeline/code-reviewer/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [context-engineering](../skills/engineering_pipeline/context-engineering/SKILL.md) | 동일 | 변경 1 | 현재 유지 |
| [core-engineering](../skills/engineering_pipeline/core-engineering/SKILL.md) | 동일 | 변경 2 | 현재 유지 |
| [cursor-task-formatter](../skills/coding_agent_pipeline/cursor-task-formatter/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [dashboard-designer](../skills/artifact_workflows/dashboard-designer/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-diagram](../skills/proposal_pipeline/defense-diagram/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-execution-manual](../skills/proposal_pipeline/defense-execution-manual/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-kpi-benchmark](../skills/proposal_pipeline/defense-kpi-benchmark/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-assembler](../skills/proposal_pipeline/defense-proposal-assembler/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-detail-plan](../archive/document-skills-2026-10-25/proposal-sections/defense-proposal-detail-plan/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-overview](../archive/document-skills-2026-10-25/proposal-sections/defense-proposal-overview/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-prep](../skills/proposal_pipeline/defense-proposal-prep/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-rd-plan](../archive/document-skills-2026-10-25/proposal-sections/defense-proposal-rd-plan/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-research-plan](../archive/document-skills-2026-10-25/proposal-sections/defense-proposal-research-plan/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-proposal-tech-analysis](../archive/document-skills-2026-10-25/proposal-sections/defense-proposal-tech-analysis/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-rfp-generator](../skills/proposal_pipeline/defense-rfp-generator/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [defense-wbs-tbs](../skills/proposal_pipeline/defense-wbs-tbs/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [doc-writer](../skills/office_document_pipeline/doc-writer/SKILL.md) | 신규 (1파일) | 없음 | skillset1 신규 추가 + 프로젝트별 상세·외부 의존성 분리 |
| [eval-planner](../skills/engineering_pipeline/eval-planner/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [eval-runner](../skills/engineering_pipeline/eval-runner/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [exp-runner](../skills/engineering_pipeline/exp-runner/SKILL.md) | 동일 | 동일 | 현재 기능 유지, 설명의 경로 자리표시 표기 정리 |
| [fresh-eyes-auditor](../skills/engineering_pipeline/fresh-eyes-auditor/SKILL.md) | 동일 | 변경 4 · 누락 3 | 현재 유지 |
| [gpu-hpc-guard](../skills/domain_audits/gpu-hpc-guard/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [hwpx-drm](../archive/document-skills-2026-10-25/hwpx-drm.SKILL.md) | 변경 2 · 추가 1 | 없음 | skillset1 기능 갱신 + 잘못된 그림 번호 처리 수정 |
| [if-designer](../skills/engineering_pipeline/if-designer/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [if-integrator](../skills/engineering_pipeline/if-integrator/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [office-com-reader](../archive/document-skills-2026-10-25/office-com-reader.SKILL.md) | 동일 | 없음 | 현재 기능 유지, YAML 설명 형식 수정 |
| [office-com-writer](../archive/document-skills-2026-10-25/office-com-writer.SKILL.md) | 동일 | 없음 | 현재 기능 유지, YAML 설명 형식 수정 |
| [office-drm-bridge](../skills/office_document_pipeline/office-drm-bridge/SKILL.md) | 변경 6 · 추가 1 | 없음 | skillset1 v1.2 갱신 + 배포 조건 분리 |
| [project-summarizer](../skills/general/project-summarizer/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [rag-data-quality](../skills/domain_audits/rag-data-quality/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [repo-doc-writer](../skills/coding_agent_pipeline/repo-doc-writer/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [req-elicitor](../skills/engineering_pipeline/req-elicitor/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [sim-physics-auditor](../skills/domain_audits/sim-physics-auditor/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [theory-decomposer](../skills/engineering_pipeline/theory-decomposer/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [travel-planner-html](../skills/artifact_workflows/travel-planner-html/SKILL.md) | 없음 | 없음 | 현재 유지 |
| [uf-chain-validator](../skills/engineering_pipeline/uf-chain-validator/SKILL.md) | 누락 3 | 누락 3 | 현재 유지 |
| [uf-designer](../skills/engineering_pipeline/uf-designer/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [uf-if-debug-mapper](../skills/engineering_pipeline/uf-if-debug-mapper/SKILL.md) | 동일 | 동일 | 현재 유지 |
| [uf-implementor](../skills/engineering_pipeline/uf-implementor/SKILL.md) | 추가 3 | 추가 3 | 현재 유지 |

## 폴더와 설치

[스킬 목록](skill-catalog.md)에 분류별 정본 경로와 용도를 기록했습니다. 각 분류 README에는 파이프라인 순서와 공용 스킬 참조가 있습니다.
[설치 도구](../scripts/install_skills.py)는 선택한 파이프라인을 프로젝트의 `.claude/skills/<name>/`에 평탄화해 설치합니다. 기존 파일 충돌은 쓰기 전에 검사하고, 명시적 --overwrite에서도 프로젝트의 추가 파일은 지우지 않습니다.

## 검증

- 브리지: **128건 중 125건 통과, 3건 조건부 제외**. 제외 사유는 Windows 심볼릭 링크 생성 권한 1건, 제공되지 않은 insert_doc.py·figure_pack.py 실제 CLI 2건입니다.
- 그림 추출: **8건 통과**. 그림 바이트·해시·크기·압축·연결 그림·잘못된 번호·중첩 위치를 합성 HWPML로 확인했습니다.
- 합계 **136건 중 133건 통과, 3건 조건부 제외**. 실제 Office/한글 COM 문서를 열거나 외부 워커를 기동하지 않았습니다.
- 설치: 43개·186파일의 원본 일치, 미리 보기 무변경, 반복 설치, 충돌 시 부분 쓰기 없음, 명시적 갱신 시 추가 파일 보존을 확인했습니다.
- 43개 스킬의 YAML·이름·설명·중복을 검사했습니다. skill-creator quick_validate는 26개가 그대로 통과했습니다. 나머지 17개는 기존 Claude 확장 키 user-invocable을 보존했고, 그 키만 제외한 검증용 사본에서 Codex 공통 메타데이터 검사를 통과했습니다. 실제 정본의 호출 정책은 바꾸지 않았습니다.
- 문서 링크·리소스 참조와 원본 비교 자료·유지한 검증 도구의 해시를 최종 검사했습니다.

## 백업과 상세 근거

작업 전 전체 파일과 Git 상태·비교 diff·검증 결과는 저장소 밖에 보관했습니다.

- [작업 전 ZIP](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/skill-update/before-update.zip)
- [파일 해시 목록](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/skill-update/before-manifest.json)
- [이동·채택 계획](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/skill-update/update-plan.json)
- [메타데이터 검사](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/skill-update/skill-validation.json)
- [브리지 시험 기록](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/skill-update/bridge-updated-tests.log)
