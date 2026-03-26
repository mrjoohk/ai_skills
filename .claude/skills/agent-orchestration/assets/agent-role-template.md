# Agent-N: <Role Name>

## role
One-line role summary (e.g., "Requirements & Design Architect", "Implementation Builder", "Verifier & Evidence Pack")

## objective
Concrete objective this agent must achieve. Be specific about what "done" looks like.

## task_prompt
<!-- This is the exact prompt passed to the subagent. Write it as if addressing the subagent directly. -->
You are responsible for: <specific responsibility>.

Read the following input files:
- <input_file_path_1>
- <input_file_path_2>

Your tasks:
1. <Task 1 — specific action with expected output>
2. <Task 2 — specific action with expected output>
3. <Task 3 — specific action with expected output>

Save all output files to the paths listed in the outputs section below.
After completion, report results in this format:
STATUS: PASS | FAIL
OUTPUTS: <List of generated file paths>
SUMMARY: <One-line summary of what was accomplished>
ISSUES: <Problems encountered, or "none">

## inputs
- <path/to/input_file_1> — <brief description of what this file contains>
- <path/to/input_file_2> — <brief description>
- agents/agent-N-role.md (this file, self-reference optional)

## outputs
- <path/to/output_file_1.md> — <what this file contains>
- <path/to/output_file_2.py> — <what this file contains>
- reports/<task_name>_<timestamp>.md — execution report

## dependencies
- none
  <!-- OR: -->
- Agent-N must complete before this agent starts

## acceptance_criteria
- [ ] <File path> exists and has size > 0
- [ ] <Metric or quality criterion> is satisfied
- [ ] No `BLOCKED` or `STUB` items remain (or all are documented with justification)

## skills_to_use
- <skill-name>
  <!-- OR: none (if agent uses raw Claude capabilities) -->
