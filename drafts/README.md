# 미통합 초안과 실험 코드

이 폴더는 `.claude/skills/`의 사용 스킬과 분리하여 보존한 자료입니다.

| 위치 | 보존한 내용 | 상태 |
|---|---|---|
| [producer-critic/](producer-critic/) | 기존 `improved_skills/`의 code-reviewer, req-critic, uf-chain-validator 및 공통 critic 계약 | 정본과 의미가 다른 초안. 일부 선언된 validator·기계 검증 리소스가 없어 그대로 배포하지 않음 |
| [hwpx-drm/](hwpx-drm/) | 기존 사내문서작업용스킬의 세션 코드, 캡처 실험, 테스트와 fixture | 정본 hwpx-drm과 다른 실험 묶음. 기존 파일 구조를 유지 |

정본은 [스킬 목록](../docs/skill-catalog.md)에서 찾습니다.
초안의 상대 경로와 파일 내용은 보존했으며, 구현·기능 검증을 완료한 상태로 승격하지 않았습니다.
