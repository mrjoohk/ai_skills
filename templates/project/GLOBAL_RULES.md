# GLOBAL_RULES.md

Common working defaults · v3 · 2026-10-26

## Scope and authority

- Follow the execution environment's higher-priority instructions and permissions. Apply the user's current request and existing authorization; do not add a routine approval step.
- Keep project facts in the project's existing configuration or PROJECT_RULES.md. Read that file if present. Its absence alone does not block work or require a questionnaire.
- These are defaults. Use the project's actual paths, formats and required checks. Do not silently disable an existing mandatory project control.
- Default to lightweight work. Read [policies/TRACEABILITY.md](policies/TRACEABILITY.md) only when tracked mode is explicitly selected or existing project requirements mandate those records.

## Work toward the requested outcome

- Establish the outcome and a proportionate completion check. For a small edit, keep this in the current conversation; do not manufacture a task document.
- Inspect available sources before asking. State consequential assumptions, make reasonable reversible choices, and ask only when missing information changes scope, correctness or authorization.
- Complete authorized work without repeated confirmation. When a final action needs separate approval, prepare the concrete change and evidence first.
- Preserve unrelated user edits and existing conventions. Refactor or generalize when needed for the requested result; avoid unrelated cleanup.
- Keep necessary project state and meaningful decisions discoverable. Do not save internal reasoning or every exchange as a new artifact.

## Plan tasks and delegate

- The main agent owns interpretation, task decomposition, shared decisions, integration and the final response.
- Work directly when delegation adds more coordination than useful independent work. Use subagents for separable implementation, bounded investigation, or independent review with a clear benefit.
- Give each delegated task an objective, inputs, output or return format, dependencies, write scope, acceptance criteria and relevant permissions. Pass only the context needed; do not imply access to another agent's private context.
- Assign one writer per shared file. Other agents return findings or separate fragments for the owner to merge. Parallelize independent work; start a dependent task only after its required input meets acceptance criteria.
- Bound concurrency by available runtime capacity, including the main agent. Do not recursively expand the team by default.
- After dispatch, do useful independent work on the critical path or integration while workers run. Use available status/wait tools when needed; avoid repeated unchanged polling.
- Inspect worker outputs and evidence. A worker's PASS or file existence alone does not establish completion. Consolidate questions and escalations through the main agent.
- Use a compact durable task/handoff record for long, resumable work. Short tasks can use messages. Subagent status or corrections must reach the main agent promptly.

## Execute and verify

- Use tools and skills available in the current environment; read only the references relevant to the task.
- Match verification to the change. Prefer a regression check for a reproducible bug; use content, link, schema or layout checks for documents as appropriate. Low-impact edits do not automatically need new tests or CI.
- Run applicable required checks. Broaden or repeat them when changes, failures or unresolved concerns justify it.
- Report what was actually run, observed, skipped or unavailable. Cite evidence for material measurements; a local check is not a CI result, and a simulation is not an application test.
- On failure, investigate or reassign within scope. Continue unaffected work. Ask the user only for a real missing decision, permission or external dependency; do not hide a blocker as completed work.

## Artifacts and completion

- Honor the requested format and existing canonical location. Tables may stay in Markdown, and diagrams may use Mermaid when the target supports it. Create extra exports only when useful or requested.
- Update current canonical documents in place; preserve important historical decisions separately. Do not keep an obsolete current value merely to retain its history.
- Create only necessary folders and records. If logging is enabled, the main agent owns shared IDs and logs; workers return change summaries for one batched update.
- Finish with the outcome, relevant verification and material limitations. Disclose unresolved work; do not declare completion solely because it has been registered in a ledger.
