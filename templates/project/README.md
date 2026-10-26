# 프로젝트 시작 팩

기본은 가벼운 작업 흐름이다. 사용자 요청을 완료하는 데 필요한 지침만 읽고, 추적·감사 체계는 해당 프로젝트에서 필요할 때 선택한다.

## 시작

1. 새 프로젝트에는 AGENTS.md, GLOBAL_RULES.md와 링크 대상인 policies/TRACEABILITY.md를 함께 복사한다. 정책 파일은 tracked가 필요할 때만 읽는다. 기존 프로젝트에는 필요한 지침을 기존 파일에 병합하며 덮어쓰지 않는다.
2. 프로젝트 사실을 지속적으로 공유할 필요가 있으면 PROJECT_RULES.template.md를 채워 PROJECT_RULES.md로 저장한다. 모든 항목을 채우기 위한 질문부터 시작하지 않는다.
3. 작은 작업은 메인이 직접 수행한다. 독립 태스크가 유용하면 서브에이전트를 사용하고, 메인이 공유 파일·통합·검증을 책임진다.
4. 버전 관리·검사 명령은 프로젝트 환경에 맞게 사용한다. 작업을 시작하기 위해 자동으로 git init이나 새 채팅을 만들지 않는다.

## 선택형 추적 모드

감사 근거·요청 이력이 필요한 프로젝트는 workflow_mode: tracked 또는 기존 필수 규약을 사용한다. 이때만 [TRACEABILITY.md](policies/TRACEABILITY.md)를 읽고 아래 도구를 설치한다.

| 자료 | 용도 |
|---|---|
| graph/edges.csv | 발견·결정·매핑의 빈 대장 |
| graph/checks_config.template.json | 실제 프로젝트에 맞춰 채울 검사 예제 |
| tools/graph_checks.py | 설정된 무결성 검사 |
| logs/files.jsonl, logs/prompts.jsonl | 기존 v2 호환 append-only 로그 |
| tools/worklog/ | 로그 스키마·검증기 |

검사 설정은 실제 경로로 채우거나 사용하지 않는 검사를 제거한 뒤 graph/checks_config.json으로 저장한다. 로그는 메인이 작업 단위로 모아 기록하고 마감 시 한 번 검증한다. known_open 등록은 결함 해결이나 전체 품질 통과를 뜻하지 않는다.

기존 빈 디렉터리·로그는 선택형 시작 자원으로 유지한다. 모든 프로젝트가 이를 복사하거나 사용해야 하는 것은 아니다. rd/, reports/, review_docs/, output_docs/는 새 문서를 만들 때의 관례이며 사용자 지정·기존 정본을 옮기는 근거가 아니다.
