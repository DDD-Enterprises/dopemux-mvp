# PM/Implementer Cockpit Design Brief - 2026-04-24

## 1. GPT-5.5 Pro prompt

You are GPT-5.5 Pro analyzing a repo-grounded PM/Implementer cockpit evidence pack for `DDD-Enterprises/dopemux-mvp`.

Task: analyze and synthesize. Do not generate final UI mocks. Do not propose runtime changes, service changes, adapters, new writes, or architecture consolidation.

Inputs to use:
- `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md`
- `docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md` only as appendix evidence
- `proof/cockpit-pm-implementer-processing-pack-2026-04-24.proof.json`

Instructions:
1. Critique the PM/Implementer mode concept against the observed authority split.
2. Preserve architecture boundaries: Leantime metadata, task-orchestrator workflow, ConPort decisions/progress, dope-memory chronicle mirror, dope-context retrieval, Serena UNKNOWN/candidate, dopecon-bridge adapter-only.
3. Identify PM and Implementer top workflows and failure modes.
4. Compress capability groups into layout priorities for a terminal cockpit.
5. Produce a design-ready brief for Claude Design.
6. Mark UNKNOWN explicitly and do not convert UNKNOWN into visual certainty.
7. Avoid implementation plans, runtime changes, service adapters, live writes, or new backend contracts.
8. Do not feed raw callable inventory rows into design content; use only the compressed capability groups below.

Expected GPT-5.5 Pro output:
- concise synthesis of authority constraints
- PM Top-3 workflow priorities
- Implementer Top-3 workflow priorities
- risks that Claude Design must avoid
- exact design questions Claude Design should answer
- acceptance checklist for static renderer/Textual-wrapper feasibility later

## 2. Claude Design prompt

You are Claude Design. Produce revised PM and Implementer TUI mocks for Dopemux cockpit based only on the compressed workflow/capability constraints below.

Hard constraints:
- no architecture changes
- no new top-level modes
- no new chips
- no web UI
- no live writes
- no bridge-as-authority
- no unified PM record
- no raw callable inventory as UI content
- preserve `authority:` in every pane title
- preserve `SRC` on every list row
- preserve RTE as child/workload surface
- segregate bridge/proxy/admin actions from canonical PM and Implementer actions
- `UNKNOWN` may appear only as text, not as a status chip

Design target:
- terminal cockpit mocks, primary size 120x40
- adaptations for 100x32 and 80x24
- PM mode and Implementer mode only
- use compressed capability groups, Top-3 lists, `more_count`, and `next_token`

## 3. Design input summary

### Top-3 PM capability groups

```yaml
items:
  - capability: PM triage and planning from split sources
    authority: Leantime metadata plus task-orchestrator queue/blockers plus ConPort decisions
    functions:
      - pm_get_sprint_snapshot
      - pm_get_priority_queue
      - pm_get_blockers
      - pm_get_decision_context
      - list_tickets
      - list_workflow_ideas
    ui_implication: PM mode needs a triage panel with per-row SRC and authority labels, not a single PM record.
  - capability: Workflow adjudication and review
    authority: task-orchestrator for workflow transitions; bridge routes are adapter-only and fail closed for workflow-significant mutations
    functions:
      - pm_get_workflow_state
      - pm_transition_work_item
      - POST /api/projects/{project_id}/workflows/{workflow_id}/transitions/{transition_name}
      - PATCH /tasks/{task_id}/status blocked
    ui_implication: Transitions need guarded actions and visible blockers/allowed transitions; bridge controls must be segregated.
  - capability: Decision, progress, chronicle evidence
    authority: ConPort for decisions/progress; dope-memory as chronicle/evidence mirror receipt
    functions:
      - pm_log_progress
      - pm_log_decision
      - create_decision
      - create_progress
      - append_chronicle
      - list_decisions
      - list_progress
    ui_implication: Use evidence/decision panes with canonical SRC and mirror receipt state; do not imply dope-memory owns PM status.
more_count: 4
next_token: pm-deferred-capability-groups
```

### Top-3 Implementer capability groups

```yaml
items:
  - capability: Focused handoff intake and next action
    authority: task-orchestrator workflow state plus dopetask execution handoff boundary
    functions:
      - pm_get_workflow_state
      - pm_get_priority_queue
      - scripts/dopetask
      - kernel_* taskx compatibility commands
    ui_implication: Implementer mode should show active packet, blockers, next action, and execution boundary without creating task state.
  - capability: Evidence retrieval for implementation context
    authority: dope-context retrieval, Serena technical context UNKNOWN/candidate, ConPort decisions
    functions:
      - pm_search_project_knowledge
      - pm_get_technical_context
      - search_all
      - find_symbol
      - search_decisions
    ui_implication: Context panes should be read-only, source-labeled, and capped to Top-3 with continuation token.
  - capability: Handback, progress, and proof logging
    authority: ConPort decision/progress canonical logs with dope-memory mirror receipts; proof artifacts remain file-based evidence
    functions:
      - pm_log_progress
      - pm_log_decision
      - append_chronicle
      - create_progress
      - create_decision
    ui_implication: Handback panel should capture evidence refs and validation status; writes must show canonical target and mirror result.
more_count: 4
next_token: implementer-deferred-capability-groups
```

### Deferred capability groups count

```yaml
items:
  - retrieval-only
  - bridge/admin
  - RTE/audit
  - ADHD/operator support
  - ingress/config
  - legacy/deprecated
  - unknown
more_count: 7
next_token: deferred-capability-groups-detail
```

### Most dangerous UNKNOWNs

```yaml
items:
  - id: U1
    unknown: task-orchestrator Docker/runtime packaging alignment remains unresolved
    design_rule: show task-orchestrator as workflow authority candidate, not as proven single deployment truth
  - id: U2
    unknown: Serena canonical surface is unresolved between in-repo service and external wrapper/proxy config
    design_rule: show Serena-derived technical context as optional/UNKNOWN support
  - id: U3
    unknown: external/proxy MCP server live tool inventories were not queried
    design_rule: do not design from absent live tool lists; use only repo-observed capability groups
more_count: 3
next_token: unknowns-full-list
```

## 4. Design output contract

Claude Design must output:

1. revised PM 120x40 mock
2. revised Implementer 120x40 mock
3. 100x32 adaptation notes
4. 80x24 adaptation notes
5. authority/SRC validation checklist
6. action model and keybindings
7. handoff/handback panel contract
8. what changed from prior spec and why

## 5. Acceptance checks for new mocks

- every pane title includes `authority:`
- every list row includes `SRC`
- PM and Implementer do not imply unified backend
- bridge actions segregated
- no new status chips
- no forbidden vocabulary
- `UNKNOWN` appears only as text, not chip
- output remains implementable by static renderer/Textual wrapper later
- PM mode keeps Leantime metadata, task-orchestrator workflow, ConPort decisions/progress, and dope-memory mirror separate
- Implementer mode keeps handoff intake, evidence retrieval, and handback/proof logging separate
- raw MCP/HTTP/CLI/function rows do not appear in UI content
