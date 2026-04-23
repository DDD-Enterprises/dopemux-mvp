---
id: tui-spec-v2
title: Dopemux TUI Specification v2.0a
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-23'
last_review: '2026-04-23'
next_review: '2026-05-23'
prelude: Terminal UI specification for Round 2 operator shell redesign from service-centric to workflow-centric IA.
---

# Dopemux TUI Specification v2.0a

**Date**: 2026-04-23
**Version**: 2.0a (Clarifications Pass 1)
**Status**: Ready for implementation planning

## 1. Design Interpretation

This specification defines the terminal-native operator shell for Dopemux Round 2, transitioning from a service-centric 7-tab information architecture (v1.0) to a workflow-centric dual-mode operator interface. The TUI is authored in the PM and Implementer roles and surfaces split task, decision, and chronicle authorities through explicit authority labeling and per-field provenance tagging.

**Non-goals**: web framing, HTML/DOM, mouse, hover effects, automation-invoked human actions, unified task records, unified PM or Implementer records.

**Authority**: This spec is normative for Terminal UI layout, interaction, and visual tokens. Per-backend HTTP/RPC contracts and role models are still UNKNOWN and will block specific implementation steps.

---

## 2. Information Architecture

### 2.1 Top-Level Mode Strip

**Five modes** (not seven tabs):
1. **PM** — Project management and feature design. Surfaces Leantime metadata visibility, ConPort decisions/progress/context, dope-memory historical receipts, task-orchestrator workflow state, and generation of PM→Implementer handoff packets.
2. **Implementer** — Implementation and review. Surfaces current task focus, linked acceptance criteria, linked decisions and chronicle, dope-context retrieval, debugging/validation/execution, and Implementer→PM handback packets.
3. **Overview** — System status, health, and event log. Read-only view of all services and queue state.
4. **Services** — Service registry, health endpoints, routing, and debug logs.
5. **Events** — Real-time event stream, filters, tail history.

Tasks, Decisions, Memory, and Search are demoted to supporting views reached by `g o` / `g d` / `g m` / `g s` from any mode, or by `Enter` drill-down on a pane row.

### 2.2 Grid Geometry

**Primary**: 120×40 (columns × rows)
- Row 0, 119: borders
- Row 1: mode strip + global status
- Row 2–4: pane headers and authority labels
- Row 5–34: body (split vertically at column 25 and 84)
- Row 35: command line
- Row 36–37: feedback
- Row 38: status rail

**Adaptive**: 100×32 and 80×24 with pane reflow and truncation.

### 2.3 Pane Structure (PM and Implementer Modes)

**Left rail** (columns 1–24, rows 5–34):
- Task list or workflow queue, scoped by mode
- Each row shows: `[glyph] task-id / title [unread-indicator]`
- Pane authority: `task-orchestrator` for workflow state

**Center** (columns 26–83, split at row 25):
- **Top** (rows 5–24): Primary pane (Leantime metadata, ConPort decisions, task details)
- **Bottom** (rows 25–34): Secondary pane (related items, drill-down, handoff packets)
- Pane authorities: task-orchestrator, leantime, conport, dope-memory (per row, tagged `SRC`)

**Inspector** (columns 85–118, rows 5–22):
- Detailed view of selected row
- Authority labeled at top
- Rows 23–34 reserved for Bridge adapter debug output

### 2.4 Handoff Packet Model

#### 2.4.1 Send Semantics

`[H] send` is a human-only dopemux authoring action that converts a draft PM→Implementer packet (`PKT-*`) or Implementer→PM packet (`PKB-*`) into a sent packet. Send is performed in dopemux and produces exactly two mirror writes:
1. One ConPort progress/log entry chipped `[LOGGED]`
2. One dope-memory chronicle receipt chipped `[LOGGED]`

Send does **not** trigger a task-orchestrator state transition and does **not** mutate Leantime metadata.

#### 2.4.2 Packet Lifecycle

- **Draft**: authored in dopemux, not visible in inspector
- **Sent (Active)**: visible in inspector with `sent_at` timestamp; remains active for 30 days
- **Archived**: after 30 days, moved to history/search
- **Pinned**: exempt from auto-archive, marked with `[PIN]` chip at archive threshold

