# The 6 Decision Axes

Every dashboard's look and feel is determined by answers to these six questions.
Collect all six during Phase A (interview). For each axis: the menu of options,
what each one means, and the default to propose when the user is unsure.

The defaults are tuned for the most common case at Realtime Visual — a research
engineer who wants to inspect training metrics or simulation results locally,
without setting up infrastructure. If the user is clearly in a different
situation (production monitoring, customer-facing deliverable, etc.), adjust the
defaults accordingly.

---

## Axis 1 — Purpose & Data Source

**What's the dashboard showing, and where does that data come from?**

Menu of data-source options:
- **Static files** — CSV, JSON, Parquet on disk. Loaded once at page load.
- **Tailing log / periodic poll** — file or REST endpoint polled every N seconds.
- **Live stream** — WebSocket or SSE, pushed updates.
- **Pre-aggregated API** — a server (FastAPI, Flask) exposes endpoints the
  dashboard calls on demand.

Menu of embedded-tool options (orthogonal to data source):
- None
- TensorBoard iframe
- MLflow iframe
- Grafana iframe
- Custom iframe

**Default:** static files + no embedded tool. It's the lowest-setup option and
works for 90% of ad-hoc research dashboards. If the user mentions training
metrics, propose TensorBoard iframe as a likely addition.

**Why this axis matters first:** data source determines whether the scaffold
needs event listeners, polling loops, or just a fetch on page load. Every later
decision depends on knowing this.

---

## Axis 2 — Layout Archetype

**Which of the five layout templates best fits the use case?**

Summaries — see `archetypes.md` for full descriptions:

1. **sidebar+main (+tabs)** — left nav listing runs/entities; main area with tabs
   showing metrics/charts. Best for training-metric dashboards, experiment
   trackers, anything with a "pick one item → see its data" flow.
2. **split-pane+inspector** — large primary canvas on the left (3D scene, map,
   log timeline) and a detail panel on the right that updates when the user
   clicks something. Best for simulation playback, object inspection, scene
   analysis.
3. **grid-of-cards** — a grid of self-contained widget cards, each showing one
   metric or view. Best for monitoring pages where you want to see many small
   things at once.
4. **timeline-centric** — a big horizontal timeline at the top or center, with
   synchronized detail views that update as you scrub. Best for event logs,
   video + telemetry sync, debug replay.
5. **single-canvas** — one dominant view (3D scene, map, graph) with minimal
   chrome. Best for interactive demos, pure visualization, customer-facing
   deliverables.

**Default:** infer from user's earlier description. If unclear, ask directly
with the five options as multi-choice. Don't default silently on this one —
the archetype determines which template is copied.

**Why this axis matters:** it determines the scaffold template and therefore
the overall structure of the output file. Getting it wrong means rewriting
from scratch later.

---

## Axis 3 — Interaction Model

**What does the user actually do with the dashboard?**

Menu (choose any that apply — usually 1–3):
- **Selection** — click an entity, see its details.
- **Brushing** — drag-select a range on a chart, filter other views.
- **Playback** — play/pause/scrub a time-indexed sequence.
- **Filter / search** — text or dropdown filters affecting all views.
- **Comparison** — overlay or side-by-side two or more items (run A vs. run B).
- **Read-only** — no interaction, just display.

**Default:** selection + filter/search for sidebar+main archetype; selection +
playback for split-pane+inspector; read-only for grid-of-cards.

**Why this axis matters:** it determines event wiring in the scaffold. Playback
needs a timer and state; comparison needs overlay logic; selection needs a
"currently-selected" store.

---

## Axis 4 — Visualization Widgets

**Which visual components are needed, and roughly how many of each?**

Menu (choose any that apply):
- **Line / scatter chart** — time series, loss curves, scatter plots.
- **3D scene** — simulation rendering (Three.js).
- **2D canvas / map** — 2D plots, trajectory overlays, Leaflet maps.
- **Data table** — sortable/filterable rows.
- **Heatmap / matrix** — confusion matrices, attention maps, grid data.
- **Image viewer** — sample images, predictions, rendered frames.
- **Log stream** — scrolling text log with optional color coding.
- **Key-value / property panel** — for detail/inspector views.
- **iframe embed** — TensorBoard, Grafana, etc.

Ask the user to roughly estimate count (1, 2–3, many) for each needed widget.
This determines whether to use a grid, tabs, or a single dominant area.

**Default:** line chart + key-value panel is the most common pair. For
training-metric dashboards, add iframe embed (TensorBoard). For simulation
playback, add 3D scene + log stream.

---

## Axis 5 — Tech Stack & Deployment

**How should the dashboard actually be built and run?**

Menu:
- **Single HTML file** — one `.html` with CDN scripts (Chart.js, Three.js).
  Open in browser, done. No build step, no server.
- **Static React app** — `vite` project, `npm run build`, deploy as static
  files. Needed if the component count is high or state management gets hairy.
- **React + FastAPI** — React frontend talking to a Python backend. Needed if
  data is too large to ship to the browser, or needs live auth.
- **Streamlit / Gradio** — Python-native dashboard frameworks. Faster to
  prototype than single-HTML for data-scientists-only audiences.

**Default:** single HTML. It's the lowest-friction option and fits 80% of
research use cases. Suggest React only if (a) there are 6+ interactive widgets,
(b) the user explicitly wants to iterate on it long-term, or (c) there's a team
handover planned.

**Why this axis matters:** it determines which archetype template to copy and
whether a build step is implied. Single HTML and React share archetype names
but have different templates.

---

## Axis 6 — Style & Branding

**What should it look like?**

Menu:
- **Theme:** dark / light / auto
- **Density:** compact (lots of info) / spacious (clean, demo-ready)
- **Branding:** none / company logo + colors (which?)
- **Live indicators:** pulsing dot / "last updated" timestamp / none

**Default:** dark + compact + no branding + "last updated" timestamp. Matches
the aesthetic of typical ML research dashboards (TensorBoard, W&B).

**Why this axis matters:** style is what makes the user feel ownership. Even
sensible defaults should be confirmed with the user — a 10-second choice here
saves a rewrite later.

---

## Interview Strategy

Don't mechanically ask six separate questions. Instead:

1. **Read the user's context first.** If they've already described the use case
   in earlier messages, prefill what you can and only ask about the gaps.
2. **Use `AskUserQuestion` with multiple questions in one call.** This batches
   the interview into one turn and makes it feel less like an interrogation.
3. **Offer a "use defaults" escape hatch.** One of the multi-choice options for
   each axis should effectively be "sensible default, just pick for me".
4. **Stop early if confident.** If answers to axes 1–3 fully determine 4–6 (they
   often do), skip the rest. A 3-question interview that produces a correct
   spec is better than a 6-question interview that loses the user's attention.
