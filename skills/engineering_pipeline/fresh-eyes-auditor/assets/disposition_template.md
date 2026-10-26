# Delta round [n] 처분표 — [변경 한 줄] ([요청 ID])

- 일시: YYYY-MM-DD HH:MM / 회차: [n] / 검토: [관점별 n기 | 고침 확인(비독립)]
- 보고 파일: [round<n>_<관점>.md 경로 목록]
- 앞 회차 처분표: [경로 | 없음] — D5 재발 대조를 마친 뒤 이 회차를 띄웠는가: [예 | 첫 회차]

| ID | 심각도 | 요지 | 처분 | 근거(수치·인용) | 시험·변이 | 대장 | 재발 |
|---|---|---|---|---|---|---|---|
| D1-①-01 | HIGH | [한 줄] | FIXED | [고친 곳 file:line] | [시험 이름 / 변이 ID] | F-xxx | NEW |
| D1-①-N01 | 메모 | [한 줄] | ACCEPTED-AS-DESIGN | 대표 데이터 [경로] 결과: [수치] | — | D-xxx | — |
| D1-②-02 | MEDIUM | [한 줄] | DEFERRED | [사유 · 해제 조건] | — | F-xxx(deferred) | NEW |
| D2-①-01 | MEDIUM | [한 줄] | FIXED | … | … | F-xxx | RECURRING(D1-①-N01) |

- 처분: FIXED · DEFERRED(사유·해제 조건) · ACCEPTED-AS-DESIGN(실제 데이터 근거 필수) ·
  REJECTED-MISQUOTE / REJECTED-JUSTIFIED / REJECTED-TRIVIAL (기각 근거는 `reference/triage_protocol.md`)
- 재발: NEW · RECURRING(앞 회차 ID) — RECURRING 은 대장 notes 에도 앞 회차 ID 를 적는다.
- 빈칸 없이: 처분 근거가 비어 있는 줄이 있으면 다음 회차를 띄우지 않는다.

## 판단 근거
- [채택·기각·보류의 핵심 근거 요약]
