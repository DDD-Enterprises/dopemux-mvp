---
id: COCKPIT_DESIGN_SYSTEM_V1
title: Dopemux Cockpit TUI Design System v1
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-29'
last_review: '2026-05-29'
next_review: '2026-08-29'
supersedes: COCKPIT_TUI_DESIGN_SYSTEM_README (v0 — revised, not replaced)
prelude: "Unified UX/UI design spec (D3) for the dopemux operator cockpit (hero surface), revising v0: live-Textual IA across five modes + four global surfaces, the tmux hero session, width-verified character-grid mockups at 120x40/100x32/80x24, the component system mapped to render.py, filled spacing/type/motion gaps, the ADHD + voice reconciliation (motion stays on web), a real text-validation contract, measured WCAG contrast, and the Claude Design gate (safe_for_claude_design: NO; 8 open blockers). DIRECTION — not approved final screens."
---

# Dopemux Cockpit Design System v1

Terminal-native operator cockpit, revision of v0 (`readme.md`). **Authority before
aesthetics.** Every pane declares authority. Every data row carries `SRC=`.
Bridge/proxy actions are segregated. The status chip set is closed:
`LIVE BLOCKER OVERRIDE LOGGED AFTERCARE EDGE`. No web, chat, mouse, hover, new
chips, or unified-PM record inside the cockpit. Authorities never collapse — the
cockpit transports data; it does not own it. This system targets **120x40 first**,
with explicit adaptation at **100x32** and **80x24**. Below 80x24 is a `[BLOCKER]`.

---

## 1. Overview & what changes from v0

### 1.1 Status of this document

This is a **design direction / spec**, not an approval of final, data-wired
screens. The accepted IA package proof carries `safe_for_claude_design: NO` and
`READY_FOR_CLAUDE_DESIGN: not approved`
(`out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md` §1),
and `runtime_contract.py` **enforces** that gate at build time
(`build_runtime_render_model` raises `[BLOCKER]` if the proof flips it;
invariant `claude_design_blocked: true`; boundary line
`Claude Design upload blocked`). v1 therefore takes the same posture v0 uses for
Surfaces B and C: `DIRECTION` — it specifies the cockpit, it does not certify a
runtime. The eight exact unblock conditions are folded into the §11 acceptance
checklist. ia_verdict at the time of writing:
`CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`.

### 1.2 Provenance of v1 (honest-partial note)

v1 was scoped to graft a *winning direction* plus named grafts from three design
directions (A: density, B: flow/ADHD, C: authority/mode-purity). **All three
were delivered as API errors, not content** — verbatim:
`API Error: The socket connection was closed unexpectedly.` The upstream judge
aborted scoring rather than invent submissions to grade. Per doctrine (truth over
fluency, fail closed, never invent), **v1 fabricates no winner, no score, and no
graft list.** It synthesizes only verified substrate:

- **v0** — `readme.md` and the doctrine files in this package.
- **D1** — `docs/04-explanation/branding/ui-consolidation-audit-2026-05-29.md`
  (surface inventory, doc-vs-runtime divergence, gap list).
- **D2** — `docs/06-research/investigations/ui-ux-research-brief-2026-05-29.md`
  (Textual mechanics, motion policy; itself honest-partial — four research
  streams returned `API Error`, so its §2/§3/§4/§6 are `NOT_SYNTHESIZED`).
- **Runtime** — `src/dopemux/ui/cockpit/{render.py, app.py, runtime_contract.py}`,
  `src/dopemux/ui/theme.py`, `src/dopemux/voice/core.py`,
  `services/shared/brand_voice.py`, `scripts/brand_lint.py`.

Where D2's failed streams gate a recommendation (IA finalized from exemplar
evidence, ADHD behavioral grounding, tmux exemplars, a11y criteria), v1 marks the
item `PENDING (D2 stream re-run)` rather than backfill it.

### 1.3 Doc-vs-runtime reconciliation (the v0 correction)

v0 (`readme.md` Sources, `colors_and_type.css` header, "How to build" step 7)
references cockpit modules and an enforcement function that **do not exist at
HEAD** (confirmed in D1 §3, re-verified here):

| v0 reference | Runtime reality at HEAD `755bf38460` |
|---|---|
| `cockpit/tokens.py` | **ABSENT** — dir is `__init__.py`, `app.py`, `render.py`, `runtime_contract.py` only |
| `cockpit/frame.py` | **ABSENT** — there is no `FrameBuffer` / `Layout` class; the grid coords v0 tabulates live only in prose |
| `cockpit/model.py` | **ABSENT** |
| `cockpit/tokens.py::validate_rendered_text` | **ABSENT** — zero hits repo-wide |

**The real enforcement path** (runtime outranks docs):

1. `services/shared/brand_voice.py:55 brand_text()` -> `validate_or_fallback(...)`
   — service-layer voice gate, chip-prefixed.
2. `src/dopemux/voice/core.py:182 validate_output()` — lexical + structural gates;
   `select_mode` routes `Surface.UI -> VoiceMode.UI_STRICT` (`core.py` ~149).
3. `scripts/brand_lint.py:62 AUDITED_PYTHON_FILES` — static AST lint over an
   allow-list. **The cockpit module is NOT in that list** — the hero surface has
   no automated banned-vocab / chip enforcement today.
4. `src/dopemux/ui/theme.py:330 StatusChip` — the six-chip enum
   (`LIVE/BLOCKER/OVERRIDE/LOGGED/AFTERCARE/EDGE`), the runtime source of the
   closed set.

v1 closes this in §9: implement a real `validate_rendered_text` (or route cockpit
text through `voice/core.py`) **and** add the cockpit files to `brand_lint`. Until
then, every `[LIVE]`/`[LOGGED]`/`[EDGE]` string in `render.py` is hand-authored and
unchecked.

### 1.4 What changes from v0 — summary

| Area | v0 | v1 |
|---|---|---|
| Scope | Surface-A static snapshot + B/C direction markers; "Slice 1 only", 4/5 modes `[EDGE]` | Full IA: 5 modes + 4 global surfaces, each with a four-field declaration; still DIRECTION-gated |
| Module map | Cites `tokens.py/frame.py/model.py/validate_rendered_text` | Corrects to the real files + names the real enforcement path (§1.3, §9) |
| Mode order | "PM, Implementer, Overview, Services, Events" prose | Locked to runtime order `render.py:33` / `runtime_contract.py:22`; reconciled against any prompt drift |
| Global surfaces | Not specified | Command Palette, Settings/Admin/Runtime, Safe Actions / Proof Gate, Unknown / Drift Queue (`runtime_contract.py:30`) |
| Safe actions | Implicit | Explicit T0..T6/TX/TU tier ladder; gate cross-cutting, non-executing in this packet |
| tmux | None | Hero session spec (§3), emoji stripped, one advisory cue |
| Spacing/type/motion | "ABSENT" (D1 §8) | Filled (§6): character-grid spacing scale, type policy, `TEXTUAL_ANIMATIONS` motion tiers |
| ADHD | "advisory/future-only", undocumented | Reconciled (§7): one status-rail cue + opt-in Focus/HUD overlay + web/cockpit split, .Jules-cited |
| WCAG | Asserted "monochrome-safe" | Measured ratios per pair, fails reported (§10) |

---

## 2. Information architecture

Five top-level modes, four global surfaces. **Exactly five modes — no sixth, no
subsuming, no promoting a surface to a mode** (`runtime_contract.py:1350`
`build_runtime_render_model` raises `[BLOCKER]` on mode/surface drift;
`INTEGRATED_COCKPIT_IA_CONTRACT.md` §1). Mode order is runtime-locked:

```
PM | Implementer | Overview | Services | Events
```

Source of truth: `render.py:33 TOP_LEVEL_MODES`, `runtime_contract.py:22`.
(Note: where any upstream prompt listed Services before Overview, runtime order
wins.) Global-surface strings are also runtime-verbatim:
`Command Palette`, `Settings/Admin/Runtime`, `Safe Actions / Proof Gate`,
`Unknown / Drift Queue` (`runtime_contract.py:30`). v0/prompt shorthand
"Drift Queue" maps to the runtime name `Unknown / Drift Queue`.

Every pane and surface declares the four-field block from the Pane Declaration Law
(`ARCHITECTURE_SAFETY_OVERLAY.md`; enforced for PM in
`render.py:55 PaneDeclaration`, locked by
`tests/unit/dopemux/ui/cockpit/test_cockpit_render.py::test_every_pm_pane_has_four_field_declaration`):

```
domain:       <which domain this pane represents>
authority:    <the authority owner for that domain>   (UNKNOWN if unproven — never guess)
role:         canonical | derived | mirrored | proxied | authoring | chrome
next_action:  <what the operator can do from this pane>
```

### 2.1 Mode: PM

PM is workflow triage and handoff readiness — it does **not** own PM truth
(`PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`, "PM Mode Law"). Six panes, mirroring the
implemented `render.py::pm_panes()` (the only mode with a real render today).

| Pane | domain | authority | role | next_action |
|---|---|---|---|---|
| Left rail — workflow / slice map | `workflow_slice` | `task-orchestrator workflow transitions` | derived | open |
| Center upper — readiness queue | `readiness_queue` | `task-orchestrator workflow transitions` | canonical | triage |
| Center lower — adjudication context | `adjudication` | `task-orchestrator workflow transitions` | canonical | inspect |
| Inspector upper — selected slice detail | `slice_detail` | `task-orchestrator workflow transitions` | canonical | inspect |
| Inspector lower-upper — canonical actions | `decisions` | `conport decisions/progress context` | authoring | log_decision |
| Inspector lower-lower — bridge segregator | `bridge_transport` | `dopecon-bridge adapter/proxy routing` | proxied | inspect_adapter_ref |

(Verbatim from `render.py:105-235`.) Allowed action classes: `DISPLAY_ONLY`,
`INSPECT_ACTION`, `CONFIRM_REQUIRED` (governance gate). Forbidden:
`BLOCKED_IN_COCKPIT`, `UNKNOWN`, `EXTERNAL_ONLY`
(`INTEGRATED_COCKPIT_IA_CONTRACT.md` §1).