Pin state is carried on the envelope and mirrored on the dope-memory chronicle receipt. Unpin writes a new receipt with `pinned_at: null`.

---

## 3. Authority Mapping

### 3.1 Service Domain Table

| Domain | Service | Authority Role | Canonical Operations |
|--------|---------|------------------|----------------------|
| Workflow state | task-orchestrator | Approver / Operator | status, queue order, blockers, approvals |
| Metadata | leantime | Operator | title, description, assignee, labels, due date, estimate, linked references |
| Decisions | conport | Operator | decision log, progress entry, pattern storage |
| History | dope-memory | System | chronicle receipt, pin state, archive entries |
| Retrieval | dope-context | System | code search, doc search, codebase navigation |
| Execution | dopetask | System | task runner, no state ownership |
| Bridge adapter | dopecon-bridge | Tier-2 (shift-Y) | adapter-only, never canonical |

### 3.2 Four Authority Prevention Mechanisms

1. **Authority label** on every pane header (`authority: <service>`)
2. **SRC tag** on every row (`SRC: <service>`)
3. **Visual segregation** of Bridge subpanel with gold hazard footer below inspector horizontal rule
4. **Write-confirm modal** naming target service (`WRITE -> <service> : <action>`)

### 3.3 Write Refusals

The following writes are forbidden:
- Leantime status transitions (route to task-orchestrator)
- Leantime queue reordering (route to task-orchestrator)
- Leantime blocker resolution (route to task-orchestrator)
- Leantime approval-state mutation (route to task-orchestrator)
- Any Bridge write without `shift-Y` confirm (requires Tier-2 acknowledge)
- Any automation-invoked `[H]` send (human-only action)
- Any write to dopetask state (execution-only, no canonical ownership)

### 3.4 Leantime Write Scope

**Allowed** (metadata only):
- title
- description / notes
- assignee
- labels / tags
- due date / dates
- estimate
- linked identifiers / references

**Forbidden** (workflow-significant):
- status transitions
- queue reordering
- blocker resolution
- approval-state mutation

### 3.5 PM-Mode Authority Split

| Intent | Canonical Service | Confirm Label | Blocks |
|--------|-------------------|---------------|--------|
| Metadata write | leantime | `WRITE -> leantime : <field>` | Step 8+ |
| Workflow write (status, queue, blockers, approvals) | task-orchestrator | `WRITE -> task-orchestrator : <action>` | Step 8+ |
| Decision / progress write | conport | `WRITE -> conport : <action>` | Step 9+ |
| History receipt | dope-memory | `WRITE -> dope-memory : <action>` | Step 11+ |

**Note**: A pane displaying a field does not imply that pane's backing service owns that field. The confirm modal's target service name is canonical.

---

## 4. ASCII Mocks (120×40)

