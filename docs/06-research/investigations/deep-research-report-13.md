---
id: deep-research-report 13
title: Deep Research Report 13
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-24'
prelude: Deep Research Report 13 (reference) for dopemux documentation and developer
  workflows.
---
# Designing a tmux-native UX for Multi-Agent AI Control

A tmux-based control system can be genuinely “daily-driver” quality for advanced developers because tmux already solves the hard terminal problems: persistent sessions, rapid context switching, and concurrent views (windows/panes). tmux windows can be split into panes, each acting as its own terminal, and tmux also offers built-in navigation modes like *choose-tree* plus overlays like *display-popup*. citeturn7view0turn8view0turn23view1

The real design challenge is not “how to show more stuff,” but how to keep multi-agent orchestration cognitively manageable: (a) show system status continuously, (b) progressively disclose detail, and (c) avoid forcing users to hold too many simultaneous threads in working memory. citeturn20view0turn20view1turn20view2

Multi-agent systems, by definition, coordinate multiple conversant agents, sometimes with human input and tools—so the UI must support parallelism *and* disciplined oversight (queueing, auditing, recoveries). citeturn20view3

## TMUX layout system

The “optimal” tmux UX is less about clever splits and more about **a stable mental model**: a small number of **role-based windows** that never change their purpose, plus **dynamic agent/run views** that come and go. tmux itself encourages this separation: sessions contain windows; windows contain panes; panes can be arranged via known layouts (e.g., *main-vertical*) with controllable main-pane sizes. citeturn10view1turn25view2turn25view0

### Baseline structure: one workspace session, role-based windows

Use **one tmux session per “workspace”** (repo/project/environment), not per agent. Agents should be *objects inside the workspace*, otherwise you end up with session sprawl and navigation entropy.

Within a workspace session, keep **five primary windows**:

**Window: Hub (supervisor + queue)**
- **Primary pane (main pane): Supervisor chat**
  This is where intent is negotiated, tasks are specified, approvals happen, and interrupts land.
- **Secondary pane: Agent roster + task queue (TUI/list)**
  A sortable/filterable list: agent name, current task, state, last event time.
- **Footer pane: Event feed (“interrupts bus”)**
  Append-only, low-noise stream of: failures, blocks, approvals needed, retries.

Why this works in tmux: main-pane layouts exist specifically to keep a “primary work area” and relegate secondary panes to a sidebar without constant manual resizing. citeturn25view2turn25view0

**Window: Run (live execution focus)**
- **Primary pane: Focused agent execution** (one agent at a time, full logs, interactive tool output)
- **Secondary panes: Up to 3–5 “hot” agents** (only those currently running, blocked, or failing)
- **Footer pane: Shared “commands + results” digest** (structured summaries, not raw spam)

tmux supports tiling but you should put explicit brakes on pane proliferation—tmux even includes `tiled-layout-max-columns` to cap column count in tiled layouts, which is a strong hint from tmux itself that unlimited tiling becomes unreadable. citeturn7view1

**Window: Audit (proofs + artifacts)**
- **Primary pane: Run ledger (structured)**
  Timeline of: prompts, tool calls, external I/O, decisions, checkpoints.
- **Secondary pane: Artifact inspector**
  Diffs, patches, generated files, references to evidence.
- **Footer pane: Reproduction recipe**
  Minimal steps to reproduce + environment fingerprint.

tmux supports piping pane output to a command via `pipe-pane`, which is ideal for capturing agent output into your audit store (files, JSONL, etc.) without building complex terminal logging yourself. citeturn8view2

**Window: Ops (system monitoring)**
- **Primary pane: “Golden signals” dashboard**
  Latency, traffic, errors, saturation, plus agent queue depth (this maps well to SRE monitoring practice). citeturn9view1turn9view1
- **Secondary pane: Logs/traces drilldown**
  Quick pivot from “symptom” to “why”, keeping signal high and noise low. citeturn9view1turn9view1