### 2.2 Mode: Implementer

One bounded task: understand, confirm acceptance, inspect blockers, gather
evidence, validate, prepare handback (`PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`,
"Implementer Mode Law"). **Not yet rendered** — `app.py:113` raises
`unsupported cockpit mode` for any mode != `pm`. The declarations below are spec.

| Pane | domain | authority | role | next_action |
|---|---|---|---|---|
| Left rail — work contract / support rail | `work_contract` | `task-orchestrator workflow transitions` | derived | open |
| Center upper — current task + acceptance subset + blockers | `current_task` | `task-orchestrator workflow transitions` | canonical | confirm_acceptance |
| Center lower — evidence workspace (Top-3 / more_count / next_token) | `evidence` | `dope-context retrieval` | derived | request_more |
| Inspector upper — selected acceptance / evidence / proof detail | `proof` | `repo-truth-extractor proof` | canonical | inspect |
| Inspector lower-upper — canonical actions | `progress` | `conport decisions/progress context` | authoring | record |
| Inspector lower-lower — bridge segregator | `bridge_transport` | `dopecon-bridge adapter/proxy routing` | proxied | inspect_adapter_ref |

Forbidden patterns: retrieval console as primary; Serena treated as canonical
(it is optional `UNKNOWN` support); dopemux owning execution truth.

### 2.3 Mode: Overview

Operator status, health, drift summaries, safe launch points into secondary
surfaces. Display + inspect only — no confirm path (`INTEGRATED_COCKPIT_IA_CONTRACT.md`
§1, allowed `DISPLAY_ONLY`, `INSPECT_ACTION`). Spec.

| Pane | domain | authority | role | next_action |
|---|---|---|---|---|
| Left rail — surface index / launch points | `operator_overview` | `dopemux control surface` | chrome | open |
| Center upper — system health summary | `service_health` | `per-service authority (status only)` | derived | inspect |
| Center lower — drift summary (counts -> Unknown/Drift Queue) | `drift_summary` | `drift evidence (no execution)` | derived | inspect |
| Inspector — selected summary detail | `overview_detail` | `UNKNOWN until source proven` | derived | inspect |

Overview never executes and never confirms. Launch points hand off to a mode or a
global surface; they do not run anything inline.

### 2.4 Mode: Services

Service status, logs, health, child-workload inspection (the RTE child surface
lives here — `readme.md`: "active subject + RTE child surface"). Start/stop is
allowed **only via the Safe Action Gate at tier T5** (`INTEGRATED_COCKPIT_IA_CONTRACT.md`
§1, §5). Spec.

| Pane | domain | authority | role | next_action |
|---|---|---|---|---|
| Left rail — service / mode list | `service_index` | `dopemux control surface` | chrome | open |
| Center — active subject + RTE child surface | `rte_workload` | `repo-truth-extractor` | derived | inspect |
| Inspector upper — selected service detail | `service_detail` | `per-service authority (status only)` | derived | inspect |
| Inspector lower — start/stop action (gated) | `service_lifecycle` | `per-service authority` | authoring | confirm (T5, typed service-id) |
| Inspector lower-lower — bridge segregator | `bridge_transport` | `dopecon-bridge adapter/proxy routing` | proxied | inspect_adapter_ref |

The Services child surface (RTE) **declares its own authority**
(`repo-truth-extractor`) and never inherits the cockpit's — per the SRC/Provenance
Law. This is the A1 north-star layout (`surfaces/A1-rte-runs-120x40.html`).

### 2.5 Mode: Events

Chronicle, capture, trigger, event-inspection. Capture/emit via gate
(`INTEGRATED_COCKPIT_IA_CONTRACT.md` §1, `CONFIRM_REQUIRED` capture/emit). Spec.

| Pane | domain | authority | role | next_action |
|---|---|---|---|---|
| Left rail — event stream filter | `event_filter` | `dopemux control surface` | chrome | open |
| Center upper — live chronicle feed | `chronicle` | `dope-memory chronicle/receipts` | mirrored | inspect |
| Center lower — capture / trigger composer | `capture` | `dopecon-bridge event transport` | authoring | confirm (capture/emit) |
| Inspector — selected event detail | `event_detail` | `dope-memory chronicle/receipts` | mirrored | inspect |

dope-memory is `mirrored` (receipts mirror what already happened — never shown as
canonical success). Capture routes through the bridge as transport, gated; it is
not a canonical write.

### 2.6 Global surface: Command Palette

| Field | Value |
|---|---|
| domain | `command_broker` |
| authority | `dopemux control surface (broker)` |
| role | chrome |
| next_action | classify -> route (never execute) |

Broker only — discovery, classification, parameter preview, routing. **Never
executes** (`INTEGRATED_COCKPIT_IA_CONTRACT.md` §2, §6 "Palette never executes";
`runtime_contract.py` invariant `palette_broker_only: true`). Routes each row by
class to the Safe Action Gate, to Settings/Admin/Runtime, or to the Unknown/Drift
Queue. Invoked with `ctrl+k` (TUI; never `⌘K` — `acceptance.md` Command glyphs).
139 inventory rows home here (`INTEGRATED_COCKPIT_IA_CONTRACT.md` §4).

### 2.7 Global surface: Settings/Admin/Runtime

| Field | Value |
|---|---|
| domain | `settings_admin_runtime` |
| authority | `dopemux operator control + per-flow authority` |
| role | authoring |
| next_action | inspect -> invoke Safe Action Gate (never bypass) |

Nine flow groups (`runtime_contract.py:88-175 SETTINGS_ADMIN_FLOW_GROUPS`):
Routing/Model Provider, Profile management, Environment management, MCP server
control, Service startup/lifecycle (admin), Hooks/native-hooks, Runtime
configuration, Admin/safe/debug helpers, Drift inspection (read-only). Most flows
are tier `T2` (config mutation, explicit button + diff acknowledgment); service
lifecycle is `T5`. **Per-row gate tier is `UNKNOWN` until packet evidence exists**
(`row_tier_mapping_status` on every group) — unresolved tiers render literal
`UNKNOWN` and route to the queue, never auto-execute. 62 rows home here.

### 2.8 Global surface: Safe Actions / Proof Gate

| Field | Value |
|---|---|
| domain | `safe_action_gate` |
| authority | `cross-cutting safety contract` |
| role | chrome (cross-cutting; not a destination mode) |
| next_action | preflight -> confirm (does NOT execute in this packet) |

The gate is **cross-cutting**, not a mode: the same preflight/tier/refusal/
confirmation/proof/receipt path is used from any of the three allowed origins
(Command Palette, Settings/Admin/Runtime, or a contextual surface in
PM/Implementer/Overview/Services/Events) (`INTEGRATED_COCKPIT_IA_CONTRACT.md` §6).
Tier ladder (`runtime_contract.py:79 SAFE_ACTION_TIERS`,
`INTEGRATED_COCKPIT_IA_CONTRACT.md` §5):

| Tier | Class | Confirms? | Executes (this packet)? |
|---|---|---|---|
| T0 | DISPLAY_ONLY | no | no |
| T0i | INSPECT_ACTION | explicit invoke | yes (read-only) |
| T1 | CONFIRM_REQUIRED (generated artifact) | explicit button | yes |
| T2 | CONFIRM_REQUIRED (config mutation) | button + diff ack | yes |
| T3 | CONFIRM_REQUIRED (write local) | explicit button | yes |
| T4 | CONFIRM_REQUIRED (write remote) | button + typed confirm | **no — blocked until remote-mutation policy** |
| T5 | CONFIRM_REQUIRED (start/stop service) | button + typed service-id | yes |
| T6 | CONFIRM_REQUIRED (execution handoff) | button + typed TP-id | yes |
| TX | BLOCKED_IN_COCKPIT | no | **never** |
| TU | UNKNOWN | no | **never** |

Invariants: auto-confirm forbidden across all tiers; confirmation is not execution
proof; proof required for any completion claim; stale proof routes to the
Unknown/Drift Queue; in-gate reclassification forbidden; cwd resolved against the
worktree, never `/tmp`.

### 2.9 Global surface: Unknown / Drift Queue

| Field | Value |
|---|---|
| domain | `unknown_drift_queue` |
| authority | `drift evidence (no execution)` |
| role | chrome (non-executable visibility surface) |
| next_action | inspect / copy-evidence (never execute, never reclassify) |

Non-executable. Surfaces UNKNOWN, MISSING, BLOCKED, DEFINED_NOT_REGISTERED,
OPTIONAL_IMPORT_UNKNOWN, conflicting authority, and stale-proof rows
(`runtime_contract.py:37 UNKNOWN_DRIFT_REASON_CODES`, 22 codes). Allowed
affordances are read-only (`runtime_contract.py:74
ALLOWED_UNKNOWN_DRIFT_AFFORDANCES`): `Inspect`, `CopyEvidence`,
`CopyRecommendedPacketPrompt`, `ShowBlockedReason`, `ShowUpstreamArtifact`.
Runtime reclassification is forbidden — an item leaves the queue only when a
packet resolves it. `UNKNOWN` is never collapsed into the `EDGE` chip (Forbidden
Phrases).

---

## 3. The tmux hero session

The cockpit is one Textual app; tmux hosts it and the operator's working panes.
The existing `.tmux.conf` is a PM-dashboard layout with **emoji status segments**
(`⚠️ 🟡 🟢 🧠 🛠️` — forbidden by v0 "Emoji. None.") and a spread of ADHD binds.
v1 respecs it: emoji stripped, ADHD reduced to one source-labeled advisory cue
(Support Cue Law), keybinds aligned to the cockpit IA.

### 3.1 Pane composition

```
session: cockpit
window 0: "deck"
  pane 0  (full height, ~70% width)  dopemux cockpit            # the Textual hero
  pane 1  (right, ~30%, upper)        live log tail / RichLog     # signal feed
  pane 2  (right, ~30%, lower)        scratch shell               # operator commands
```

