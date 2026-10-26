# 스킬 목록

활성 스킬 **36개**, 분류 **8개**. 정본은 skills/<분류>/<스킬>/이며 중복 진입점은 설치하지 않는다.

[공통 지침·태스크 분담 개선](global-rules-review-2026-10-26.md) · [문서 스킬 통합](document-skill-consolidation-2026-10-25.md) · [설치 정의](../skills/pipelines.json)

| 분류 | 용도 | 스킬 수 |
|---|---|---:|
| [engineering_pipeline](../skills/engineering_pipeline/README.md) | 엔지니어링 설계·구현·평가 | 15 |
| [coding_agent_pipeline](../skills/coding_agent_pipeline/README.md) | 외부 코딩 에이전트 연계 | 3 |
| [proposal_pipeline](../skills/proposal_pipeline/README.md) | 연구 제안서 작성 | 8 |
| [office_document_pipeline](../skills/office_document_pipeline/README.md) | Office·한글 문서 작업 | 2 |
| [domain_audits](../skills/domain_audits/README.md) | 도메인별 감사 | 3 |
| [agent_orchestration](../skills/agent_orchestration/README.md) | 에이전트 오케스트레이션 | 2 |
| [artifact_workflows](../skills/artifact_workflows/README.md) | HTML 산출물 생성 | 2 |
| [general](../skills/general/README.md) | 범용 프로젝트 기록 | 1 |

