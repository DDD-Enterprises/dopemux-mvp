---
id: tmux_ux_system_design
title: Tmux Ux System Design
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-21'
last_review: '2026-03-21'
next_review: '2026-06-19'
prelude: Tmux Ux System Design (reference) for dopemux documentation and developer
  workflows.
---
# Tmux UX System Design — Multi-Agent Control

> Grounded in the Dopemux SIA architecture, energy-adaptive layouts, and existing `theme.py` palette.

---

## 1. TMUX LAYOUT SYSTEM

### Window Map

| Window | Name | Purpose | Persistence |
|--------|------|---------|-------------|
| `0` | **command** | Supervisor chat + task issuance | Always open |
| `1` | **agents** | Live agent execution panes | Always open |
| `2` | **audit** | Proof bundles + audit verdicts | On demand |
| `3` | **monitor** | System health + ADHD metrics | Always open |
| `4` | **compare** | Side-by-side model evaluation | On demand |

### Pane Layouts Per Window

#### Window 0: `command` — The Cockpit

```
┌──────────────────────────────────┐
│                                  │
│     SUPERVISOR CHAT (80%)        │
│     Interactive REPL              │
│     dopemux> _                   │
│                                  │
├──────────────────────────────────┤
│  TASK QUEUE (20%)                │
│  TP-055 ⧗ EXECUTING  TP-056 ◌   │
└──────────────────────────────────┘
```

- **Pane 0** (`supervisor:chat`): Full-width interactive shell. This is where the developer lives.
- **Pane 1** (`supervisor:queue`): Compact task queue ticker — `watch` over `dopemux task list --compact`.

#### Window 1: `agents` — Live Execution

