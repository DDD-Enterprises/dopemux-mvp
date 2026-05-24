---
id: mobile-tmux-cockpit-ux-spec
title: Mobile Tmux Cockpit UX Spec
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Docs-only mobile-first tmux Cockpit UX addendum for Dopemux authority-safe terminal operation.
---

# Mobile Tmux Cockpit UX Spec

Packet: `TP-DMX-MOBILE-TUI-SPEC-001`

Status: docs/spec addendum only. No runtime, source, config, dependency, or
tmux behavior is changed by this document.

## 1. Purpose And Non-Goals

Purpose: define a mobile-first tmux Cockpit UX architecture for Blink/SSH/Mosh
clients while preserving the repo's split authority model and proof discipline.

Non-goals:

- Do not implement runtime behavior.
- Do not add or change Python code.
- Do not mutate `.tmux.conf` or `config/mobile/tmux.mobile.conf`.
- Do not promote Cockpit, dopecon-bridge, dope-context retrieval, generated
  reports, adapters, mirrors, or UI summaries into canonical truth.
- Do not replace the existing TUI design system. This is a mobile addendum and
  future prototype contract.

## 2. Authority Boundary Model

Repo evidence used:

- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/systems/dopemux/system-dopemux.md`
- `docs/03-reference/systems/dopetask/system-dopetask.md`
- `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md`
- `docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md`
- `docs/03-reference/systems/dope-context/system-dopecontext.md`

Authority boundaries for this UX:

| Surface | Authority boundary |
| --- | --- |
| dopemux | Operator control, CLI, startup, routing, MCP/service coordination. Not PM truth, memory truth, retrieval truth, or execution truth after handoff. |
| dopetask | External execution runtime reached through `scripts/dopetask`. Not PM, memory, retrieval, or Cockpit authority. |
| task-orchestrator | Workflow transitions and workflow views. Runtime packaging and some storage boundaries remain drifted. |
| Leantime | Passive PM metadata and project/ticket snapshots. |
| ConPort | Structured decisions, progress, context, and custom data. |
| dope-memory | Chronicle and evidence-preserving memory/receipt history. |
| dope-context | Code/docs retrieval and indexing only. Search results are derived views. |
| dopecon-bridge | Proxy, routing, compatibility, auth, and event transport only. It is not task, workflow, decision, progress, PM, chronicle, or retrieval truth. |
| ADHD Engine | Operator support and cognitive-state cues only. It does not gate PM or prove execution success. |
| Repo Truth Extractor | Extraction/audit only. Outputs are evidence artifacts, not runtime truth. |

Rule: every data row or action surface names its canonical writer. If the writer
is unresolved, render `UNKNOWN` and block mutation.

## 3. Mobile-First Constraints

- The mobile client is a replaceable viewport. Remote state and proof stay on
  the host.
- tmux is the reconnect/resume chassis, not business logic.
- SSH is the common transport. Mosh is optional for roaming links and cannot be
  assumed for tunnels, bastions, scrollback, or all terminal features.
- Touch and mouse are optional conveniences. Keyboard navigation is the primary
  accessibility and reliability contract.
- Clipboard behavior is convenience only. It is not proof transport.
- Permanent multi-pane density is unsafe on phone-sized terminals.
- Full-screen overlays are safer than cramped popups on mobile.

## 4. Viewport Rules

| Viewport | Contract |
| --- | --- |
| Under 70 columns | Proposed mobile-first fallback: single-column, one active region, one-line status, full-screen drill-down overlays. CONFLICTING with current runtime/design-system blocker below `80x24`; not implemented by this packet. |
| `80x24` | Current minimum supported runtime viewport. One primary region plus minimal chrome. Bridge/retrieval/proxy details collapse into inspector/detail. |
| `100x30` or `100x32` | One dominant region plus one secondary region. Prefer stacked or strongly asymmetric split. |
| `120x40+` | Restrained desktop tmux layout with optional third region for provenance, proof, or segregated bridge detail. |

Observed runtime conflict: `src/dopemux/ui/cockpit/render.py` and the Cockpit
design-system acceptance currently require a blocker below `80x24`. Future
prototype work must explicitly decide whether and how to implement the
under-70-column fallback without silently weakening existing tests.

## 5. Global Navigation Model

Primary mobile homes:

- Home / Cockpit
- Task Packet Queue
- Execution Monitor
- PM Plane View
- Memory / Chronicle View
- Retrieval / Search View

Secondary routed views:

- System Health
- Proof / Evidence Viewer
- Settings / Terminal Diagnostics
- Unknown / Drift Queue
- Blocked Reason

Global overlays:

- Command Palette
- Safe Action Gate
- Help

Rules:

- On mobile, top-level navigation must fit without horizontal scrolling.
- Numeric shortcuts are optional accelerators; all flows must be reachable by
  arrows, Tab, Enter, Back/Esc equivalent, and Command Palette.
- Global overlays take over the full active tmux pane or app surface.

## 6. Screen Inventory

### Home / Cockpit

| Field | Contract |
| --- | --- |
| Purpose | Operator summary and safe launch point. |
| Primary data sources | dopemux status/health/doctor outputs, service summaries, packet summaries, proof pointers. |
| Authority boundary | dopemux owns chrome/control only; tile data names upstream authority. |
| Mobile layout | Single-column stack: Now, Risk, Next, Source. |
| Desktop tmux layout | Summary, queue/execution snapshot, authority/drift strip. |
| Keybindings | `1`, `h`, `q`, `x`, `:`, `?`, Enter, Back/Esc equivalent. |
| Empty state | No active work; show Queue, Palette, and last proof path if available. |
| Error state | Failed tile renders `UNKNOWN` with source name. |
| Forbidden actions | Direct mutation, fake unified PM row, bridge or retrieval result shown as canonical. |

### System Health

| Field | Contract |
| --- | --- |
| Purpose | Service status, logs, operator diagnostics, and authority warnings. |
| Primary data sources | dopemux health/status, service registry, runtime authority docs, logs. |
| Authority boundary | dopemux hosts the view; each service row keeps its own authority. |
| Mobile layout | Service list plus selected-service detail and diagnostics footer. |
| Desktop tmux layout | Service list, health/log body, authority manifest/resources. |
| Keybindings | `h`, `r`, `l`, `s`, `d`, Enter, Back/Esc equivalent. |
| Empty state | No services configured for this workspace. |
| Error state | Unreachable health source is `UNKNOWN`, not healthy. |
| Forbidden actions | Inline start/stop without gate, hiding conflicts, treating reachability as correctness. |

### Task Packet Queue

| Field | Contract |
| --- | --- |
| Purpose | Workflow queue and packet readiness view. |
| Primary data sources | task-orchestrator workflow views, task packet metadata, packet index. |
| Authority boundary | task-orchestrator owns workflow transitions; packet files are artifacts; execution remains downstream. |
| Mobile layout | Packet list with sticky detail footer for selected packet. |
| Desktop tmux layout | Queue, packet detail, linked proof/provenance. |
| Keybindings | `2`, `q`, arrows, `j/k`, Enter, `p`, `x`, Back/Esc equivalent. |
| Empty state | No queued or active packets. |
| Error state | Queue fetch failure names source and renders `UNKNOWN`, not empty. |
| Forbidden actions | Reorder/status/promote without canonical writer and Safe Action Gate. |

### Execution Monitor

| Field | Contract |
| --- | --- |
| Purpose | Bounded execution view for active or recent packet runs. |
| Primary data sources | dopetask handoff state, runner identity, validation logs, proof path. |
| Authority boundary | dopetask owns execution after handoff; stdout is not proof. |
| Mobile layout | Metadata header, log body, bottom action rail. |
| Desktop tmux layout | Log main, event/proof inspector, queue strip. |
| Keybindings | `3`, `x`, `c`, `p`, `o`, tmux `prefix z`, Back/Esc equivalent. |
| Empty state | No active run; show last proof path if known. |
| Error state | Runner unreachable, proof missing, and stale validation are distinct states. |
| Forbidden actions | Hidden rerun, implicit cancel, treating started/confirmed as completed. |

### Proof / Evidence Viewer

| Field | Contract |
| --- | --- |
| Purpose | Inspect proof bundles, receipts, paths, hashes, diffs, logs, and validation summaries. |
| Primary data sources | File-backed proof bundles, receipts, validation logs, artifact manifests. |
| Authority boundary | Viewer owns nothing; every artifact declares canonical writer and provenance. |
| Mobile layout | Metadata header, artifact selector, artifact body. |
| Desktop tmux layout | Artifact list, preview, provenance/receipts. |
| Keybindings | `e`, `p`, arrows, `j/k`, Enter, `o`, `y`, Back/Esc equivalent. |
| Empty state | Proof pending; show expected proof requirement. |
| Error state | Missing artifact, stale proof, parse error, and receipt mismatch are separate. |
| Forbidden actions | Editing proof, collapsing absence into success, hiding request IDs, accepting confirmation as proof. |

### PM Plane View

| Field | Contract |
| --- | --- |
| Purpose | Workflow triage and PM readiness without unified PM truth. |
| Primary data sources | Leantime metadata, task-orchestrator workflow, ConPort decisions/progress/context, dope-memory receipts. |
| Authority boundary | Split by slice; dopemux and Cockpit are not PM systems of record. |
| Mobile layout | Work-item list, full-screen detail with Leantime, Workflow, ConPort, Receipts sections. |
| Desktop tmux layout | List, selected item, decisions/receipts pane. |
| Keybindings | `4`, `p`, `w`, `d`, `m`, `r`, Enter, Back/Esc equivalent. |
| Empty state | No PM items matching scope. |
| Error state | Missing slice remains visible as `UNKNOWN`; no silent backfill from another system. |
| Forbidden actions | Fake single PM record, inline admin mutation, hiding which owner is written. |

### Memory / Chronicle View

| Field | Contract |
| --- | --- |
| Purpose | Chronicle and event/receipt inspection. |
| Primary data sources | dope-memory chronicle, receipt artifacts, upstream event producers. |
| Authority boundary | dope-memory is receipt/history authority, not current PM truth. |
| Mobile layout | Timeline list plus selected receipt detail. |
| Desktop tmux layout | Timeline, selected event body, linked source/proof. |
| Keybindings | `5`, `m`, `f`, `p`, `o`, Enter, Back/Esc equivalent. |
| Empty state | No chronicle entries in current filter. |
| Error state | Ledger unavailable, stale mirror, or parse failure named separately. |
| Forbidden actions | Treating receipts as current state, mutating PM from chronicle, hiding mirror status. |

### Retrieval / Search View

| Field | Contract |
| --- | --- |
| Purpose | Search code/docs and route results back to source authorities. |
| Primary data sources | dope-context code/docs retrieval, optional ConPort search results when explicitly labeled. |
| Authority boundary | dope-context owns retrieval/index behavior only; hits are derived leads. |
| Mobile layout | Query line, result list, selected result preview. |
| Desktop tmux layout | Query/results, preview, provenance/detail. |
| Keybindings | `6`, `/`, `s`, `f`, Enter, `o`, Back/Esc equivalent. |
| Empty state | No results; show active filters. |
| Error state | Index unavailable, stale index, and upstream fetch failure named separately. |
| Forbidden actions | Treating retrieval output as truth, hiding source path, writing through search result. |

### Command Palette

| Field | Contract |
| --- | --- |
| Purpose | Global broker for discover, inspect, preview, and route. |
| Primary data sources | Command catalog, safe-action catalog, authority map, current route. |
| Authority boundary | Palette is broker only; it never executes or confirms. |
| Mobile layout | Full-screen input, result list, preview/route footer. |
| Desktop tmux layout | Center overlay with preview; still not a side drawer on narrow panes. |
| Keybindings | `:`, `ctrl+k` where available, arrows, Enter, Back/Esc equivalent. |
| Empty state | No commands matching filter. |
| Error state | Unknown command, unresolved params, or unknown writer routes to Unknown/Drift. |
| Forbidden actions | Execute, auto-confirm, silently reroute, hide authority or proof requirement. |

### Safe Action Gate

| Field | Contract |
| --- | --- |
| Purpose | Refuse, confirm intent, execute supervised actions only when authorized, and demand proof. |
| Primary data sources | Action request, canonical writer, tier policy, proof requirement, rollback/abort plan. |
| Authority boundary | Gate is control/checkpoint only; canonical writer owns mutation. |
| Mobile layout | Full-screen review: action, writer, tier, proof, risks, confirm/refuse. |
| Desktop tmux layout | Full-screen or dominant overlay; no cramped modal for T4/T5/TU. |
| Keybindings | `g`, Enter to inspect/confirm when allowed, typed confirmation for high tiers, Back/Esc abort. |
| Empty state | No pending action. |
| Error state | Missing writer, missing proof path, stale request, or unknown side effect refuses closed. |
| Forbidden actions | Confirmation-only success, hidden side effects, bridge-owned canonical write, destructive action without typed confirmation and proof path. |

### Settings / Terminal Diagnostics

| Field | Contract |
| --- | --- |
| Purpose | Inspect terminal capabilities, tmux state, profile, and proposed settings. |
| Primary data sources | tmux environment, terminal size, feature probes, config paths, dopemux settings. |
| Authority boundary | dopemux owns settings chrome; tmux config remains external until a separate mutation packet authorizes changes. |
| Mobile layout | Diagnostics list plus selected detail/proposed command. |
| Desktop tmux layout | Diagnostics, feature matrix, proposed config preview. |
| Keybindings | `d`, `t`, `r`, `c`, Enter, Back/Esc equivalent. |
| Empty state | No diagnostics run yet. |
| Error state | Probe unavailable or capability UNKNOWN; do not assume support. |
| Forbidden actions | Mutating tmux config, enabling terminal features without probe, treating clipboard/mouse/glyph support as guaranteed. |

## 7. Command Palette Model

The palette accepts free text and structured filters:

- `auth:`
- `writer:`
- `class:`
- `place:`
- `proof:`
- `status:`
- `coverage:`
- `src:`
- `tp:`
- `svc:`

Each result shows:

- command or route
- authority domain
- canonical writer or `UNKNOWN`
- safety tier
- proof requirement
- expected destination: inspect, copy command, Safe Action Gate, blocked reason,
  Unknown/Drift, or settings/diagnostics

The palette cannot execute actions directly.

## 8. Breadcrumb Model

Breadcrumbs describe route and authority:

```text
<screen> / <entity> / <subview> / AUTH=<canonical-writer-or-UNKNOWN>
```

Examples:

```text
Queue / TP-055 / detail / AUTH=task-orchestrator
Execution / TP-055 / proof / AUTH=dopetask
PM / LT-412 / decisions / AUTH=ConPort
Search / query:runner-timeout / AUTH=dope-context-derived
```

## 9. Search And Filter Model

- The filter row shows one line on mobile.
- Expanded filters open as a full-screen overlay.
- Result rows carry source path, source system, derived/canonical label, and
  stale/fresh status when known.
- Retrieved code/docs/results remain leads back to the source file or upstream
  system.

## 10. Focus Model

- Narrow mode: one active region only.
- `80x24`: one primary region and minimal chrome.
- `100x30` or `100x32`: one primary region plus one secondary region.
- `120x40+`: optional third region for provenance, proof, or segregated bridge
  detail.
- Focus order is deterministic: primary list, detail, action rail, chrome.
- There is always one obvious Back/Esc equivalent.

## 11. Modal And Overlay Behavior

- Command Palette, Safe Action Gate, and Help are full-screen overlays on
  mobile.
- Do not stack overlays.
- T4, T5, and TU actions always use full-screen review.
- Popups and tmux menus are optional desktop conveniences, never required
  mobile controls.

## 12. Help Overlay

Help is context-sensitive and full-screen on mobile. It shows:

- current screen purpose
- authority boundary
- keybindings available from the current route
- proof expectation for actions
- how to leave the screen
- current unresolved UNKNOWNs, if any

Help text must not imply that Cockpit owns upstream truth.

## 13. Safe Action Gate Tiers

These tier names are a mobile UX taxonomy. Runtime mapping to the current
`runtime_contract.py` constants is `UNKNOWN` until a runtime packet implements
or rejects the mapping.

Confirmation is intent evidence only. It is not completion proof.

| Tier | Allowed examples | Forbidden examples | Canonical writer requirement | Confirmation requirement | Proof requirement | Receipt requirement | Refusal behavior | Mobile UX rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `T0_READ_ONLY` | View status, open proof, inspect source path. | Any mutation, write, execution, or generated command that changes state. | Writer may be `none`; source authority still labeled. | None. | Source path or read timestamp when relevant. | Optional read receipt. | Refuse mutation request. | Inline view allowed; no modal required. |
| `T1_INSPECT` | Run bounded diagnostics, query health, validate packet schema. | State changes, service start/stop, writes, destructive operations. | Target inspected system named or `UNKNOWN`. | Explicit invoke. | Inspect output, timestamp, command, exit code when command runs. | Inspect receipt recommended. | If target or side effect unknown, downgrade/refuse. | Full-screen output on narrow viewports. |
| `T2_GENERATE_COMMAND` | Generate a command for operator copy/review. | Execute generated command, hide risk, omit cwd. | Proposed writer and cwd named or `UNKNOWN`. | Explicit copy/accept intent only. | Generated command text and rationale. | Command-generation receipt. | If writer/cwd unresolved, route to Unknown/Drift. | Show command, cwd, writer, and proof expectation together. |
| `T3_SUPERVISED_EXECUTION` | Run approved non-mutating or low-risk command with visible output. | Background hidden execution, implicit retries, missing proof path. | Writer or inspected authority named. | Explicit confirmation. | Exit code, output summary/path, command, cwd. | Execution receipt. | Abort on stale request, changed cwd, or unknown side effect. | Full-screen running state with cancel/abort visible. |
| `T4_STATE_MUTATION` | Write PM metadata to Leantime, log decision to ConPort, update workflow through task-orchestrator. | Cross-authority save-all, bridge-owned canonical write, silent mirror writes. | Canonical writer required and must not be bridge/retrieval/Cockpit unless repo evidence proves it. | Explicit confirmation; typed field/action for sensitive writes. | File-backed or upstream receipt-backed proof. | Required canonical writer receipt plus mirror receipt when mirrors exist. | Refuse if writer, rollback, proof, or side effects are unknown. | Full-screen gate. Writer and proof path must stay visible. |
| `T5_DESTRUCTIVE` | Delete/archive/prune only when separately authorized. | Destructive action from palette, implied cleanup, broad deletion. | Canonical writer and rollback/restore path required. | Typed confirmation plus exact target. | Pre/post evidence, receipt, and rollback/restore record. | Required destructive receipt. | Default deny. | Full-screen gate with exact target and irreversible warning. |
| `TU_UNKNOWN_RISK` | Inspect unknown action, copy recommended packet prompt. | Execute, mutate, auto-classify as safe. | Writer unknown by definition. | None for execution; inspect only. | Blocked reason and unknown ledger. | Unknown/refusal receipt. | Fail closed. | Full-screen blocked reason with next evidence needed. |

## 14. Proof / Receipt Display Pattern

Every proof view or action result shows:

- action/request ID when available
- canonical writer
- authority domain
- safety tier
- confirmation record if any
- proof artifact path
- validation command and exit code
- timestamp
- upstream receipt ID or file hash when available
- mirror receipt ID when mirrors exist
- stale/fresh status
- missing proof as explicit `UNKNOWN` or `PENDING`, never success

Proof must be file-backed and replayable. Clipboard, color, UI toast, and
confirmation button state are not proof.

## 15. Mobile Layout Fallbacks

- Prefer truncation with inspect/drill-down over wrapping dense rows.
- Collapse bridge/proxy/retrieval detail before canonical state.
- Collapse decorative chrome before proof, writer, tier, and error state.
- If text cannot fit, route to full-screen detail.
- Keep one-line current filter; expand filters on demand.
- Use ASCII fallback for glyph-sensitive operator surfaces.

## 16. Anti-Patterns

- Cockpit as a fake unified brain.
- dopecon-bridge as PM/workflow/decision/progress authority.
- dope-context retrieval result as source truth.
- Safe action confirmation as completion proof.
- Clipboard as proof transport.
- Mouse-required or hover-required controls.
- F-key-only navigation.
- Permanent multi-pane layout under narrow viewports.
- Cross-authority save-all.
- Hidden retries, silent fallbacks, or implicit coercions.
- Generated reports promoted above runtime/source truth.

## 17. Open UNKNOWNs

- Whether the under-70-column fallback should replace or coexist with the
  current below-`80x24` blocker.
- Exact runtime mapping between `T0_READ_ONLY` style names and current
  `runtime_contract.py` tier constants.
- Canonical writers for future Cockpit actions not yet represented in the
  runtime action catalog.
- Terminal capability probes for Blink + tmux + SSH + Mosh.
- Whether mobile tmux mouse, OSC 52, extended keys, glyphs, and true color are
  reliable enough for anything beyond optional convenience.
- Proof schema for mobile UI action receipts.
- Relationship between in-repo task-orchestrator service and the upstream local
  13-tool MCP Task Orchestrator remains a boundary, not one unified runtime.

## 18. Prototype Acceptance Contract

A future prototype packet should be read-only first and must satisfy:

- No runtime writes or upstream mutations.
- Deterministic render snapshots for `80x24`, `100x32`, and `120x40`.
- Explicit decision on under-70-column fallback vs current blocker.
- Authority label visible on every data screen.
- Bridge and retrieval outputs visibly derived/proxy.
- Command Palette broker-only behavior.
- Safe Action Gate refuses `TU_UNKNOWN_RISK`.
- Proof viewer distinguishes pending, missing, stale, and passing proof.
- Mobile navigation works without mouse, hover, or F-keys.
- Terminal diagnostics report unknown capabilities as `UNKNOWN`, not supported.
- Tests cover viewport degradation and forbidden authority claims.

## 19. Cross-References

- Research manifest:
  `docs/06-research/mobile-tmux-tui/source-manifest.md`
- Mobile constraints:
  `docs/06-research/mobile-tmux-tui/01-mobile-blink-ssh-constraints.md`
- Framework architecture:
  `docs/06-research/mobile-tmux-tui/02-tui-framework-architecture.md`
- UX research:
  `docs/06-research/mobile-tmux-tui/03-dopemux-cockpit-ux-spec.md`
- Existing TUI spec:
  `docs/03-reference/systems/dopemux/tui-spec-v2-0a.md`
- Existing Cockpit safety overlay:
  `docs/03-reference/Dopemux Cockpit TUI Design System/ARCHITECTURE_SAFETY_OVERLAY.md`
