---
name: cursor-task-formatter
description: >
  Converts UF Block definitions (from rd/uf.md) or code review findings (from code-reviewer)
  into ready-to-paste task prompts for any external coding agent (Cursor Composer, Windsurf,
  Copilot Workspace, Codex/Gemini CLI, etc. — "Cursor" is the canonical example). Produces
  structured, self-contained prompts that any coding agent can act on without additional
  context. Trigger when the user says "Cursor 프롬프트 만들어줘", "코딩 에이전트 프롬프트
  만들어줘", "구현 지시서 써줘", "task prompt 생성해줘", "fix prompt 만들어줘", "에이전트에
  넘겨줄 내용 만들어줘", or after uf-designer or code-reviewer has produced output and the
  user wants to move to the implementation/fix step with an external coding agent. Also
  trigger when the user has a UF spec or review result and wants to know exactly what to
  paste into their coding agent.
---

# Cursor-Task-Formatter (coding-agent task formatter)

Takes structured design or review output and produces clean, self-contained coding-agent
prompts — one prompt per task, ready to paste into Cursor Composer, Windsurf, Copilot,
or any CLI/IDE coding agent.

> **Agent-neutral contract:** prompts must be fully self-contained markdown (spec + I/O
> contract + edge cases + "Verify by:"), so they work identically regardless of which
> coding agent consumes them. Different UF groups may even be routed to different agents
> in parallel. The skill name retains "cursor" for historical compatibility.

> **Read `references/prompt_patterns.md`** for prompt templates and anti-patterns before writing.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/prompt_patterns.md` | Cursor prompt patterns, do's/don'ts, length guidelines |
| `assets/implement_prompt_template.md` | For UF → Cursor implementation task |
| `assets/fix_prompt_template.md` | For review findings → Cursor fix/refactor task |

---

## Two Modes

### Mode A — Implement (UF → Cursor)

**Input:** one or more UF Blocks from `uf.md` (or `docs/ai/tasks/*.md`)
**Output:** one Cursor Composer prompt per UF

Use `assets/implement_prompt_template.md`. Each prompt must be:
- Self-contained: includes the function signature, I/O contract, edge cases
- File-aware: specifies the exact file path where code should go
- Verifiable: ends with "Verify by:" criteria Cursor can check

Group tightly coupled UFs (same parent IF, sequential data flow) into a single prompt if
they total under ~15 lines of spec. Never group UFs from different IFs.

### Mode B — Fix (Review → Cursor)

**Input:** a code review finding block from `code-reviewer` output
**Output:** one Cursor Composer prompt per finding (or per logical fix group)

Use `assets/fix_prompt_template.md`. Each prompt must be:
- Location-specific: file path + line range
- Outcome-focused: states what the fixed code should do, not just what's wrong
- Scoped: no broader refactors unless the review explicitly calls for them

---

## Execution

1. Identify the input type: UF spec (Mode A) or review findings (Mode B)
2. For each task/finding, fill the appropriate template
3. Output prompts as numbered fenced code blocks (` ```cursor-prompt `) so the user
   can copy each one cleanly
4. After the last prompt, print a **Handoff Checklist** (see `references/prompt_patterns.md`)

---

## Rules

- Each prompt must stand alone — Cursor has no memory of previous prompts in a session.
- Keep prompts under 300 words. If a task is larger, split it.
- Do not include design rationale, history, or "why" context — Cursor only needs "what" and "how".
- Always end with a concrete "Verify by:" statement.
