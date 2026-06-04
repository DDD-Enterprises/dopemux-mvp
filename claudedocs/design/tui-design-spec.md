# Unified Cockpit TUI — Design Specification

**Version:** v0.1.0 · **Date:** 2026-06-04 · **Palette:** Direction B Electric Refresh
**Status:** Design spec — drives Claude Design mockups + a later implementation packet. No runtime code changes.

---

## 1. Purpose & authority inheritance

This spec consolidates the three overlapping TUI surfaces in the repo —
`tui/app.py` (OrchestratorTUI grid), `ui/dashboard.py` (DopemuxDashboard HUD), and
`ui/cockpit/` (CockpitApp) — into **one governed cockpit** under the existing
**Dopemux Cockpit TUI Design System** (`docs/03-reference/Dopemux Cockpit TUI Design System/`).

It does **not** restate or fork the existing laws. It **cites and obeys** them:

- **Authority model + Pane Declaration Law** — every pane declares `domain / authority / role /
  next_action`. Source: `ARCHITECTURE_SAFETY_OVERLAY.md`; encoded in
  `src/dopemux/ui/cockpit/render.py::PaneDeclaration`.
- **SRC / provenance law** — every *data* row carries `SRC=<service>`; chrome (header, mode bar,
  command rail, status rail) never does. `SRC=dopemux` is forbidden on canonical data.
- **Bridge law** — `dopecon-bridge` adapter/proxy surfaces are visually segregated, labeled
  `adapter-only segregated`, never canonical authority, never a peer pane at small viewports.
- **Closed chip set** — `LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE`. No other chip
  exists. `UNKNOWN` stays literal text, never a chip. Web-equivalent mapping:
  `DEGRADED→OVERRIDE`, `FAILED→BLOCKER`, `BLOCKED→BLOCKER`, `SYNC→AFTERCARE`.
- **Viewports** — `120×40` (north star) / `100×32` / `80×24`; below `80×24` renders a `[BLOCKER]`.
  Fixed coordinates from `cockpit/frame.py::Layout`.
- **Vocabulary + render gate** — forbidden words/chips enforced by
  `cockpit/tokens.py::validate_rendered_text`; no emoji; `->` not `→`.
- **Type** — Iosevka Hue Term mono, single weight/size per viewport; emphasis is bold + color,
  never size. Box-drawing grid; hard corners (`┏ ┓ ┗ ┛`); no rounded corners, gradients, blur,
  mouse, or hover.
- **Palette** — Direction B from `claudedocs/design/tokens.json`. Color encodes state, never
  decoration; **color-never-alone** (every status carries glyph + literal label so `NO_COLOR=1`
  preserves all signal).

> **Truth order:** runtime outranks docs. Where this spec and shipped runtime (`render.py`)
> disagree, runtime wins and this spec is corrected.

---

## 2. Information architecture

### 2.1 Modes (the existing closed set of five)

`PM | Implementer | Overview | Services | Events` — from `render.py::TOP_LEVEL_MODES` and
`runtime_contract.py::TOP_LEVEL_MODES`. The mode bar is chrome (no SRC). Active mode:
`[ PM ]`; inactive: `  Implementer  `.

### 2.2 Global surfaces (from `runtime_contract.py::GLOBAL_SURFACES`)

`Command Palette` (`ctrl+k`) · `Settings/Admin/Runtime` · `Safe Actions / Proof Gate` ·
`Unknown / Drift Queue`. These overlay any mode; they are not modes.

### 2.3 The unification mapping (spine)

Every existing **real** surface is placed into the IA. This table is the core design decision.