## 엔지니어링 설계·구현·평가

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [core-engineering](../skills/engineering_pipeline/core-engineering/SKILL.md) | Global rules for requirements, verification, and integration across projects. Defines the end-to-end design process from problem to unit functions. | 3 |
| [context-engineering](../skills/engineering_pipeline/context-engineering/SKILL.md) | 기존 저장소 환경과 규칙을 확인해 요청한 에이전트 설정 파일의 프로젝트 맥락·태스크 분담·재개 지침을 생성하거나 갱신한다. CLAUDE.md·AGENTS.md·GEMINI.md 등 설정 정리와 프로젝트 컨텍스트 동기화에 사용한다. | 0 |
| [req-elicitor](../skills/engineering_pipeline/req-elicitor/SKILL.md) | Executes core-engineering Stages 1–4: transforms a natural-language problem description into four structured design artifacts — problem_statement.md, clarification_log.md, assumptions_and_constraints.md, and requirements.md (REQ Blocks with numeric Given/When/Then acceptance criteria). This is the mandatory entry point for every new core-engineering project. Trigger whenever the user describes a problem they want to design or engineer, says things like "문제 정의해줘", "요구사항 뽑아줘", "REQ 써줘", "requirements 만들어줘", "프로젝트 시작", "설계 시작", or provides a problem background and wants to proceed with structured engineering. Also trigger before running if-designer or uf-implementor when no requirements.md exists yet. | 7 |
| [if-designer](../skills/engineering_pipeline/if-designer/SKILL.md) | Executes core-engineering Stages 5–6: reads requirements.md (REQ Blocks) and produces if_list.md (Integration Function definitions with I/O contracts) and if_decomposition.md (IF→UF candidate tree with dependency graph). This is the bridge between requirements and implementation — it translates what the system must do into a concrete module boundary design. Trigger when the user says "IF 설계해줘", "인터페이스 설계", "if_list 만들어줘", "시스템 경계 설계", "IF 분해해줘", "IF decomposition", "모듈 경계 잡아줘", or after req-elicitor has produced requirements.md and the user wants to proceed to Stage 5–6. Also trigger when the user provides requirements.md and wants to know how to break the system into integration functions before implementing UFs. | 5 |
| [uf-designer](../skills/engineering_pipeline/uf-designer/SKILL.md) | Executes core-engineering Stage 7: reads if_decomposition.md (UF candidate tree from if-designer) and produces uf.md — fully specified UF Blocks with I/O contracts, algorithm summaries, edge cases, and verification plans. This is the final design artifact before implementation begins. Trigger when the user says "UF 설계해줘", "UF 블록 만들어줘", "uf.md 작성", "유닛 함수 정의해줘", "UF spec 써줘", or after if-designer has produced if_decomposition.md and the user wants to define UF Blocks before running uf-implementor or uf-chain-validator. Also trigger when the user has a decomposition tree and wants to formalize each leaf node into an implementable spec. | 3 |
| [uf-chain-validator](../skills/engineering_pipeline/uf-chain-validator/SKILL.md) | Validates UF-chain integrity, I/O contracts, verification ownership completeness, and evidence linkage. Uses three separate gates: implementation/runtime, document-to-test-plan alignment, and evidence-pack completeness. | 6 |
| [uf-implementor](../skills/engineering_pipeline/uf-implementor/SKILL.md) | Implements Unit Functions (UFs) as production-ready code from UF Block definitions. Generates implementation stubs, docstrings, unit tests, and verifies against I/O contracts and acceptance criteria. Trigger when the user says 'implement UF', 'write code for unit function', 'generate UF implementation', or 'code up the UF blocks'. | 6 |
| [if-integrator](../skills/engineering_pipeline/if-integrator/SKILL.md) | Integrates implemented Unit Functions (UFs) into Integration Function (IF) level modules. Generates integration glue code, public API interfaces, integration tests, and validates that the combined UF outputs satisfy the parent IF's I/O contract and acceptance criteria. Trigger when the user says 'integrate UFs into IF', 'build IF module', 'write integration code', 'assemble unit functions', or 'create integration tests'. | 3 |
| [uf-if-debug-mapper](../skills/engineering_pipeline/uf-if-debug-mapper/SKILL.md) | Maps UF/IF issues to code locations and generates a human-in-the-loop debugging plan. | 3 |
| [theory-decomposer](../skills/engineering_pipeline/theory-decomposer/SKILL.md) | Reconstructs a domain theory's equations and dynamics when no (or partial) open-source reference exists: checks source availability first, then recursively decomposes the theory into atomic sub-theories using explicit stopping criteria, writes each as an EQ Block (UF Block superset with Equation, Assumptions, Validity Domain, Source), and gates the merge with unit/dimension/frame/assumption-compatibility and coupling-term coverage checks so the existing pipeline (uf-implementor → if-integrator) can implement and merge them into the original dynamics. Trigger when the user says "이론 분해해줘", "이론 쪼개줘", "수식 유도해줘", "수식 머지", "동역학 만들어줘", "동역학 유도", "지배방정식 도출", "theory decomposition", "derive dynamics", "equation merge", or wants to build a physics/domain model without a reference implementation. Also trigger when the user has a theory or phenomenon description and wants equation-level design artifacts (eq.md, theory_tree.md) before implementation. | 3 |
| [eval-planner](../skills/engineering_pipeline/eval-planner/SKILL.md) | Designs domain-appropriate evaluation metrics, thresholds, and benchmark plans from REQ/UF/IF blocks or design documents. Use as the dedicated entry point for core-engineering Stage 8. Trigger when the user asks to define evaluation criteria, set acceptance thresholds, plan benchmarks, or translate requirements into measurable metrics — even if they don't explicitly mention 'Stage 8' or 'evaluation plan'. Also trigger when a design document exists and the user wants to know how to measure success. Boundary: engineering evaluation design only — defense-proposal KPI/SoA benchmarking belongs to defense-kpi-benchmark. | 4 |
| [exp-runner](../skills/engineering_pipeline/exp-runner/SKILL.md) | Executes experiments defined in rd/evaluation_plan.md and produces the raw result data + provenance records that eval-runner consumes. Fills the pipeline gap between eval-planner (plan) and eval-runner (metric computation): fixes seeds and environment, runs training/inference/simulation commands per scenario, and writes evidence_pack/runs.yaml, evidence_pack/env.yaml, and results/{exp_id}/ outputs. Trigger when the user says "실험 돌려줘", "실험 실행", "run experiments", "execute the evaluation plan", "베이스라인 돌려줘", "학습 실행하고 기록해줘", or when evaluation_plan.md exists but no experiment results/runs.yaml exist yet. Also trigger before eval-runner when the user asks to compare models but no result data has been produced. | 2 |
| [eval-runner](../skills/engineering_pipeline/eval-runner/SKILL.md) | Generates metric calculation functions and formatted comparison reports from an evaluation plan or metric list with experimental result data. Trigger when the user has experiment outputs and wants to compute metrics, compare runs, or produce a readable evaluation report — even without mentioning 'eval-runner' explicitly. Also trigger when the user says things like 'calculate metrics', 'compare these results', 'show me how the model did', or 'make a results table'. | 4 |
| [ci-evidence-automation](../skills/engineering_pipeline/ci-evidence-automation/SKILL.md) | Automates CI checks, coverage gates, evidence packs, and regression reporting. | 6 |
| [fresh-eyes-auditor](../skills/engineering_pipeline/fresh-eyes-auditor/SKILL.md) | 무맥락 신규 에이전트를 스폰해 지금까지의 설계·구현을 모호함·억지·오류·환각 4축으로 감사하고, 발견을 인용 검증(트리아지) 후 자문 리포트로 보고한다. 트리거: "모호함, 억지, 오류, 환각 없는지 검토", "지금까지 설계/구현 검토해줘", "새 에이전트로 검토", "독립 검증", "무맥락 검토", "신선한 눈으로 봐줘", "fresh eyes review". Delta 모드는 변경 범위와 가용 인원에 맞춰 알고리즘 성질·호스트 흐름·시험 관점을 선택해 검토한다. 검토 범위·예산을 정하고 채택된 변경만 재확인한다. 트리거: "같은 날 변경 검토", "변경분 검토", "델타 검토", "delta review". (기계적 계약 검증은 uf-chain-validator, 코드 품질 리뷰는 code-reviewer 소관) | 13 |