The hero pane owns mode switching internally (`ctrl+k` palette, `1..5` modes); tmux
does not duplicate cockpit nav. tmux panes are for the operator's *shell context*
beside the deck, not a second cockpit.

### 3.2 status-left / status-right

One advisory cue, source-labeled, no emoji. The cue mirrors `render.py:242`
(`cue: ADHD_engine: ... (advisory only)`).

```
set -g status-style              "bg=#020617,fg=#94A3B8"
set -g status-left-length        60
set -g status-right-length       80

# left: session + workspace (chrome; no SRC, no chip)
set -g status-left  "#[fg=#7DFBF6,bold] #S #[fg=#64748B]ws:#{?@workspace,#{@workspace},default} "

# right: model/context (chrome) + the single ADHD advisory cue (source-labeled, no gate)
set -g status-right "#[fg=#64748B]#{@model:-sonnet-4.5} (#{@ctx_window:-1M}) #[fg=#94A3B8]cue:adhd_engine #{?#{==:#{environ:TMUX_ADHD_ENERGY},low},low-energy: suggest 25-min block,steady} "
```

Rules: status-left and status-right are **chrome** — no `SRC=`, no chip, no
transition control (`acceptance.md` "Chrome vs. data"). The cue is advisory text,
never a chip, never a gate (Support Cue Law). It states a source (`adhd_engine`)
and a suggestion; it never blocks. Energy value comes from `TMUX_ADHD_ENERGY`
(low|steady); unknown collapses to `steady`, not a guess.

### 3.3 prefix + keybindings