| Existing surface | Real data source (verified) | Mode | Pane role |
|---|---|---|---|
| `packets` (`task-packets/generated/*.json`) | filesystem | **PM** | canonical — readiness queue feed |
| `pr_queue` (`build_pr_queue` → GitHub) | github | **PM** | derived — review queue |
| `today` (ConPort active tasks) | ConPort SQLite | **Overview** | derived — daily plan |
| `ProductivityPanel` (tasks/velocity) | ConPort progress | **Overview** | derived |
| `proof` (`proof/**/*.json`) | filesystem | **Implementer** | canonical — handback/proof |
| `context` (dope-context freshness) | dope-context | **Implementer** | derived — evidence freshness |
| `ServicesGrid` + `HealthChecker.check_all` | health endpoints + psutil | **Services** | canonical — service health |
| `authority` (approval policy classification) | policy file | **Services** | derived — capability tiers |
| `risks` (TX/TU/T6 elevated capabilities) | `orchestrator.policy` | **Services** | derived — security risks |
| `do_not_touch` (refusal matrix) | `orchestrator.policy` | **Services** | derived — forbidden set |
| native_hooks activity | Redis `dopemux:events` | **Events** | canonical — live feed |
| `workspace.switched` (workspace-watcher) | Redis `dopemux:events` | **Events** | canonical — live feed |
| `ADHDStatePanel` (energy/attention/load) | adhd-engine (advisory) | status rail cue + **Overview** | advisory — never a gate |

All 8 OrchestratorTUI panels and all 4 DopemuxDashboard panels are accounted for.

---

## 3. Architecture decisions (stated, not implicit)

1. **Snapshot-on-refresh vs live-reactive.** PM / Implementer / Overview / Services render as
   **deterministic snapshots** (pure render + manual `r` refresh + optional slow interval),
   preserving `render.py`'s pure contract and testability. **Events** is the single
   **live-reactive** surface — it is an event stream. The ADHD advisory cue polls slowly. This
   honors "static snapshot renderer by design" while letting the one genuinely-live mode stream.

2. **Non-uniform mode depth (honest by design).** Spec depth tracks where real data + real
   workflows exist. **PM** and **Services** get full pane-by-pane designs (all data real today).
   **Implementer** gets a full design — `proof/`, `context`, `packets` are real — elevated from its
   current `[EDGE]` stub. **Overview** gets a medium design (ConPort + advisory). **Events** gets a
   live-feed design. History/trends that are demo-only stay `[EDGE]`/direction, not invented.
   Uniform-shallow-across-five is rejected.

3. **One Textual App, mode bar switches body.** The design target replaces the three separate
   `App` subclasses (`OrchestratorTUI`, `DopemuxDashboard`, `CockpitApp`) with a single shell +
   mode bar. (Implementation is a later packet; this spec defines the target.)

---

## 4. Per-mode design

Layout regions reference `cockpit/frame.py::Layout` at 120×40: left divider col 25, right divider
col 84, inspector split row 22, center split row 25, body rule row 35, command row 36, status rule
row 37, status row 38, bottom row 39. Three columns: **left rail** (cols 1–24), **center**
(cols 26–83), **right inspector** (cols 85–120). Bottom: command rail then status rail.

Each pane below lists its four-field declaration, region, real source, SRC, and states.

### 4.1 PM — workflow adjudication (full; matches shipped `render_pm()`)

PM left rail is a **workflow/slice map** (not a service map). Center upper is the **readiness
queue**; center lower is **adjudication context**; inspector upper is **selected slice detail**;
inspector lower is **canonical actions** then the **hard-divided bridge segregator**.

| Pane | Declaration (`domain·authority·role·next_action`) | Region | Source · SRC |
|---|---|---|---|
| Workflow / slice map | `workflow_slice · task-orchestrator · derived · open` | left rail | task-orchestrator · `SRC=task-orchestrator` |
| Readiness queue | `readiness_queue · task-orchestrator · canonical · triage` | center upper | task-orchestrator + `packets` · `SRC=task-orchestrator` |
| Adjudication context | `adjudication · task-orchestrator · canonical · inspect` | center lower | per-row inline SRC (conport/dope-memory/leantime) |
| Selected slice detail | `slice_detail · task-orchestrator · canonical · inspect` | inspector upper | per-row inline SRC |
| Canonical actions | `decisions · conport · authoring · log_decision` | inspector lower-upper | conport · per-row SRC |
| Bridge segregator | `bridge_transport · dopecon-bridge · proxied · inspect_adapter_ref` | inspector lower-lower | `SRC=dopecon-bridge` · `[EDGE] adapter-only segregated` |

**Chip usage:** queue rows use `LIVE`/`LOGGED`/`EDGE`; legality shown as body text
(`legality=ok` / `legality=UNKNOWN`), blockers as integer counts. **PM forbidden patterns**
(carried from `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`): no unified mega-list as primary surface,
no single "PM save" affecting multiple authorities, no workflow mutation via bridge, no Leantime
shown as workflow authority, no service/system map as the PM left rail.