## 외부 코딩 에이전트 연계

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [repo-doc-writer](../skills/coding_agent_pipeline/repo-doc-writer/SKILL.md) | REQ·IF·UF 설계 산출물을 외부 코딩 에이전트가 구현에 사용할 개요·아키텍처·UF별 태스크 Markdown으로 변환하거나 갱신한다. 코딩 에이전트용 문서, docs/ai 갱신, 설계의 저장소 반영, task 문서 요청에 사용한다. 진행 이력·회고 요약은 project-summarizer의 별도 목적을 유지한다. | 7 |
| [cursor-task-formatter](../skills/coding_agent_pipeline/cursor-task-formatter/SKILL.md) | Converts UF Block definitions (from rd/uf.md) or code review findings (from code-reviewer) into ready-to-paste task prompts for any external coding agent (Cursor Composer, Windsurf, Copilot Workspace, Codex/Gemini CLI, etc. — "Cursor" is the canonical example). Produces structured, self-contained prompts that any coding agent can act on without additional context. Trigger when the user says "Cursor 프롬프트 만들어줘", "코딩 에이전트 프롬프트 만들어줘", "구현 지시서 써줘", "task prompt 생성해줘", "fix prompt 만들어줘", "에이전트에 넘겨줄 내용 만들어줘", or after uf-designer or code-reviewer has produced output and the user wants to move to the implementation/fix step with an external coding agent. Also trigger when the user has a UF spec or review result and wants to know exactly what to paste into their coding agent. | 3 |
| [code-reviewer](../skills/coding_agent_pipeline/code-reviewer/SKILL.md) | Performs structured code review against UF/IF contracts, requirements, and coding standards. Produces a prioritized finding report that cursor-task-formatter can turn into fix prompts for any external coding agent. Implementation-agent-agnostic: reviews code the same way whether it was written by Cursor, Windsurf, Copilot, another agent, or a human. Trigger when the user says "코드 리뷰해줘", "리뷰 해줘", "구현 검토해줘", "코드 확인해줘", "review this code", "PR 리뷰", "버그 찾아줘", "개선점 찾아줘", or after a coding agent has finished implementing UFs and the user wants to validate the result before merging. Also trigger when the user shares code files and asks for quality, correctness, or contract compliance checks. Do NOT wait for the user to say "code review" specifically — trigger whenever new implementation is ready and the user wants feedback. | 2 |

