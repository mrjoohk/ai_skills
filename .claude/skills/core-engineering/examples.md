# Examples: Core Engineering

## Test Prompt Example (Requirements)
**Prompt to Claude Code:**
- "Given the goal 'Implement SAR backprojection for a 3D voxel grid', produce REQ blocks with numeric acceptance criteria, then propose a UF chain (UF-01..UF-xx) and a verification plan."

## Test Prompt Example (Minimal Diff)
**Prompt:**
- "Refactor `src/sar/bp.py` to remove duplicated allocations, but do not change behavior. Provide only a patch and add a unit test that asserts output equality vs baseline."

## Expected Output Checklist
- Requirements are testable
- I/O contracts contain shapes + units
- Evidence artifacts are defined
