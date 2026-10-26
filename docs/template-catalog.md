# 템플릿 목록

템플릿은 사용하는 스킬 폴더 안에 둔다. 프로젝트의 실제 내용과 입력 경로는 명세·메타데이터에서 지정한다.

## 문서 작성

| 템플릿 | 용도 |
|---|---|
| [technical-report](../skills/office_document_pipeline/doc-writer/templates/technical-report/) | A4 한글 기술문서: HWPX 패키지·XML 원본·프로파일·표 서식·가짜 COM 모형·생성기·검사기 |
| [제안서 목차 5종과 메타데이터](../skills/proposal_pipeline/defense-proposal-writer/templates/) | 개요·개발 방안·기술 분석·연구 계획·세부 계획, 선택형 발표 테마 |
| [저장소 문서](../skills/coding_agent_pipeline/repo-doc-writer/assets/) | 개요·아키텍처·단위 기능 작업 문서 |
| [프로젝트 요약](../skills/general/project-summarizer/references/template.md) | 진행·결정·검증·다음 단계 기록 |

한글 번들은 구조 검사 통과, 실제 앱 열림·조판 미검증이다. [서식 적용 방법](../skills/office_document_pipeline/doc-writer/references/profiles.md)을 확인한다.

## 그 밖의 스킬 템플릿

| 스킬 | 리소스 |
|---|---|
| req-elicitor | [assets/assumptions_constraints_template.md](../skills/engineering_pipeline/req-elicitor/assets/assumptions_constraints_template.md) |
| req-elicitor | [assets/clarification_log_template.md](../skills/engineering_pipeline/req-elicitor/assets/clarification_log_template.md) |
| req-elicitor | [assets/problem_statement_template.md](../skills/engineering_pipeline/req-elicitor/assets/problem_statement_template.md) |
| req-elicitor | [assets/requirements_template.md](../skills/engineering_pipeline/req-elicitor/assets/requirements_template.md) |
| if-designer | [assets/if_decomposition_template.md](../skills/engineering_pipeline/if-designer/assets/if_decomposition_template.md) |
| if-designer | [assets/if_list_template.md](../skills/engineering_pipeline/if-designer/assets/if_list_template.md) |
| uf-designer | [assets/uf_block_template.md](../skills/engineering_pipeline/uf-designer/assets/uf_block_template.md) |
| uf-implementor | [assets/test-template.py](../skills/engineering_pipeline/uf-implementor/assets/test-template.py) |
| uf-implementor | [assets/uf-module-template.py](../skills/engineering_pipeline/uf-implementor/assets/uf-module-template.py) |
| fresh-eyes-auditor | [assets/checks_config.template.json](../skills/engineering_pipeline/fresh-eyes-auditor/assets/checks_config.template.json) |
| fresh-eyes-auditor | [assets/disposition_template.md](../skills/engineering_pipeline/fresh-eyes-auditor/assets/disposition_template.md) |
| fresh-eyes-auditor | [assets/report_template.md](../skills/engineering_pipeline/fresh-eyes-auditor/assets/report_template.md) |
| fresh-eyes-auditor | [reference/delta_prompt_template.md](../skills/engineering_pipeline/fresh-eyes-auditor/reference/delta_prompt_template.md) |
| fresh-eyes-auditor | [reference/spawn_prompt_template.md](../skills/engineering_pipeline/fresh-eyes-auditor/reference/spawn_prompt_template.md) |
| cursor-task-formatter | [assets/fix_prompt_template.md](../skills/coding_agent_pipeline/cursor-task-formatter/assets/fix_prompt_template.md) |
| cursor-task-formatter | [assets/implement_prompt_template.md](../skills/coding_agent_pipeline/cursor-task-formatter/assets/implement_prompt_template.md) |
| code-reviewer | [assets/review_report_template.md](../skills/coding_agent_pipeline/code-reviewer/assets/review_report_template.md) |
| defense-proposal-prep | [references/rfp-analysis-template.md](../skills/proposal_pipeline/defense-proposal-prep/references/rfp-analysis-template.md) |
| defense-kpi-benchmark | [references/benchmark-survey-template.md](../skills/proposal_pipeline/defense-kpi-benchmark/references/benchmark-survey-template.md) |
| defense-execution-manual | [references/manual-template.md](../skills/proposal_pipeline/defense-execution-manual/references/manual-template.md) |
| agent-orchestration | [assets/agent-role-template.md](../skills/agent_orchestration/agent-orchestration/assets/agent-role-template.md) |
| agent-orchestration | [assets/orchestration-plan-template.md](../skills/agent_orchestration/agent-orchestration/assets/orchestration-plan-template.md) |
| dashboard-designer | [assets/archetypes/single-html-tabbed/template.html](../skills/artifact_workflows/dashboard-designer/assets/archetypes/single-html-tabbed/template.html) |
| dashboard-designer | [assets/archetypes/split-pane-inspector/template.html](../skills/artifact_workflows/dashboard-designer/assets/archetypes/split-pane-inspector/template.html) |
| dashboard-designer | [assets/dashboard_spec_template.md](../skills/artifact_workflows/dashboard-designer/assets/dashboard_spec_template.md) |

## 프로젝트 시작 팩

[AGENTS 진입점](../templates/project/AGENTS.md) · [가벼운 공통 규칙](../templates/project/GLOBAL_RULES.md) · [선택형 추적 규약](../templates/project/policies/TRACEABILITY.md) · [프로젝트 설정 골격](../templates/project/PROJECT_RULES.template.md)

[templates/project/](../templates/project/)에는 선택형 프로젝트 규칙·빈 로그·검증 도구가 있다. 문서 작성 스킬은 이 팩이나 특정 이름의 규칙 파일 설치를 전제로 하지 않는다.

[MCP 골격 생성기](../scripts/generate_mcp_templates.py) · [초안 템플릿](../drafts/producer-critic/)
