# Widget Catalog

Reference for the visualization widgets available in the bundled archetypes,
and for external-tool integrations (TensorBoard, MLflow, Grafana). For each
widget: which library is used in the template, what data shape it expects,
and what customization knobs are exposed.

Use this during Phase B (spec writing) to fill in the "widgets" section with
concrete data-binding contracts. Use it during Phase C (scaffolding) to know
what to wire into the template.

---

## Charts (Chart.js)

Both bundled archetypes use **Chart.js** via CDN because it's small, zero-build,
and handles the common cases (line, scatter, bar) without ceremony. For more
advanced needs (interactive brushing, large N, custom rendering), mark as a
TODO in the spec and suggest Plotly or D3 in the implementation pass.

**Line chart**
- Expected data: `[{ x: number, y: number }, ...]` (or `{labels: [], datasets: [{data: []}]}`)
- Typical use: loss / accuracy / reward over training steps.
- Customization: multiple datasets for run comparison, log/linear Y axis,
  optional smoothing (EMA).

**Scatter chart**
- Expected data: `[{ x: number, y: number, label?: string }, ...]`
- Typical use: embedding projections, hyperparameter-vs-metric scatters.

**Bar chart**
- Expected data: `[{ label: string, value: number }, ...]`
- Typical use: metric summaries, final-epoch comparisons.

---

## 3D Scene (Three.js)

Used in the split-pane-inspector archetype. Loaded from CDN.

- Expected data: a scene description — typically `{ objects: [{ id, type, position, rotation, scale, meta }], camera: {...} }`.
- Each object gets a raycastable mesh; clicking fires a selection event that
  the inspector panel listens to.
- Customization: orbit vs. first-person controls, layer toggles, per-object
  highlight on hover.

**Do not** write a full physics / scene-graph system in the scaffold. Keep the
scene minimal (cubes + spheres as placeholders) and mark the actual object
loading as a TODO — the real project will have its own scene format.

---

## Data Table

Plain HTML tables with a tiny amount of JS for sort + filter. No library needed
below ~10k rows. Above that, suggest using a virtualized table (TanStack
Table, AG Grid) in the implementation pass.

- Expected data: `[{ col1: ..., col2: ... }, ...]`
- Customization: column headers, sort direction, filter input above the table.

---

## Log Stream

Scrolling `<div>` with monospace text. Auto-scrolls to bottom unless the user
has scrolled up (standard log-viewer UX).

- Expected data: `[{ timestamp, level, message }, ...]` or a stream of the same.
- Customization: color coding by level (INFO / WARN / ERROR), filter by level,
  search box.

---

## Property / Key-Value Panel

Used in the inspector panel of split-pane-inspector archetype. Plain HTML
list of `<dt>/<dd>` pairs.

- Expected data: `Record<string, any>` where values are strings/numbers/booleans.
- Customization: grouping (sections with headers), expand/collapse for nested
  objects.

---

## Timeline / Playback Bar

Slider + play/pause buttons + current-time indicator. Built with a range
`<input>` and a few buttons — no library.

- Expected data: `{ start: number, end: number, current: number }` and a
  callback on change.
- Customization: speed multiplier, keyframe markers, loop toggle.

---

## iframe Embed (TensorBoard, Grafana, MLflow, custom)

The simplest and most powerful widget — just an `<iframe>` pointed at an
external URL. Works inside any archetype; especially natural as a dedicated
tab in the sidebar+main archetype.

**TensorBoard**
- Start TensorBoard: `tensorboard --logdir=<path> --port=6006 --bind_all`.
- Embed URL: `http://localhost:6006` (or wherever it's served).
- **Gotcha:** TensorBoard sends `X-Frame-Options: SAMEORIGIN` by default. The
  scaffold should include a note telling the user to run with
  `--load_fast=false` or a reverse proxy strip. A simpler workaround is
  opening TensorBoard in a new tab instead of embedding — the scaffold should
  support both and let the user choose.

**MLflow**
- Start: `mlflow ui --port 5000`.
- Same iframe headers gotcha as TensorBoard. Same workaround options.

**Grafana**
- Usually already running on a known URL. Embed works cleanly if Grafana's
  `allow_embedding = true` is set.

**Custom**
- Any URL. Just make sure the source sends the right headers or you're on
  the same origin.

For the spec document, record: (a) which tool, (b) the URL or how to start it,
(c) whether to iframe-embed or open-in-new-tab.

---

## Adding a New Widget

Don't extend the catalog speculatively. Add a widget here only when a real
project needs it and the bundled archetype templates are updated to include
it. Every entry in this file should correspond to an actual, tested snippet
in the templates.
