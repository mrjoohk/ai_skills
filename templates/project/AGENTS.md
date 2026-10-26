# Project agent entrypoint

Read [GLOBAL_RULES.md](GLOBAL_RULES.md) for shared defaults and PROJECT_RULES.md if present for actual project facts and mandatory controls. Follow higher-priority runtime instructions and the user's current scope and authorization.

The main agent decomposes the request, delegates only useful independent work, integrates results and verifies completion. Use one writer per shared file and respect available runtime capacity. Keep simple work in this conversation; persist a compact task record when resumption or coordination needs it.

Read [policies/TRACEABILITY.md](policies/TRACEABILITY.md) only when tracked mode or existing project requirements apply. Do not create logs, role files or a project questionnaire merely to begin an ordinary task.

When adding this entrypoint to an existing repository, merge applicable guidance into its existing AGENTS.md; do not replace repository-specific instructions.