**States:** empty queue → `No work items ready for triage.` (literal, no apology). Source down →
`[BLOCKER]` pane with `Problem/Why/Fix/NEXT`. Unproven legality → literal `UNKNOWN`, never a chip.

### 4.2 Services — health & authority (full; all real today)

Left rail = service list. Center = selected service detail + RTE child surface. Inspector =
authority/risk lens.

| Pane | Declaration | Region | Source · SRC |
|---|---|---|---|
| Service health grid | `service_health · per-service · canonical · inspect` | center upper | `HealthChecker.check_all` + health endpoints · `SRC=<service>` per row |
| MCP server status | `mcp_runtime · per-mcp · canonical · inspect` | center upper | psutil/process + `dopemux mcp status` · per-row SRC |
| RTE child surface | `rte_runs · repo-truth-extractor · canonical · inspect` | center lower | RTE · `SRC=repo-truth-extractor` (declares own authority) |
| Authority / capability tiers | `authority · orchestrator.policy · derived · inspect` | inspector upper | policy · `SRC=orchestrator-policy` |
| Risks (TX/TU/T6) | `security_risk · orchestrator.policy · derived · inspect` | inspector lower-upper | policy · `SRC=orchestrator-policy` |
| Do-not-touch refusal set | `refusal · orchestrator.policy · derived · inspect` | inspector lower-lower | policy · `SRC=orchestrator-policy` |

**Health status language:** `healthy · degraded · blocked · unknown` as body text; chip column
maps `degraded→OVERRIDE`, `down→BLOCKER`, healthy→`LIVE`. Latency + `last_check` timestamp on every
row (time anchor law). A service that cannot prove status is labeled literal `unknown`.

### 4.3 Implementer — work contract & evidence (full; elevated from `[EDGE]`)

Left rail = work contract / support rail. Center upper = current task, next action, acceptance
subset, blockers. Center lower = evidence workspace (Top-3 + `more_count` + `next_token`).
Inspector = selected acceptance/evidence/proof; lower = canonical handback actions then bridge.

| Pane | Declaration | Region | Source · SRC |
|---|---|---|---|
| Work contract | `work_contract · task-orchestrator · derived · open` | left rail | task-orchestrator · `SRC=task-orchestrator` |
| Active task + next action | `active_task · task-orchestrator · canonical · advance` | center upper | task-orchestrator · `SRC=task-orchestrator` |
| Evidence workspace | `evidence · dope-context · derived · query` | center lower | dope-context (Top-3) · `SRC=dope-context` |
| Selected proof detail | `proof · filesystem · canonical · inspect` | inspector upper | `proof/**/*.json` · `SRC=proof-fs` |
| Handback actions | `handback · conport · authoring · log_progress` | inspector lower-upper | conport · per-row SRC |
| Bridge segregator | `bridge_transport · dopecon-bridge · proxied · inspect` | inspector lower-lower | `SRC=dopecon-bridge` |

**Implementer forbidden patterns:** retrieval console as primary surface; dope-context treated as
source-of-truth for acceptance/decisions; Serena treated as canonical (mark `UNKNOWN` unless
runtime-proven); PM metadata edits inside Implementer; workflow transitions via bridge.

### 4.4 Overview — daily operator orientation (medium)

Three stacked panes; no inspector authority claims (Overview is orientation, not adjudication).

| Pane | Declaration | Source · SRC |
|---|---|---|
| Today's plan | `today · conport · derived · open` | ConPort active tasks · `SRC=conport` |
| Productivity / velocity | `productivity · conport · derived · inspect` | ConPort progress · `SRC=conport` |
| ADHD advisory cue | `operator_support · adhd-engine · advisory · inspect` | adhd-engine · `SRC=adhd-engine` (see §5) |

Cognitive/velocity **history/trends** are demo-only today → render as `[EDGE]` direction with a
literal `historical trend data not wired` note. Do not draw fabricated sparklines.

### 4.5 Events — live activity feed (live-reactive; the streaming exception)

