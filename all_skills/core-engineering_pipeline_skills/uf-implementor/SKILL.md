---
name: uf-implementor
description: "Implements Unit Functions (UFs) as production-ready code from UF Block definitions. Generates implementation stubs, docstrings, unit tests, and verifies against I/O contracts and acceptance criteria. Trigger when the user says 'implement UF', 'write code for unit function', 'generate UF implementation', or 'code up the UF blocks'."
user-invocable: true
allowed-tools: Read, Write
---

# UF Implementor

Takes `uf.md` (UF Block definitions, output of Stage 7) as input and generates **production-ready implementation code** with unit tests for each Unit Function.
This skill bridges the design phase and the coding phase.

---

## When to Use
- After Stage 7.5 (UF→IF Coverage Review) has been approved and `uf_if_coverage_review.md` shows no `UNCOVERED` gaps
- When you want to translate UF Block definitions into actual runnable code
- When you need unit test scaffolding generated from acceptance criteria

---

## Inputs
- `uf.md` — UF Block definitions (required)
- `uf_if_coverage_review.md` — coverage review result (recommended; skip if unavailable)
- `requirements.md` — for cross-referencing non-functional constraints (optional)

---

## Execution Steps

### Step 1 — Load and Parse UF Blocks
- Read `uf.md` and extract all UF Blocks
- For each UF, capture: UF-ID, Parent IF, Goal, I/O Contract, Algorithm Summary, Edge Cases, Verification Plan
- If `uf_if_coverage_review.md` exists, skip any UFs flagged `REDUNDANT` unless explicitly requested
- Detect implementation language from project context (Python default; check for existing source files)

### Step 2 — RED: Write Tests First (from Acceptance Criteria)

**테스트가 증거다 — "잘 될 것 같다"는 완료가 아니다.** 구현 전에 테스트를 먼저 작성한다.

각 UF의 `Verification Plan`(Given/When/Then)을 pytest 함수로 직접 변환:
- **Acceptance criteria test** — Given/When/Then 그대로 매핑. 먼저 작성하고 FAIL 확인 필수
- **Nominal test** — 정상 입력 → 허용 오차 내 기대 출력
- **Edge-case tests** — UF Block의 Edge Cases 항목당 1개

```python
# RED step: 테스트 먼저 작성 → NameError/AssertionError로 FAIL나야 정상
def test_uf_<id>_<name>_acceptance():
    """Given <상황>, When <동작>, Then <결과>."""
    # Arrange
    input_data = <nominal_input>           # Given 기반
    # Act
    result = uf_<id>_<name>(input_data)   # NameError FAIL — 올바른 상태
    # Assert
    assert result == pytest.approx(expected, rel=1e-4)  # Then 기반

def test_uf_<id>_<name>_edge_<case>():
    with pytest.raises(ValueError):
        uf_<id>_<name>(<invalid_input>)
```

**DAMP > DRY (테스트 한정):** 각 테스트는 독립적으로 읽혔을 때 스펙처럼 이해돼야 한다.
테스트 간 중복은 허용된다. setup 추상화로 "무엇을 검증하는지"가 불명확해지는 것을 피한다.

**실제 구현 우선, Mock 최소화:** 시스템 경계(파일 I/O, 네트워크, 하드웨어)에서만 Mock 사용.
UF Block의 acceptance criteria가 모호하면 `# CLARIFICATION NEEDED: <질문>` 기록 후 `BLOCKED` 처리.

### Step 3 — GREEN: Generate Implementation Stub per UF

테스트가 FAIL 확인된 후, 테스트를 통과시키는 최소 구현을 작성한다:
- I/O Contract와 일치하는 시그니처 (타입, 형태, 단위를 독스트링에 명시)
- Google-style docstring (Args, Returns, Raises, Example)
- 알고리즘 본문 (`pass` 불가 — 최소한 알고리즘 개요 주석이라도 작성)
- 입력 검증 가드 (타입 체크, 형태 체크, 범위 체크)
- Edge Cases 필드의 엣지케이스 처리