### 4.1 PM Mode Home

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [1] PM    [2] Implementer  [3] Overview  [4] Services  [5] Events   │ workspace: dopemux-mvp  │ today: 2026-04-23 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                           │
│ LEFT RAIL: TASK LIST              │ CENTER: PRIMARY (rows 5-24)                                 │ INSPECTOR        │
│ authority: task-orchestrator      │ authority: leantime + conport + task-orchestrator          │ authority: mixed │
├──────────────────────────────────┼────────────────────────────────────────────────────────────┼──────────────────┤
│  > [LIVE]   T-1203               │ title: Refactor auth module    │ related decisions:           │ Packet PKT-481   │
│    [BLOCKER] T-1205              │ assignee: @alice               │ ADR-042 (JWT schema)         │ sent: 2026-04-22 │
│    T-1198 [unread PKT]           │ due: 2026-04-30                │ ADR-039 (session mgmt)       │ from: PM         │
│    T-1192                        │ estimate: 8h                   │                              │ to: Implementer  │
│                                  │ SRC: leantime                                                    │ [PIN]            │
│                                  │ description: Implementation of OpenID Connect for...            │ NEXT: [a]pprove  │
│                                  │ progress entry: conport                                          │ or [x]close      │
│                                  │ status: in_progress [SRC: task-orchestrator]                    │                  │
│                                  │ linked_tasks: [T-1205, T-1192]                                   │                  │
│                                  │                                                                  │                  │
├──────────────────────────────────┼────────────────────────────────────────────────────────────┼──────────────────┤
│                                  │ CENTER: SECONDARY (rows 25-34)                               │ authority: mixed │
│                                  │ related decisions: ADR-042, ADR-039                          │ ─━━ BRIDGE ADAPTER DEBUG ━━━ │
│                                  │ related tasks: T-1195, T-1201 [SRC: task-orchestrator]      │ adapter: idle    │
│                                  │ chronicle: [LOGGED] handoff sent 2026-04-22 [SRC: dope-memory]│ shift-Y required │
│                                  │ HANDOFF PACKET DRAFT PKT-482 [H] send [c] clear [p] pin     │                  │
│                                  │ COMMAND HISTORY > [a] approve PKB-481 [✓] decision logged    │                  │
├──────────────────────────────────┼────────────────────────────────────────────────────────────┤                  │
│ [g] global [n] next [p] prev     │ command: _                                                     │ [g o] go Tasks   │
│ [g o]Tasks [g d]Decisions        │ feedback: Ready.                                               │ [g d] Decisions  │
│ [g m]Memory [g s]Search          │                                                                │ [g m] Memory     │
├──────────────────────────────────┴────────────────────────────────────────────────────────────────┴──────────────────┤
│ ✓ PM plane ready │ ⏳ task-orchestrator: live │ ⏳ leantime: synced │ ✓ conport: 127 entries │ ⏳ dope-memory: live │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Implementer Mode Home

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [1] PM    [2] Implementer  [3] Overview  [4] Services  [5] Events   │ workspace: dopemux-mvp  │ today: 2026-04-23 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                           │
│ LEFT RAIL: CURRENT TASK          │ CENTER: PRIMARY (rows 5-24)                                 │ INSPECTOR        │
│ authority: task-orchestrator     │ authority: conport + context + dopetask                      │ authority: mixed │
├──────────────────────────────────┼────────────────────────────────────────────────────────────┼──────────────────┤
│  > [LIVE] T-1203                 │ task: T-1203                   │ recent commits:              │ Packet PKB-481   │
│    [BLOCKER] T-1205              │ acceptance criteria:            │ commit: 3ca12e (auth review) │ sent: 2026-04-22 │
│    [unread PKB] T-1192           │ - login form works             │ branches: feature/auth       │ from: Implementer│
│    T-1198                        │ - token validation OK           │ test status: 15/16 passing   │ to: PM           │
│                                  │ - MFA optional [SRC: task-orchestrator]                       │ [PIN]            │
│                                  │ linked decision: ADR-042                                       │ NEXT: [a]pprove  │
│                                  │ [LOGGED] decision link from conport progress entry             │ or [x]close      │
│                                  │                                                                  │                  │
├──────────────────────────────────┼────────────────────────────────────────────────────────────┼──────────────────┤
│                                  │ CENTER: SECONDARY (rows 25-34)                               │ authority: mixed │
│                                  │ recent commits: 3ca12e (auth review) [SRC: dopetask]        │ ─━━ BRIDGE ADAPTER DEBUG ━━━ │
│                                  │ code navigation: src/auth.py:45 [✓], tests/test_auth.py:120 [!]│ adapter: idle  │
│                                  │ HANDBACK PACKET DRAFT PKB-482 [H] send [c] clear [p] pin    │ shift-Y required │
│                                  │ EVIDENCE LINKS PR: #298, Test run: passed                    │                  │
├──────────────────────────────────┼────────────────────────────────────────────────────────────┤                  │
│ [g] global [n] next [p] prev     │ command: _                                                     │ [g o] go Tasks   │
│ [g o]Tasks [g d]Decisions        │ feedback: Ready to send handback.                              │ [g d] Decisions  │
│ [g m]Memory [g s]Search          │                                                                │ [g m] Memory     │
├──────────────────────────────────┴────────────────────────────────────────────────────────────────┴──────────────────┤
│ ✓ Implementer plane ready │ ✓ task-orchestrator: live │ ✓ conport: linked │ ✓ dope-context: ready │ ✓ dopetask: live │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Grid Invariants