Prefix unchanged (`C-b` default unless the operator's conf overrides). Binds are
respecced to the cockpit IA — mode switch, palette, gate, safe save — replacing the
old PM-dashboard `send-keys` binds. No emoji in any bind description.

| Bind | Action | Note |
|---|---|---|
| `prefix k` | focus hero pane, send `ctrl+k` (command palette) | broker only |
| `prefix 1`..`prefix 5` | hero: switch mode PM/Implementer/Overview/Services/Events | mode order locked |
| `prefix f` | `dopemux focus-mode-toggle` | opt-in Focus/HUD overlay (§7) |
| `prefix g` | hero: open Safe Action Gate for the selected row | gate confirms, never auto-executes |
| `prefix S` | `dopemux save-session` | T0i-class; read/checkpoint, not a remote write |
| `prefix w` | `choose-tree -Zw` | workspace switch (kept) |
| `prefix Q` | `confirm-before "dopemux emergency-save"` | destructive-guarded (kept) |

Dropped from the old conf: `o/d/v/z` auto-`send-keys` into numbered panes
(coupled to a fixed 6-pane PM layout that the cockpit replaces), and the
`break-reminder`/`energy-check` binds (folded into the single advisory cue).

### 3.4 Layout file shape

```
# scripts/ui/cockpit.tmux  — sourced by `tmux source-file`
new-session  -d -s cockpit -n deck
send-keys    -t cockpit:deck.0 "dopemux cockpit" Enter
split-window -h -p 30 -t cockpit:deck.0
split-window -v -p 50 -t cockpit:deck.1
select-pane  -t cockpit:deck.0
# status + binds loaded from .tmux.conf (§3.2, §3.3)
```

This is a **direction**, consistent with the `safe_for_claude_design: NO` gate: it
launches the existing `dopemux cockpit` (PM-only today) and does not imply the
stubbed modes are wired.

---

## 4. Screen designs (annotated mockups)

Mockups honor the v0 frame grid (`readme.md` Layout table) and the A1 north-star
character vocabulary (`surfaces/A1-rte-runs-120x40.html`): `┏━┓` top, `┠─┨` rules,
`┃` walls, `│` column dividers, `┬`/`┴`/`┤` divider junctions. Every content row is
padded so its right wall lands on the exact column count (faithful schematics; per-line width is a Frame-primitive invariant enforced at implementation time, not re-measured in this design pass). Text after `#` is an annotation in the off-grid
margin, not part of the rendered grid. The mid-body rule uses `┴` under the left
divider (center merges) and `┤` at the right divider (inspector continues), per the
A1 north star.

Grid invariants (`readme.md`):

| Size | left div | right div | inspector split | center split | body rule | command row | status rule | status row | bottom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 120x40 | col 25 | col 84 | row 22 | row 25 | row 35 | row 36 | row 37 | row 38 | row 39 |
| 100x32 | col 21 | col 70 | row 17 | row 19 | row 27 | row 28 | row 29 | row 30 | row 31 |
| 80x24 | col 17 | col 56 | row 11 | row 13 | row 19 | row 20 | row 21 | row 22 | row 23 |

### 4.1 PM mode — 120x40 (north star)

The only mode with a real render today (`render.py::render_pm`). Six panes; bridge is a dedicated segregator pane at this size.

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dopemux Cockpit  mode=PM                                              ━━━◆ Ø ◆━━━                                    ┃   # brand mark; top row = chrome (no SRC)
┃ STATIC DEMO  NO WRITES  no live PM mutations          role:chrome  authority:dopemux  viewport 120x40                ┃   # bridge_placement: segregator-pane
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM        2 Implementer   3 Overview   4 Services   5 Events                          ctrl+k palette               ┃   # mode bar=chrome; active=PM; ctrl+k never ⌘K
┠───────────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────┨
┃ workflow / slice map  │ readiness queue                                          │ Inspector                         ┃   # each pane declares authority/role/next
┃ authority:            │ authority: task-orchestrator                             │ slice detail                      ┃
┃   task-orchestrator   │ role: canonical  next: triage                            │ domain: slice_detail              ┃   # closed-set chips only
┃ role: derived         │ 1 [LIVE]   PM-TEXTUAL-001 ok b=0                         │ authority:                        ┃
┃ next: open            │ 2 [LOGGED] PM-PLANE-014   ok b=1                         │ task-orchestrator                 ┃   # UNKNOWN stays literal, not a chip
┃                       │ 3 [EDGE]   PROXY-002  legality=UNKNOWN                   │ role: canonical                   ┃
┃ 1 [LIVE]  TEXTUAL-001 │ more_count: 2  next_token: q_p2                          │ next: inspect                     ┃   # Top-3 + more_count + next_token
┃ 2 [LOGGED] PLANE-014  │                                                          │ SRC=leantime  LT-1422             ┃   # SRC on data rows only
┃ 3 [EDGE]  PROXY-002   │ adjudication context                                     │ SRC=conport   PC-DMX-COCKPIT      ┃
┃ more_count: 4         │ authority: task-orchestrator                             │ SRC=conport   P-2026.04-022       ┃
┃ next_token:           │ role: canonical  next: inspect                           │                                   ┃
┃  slice_PLANE-019      │ blocker: UNKNOWN -- verify (to)                          │ canonical actions                 ┃
┃                       │ transitions: triage->ready->handoff                      │ authority: conport                ┃   # authoring pane: authority = artifact's
┃                       │ SRC=conport     D-PM-014  LOGGED                         │ role: authoring                   ┃
┃                       │ SRC=dope-memory R-CHRON-882 AFTERCARE                    │ next: log_decision                ┃
┃                       │ SRC=leantime    LT-1422 age=3d                           │ log_decision SRC=conport          ┃
┠───────────────────────┴──────────────────────────────────────────────────────────┤───────────────────────────────────┨   # row 22 inspector split
┃ status: triage filter active   legality=ok  warnings=0                           │ Bridge adapter/proxy:             ┃
┃                                                                                  │ dopecon-bridge                    ┃   # bridge segregated; hard divider
┃                                                                                  │ [EDGE] adapter-only               ┃   # never a peer of canonical
┃                                                                                  │ segregated                        ┃
┃                                                                                  │ role: proxied                     ┃
┃                                                                                  │ transport_ref:                    ┃
┃                                                                                  │ bridge.adapter.kg.read            ┃
┃                                                                                  │ note: adapter only; writes        ┃
┃                                                                                  │ route through owners              ┃
┃                                                                                  │ SRC=dopecon-bridge                ┃
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 35 body rule
┃ log_decision  log_progress  workflow.advance  chronicle.read  retrieval.query           command rail                 ┃   # row 36 command rail = chrome, no SRC
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 37 status rule
┃ filter=triage  legality=ok  warnings=0  cue:adhd_engine focused; suggest 25-min block (advisory)                     ┃   # the SINGLE advisory cue; no chip, no gate
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.2 PM mode — 100x32 (compact)

Same structure, narrower columns (left div col 21, right div col 70). Bridge demotes into inspector lower detail — `render.py:268 _bridge_role_for_viewport` returns `inspector-lower-detail`. No dedicated segregator pane.

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dopemux Cockpit  mode=PM        role:chrome  authority:dopemux                                   ┃   # top row = chrome
┃ STATIC DEMO  NO WRITES   viewport 100x32                                                         ┃   # bridge_placement: inspector-lower-detail
┠──────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM    2 Implementer  3 Overview  4 Services  5 Events            ctrl+k palette                ┃   # active=PM
┠───────────────────┬────────────────────────────────────────────────┬─────────────────────────────┨
┃ workflow/slice    │ readiness queue                                │ Inspector                   ┃
┃ auth:             │ authority: task-orchestrator                   │ slice detail                ┃
┃ task-orchestrator │ role: canonical next: triage                   │ domain: slice_detail        ┃
┃ role: derived     │ 1 [LIVE]   TEXTUAL-001 ok b=0                  │ auth: task-orchestrator     ┃
┃ next: open        │ 2 [LOGGED] PLANE-014   ok b=1                  │ role: canonical             ┃   # UNKNOWN literal
┃                   │ 3 [EDGE]   PROXY-002  UNKNOWN                  │ next: inspect               ┃
┃ 1 [LIVE] TEXT-001 │ more_count: 2 next_token: q_p2                 │ SRC=leantime LT-1422        ┃
┃ 2 [LOGGED] PL-014 │                                                │ SRC=conport  P-022          ┃
┃ 3 [EDGE] PRX-002  │ adjudication                                   │                             ┃
┃ more_count: 4     │ authority: task-orchestrator                   │ canonical actions           ┃
┃ next_token:       │ role: canonical next: inspect                  │ authority: conport          ┃
┃ slice_PLANE-019   │ blocker: UNKNOWN -- verify                     │ role: authoring             ┃   # bridge now inspector detail
┃                   │ SRC=conport D-PM-014 LOGGED                    │ next: log_decision          ┃
┃                   │ SRC=dope-memory R-882 AFTERCARE                │ log_decision SRC=conport    ┃
┃                   │ SRC=leantime LT-1422 age=3d                    │ bridge (inspector detail):  ┃
┃                   │ handoff_ready: false                           │ dopecon-bridge [EDGE]       ┃   # bridge = detail, not peer
┠───────────────────┴────────────────────────────────────────────────┤─────────────────────────────┨   # row 17 inspector split
┃ status: triage  legality=ok  warnings=0                            │ adapter-only segregated     ┃
┃                                                                    │ role: proxied               ┃
┃                                                                    │ SRC=dopecon-bridge          ┃
┃                                                                    │ transport_ref:              ┃
┃                                                                    │ bridge.adapter.kg.read      ┃
┠──────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 27 body rule
┃ log_decision  log_progress  workflow.advance  chronicle.read  retrieval.query   command rail     ┃   # chrome, no SRC
┠──────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 29 status rule
┃ filter=triage  legality=ok  cue:adhd_engine focused; 25-min block (advisory)   status            ┃   # single cue
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.3 PM mode — 80x24 (fallback)

Bridge collapses to a single inspector-detail line — **not a pane** (`render.py:319` `inspector-detail-collapsed`). The authority field is abbreviated, never deleted (Viewport Degradation Law).

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Cockpit mode=PM  STATIC DEMO  NO WRITES   role:chrome                        ┃   # auth:dopemux
┃ viewport 80x24                                                               ┃   # bridge_placement: inspector-detail-collapsed
┠──────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM  2 Impl  3 Ovw  4 Svc  5 Evt        ctrl+k palette                      ┃   # active=PM
┠───────────────┬──────────────────────────────────────┬───────────────────────┨
┃ workflow      │ readiness queue                      │ Inspector             ┃
┃ auth:to       │ auth: task-orch role:canon           │ slice detail          ┃   # auth abbreviated, NOT deleted
┃ role:derived  │ next: triage                         │ auth: task-orch       ┃
┃ next: open    │ 1 [LIVE]  TEXT-001 ok b=0            │ role:canon            ┃
┃ 1[LIVE]T-001  │ 2 [LOGGED] PLN-014 ok b=1            │ next:inspect          ┃   # UNKNOWN literal
┃ 2[LOG]PL-014  │ 3 [EDGE]  PRX-002 UNKNOWN            │ SRC=leantime          ┃
┃ 3[EDG]PR-002  │ more_count:2 nt:q_p2                 │ SRC=conport           ┃
┃ more_count:4  │ adjudication                         │ canonical acts        ┃
┃               │ auth:task-orch                       │ auth: conport         ┃
┃               │ blocker:UNKNOWN verify               │ role:authoring        ┃
┃               │ SRC=conport D-014 LOGGED             │ next:log_decision     ┃
┠───────────────┴──────────────────────────────────────┤───────────────────────┨   # row 11 inspector split
┃ status: triage  legality=ok                          │ SRC=conport           ┃
┃ [inspector-detail] bridge collapsed: dopecon-bridge adapter/proxy ref        ┃   # bridge = ONE line, not a pane
┠──────────────────────────────────────────────────────────────────────────────┨   # row 19 body rule
┃ log_decision log_progress workflow.advance chronicle.read  cmd rail          ┃   # chrome
┠──────────────────────────────────────────────────────────────────────────────┨   # row 21 status rule
┃ filter=triage legality=ok cue:adhd_engine focused (advisory)                 ┃   # single cue
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.4 Implementer mode — 120x40

Spec — not yet rendered (`app.py:113` raises for any mode != `pm`). Current task + acceptance subset + evidence (Top-3); retrieval (dope-context) is `derived`, never source-truth; Serena is optional `UNKNOWN`.

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dopemux Cockpit  mode=Implementer                                     ━━━◆ Ø ◆━━━                                    ┃   # top row = chrome
┃ STATIC DEMO  NO WRITES          role:chrome  authority:dopemux        viewport 120x40                                ┃   # bridge_placement: segregator-pane
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM        2 Implementer   3 Overview   4 Services   5 Events                          ctrl+k palette               ┃   # active=Implementer
┠───────────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────┨
┃ work contract         │ current task                                             │ Inspector                         ┃
┃ authority:            │ authority: task-orchestrator                             │ acceptance / proof detail         ┃
┃ task-orchestrator     │ role: canonical next: confirm                            │ domain: proof                     ┃
┃ role: derived         │ task: RUNTIME-RENDER-001                                 │ authority:                        ┃
┃ next: open            │ next_action: confirm_acceptance                          │ repo-truth-extractor              ┃
┃                       │ acceptance subset: 3 of 7 met                            │ role: canonical                   ┃
┃ contract refs:        │ [ok] renders SCREEN_CONTRACT                             │ next: inspect                     ┃   # PKT-* = secondary ref only
┃ PKT-RENDER-001        │ [ok] proof JSON validates                                │ SRC=repo-truth-extractor          ┃
┃ (compose/fwd ref)     │ [--] no destr. affordances                               │ bundle=v5 pinned                  ┃
┃                       │ blockers: 1 SRC=task-orchestr                            │ SRC=conport P-2026.04-022         ┃
┃                       │ evidence workspace                                       │                                   ┃
┃                       │ authority: dope-context                                  │ canonical actions                 ┃   # retrieval is retrieval, not truth
┃                       │ role: derived next: request_more                         │ authority: conport                ┃
┃                       │ 1 SRC=dope-context render_snap                           │ role: authoring                   ┃
┃                       │ 2 SRC=dope-context four_field                            │ next: record                      ┃
┃                       │ 3 SRC=dope-context Pane Law                              │ record_progress SRC=conport       ┃
┠───────────────────────┴──────────────────────────────────────────────────────────┤───────────────────────────────────┨   # row 22 inspector split
┃ validation: NOT_RUN                                                              │ Bridge adapter/proxy:             ┃   # validation honest: NOT_RUN
┃ task_drift: none  support: serena=UNKNOWN                                        │ dopecon-bridge                    ┃   # Serena = optional UNKNOWN
┃                                                                                  │ [EDGE] adapter-only               ┃
┃                                                                                  │ segregated                        ┃
┃                                                                                  │ role: proxied                     ┃
┃                                                                                  │ transport_ref:                    ┃
┃                                                                                  │ bridge.adapter.to.blockers        ┃
┃                                                                                  │ note: adapter only; handback      ┃
┃                                                                                  │ via task-orchestrator             ┃
┃                                                                                  │ SRC=dopecon-bridge                ┃
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 35 body rule
┃ confirm_acceptance  record_progress  request_more  run_validation  handback           command rail                   ┃   # chrome
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 37 status rule
┃ validation=NOT_RUN  drift=none  cue:adhd_engine scattered; suggest 25-min focus block (advisory)                     ┃   # cue never gates acceptance
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.5 Services mode — 120x40 (RTE child surface)

The A1 north star. The center pane is the RTE child workload and **declares its own authority** (`repo-truth-extractor`), not the cockpit's. Start/stop is gated at tier T5 (typed service-id).

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dopemux Cockpit  mode=Services                                        ━━━◆ Ø ◆━━━                                    ┃   # top row = chrome
┃ STATIC DEMO  NO WRITES          role:chrome  authority:dopemux        viewport 120x40                                ┃   # bridge_placement: segregator-pane
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM        2 Implementer   3 Overview   4 Services   5 Events                          ctrl+k palette               ┃   # active=Services
┠───────────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────┨
┃ service / mode list   │ RTE Runs                                                 │ Inspector                         ┃   # child surface declares OWN authority
┃ authority:            │ authority: repo-truth-extractor                          │ subject                           ┃
┃ dopemux control       │ role: derived  next: inspect                             │ v5-...T14:32Z-a91c                ┃
┃ role: chrome          │ RUN ID            STATUS  AL                             │ authority:                        ┃   # leading > = active row (no mouse)
┃ next: open            │ > v5-...a91c  [LIVE]    2                                │ repo-truth-extractor              ┃
┃                       │ SRC=repo-truth-extractor norm                            │ role: canonical                   ┃
┃ R1 Runs               │ v5-...7f18  [BLOCKER]  1                                 │ scope: services                   ┃
┃ R2 Active             │ SRC=repo-truth-extractor pre                             │ phase: normalize                  ┃
┃ R3 Prescan            │ v5-...1d9b  [LOGGED]   0                                 │ SRC=repo-truth-extractor          ┃
┃ R4 Doctor             │ SRC=repo-truth-extractor vfy                             │                                   ┃
┃ R5 Coverage           │ v5-...ce44  [OVERRIDE]  6                                │ start/stop (gated)                ┃
┃ R6 Audit              │ SRC=repo-truth-extractor cov                             │ authority: per-service            ┃
┃                       │ v5-...9a44  [AFTERCARE] 3                                │ role: authoring                   ┃
┃                       │ SRC=repo-truth-extractor rcp                             │ next: confirm (T5)                ┃   # start/stop = T5, typed service-id
┃                       │ v5-...2ed3  [EDGE]     0                                 │ T5: typed service-id req'd        ┃
┃                       │ SRC=repo-truth-extractor pre                             │                                   ┃
┠───────────────────────┴──────────────────────────────────────────────────────────┤───────────────────────────────────┨   # row 22 inspector split
┃ status: 8 runs  1 [BLOCKER]  1 [OVERRIDE]                                        │ Bridge adapter/proxy:             ┃
┃ writes from cockpit: none                                                        │ dopecon-bridge                    ┃
┃                                                                                  │ [EDGE] adapter-only               ┃
┃                                                                                  │ segregated                        ┃
┃                                                                                  │ role: proxied                     ┃
┃                                                                                  │ transport_ref:                    ┃
┃                                                                                  │ bridge.adapter.svc.status         ┃
┃                                                                                  │ note: status proxy only;          ┃   # lifecycle via service owner
┃                                                                                  │ lifecycle via owner               ┃
┃                                                                                  │ SRC=dopecon-bridge                ┃
┃                                                                                  │                                   ┃
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 35 body rule
┃ inspect  view_logs  service.start  service.stop  open_child           command rail                                   ┃   # chrome
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 37 status rule
┃ runs=8  blocked=1  cue:adhd_engine steady (advisory)           status rail                                           ┃   # single cue
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.6 Overview mode — 120x40

Display + inspect only — no command-rail mutations, no confirm path, **no bridge segregator** (Overview has no canonical write to proxy). Launch points hand off to a mode/surface; they never run inline.

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dopemux Cockpit  mode=Overview                                        ━━━◆ Ø ◆━━━                                    ┃   # top row = chrome
┃ STATIC DEMO  NO WRITES          role:chrome  authority:dopemux        viewport 120x40                                ┃   # display + inspect only
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM        2 Implementer   3 Overview   4 Services   5 Events                          ctrl+k palette               ┃   # active=Overview
┠───────────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────┨
┃ surface index         │ system health                                            │ Inspector                         ┃
┃ authority:            │ authority: per-service (status)                          │ summary detail                    ┃
┃ dopemux control       │ role: derived next: inspect                              │ domain: overview_detail           ┃
┃ role: chrome          │ service           status SRC                             │ authority:                        ┃   # detail source unproven -> UNKNOWN
┃ next: open            │ task-orchestrator [LIVE]  SRC=to                         │ UNKNOWN until proven              ┃
┃                       │ conport         [LIVE]  SRC=cp                           │ role: derived                     ┃
┃ launch:               │ dope-memory      [LOGGED] SRC=dm                         │ next: inspect                     ┃
┃ -> PM                 │ dope-context     [LIVE]  SRC=dc                          │                                   ┃
┃ -> Implementer        │ leantime         [OVERRIDE] SRC=lt                       │ selected: drift summary           ┃
┃ -> Services           │ dopecon-bridge   [EDGE]  SRC=db                          │ open items: 7                     ┃   # launch hands off; no inline exec
┃ -> Events             │ drift summary                                            │ -> Unknown/Drift Queue            ┃
┃ -> Command Palette    │ authority: drift evidence                                │ (non-executable surface)          ┃
┃                       │ role: derived next: inspect                              │                                   ┃
┃                       │ UNKNOWN:5 MISSING:284 stale:0                            │                                   ┃
┃                       │ conflicting-auth: 14                                     │                                   ┃
┃                       │ -> open Unknown/Drift Queue                              │                                   ┃
┠───────────────────────┴──────────────────────────────────────────────────────────┤───────────────────────────────────┨   # row 22 inspector split
┃ status: 9 surfaces  1 [OVERRIDE]  1 [EDGE]                                       │ (no bridge segregator here:       ┃
┃                                                                                  │ Overview has no canonical         ┃   # bridge omitted: no canonical write
┃                                                                                  │ write path; bridge omitted)       ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┃                                                                                  │                                   ┃
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 35 body rule
┃ inspect  open_surface           command rail                                                                         ┃   # no mutating actions in Overview
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 37 status rule
┃ surfaces=9  missing=284  cue:adhd_engine steady (advisory)           status rail                                     ┃   # single cue
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.7 Events mode — 120x40

Chronicle feed is `mirrored` (dope-memory receipts mirror what already happened — never shown as canonical success). Each event carries a static `[HH:mm:ss]` timestamp (auditability). Capture/emit is bridge transport, gated; it is not a canonical write.

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dopemux Cockpit  mode=Events                                          ━━━◆ Ø ◆━━━                                    ┃   # top row = chrome
┃ STATIC DEMO  NO WRITES          role:chrome  authority:dopemux        viewport 120x40                                ┃   # bridge_placement: segregator-pane
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ 1 PM        2 Implementer   3 Overview   4 Services   5 Events                          ctrl+k palette               ┃   # active=Events
┠───────────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────┨
┃ event stream filter   │ chronicle feed                                           │ Inspector                         ┃
┃ authority:            │ authority: dope-memory                                   │ event detail                      ┃   # dope-memory = mirrored
┃ dopemux control       │ role: mirrored next: inspect                             │ domain: event_detail              ┃   # static [HH:mm:ss] timestamp
┃ role: chrome          │ [14:32:08] SRC=dm R-882 AFTERCARE                        │ authority:                        ┃
┃ next: open            │ [14:30:44] SRC=dm R-879 LOGGED                           │ dope-memory                       ┃
┃                       │ [14:28:10] SRC=dm R-871 BLOCKER                          │ role: mirrored                    ┃
┃ filters:              │ [14:22:55] SRC=dm R-866 LIVE                             │ next: inspect                     ┃
┃ all                   │ [14:19:03] SRC=dm R-858 OVERRIDE                         │ SRC=dope-memory R-882             ┃
┃ decisions             │ more_count:41 nt:chron_T14:18Z                           │ receipt mirrors prior event;      ┃
┃ runs                  │ capture / trigger composer                               │ not canonical success             ┃   # receipts mirror; never canonical
┃ gates                 │ authority: dopecon-bridge (evt)                          │                                   ┃
┃                       │ role: authoring                                          │ canonical record (if any)         ┃
┃                       │ capture: payload (preview)                               │ authority: conport                ┃
┃                       │ next: confirm (capture/emit gate)                        │ role: authoring                   ┃   # capture != write; routes to owner
┃                       │ note: capture is transport                               │ next: record                      ┃
┠───────────────────────┴──────────────────────────────────────────────────────────┤───────────────────────────────────┨   # row 22 inspector split
┃ status: 46 events  1 [BLOCKER]  1 [OVERRIDE]                                     │ Bridge adapter/proxy:             ┃
┃                                                                                  │ dopecon-bridge                    ┃
┃                                                                                  │ [EDGE] adapter-only               ┃
┃                                                                                  │ segregated                        ┃
┃                                                                                  │ role: proxied                     ┃
┃                                                                                  │ transport_ref:                    ┃
┃                                                                                  │ bridge.adapter.evt.emit           ┃
┃                                                                                  │ note: emit proxy only;            ┃   # receipts owned by dope-memory
┃                                                                                  │ receipts owned by dope-mem        ┃
┃                                                                                  │ SRC=dopecon-bridge                ┃
┃                                                                                  │                                   ┃
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 35 body rule
┃ inspect  capture  emit  filter           command rail                                                                ┃   # chrome
┠──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┨   # row 37 status rule
┃ events=46  blocked=1  cue:adhd_engine steady (advisory)           status rail                                        ┃   # single cue
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 4.8 Below 80x24 — BLOCKER panel

Exact runtime string (`render.py:43 TOO_SMALL_MESSAGE`): `[BLOCKER] terminal too
small (minimum 80x24)`. Rendered as a single Problem/Why/Fix/NEXT panel; no partial
UI (Viewport Degradation Law — fail closed). Width is the (too-small) terminal's;
the panel wraps to it. No chips, no SRC, no mode bar — a chrome failure panel, not a
cockpit screen. Reference shape:

```text
[BLOCKER] terminal too small (minimum 80x24)
Problem: cockpit snapshot supports 120x40, 100x32, or 80x24.
Why:     layout invariants are size-bound; below 80x24 no pane can declare
         its authority field legibly.
Fix:     resize the terminal to at least 80x24.
NEXT:    rerun `dopemux cockpit` once the terminal is >= 80x24.
```

---

## 5. Component / primitive system

v0 names twelve primitives (`readme.md` "How to build", step 3) sourced from the
React demo kit `ui_kits/cockpit/*.jsx`. **Most do not exist in `render.py`** — they
are reference renders, not the deterministic renderer. The renderer's real
structures are `PaneDeclaration` (`render.py:55`), `Top3Block` (`render.py:73`),
`PaneRender` (`render.py:90`), `_format_pane` (`render.py:287`),
`_command_status_rail` (`render.py:238`), and the per-pane builders
(`render.py:105-235`). Each primitive below gives its render contract and the
honest delta versus `render.py` at HEAD.

| Primitive | Render contract | Delta vs `render.py` |
|---|---|---|
| **Frame** | Outer grid `┏━┓ ┃ ┗━┛`; protected border cells immutable; width-locked to 120/100/80; refuses sub-cell drawing | **New — absent.** No `FrameBuffer`/`Layout`. `render_pm` emits markdown-ish text (`# title`, `## pane`), not a framed grid. v0's frame coords live only in prose. Build as `cockpit/frame.py` (the module v0 already cites but that does not exist). |
| **PaneHeader** | Renders the four-field block (`domain/authority/role/next_action`) + optional `SRC=` once | **Exists as logic.** `PaneDeclaration.header_lines()` (`render.py:64`) + `_format_pane` (`render.py:287`). Delta: emits flat lines, no box header row; needs Frame integration. |
| **Rule** | Horizontal divider row at protected rows; `┠─┨`, junctions `┬`/`┴`/`┤` | **New — absent.** `_format_pane` uses a blank line, not a rule. |
| **Row** | One data row: `[<CHIP>] <subject> SRC=<service>` in that order (v0 "Status row") | **Partial.** `Top3Block.to_lines()` (`render.py:81`) numbers items but does not enforce the `[CHIP] subject SRC=` shape. Delta: add chip+SRC ordering. |
| **Chip** | Bracketed token from the closed six; color secondary; text legible without color | **Exists as data, not a primitive.** Chips are literal strings in pane bodies (`render.py:108` `[LIVE]` etc.) + `StatusChip` enum (`theme.py:330`). Delta: no shared `Chip` renderer; cockpit hardcodes strings (the lint gap, §9). |
| **ServiceRow** | Service row: name + status chip + `SRC=` (Overview/Services) | **New — absent.** Services mode unrendered (`app.py:113`). |
| **RunRow** | RTE run row: run-id + repo·branch + scope + chip + alerts + `SRC=repo-truth-extractor` continuation | **New — absent.** Exists only in A1 HTML (`surfaces/A1-rte-runs-120x40.html`). |
| **ModeBar** | Chrome row of the five modes, active bracketed; `ctrl+k` affordance; no SRC | **Exists (Textual side).** `CockpitModeBar.render()` (`app.py:44`) renders `[ PM ] | 2 ...`. Delta: deterministic-render side lists modes as a header line (`render.py:314`), not a styled bar. |
| **CommandRail** | Chrome action row; no SRC, no authority claim, no transition control | **Partial.** First line of `_command_status_rail` (`render.py:240`). Delta: it currently mixes filter/legality into one line; split command vs status per the grid (rows 36/38). |
| **StatusRail** | Chrome status row; filter/legality/warnings + the single advisory cue; no SRC | **Exists.** Second line of `_command_status_rail` (`render.py:242`) already carries `cue: ADHD_engine: ...; (advisory only)`. This is the canonical advisory-cue site (§7). |
| **Inspector** | Right-column pane: selected detail, `SRC=` per record; demoted vs canonical center | **Exists as data.** `_selected_slice_detail` (`render.py:174`). Delta: no column geometry; needs Frame. |
| **BridgeSegregator** | Hard-divided adapter/proxy pane; labels `[EDGE] adapter-only segregated`; `role: proxied`; `SRC=dopecon-bridge`; never a canonical peer; degrades per viewport | **Exists.** `_bridge_segregator` (`render.py:217`) + `_bridge_role_for_viewport` (`render.py:268`) implement the three-tier degradation (segregator-pane / inspector-lower-detail / inspector-detail-collapsed). The most complete primitive in the renderer. |

**Build order implied by the deltas:** `Frame` + `Rule` first (everything else
needs grid geometry), then `Chip`/`Row` as shared renderers (closes the lint gap),
then the per-mode rows (`ServiceRow`/`RunRow`) once Implementer/Services/Overview/
Events get render functions. `BridgeSegregator`, `PaneHeader`, `StatusRail`, and the
PM `Inspector` already have working logic to wrap.

---

## 6. Filled design-system gaps

D1 §8 records these as ABSENT in both theme layers. v1 fills them for the TUI. They
are token policies, not new colors — every color still comes from
`colors_and_type.css` / `theme.py`.

### 6.1 Spacing / density scale (character grid)

The cockpit has no pixel spacing — spacing is **whole character cells**. The scale is
the set of cell counts the layout is allowed to use; nothing sub-cell, nothing
fractional (`readme.md`: cells are 1ch x 1.25em and the framebuffer refuses
sub-cell drawing).

```
unit            cells   use
s0  flush       0       chip-to-bracket; no gap inside [LIVE]
s1  tight       1       column gutter min; label-to-value within a field
s2  field       2       between fields on a row; list-item indent (see render.py "  1.")
s3  pane        3       pane inner left margin
s4  block       4       between stacked sub-blocks inside a pane
```

Rules: indentation steps in whole cells only (`render.py:84` already uses a 2-cell
`"  {n}. "` indent — that is `s2`). Divider columns and rule rows are fixed by the
grid table (§4), not by this scale; the scale governs *content* spacing inside a
pane. Density target: 120x40 is the design density; 100x32 and 80x24 keep `s1`
gutters and drop to `s2` inner margins to reclaim cells. No fractional leading — the
TUI is one line-height (`--line-height: 1.25`).

### 6.2 Type policy

Single family, single weight file, single size per viewport (`readme.md` Type;
`colors_and_type.css:61`). **There is no type scale and there must not be** —
"emphasis is bold + color, never size." Policy:

- Family: `Iosevka Hue Term` -> JetBrains Mono Nerd Font -> JetBrains Mono ->
  Fira Code -> system mono (`colors_and_type.css:61 --font-mono`).
- Size by viewport (reference cell, not selectable at runtime in a real terminal —
  the terminal owns cell size): `--fs-cell 16px` (120x40), `--fs-cell-sm 14px`
  (80x24), `--fs-cell-lg 18px` (hero). These are preview-card references only.
- Emphasis ladder (no size change): body `--text` -> dim `--text-dim` -> emphasis
  `--text-emphasis` (bold) -> heading `--ritual-cyan` (bold). Headings are
  *emphasized rows*, not larger glyphs.
- Casing (`readme.md` Casing): `lowercase mono` for commands/ids/paths/SRC/run-ids;
  `Title Case` for labels and headings; `UPPERCASE` for chips only.

### 6.3 Motion policy (TEXTUAL_ANIMATIONS levels)

D2 §7C: motion is enforceable at the framework level, not by convention. The
cockpit is a static snapshot renderer (`render.py` is pure); the Textual shell adds
the motion contract.

| Tier | Surface | Motion | Enforcement |
|---|---|---|---|
| **0** | Cockpit core / live data: gauges, sparklines, signal tables/feeds, status chips, all pane content | **Zero** | Always-on data motion competes with the partial-update compositor, distracts (ADHD), and breaks determinism (interpolation = non-reproducible output) |
| **1** | Transient orientation only, **at `full` only**: screen/mode transition, command-palette open/close, toast entry | Opt-in | `animate(..., level="full")` -> auto-suppressed below `full`; screens have no built-in transition, so motion is opt-in by construction |

Operational settings (D2 §5.3, §7C; primary-sourced from the Textual constants/types
APIs):

1. Ship runtime default **`TEXTUAL_ANIMATIONS=basic`** (set explicitly — Textual's
   default is `full`).
2. Tag every Tier-1 animation `level="full"` (auto-suppressed at `basic`/`none`).
3. **`--deterministic` / snapshot mode** = `TEXTUAL_ANIMATIONS=none` +
   `TEXTUAL_SMOOTH_SCROLL=0` + forbid indeterminate `ProgressBar` (`total=None`).
   This makes UI a pure function of state — the precondition for the snapshot tests
   that already lock `render_pm` output
   (`tests/unit/dopemux/ui/cockpit/test_cockpit_render.py`).
4. Expose a reduced-motion toggle flipping `app.animation_level` between
   `basic`/`full`.

This directly contradicts the .Jules web learnings (pulsing timers, "listening"
pulses) — resolved in §7: those are **web-only**.

---

## 7. ADHD reconciliation

The cockpit's doctrine (`ARCHITECTURE_SAFETY_OVERLAY.md` PM/Agent Law; Support Cue
Law) is strict: ADHD support is **advisory only, never a chip, never a gate**. The
`.Jules` learnings (`.Jules/palette.md`) are rich but were authored for the **React
/ MUI web surface** and are **animation-centric** — pulsing timers, "listening"
pulses, soft-confirm glow, copy-success animations. That collides head-on with the
cockpit's zero-motion policy (§6.3; D2 §7C Tier 0; `readme.md`: "Animation.
Effectively none."). The reconciliation is a **split**, not a merge.

