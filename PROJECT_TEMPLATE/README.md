# PROJECT_TEMPLATE — 신규 프로젝트 시작 팩

새 프로젝트가 **Day 1부터** 근거 사슬(요청 → 분석 → 결정/발견 → 변경 → 검증)을 갖고 시작하게 하는 템플릿.
기존 프로젝트에서 검증 실패의 원인이 "기록 부족"이 아니라 **ID 연결·상태 의미론·기계 게이트의 부재**였다는 감사 결과에서 나왔다 — 이 팩은 그 세 가지를 시작 시점에 설치한다.

## 구성

```
GLOBAL_RULES.md                     ← 범용 지침 (프로젝트 사실 0건 — 그대로 복사)
PROJECT_RULES.template.md           ← 프로젝트 바인딩 골격 (채워서 PROJECT_RULES.md로 저장)
graph/edges.csv                     ← 발견(F-)·결정(D-)·매핑(M-) 대장 (헤더만)
graph/checks_config.template.json   ← 기계 검사 정의 골격 (채워서 checks_config.json으로)
tools/graph_checks.py               ← 범용 검사 엔진 (수정 불필요 — 설정만 소비)
0.FilesUpdate.xlsx                  ← 파일 로그 (v2 스키마: +요청 ID·근거 ID·검증·커밋 ID)
1.PromptsUpdate.xlsx                ← 프롬프트 로그 (v2 스키마: +요청 ID·산출물 경로)
review_docs/  rd/  logs/            ← 빈 표준 디렉터리
```

## 시작 절차 (10분)

1. 이 폴더 내용물을 새 프로젝트 루트에 복사한다.
2. `PROJECT_RULES.template.md` → `PROJECT_RULES.md`로 채운다. **원년 = 프로젝트 시작일** — 소급 문제가 원천적으로 없다.
3. `graph/checks_config.template.json` → `checks_config.json`으로 채운다 (처음엔 검사 1~2개면 충분 — dangling 상수 검사부터).
4. `git init` (버전 관리 없이 시작하지 않는다 — 델타 감사·blame·커밋 ID 컬럼이 전부 여기 걸린다).
5. `python tools/graph_checks.py` 실행 → EXIT=0 확인.
6. 첫 사용자 요청부터 P-001 발급, 워크플로 v2(GLOBAL_RULES 하단)를 따른다.

## 운영 원칙 요약 (상세는 GLOBAL_RULES)

- **수정 = 되돌리면 실패하는 테스트 동반** (Rule 12). 아니면 fixed가 아니다.
- **수치는 복사하지 말고 evidence 경로를 인용** (Rule 13). 시험 실행은 evidence 파일을 생성한다.
- **결정 번복은 supersedes 기록** (Rule 11). 구 문서를 고치는 게 아니라 대장에 대체 관계를 남긴다.
- **대규모 변경은 당일 델타 검토, 마일스톤엔 무맥락 감사** (Rule 15). 건강 지표는 발견 수가 아니라 재발률 ≈ 0.
- **게이트 위반은 수정하거나 대장에 open 등록 후에만 "완료"** (Rule 14).

## ctest 연동 (선택)

CMake 프로젝트라면:

```cmake
find_package(Python3 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND)
  add_test(NAME graph_checks
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/graph_checks.py)
endif()
```