- **Every pane header** names its authority and sources (`authority: <service>`)
- **Every row** carries an `SRC:` tag identifying the canonical service
- **Column alignment**: fixed. Rows reflow only on pane resize.
- **Glyphs**: closed set only (`*`, `~`, `o`, `x`, `>`, border chars, mint neon).
- **Colors**: closed set of DOPEMUX_THEME tokens (chip.*, text.*, table.*, etc.)
- **Write confirms**: always name target service in confirm modal

### 4.4 Supporting Views (100×32)

Supporting views (Tasks, Decisions, Memory, Search) are reached via `g o`, `g d`, `g m`, `g s` and render in a 100×32 layout with pane borders and scrollable content. Layout is identical to the primary view's center + inspector areas stacked vertically.

**Note**: The 7-tab strip shown in these mocks is v1.0 cosmetic carry-over. Implementation must render the 5-tab strip from §2.1.

### 4.5 Compact Layout (80×24)

On 80×24 terminals:
- Left rail: task ID + glyph only
- Center: single pane, vertical split at row 12
- Inspector: hidden, accessible via `[i]nspect` command
- Mode strip: abbreviated (`P I O S E`)
- Command line: at row 22

---

## 5. Interaction Model

### 5.1 Command Set

**Global**:
- `[g] g` — go to (followed by mode or view letter)
- `[n]` — next item
- `[p]` — prev item
- `[j] [k]` — vim-style navigation
- `[?]` — help

**Mode navigation**:
- `[g o]` — go to Tasks supporting view
- `[g d]` — go to Decisions supporting view
- `[g m]` — go to Memory supporting view
- `[g s]` — go to Search supporting view

**Item actions**:
- `[Enter]` — drill-down (open inspector for selected item)
- `[i]` — inspect detail (same as Enter)
- `[e]` — edit (routed to correct authority based on field)
- `[H] send` — send draft packet (human-only, dopemux authoring)
- `[c]` — clear / cancel draft (mode-dependent)
- `[p]` — pin packet (dope-memory ownership, with confirmation)
- `[o]` — open full view (expand to supporting view)
- `[x]` — close / abandon draft (with confirmation)
- `[a]` — approve task (role-gated, task-orchestrator-only)

**Meta**:
- `[q]` — quit
- `[:]` — command mode (ex-style)

### 5.2 Modal Workflows

**Send packet**:
```
[H] send  →  confirm modal names target (ConPort + dope-memory)  →  writes both  →  marks sent_at  →  pin offered
```

**Approve task**:
```
[a] approve  →  role check  →  confirm modal → task-orchestrator write  →  return to mode
```

**Pin packet**:
```
[p] pin  →  dope-memory receipt updated  →  `pinned_at` set  →  exempt from 30-day archive
```

### 5.3 Keyboard vs Mouse

- **Mouse**: disabled. No hovering, clicking, or selection.
- **Keyboard**: all navigation and action via explicit command.

### 5.4 Confirm Modal Bodies

All write confirms follow this pattern:

```
┌─────────────────────────────────┐
│ Confirm: <action>               │
├─────────────────────────────────┤
│ target: <canonical service>     │
│ action: <field or state change> │
│ affected: <item id and scope>   │
│                                 │
│ [Y]es [N]o [?]help              │
└─────────────────────────────────┘
```

**Examples**:
- `WRITE -> leantime : title` — metadata
- `WRITE -> task-orchestrator : status = in_progress` — workflow
- `WRITE -> conport : decision logged` — decision
- `WRITE -> dope-memory : pinned` — history
- `ADAPTER -> dopecon-bridge : fallback-read` — bridge (requires `shift-Y`)

---

## 6. Pane Specifications

### 6.1 Left Rail (Task List / Workflow Queue)

**Columns**: icon (1) + glyph (1) + id (6) + title (15) + unread (1) = 24 chars