## 연구 제안서 작성

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [defense-rfp-generator](../skills/proposal_pipeline/defense-rfp-generator/SKILL.md) | 연구 주제만 있고 RFP(공모 문서)가 없을 때, 유사 국내외 프로그램을 웹에서 조사하여 합성 RFP(공모 문서)를 자동 생성하는 스킬. 과제명을 입력하면 유사 DARPA/AFRL/NATO/방위사업청 프로그램을 5~7개 검색·분석하고, 현실적인 기술 요구사항·평가 배점·납품물·일정이 담긴 RFP 문서(.docx)와 분석 요약(.md)을 생성한다. MANDATORY TRIGGERS: "RFP 만들어줘", "공모 문서 만들어줘", "RFP가 없어", "RFP 없는데", "유사 프로그램 찾아줘", "비슷한 RFP", "과제 공고 만들어줘", "rfp generator", "모의 RFP", "합성 RFP", "주제만 있어", "공모문서 없음". RFP 없이 제안서 작성을 시작하려는 상황이면 반드시 이 스킬을 사용할 것. defense-proposal-prep 스킬 실행 전에 이 스킬을 먼저 실행하도록 안내한다. | 2 |
| [defense-proposal-prep](../skills/proposal_pipeline/defense-proposal-prep/SKILL.md) | 방산 연구 제안서 작성 전 사전 분석 스킬. RFP(공모 문서) 분석 → 요구사항 도출 → 기능·TRL 갭 분석 → 최신 기술 벤치마킹 → 혁신성·도전성 포지셔닝까지 제안 전략 문서를 생성한다. MANDATORY TRIGGERS: "RFP 분석", "공모 문서 분석", "제안서 준비", "요구사항 뽑아줘", "제안 전략 잡아줘", "벤치마킹 조사", "혁신성 포지셔닝", "제안 전 준비", "사전 분석". 방산 제안서를 쓰기 전 준비 단계가 언급되면 반드시 이 스킬을 사용할 것. | 2 |
| [defense-kpi-benchmark](../skills/proposal_pipeline/defense-kpi-benchmark/SKILL.md) | 방산 제안 기술의 구성 기술별 국내외 연구동향을 조사하여 주요 성능 지표(KPI)를 도출하고, 근거 있는 정량적·정성적 목표치를 제안한다. 혁신성과 도전성을 성능 수치로 뒷받침하는 핵심 스킬. MANDATORY TRIGGERS: "성능 목표 설정", "KPI 도출", "목표치 제안", "성능 지표 뽑아줘", "벤치마크 조사", "국내외 성능 비교", "정량 목표 근거", "목표 수치 어떻게 정해", "기술 수준 조사", "SoA 조사", "state-of-the-art 조사". 성능 목표치나 KPI 설정이 언급되면 반드시 이 스킬을 사용할 것. 경계: 이 스킬은 "제안서 KPI·SoA 벤치마킹" 전용. 엔지니어링 실행 단계의 평가 지표· 데이터셋·임계값 설계(evaluation_plan.md)는 eval-planner 소관. 이 스킬의 KPI 산출표는 모든 제안서 섹션 스킬이 인용하는 단일 정본이다. | 2 |
| [defense-proposal-writer](../skills/proposal_pipeline/defense-proposal-writer/SKILL.md) | 연구 제안서의 개요·연구개발 방안·기술 분석·연구 계획·세부 계획을 출처와 사용자 양식에 맞춰 작성하거나 수정한다. 제안서 장·절 작성, 연구 목표·일정·예산·시험 계획 본문, 장별 슬라이드 요청에 사용한다. RFP 분석·KPI 조사·최종 문서 병합은 해당 전문 스킬과 연결한다. | 13 |
| [defense-diagram](../skills/proposal_pipeline/defense-diagram/SKILL.md) | 방산 연구 제안서용 개념도·블록다이어그램·시스템 구성도·연구개발 개념도를 일관된 디자인으로 생성한다. MANDATORY TRIGGERS: "개념도 그려줘", "블락다이어그램", "시스템 구성도", "R&D 개념도", "다이어그램 만들어줘", "그림 만들어줘", "diagram", "block diagram", "concept figure", "연구개발 개념도", "기술 구조도", 제안서 그림이 언급될 때마다 이 스킬을 사용할 것. 사용자 서식이 없으면 번들 design-system.md를 재사용 기본 프리셋으로 적용한다. | 1 |
| [defense-wbs-tbs](../skills/proposal_pipeline/defense-wbs-tbs/SKILL.md) | 방산 연구 제안서용 WBS(작업분류체계), TBS(기술분류체계), 추진 일정(간트차트), 마일스톤 표를 생성하고 PPTX 슬라이드 및 xlsx로 만든다. MANDATORY TRIGGERS: "WBS 만들어줘", "TBS 만들어줘", "간트차트", "추진 일정", "마일스톤", "작업분류체계", "기술분류체계", "일정 계획 표", "연구 일정", "WBS 다이어그램". 방산 제안서에서 WBS, TBS, 간트차트, 일정 표가 언급되면 이 스킬을 사용할 것. 경계: 이 스킬은 WBS/TBS/일정의 "다이어그램·간트·xlsx 시각화" 전담. 3장 본문의 WBS/TBS 표 서술은 defense-proposal-writer(section=tech-analysis), 4장 일정 서술·성과평가는 defense-proposal-writer(section=research-plan) 소관 — 시각화 요청이면 이 스킬을 사용. | 0 |
| [defense-execution-manual](../skills/proposal_pipeline/defense-execution-manual/SKILL.md) | 방산 연구 제안서 스킬 수트의 실행 매뉴얼을 자동 생성하는 스킬. 연구 주제(과제명)를 입력하면 제안서 공통 스킬과 defense-proposal-writer의 5개 section을 어떤 순서로, 어떤 입력값으로 실행해야 하는지 단계별 실행 매뉴얼 Word 문서(.docx)를 생성한다. MANDATORY TRIGGERS: "실행 매뉴얼 만들어줘", "매뉴얼 작성", "스킬 사용 방법", "어떻게 쓰면 돼", "how to use skills", "execution manual", "스킬 실행 순서", "제안서 작성 가이드", "주제 넣고 매뉴얼". 연구 주제를 주고 제안서 작성 절차를 안내받고 싶을 때 반드시 이 스킬을 사용할 것. | 2 |
| [defense-proposal-assembler](../skills/proposal_pipeline/defense-proposal-assembler/SKILL.md) | 방산 제안서 파이프라인의 마지막 단계. 장별 산출물(1~5장 pptx, figures, WBS/TBS)을 최종 통합 제안서 1건으로 병합하고, 병합 전 장 간 수치 일관성(KPI·TRL·예산·일정)을 교차 검사하여 불일치 리포트를 생성한다. MANDATORY TRIGGERS: "제안서 합쳐줘", "최종 제안서 만들어줘", "제안서 통합", "장별 슬라이드 병합", "제안서 마무리", "assemble proposal", "최종본 만들어줘", "제안서 패키징". 섹션 스킬들이 각 장을 생성한 뒤 최종본이 언급되면 반드시 이 스킬을 사용할 것. | 0 |

