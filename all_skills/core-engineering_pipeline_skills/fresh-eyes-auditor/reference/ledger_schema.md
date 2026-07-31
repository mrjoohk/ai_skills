# 발견·결정 대장 스키마 (graph/edges.csv)

한 프로젝트의 발견(F-)·결정(D-)·매핑(M-)의 **상태 단일 정본**. 감사·수정·번복이 전부 이 파일의
상태 전이로 기록된다. 리포트는 서사, 대장은 상태 — 서사는 낡아도 되지만 상태는 낡으면 안 된다.

## 컬럼

| 컬럼 | 내용 |
|---|---|
| id | F-xxx(발견) / D-xxx(결정) / M-xxx(인터페이스 매핑) |
| type | finding / decision / mapping |
| severity | CRITICAL / WARN / INFO (finding만) |
| title | 한 줄 요약 |
| location | file:line 또는 문서 경로 (복수는 세미콜론) |
| status | 아래 상태 의미론 |
| fix_ref | 수정 커밋/문서 참조 |
| test_ref | 음성 대조 테스트(되돌리면 실패) 또는 "없음" — 없음은 verified 승급 불가 사유 |
| source_doc | 최초 보고 감사 리포트 경로 |
| notes | supersedes 관계, 보류 사유 등 |

## 상태 의미론

| 상태 | 의미 | 전이 조건 |
|---|---|---|
| open | 보고됨, 미처리 | — |
| fixed | 수정 적용됨 | 수정 참조 기록 |
| verified | 음성 대조 테스트 통과 확인 | test_ref 존재 + 통과 — **fixed와 구분하는 것이 핵심** |
| rejected | 트리아지 기각 (오탐) | 기각 분류·근거 기록 |
| deferred | 의도적 보류 | 보류 사유·해제 조건 기록 |
| superseded | 후속 결정으로 대체 | notes에 대체 관계 (구 문서는 고치지 않는다) |

## 운용 규칙

- 감사는 open 전수 재검(RECURRING 태깅)으로 시작하고, 신규 등록·상태 전이로 끝난다.
- 결정 번복은 구 문서 수정이 아니라 **supersedes 기록**이다 — 문서 3곳에 흩어진 "확정"이
  현실과 어긋난 채 잔존하는 사고의 방지책.
- 기계 검사(graph_checks)의 known_open 매핑이 이 대장의 id를 가리킨다 — 등록된 위반은
  게이트를 통과(KNOWN-OPEN)하고, 미등록 위반은 실패(NEW)한다.
