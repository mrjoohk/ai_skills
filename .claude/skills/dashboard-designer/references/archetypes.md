# Layout Archetypes

Five layouts cover the vast majority of research/engineering dashboards. Pick
the one that matches the user's **dominant interaction pattern**, not the one
that matches the number of widgets. A page with many widgets can still be
sidebar+main; a page with few widgets can still be split-pane+inspector if
clicking-to-inspect is the core flow.

Only two archetypes (#1 and #2) ship with ready-made HTML templates. The
others are documented here so the skill knows when to recommend them — if the
user picks #3, #4, or #5, the skill should emit a spec document but tell the
user that template generation for that archetype isn't bundled yet, and offer
to hand-write the scaffold or fall back to the closest bundled archetype.

---

## 1. sidebar+main (+tabs)  —  template: `single-html-tabbed/`

```
┌────────────┬──────────────────────────────┐
│  sidebar   │  header                      │
│            ├──────────────────────────────┤
│  [run A]   │  [tab1] [tab2] [tab3]        │
│  [run B]   ├──────────────────────────────┤
│  [run C]   │                              │
│            │       main content area      │
│            │                              │
└────────────┴──────────────────────────────┘
```

**When it fits:**
- User picks one entity from a list (run, experiment, model) → sees many views
  of that entity.
- Views are organized into categories (metrics / logs / artifacts / config).
- External tool embedding (TensorBoard, MLflow) fits naturally as a dedicated
  tab.

**Typical widgets:** line charts, data tables, iframe embeds, log streams,
key-value config panels.

**Typical interactions:** selection (pick run from sidebar), filter (search
runs), comparison (multi-select in sidebar overlays on charts).

**Real examples:** TensorBoard, Weights & Biases, MLflow UI, experiment
trackers in general.

---

## 2. split-pane+inspector  —  template: `split-pane-inspector/`

```
┌────────────────────────────┬──────────────┐
│  header / playback         │              │
├────────────────────────────┤  inspector   │
│                            │              │
│     primary canvas         │  (details of │
│   (3D scene / timeline /   │   selected   │
│    map / graph)            │   object)    │
│                            │              │
│                            │              │
└────────────────────────────┴──────────────┘
```

**When it fits:**
- There's one dominant visualization (3D scene, map, scene graph) that the
  user spends 80% of their time looking at.
- Clicking on objects in the dominant view should reveal properties/metadata.
- Playback or timeline scrubbing is involved.

**Typical widgets:** 3D scene (Three.js), 2D canvas, timeline/playback bar,
property panel, log stream.

**Typical interactions:** selection (click to inspect), playback (time
scrubbing), filter (toggle layers on/off).

**Real examples:** Unreal Insights, Chrome DevTools Performance tab, RViz,
CARLA's replay UI, game replay viewers.

---

## 3. grid-of-cards  —  template: *(not bundled)*

```
┌───────┬───────┬───────┬───────┐
│  A    │  B    │  C    │  D    │
├───────┼───────┼───────┼───────┤
│  E    │  F    │  G    │  H    │
└───────┴───────┴───────┴───────┘
```

**When it fits:**
- Monitoring multiple independent signals, each deserving its own card.
- User wants to glance at all of them, not drill into one.
- Cards are largely read-only.

**Typical widgets:** single-number KPIs, sparklines, small gauges, traffic
lights.

**Real examples:** Grafana/Datadog dashboards, status pages, live ops
monitoring.

**Fallback:** if the user picks this but no template exists, suggest Grafana
or Streamlit — those tools do this better than hand-rolled HTML.

---

## 4. timeline-centric  —  template: *(not bundled)*

```
┌──────────────────────────────────────────┐
│             details / charts             │
├──────────────────────────────────────────┤
│  ═══════════════▶═══════════════════════ │  ← timeline scrubber
├──────────────────────────────────────────┤
│  video / canvas / synced secondary view  │
└──────────────────────────────────────────┘
```

**When it fits:**
- Everything in the dashboard is synchronized to a single timeline.
- Events, logs, video, telemetry are all views of the same temporal sequence.

**Typical widgets:** video player, event markers, synchronized charts, log
stream pinned to current time.

**Real examples:** Chrome DevTools Performance, video annotation tools,
driving-log replay tools.

**Fallback:** the split-pane+inspector archetype with a timeline in the top bar
covers a lot of this ground. Consider whether that's close enough.

---

## 5. single-canvas  —  template: *(not bundled)*

```
┌──────────────────────────────────────────┐
│                                          │
│                                          │
│           full-bleed canvas              │
│            (3D / map / graph)            │
│                                          │
│                                          │
└──────────────────────────────────────────┘
```

**When it fits:**
- Pure visualization, minimal chrome.
- Demo / customer-facing / showcase context.
- User wants maximum pixel budget for the visual itself.

**Typical widgets:** one dominant canvas + optional floating controls.

**Real examples:** Kepler.gl standalone view, many physics simulation demos,
WebGL showcase pages.

**Fallback:** split-pane+inspector with the inspector collapsed/hidden by
default is very close. Consider whether that's close enough.

---

## Archetype Selection Cheat Sheet

Given the user's description, match to archetype:

| User says... | Archetype |
|---|---|
| "see training metrics, compare runs, embed TensorBoard" | 1. sidebar+main |
| "replay simulation, click objects for details" | 2. split-pane+inspector |
| "monitor a fleet / many servers / many signals at a glance" | 3. grid-of-cards |
| "sync video + telemetry + events on one timeline" | 4. timeline-centric |
| "interactive demo / showcase / immersive view" | 5. single-canvas |

If the user's description spans multiple archetypes, ask them which interaction
dominates — that picks the archetype. Dashboards that try to be everything end
up being nothing.