## Office·한글 문서 작업

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [doc-writer](../skills/office_document_pipeline/doc-writer/SKILL.md) | Office·한글 문서의 판독, 기존 서식 채우기·수정, 내용 명세에서 기술문서 작성을 처리한다. .docx·.xlsx·.pptx·.hwp·.hwpx 및 앱 COM이 필요한 문서에 사용한다. | 69 |
| [office-drm-bridge](../skills/office_document_pipeline/office-drm-bridge/SKILL.md) | Windows의 Office·한글 COM을 다른 세션에서 호출하는 파일 요청 브리지. doc-writer의 Office/HWP backend로 판독·필드 채우기·치환·문서 끼워 넣기·그림 작업을 수행한다. 평문은 평문으로 처리할 수 있고 보호 원본은 보호를 유지한다. Windows 워커가 필요한 문서 작업에 사용한다. | 9 |

## 도메인별 감사

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [gpu-hpc-guard](../skills/domain_audits/gpu-hpc-guard/SKILL.md) | Audits GPU/HPC memory footprint, complexity hotspots, and proposes chunking/streaming strategies for any compute-intensive workload. | 3 |
| [sim-physics-auditor](../skills/domain_audits/sim-physics-auditor/SKILL.md) | Audits physics and simulation consistency: units, dimensions, coordinate frames, numerical stability, and domain-specific invariants. | 3 |
| [rag-data-quality](../skills/domain_audits/rag-data-quality/SKILL.md) | Assesses RAG corpus quality: chunking, metadata, deduplication, coverage, and recall/rerank evaluation for any domain. | 3 |