Energy-adaptive via [layouts.py](file:///Users/hue/code/dopemux-mvp/src/dopemux/tmux/layouts.py). Defaults to **medium** energy:

```
┌─────────────────┬─────────────────┐
│                 │                 │
│  IMPLEMENTER-0  │  IMPLEMENTER-1  │
│  (primary)      │  (secondary)    │
│  stdout/stderr  │  stdout/stderr  │
│                 │                 │
├─────────────────┴─────────────────┤
│  AGENT EVENT LOG (25%)            │
│  task.assigned → task.proof.emit  │
└───────────────────────────────────┘
```

- **Pane 0** (`agent:primary`): Primary implementer stream. Bordered `TMUX_SUCCESS`.
- **Pane 1** (`agent:secondary`): Secondary/parallel implementer. Bordered `TMUX_GOLD`.
- **Pane 2** (`agent:events`): `EventBus` subscriber tail — all `dopemux:sia:*` events, filtered.

> [!TIP]
> At **low energy**, collapse to single implementer + events. At **high energy**, expand to 2×2 tiled (3 implementers + events).

#### Window 2: `audit` — Proofs and Verdicts

```
┌─────────────────┬─────────────────┐
│                 │                 │
│  AUDIT VERDICT  │  PROOF BUNDLE   │
│  PASS/FAIL      │  BROWSER        │
│  criteria list  │  artifact tree  │
│                 │                 │
└─────────────────┴─────────────────┘
```

- **Pane 0** (`audit:verdict`): Latest `AUDIT_VERDICT.json` rendered via `rich` — color-coded PASS/FAIL per criterion.
- **Pane 1** (`audit:proof`): `tree proof/<TP-ID>/` + `jq` previews of selected artifacts.

#### Window 3: `monitor` — System Visibility

```
┌──────────────────────┬────────────┐
│                      │  SERVICES  │
│  ADHD DASHBOARD      │  HEALTH    │
│  (Textual app)       │  grid      │
│  Energy/Flow/Load    ├────────────┤
│                      │  RESOURCE  │
│                      │  USAGE     │
│                      │  cpu/mem   │
└──────────────────────┴────────────┘
```

- **Pane 0** (`monitor:adhd`): The existing Textual dashboard from [tmux-dashboard-design.md](file:///Users/hue/code/dopemux-mvp/docs/03-reference/systems/dashboard/tmux-dashboard-design.md).
- **Pane 1** (`monitor:services`): Service health grid (ConPort, Redis, LiteLLM, ADHD Engine).
- **Pane 2** (`monitor:resources`): `btop --utf-force` or a lightweight resource gauge.

#### Window 4: `compare` — Model Evaluation

See [§6. Comparison Mode](#6-comparison-mode).

### Naming Convention

All panes use the existing `theme.py` naming scheme: `<role>:<function>`.

| Prefix | Meaning |
|--------|---------|
| `supervisor:` | Control plane — user-facing |
| `agent:` | Data plane — agent execution |
| `audit:` | Verification plane |
| `monitor:` | Observability plane |

---

## 2. INTERACTION MODEL

### Supervisor Chat

The developer interacts **exclusively** through `Window 0, Pane 0` — the supervisor REPL.

```
dopemux> task submit task-packets/TP-PRMS-055.md --budget $2.00 --provider MID
  ✓ Parsed: TP-PRMS-055 "Fix dashboard latency"
  ✓ Budget: $2.00 ceiling
  ✓ Provider: MID → claude-sonnet-4-20250514
  ✓ Dispatched to implementer-0
  ⧗ Watching...

dopemux> status
  TP-PRMS-055  EXECUTING  step 3/5  $0.34 spent  implementer-0

dopemux> agents
  [0] implementer-0  BUSY   TP-PRMS-055  claude-sonnet-4-20250514  $0.34/$2.00
  [1] implementer-1  IDLE   —

dopemux> kill 0
  ✗ implementer-0 terminated. Partial proof bundle saved.
```

### Task Issuance Flow

```
1. dopemux task submit <packet.md>     → Supervisor intake
2. Supervisor decomposes               → Auto (user sees log)
3. Supervisor dispatches                → Agent pane lights up
4. User watches Window 1               → Live execution stream
5. Proof emitted                        → Window 2 auto-populated
6. Audit verdict arrives                → Notification in status bar
7. User reviews in Window 0            → dopemux task review <TP-ID>
```

### Result Review

Three progressive levels:

| Level | Command | What You See |
|-------|---------|-------------|
| **Glance** | Status bar | `✓ TP-055 VERIFIED $0.89` or `✗ TP-055 BLOCKED` |
| **Summary** | `dopemux task status TP-055` | Verdict, cost, retry count, duration |
| **Deep dive** | `Ctrl-b 2` (switch to audit window) | Full proof bundle + criterion-by-criterion verdict |

---

## 3. VISUAL HIERARCHY

### Priority Encoding

Attention is guided by **position**, **color**, and **motion** — in that order.

```
HIGHEST ATTENTION                              LOWEST ATTENTION
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Window 0 │  │ Status   │  │ Window 1 │  │ Window 3 │
│ Cmd input│  │ Bar      │  │ Agent    │  │ Monitor  │
│ TOP-LEFT │  │ BOTTOM   │  │ STREAM   │  │ DETAIL   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
  INTERACT      SCAN          WATCH         REFERENCE
```

### Color Rules (from `theme.py`)

| Signal | Color | Token | When |
|--------|-------|-------|------|
| **Action required** | `#ff8bd1` | `TMUX_ALERT` | Blocked tasks, failures, budget exceeded |
| **In progress** | `#7dfbf6` | `TMUX_ACCENT` | Active execution, focused pane |
| **Success** | `#94fadb` | `TMUX_SUCCESS` | Verified tasks, healthy services |
| **Warning** | `#f5f26d` | `TMUX_WARNING` | Approaching limits, retries |
| **Neutral** | `#e0def4` | `TMUX_FOREGROUND` | Informational, idle states |
| **Background** | `#020617` | `TMUX_BACKGROUND` | Pane backgrounds, chrome |

### Status Bar Layout

```
 ◆ Ø ◆  dopemux  host │ TP-055:EXEC TP-056:QUEUED │ 📱 idle  🤖 claude-sonnet  14:30  Sat Mar 21
```

Left: Brand + host. Center: Active task ticker (injected dynamically). Right: Mobile, model, time.

> [!IMPORTANT]
> The center segment is the **only dynamic element** in the status bar. Everything else is static. This prevents the "Christmas tree" effect that destroys terminal readability.

---

## 4. FAILURE VISIBILITY

### Error Surfacing — Three Channels

| Channel | Latency | Mechanism | Example |
|---------|---------|-----------|---------|
| **Status bar flash** | Instant | `TMUX_ALERT` background pulse on status bar center segment | `✗ TP-055 AUDIT FAIL` |
| **Bell** | Instant | `tmux set -g visual-bell on` — triggers terminal bell on FAIL/BLOCKED | OS notification if configured |
| **Supervisor log** | <1s | Event printed to `supervisor:chat` pane | `[FAIL] TP-055: 2/5 criteria failed. Run: dopemux task review TP-055` |

### Blocked Task Display

Blocked tasks are **permanently** visible until resolved:

```
# Status bar (persists until acknowledged)
 ◆ Ø ◆  dopemux │ ⚠ TP-055:BLOCKED (3 retries exhausted) │ 14:30

# Supervisor chat (on any command)
dopemux> status
  ⚠ BLOCKED TASKS:
    TP-055  "Fix dashboard latency"  BLOCKED  3/3 retries  $1.89 spent
    Reason: Auditor FAIL — missing test coverage for edge case
    Action: dopemux task retry TP-055 --provider POWER
            dopemux task escalate TP-055 --to human
```

### Failure Taxonomy in Pane Borders

| State | Border Color | Border Token |
|-------|-------------|--------------|
| Executing normally | `TMUX_ACCENT` (cyan) | Active |
| Warning (retry in progress) | `TMUX_WARNING` (yellow) | Degraded |
| Failed / Blocked | `TMUX_ALERT` (pink) | Critical |
| Idle | `TMUX_BORDER` (dim mint) | Inactive |

---

## 5. MULTI-AGENT CONTROL

### Agent Registry View

```
dopemux> agents
  ID  ROLE           STATUS  TASK       MODEL              COST     PANE
  0   implementer    BUSY    TP-055     claude-sonnet-4    $0.34    agents:0
  1   implementer    IDLE    —          —                  —        agents:1
  2   auditor        BUSY    TP-055     gemini-2.0-flash   $0.02    (headless)
```

### Switching

| Action | Keybinding | Effect |
|--------|-----------|--------|
| Focus agent pane | `Ctrl-b 1` then `Ctrl-b <arrow>` | Standard tmux pane navigation |
| Jump to agent by ID | `dopemux focus <agent-id>` | Selects window + pane automatically |
| Return to supervisor | `Ctrl-b 0` | Always goes back to command window |

### Monitoring

Each agent's pane shows:

```
┌─ agent:primary ── TP-055 step 3/5 ── claude-sonnet-4 ── $0.34/$2.00 ──┐
│                                                                         │
│  [stdout from agent execution]                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

The **pane title** (set via `select-pane -T`) carries live metadata: task ID, step progress, model, cost. Updated by the `EventBus` subscriber on each `task.execution.step` event.

### Lifecycle Commands

| Command | Effect |
|---------|--------|
| `dopemux agent kill <id>` | SIGTERM → partial proof bundle saved → status: BLOCKED |
| `dopemux agent restart <id>` | Kill + re-dispatch same assignment |
| `dopemux agent spawn` | Launch new implementer pane (up to max from energy level) |
| `dopemux agent pause <id>` | Suspend agent process (`SIGSTOP`), pane border → yellow |
| `dopemux agent resume <id>` | Resume (`SIGCONT`), border → cyan |

---

## 6. COMPARISON MODE

### Purpose

Evaluate the same task across multiple models side-by-side. Activated via:

```
dopemux compare TP-055 --models "claude-sonnet-4,gemini-2.5-pro,gpt-4o" --budget $3.00
```

### Layout (Window 4: `compare`)

```
┌─────────────┬─────────────┬─────────────┐
│  MODEL A    │  MODEL B    │  MODEL C    │
│  claude-s4  │  gemini-2.5 │  gpt-4o     │
│             │             │             │
│  [output]   │  [output]   │  [output]   │
│             │             │             │
├─────────────┴─────────────┴─────────────┤
│  COMPARISON SUMMARY                      │
│  Cost:  $0.42    $0.18       $0.31       │
│  Time:  34s      22s         28s         │
│  Audit: PASS     PASS        FAIL        │
│  Score: ★★★★☆   ★★★★★      ★★☆☆☆       │
└──────────────────────────────────────────┘
```

- **Top row**: Synchronized scroll — all three panes show the same logical section of output.
- **Bottom pane**: Auto-generated comparison table after all three complete.

### Synchronized Scrolling

```bash
# Bind synchronized scroll toggle for compare window
tmux set-window-option -t compare synchronize-panes on
```

Toggle with `dopemux compare sync-scroll toggle`. Off by default during execution (outputs arrive at different speeds), on after completion for review.

### Verdict Overlay

After all models finish, the comparison summary pane auto-renders:

```
dopemux> compare results TP-055
  ┌────────────┬──────────┬──────────┬──────────┐
  │ Metric     │ Sonnet 4 │ Gemini   │ GPT-4o   │
  ├────────────┼──────────┼──────────┼──────────┤
  │ Audit      │ ✓ PASS   │ ✓ PASS   │ ✗ FAIL   │
  │ Cost       │ $0.42    │ $0.18    │ $0.31    │
  │ Duration   │ 34s      │ 22s      │ 28s      │
  │ Steps      │ 5/5      │ 5/5      │ 3/5      │
  │ Retries    │ 0        │ 0        │ 2        │
  │ WSEMT      │ 0.78     │ 0.95     │ 0.32     │
  └────────────┴──────────┴──────────┴──────────┘
  Winner: gemini-2.5-pro (highest WSEMT score)
```

---

## 7. ANTI-PATTERNS

### What Makes Terminal Systems Unusable

| Anti-Pattern | Why It Kills Productivity | Dopemux Mitigation |
|---|---|---|
| **Pane explosion** | >6 panes = cognitive overload, can't find anything | Energy-adaptive layouts cap panes: low=2, med=3, high=4. Windows separate concerns. |
| **Christmas tree status bar** | Constantly flickering colors destroy peripheral vision | Single dynamic center segment. Static left/right. No animation. |
| **Log vomit** | Unfiltered agent output floods the terminal | Agent panes show filtered stdout, full logs in `monitor:logs` only on demand. |
| **Hidden state** | System doing things you can't see | Every state transition emits to EventBus → visible in `agent:events` pane. Pane titles carry live metadata. |
| **Modal traps** | Entering a mode you can't exit without arcane keybindings | `Ctrl-b 0` **always** returns to supervisor. No nested modes. No custom keybinding schemes beyond standard tmux. |
| **Phantom processes** | Agents running after you think they stopped | `dopemux agents` always shows ground truth. `SIGTERM` → proof bundle saved. No orphans possible due to tmux process group management. |
| **Notification fatigue** | Bell on every event | Bell only on `FAIL` and `BLOCKED`. Success is silent. |
| **Context amnesia** | Switching windows loses your place | Pane titles persist state. `dopemux status` works from any window. Status bar shows active tasks globally. |
| **Synchronous blocking** | CLI command blocks while agent runs for 5 minutes | Async dispatch. Supervisor returns immediately after dispatch. Events stream to separate panes. |
| **Infinite scroll** | Agent output that requires scrolling 10,000 lines | Proof bundles capture output as files. Agent panes use `tmux capture-pane` snapshots. `less` for history, not scroll. |
| **Undiscoverable commands** | Power user features nobody knows about | Footer hotkey hints in Textual dashboard. `dopemux help` in supervisor. Tmux key hints in status bar. |
| **Split-brain state** | Status bar says one thing, agent pane says another | Single source of truth: `EventBus`. All displays subscribe to same stream. |

### The Golden Rule

> **If the user has to switch windows more than once per task lifecycle, the layout is wrong.**

Ideal flow: Start in `command` (window 0) → glance at `agents` (window 1) during execution → back to `command` for review. The `audit` and `monitor` windows exist but are **reference material**, not part of the core loop.

---

## Appendix: Integration Points

| Existing Component | Role in This Design |
|---|---|
| [layouts.py](file:///Users/hue/code/dopemux-mvp/src/dopemux/tmux/layouts.py) | Energy-adaptive pane creation for `agents` window |
| [theme.py](file:///Users/hue/code/dopemux-mvp/src/dopemux/tmux/theme.py) | All color tokens, pane naming, status bar segments |
| [controller.py](file:///Users/hue/code/dopemux-mvp/src/dopemux/tmux/controller.py) | Pane/window lifecycle management |
| [tmux-dopemux-orchestrator.yaml](file:///Users/hue/code/dopemux-mvp/tmux-dopemux-orchestrator.yaml) | Declarative startup config (to be extended with this window map) |
| [SIA_ARCHITECTURE.md](file:///Users/hue/code/dopemux-mvp/llm-plans/SIA_ARCHITECTURE.md) | Agent roles, event types, task lifecycle FSM |
| [tmux-dashboard-design.md](file:///Users/hue/code/dopemux-mvp/docs/03-reference/systems/dashboard/tmux-dashboard-design.md) | Textual app for `monitor:adhd` pane, 3-tier display system |