For instrumentation, base your mental model on entity["organization","OpenTelemetry","observability project"]: traces/metrics/logs as first-class signals, with backends and visualizers intentionally decoupled. citeturn15view0turn15view1

**Window: Compare (side-by-side)**
- **Columns: Model/agent outputs** (2–3 columns max in a standard terminal width)
- **Footer: Diff + scoring + decision log**

This window exists because comparison is a distinct cognitive task: you’re evaluating alternatives, not executing. Tools like promptfoo explicitly show side-by-side and matrix views to review outputs across prompts/models. citeturn18view0turn18view2

### Popups: “ephemeral detail without navigation thrash”

Use tmux *display-popup* for:
- quick help / keybinding overlay
- “pick an agent/run” selector
- inspect last error details
- quick command palette

tmux defines popups as rectangular overlays drawn over panes (and notes panes aren’t updated while the popup is present), which is perfect for “temporary focus” actions. citeturn8view0

### Pane titles and borders: make every pane self-identifying

Your panes should never be anonymous. Use pane border status lines and formats so every pane shows:
- agent name / id
- state (RUN / BLK / ERR / DONE)
- last event age
- optional current task slug

tmux supports `pane-border-status` (top/bottom) and `pane-border-format`, plus active pane indicators (colour/arrows) to reduce “where am I typing?” errors. citeturn22view0turn25view0

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["tmux pane border status pane titles screenshot","k9s terminal UI screenshot keyboard help overlay","lazygit terminal UI screenshot panels","htop terminal screenshot cpu memory gauges"],"num_per_query":1}

## Interaction model

The interaction model should treat the system as **a supervisor-led control plane** with two equally important interfaces:
- **conversational** (for intent, triage, ambiguity)
- **commandable** (for automation, repeatability, auditing)

This aligns with modern CLI design guidance: human-first ergonomics, but with robust automation affordances (exit codes, stdout/stderr, machine-readable output). citeturn12view2turn15view4turn13view0turn16view0

### Supervisor interaction: chat plus explicit control verbs

In practice, “supervisor chat” works best as:

1) **Free-form intent** (“what we want”)
2) **Structured task spec** (“what we’ll do, how we’ll know it worked”)
3) **Execution + interrupt handling** (“what’s happening now”)
4) **Review + accept/reject** (“what changed, what evidence exists”)

Terminal AI tools show that chat + command verbs coexist well. For example, aider exposes many in-chat slash commands (`/diff`, `/test`, `/run`, mode switches) so a user can move from discussion to deterministic action without leaving the terminal loop. citeturn17view0

**Recommendation:** adopt a small set of high-leverage supervisor commands (typed in chat or via a command prompt):
- `task new …` (define task + success criteria)
- `task split …` (decompose)
- `task assign …` (route to agent)
- `task approve` / `task reject`
- `agent focus …`
- `agent pause|resume|kill|restart …`
- `compare run …` (open compare view)
- `audit export …` (produce proof bundle)

### Task issuance: always produce a durable, replayable task object

To keep audits and proofs real (not vibes), every user task should be compiled into a **task object** with:
- inputs (repo, branch/commit, files, external URLs)
- constraints (allowed tools, sandbox, network)
- success checks (tests, file existence, command outputs)
- risk level (requires approval steps)
- routing policy (which agent types can do it)

Why: evaluation practice for agents increasingly treats “prompt → captured run (trace + artifacts) → checks → score” as the unit of reliability, precisely because AI systems are nondeterministic. citeturn16view4turn16view3

### Reviewing results: default to summary, keep raw evidence one keystroke away

A cognitively manageable flow is:
- Supervisor posts **a short structured summary**: what changed, what evidence exists, what remains uncertain.
- User can press a single key to open:
  - diff/artifacts (Audit window)
  - full logs (focused pane)
  - comparison (Compare window)

This is “progressive disclosure” applied to terminal ops: show only the essential options first, reveal everything else on demand. citeturn20view1turn20view0