Single full-width scrolling feed of real events from Redis `dopemux:events`. Each row:
`<ts> [<CHIP>] <event_type> <subject> SRC=<source>`. Sources: `native_hooks`
(tool/prompt/session lifecycle), `workspace-watcher` (`workspace.switched`). Newest at top;
bounded to last N (stream is truncated to ~10k upstream). A `*WS STREAM` indicator in the status
rail shows live vs. stalled. Stream unavailable → `[BLOCKER] event stream unavailable` +
`Fix: start redis / event services.` This is the only mode that updates without `r`.

### 4.6 Global surfaces

- **Command Palette** (`ctrl+k`): fuzzy command list; each row carries `authority_domain` +
  `gate_tier`; non-executable/unknown rows stay visible but blocked (per `runtime_contract.py`).
- **Settings/Admin/Runtime**: tiered rows (T0–T6/TX/TU); per-row tier shown; unproven rows are
  literal `UNKNOWN` and route to the Unknown/Drift Queue. Confirmation strength per tier.
- **Safe Actions / Proof Gate**: tier-gated execution; refusal routes (`PARAM_UNRESOLVED`,
  `CWD_UNRESOLVED`, `REMOTE_MUTATION_POLICY_MISSING`, …) shown literally with `NEXT:`.
- **Unknown / Drift Queue**: aggregated unresolved rows; affordances limited to
  `Inspect · CopyEvidence · CopyRecommendedPacketPrompt · ShowBlockedReason · ShowUpstreamArtifact`.
  Never executes; never reclassifies at runtime.

---

## 5. ADHD signal pipeline — per-stage provenance (the explicit ask)

Honesty is labeled **per stage**, not per surface. The display layer is already honest
(`dashboard.py:142` sets `is_connected=False` on any error and renders a `[BLOCKER]` panel rather
than the seed defaults); the gap is provenance of the *value* when the endpoint returns 200.

| Stage | Component | Status | Note |
|---|---|---|---|
| 0 — raw signals | workspace-watcher (app focus 5s; file activity 30s window), native_hooks (Claude tool/prompt/session → Redis), Redis `session_start`/`last_break`, ConPort progress | **REAL when services up** | content-free, coarse (≥5s granularity) |
| 1 — aggregation | activity-capture 5-min windows → `completion_rate`, `context_switches`, `break_compliance`, `minutes_since_break` | `completion_rate` **REAL** · `minutes_since_break` **REAL** · `context_switches` **SYNTHETIC** (app-switch proxy, not code focus) · `break_compliance` **HEURISTIC** | |
| 2 — inference | adhd-engine heuristic blend (+ optional ML) → energy / attention / cognitive_load | **INFERRED**; monitor loops may be **unwired** in deployed runtime → a 200 can carry engine defaults | |
| 3 — display | `ADHDStatePanel.update_state` → cockpit advisory cue | **HONEST failure** (`[BLOCKER]` when endpoint down) but does **not** distinguish freshly-inferred vs engine-default when up | verified `dashboard.py:142` |

### 5.1 Design output

1. **Contract extension** — extend the engine `GET /api/v1/state` response with `confidence`
   (0.0–1.0), `inputs_present` (which Stage-1 inputs were real this sample), and `computed_at`
   (so staleness is detectable). Backward-compatible additive fields.
2. **Cockpit rendering** — the ADHD pane/cue renders `SRC=adhd-engine  role=advisory` +
   `confidence=<n>` + per-input provenance, and shows literal `UNKNOWN` when `computed_at` is stale
   or `confidence` absent. It is an **advisory cue only — never a gate** (authority law: ADHD Engine
   = advisory cues, never PM truth, never blocks operator action).
3. **Gap-closing roadmap (future packets, not faked here):**
   - emit a real `cognitive.state` event with `confidence` from the monitor loop (closes the
     "unwired monitor → engine default" gap);
   - replace the synthetic app-switch `context_switches` proxy with an **editor-focus**
     context-switch signal (code focus within an app);
   - add `computed_at`/staleness so the display can honestly degrade to `UNKNOWN`;
   - sub-second **flow / hyperfocus** detection requires IDE-level signals (cursor, dwell,
     unsaved-count) that **do not exist today** — marked **future**, never fabricated.

---

## 6. Visual language — Direction B on cockpit primitives

