# Office·한글 문서 작업

입력·서식 확인 → doc-writer의 Office·한글 모드로 판독/편집/작성 → 저장 후 내용·보호 상태 검증. Windows 앱이 없는 환경에서만 office-drm-bridge를 통해 워커를 호출한다.

| 스킬 | 정본 |
|---|---|
| doc-writer | [doc-writer/SKILL.md](doc-writer/SKILL.md) |
| office-drm-bridge | [office-drm-bridge/SKILL.md](office-drm-bridge/SKILL.md) |

doc-writer 하나가 공통 진입점이며 앱별 백엔드는 하위 모듈로 유지한다. templates/technical-report/에 프로젝트 정보가 없는 HWPX 패키지·XML·스타일 프로파일·표 서식을 포함한다. 설치 시 실행 도구는 tools/, 서식은 document_templates/로 배포한다. 실제 한글 앱 열림·조판은 사용 환경에서 검증한다.

[전체 스킬 목록](../../docs/skill-catalog.md) · [파이프라인 설치 정의](../pipelines.json)
