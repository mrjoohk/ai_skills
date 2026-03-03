# Reference: Agent Orchestration Templates

## Standard 3-Agent Workflow
1. Agent-1: Spec + UF decomposition
2. Agent-2: Implement minimal diffs
3. Agent-3: Tests + evidence + CI gates

## Handoff Message (copy/paste)
From Agent:  
To Agent:  
Objective:  
Context Links:  
Deliverables:  
Constraints:  
Acceptance Tests:  
Evidence Outputs:  

## Status Webhook Templates
- SUCCESS: {task, commit, summary, artifacts}
- FAILURE: {task, commit, error_summary, failing_commands, logs_path}
- COVERAGE_LOW: {task, current, required, missing_modules}
- REGRESSION: {metric, before, after, threshold, reproduction_steps}
