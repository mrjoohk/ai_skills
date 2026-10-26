# fresh-eyes-auditor (v3)

무맥락(fresh-context) 서브에이전트로 설계·구현 산출물을 독립 감사하는 스킬.
세션 에이전트의 확증 편향을 구조적으로 우회한다: 감사자는 대화를 모르고 파일만 본다,
본 에이전트는 감사자의 발견을 인용 대조로만 채택한다.

## 언제 쓰나

- "지금까지 만든 것에 모호함·억지·오류·환각 없는지 봐줘"
- 마일스톤 직전 독립 검증 / 대규모 리팩터 후 델타 검토(Delta 모드 — 관점 셋 동시, 회차마다 처분표)
- 문서-코드 정합이 의심될 때

기계적 계약 검증(uf-chain-validator)·코드 품질 리뷰(code-reviewer)와 역할이 다르다 —
이 스킬은 **인식론적 결함**(근거 없는 주장, 존재하지 않는 인용, 문서 간 모순)을 잡는다.

## 구조

```
SKILL.md                              핵심 절차 (5단계 + Delta 모드 D0~D6 + 규칙 12)
reference/
  spawn_prompt_template.md            무맥락 감사자 스폰 프롬프트 (루브릭·심각도표·출력형식) — 그대로 사용
  delta_prompt_template.md            같은 날 변경 검토(Delta) 스폰 프롬프트 + 고침 확인(비독립) 꼴
  delta_lenses.md                     Delta 관점 부록 셋 (① 알고리즘·수치 성질 ② 호스트 API·데이터 흐름 ③ 시험·음성 대조)
  triage_protocol.md                  트리아지 세부: U-게이트·기각 분류·재발 대조 프로토콜과 그 근거
  ledger_schema.md                    발견·결정 대장(graph/edges.csv) 스키마와 상태 의미론
scripts/
  graph_checks.py                     범용 무결성 검사 엔진 (Step 0.5용, 프로젝트에 없을 때 복사)
assets/
  report_template.md                  감사 리포트 골격 (필수 섹션 포함)
  disposition_template.md             Delta 회차 처분표 (지적·설계 메모 전부, 처분·근거·재발)
  checks_config.template.json         기계 검사 설정 골격
  edges_header.csv                    대장 헤더
examples/
  example_audit_report.md             작성된 리포트 예 (가상 프로젝트)
  example_ledger_rows.csv             대장 행 예
```

## 설치

- `.skill` 파일을 Claude에서 열어 Save skill — 디렉터리 구조째 설치된다.
- 수동: 이 디렉터리를 스킬 폴더에 그대로 복사.

## v2 변경점 (v1 대비)

- Step 0.5 기계 검사 선행 — 기계가 잡는 클래스를 스크립트 전담으로 분리
- 심각도 기준표를 스폰 프롬프트에 내장 — 회차 간 드리프트 차단
- 트리아지 ⓪ U-의존 게이트 — 열람 불가 원본에 걸린 발견은 심각도 불문 채택 금지
- 재발 대조(RECURRING/NEW/RESOLVED)와 대장 갱신을 감사의 완결 조건으로 승격

## v3 변경점 (v2 대비, drmHWP P-043)

- Delta 모드(같은 날 변경 검토): 관점 셋을 한 메시지에서 동시에 스폰, 검토자 예산·탐침 폴더, 보고는 끝내기 전 파일로
- 회차마다 처분표 — '결함 아님' 설계 메모까지 처분, ACCEPTED-AS-DESIGN 은 실제 데이터 근거, 다음 회차 전 재발 대조
- 고침 확인 모드를 비독립으로 분리(새 검토자, 지적 목록 + 고친 diff 만)
- 근거: P-041 시간 검토(`review_docs/261013_1425_P041_duration_parallel_review.md`) — 검토 대기 76분·설계 메모 처분 빈틈으로 한 바퀴 더
