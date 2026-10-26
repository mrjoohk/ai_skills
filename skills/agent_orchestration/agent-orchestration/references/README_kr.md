# 오케스트레이션 사용 안내

요청은 메인이 해석하고, 독립적으로 완료할 가치가 있는 일만 서브에이전트에 나눈다. 고정 3명이나 역할 파일 생성은 시작 조건이 아니다.

- [사용 지침](../SKILL.md)
- [계약과 역할 선택](reference.md)
- [배분 예시](examples.md)
- [역할 템플릿](../assets/agent-role-template.md)
- [계획 템플릿](../assets/orchestration-plan-template.md)

전체 REQ→IF→UF 파이프라인을 선택했을 때만 [상세 manifest](engineering-manifest.md)를 읽는다. 실제 실행은 agent-executor 또는 현재 환경의 같은 기능을 사용한다.