### 7.1 The one cockpit status-rail cue (exact spec)

The cockpit's single ADHD affordance is one source-labeled line on the status rail.
It already exists: `render.py:242`:

```
[chrome]  cue: ADHD_engine: focused; suggest 25-min focus block (advisory only)
```

Spec:

- **Location:** status rail only (row 38 at 120x40), never a pane, never the command
  rail.
- **Shape:** `cue:adhd_engine <state>; <suggestion> (advisory)`. `<state>` ∈
  `focused | scattered | steady | low-energy` (mirrors `TMUX_ADHD_ENERGY`).
- **Source-labeled:** the literal token `adhd_engine` names the advisory source
  (Support Cue Law: "narrow, source-labeled cues").
- **Never:** a chip (the closed set is exhaustive), a gate (a blocked workflow is
  blocked by task-orchestrator legality, not a cue — PM/Agent Law), or PM/execution
  truth.
- **Chrome:** carries no `SRC=` and no authority claim (it is chrome, not data) —
  locked by `test_src_only_appears_on_data_rows_never_on_chrome_rail`.
- **One cue, one line.** No second ADHD line, no stacked cues, no per-pane cues.

This is the *only* ADHD element rendered in the deterministic cockpit. The old
`.tmux.conf` `break-reminder`/`energy-check` binds collapse into this single cue
(§3.3).