Tokens from `claudedocs/design/tokens.json`. Primitives from `ui_kits/cockpit/`
(Frame, PaneHeader, Rule, Chip, Row, ModeBar, CommandRail, StatusRail, Inspector,
BridgeSegregator, RunRow, ServiceRow).

| Element | Token | Hex |
|---|---|---|
| Window background | `base` | `#020617` |
| Inset row / selected row | `raised` | `#041628` |
| Frame / divider lines | `border_strong` | `#2E3F54` |
| Headings / brand mark / active mode | `brand` | `#2FFFF0` |
| `LIVE` chip + info | `info` | `#00E5FF` |
| `LOGGED` chip + success | `success` | `#00FF85` |
| `OVERRIDE` chip + warning | `warning` | `#FFE600` |
| `BLOCKER` chip + error | `error` | `#FF2255` |
| `AFTERCARE` chip | `aftercare` | `#C07BFF` |
| `EDGE` chip / inactive / unknown | `text_muted` | `#808DA0` |
| Brand accent (mark glow only, non-status) | `gremlin_pink` | `#FF00CC` |
| Primary text | `text_primary` | `#E2E8F0` |

**Chips** (closed set, glyph + label always):
`◉ LIVE` (info) · `⊘ BLOCKER` (error) · `⚠ OVERRIDE` (warning) · `✓ LOGGED` (success) ·
`◈ AFTERCARE` (aftercare) · `· EDGE` (muted). `NO_COLOR=1` keeps the literal label so signal
survives. Glyphs from `theme.py::Glyphs` with ASCII fallback.

**Type:** Iosevka Hue Term, 1 weight / 1 size per viewport; cells 1ch × 1.25em. Emphasis = bold +
color. **Box-drawing grid** `━ ┃ ┏ ┓ ┗ ┛ ┠ ┨ ┬ ┴ ┤ ├ │ ─`; brand mark `━━━◆ Ø ◆━━━`. No emoji,
no SVG, no rounded corners, no gradient, no shadow, no blur.

---

## 7. Viewport adaptation

| Size | left div | right div | inspector split | center split | body rule | cmd | status rule | status | bottom | Bridge placement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 120×40 | 25 | 84 | 22 | 25 | 35 | 36 | 37 | 38 | 39 | dedicated segregator pane |
| 100×32 | 21 | 70 | 17 | 19 | 27 | 28 | 29 | 30 | 31 | inspector lower-detail |
| 80×24 | 17 | 56 | 11 | 13 | 19 | 20 | 21 | 22 | 23 | collapsed inline (no peer pane) |

Structure is identical at all three; only column widths and rows-per-pane change. No mobile
cascade, no reflow. Below 80×24:

```
[BLOCKER] terminal size unsupported.
Problem: cockpit snapshot supports 120x40, 100x32, or 80x24.
Why:     layout invariants are size-bound.
Fix:     choose a supported size.
NEXT:    resize to at least 80x24.
```

---

## 8. Verification checklist

- [ ] Every pane carries a four-field declaration; every data row carries `SRC=`; chrome carries none.
- [ ] No forbidden chips/vocab (cross-check `cockpit/tokens.py::validate_rendered_text`).
- [ ] Mapping completeness: all 8 OrchestratorTUI + 4 DopemuxDashboard panels placed with a real source.
- [ ] Every color reference resolves to a `tokens.json` Direction B token; ANSI anchors preserved;
      color-never-alone (glyph + label) on every status.
- [ ] ADHD pipeline: each stage labeled REAL/SYNTHETIC/HEURISTIC/INFERRED/UNKNOWN; advisory-not-gate
      stated; no stage claims unearned certainty.
- [ ] PM section reconciled against shipped `render_pm()` text (runtime outranks docs).
- [ ] Bridge segregated and labeled `adapter-only segregated` at every viewport; no peer placement
      at 80×24.
- [ ] Sub-80×24 BLOCKER copy present with Problem/Why/Fix/NEXT.

---

## 9. Out of scope (separate packets)

- Collapsing the three `App` subclasses into one shell (implementation).
- Elevating Implementer/Overview/Events from `[EDGE]` in `render.py` (implementation).
- The adhd-engine `/api/v1/state` contract extension (`confidence`/`inputs_present`/`computed_at`).
- Editor-focus context-switch signal + `cognitive.state` event emission.