**Row format**: `[glyph] T-1234 task title [indicator]`

**Glyphs**:
- `>` — selected
- `*` — in_progress
- `~` — pending
- `o` — open
- `x` — closed / blocked
- `!` — warning

**Unread indicators**:
- `⊕` — unread PKT (in PM mode)
- `⊖` — unread PKB (in Implementer mode)
- empty — no unread packets

**Authority**: always `task-orchestrator` for workflow state (status, queue order).

### 6.2 Center Pane (Task Details + Handoff Packets)

**Top (rows 5–24)**: task metadata and decision links.
**Bottom (rows 25–34)**: handoff packet draft / active packet view.

**Row format**: `field_name: value [SRC:service]`

**Authority**: mixed — each row tagged with its canonical service (leantime, task-orchestrator, conport, dope-memory).

### 6.3 Inspector (Detailed View)

**Columns 85–118, rows 5–22**:
- Expanded view of selected row
- Scrollable if content > 16 lines
- Authority labeled at header

**Rows 23–34**: Bridge adapter debug output (only if `dopecon-bridge` is active). Segregated with gold hazard footer (`━━━ BRIDGE ADAPTER DEBUG (shift-Y to ack) ━━━`).

### 6.4 Command Line

**Row 35**: single-line text input

**Execution**: on `[Enter]`, parse command and dispatch to handler.

### 6.5 Feedback / Status Rail

**Rows 36–37**: brief status messages (errors, confirmations, help hints).

**Row 38**: service health and last-activity timestamps.

### 6.6 Action Suffix Rules

Every user action in a confirm modal must include the target service name and action descriptor:

- **Metadata**: `WRITE -> leantime : <field-name>`
- **Workflow**: `WRITE -> task-orchestrator : <state-change>`
- **Decision**: `WRITE -> conport : <decision|progress-entry>`
- **History**: `WRITE -> dope-memory : <receipt-type>`
- **Bridge**: `ADAPTER -> dopecon-bridge : <action>` (shift-Y required)

---

## 7. Visual Token Mapping

### 7.1 Chip Typography (Closed Vocabulary)

| Chip | Style | Meaning | Use |
|------|-------|---------|-----|
| `[LIVE]` | chip.live (cyan) | Active / running process | Task in progress, live service |
| `[BLOCKER]` | chip.blocker (pink) | Blocking error | Task stuck, critical issue |
| `[OVERRIDE]` | chip.override (gold) | Manual override | Scope edge crossed, decision override |
| `[LOGGED]` | chip.logged (mint) | Successfully recorded | Packet sent, decision logged |
| `[AFTERCARE]` | chip.aftercare (violet) | Post-action follow-up | Requires follow-up decision |
| `[PIN]` | chip.logged (mint) | Pin exemption from archive | Pinned packet at archive threshold |
| `[EDGE]` | chip.edge (cyan) | Scope edge crossed (pending brand review) | Boundary condition flagged |

### 7.2 Glyph Set

| Glyph | Unicode | Nerd Font | Fallback | Color | Meaning |
|-------|---------|-----------|----------|-------|---------|
| `*` | U+002A | — | `*` | info | Task in progress |
| `~` | U+007E | — | `~` | text.dim | Pending / waiting |
| `o` | U+006F | — | `o` | info | Task open |
| `x` | U+0078 | — | `x` | error | Task closed / blocked |
| `>` | U+003E | `\uf054` | `>` | mint | Selection / current item |
| `✓` | U+2713 | — | `✓` | success | Checked / passed |
| `!` | U+0021 | — | `!` | warning | Warning / attention |
| Border | U+250x | — | `-/\|` | mint.dim | Box drawing |

### 7.3 ANSI Palette

