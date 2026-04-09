# IF Integrator 스킬

## 개요

`if-integrator`는 구현된 단위기능(UF) 코드들을 통합기능(IF) 수준의 모듈로 **조립하는 스킬**입니다. UF 함수들의 호출 순서를 오케스트레이션하고, IF 수준의 공개 API 진입점을 생성하며, IF 인수 조건(acceptance criteria)에 기반한 통합 테스트를 자동 생성합니다.

`uf-implementor`가 UF 구현을 완료한 뒤, 시스템 수준 검증 단계의 입구 역할을 합니다.

---

## 언제 사용하나요?

- `uf-implementor`로 `src/uf/` 파일들이 완성되고 상태가 `IMPLEMENTED`일 때
- 여러 UF를 하나의 IF 수준 API로 묶어야 할 때
- `if_list.md`의 인수 조건을 통합 테스트로 자동 변환하고 싶을 때

---

## 입력 파일

| 파일 | 필수 여부 | 설명 |
|---|:---:|---|
| `if_list.md` | ✅ 필수 | IF Block 정의 목록 |
| `if_decomposition.md` | ✅ 필수 | IF별 UF 호출 그래프 |
| `src/uf/<module>.py` | ✅ 필수 | 구현된 UF 파일들 |
| `uf_if_coverage_review.md` | 권장 | 커버리지 검증 참조용 |
| `reports/impl/uf_impl_report_*.md` | 선택 | STUB/BLOCKED UF 스킵 판단용 |

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `src/if/<module>.py` | IF 통합 모듈 (IF별 1파일) |
| `tests/integration/test_<module>.py` | 통합 테스트 파일 |
| `reports/impl/if_integration_report_<timestamp>.md` | 통합 상태 리포트 |

---

## 사용법 (slash 명령어)

### Case 1 — 모든 IF 통합

```
/if-integrator Read if_list.md and if_decomposition.md.
Generate integration modules for all IFs using src/uf/ implementations.
Output to src/if/ and tests/integration/.
```

### Case 2 — 특정 IF만 통합

```
/if-integrator Integrate IF-02 only.
Read if_list.md, if_decomposition.md, and src/uf/analysis.py.
Output to src/if/analysis_if.py.
```

### Case 3 — 구현 완료된 IF만 선택하여 통합

```
/if-integrator Read if_list.md, if_decomposition.md, and uf_impl_report_*.md.
Generate integration modules only for IFs where all UFs are IMPLEMENTED.
Report IFs with STUB or BLOCKED UFs as action items.
```

---

## 실행 흐름

```
if_list.md + if_decomposition.md 파싱
  ↓
UF 호출 그래프 재구성 (실행 순서, 데이터 흐름)
  ↓
함수 시그니처 검증 (UF 출력 ↔ 다음 UF 입력 타입/shape 일치 여부)
  ↓
IF 통합 모듈 생성 (src/if/<module>.py)
  - UF 호출 오케스트레이션 (순차/병렬/조건 분기)
  - IF 수준 공개 API 진입점 (if_<id>_<name>())
  - 사후조건 검사 (IF 인수 조건 위반 시 IntegrationError)
  ↓
통합 테스트 생성 (tests/integration/test_<module>.py)
  - Given/When/Then → pytest 함수
  - 경계값 테스트 (최소/최대 입력)
  - 회귀 테스트
  ↓
if_integration_report_<timestamp>.md 출력
```

---

## UF 호출 오케스트레이션 패턴

| 패턴 | 사용 시나리오 |
|---|---|
| 순차 (Sequential) | 각 UF 출력이 다음 UF 입력으로 직렬 연결 |
| 병렬 (Parallel) | 독립적인 UF 브랜치 → 결과 병합 |
| 조건 분기 (Conditional) | 입력 조건에 따라 서로 다른 UF 경로 선택 |
| 반복/피드백 (Iterative) | 수렴 조건까지 반복 실행 |

---

## 통합 상태 코드

| 코드 | 의미 |
|---|---|
| `COMPLETE` | 모든 UF 통합 완료, IF 인수 조건 통과 |
| `PARTIAL` | 통합 모듈 생성 완료; 일부 테스트 실패 또는 UF STUB |
| `INTERFACE_ERROR` | UF 시그니처와 IF I/O Contract 불일치 |
| `BLOCKED` | 필수 UF가 STUB/BLOCKED → 런타임에 NotImplementedError 발생 |

---

## 설계 프로세스 내 위치

```
Stage 5  통합기능(IF) 도출 → if_list.md
Stage 6  IF Decomposition → if_decomposition.md
Stage 7  단위기능(UF) 도출 → uf.md
Stage 7.5 UF→IF 커버리지 리뷰 → uf_if_coverage_review.md
  ↓
[uf-implementor]  UF 구현 → src/uf/, tests/unit/
  ↓
[if-integrator]   IF 통합 → src/if/, tests/integration/
  ↓
Stage 8  검증·증거 계획 / CI 파이프라인 연결
```

---

## 관련 스킬

| 스킬 | 관계 |
|---|---|
| `core-engineering` | Stage 5/6 IF 설계 기반 |
| `uf-implementor` | 선행 스킬; UF 구현 코드 제공 |
| `uf-chain-validator` | UF 체인 유효성 검증 (구현 전/후 모두 사용 가능) |
| `ci-evidence-automation` | 통합 테스트를 CI 파이프라인에 연결 |
| `eval-runner` | IF 수준 메트릭 계산 및 비교 리포트 생성 |
