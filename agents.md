# agents.md — 작업 라우팅

이 저장소는 재사용 스킬·프로젝트 템플릿의 정본이다. 경로와 설치 구성은 [skills/pipelines.json](skills/pipelines.json)을 따른다. templates/project/GLOBAL_RULES.md는 검토·배포 대상인 프로젝트 템플릿이며 이 저장소에 자동 적용되는 추가 승인 절차가 아니다.

## 메인의 책임

- 현재 요청·기존 승인·완료 기준을 확인하고 필요한 태스크만 만든다.
- 작은 수정과 긴밀히 연결된 작업은 직접 수행한다. 독립 구현·조사·검토에 이점이 있으면 서브에이전트를 쓴다.
- 각 위임에는 목표·입력·기준점·출력/반환·의존성·쓰기 범위·완료 검사를 전달한다.
- 같은 파일은 단일 writer가 소유한다. 다른 worker는 고유 조각·findings를 반환한다. 공용 정본·로그·대장은 메인 또는 지정된 한 명이 갱신한다.
- 준비된 태스크만 현재 런타임 용량 안에서 실행한다. 고정 3명이나 역할별 최대값을 채우지 않으며, 메인 포함 전체 한도를 넘지 않는다.
- 위임 후 미위임 critical path 작업·통합 준비를 계속한다. 기존 승인·제약은 승계하고 추가 권한·필수 정보만 사용자에게 묻는다.
- 반환된 실제 변경·증거·수락 기준을 확인하고 필요한 통합 검사를 수행한다. 필수 기준 실패는 의존 작업만 보류하며 독립 작업은 계속한다.

## 필요한 지침만 읽기

- 태스크와 역할 설계: [agent-orchestration](skills/agent_orchestration/agent-orchestration/SKILL.md)
- 실행·결과 통합: [agent-executor](skills/agent_orchestration/agent-executor/SKILL.md)
- 전체 REQ→IF→UF 설계 파이프라인을 선택한 경우만 [engineering manifest](skills/agent_orchestration/agent-orchestration/references/engineering-manifest.md) 추가 로드.
- 수정·정리·문서화 요청을 자동으로 전체 엔지니어링 파이프라인으로 확대하지 않는다. 기존 완료 산출물과 확인된 답변은 재사용한다.
- 긴 재개 작업에는 작은 태스크/핸드오프 기록을 남긴다. 짧은 작업에 역할 파일·추적 대장을 일괄 생성하지 않는다.

## 저장소 작업

스킬의 상세 참조·템플릿·백엔드는 해당 정본 폴더에 둔다. 등록 이름·설치 리소스가 바뀌면 관련 catalog와 installer 계약을 함께 갱신한다. 원본 비교 프로젝트와 사용자 수정은 보존한다. 현재 작업 범위에 맞는 검사 후 결과·검증·남은 한계를 보고한다.