| Token | Hex | RGB | WCAG AA | Use |
|-------|-----|-----|---------|-----|
| ritual.cyan (mint) | #7DFBF6 | 125, 251, 246 | AAA (15.2:1) | Primary accent |
| serum.mint (mint.soft) | #94FADB | 148, 250, 219 | AAA (13.9:1) | Data emphasis |
| gremlin.pink (magenta) | #FF8BD1 | 255, 139, 209 | AA (5.1:1) | Errors, alerts |
| aftercare.violet | #9B78FF | 155, 120, 255 | AA (5.8:1) | Aftercare chips |
| gilt.edge (gold) | #F5F26D | 245, 242, 109 | AA (9.3:1) | Warnings only |
| saint.gold (amber) | #FFCF78 | 255, 207, 120 | AA (7.2:1) | Override states |
| ink.black (surface) | #020617 | 2, 6, 23 | — | Primary background |
| void.navy | #041628 | 4, 22, 40 | — | Panel background |
| text (primary) | #E2E8F0 | 226, 232, 240 | — | Body text |
| text.dim | #94A3B8 | 148, 163, 184 | — | Secondary text |

---

## 8. Failure Prevention Notes

- **Authority always labeled**: If a pane header lacks `authority:`, it's a bug.
- **SRC always visible**: If a row lacks `SRC:`, it's a bug.
- **Confirm modal always names target**: If a write confirm doesn't name the service, it's a bug.
- **No unified task record**: PM and Implementer never see a single canonical "task" — they see a composite view over split authorities.
- **No silent service mutations**: A handoff `[H] send` never transitions task-orchestrator state without explicit user action.
- **No mouse**: If the TUI accepts mouse input, it violates the spec.
- **Bridge always segregated**: Bridge output is always below a gold hazard line and requires `shift-Y` to acknowledge.

---

## 9. Claude Code Handoff Notes

### 9.1 Preferred Stack

- **Language**: Rust + ratatui (preferred) or Python + Textual
- **Protocol**: Direct cell-level rendering only — no sequential-print renderers.
- **Event loop**: max(2 fps, event-driven). Frame buffer, commit on render cycle.
- **No web**: Terminal-native fixed-grid. No HTML, DOM, JavaScript, CSS.

### 9.2 Runtime Contracts

**`Source` trait**:
```rust
trait Source {
    fn authority(&self) -> ServiceId;
    fn canonical(&self) -> bool;  // Bridge returns false
    fn read(&self, query) -> Future<Result<Vec<Row>>>;
    fn write(&self, action) -> Future<Result<WriteReceipt>>;
}
```

**Frame model**:
```
1. Clear buffer
2. Draw panes (parallel safe)
3. Commit frame to terminal
→ Repeat at max(2 fps, event-driven)
```

**Authority enforcement**: Every pane carries `authority: ServiceId`. Bridge adapter always returns `canonical() = false`.

### 9.3 Acceptance Criteria

1. ✓ Five top-level modes (PM, Implementer, Overview, Services, Events)
2. ✓ Supporting views for Tasks, Decisions, Memory, Search (reached via `g o` / `g d` / `g m` / `g s`)
3. ✓ Left rail shows task list; center shows details + handoff packets; inspector shows expanded view
4. ✓ Every pane header includes `authority: <service>`
5. ✓ Every row includes `SRC: <service>`
6. ✓ Confirm modals name target service (`WRITE -> <service> : <action>`)
7. ✓ Bridge adapter output segregated below gold hazard line
8. ✓ `[H] send` writes to ConPort and dope-memory only (no task-orchestrator transition)
9. ✓ Pin state owned by dope-memory with `pinned_at` field on chronicle receipt
10. ✓ 30-day packet archive with reaper owned by dopemux
11. ✓ Leantime writes limited to 7 metadata fields only
12. ✓ Workflow-significant writes blocked from Leantime (routed to task-orchestrator)
13. ✓ Role gating on `[a] approve` (task-orchestrator-only)
14. ✓ No mouse, no hover, no HTML/DOM
15. ✓ DOPEMUX_THEME tokens enforced (no raw hex colors)

### 9.4 Build Order (17 Steps)

