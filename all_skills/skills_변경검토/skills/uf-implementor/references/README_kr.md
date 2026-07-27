# UF Implementor 스킬

## 개요

`uf-implementor`는 UF Block 정의(`uf.md`)를 입력으로 받아, 각 단위기능(UF)을 **실제 실행 가능한 코드**로 구현하는 스킬입니다. 구현 코드, 유닛 테스트, 구현 상태 리포트를 자동 생성합니다.

설계 프로세스의 Stage 7.5 (UF→IF Coverage Review) 승인 후, 코딩 단계의 첫 번째 진입점입니다.

---

## 언제 사용하나요?

- `uf.md`가 완성되고 Stage 7.5 커버리지 리뷰에서 `UNCOVERED` 항목이 없을 때
- UF Block의 I/O Contract와 알고리즘 요약을 실제 함수 코드로 변환하고 싶을 때
- 인수 조건(Given/When/Then)에서 pytest 테스트를 자동 생성하고 싶을 때

---

## 입력 파일

| 파일 | 필수 여부 | 설명 |
|---|:---:|---|
| `uf.md` | ✅ 필수 | UF Block 정의 목록 |
| `uf_if_coverage_review.md` | 권장 | REDUNDANT UF 스킵 판단에 사용 |
| `requirements.md` | 선택 | 비기능 요구사항 확인용 |

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `src/uf/<module>.py` | UF 구현 코드 (IF 그룹 단위로 모듈화) |
| `tests/unit/test_<module>.py` | 유닛 테스트 파일 |
| `reports/impl/uf_impl_report_<timestamp>.md` | 구현 상태 리포트 |

---

## 사용법 (slash 명령어)

### Case 1 — 모든 UF 구현

```
/uf-implementor Read uf.md and implement all UF blocks.
Output to src/uf/ and tests/unit/.
```

### Case 2 — 특정 UF만 구현

```
/uf-implementor Implement UF-03 from uf.md using PyTorch.
Output to src/uf/processing.py.
```

### Case 3 — Coverage Review 결과 반영하여 구현

```
/uf-implementor Read uf.md and uf_if_coverage_review.md.
Skip REDUNDANT UFs. Generate implementations for all remaining UFs.
```

---

## 실행 흐름

```
uf.md 파싱
  ↓
각 UF별 구현 코드 생성
  - 함수 시그니처 (I/O Contract 반영)
  - 핵심 알고리즘 구현
  - 입력 유효성 검사 (타입, shape, 범위)
  - 엣지 케이스 처리
  ↓
각 UF별 유닛 테스트 생성
  - Happy-path 테스트
  - 엣지 케이스 테스트
  - 인수 조건 테스트 (Given/When/Then → pytest)
  ↓
I/O 체인 정합성 검증
  - UF-N 출력 타입/shape ↔ UF-M 입력 타입/shape
  ↓
uf_impl_report_<timestamp>.md 출력
```

---

## 구현 상태 코드

| 코드 | 의미 |
|---|---|
| `IMPLEMENTED` | 완전 구현 완료, 엣지 케이스 포함 |
| `STUB` | 시그니처·docstring 작성, 알고리즘 미완성 |
| `BLOCKED` | 추가 명확화 필요 (인라인 주석으로 표기) |
| `SKIPPED` | Coverage Review에서 REDUNDANT 판정 |

---

## 설계 프로세스 내 위치

```
Stage 7   단위기능(UF) 도출 → uf.md
  ↓
Stage 7.5  UF→IF 커버리지 리뷰 → uf_if_coverage_review.md
  ↓
[uf-implementor]  UF 구현 → src/uf/, tests/unit/
  ↓
[if-integrator]   IF 통합 구현 → src/if/, tests/integration/
```

---

## 관련 스킬

| 스킬 | 관계 |
|---|---|
| `core-engineering` | Stage 7/7.5 설계 프로세스 기반 |
| `uf-chain-validator` | UF 체인 유효성 검증 (구현 전 사용 가능) |
| `if-integrator` | UF 구현 완료 후, IF 수준 통합 구현 |
| `ci-evidence-automation` | 유닛 테스트를 CI 파이프라인에 연결 |
