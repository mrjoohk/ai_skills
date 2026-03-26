# IF Decomposition

## IF-01: <title>

Input:  <name> (<type>, <unit/shape>)
Output: <name> (<type>, <unit/shape>)

[→ sequential]  <!-- or [‖ parallel] -->

├── UF-01-01: <verb_noun>
│     Input:  <name> → Output: <name> (<type>)
│     Note: <!-- algorithm in 1 line -->
│
├── UF-01-02: <verb_noun>          [depends on UF-01-01]
│     Input:  <name> → Output: <name> (<type>)
│     Note:
│
└── UF-01-03: <verb_noun>          [depends on UF-01-02]
      Input:  <name> → Output: <name> (<type>)
      Note:

---
<!-- Copy the section above for each IF -->

## UF Candidate Summary

| UF-ID | Parent IF | Verb-Noun Name | Input Type | Output Type |
|-------|-----------|---------------|------------|-------------|
| UF-01-01 | IF-01 | | | |
| UF-01-02 | IF-01 | | | |