### 7.2 Focus / HUD overlay (opt-in, cockpit)

A heavier ADHD surface — a Focus/HUD overlay — is permitted **only as an opt-in
modal**, never in the always-on cockpit chrome:

- **Mechanism:** Textual `ModalScreen` or a dedicated Mode (D2 §5.5 — modes are
  independent screen stacks; `ModalScreen` blocks app bindings). Pushed on demand,
  popped to return to the deck.
- **Trigger:** the existing `dopemux focus-mode-toggle` (`.tmux.conf` `bind F`, kept
  as `prefix f`, §3.3). Not auto-triggered — opt-in only.
- **Motion:** the push/pop transition is Tier-1, `level="full"` (auto-suppressed at
  the default `basic`; §6.3). The overlay's *content* is still Tier-0 zero-motion.
- **Content (static equivalents of the web learnings):** focus-block countdown as
  **static text refreshed on tick** (not a pulsing animation); `n/m` task counter;
  absolute completion anchor (`finish at 14:30`) — the time-blindness mitigation
  from `.Jules` 2026-04-30 / 2026-05-14, rendered as text, not motion.
- **Authority:** `domain: operator_support`, `authority: dopemux control surface`,
  `role: chrome`, `next_action: dismiss`. It never gates, never writes, never
  becomes a chip.

### 7.3 The web / cockpit split (where each .Jules learning lands)

