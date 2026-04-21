---
name: dashboard-designer
description: >
  Turns a vague "I want a web dashboard" request into a concrete GUI specification
  and a working HTML scaffold. Runs a structured 6-axis interview (purpose/data,
  layout archetype, interaction model, visualization widgets, tech stack, style),
  writes a machine-readable dashboard_spec.md, picks the right archetype template,
  and emits a runnable starter. Use this whenever the user mentions building a web
  dashboard, a training-metrics viewer, a TensorBoard embed, a simulation log
  playback UI, a model/object inspector, a monitoring panel, or says things like
  "대시보드 만들어줘", "web 기반 대시보드", "로그 뷰어", "시뮬레이션 플레이백 UI",
  "학습 지표 보는 화면", "객체 클릭하면 정보 뜨는 패널", "TensorBoard 임베딩",
  "dashboard spec 만들어줘", "GUI 형식화", even when they don't explicitly use
  the word "dashboard". Also use before running repo-doc-writer or uf-designer
  when the frontend/GUI design isn't fixed yet.
---

# Dashboard-Designer — Web Dashboard GUI Formalizer

This skill solves a recurring problem: every research / simulation / training project
needs a web-based dashboard, and every one of them ends up looking different because
the GUI is improvised on the fly. This skill forces the GUI characteristics to be
decided **before** coding by running a short structured interview, then emits a spec
document and a working scaffold.

The design philosophy: a dashboard's look and feel is almost entirely determined by
six orthogonal decisions. Nail those six, and the rest is mechanical. That is why
this skill asks a bounded set of questions rather than an open-ended "what do you
want?" — bounded questions converge; open-ended ones do not.

> **Always read `references/axes.md` and `references/archetypes.md` before starting
> the interview** so you know the full option space and can offer sensible defaults
> instead of vague prompts.

---

## Bundled Resources

| File | When to use |
|---|---|
| `references/axes.md` | The 6 decision axes + each axis's option menu + default recommendations |
| `references/archetypes.md` | The 5 layout archetypes (when each fits, which widgets belong) |
| `references/widget_catalog.md` | Catalog of visualization widgets + embedded-tool integrations (TensorBoard, MLflow, etc.) |
| `assets/dashboard_spec_template.md` | Copy → fill for the final spec document |
| `assets/archetypes/single-html-tabbed/template.html` | Scaffold for sidebar+main+tabs layout (good for training-metric dashboards) |
| `assets/archetypes/split-pane-inspector/template.html` | Scaffold for split-pane w/ detail inspector (good for simulation playback / object inspection) |

Two archetypes are intentional — starting with too many fragments the user's mental
model. New archetypes should be added only when a real project can't be served by
any existing one.

---

## Execution Flow

### Phase A — Interview (interactive)

Before writing any files, run a 6-axis interview. Use the `AskUserQuestion` tool
(a single call with multiple questions is fine — it is friendlier than many
back-to-back turns) to collect answers for the axes defined in `references/axes.md`:

1. **Purpose & Data Source** — what's being visualized, static/live/streaming, external tools to embed
2. **Layout Archetype** — sidebar+main, split-pane+inspector, grid-of-cards, timeline-centric, single-canvas
3. **Interaction Model** — selection, brushing, playback, filter/search, comparison
4. **Visualization Widgets** — line/scatter charts, 3D scene, table, heatmap, image viewer, log stream, iframe embeds
5. **Tech Stack & Deployment** — single HTML vs React project vs full-stack, static/server, Docker
6. **Style** — dark/light, branding, compact/spacious

**Guidance for running the interview well:**

- Offer **sensible defaults** for every question. A user who just says "I dunno"
  should still get a good dashboard. The defaults in `references/axes.md` are tuned
  to produce a reasonable result for the most common research scenarios.
- If the user has already described their use case in earlier messages, **prefill**
  the answers you can infer and only ask about the remaining ones. Don't make the
  user repeat themselves.
- Keep it to ≤ 8 questions total. If an axis is fully implied by earlier answers,
  skip it. The interview should take under two minutes; longer than that and the
  user abandons the tool.
