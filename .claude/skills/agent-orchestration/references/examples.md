# Examples: Agent Orchestration

## Test Prompt 1: Establish 3-Agent Plan
```
"Establish a 3-agent plan for implementing UF-10..UF-15.
 Include role definitions for each agent, handoff messages, and MCP command list."
```

**Expected Outputs:**
- Agent-1/2/3 role definitions
- Handoff blocks by stage
- MCP command list for each agent

---

## Test Prompt 2: Write Handoff Message
```
"Write a handoff message from Agent-1 to Agent-2.
 Target: IF-03 implementation in src/pipeline/encoder.py.
 Include acceptance criteria (encoding latency <= 5ms, error rate <= 0.1%)
 and evidence artifact paths."
```

**Expected Outputs:**
- Handoff block (From/To/Objective/Context/Deliverables/Constraints/Tests/Evidence)

---

## Test Prompt 3: Generate Webhook Payloads
```
"Generate 4 webhook payload types (SUCCESS / FAILURE / COVERAGE_LOW / REGRESSION)
 and save them to configs/webhook_templates/."
```

**Expected Outputs:**
- `configs/webhook_templates/success.json`
- `configs/webhook_templates/failure.json`
- `configs/webhook_templates/coverage_low.json`
- `configs/webhook_templates/regression.json`

---

## Test Prompt 4: Design Process Agent Allocation
```
"Handle the following issue with a 3-agent structure:
 'Batch data collection module memory usage exceeds baseline.'
 Allocate Agent-1 to perform Stage 1~7, Agent-2 for implementation,
 and Agent-3 for Stage 8 validation planning."
```

**Expected Outputs:**
- Agent-assigned stages and output list by agent
- Handoff messages (Agent-1→2, Agent-2→3)