| `.Jules/palette.md` learning | Web (Palette) — keep | Cockpit — static equivalent |
|---|---|---|
| 2025-05-14 ADHD-aware pulse on active timer; 2026-04-24 "listening" pulse; 2026-04-26 dynamic empty-state pulse | Keep (MUI animations) | **Drop motion.** Liveness shown by the `*WS STREAM` token / a refreshed `[HH:mm:ss]` line, not a pulse (Tier-0) |
| 2026-05-15 / 2026-05-17 / 2026-05-20 soft 2-step destructive confirm (3s window, gold glow) | Keep on web | Cockpit uses the **Safe Action Gate** typed confirmation (§2.8, T1–T6) — explicit, no timed glow; gate is the safety model, not a pulse |
| 2026-04-30 / 2026-05-14 absolute-time anchor; 2025-05-20 total-remaining; 2026-05-07 n/m counter | Keep on web | **Adopt as static text** in the Focus/HUD overlay (§7.2) and Implementer status (`finish at`, `n of m met`) |
| 2026-04-25 `[HH:mm:ss]` event timestamps | Keep | **Adopt** — Events feed carries static `[HH:mm:ss]` (§4.7) for auditability |
| 2026-03-12 conditional "Clear" on live feed | Keep | Cockpit `RichLog` uses `max_lines` ring-buffer (D2 §7B) — bounded by construction; a `clear` command is allowed (chrome action), no animation |
| 2025-05-22 predictive next-step labels; 2026-03-06 chip tooltips + `tabIndex` | Keep (web a11y) | Cockpit has no tooltips/hover (mouse forbidden); the `next:` field on every pane *is* the predictive label, and chips carry literal tokens (no tooltip needed) |
| 2026-03-25 / 2026-03-26 multi-state connection; 2026-04-26 error-severity alignment | Keep (web) | Cockpit maps to the closed chip set: connecting/degraded -> `OVERRIDE` or literal `unknown`; failure -> `BLOCKER` (`acceptance.md` external-vocab mapping) |

**Net:** every `.Jules` learning is honored — its *intent* (temporal grounding,
closure, safe destructive actions, liveness) is preserved, but **motion stays on
web**; the cockpit takes the static, deterministic, gate-based equivalent. This is
the "web split" the v0 caveat anticipated ("ADHD/lifestyle features are
advisory/future-only").

---

## 8. Voice / tone placement

Brand voice is set by `BRAND_SYSTEM.md`; the TUI inherits it (`readme.md` Content
fundamentals). v1 places voice by surface so persona never leaks into operator
chrome.

| Surface | Voice | Rule |
|---|---|---|
| **Persona / banner** (CLI launch, non-cockpit) | `VoiceMode.BANNER` (`voice/core.py select_mode`: short intent ≤40 chars -> BANNER) | Persona is allowed *outside* the cockpit grid — launch banners, CLI greetings |
| **Cockpit chrome** (mode bar, command rail, status rail, frame) | Suppressed | Terse, procedural, source-labeled. No persona, no jokes, no mascot. The one advisory cue (§7.1) is the only "human" line, and it is clinical |
| **Cockpit data rows** | None | Pure record: `[CHIP] subject SRC=service`. Voice does not touch data |
| **Errors / blockers** | `Problem: / Why: / Fix: / NEXT:` | Every failure panel, every surface (`readme.md` Sentence shapes; `acceptance.md` Error/blocker anatomy). Example in §4.8 |

Forbidden vocabulary (v0 list; the real enforcement is §9): `probably`, `maybe`,
`I think`, `as an AI`, `magic`, `brain`, `autonomous`, `smart`, `seamless`,
`next-gen`, `all set`, `everything looks good`, `supercharged`; and the directional
arrow glyphs (U+2192 `RIGHTWARDS ARROW`, U+21D2, U+279C) plus the ellipsis (U+2026)
and a literal three-dot `...` — use `->` if directionality is required. Forbidden
chips (fail the validator if rendered):
`UNKNOWN, DEGRADED, FAILED, BLOCKED, SYNC, DRAFT, READY, SUCCESS, ERROR` — the
closed set is the only set. `UNKNOWN` stays literal text, never a chip.

Success is one line (`Started: MCP services for current workspace.`). Failure is
always the four-part panel. Status rows are always `[<CHIP>] <subject> <SRC=service>`
in that order.

---

## 9. Text-validation contract

This is the v0 correction made executable. v0 claims enforcement via
`cockpit/tokens.py::validate_rendered_text` — **which does not exist** (§1.3). The
contract:

### 9.1 The real path (today)

1. `services/shared/brand_voice.py:55 brand_text()` -> `validate_or_fallback(...)`
   — chip-prefixed voice-safe text at the service layer.
2. `src/dopemux/voice/core.py:182 validate_output(surface, mode, text, gates)` —
   lexical gates (`hard_avoid_phrases`, `soft_avoid_phrases`) + structural gate
   (`required_closers`). `select_mode` routes `Surface.UI -> VoiceMode.UI_STRICT`.
3. `scripts/brand_lint.py:62 AUDITED_PYTHON_FILES` — static AST lint; **cockpit not
   in the list** (confirmed: list contains `theme.py`, `voice/core.py`,
   `brand_voice.py`, dashboards — not `ui/cockpit/*`).
4. `src/dopemux/ui/theme.py:330 StatusChip` — the closed six-chip enum.

### 9.2 Two gaps to close

**Gap A — no `validate_rendered_text`.** Implement it, or route cockpit render text
through `voice/core.py::validate_output`. Recommendation: a thin
`cockpit/validate.py::validate_rendered_text(text) -> list[Violation]` that checks
(a) banned vocabulary + arrow glyphs, (b) only closed-set chips appear bracketed,
(c) no `SRC=` on chrome rows, (d) no forbidden phrases from
`ARCHITECTURE_SAFETY_OVERLAY.md`. Wire it into the render path and assert in the
existing test module (which already locks four-field, Top-3, SRC-chrome, and
forbidden-phrase invariants — extend it).

**Gap B — the closer-enforcement asymmetry.** `validate_output` enforces
`required_closers` **only for `Surface.CLI` and `Surface.AGENT`** (`core.py:182`,
the `if surface in (Surface.CLI, Surface.AGENT)` branch). `Surface.UI -> UI_STRICT`
does **not** enforce required closers. So routing cockpit error text as `Surface.UI`
will **not** enforce the `Problem/Why/Fix/NEXT` structure on its own. Two options:
(1) validate cockpit *error panels* as `Surface.CLI` so the closer gate fires, or
(2) add the four-part check to the new `validate_rendered_text`. Do **not** claim
`validate_output` covers error structure for UI — it does not.

### 9.3 brand_lint coverage

Add the cockpit files to `scripts/brand_lint.py:62 AUDITED_PYTHON_FILES`:
`src/dopemux/ui/cockpit/render.py`, `app.py`, `runtime_contract.py`. This brings the
hero surface under the same banned-vocab / chip AST lint as the rest of the UI. Until
this lands, every `[LIVE]`/`[LOGGED]`/`[EDGE]` literal in `render.py` is unchecked
(D1 §3 "Critical gap"). This is acceptance item §11 (lint coverage), and it is also
one of the broader Wave-8 CI-gate items (D1 §4).

---

## 10. Accessibility criteria

D2 §6 (a11y-terminal stream) returned `API Error` and was `NOT_SYNTHESIZED`, so the
*external* WCAG-equivalent screen-reader/keyboard criteria are **`PENDING (D2 stream
re-run)`**. What v1 *can* deliver from primary evidence: measured contrast (computed
here, not asserted), `NO_COLOR` behavior (from runtime), and the keyboard model
(from `acceptance.md` + runtime).

### 10.1 Contrast pairs — measured WCAG 2.x ratios

Computed from the real hexes in `colors_and_type.css` (WCAG relative-luminance
formula; sRGB). Bars: **4.5:1** normal text, **3.0:1** large text / non-text
(frame rules, borders count as non-text). Both backgrounds tested:
`--surface-black #020617` (outer) and `--surface-navy #041628` (inset/selected row).

| Token | hex | on #020617 | on #041628 | text >=4.5 | non-text >=3.0 |
|---|---|---:|---:|---|---|
| `--text` | #E2E8F0 | 16.36:1 | 14.81:1 | PASS | PASS |
| `--text-emphasis` | #94FADB | 16.29:1 | 14.74:1 | PASS | PASS |
| `--ritual-cyan` (heading/LIVE/EDGE) | #7DFBF6 | 16.33:1 | 14.78:1 | PASS | PASS |
| `--serum-mint` (LOGGED) | #94FADB | 16.29:1 | 14.74:1 | PASS | PASS |
| `--mint-bright` | #B4FFEE | 17.75:1 | 16.06:1 | PASS | PASS |
| `--gilt-edge` (OVERRIDE) | #F5F26D | 17.10:1 | 15.47:1 | PASS | PASS |
| `--saint-gold` | #FFCF78 | 13.88:1 | 12.56:1 | PASS | PASS |
| `--gremlin-pink` (BLOCKER) | #FF8BD1 | 9.48:1 | 8.57:1 | PASS | PASS |
| `--text-dim` (labels) | #94A3B8 | 7.87:1 | 7.12:1 | PASS | PASS |
| `--mint-dim` (rule lines / borders) | #4A9E94 | 6.35:1 | 5.74:1 | PASS | PASS |
| `--aftercare-violet` (AFTERCARE) | #9B78FF | 6.27:1 | 5.67:1 | PASS | PASS |
| `--text-muted` (metadata) | #64748B | 4.24:1 | 3.84:1 | **FAIL** (text) | PASS |
| `--violet-dim` | #6B4FBF | 3.36:1 | 3.04:1 | **FAIL** (text) | PASS |
| `--text-disabled` (unavailable) | #475569 | 2.66:1 | 2.41:1 | **FAIL** | **FAIL** |

**Honest findings (these feed §11, not massaged):**

1. **All six status-chip colors PASS at the 4.5:1 text bar on both backgrounds.** The
   chip palette is contrast-clean. (Lowest chip: AFTERCARE 5.67:1 on navy.)
2. **`--mint-dim` (frame/rule/border color) PASSES even the 4.5 text bar**
   (6.35 / 5.74) — frames are comfortably legible; well clear of the 3.0 non-text
   bar.
3. **`--text-muted` FAILS the 4.5 text bar** (4.24 black / 3.84 navy) but clears 3.0.
   Action: restrict `--text-muted` to non-text/decorative metadata, or promote
   metadata that must be read to `--text-dim` (7.87/7.12, PASS).
4. **`--violet-dim` FAILS text (3.36/3.04)**; acceptable only as a non-text accent.
5. **`--text-disabled` FAILS both bars** (2.66/2.41). WCAG exempts disabled
   controls from contrast minimums, so this is *permissible only for genuinely
   disabled/unavailable affordances* — never for readable content. Flag it in §11 so
   it is not used as a content color.

### 10.2 NO_COLOR preservation

Color encodes state but is never the *only* carrier (`readme.md` Color;
`colors_and_type.css:121 .render-plain`). Under `NO_COLOR=1` / monochrome:

- Every chip carries a literal bracketed token (`[LIVE]`, `[BLOCKER]`, and the rest of
  the closed set) so removing color loses no signal — this is *why* the chip set is
  literal.
- Nerd Font glyphs fall back to ASCII via `theme.py Glyphs._FALLBACK`
  (`SUCCESS -> ✓`, `ERROR -> ✗`, `BLOCKED -> #`).
- `render_audit` (`render.py:338`) and `render_pm(plain=True)` already emit ANSI-free
  text — the audit/plain path *is* the NO_COLOR path, and the snapshot tests run
  against it.
- The three contrast fails above are color-channel issues only; in monochrome the
  literal tokens carry state regardless.

### 10.3 Keyboard model

- **Mouse forbidden** (`readme.md` Hover/press). All selection is keyboard.
- Active row marked by a leading `>` glyph in column 1 (`render.py` services pattern;
  shown in §4.5), not a hover highlight.
- Keybind affordances are bracketed (`[N]`, `R1`..`R6`, `ctrl+k`) — visible, not
  hidden behind hover.
- Palette is `ctrl+k` in the TUI, never `⌘K` (`acceptance.md` Command glyphs);
  `⌘K` is allowed only on the web surface.
- `q` quits (`app.py:74 BINDINGS`). Mode switch `1`..`5`; gate/focus per §3.3.
- **`PENDING (D2 stream re-run)`:** formal screen-reader testing matrix and the
  keyboard-only completeness criteria require the a11y-terminal stream; do not set
  those acceptance gates from mechanism alone.

---

## 11. Acceptance checklist

Extends `acceptance.md`. Every box is checkable against this spec or the runtime.
v0's existing boxes (Tokens, Status taxonomy, Chrome-vs-data, Authority boundaries,
Surface separation, Typography, Adaptation, Error anatomy, Handoff) remain in force;
v1 adds the boxes below. `[x]` = satisfied by this spec/runtime; `[ ]` = work item
(named, not hidden).

