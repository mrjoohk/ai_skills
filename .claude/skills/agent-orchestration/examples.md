# Examples: Agent Orchestration

## Test Prompt 1: 3-Agent Plan
"Create a 3-agent plan to implement UF-19..UF-21, including handoffs and MCP commands for each step."

## Test Prompt 2: Handoff Message
"Write a handoff from Agent-1 to Agent-2 for implementing `src/uav/dynamics.c` integration at 120Hz with shared memory IPC. Include acceptance tests."

## Test Prompt 3: Webhook Templates
"Generate webhook payloads for success/failure/coverage_low/regression, and store them in `configs/webhook_templates/`."

## Expected Output
- handoff blocks
- command lists (MCP)
- artifact paths
