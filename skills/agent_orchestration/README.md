# 에이전트 오케스트레이션

작은 요청은 메인이 직접 수행한다. 독립적으로 처리할 이점이 있을 때 agent-orchestration으로 태스크·입출력·의존성·소유권을 정하고 agent-executor로 실행·통합한다. 고정 인원수와 계획 파일 생성은 시작 조건이 아니다.

| 스킬 | 정본 |
|---|---|
| agent-orchestration | [설계](agent-orchestration/SKILL.md) |
| agent-executor | [실행·통합](agent-executor/SKILL.md) |

전체 설계 파이프라인에만 [engineering manifest](agent-orchestration/references/engineering-manifest.md)를 사용한다. 메인은 공유 정본과 최종 검증을 책임진다.

[context-engineering](../engineering_pipeline/context-engineering/SKILL.md) · [project-summarizer](../general/project-summarizer/SKILL.md) · [설치 정의](../pipelines.json)