1. **Grid skeleton**: Create 120×40 buffer, render fixed borders, initialize panes
2. **Mode strip**: Render mode buttons (1–5), global status tile
3. **Source abstraction**: Wire Source trait, mock backends for proof-of-concept (BLOCKED: U1 surface contract UNKNOWN)
4. **Task list pane**: Load and display task-orchestrator task list in left rail
5. **Task details center**: Display selected task metadata from leantime + conport
6. **Handoff packet pane**: Draft / active packet rendering in center bottom
7. **Inspector pane**: Expanded view of selected row, Bridge adapter subpane
8. **Authority labeling**: Add `authority:` headers and `SRC:` tags to all rows (BLOCKED: Source contract UNKNOWN; degraded to mock until U1 resolved)
9. **Role model wire**: Implement role resolver and gating for `[a] approve` and `shift-Y` (BLOCKED: U4 role model UNKNOWN; degraded until U4 resolved)
10. **Confirm modals**: Build confirm dialog with target service name in body
11. **Pin state**: Implement dope-memory integration for pin/unpin with `pinned_at` field (BLOCKED: U7 field schema UNKNOWN; degraded until U7 resolved)
12. **Packet lifecycle**: 30-day archive trigger and reaper (BLOCKED: U3 tail retention window UNKNOWN; degraded until U3 resolved)
13. **Event stream**: Real-time event pane with rate limiting and tail buffer (BLOCKED: U3 event rate limit UNKNOWN; degraded until U3 resolved)
14. **Supporting views**: Task / Decision / Memory / Search views (BLOCKED: U6 [EDGE] brand-voice pending; degraded until review)
15. **Keyboard input**: Command parsing and dispatch (all commands)
16. **Brand voice gate**: Audit all output strings against DOPEMUX_THEME and hedging vocabulary
17. **Resize handling**: Adapt grid to 100×32 and 80×24

### 9.5 Remaining UNKNOWNs

**See UNKNOWN Resolution Questionnaire (§11.5 → §11.7)**:
1. U1: Source adapter HTTP/RPC surface per backend
2. U2: dopetask health endpoint path
3. U3: Event stream rate limits and tail retention window
4. U4: Role model for non-`[a]` canonical writes
5. U5: Display priority when unread PKT and unread PKB coexist
6. U6: `[EDGE]` chip reuse on PKB recommendation arrival — pending brand-voice review
7. U7: Pin-state schema (field name on chronicle receipt, append-only guarantee)

---

## 10. Change Log

### v2.0a (2026-04-23) — Clarifications Pass 1

- **Frontmatter**: Bump version to v2.0a
- **§2.4**: New §2.4.1 and §2.4.2 for send semantics and packet lifecycle (30-day archive, pin exemption)
- **§3.4**: New Leantime write scope (enumerated 7 allowed fields, 4 forbidden mutations)
- **§3.5**: New PM-mode authority split table (metadata → leantime, workflow → task-orchestrator, decision/progress → conport, history → dope-memory)
- **§3.3**: Clarified write refusals (forbidden mutations listed explicitly)
- **§5.4**: Confirm modal bodies (named target services, with examples)
- **§6.6**: Action-suffix rules (explicit naming of target + action in every confirm)
- **§9.3**: New acceptance criteria 11–15 (Leantime scope, role gating, workflow blocking, Bridge segregation, source contract)
- **§9.4**: Updated build order (17 steps, blocks and degrades noted)
- **§9.5**: Reduced UNKNOWN list from 10 to 7 items (U1–U7); moved resolved items to §11.6
- **§11.6**: New resolved log (8 items with rationale)
- **§11.7**: New data contracts (Packet schema, PinState schema, AppState shape)

### v2.0 (2026-04-23) — Initial Specification

- Draft from `01_REVISION_BRIEF_PM_IMPLEMENTER.md` requirements
- Five-mode IA (PM, Implementer, Overview, Services, Events)
- Split authority model with per-field SRC tagging
- Handoff packet model (PKT-*, PKB-*) with send/archive semantics
- Authority prevention mechanisms (4) and refusal rules
- Terminal-native fixed-grid 120×40 (+ adaptive 100×32, 80×24)
- DOPEMUX_THEME palette and closed glyph set
- Build order (stale v1.0 carry-over cleanup, 17-step progression)

---

## 11. Migration Notes

### 11.1 Superseded v1.0 Artifacts

