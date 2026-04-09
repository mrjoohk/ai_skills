---
name: uf-chain-validator
description: "Validates UF-chain integrity, I/O contracts, verification ownership completeness, and evidence linkage. Uses three separate gates: implementation/runtime, document-to-test-plan alignment, and evidence-pack completeness."
user-invocable: true
allowed-tools: Read, Write
---

# UF Chain Validator

Validates the correctness of a UF chain against three independent gates.
**Missing a per-UF standalone functional test is NOT an automatic failure** —
the validator checks whether declared verification ownership is explicit and satisfied,
not whether every UF has a standalone test.

## When to Use
- Before merging a feature branch
- After adding or refactoring UF modules
- When coverage or evidence gates fail in CI
- After `uf-designer` completes, to confirm ownership is declared before implementation

## Inputs
- Path(s) to UF definition files (e.g., `uf.md`, `uf_split/uf_if*.md`)
- `if_list.md` — used to verify IF-level acceptance test references
- Project source paths (e.g., `src/`)
- Test paths (e.g., `tests/`)
- Evidence pack root (e.g., `evidence_pack/`)

---

## Three Validation Gates

Run each gate independently and report results separately.
A gate FAIL blocks handoff; a gate WARN is advisory.

---

### Gate 1 — Implementation / Runtime Validation

Checks that the implemented chain produces correct outputs at runtime.

**Checks:**
- UF IDs are complete, ordered, and match `uf.md`
- Each UF has an explicit I/O contract (type + unit/shape + range)
- I/O chain continuity: output type of UF-N matches input type of UF-(N+1)
- No implicit type conversions between UFs
- Runtime smoke test passes (if available): invoke the chain end-to-end with a known input

**FAIL conditions:**
- Missing UF blocks or broken UF-ID sequence
- I/O contract absent or underspecified (e.g., "tensor" without shape)
- Chain break: output/input type mismatch at any UF boundary
- Runtime invocation raises an uncaught exception

**WARN conditions:**
- I/O range not specified (type + shape present but value range missing)

---

### Gate 2 — Document-to-Test-Plan Alignment

Checks that every UF's declared `Verification Plan` is internally consistent and
that the referenced test artifacts exist (or are explicitly deferred).

**Ownership-based rules:**

| Declared Ownership | Unit Verification required | Chain Verification required |
|---|---|---|
| `UF-local` | ✅ Named test path must exist in `tests/` | ❌ Not required |
| `guard-rail+chain` | ⚠️ Guard-rail tests required; standalone functional test NOT required | ✅ Named IF-chain test path must exist |
| `IF-acceptance` | ❌ No standalone test required | ✅ Named IF-acceptance test path must exist |

**FAIL conditions:**
- Any UF has no `Ownership` field declared
- A `UF-local` UF names a test path that does not exist in `tests/`
- A `guard-rail+chain` or `IF-acceptance` UF has no Chain Verification path named
- A `guard-rail+chain` or `IF-acceptance` UF has a standalone functional test path listed as its primary coverage mechanism (contradicts ownership)

**WARN conditions:**
- `UF-local` coverage target below 90% without justification
- Guard-rail tests for `guard-rail+chain` UFs are absent (type/sentinel checks missing)
- **Beyonce Rule 위반:** 기존 UF를 수정했는데 해당 UF의 테스트 커버리지가 이전보다 줄어든 경우. 동작을 바꾸면 테스트도 함께 갱신해야 한다.

**테스트 품질 체크 (WARN — 발견 시 보고):**
- 테스트명이 `test_case1`, `test_func` 등 동작을 설명하지 않는 경우 → `test_uf_XX_<동작>_<조건>` 형식 권장
- 테스트가 UF 내부 구현 방식(특정 함수 호출 여부)을 검증하고 있는 경우 → 입력/출력(상태)만 검증하도록 수정 권장
- 단일 테스트 함수에 여러 개념이 혼합된 경우 → 개념당 1개 테스트로 분리 권장

> **Do NOT fail** a `guard-rail+chain` or `IF-acceptance` UF solely because it lacks
> a standalone functional test. That is the intended design.

---

### Gate 3 — Evidence Pack Completeness

Checks that the evidence pack references are consistent with the declared verification plan.

**Checks:**
- Each `UF-local` UF has a corresponding evidence entry (test run result, coverage report)
- Each IF-chain test referenced in `guard-rail+chain` or `IF-acceptance` UFs has a corresponding evidence entry
- Evidence entries are not stale (timestamp >= last code change, if determinable)
- `uf_split/` companion files exist for every IF and are in sync with `uf.md`

**FAIL conditions:**
- Evidence entry missing for a `UF-local` UF that claims PASS
- IF-chain evidence missing for `guard-rail+chain` or `IF-acceptance` UFs
- `uf_split/` files out of sync with `uf.md` (UF-ID or Ownership mismatch)

**WARN conditions:**
- Evidence timestamps suggest staleness (> 7 days without code change annotation)

---

## Output

A validation report in Markdown with the following structure:

```
# UF Chain Validation Report

## Summary
| Gate | Result | Issues |
|------|--------|--------|
| Gate 1 — Implementation / Runtime | PASS / FAIL / WARN | N |
| Gate 2 — Document-to-Test-Plan    | PASS / FAIL / WARN | N |
| Gate 3 — Evidence Pack            | PASS / FAIL / WARN | N |

Overall: PASS / FAIL

## Gate 1 Findings
...

## Gate 2 Findings
...

## Gate 3 Findings
...

## Proposed Fixes
(minimal diffs or action items per finding)
```

---

## MCP Integration
- `mcp.filesystem`: scan UF docs, test directories, and evidence pack
- `mcp.shell`: run `pytest -q`, `pytest --cov`, `ruff`, `mypy` (as applicable)
- `mcp.github`: comment on PRs with the report

## Token Saving
- Reference failing files + exact sections; avoid pasting whole documents.
- Provide patches/diffs for fixes.
- Summarize errors with paths and line numbers.

See `references/reference.md` for report format and `references/examples.md` for test prompts.