## 에이전트 오케스트레이션

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [agent-orchestration](../skills/agent_orchestration/agent-orchestration/SKILL.md) | 요청을 완료 기준·의존성·수정 범위가 있는 태스크로 나누고 메인·서브에이전트의 역할과 핸드오프를 설계한다. 복잡한 작업 분해, 병렬 작업 계획, 에이전트 역할 분담에 사용한다. | 6 |
| [agent-executor](../skills/agent_orchestration/agent-executor/SKILL.md) | 태스크 계획이나 대화의 작업 계약에 따라 서브에이전트를 실행하고 의존성·공유 파일·결과 검증을 조정한다. 계획 실행, 병렬 작업 진행, 특정 작업자 재실행과 결과 통합 요청에 사용한다. | 3 |

## HTML 산출물 생성

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [dashboard-designer](../skills/artifact_workflows/dashboard-designer/SKILL.md) | Turns a vague "I want a web dashboard" request into a concrete GUI specification and a working HTML scaffold. Runs a structured 6-axis interview (purpose/data, layout archetype, interaction model, visualization widgets, tech stack, style), writes a machine-readable dashboard_spec.md, picks the right archetype template, and emits a runnable starter. Use this whenever the user mentions building a web dashboard, a training-metrics viewer, a TensorBoard embed, a simulation log playback UI, a model/object inspector, a monitoring panel, or says things like "대시보드 만들어줘", "web 기반 대시보드", "로그 뷰어", "시뮬레이션 플레이백 UI", "학습 지표 보는 화면", "객체 클릭하면 정보 뜨는 패널", "TensorBoard 임베딩", "dashboard spec 만들어줘", "GUI 형식화", even when they don't explicitly use the word "dashboard". Also use before running repo-doc-writer or uf-designer when the frontend/GUI design isn't fixed yet. | 6 |
| [travel-planner-html](../skills/artifact_workflows/travel-planner-html/SKILL.md) | 여행 계획을 공유 가능한 단일 HTML 파일(탭형 일정 타임라인 + Leaflet.js 지도 + 체크리스트)로 생성한다. Trigger: "여행 계획 HTML로 만들어줘", "공유용 여행 계획 파일", "여행 일정 시각화", "지도 포함 여행 플래너", 여행 계획 대화 후 "이거 HTML로 뽑아줘". | 6 |

## 범용 프로젝트 기록

| 스킬 | 용도 | 리소스 파일 수 |
|---|---|---:|
| [project-summarizer](../skills/general/project-summarizer/SKILL.md) | 프로젝트의 실제 진행 이력·설계 결정·문제와 해결·교훈·다음 단계를 요약 문서로 만들거나 기존 요약에 병합한다. 프로젝트 요약, 회고, 인수인계, 지금까지 한 일 정리, summary 갱신 요청에 사용한다. 구현 태스크나 기술문서 본문 작성과 구별한다. | 1 |