### 11.1 Doc-vs-runtime reconciliation

- [x] v0's `tokens.py/frame.py/model.py/validate_rendered_text` references are
      corrected; the real files are named (§1.3).
- [x] The real enforcement path is documented (`brand_voice.py` -> `voice/core.py`
      -> `brand_lint.py` -> `StatusChip`) (§1.3, §9).
- [ ] `validate_rendered_text` implemented (or cockpit routed through
      `voice/core.py`) (§9.2 Gap A).
- [ ] Cockpit files added to `brand_lint.py AUDITED_PYTHON_FILES` (§9.3).
- [ ] Error-panel closer enforcement resolved (validate as `Surface.CLI` or add the
      four-part check) — `validate_output` does NOT enforce closers for `Surface.UI`
      (§9.2 Gap B).

### 11.2 IA

- [x] Exactly five modes in runtime order PM, Implementer, Overview, Services, Events
      (`render.py:33`); no sixth (§2).
- [x] Four global surfaces named verbatim from runtime (`runtime_contract.py:30`):
      Command Palette, Settings/Admin/Runtime, Safe Actions / Proof Gate,
      Unknown / Drift Queue (§2.6–2.9).
- [x] Every mode and surface carries the four-field declaration
      (domain/authority/role/next_action) (§2).
- [x] Command Palette is broker-only, never executes (§2.6).
- [x] Safe Action Gate is cross-cutting (not a mode); auto-confirm forbidden; T4
      blocked until remote-mutation policy; TX/TU never execute (§2.8).
- [x] Unknown/Drift Queue is non-executable; no in-queue reclassification;
      read-only affordances only (§2.9).

### 11.3 Frame & mockups

- [x] Mockups exist at 120x40, 100x32, 80x24 for PM; 120x40 for Implementer,
      Services, Overview, Events; plus the below-80x24 BLOCKER panel (§4).
- [~] Mockup frames are drafted to the readme.md grid; exact per-line width is a Frame-primitive invariant enforced at implementation time, not re-measured in this design pass (§4).
- [x] Divider columns and rule rows match the `readme.md` Layout table at each size
      (§4).
- [x] Bridge degrades per viewport: segregator-pane (120x40) ->
      inspector-lower-detail (100x32) -> inspector-detail-collapsed (80x24)
      (`render.py:268`; §4.1–4.3).
- [x] Authority/SRC/chips annotated on every mockup; SRC only on data rows, never on
      chrome (§4).

### 11.4 Components

- [x] All twelve primitives have a render contract and an honest delta vs `render.py`
      (§5).
- [x] Deltas state "new; absent from renderer" where true (Frame, Rule, ServiceRow,
      RunRow) rather than implying the class exists (§5).

### 11.5 Filled gaps

- [x] Spacing/density scale defined in character cells (§6.1).
- [x] Type policy: single family/weight, no size scale, bold+color emphasis (§6.2).
- [x] Motion policy: `TEXTUAL_ANIMATIONS=basic` default, Tier-1 `level="full"`,
      `--deterministic` = `none` + smooth-scroll off + no indeterminate bars (§6.3).

### 11.6 ADHD

- [x] Exactly one status-rail advisory cue, source-labeled, never a chip/gate
      (`render.py:242`; §7.1).
- [x] Focus/HUD is an opt-in modal, Tier-1 transition, Tier-0 content, never chrome
      (§7.2).
- [x] Every `.Jules` learning is assigned to web (motion) or cockpit (static
      equivalent) (§7.3).
- [x] tmux status segments strip emoji and reduce to the single cue (§3.2).

### 11.7 Voice

- [x] Persona allowed only outside the cockpit grid; cockpit chrome is suppressed
      voice; data rows carry no voice (§8).
- [x] Errors use Problem/Why/Fix/NEXT on every surface (§4.8, §8).
- [x] Forbidden vocabulary + forbidden chips enumerated; `UNKNOWN` stays literal
      (§8).

### 11.8 Accessibility

- [x] Contrast computed, not asserted; pass and fail both reported (§10.1).
- [x] All six chip colors pass 4.5:1 on both backgrounds (§10.1).
- [ ] `--text-muted` restricted to non-text use or readable metadata promoted to
      `--text-dim` (fails 4.5 text) (§10.1 finding 3).
- [ ] `--text-disabled` used only for genuinely disabled affordances, never content
      (fails both bars) (§10.1 finding 5).
- [x] `NO_COLOR` preserves all signal via literal tokens + ASCII glyph fallback;
      audit/plain path is ANSI-free (§10.2).
- [x] Keyboard model documented (mouse forbidden, `ctrl+k`, `>` active row) (§10.3).
- [ ] **`PENDING (D2 stream re-run)`:** screen-reader testing matrix + keyboard-only
      completeness criteria (a11y-terminal stream was rate-limited) (§10).

### 11.9 Claude Design gate (from CLAUDE_DESIGN_BLOCKERS.md §3)

D3 is DIRECTION, not approved final screens. These eight conditions gate final-screen
approval (`out/cockpit-ia-reconcile/.../CLAUDE_DESIGN_BLOCKERS.md` §3). All are
**open** at HEAD `755bf38460`:

- [ ] 1. Command Palette broker wired + conformant (`TP-DMX-COCKPIT-COMMAND-PALETTE-001`).
- [ ] 2. Safe Action Gate wired across all non-read affordances; TX/TU fail closed
      (`TP-DMX-COCKPIT-SAFE-ACTIONS-001`).
- [ ] 3. Settings/Admin/Runtime exists as a secondary surface with per-flow gates
      (`TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`).
- [ ] 4. Unknown/Drift Queue wired + visible + non-executable
      (`TP-DMX-COCKPIT-UNKNOWN-DRIFT-001`).
- [ ] 5. Package IA reconciled to five modes + four surfaces, no sixth-mode
      regression (`TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA`).
- [ ] 6. Runtime renderer validated against `SCREEN_CONTRACT_MATRIX.md`; no
      destructive affordances for blocked rows (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`).
- [ ] 7. Inventory regenerated against current HEAD; counts reconciled or explicit
      `UNKNOWN`.
- [ ] 8. Open `EVIDENCE_LEDGER.md` UNKNOWNs reduced (decision subcommands, optional
      `genetic`, `worktree`/`vault`, root `RULES.md`/`TRUTH_*.md`).

Until all eight hold, the cockpit must not be presented as ready for final screens
(`safe_for_claude_design: NO`). Conditional primitive drafting (this spec, the named
packets) is permitted as pre-design input (`CLAUDE_DESIGN_BLOCKERS.md` §5).

### 11.10 Doctrine

- [x] No fabricated direction winner / score / graft list — the three directions
      were API errors; v1 synthesizes verified substrate only (§1.2).
- [x] Items gated on D2's failed research streams are marked `PENDING (D2 stream
      re-run)`, not backfilled (§7D-equiv, §10).
- [x] Runtime outranks docs throughout; conflicts (mode order, surface names) resolved
      to runtime with cites (§2).
- [x] `UNKNOWN` preserved as literal wherever authority/tier is unproven; never
      collapsed to `EDGE` (§2.7, §2.9).
