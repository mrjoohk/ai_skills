# Fresh-Eyes Audit — 예시 (가상 프로젝트 acme_ctrl)

- 일시: 2026-01-15 14:00 / 모드: A / 성격: 자문
- 감사자: 무맥락 서브에이전트 2기

## 0. 기계 검사 선행 결과
- graph_checks: 위반 2건 (KNOWN-OPEN 2 / NEW 0) — kMaxRate 미사용(F-007), "5개 채널" 주장 불일치(F-009)
- evidence: logs/graph_checks_last.json

## 1. 범위
| 에이전트 | 담당 | 파일 수 |
|---|---|---|
| A1 | 설계 문서 교차 | 6 |
| A2 | src/ + tests/ | 14 |
- 커버리지 결손: 없음

## 2. 이전 감사/대장 대조표
| 구분 | 건수 | 목록 |
|---|---|---|
| RECURRING | 1 | F-004 (재보고 — open 유지 중) |
| NEW | 2 | F-012, F-013 |
| RESOLVED | 1 | F-002 (수정 확인, fixed→verified 제안) |
- 재발률: 1/3

## 4. ACCEPTED
- F-012 / 오류 / WARN / NEW
  위치: src/rate_limiter.cpp:88 / 인용: "window_ms = 100; // 10 Hz"
  설명: 주석은 10 Hz라 하나 100 ms 창은 설정 kControlHz(50)와 무관하게 고정. 설계 §3은 "제어 주기의 5배"로 규정.
  제안: 창을 주기 파생값으로. / 채택 근거: 인용 실재 + 파일 내 해명 없음 / 라우팅: uf-implementor
- F-013 / 환각 / CRITICAL / NEW
  위치: rd/design.md:41 / 인용: "RFC 9999에 따라 재전송은 3회로 한다"
  설명: RFC 9999는 존재하지 않음(웹 대조). 재전송 3회의 실근거 부재.
  제안: 실출처 기재 또는 자체 결정으로 재분류. / 라우팅: req-elicitor

## 5. REJECTED
- (A2 보고) "mutex 없이 큐 접근" → REJECTED-JUSTIFIED: queue.hpp:12 주석 "single-consumer,
  producer는 시작 전 1회만 접근" 해명 실재.

## 6. UNVERIFIABLE
| ID | 필요한 정보 | 걸려 있는 발견 |
| U-01 | 협력사 ICD v2.3 원본 | (U-게이트 이동) A2의 "채널 수 8 초과" 지적 — 원본 없이는 판정 불가 |

## 8. 대장 갱신 내역
- 신규: F-012(open), F-013(open) / 전이: F-002 fixed→verified

## 판단 근거
- F-013을 CRITICAL로 판정: 심각도표의 "존재하지 않는 근거의 인용" 항목 해당.
- U-01은 심각도 미부여 — U-의존 게이트 원칙.
