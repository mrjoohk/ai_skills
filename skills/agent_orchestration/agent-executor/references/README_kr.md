# 에이전트 실행 사용 안내

[agent-executor](../SKILL.md)는 현재 메인이 태스크 계약을 실행·수집·통합하는 절차다. 특정 제품의 Agent 도구나 사전 역할 파일을 필수로 가정하지 않는다.

- [실행 계약·상태·복구](reference.md)
- [배분과 실행 예시](examples.md)
- 계획이 필요하면 [agent-orchestration](../../agent-orchestration/SKILL.md)

필수 기준 미달은 의존 태스크를 막는다. 메인은 중간 조정과 최종 검증 책임을 유지하며, 공유 파일·로그·대장은 단일 writer가 갱신한다.
