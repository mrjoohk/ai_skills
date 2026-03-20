---
name: if-integrator
description: "Integrates implemented Unit Functions (UFs) into Integration Function (IF) level modules. Generates integration glue code, public API interfaces, integration tests, and validates that the combined UF outputs satisfy the parent IF's I/O contract and acceptance criteria. Trigger when the user says 'integrate UFs into IF', 'build IF module', 'write integration code', 'assemble unit functions', or 'create integration tests'."
user-invocable: true
allowed-tools: Read, Write
---

# IF Integrator

Takes UF implementation files (`src/uf/`) and IF definitions (`if_list.md`) as input and **assembles UFs into IF-level integration modules** with public API wrappers, call orchestration, and integration tests.
This skill bridges UF-level implementation and system-level validation.

---

## When to Use
- After `uf-implementor` has produced `src/uf/` files with `IMPLEMENTED` status for all required UFs
- When you need to compose individual UFs into a coherent IF-callable API
- When you want integration test scaffolding generated from IF acceptance criteria

---

## Inputs
- `if_list.md` — IF Block definitions (required)
- `if_decomposition.md` — UF dependency graph per IF (required)
- `src/uf/<module>.py` — implemented UF files (required)
- `uf_if_coverage_review.md` — coverage matrix for validation reference (recommended)
- `reports/impl/uf_impl_report_<timestamp>.md` — implementation status (optional; to skip `STUB`/`BLOCKED` UFs)

---

## Execution Steps

### Step 1 — Load IF Definitions and UF Call Graph
- Read `if_list.md` to get each IF's: inputs, outputs, constraints, acceptance criteria, linked REQs
- Read `if_decomposition.md` to reconstruct the UF call graph per IF (execution order, data flow)
- Read `src/uf/*.py` to confirm function signatures match the I/O contracts in the call graph
- Flag any signature mismatch as `INTERFACE_ERROR` before proceeding

### Step 2 — Generate IF Integration Module per IF
For each IF, produce an integration module that:
- Imports the relevant UF functions from `src/uf/`
- Orchestrates UF calls in dependency order (sequential, parallel, or conditional)
- Exposes a single public entry-point function named `if_<id>_<snake_name>(**kwargs)`
- Maps the IF-level I/O contract to internal UF arguments
- Handles inter-UF data conversion if type/shape mismatches are detected

```python
# Example structure
def if_01_<snake_name>(
    <if_input>: <type>,   # IF-level input
    **kwargs,
) -> <if_output_type>:
    """<IF Goal statement>

    Integrates: UF-01 → UF-02 → UF-03
    REQ links: REQ-01, REQ-04

    Args:
        <if_input>: <description>. Shape: <shape>. Unit: <unit>.
    Returns:
        <if_output>: <description>. Shape: <shape>. Unit: <unit>.
    Raises:
        IntegrationError: if any constituent UF fails its postcondition.
    """
    # Step 1: UF-01
    intermediate_1 = uf_01_<name>(<if_input>)

    # Step 2: UF-02 (depends on UF-01 output)
    intermediate_2 = uf_02_<name>(intermediate_1)

    # Step 3: UF-03 (depends on UF-02 output)
    result = uf_03_<name>(intermediate_2)

    # Postcondition check
    _assert_if_postcondition(result)
    return result
```

### Step 3 — Generate Integration Tests per IF
For each IF, produce integration tests that:
- Exercise the full UF call chain through the IF entry point
- Assert the IF-level acceptance criteria (Given/When/Then with numeric thresholds)
- Include boundary tests for IF-level inputs
- Mock unavailable external dependencies (hardware, services) as fixtures

```python
# Example integration test
def test_if_01_<name>_acceptance_criteria(realistic_input):
    """Given <IF context>, When if_01_<name>() runs,
    Then <IF metric> <op> <threshold>."""
    result = if_01_<name>(realistic_input)
    metric = compute_if_metric(result)
    assert metric >= <threshold>, f"IF-01 acceptance: expected >= {<threshold>}, got {metric:.4f}"
```

### Step 4 — Emit Integration Report
Record the integration result in `reports/impl/if_integration_report_<timestamp>.md`:
- Per-IF: entry-point function, UF call sequence, interface match status, test results summary
- I/O contract compliance: IF-level input/output vs. REQ constraints
- Action items for any `INTERFACE_ERROR` or unresolved `STUB` UFs

---

## Output Files

| File | Description |
|---|---|
| `src/if/<module_name>.py` | IF integration module, one file per IF |
| `tests/integration/test_<module_name>.py` | Integration test file per IF |
| `reports/impl/if_integration_report_<timestamp>.md` | Integration status report |

---

## Output Template — `if_integration_report_<timestamp>.md`

```markdown
# IF Integration Report
Date: <date>

## Integration Status

| IF-ID | Entry Point | UF Call Sequence | Interface | Tests | Status |
|---|---|---|:---:|:---:|:---:|
| IF-01 | if_01_process | UF-01→UF-02→UF-03 | ✅ | 3/3 pass | COMPLETE |
| IF-02 | if_02_analyze | UF-04→UF-05       | ⚠️ | 1/2 pass | PARTIAL  |

## Interface Validation

| IF | I/O Contract | Matched | Notes |
|---|---|:---:|---|
| IF-01 | Input: float32(N,), Output: float32(M,) | ✅ | — |
| IF-02 | Input: float32(N,), Output: dict        | ❌ | UF-05 returns list; needs dict wrap |

## REQ Coverage

| REQ-ID | Linked IF | Acceptance Criterion | Status |
|---|---|---|:---:|
| REQ-01 | IF-01 | PESQ ≥ 3.0 | ✅ PASS |
| REQ-04 | IF-02 | Latency ≤ 50ms | ❌ FAIL |

## Action Items
- [ ] IF-02: wrap UF-05 list output into expected dict schema
- [ ] IF-02: profile and optimize to meet REQ-04 latency target (≤ 50ms)
```

---

## Rules
1. The IF entry-point function must satisfy the IF's I/O contract exactly — no internal detail should leak through the public signature
2. Every IF acceptance criterion must have a corresponding `assert` in the integration test
3. If a required UF is `STUB` or `BLOCKED`, the IF module must raise `NotImplementedError` at runtime with a descriptive message — never silently proceed
4. Data conversion between UFs (e.g., `ndarray → Tensor`) must be explicit and logged as a comment

See `reference.md` for integration patterns and test structure templates.