For discovery, imitate proven terminal UIs:
- k9s exposes `?` for help and mnemonic keys for actions, and uses a command mode (`:`) + filters (`/`) to drill down. citeturn21view0turn21view1
- lazygit provides a keybindings menu and a command log, reinforcing learnability for power users. citeturn21view2

## Visual hierarchy

Terminal UX has fewer “channels” than GUIs (mostly text, colour, borders, and layout). Your hierarchy should therefore rely on three mechanisms:
- **spatial invariants** (this region always means X)
- **textual labels** (pane titles, window names, status indicators)
- **alert-level styling** (minimal, consistent)

This supports usability heuristics like visibility of system status and reduces reliance on recall (users shouldn’t have to remember where things are or what they mean). citeturn20view0turn12view0

### Priority model: focus, periphery, background

A practical hierarchy that scales:

**Focus (one thing):**
- The active pane is always either:
  - Supervisor chat input, or
  - The currently focused agent execution output (Run window), or
  - The comparison decision workspace (Compare window)

Use tmux’s active-pane border options and indicators to make the focus unambiguous. citeturn22view0

**Periphery (few things):**
- Task queue + agent roster (just statuses, no walls of logs)
- Event feed (only high-signal events)

**Background (many things, summarized):**
- The rest of the agent fleet is summarized in roster counts and status flags, not rendered as dozens of panes.

This is a cognitive-load decision: working memory capacity is limited (often estimated around 3–5 “chunks” under many conditions), so the interface should not demand tracking 10 simultaneous moving targets. citeturn20view2

### Use tmux status line as your global “radar”

tmux status lines are explicitly designed as a taskbar-like baseline: configurable left/right sections plus a central window list. citeturn6search6turn7view1

Make the status line carry:
- `workspace` (session name)
- agent counts by state (RUN/BLK/ERR)
- queue depth
- last alert time
- current focus (agent id / task id)

You can also exploit tmux’s built-in window flags and alert styling:
- `#` for activity, `!` for bell, `~` for silence
- different status styles for alerted windows
This makes attention routing *automatic*: the user’s eyes are drawn to the right window without polling. citeturn7view1turn5search1

## Failure visibility

A multi-agent control plane fails in more ways than a normal CLI: agents can error, hang, wait for input, wedge on I/O, or produce low-quality outputs that “look fine” but are wrong. Failure visibility has to cover both **run-time faults** and **quality faults**.

### Runtime faults: surface immediately, persist until resolved

Use tmux primitives to make failures sticky:

- **Keep failed panes visible:** set panes/windows to persist on failure using `remain-on-exit` with the `failed` mode, then allow restart with `respawn-pane`. citeturn10view0turn10view3
- **Hard-highlight failing windows:** rely on the status-bar window flags and alert styles so the failure is visible even when you’re in a different window. citeturn7view1turn5search1
- **Capture logs automatically:** pipe each agent’s stdout/stderr to your audit store with `pipe-pane`, ideally as structured logs (JSONL) for later slicing. citeturn8view2turn12view2

### Blocked tasks: treat “needs input” as a first-class state

Blocked workflows are common in orchestration: credentials, ambiguous requirements, flaky tests, tool permission constraints. Your UI should make “blocked” impossible to miss:

- event feed emits a **single concise interrupt**: “Agent X blocked: needs Y”
- supervisor chat receives an actionable prompt (options + default)
- agent roster shows `BLK` with duration (e.g., `BLK 12m`)

This is directly aligned with “visibility of system status”: no consequential action should be taken (or stalled) without informing the user. citeturn20view0turn9view1

### Error taxonomy: stable codes + human resolution steps

Borrow a proven operational pattern: **error codes that classify failures** and are searchable in logs. entity["company","Heroku","paas company"] uses structured error codes (e.g., classes like runtime/logging) specifically to make log debugging faster. citeturn15view5