```python
def uf_<id>_<snake_name>(
    <input_name>: <type>,  # <unit/shape>, <range>
) -> <output_type>:
    """<Goal statement>

    Args:
        <input_name>: <description>. Shape: <shape>. Unit: <unit>.
    Returns:
        <output_name>: <description>. Shape: <shape>. Unit: <unit>.
    Raises:
        ValueError: if <edge case condition>
    Example:
        >>> result = uf_<id>_<name>(...)
        >>> assert result.shape == (...)
    """
    # Input validation
    ...
    # Core algorithm
    ...
    return result
```

구현 후 테스트 실행 → PASS(GREEN) 확인. 이후 테스트가 여전히 PASS인 상태에서 리팩터링.

**테스트 안티패턴 — 발견 즉시 수정:**

| 안티패턴 | 문제 | 수정 |
|---|---|---|
| 구현 내부 동작 테스트 | 리팩터링만 해도 테스트 깨짐 | 입력/출력(상태)만 검증 |
| 불안정 테스트 (타이밍·순서 의존) | 테스트 신뢰도 하락 | 결정론적 assertion, 격리 |
| 과도한 Mock | Mock 통과해도 프로덕션 실패 | 실구현 > fake > stub > mock |
| 첫 실행부터 PASS | 아무것도 검증하지 않을 가능성 | RED 단계 FAIL 확인 의무화 |
| 모호한 테스트명 (`test_case1`) | 실패 시 원인 파악 불가 | `test_uf_XX_<동작>_<조건>` 형식 |

### Step 4 — Validate and Emit Coverage Report
- Run a static I/O chain check: output type/shape of UF-N must match input type/shape of its consumer UF
- Record each UF implementation status: `IMPLEMENTED` / `STUB` / `BLOCKED`
- Emit `reports/impl/uf_impl_report_<timestamp>.md`

---

## Output Files

| File | Description |
|---|---|
| `src/uf/<module_name>.py` | Implementation code, one file per IF group |
| `tests/unit/test_<module_name>.py` | Unit test file per IF group |
| `reports/impl/uf_impl_report_<timestamp>.md` | Implementation status report |

---

## Output Template — `uf_impl_report_<timestamp>.md`

```markdown
# UF Implementation Report
Date: <date>

## Implementation Status

| UF-ID | Function Name | Status | Test Coverage | Notes |
|---|---|:---:|:---:|---|
| UF-01 | uf_01_load_signal | IMPLEMENTED | nominal + 2 edge | — |
| UF-02 | uf_02_normalize | IMPLEMENTED | nominal + 1 edge | — |
| UF-03 | uf_03_transform  | STUB        | —               | algorithm TBD |

## I/O Chain Validation

| UF-N → UF-M | Output Type | Input Type | Match |
|---|---|---|:---:|
| UF-01 → UF-02 | np.ndarray(float32) | np.ndarray(float32) | ✅ |
| UF-02 → UF-03 | np.ndarray(float32) | torch.Tensor        | ❌ type mismatch |

## Action Items
- [ ] UF-03: finalize algorithm; resolve tensor type mismatch with UF-02
```

---

## Rules
1. Never leave a function body as `pass` or `raise NotImplementedError` without at least a partial algorithm outline
2. Every numeric threshold from the acceptance criteria must appear verbatim in the test assert
3. If the algorithm is underdetermined by the UF Block, note `# CLARIFICATION NEEDED: <question>` inline and flag as `STUB`
4. Do not import libraries not listed in `requirements.md` or `reference.md` without noting the addition
5. **Beyonce Rule:** 기존 UF를 수정할 때, 기존 테스트 커버리지가 줄어들어서는 안 된다. 동작을 변경하면 해당 동작에 대한 테스트도 함께 갱신한다.

See `references/reference.md` for language-specific templates and library recommendations.

---

## Bundled Resources

| Resource | When to use |
|---|---|
| `references/reference.md` | Python module template, pytest template, I/O type table, algorithm → code mapping |
| `references/examples.md` | Example prompts and expected outputs |
| `assets/uf-module-template.py` | Base Python module template — copy and fill in for each IF group |
| `assets/test-template.py` | Base pytest template — copy and fill in for each module |
| `scripts/validate_uf_impl.py` | Run after generating `src/uf/` and `tests/unit/` to verify completeness |

```bash
python <skill_dir>/scripts/validate_uf_impl.py <project_root>
```