The following v1.0 elements are no longer authoritative and must be discarded:
- Seven-tab mode strip (`Tasks`, `Decisions`, `Memory`, `Search`, `Services`, `Events`, `Overview`)
- Unified task record (PMTask + ImplementerTask merged into single view)
- Unified PM record and Implementer record
- Mock port numbers treated as real
- Leantime-routed workflow verbs (status, queue, approvals)
- Automation-invoked `[H] send`
- `[AFTERCARE]` chipped packet receipts (use `[LOGGED]` instead)

### 11.2 v1.0 → v2.0a Stale Carryover Cleanup (Build Prerequisite)

Before step 1 of the build order, remove:
- All references to unified task state
- All 7-tab tab-strip code (replace with 5-tab strip)
- All mock port bindings (use live config / registry discovery)
- All leantime-routed workflow mutations
- All auto-invoked `[H]` send logic
- All `[AFTERCARE]` chip rendering for packets (update to `[LOGGED]`)

### 11.3 Interaction Model Pivot

v1.0 interaction was tab-centric (switch tab → see domain-specific view).
v2.0a interaction is mode-centric (stay in PM or Implementer, drill-down via `Enter` or navigate to supporting view via `g o` / `g d` / `g m` / `g s`).

**Impact**: All key bindings, menu structures, and command dispatch must be rewritten.

### 11.4 Data Contracts (New)

#### AppState Contract

```rust
struct AppState {
    workspace: String,
    instance: String,
    mode: Mode,              // PM | Implementer | Overview | Services | Events
    selection: RowId,
    filters: FilterSet,
    overlay: Option<Modal>,
    services: Vec<ServiceStatus>,
    queue: Vec<WorkflowItem>,
    events: VecDeque<Event>,
    inspector: InspectorPane,
    packets: PacketStore,    // {drafts, active, pinned, archived_ref}
    unread: UnreadCounter,   // {pkt_count, pkb_count}
}
```

#### Packet Contract

```rust
struct Packet {
    id: String,              // PKT-* or PKB-*
    authoring_src: "dopemux",
    state: PacketState,      // draft | sent | pinned | archived
    sent_at: Option<DateTime>,
    mirror_refs: MirrorRefs, // {conport_progress_id, dope_memory_chronicle_id}
    fields: Map<String, Value>,
    field_src: Map<String, ServiceId>,  // SRC tagging per field
    pinned: bool,
}
```

### 11.5 Remaining UNKNOWNs (See §9.5 for Details)

Seven items remain open and will block specific implementation steps:
1. U1: Source adapter HTTP/RPC surface per backend
2. U2: dopetask health endpoint path
3. U3: Event stream rate limits and tail retention window
4. U4: Role model for non-`[a]` canonical writes
5. U5: Display priority when unread PKT and unread PKB coexist
6. U6: `[EDGE]` chip reuse on PKB recommendation — pending brand-voice review
7. U7: Pin-state schema (field name on chronicle receipt)

### 11.6 Resolved Items (From §9.5 v2.0)

The following items from the baseline UNKNOWN list have been resolved via locked clarifications:
1. ✓ Packet send creates mirror records only (clarification 2)
2. ✓ Chronicle receipts use `[LOGGED]` chip (clarification 3)
3. ✓ 30-day auto-archive with pin exemption (clarifications 4–5)
4. ✓ Supporting-view mocks are layout-authoritative only (clarification 6)
5. ✓ Old 7-tab strip is non-authoritative v1.0 carry-over (clarification 7)
6. ✓ All mock ports are illustrative, not real (clarification 8)
7. ✓ Leantime write scope enumerated (clarification 10)
8. ✓ Forbidden Leantime mutations listed (clarification 11)

### 11.7 Data Contracts (Implementation Anchors)

#### Pin State Schema

**Owner**: dope-memory (append-only in spirit)

**Field name on chronicle receipt**: `pinned_at: Option<DateTime>`
- null = not pinned
- non-null = pinned at that timestamp

**Unpin operation**: writes new receipt with `pinned_at: null` and back-reference to original; reaper reads latest receipt per packet id.

---

**NEXT**: Apply ADR-001 and ADR-002 to implementation planning; resolve U1–U7 before build step 3.