For an AI control system, an error code scheme might look like:
- `AIO-EXEC-*` (tool execution failures)
- `AIO-AUD-*` (audit/provenance capture failures)
- `AIO-MDL-*` (model response failures/timeouts)
- `AIO-SBX-*` (sandbox/permission violations)
- `AIO-EVAL-*` (evaluation/check failures)

Each emitted error should include:
- code + short title
- what failed (agent/task/run ids)
- immediate mitigation
- pointer to audit artifacts

Good CLI guidance consistently recommends informative errors and correct stdout/stderr separation for scriptability. citeturn12view2turn13view0turn15view4

### Alert noise: less, but better

A tempting failure mode is “make everything red.” entity["company","Google","search and cloud company"]’s SRE guidance explicitly warns that paging/alerts are expensive, and too much noise causes humans to skim or ignore real alerts; effective alerting must keep signal high and noise low. citeturn9view1turn9view1

So: only escalate to “interrupt” when something is urgent, actionable, and user-impacting (or will imminently be). Everything else stays in the event feed/roster until the user has attention bandwidth. citeturn9view1

## Multi-agent control

Multi-agent control is where tmux can feel “native” if you lean into its strengths: fast switching, tree navigation, and lifecycle actions on panes/windows.

### Switching: tree navigation as the primary affordance

Use tmux *choose-tree* as the canonical “overview + jump” UI:
- it displays sessions/windows/panes in a tree
- it supports search, previews, and killing items (`x`)
- it can run commands on tagged items

tmux documents *choose-tree* explicitly as an interactive tree mode to choose (and manipulate) sessions/windows/panes. citeturn23view1

In your system, map this to agents by ensuring:
- each agent has a dedicated pane (even if hidden most of the time)
- pane titles include agent id + state
- choose-tree becomes “agent switcher” for free

### Monitoring: combine “roster summary” + “hot panes”

Do not attempt to render all agents live. Instead:
- agent roster pane shows *all* agents (compact)
- Run window shows only “hot” agents (running/blocked/failing)
- Ops window shows fleet health metrics (rates, latencies, errors)

This separation mirrors monitoring best practice: dashboards answer basic questions; deeper inspection tools handle detailed debugging, and you avoid situations where someone must stare at a screen to watch for problems. citeturn9view1

### Killing and restarting agents: make it safe and reversible

tmux provides direct lifecycle actions:
- `kill-pane` / `kill-window` to terminate execution view units citeturn10view2
- `respawn-pane` / `respawn-window` to restart an inactive (or forcibly killed) unit, designed for workflows where commands exit and panes persist via `remain-on-exit` citeturn10view0turn10view1

Your UX should wrap these in supervisor-level semantics:
- “Kill” requires confirmation if the agent has uncommitted artifacts
- “Restart” defaults to same task with a new run id (preserve history)

### Broadcasting actions: rare, explicit, and dangerous

tmux supports `synchronize-panes` to duplicate input to all panes in a window. citeturn10view3
This is powerful but easy to misuse (you can accidentally send destructive commands to many agents). In an AI control system, keep broadcast behind:
- an explicit “arm” step (`BROADCAST ARMED`)
- a strict scope (only selected agent group)
- an automatic timeout that disarms

## Comparison mode

Comparison is not a luxury feature for AI systems; it’s how you prevent “model drift” and confirmation bias from quietly shipping regressions.

There are two distinct comparison modes worth supporting:

### Interactive side-by-side for a single prompt or task

This is the “I need to choose” workflow:
- show 2–3 model outputs in columns
- show a bottom pane with:
  - diff highlights (semantic or literal)
  - rubric checklist (must-pass constraints)
  - “decision log” (why you chose output B)

For terminal-native precedent:
- promptfoo explicitly produces side-by-side/matrix views to evaluate outputs across prompts/models, and supports exporting results (HTML/JSON/CSV) for later review. citeturn18view0turn18view2
- aider has an `/architect` mode that uses two different models (architect/editor) and provides in-chat commands like `/diff`, reflecting a pragmatic split between “plan/decide” and “execute/change.” citeturn17view0