- For **Layout Archetype**, if the user's earlier description maps cleanly to one
  archetype (e.g. "I want to replay simulation logs and click objects to see
  details" → split-pane+inspector), propose that archetype as the default and let
  the user confirm rather than asking open-endedly.

---

### Phase B — Write the spec (autonomous)

Using answers from Phase A, copy `assets/dashboard_spec_template.md` and fill in
every section. Save as `dashboard_spec.md` in the user's output folder
(`/sessions/ecstatic-nifty-wozniak/mnt/AI_TOOLS/` if there is no project folder
context, otherwise the project's `docs/` or similar).

The spec must be complete enough that a different engineer (or Cursor, or the
`uf-designer` skill) could read it alone and build the dashboard without the user
in the room. That means: resolved values for all 6 axes, explicit list of widgets
with their data bindings, layout sketch in plain text, and a "TODOs for
implementation" section listing anything that was deferred.

---

### Phase C — Generate the scaffold (autonomous)

Based on the chosen archetype, copy the matching template from `assets/archetypes/`
and emit a working starter file. Customize the template to match the spec:

- **Single HTML archetypes** — fill in tab titles, widget placeholders, and any
  iframe embeds (TensorBoard, Grafana, etc.) directly in the template. The output
  is a single `.html` file the user can open in a browser immediately.
- **React project** (not yet bundled) — if the user picks React, generate a single
  `App.jsx` that matches the chosen archetype, plus a short note telling the user
  to scaffold the surrounding project with `npm create vite@latest`. Don't
  fabricate an entire project tree inline; the value is in the component layout
  and data wiring, not the boilerplate around it.

Keep data-binding code as **clearly-marked TODOs** rather than guessing. For
example:

```html
<!-- TODO: replace with your data source.
     Expected shape: [{ step: number, loss: number, accuracy: number }, ...] -->
<script>const metricsData = [];</script>
```

Future invocations of `uf-implementor` or Cursor fill those TODOs in. The
scaffold's job is to nail the GUI, not the data pipeline.

Save the scaffold to the same output folder as the spec. Use a meaningful filename
derived from the project name, e.g. `training_metrics_dashboard.html`.

---

### Phase D — Summary (short)

After both files are written, respond with:

1. A `computer://` link to the spec document
2. A `computer://` link to the scaffold file
3. A 2–3 line summary of what was decided on each axis
4. Suggested next steps (usually: "Open the HTML to preview the layout, then pipe
   the spec into `uf-designer` or Cursor to implement the data bindings")

Do not dump the full spec into the chat — the user can read the file. Conversational
brevity matters here; the deliverable is the files.

---

## Design Principles

**Why six axes and not more or fewer.** Too few axes leave the GUI underspecified
and the output still feels improvised. Too many axes turn the interview into a
chore and users bail before finishing. Six is the sweet spot we arrived at by
looking at real dashboards: every meaningful GUI decision we found either slots
into one of these six or is a detail that can be deferred to implementation.

**Why only two archetypes initially.** A pattern library with ten archetypes
sounds nice but degrades quickly — the skill spends more time "choosing" than
"building", and each archetype's quirks have to be maintained. Two archetypes
cover roughly 80% of research dashboards (metric monitoring vs. object/state
inspection). Add more only when a concrete project proves the existing two can't
accommodate it.

**Why defaults matter so much.** Most users don't actually care about half the
decisions — they just want something reasonable. Defaults let them say "use the
default" and still get a coherent result. Without defaults, the interview becomes
a nightmare of "I don't know, what do you recommend?" ping-pong.

**Why the spec is a separate artifact.** The spec is the long-term asset. The
scaffold rots (frameworks change, styles date); the spec captures the *intent*
and lets any future developer (or AI) regenerate the scaffold. It's also the
handoff point to `uf-designer` / `repo-doc-writer` / Cursor, mirroring how
`requirements.md` flows downstream in the core-engineering pipeline.

---

## Out of Scope

- Full backend design (data APIs, WebSocket protocols, authentication) — use
  `req-elicitor` and `if-designer` for those in a separate pass.
- Pixel-perfect styling — the scaffold aims for "looks clean and works", not
  "matches Figma". A designer can take the spec and redo the visuals.
- Accessibility audits and i18n — worth doing later, but out of scope for the
  initial scaffold.

If the user asks for any of the above, acknowledge and suggest the right
follow-up.
