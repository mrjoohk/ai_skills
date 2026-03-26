# Reference: if-designer Templates and Rules

## Stage Output Summary

| Stage | Output File | Key Contents |
|:---:|---|---|
| 5 | `if_list.md` | IF Blocks — system boundary modules with I/O contracts |
| 6 | `if_decomposition.md` | IF → UF candidate tree with dependency graph |

---

## IF Block Template (if_list.md)

```markdown
- IF-ID: IF-##
- Title: (one-line summary — "what this interface does")
- Producer: <component or actor that generates the output>
- Consumer: <component or actor that consumes the output>
- Input Contract:
    <name>: <type>, <unit/shape>, <range>
- Output Contract:
    <name>: <type>, <unit/shape>, <range>
- Constraints:
    (timing, protocol, serialization, resource limits)
- Failure Modes:
    - <what breaks and what the symptom is>
- Linked REQs: REQ-###, REQ-###
```

---

## IF Decomposition Tree Notation (if_decomposition.md)

Use indented tree notation. Annotate execution order and data flow.

```
IF-01: <title>
  Input:  raw_frame (ndarray, uint8, H×W×3)
  Output: detections (List[BoundingBox])

  [→ sequential]  [‖ parallel]

  ├── UF-01-01: preprocess_frame
  │     Input:  raw_frame → Output: normalized_frame (float32, 0–1)
  │
  ├── UF-01-02: run_inference          [depends on UF-01-01]
  │     Input:  normalized_frame → Output: raw_predictions (tensor, N×85)
  │
  └── UF-01-03: postprocess_detections [depends on UF-01-02]
        Input:  raw_predictions → Output: detections (List[BoundingBox])
```

### Annotation Legend

| Symbol | Meaning |
|---|---|
| `→` | Sequential execution (must complete before next starts) |
| `‖` | Parallel execution (can run concurrently) |
| `[depends on UF-XX-YY]` | Explicit data dependency |
| `[UNCOVERED: REQ-###]` | REQ not mapped to any UF candidate in this IF |

---

## IF Identification Heuristics

**When to create a new IF:**
- Data changes type, protocol, or coordinate system at the boundary
- A clear producer and consumer can be named on both sides
- A different team or component owns each side
- The boundary is a natural test seam (can be mocked)

**When NOT to create a separate IF:**
- The "interface" is just a function call within the same module
- It would result in an IF with only one UF that just passes data through
- Two candidate IFs have exactly the same Producer, Consumer, and data type

**Typical IF count by system type:**

| System Type | Typical IF Count |
|---|---|
| Small ML pipeline (input → model → output) | 3–5 |
| Multi-modal sensor fusion | 5–8 |
| Distributed microservice | 6–10 per service |
| Embedded real-time system | 4–7 |

---

## REQ→IF Coverage Matrix

Include a coverage table at the end of `if_list.md`:

```markdown
## REQ→IF Coverage Matrix

| REQ ID | IF Coverage | Status |
|--------|-------------|--------|
| REQ-001 | IF-01, IF-02 | ✅ Covered |
| REQ-002 | IF-02 | ✅ Covered |
| REQ-010 | IF-01 | ✅ Covered |
```

Any uncovered REQ → add `[UNCOVERED]` row and flag before proceeding.

---

## SRP Decomposition Guide

A UF candidate at a leaf node is "small enough" when:
- It has exactly one reason to change
- It can be tested with a single test function (happy path + 2–3 edge cases)
- Its algorithm summary fits in 1–3 lines
- It operates on one data type in → one data type out

A leaf node is "too large" when:
- It combines data loading + transformation + validation
- Its name contains "and" or "or"
- You can't describe its input in a single I/O contract line
