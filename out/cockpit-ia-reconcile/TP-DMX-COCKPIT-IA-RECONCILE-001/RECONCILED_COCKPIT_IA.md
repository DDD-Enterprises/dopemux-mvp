# Reconciled Cockpit IA

## 1. Verdict

CURRENT_COCKPIT_IA_PARTIAL_CONDITIONAL_PRIMITIVES_ONLY

Claude Design may resume only conditionally for primitives and shell contracts. Final screens remain blocked.

- safe_for_claude_design: CONDITIONAL
- READY_FOR_CLAUDE_DESIGN: conditional
- Baseline inventory rows: 405
- Active rows: 366
- High-risk rows: 199
- Missing coverage rows: 284

## 2. Evidence Base

Primary input was the prior command inventory JSON. Its counts were preferred over markdown when producing this packet.

- Coverage: {'MISSING': 284, 'OUT_OF_SCOPE': 7, 'PARTIAL': 82, 'UNKNOWN': 32}
- Safe UI exposure: {'BLOCKED_IN_COCKPIT': 48, 'COMMAND_PALETTE_ONLY': 40, 'CONFIRM_REQUIRED': 111, 'DISPLAY_ONLY': 178, 'INSPECT_ACTION': 23, 'UNKNOWN': 5}
- Placement: {'Command Palette': 139, 'Events': 15, 'External/Not Cockpit': 37, 'Implementer': 73, 'Overview': 9, 'PM': 15, 'Services': 54, 'Settings/Admin': 62, 'UNKNOWN': 1}
- Authority domains: {'ADHD/operator support': 21, 'ConPort structured context/decision/progress': 15, 'Repo Truth Extractor audit/extraction': 44, 'dope-memory chronicle': 15, 'dopecon-bridge adapter/proxy/event transport': 11, 'dopemux operator control': 145, 'dopetask execution handoff': 109, 'routing/model-provider support': 20, 'task-orchestrator workflow': 11, 'unknown / conflicting': 14}

Current worktree authority files confirm the same boundary rule: Dopemux is operator control, Dopetask is execution handoff, task-orchestrator owns workflow coordination, ConPort owns structured decision/progress/context slices, dope-memory owns chronicle history, dope-context owns retrieval/indexing, dopecon-bridge is adapter/proxy/event transport, ADHD Engine is operator support, and Repo Truth Extractor is audit/extraction runtime.

## 3. Current Five-Mode Assessment

The five modes remain valid as primary operator lenses, but they are insufficient as the whole IA.

| Mode | Decision | Reason |
| --- | --- | --- |
| PM | keep top-level | PM is workflow triage and handoff readiness. It must not claim unified PM truth. |
| Implementer | keep top-level | Implementer owns task focus and evidence framing, not execution truth after dopetask handoff. |
| Overview | keep top-level | Overview is the right status/drift lens and safe launch context. |
| Services | keep top-level | Services covers service status and child workload inspection, but not all admin/runtime mutation. |
| Events | keep top-level | Events covers chronicle/event/capture views while preserving dope-memory boundaries. |

## 4. Reconciled Navigation Model

Recommended primary mode bar remains exactly:

1. PM
2. Implementer
3. Overview
4. Services
5. Events

Required global/secondary surfaces:

- Command Palette: global, always available, required for rare and parameter-heavy commands.
- Settings/Admin/Runtime: major secondary surface, not hidden inside Services.
- Safe Actions / Proof Gate: cross-cutting gate before non-read actions.
- Unknown/Drift Queue: non-executable queue for unproven commands and authority drift.

## 5. Required Surfaces

Required surfaces are defined in SCREEN_CONTRACT_MATRIX. No final screen is approved. Shell contracts and primitives are approved conditionally.

- Overview
- PM
- Implementer
- Services
- Events
- Command Palette
- Settings/Admin/Runtime
- Routing/Model Provider
- Execution Handoff
- Repo Truth / Audit
- PR Merge
- System Data
- Mobile/Tmux
- Hooks/Profile/Env
- Safe Actions / Proof Gate
- Unknown/Drift Queue

## 6. Command Palette Role

Command Palette is mandatory. It owns discovery and parameter preview for commands that are rare, admin-heavy, parameter-heavy, or inappropriate for the five primary homes. It must show command path, authority domain, safety class, required gate, parameters, and blocked status. It must not execute blocked or unknown actions.

## 7. Settings / Admin / Runtime Role

Settings/Admin/Runtime is required as a major secondary surface because the inventory places 62 rows in that family and routing/profile/hooks/env/debug actions cannot be safely mixed into PM, Implementer, Services, or Events home screens. It may be presented as an admin surface reachable from Overview, Services, and Command Palette; it should not become a silent sixth data-authority claim.

## 8. Safe Action Model

Safe Action Gate is required before final UI. The gate must classify every candidate action as DISPLAY_ONLY, INSPECT_ACTION, CONFIRM_REQUIRED, COMMAND_PALETTE_ONLY, BLOCKED_IN_COCKPIT, EXTERNAL_ONLY, or UNKNOWN. Confirmation alone is not enough for destructive or remote actions; proof, TP/governance, and audit expectations are class-specific.

## 9. Authority Boundary Map

| Boundary | Cockpit treatment |
| --- | --- |
| Dopemux | Operator control, CLI coordination, shell/runtime framing. |
| Dopetask | Execution handoff runtime; shown through explicit handoff and proof gates. |
| Task-orchestrator | Workflow coordination and workflow-significant transitions. |
| ConPort | Structured decision/progress/context/custom-data slices. |
| Dope-memory | Chronicle and historical receipt authority only. |
| Dope-context | Code/docs retrieval/indexing only. |
| Dopecon-bridge | Adapter/proxy/event transport only; never shown as canonical PM/workflow/decision/progress authority. |
| ADHD Engine | Advisory operator-support/cognitive-state surface only. |
| Repo Truth Extractor | Audit/extraction runtime and evidence artifact generator only. |

## 10. Claude Design Gate

Claude Design is conditional for primitives and shell contracts only.

Allowed:

- navigation skeleton
- command palette primitive
- safe-action confirmation primitive
- proof requirement badge
- blocked action row
- admin/runtime shell
- screen shell placeholders

Blocked:

- final screens implying complete command coverage
- direct high-risk action buttons
- runtime execution flows
- destructive action affordances
- complete Cockpit readiness claims

## 11. Remaining UNKNOWNs

- Root RULES.md is absent in the fresh worktree; docs/reference rules and AGENTS.md were used where available.
- Root TRUTH_*.md files are absent; docs/03-reference/truth equivalents were used.
- Prior command inventory was generated at old HEAD af5c4627 while this fresh worktree is origin/main 4959a089f; no new command inventory was regenerated in this packet.
- Runtime dopemux help remained an input UNKNOWN from the inventory packet because its environment lacked litellm.
- Decision subcommands, optional genetic, and defined-but-not-registered worktree/vault surfaces remain unresolved until runtime registration is repaired or rejected.
- Final runtime renderer, browser visual approval, screenshot approval, and proof JSON validation for Cockpit remain outside this packet.

## 12. Next Packets

Recommended next packet: TP-DMX-COCKPIT-COMMAND-PALETTE-001

Additional follow-ups:

- TP-DMX-COCKPIT-SAFE-ACTIONS-001
- TP-DMX-COCKPIT-UIKIT-RENDER-001
- TP-DMX-COCKPIT-RUNTIME-RENDER-001
