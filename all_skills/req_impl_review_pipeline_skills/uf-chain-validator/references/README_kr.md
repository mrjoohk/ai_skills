# UF Chain Validator - 한국어 가이드

## 스킬 개요

단위 기능(Unit Function, UF) 체인의 무결성과 일관성을 검증하는 스킬입니다. UF-ID 연속성, I/O 컨트랙트 완전성, 테스트 매핑, 증거 팩 참조를 검사하여 설계와 구현의 추적 가능성(Traceability)을 확보합니다. PR 머지 전 CI 게이트로 사용되는 필수 검증 도구입니다.

## 언제 사용하는가

다음과 같은 상황에서 사용합니다:
- **PR 머지 전:** 코드 품질 게이트로 자동 실행
- **Stage 7 완료 후:** UF 도출 후 문서 일관성 검증
- **테스트 커버리지 미달:** 커버리지 71% (<85%) 등 게이트 실패 시
- **UF 모듈 추가/리팩토링:** 새 UF 추가 후 전체 체인 무결성 확인

## 입력

다음 정보를 제공해야 합니다:
- **UF 정의 파일 경로:** `docs/uf/*.md` 또는 `uf_chain.yaml`
- **소스 코드 경로:** `src/` (UF 구현 위치)
- **테스트 경로:** `tests/` (단위/통합 테스트)
- **증거 팩 경로:** `evidence_pack/` (메트릭, 로그, 플롯)

## 출력물

다음 산출물이 생성됩니다:

| 산출물 | 설명 |
|--------|------|
| **검증 리포트** | PASS/WARN/FAIL 요약, 전체 커버리지, 최우선 Fix 항목 |
| **Findings 테이블** | UF-ID, 상태, 문제 유형, 위치(경로::심볼), Fix 제안 |
| **체크 항목 결과** | 7개 체크 항목별 상태 (UF-ID 연속성, I/O 컨트랙트, 테스트 매핑 등) |
| **최소 Fix 제안** | 수정 필요 항목별 패치(diff) |

## 슬래시 명령 예시

### 예시 1: UF 체인 무결성 검증
```
docs/uf/ 에 있는 UF-01..UF-18 을 검증하라.
누락된 I/O 컨트랙트, 테스트 매핑, 증거 팩 참조를 플래그하고
reports/uf_validation.md 를 출력하라.
```

### 예시 2: PR 머지 전 게이트 검사
```
현재 브랜치의 UF 체인을 검증하고,
PR 코멘트에 적합한 간결한 PASS/FAIL 요약을 출력하라.
문서 수정이 필요한 경우 최소 diff를 함께 제공하라.
```

### 예시 3: 커버리지 미달 트리아지
```
CI에서 커버리지 71% (<85%) 가 보고되었다.
어떤 UF 모듈에 테스트가 부족한지 식별하고,
85% 달성을 위한 최소 테스트 세트를 제안하라.
```

### 예시 4: IF → UF 연결 완전성 검사
```
docs/if/ 의 IF-01..IF-08 에 대해 각 IF가 최소 1개 이상의
UF와 연결되어 있는지 확인하라.
연결이 없는 IF를 FAIL로 표시하고 UF 추가를 제안하라.
```

## 다른 스킬과의 연결

**함께 사용하는 스킬 흐름:**

1. **core-engineering** → **uf-chain-validator**
   - Stage 7에서 UF를 도출한 후 체인 검증

2. **uf-chain-validator** → **eval-runner**
   - 테스트 커버리지 개선을 위해 벤치마크 실행

3. **uf-chain-validator** + **uf-if-debug-mapper**
   - UF 무결성 확인 후, 디버그 맵 생성

## 7개 체크 항목

| # | 체크 내용 | PASS 기준 |
|---|---------|---------|
| 1 | **UF-ID 연속성 및 유일성** | 번호 중복·누락 없음 (UF-01, UF-02, ..., UF-XX) |
| 2 | **I/O 컨트랙트 존재** | 타입·단위·shape 모두 명시 (Input/Output Contract 완성) |
| 3 | **테스트 매핑 존재** | 단위/통합 테스트가 UF에 명시적으로 연결됨 |
| 4 | **수락 기준(Assert) 유의미함** | smoke test 이상의 수량적 assertion 포함 |
| 5 | **증거 팩 참조 존재** | 경로와 스키마가 명시됨 (scenario_id, run_id, metrics) |
| 6 | **CI 게이트와 로컬 기대값 일치** | 커버리지 임계값, 성능 목표 일치 |
| 7 | **IF → UF 연결 완전성** | 모든 UF가 parent IF를 명시, 고아 UF 없음 |

## 리포트 헤더 예시

```
- Project:           MyProject
- Commit:            a1b2c3d4
- Date:              2024-03-19
- Validator Version: 1.0
- UF Scope:          UF-01 .. UF-18
- IF Scope:          IF-01 .. IF-08
```

## Findings 테이블 예시

| UF-ID | 상태 | 문제 유형 | 위치 (경로::심볼) | 증거 링크 | Fix 제안 |
|------:|:----:|---------|----------------|---------|--------|
| UF-03 | FAIL | I/O 컨트랙트 누락 | docs/uf/uf03.md | — | 타입·단위·shape 추가 |
| UF-07 | WARN | 단위 테스트 없음 | tests/unit/test_uf07.py | — | pytest 테스트 추가 |
| UF-12 | PASS | 완전 | docs/uf/uf12.md | evidence_pack/uf12/ | — |

## 최소 Fix 가이드

1. **수정 대상 파일:** 경로 + 섹션 제목 명시
   - 예: `docs/uf/uf03.md` → "I/O Contract" 섹션

2. **코드·문서 변경:** 패치(diff) 형식 제공
   ```diff
   - I/O Contract:
   + I/O Contract:
   +   Input: tensor of shape (B, C, H, W), dtype float32
   +   Output: tensor of shape (B, C, H//2, W//2), dtype float32
   ```

3. **커밋 분리:** 리팩토링과 동작 변경은 별도 커밋으로 유지
