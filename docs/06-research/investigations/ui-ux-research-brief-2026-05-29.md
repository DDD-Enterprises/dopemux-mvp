---
id: ui-ux-research-brief-2026-05-29
title: "Dopemux UI/UX Research Brief (D2) — 2026-05-29"
type: explanation
owner: brand-system
author: '@hu3mann'
date: 2026-05-29
last_review: '2026-05-29'
next_review: '2026-08-29'
status: draft
prelude: "Research brief feeding the dopemux cockpit redesign (D3): terminal data-viz + Textual capabilities, exemplar TUIs, ADHD-in-terminal patterns, tmux UX, and terminal accessibility. PARTIAL pending stream re-run."
---

The advisor confirms: honest-partial is the correct, in-scope move. Four streams returned literal `API Error` strings — fabricating findings or URLs for them violates the doctrine. Stream 4 (dataviz + Textual) is genuinely rich and gets full treatment. I'll write the deliverable now.

# Dopemux UI/UX Research Brief — D2

**Target:** terminal-first ADHD cockpit redesign · feeds design spec D3
**Date:** 2026-05-29 · **Status:** PARTIAL (see provenance)

---

> ## ⚠️ Provenance / data-integrity note
>
> This brief was to synthesize **five** research streams. **Only one (Stream 4: dataviz-textual) returned data.** The other four returned literal `API Error` strings (server-side rate-limiting that hit all parallel streams):
>
> | Stream | Topic | Status |
> |---|---|---|
> | 1 | exemplar-tuis | ❌ rate-limited — zero content |
> | 2 | adhd-terminal | ❌ rate-limited — zero content |
> | 3 | tmux-ux | ❌ rate-limited — zero content |
> | 4 | dataviz-textual | ✅ delivered (high confidence, primary-source-grounded) |
> | 5 | a11y-terminal | ❌ rate-limited — zero content |
>
> **Doctrine: fail closed.** Sections fed by failed streams are marked `NOT_SYNTHESIZED` rather than backfilled — writing "citation-rich" findings for content we never received would mean fabricating sources. **The four failed streams are the single largest open item** (see §8). Re-run them and re-issue this brief before D3 treats §2/§3/§4/§6 as settled.

---

## 1. Executive summary

**Scope caveat:** these findings derive **only** from Stream 4 (terminal data-viz + the Textual framework). High-leverage findings for cockpit IA & navigation, ADHD-in-terminal behavior, tmux integration, and accessibility are **pending stream re-run** and are not represented below.

The 8 highest-leverage findings we *can* stand behind:

1. **Motion policy is enforceable at the framework level, not by convention.** Textual exposes a global three-level switch `TEXTUAL_ANIMATIONS = none|basic|full` plus a per-animation `level=` gate ("minimum level required for the animation to take place"). Ship the cockpit at `basic`, tag every non-essential motion `level="full"`, and it is *automatically suppressed* unless the user opts in ([constants API](https://textual.textualize.io/api/constants/), [types API](https://textual.textualize.io/api/types/), [widget API](https://textual.textualize.io/api/widget/)).
2. **"Animation-free deterministic core" = `TEXTUAL_ANIMATIONS=none` + `TEXTUAL_SMOOTH_SCROLL=0` + no indeterminate progress bars.** This makes UI output a pure function of state — the precondition for snapshot/determinism testing ([constants API](https://textual.textualize.io/api/constants/), [ProgressBar](https://textual.textualize.io/widgets/progress_bar/)).
3. **The cheap-vs-costly render ladder is explicit.** Plain refresh (cheap, repaint within bounds) → `reactive(layout=True)` (costly, full CSS layout recalc) → `reactive(recompose=True)` (heaviest, tears down child widgets; unsafe for `DataTable`/`Input`) ([Reactivity guide](https://textual.textualize.io/guide/reactivity/)).
4. **The compositor does region-based partial updates** keyed off a 100×20 spatial map, so widget count barely affects redraw cost — *provided you stay off the relayout/recompose path* ([rendering algorithms blog](https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/)).
5. **`RichLog` is the idiomatic signal-feed primitive** — append-only, `auto_scroll`, `max_lines` ring-buffer for bounded memory, accepts styled Rich renderables per line. `Log` for plain text only ([RichLog](https://textual.textualize.io/widgets/rich_log/)).
6. **There is NO native gauge widget — it must be composed** (subclass `ProgressBar` with a fixed `total`, or render block chars in a `Static`). Any "use the built-in gauge" assumption in D3 is wrong ([ProgressBar](https://textual.textualize.io/widgets/progress_bar/)).
7. **Block-glyph alignment is a real hazard for a dense, alignment-critical brand.** `▁`/`█` render narrower than the rest; `▄`/`█` drop below baseline in some fonts. Jitter averages out over *long* sparklines, breaks *short* ones. Pin and verify the Nerd Font ([Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/), [cli.r-lib](https://cli.r-lib.org/reference/spark_bar.html)).
8. **Live data must run on workers, never the event loop.** `@work(exclusive=True)` cancels the prior worker — the canonical fix for out-of-order responses on live feeds ([Workers guide](https://textual.textualize.io/guide/workers/)).

---

## 2. Exemplar TUI patterns

**`NOT_SYNTHESIZED` — Stream 1 (exemplar-tuis) returned `API Error: Rate limited`. Zero content received.**

This section was scoped to identify specific best-in-class TUI tools as evidence for cockpit patterns. **No tools were surveyed; no patterns can be cited without fabricating sources.** Re-run Stream 1 before D3 relies on exemplar evidence.

---

## 3. ADHD-in-terminal patterns

**`NOT_SYNTHESIZED` — Stream 2 (adhd-terminal) returned `API Error: Server is temporarily limiting requests · Rate limited`. Zero content received.**

This section was scoped to cover ADHD-specific terminal interaction patterns **and the static-TUI-vs-rich-surface tension**. **No findings were received.** The static-vs-rich tension is partially addressable from Stream 4's motion/cost model (see §5/§7B), but the ADHD behavioral grounding is missing and must not be invented. Re-run Stream 2.

---

## 4. tmux cockpit patterns

**`NOT_SYNTHESIZED` — Stream 3 (tmux-ux) returned `API Error: Server is temporarily limiting requests · Rate limited`. Zero content received.**

This section was scoped to cover tmux-based cockpit/shell patterns (pane layout, session orchestration, status-line use). **No findings were received.** Re-run Stream 3.

---

## 5. Terminal data-viz + Textual capabilities

*(Full synthesis — Stream 4. Confidence: High on Textual mechanics, all load-bearing claims fetched from primary docs/API pages; Medium where cost is inferred from architecture — flagged inline.)*

### 5.1 Dense-data display in monospaced terminals

**Sparklines.** Per inventor Edward Tufte, a sparkline is "a small, intense, simple, word-sized graphic with typographic resolution" — meant to sit inline, "everywhere a word or number can be" ([deeplook/sparklines](https://github.com/deeplook/sparklines), [Tufte via QuestDB](https://questdb.com/blog/sparklines-candlesticks-depth-charts-sql/)). In a terminal this maps onto the eight Unicode lower-block chars `▁▂▃▄▅▆▇█` (U+2581–U+2588) — eight quantization buckets per monospace cell ([Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/), [Rosetta Code](https://rosettacode.org/wiki/Sparkline_in_unicode)). The selling point is portability: it is just text, so it sorts and lives inside table cells ([Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/)).

**The glyph-alignment hazard (the single most important practical caveat for a dense, deterministic, alignment-critical brand):**

| Glyph issue | Detail | Source |
|---|---|---|
| Width jitter | `▁` (U+2581) and `█` (U+2588) render **narrower** than the rest in many fonts | [Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/) |
| Baseline drop | `▄` (U+2584) and `█` (U+2588) **drop below baseline** in some monospace fonts | [Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/) |
| General caution | In most fixed-width fonts these are "rendered wider than regular characters … not suitable if you need precise alignment" | [cli.r-lib spark_bar](https://cli.r-lib.org/reference/spark_bar.html) |
| Long vs short | Jitter **averages out** over long strings (negligible); over **short** strings it's "a deal breaker" (Udell dropped to a 5-char subset) | [Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/) |
| Implementation gotchas | Guard divide-by-zero when all values equal (`if extent == 0: extent = 1`); lowest bucket is ambiguous between space and `▁` | [Udell](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/), [sparklines PyPI](https://pypi.org/project/sparklines/) |

**Block vs braille — two precision/alignment trade-offs:**

| Technique | Resolution/cell | Best for | Alignment risk |
|---|---|---|---|
| **Block** `▁▂▃▄▅▆▇█` | 8 vertical levels, 1 col | Sparklines, gauges, level meters | Width/baseline jitter on `▁▄█` |
| **Quadrants / half-blocks** | 2×2 or 1×2 sub-cell | Coarse line/scatter | Lower jitter, lower resolution |
| **Braille** (U+2800) | **2×4 = 8 dots/cell** | High-res line/scatter | Dots uniform; renders as true grid |

Braille packs a 2×4 dot matrix per cell (~8× the effective resolution; "reduce the line thickness and improve the resolution tremendously") ([textual-plot README](https://github.com/davidfokkema/textual-plot)). [plotille](https://pypi.org/project/plotille/) is the canonical dependency-free braille plotter.

**Rule of thumb:** block chars for *word-sized, fixed-width* indicators (gauges, sparklines, level bars) that must column-align; braille for *larger XY plots* (latency/throughput over time) where line fidelity matters and the plot owns its rectangle.

**Standalone plotting libs:**
- **plotext** — matplotlib-like: scatter, line, bar, histogram, date-time, candlestick, error bars ([plotext repo](https://github.com/piccolomo/plotext)). **Recency correction:** a search snippet claimed "not updated since 2024"; the repo's latest concrete release is **v5.2.8, dated Oct 30 2022**. Honest statement: "last release ~3.5 years ago; maintenance slow."
- **plotille** — braille plots/histograms/heatmaps, zero deps ([plotille PyPI](https://pypi.org/project/plotille/)).

Neither is Textual-aware on its own (see 5.7).

### 5.2 The Textual framework — render/refresh model

Textual is built **on top of Rich**; Rich emits `Segment`s, Textual's compositor consumes them ([rendering algorithms blog](https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/)). Practical consequence: **Rich renderables work inside Textual, but Textual's own widgets supersede Rich primitives for app-building** — reach for Rich `Text` (styled cells) and renderables inside `RichLog`, but build the UI from `DataTable`/`Static`+borders/`ProgressBar`, not Rich `Table`/`Panel`/`Progress`.

**The cheap-vs-costly cost ladder (the core answer), from the reactivity guide:**

| Tier | Mechanism | Cost | Notes |
|---|---|---|---|
| 1 | Plain refresh / `reactive()` default | **Cheapest** | Re-runs `render()`, updates content within existing bounds; no relayout |
| 2 | `reactive(layout=True)` | More expensive | "Forces a complete CSS layout recalculation … recalculates dimensions and positioning" |
| 3 | `reactive(recompose=True)` | **Heaviest** | "Removes all the child widgets and calls `compose()` again"; explicitly "unsuitable for stateful child widgets like `Input` or `DataTable`" |

([Reactivity guide](https://textual.textualize.io/guide/reactivity/))

Other lifecycle hooks: `validate_*` (coerce/clamp), `watch_*(old, new)` (fires only on actual change unless `always_update=True`), `compute_*` (cached derived values), `var()` (reactive *without* triggering render), `data_bind()` (one-way parent→child) ([Reactivity guide](https://textual.textualize.io/guide/reactivity/)).

**Why this answers cheap-vs-costly:** the compositor does region-based partial updates — "if you click a button and it changes color, the compositor can update just the region occupied by the button" ([rendering algorithms blog](https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/)). A repaint of a fixed-size widget is a small localized segment-diff; a relayout (`layout=True`) invalidates positions and re-composites more broadly. *(Inference flag: the docs separately state relayout is "more expensive" / "recalculates dimensions and positioning" and that the compositor does partial updates — joining those two documented facts into "relayout is heavier because it invalidates the spatial map / positions" is synthesis, not a verbatim quote.)* The compositor's scaling trick: a **100×20 spatial map** so "as the number of widgets increases, the time it takes to figure out which are visible stays relatively constant" ([rendering algorithms blog](https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/)). Max frame rate: `MAX_FPS` default **60** (env `TEXTUAL_FPS`) ([constants API](https://textual.textualize.io/api/constants/)).

### 5.3 Animation — and the motion-policy switch

Animation is via `animate()` on apps/widgets/styles (e.g. `offset`, `opacity`): params `duration`/`speed`/`easing` (default `in_out_cubic`)/`delay`/`on_complete` ([Animation guide](https://textual.textualize.io/guide/animation/)). TCSS transitions also exist (`.tcss` stylesheets; web-CSS-like syntax) ([Textual CSS guide](https://textual.textualize.io/guide/CSS/)).

**The load-bearing mechanism — a global three-level switch plus a per-animation gate:**

| Control | Value/behavior | Source |
|---|---|---|
| `TEXTUAL_ANIMATIONS` env var | "Determines whether animations run or not" | [constants API](https://textual.textualize.io/api/constants/) |
| `AnimationLevel` | `Literal['none','basic','full']` | [types API](https://textual.textualize.io/api/types/) |
| `App.animation_level` | Reflects the env var; "determines what type of animations the app will display" | [app API](https://textual.textualize.io/api/app/) |
| `Widget.animate(..., level=)` | "**Minimum level required for the animation to take place (inclusive)**"; `App.animate()` default `"full"` | [widget API](https://textual.textualize.io/api/widget/), [app API](https://textual.textualize.io/api/app/) |

So the policy is two-sided: **globally** run at `basic` (or `none`); **per animation** tag non-essential motion `level="full"` (auto-suppressed below full) and orientation cues `level="basic"`.

**Other time-based motions to disable for a deterministic core:**
- `TEXTUAL_SMOOTH_SCROLL` (default on) → set `0` ([constants API](https://textual.textualize.io/api/constants/)).
- Indeterminate `ProgressBar` shows a "pulsing animation" when `total=None` — avoid in static core ([ProgressBar](https://textual.textualize.io/widgets/progress_bar/)).

*(Synthesis flag: the "determinism ⇒ disable time-based motion" rationale is mine; the docs supply the mechanism, not the reasoning.)*

### 5.4 Workers & async

Live data must not block the event loop. `run_worker()` / `@work` spawn background coroutines; **async workers** (default) suit async APIs (`httpx`), **thread workers** (`thread=True`) suit blocking calls but must use `App.call_from_thread()`. `@work(exclusive=True)` cancels the prior worker (fixes out-of-order responses / search-as-you-type). Workers expose `state` (`PENDING/RUNNING/CANCELLED/ERROR/SUCCESS`) and emit `Worker.StateChanged` ([Workers guide](https://textual.textualize.io/guide/workers/)).

### 5.5 Screens & modes (spatial structure)

Screens are a **stack** — `push_screen`/`pop_screen`/`switch_screen`; only the top is active ([Screens guide](https://textual.textualize.io/guide/screens/)). `ModalScreen` blocks app-level bindings and sets an alpha background so the screen beneath shows through. **Modes** are *independent* screen stacks switched via `switch_mode('name')`, declared in `MODES` with `DEFAULT_MODE` — a clean fit for cockpit "workspaces" (RUN/AUDIT/PLAN), each preserving its own nav history. Events: `ScreenSuspend`/`ScreenResume`. **No built-in push/pop transition animation defaults** — any screen-change motion is opt-in (and gate it by level) ([Screens guide](https://textual.textualize.io/guide/screens/)).

### 5.6 Widget primitives (the cockpit building blocks)

| Widget | Key API | Cockpit use | Source |
|---|---|---|---|
| **`DataTable`** | `add/update_cell`, `cursor_type` (`cell/row/column/none`), `fixed_rows`/`fixed_columns`, `zebra_stripes`, cells accept **Rich `Text`**, `sort()`, `refresh_row()`/`refresh_coordinate()` (cheap partial repaint) | Signal/status tables; color chips as Rich `Text` in cells | [DataTable](https://textual.textualize.io/widgets/data_table/) |
| **`Sparkline`** | reactive `data`, `summary_function` (default `max`), **bar count = widget width in cells**, renders `▁▂▃▄▅▆▇█`; component classes `sparkline--max-color`/`--min-color` (color **interpolated** by value; affect `color` only) | Inline trend/spike indicators | [Sparkline](https://textual.textualize.io/widgets/sparkline/) |
| **`ProgressBar`** | reactive `progress`/`total`/`percentage`; `advance()`, `update()`; sub-widgets `#bar`/`#percentage`/`#eta`; classes `.bar--bar`/`.bar--complete`/`.bar--indeterminate`; **`total=None` → indeterminate pulse** | Compose into gauge (fixed `total`) | [ProgressBar](https://textual.textualize.io/widgets/progress_bar/) |
| **`Tree`** | `add()`/`add_leaf()`, `expand/collapse/toggle`, `show_root`, `show_guides`, `guide_depth` (def 4); events `NodeExpanded/Collapsed/Highlighted/Selected`; classes `tree--guides/--label/--cursor` | Task trees, dependency graphs | [Tree](https://textual.textualize.io/widgets/tree/) |
| **`RichLog`** | "scrollable content appended in realtime"; `write()` (Rich renderables *or* strings), `auto_scroll` (def True), `max_lines` (ring buffer), `markup`, `highlight`, `wrap`; sibling **`Log`** = plain text only | **Signal feed** ("tail -f" feel) | [RichLog](https://textual.textualize.io/widgets/rich_log/) |

TCSS theming hook points are widget **component classes** (`sparkline--max-color`, `bar--complete`, `tree--cursor`) — where mint-on-navy + the closed chip palette get encoded as tokens ([Textual CSS guide](https://textual.textualize.io/guide/CSS/)).

### 5.7 Plotting inside Textual — two routes

| Route | What it is | Best when | Caveat |
|---|---|---|---|
| **`textual-plotext`** | Textualize-**official** plotext wrapper; one `PlotextPlot` widget exposing `plt`; ships `textual-` themes, auto-switches light/dark (`auto_theme=False` to disable) | Want plotext's chart breadth (candlestick/datetime/histogram) with zero theming, no interactivity needed | Known log-scale bug (`math domain error` on repeated `"log"` renders; reset to `"linear"`); inherits plotext's slow maintenance | [announcement](https://textual.textualize.io/blog/2023/10/04/announcing-textual-plotext/), [README](https://github.com/Textualize/textual-plotext/blob/main/README.md) |
| **`textual-plot`** (davidfokkema) | **Native** Textual widget (not a wrapper); half-blocks, quadrants, **braille (2×4)**; **interactive mouse zoom/pan**, keyboard zoom/pan, auto axis scaling, nice ticks (1/2/5) | Want native-feeling, interactive, high-res XY plot (latency/throughput); line fidelity > chart-type breadth | — | [repo](https://github.com/davidfokkema/textual-plot) |

### 5.8 Motion-policy implications (preview of §7B)

Textual makes "animation-free deterministic core" a **line, not a vibe**: it is `TEXTUAL_ANIMATIONS=none/basic` + per-animation `level="full"` tagging, enforced by the framework rather than hoped-for from contributors. Full operational tiering in §7B.

---

## 6. Terminal accessibility criteria

**`NOT_SYNTHESIZED` — Stream 5 (a11y-terminal) returned `API Error: Server is temporarily limiting requests · Rate limited`. Zero content received.**

This section was scoped to define terminal accessibility criteria (screen-reader behavior, contrast, keyboard-only operation, reduced-motion). **No criteria were received and none can be cited without fabrication.**

Partial bridge from Stream 4 (mechanism only, not a11y findings): Textual provides a **reduced-motion lever** (`app.animation_level` flip between `basic`/`full`) and contrast is encodable via TCSS tokens (§7C). But the *criteria* — WCAG-equivalent thresholds, screen-reader testing matrix, keyboard-nav requirements — are absent. Re-run Stream 5 before D3 sets accessibility acceptance gates.

---

## 7. Consolidated "Mapped to dopemux" recommendations

> **Coverage note:** only buckets fed by Stream 4 are populated. The rest are blocked on stream re-run and marked `PENDING`.

### 7A. Cockpit IA & navigation
**`PENDING` — depends on Streams 1 (exemplar-tuis) + 3 (tmux-ux), both rate-limited.**
Partial mechanism available from Stream 4: Textual **Modes** (`MODES` dict, `switch_mode`, `DEFAULT_MODE`) give independent screen stacks per workspace (RUN/AUDIT/PLAN), each preserving nav history; screens are a push/pop stack ([Screens guide](https://textual.textualize.io/guide/screens/)). **IA *structure* recommendations require the missing exemplar/tmux evidence — do not finalize IA from mechanism alone.**

### 7B. Component library *(fully supported by Stream 4)*

Build composed widgets subclassing Textual primitives, each carrying mint-on-navy TCSS + closed chip palette as tokens:

1. **`Gauge` — NO native widget; compose one.**
   - *Bar gauge:* subclass `ProgressBar`, style `.bar--bar`/`.bar--complete` mint/navy, **fixed `total` (never `None`** — avoids indeterminate pulse), threshold color flip (→ BLOCKER red past limit) ([ProgressBar](https://textual.textualize.io/widgets/progress_bar/)).
   - *Block level meter:* a `Static` rendering one column of `▁▂▃▄▅▆▇█` for a single live value — word-sized, alignment-safe. **Verify `▁`/`█` width in the pinned Nerd Font first** (§5.1 hazard).
2. **`Sparkline` (themed):** built-in `Sparkline`; `--min-color`/`--max-color` = mint ramp; width = cells you can spare; `summary_function` per metric (`max` spikes, `mean` trend). Keep in a **fixed-width column** so block-glyph jitter is absorbed over length and never breaks neighbor alignment ([Sparkline](https://textual.textualize.io/widgets/sparkline/)).
3. **`SignalTable`:** `DataTable` with `fixed_columns` for the timestamp/severity key column, zebra-stripes off or navy-styled, **status chips as Rich `Text`** (LIVE/BLOCKER/OVERRIDE/LOGGED/AFTERCARE/EDGE → fixed fg/bg pairs). Update with `update_cell_at` + `refresh_coordinate()` — **never `clear()`+rebuild** ([DataTable](https://textual.textualize.io/widgets/data_table/)).
4. **`SignalFeed`:** base on **`RichLog`** (`auto_scroll=True`, `max_lines=<cap>`), write pre-styled chip lines. Use `DataTable` newest-first if you need a queryable grid instead; `Log` only for plain text ([RichLog](https://textual.textualize.io/widgets/rich_log/)).
5. **`Tree`** for hierarchical state: style `tree--guides`/`tree--cursor`; tight `guide_depth` for density ([Tree](https://textual.textualize.io/widgets/tree/)).
6. **Charts:** default to **`textual-plot`** (native, braille, interactive) for latency/throughput panels; fall back to **`textual-plotext`** only for chart types it lacks (candlestick/histogram), accepting slow upstream + log-scale caveat ([textual-plot](https://github.com/davidfokkema/textual-plot), [textual-plotext](https://github.com/Textualize/textual-plotext)).

**Update discipline (per the 5.2 cost ladder):** drive every live widget from **reactive attributes**; keep fixed-size indicators on **plain refresh / `layout=False`**; reserve `layout=True` for genuine size changes; **never `recompose=True`** on a panel containing `DataTable`/`Input` ([Reactivity guide](https://textual.textualize.io/guide/reactivity/)).

### 7C. Motion / animation policy *(fully supported by Stream 4)*

| Tier | Surface | Motion | Rationale |
|---|---|---|---|
| **0** | Cockpit core / live data: gauges, sparklines, signal tables/feeds, status chips | **Zero** | (1) cost — competes with partial-update compositor; (2) ADHD — motion on always-on data is distraction; (3) determinism — interpolation makes output non-reproducible |
| **1** | Transient orientation only, **at `full` only**: screen/mode transitions, command-palette open/close, toast entry | Opt-in | Aids *spatial* orientation, not on live data. `animate("offset"/"opacity", ..., level="full")` → auto-suppressed below full. Screens have **no** built-in transition, so opt-in by construction |

**Enforcement (operationalize, don't trust convention):**
1. Ship default runtime **`TEXTUAL_ANIMATIONS=basic`** (set explicitly — default is `full`) ([constants API](https://textual.textualize.io/api/constants/), [types API](https://textual.textualize.io/api/types/)).
2. Tag every Tier-1 animation `level="full"` (auto-suppressed at `basic`/`none`) ([widget API](https://textual.textualize.io/api/widget/)).
3. Provide **`--deterministic` / snapshot mode = `TEXTUAL_ANIMATIONS=none` + `TEXTUAL_SMOOTH_SCROLL=0`** + forbid indeterminate `ProgressBar` (`total=None`) — makes UI a pure function of state for reliable snapshot tests ([constants API](https://textual.textualize.io/api/constants/), [ProgressBar](https://textual.textualize.io/widgets/progress_bar/)).
4. Expose a user **reduced-motion toggle** flipping `app.animation_level` between `basic`/`full` ([app API](https://textual.textualize.io/api/app/)).

### 7D. tmux shell
**`PENDING` — depends on Stream 3 (tmux-ux), rate-limited. No tmux recommendations can be made.**

### 7E. ADHD placement
**`PENDING` — depends on Stream 2 (adhd-terminal), rate-limited.**
Stream 4 supplies *enabling* primitives only (motion suppression for distraction control §7C; bounded `RichLog` feed; complexity-aware density), **not** placement guidance. ADHD *placement* (what goes where, attention-routing, cognitive-load layout) requires the missing stream and must not be invented.

### 7F. Accessibility
**`PENDING` — depends on Stream 5 (a11y-terminal), rate-limited.**
Stream 4 supplies levers only (reduced-motion via `animation_level`; TCSS contrast tokens), **not** acceptance criteria. Re-run Stream 5.

---

## 8. Open questions

**🔴 Largest open item — the four failed research streams.** §2 (exemplar TUIs), §3 (ADHD-in-terminal + static-vs-rich tension), §4 (tmux cockpit), §6 (accessibility) all returned `API Error` and were **not synthesized**. Re-run them and re-issue this brief. D3 must not treat those sections as resolved. The rate-limiting was server-side and hit all parallel streams — sequence the re-run to avoid a repeat.

Remaining questions answerable in-house (from Stream 4):

1. **Glyph width in the chosen Nerd Font** — verify `▁ ▄ █` cell width and baseline before committing to block sparklines/gauges (§5.1). Font-specific; not confirmable externally.
2. **The relayout-cost claim is partly inferred** (§5.2) — docs confirm `layout=True` is "more expensive" and the compositor does partial repaints, but the precise "relayout invalidates the spatial map" linkage is synthesis. Validate under real cockpit load via devtools (`TEXTUAL_SLOW_THRESHOLD`, default 500ms) ([constants API](https://textual.textualize.io/api/constants/)).
3. **Upstream maintenance** — plotext is effectively stale (v5.2.8, Oct 2022); `textual-plotext` inherits it. Prefer native `textual-plot` where chart-type breadth isn't required (§5.7).
4. **Determinism rationale** is synthesis (§5.3) — the framework supplies the motion-off mechanism; confirm the snapshot-test pipeline actually requires `none` (not just `basic`) in practice.

---

### Sources *(Stream 4 only; primary unless noted)*

**Textual:** [Reactivity](https://textual.textualize.io/guide/reactivity/) · [Animation](https://textual.textualize.io/guide/animation/) · [Workers](https://textual.textualize.io/guide/workers/) · [Screens & modes](https://textual.textualize.io/guide/screens/) · [Textual CSS](https://textual.textualize.io/guide/CSS/) · [Rendering algorithms blog](https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/) · [constants API](https://textual.textualize.io/api/constants/) · [types API (AnimationLevel)](https://textual.textualize.io/api/types/) · [app API](https://textual.textualize.io/api/app/) · [widget API](https://textual.textualize.io/api/widget/) · widgets: [DataTable](https://textual.textualize.io/widgets/data_table/), [Sparkline](https://textual.textualize.io/widgets/sparkline/), [ProgressBar](https://textual.textualize.io/widgets/progress_bar/), [Tree](https://textual.textualize.io/widgets/tree/), [RichLog](https://textual.textualize.io/widgets/rich_log/)
**Plotting:** [textual-plotext repo](https://github.com/Textualize/textual-plotext) / [announcement](https://textual.textualize.io/blog/2023/10/04/announcing-textual-plotext/) / [README](https://github.com/Textualize/textual-plotext/blob/main/README.md) · [textual-plot (native)](https://github.com/davidfokkema/textual-plot) · [plotext](https://github.com/piccolomo/plotext) · [plotille](https://pypi.org/project/plotille/)
**Sparkline/Tufte theory:** [The Tao of Unicode Sparklines (Udell)](https://blog.jonudell.net/2021/08/05/the-tao-of-unicode-sparklines/) · [deeplook/sparklines](https://github.com/deeplook/sparklines) · [sparklines PyPI](https://pypi.org/project/sparklines/) · [Rosetta Code](https://rosettacode.org/wiki/Sparkline_in_unicode) · [cli.r-lib spark_bar](https://cli.r-lib.org/reference/spark_bar.html) · [QuestDB sparklines](https://questdb.com/blog/sparklines-candlesticks-depth-charts-sql/)