### Systematic eval comparison across many prompts

This is the “I need to trust this daily” workflow:
- run a small suite of eval prompts whenever:
  - the model changes
  - the prompt changes
  - the toolchain changes
- store run traces + artifacts
- compute scores over time

entity["company","OpenAI","ai research and api company"]’s eval guidance describes evals as structured tests that help ensure reliability despite nondeterminism, and their agent-skill evaluation framing explicitly ties evals to captured runs (trace + artifacts) plus checks and scores. citeturn16view3turn16view4

**tmux UX implication:** your Compare window should support both:
- quick column comparison (human choice)
- “matrix view” embedding (batch eval triage), potentially opening a pager/export for deep review

### Machine-readable outputs are part of comparison

Comparison often becomes data work (filter, score, diff, regressions). Follow existing CLI conventions:
- human-readable default
- optional JSON output
- post-processing via jq/templates

entity["company","GitHub","code hosting company"]’s gh docs describe this pattern directly: plain text by default, `--json` for structured output, then `--jq` / `--template` for formatting. citeturn16view0

## Anti-patterns

Terminal systems become unusable in predictable ways. The failures below are especially lethal for multi-agent control because they compound across agents.

### Pane explosion and “log wallpaper”

- **Symptom:** 12+ panes of streaming output; nothing is legible; everything feels urgent.
- **Why it fails:** you exceed human attention/working-memory limits and turn monitoring into staring. citeturn20view2turn9view1
- **Fix:** cap live panes; route everything else to roster summary + event feed; make deep logs opt-in.

### No stable structure, everything is “wherever it fits”

- **Symptom:** windows/panes change meaning between sessions; users must re-learn layout each time.
- **Why it fails:** violates consistency/recognition; increases cognitive load. citeturn20view0turn12view0
- **Fix:** role-based windows with immutable purpose; dynamic content lives inside those roles, not as new ad-hoc windows.

### Hidden modes, undiscoverable commands

- **Symptom:** functionality exists but only via tribal-knowledge key chords; no help overlay.
- **Why it fails:** violates help/documentation and ease of discovery. citeturn20view0turn12view2
- **Fix:** `?` help overlay (k9s pattern), keybindings menu, and a command palette popup. citeturn21view0turn8view0turn21view2

### Mandatory prompts that break automation

- **Symptom:** tasks can’t be scripted; CI and repeatability are painful.
- **Why it fails:** advanced dev workflows require non-interactive modes.
- **Fix:** prompts are allowed but never required; always provide flags/inputs to bypass them. citeturn13view0turn12view2

### Unstructured errors and missing exit semantics

- **Symptom:** errors are walls of text; no error codes; unclear what to do; scripts can’t reliably detect failure.
- **Fix:** stable error codes + resolution steps; correct exit codes; stdout vs stderr separation. citeturn15view5turn12view2turn15view4

### “Trust me bro” audits

- **Symptom:** the system claims something happened, but you can’t prove what prompts/tools/inputs produced it.
- **Fix:** treat provenance as a first-class artifact. Use:
  - entity["organization","W3C","web standards body"] PROV-style modelling concepts (entities/activities/agents) for provenance structure citeturn15view3
  - SLSA-style provenance goals (verify built as expected; enable rebuilds) citeturn15view2
  - content-addressable storage concepts (Git objects) to hash-identify artifacts citeturn19view2
  - transparency log thinking (append-only, auditable logs) as demonstrated by Sigstore/Rekor. citeturn19view0

### Alert fatigue by design

- **Symptom:** everything is an interrupt; users start ignoring alerts.
- **Why it fails:** human interruption cost is real; noisy systems prolong incidents. citeturn9view1
- **Fix:** tiered alerting: “interrupt only when urgent/actionable,” everything else stays visible but non-paging. citeturn9view1turn20view0
