# PM/Implementer Cockpit Processing Pack - 2026-04-24

## 1. Executive readout

- verdict: Proceed to GPT-5.5 Pro synthesis and Claude Design only as an evidence pack. Do not implement UI/runtime/service changes from this packet.
- current cockpit stack state: Open PR search for "cockpit static" showed PR #524 DMX-COCKPIT-STATIC-001-equivalent static renderer merged to main at 2026-04-24T23:40:08Z and PR #528 CLI static demo merged to main at 2026-04-24T23:40:44Z; PR #525 against the intermediate branch is closed. Exact packet IDs were not present in PR titles, so dependency mapping is inferred from branch/title correspondence and marked as stack-status evidence, not packet-completion proof.
- dependency drift: Current local checkout is on `codex/rte-wizard-prescan-telemetry` with unrelated runtime/test/generated changes before this packet. This packet creates only allowlisted docs/proof/task-packet files. Task-orchestrator runtime and Docker packaging remain drifted in repo truth docs.
- highest-risk design assumption: a PM cockpit can look like a single authoritative PM record. Runtime evidence rejects that assumption; PM truth is split across Leantime, task-orchestrator, ConPort, dope-memory mirror receipts, dope-context, and Serena/technical retrieval.

## 2. Authority map

### PM metadata

- canonical owner: Leantime metadata, accessed through leantime-bridge tool surfaces and normalized by `src/dopemux/pm/writes.py`.
- supporting surfaces: `pm_get_sprint_snapshot`, leantime-bridge `list_projects`, `list_tickets`, `update_ticket`.
- mirror/adapter surfaces: `services/dopecon-bridge/dopecon_bridge/routes.py` `/route/pm` may route adapter-safe PM operations but is not authority.
- allowed reads: project/ticket/sprint snapshot where Leantime credentials/runtime exist.
- allowed writes: passive metadata only (`headline`, `description`, assignment aliases) through `pm_update_work_item`/Leantime update surface.
- forbidden UI implication: do not show Leantime status as workflow authority; do not let a PM metadata edit imply transition approval.
- evidence paths: `src/dopemux/pm/writes.py`, `src/dopemux/pm/reads.py`, `docker/mcp-servers/leantime-bridge/leantime_bridge/http_server.py`, `services/dopecon-bridge/dopecon_bridge/routes.py`.

### Workflow transitions

- canonical owner: task-orchestrator workflow authority candidate.
- supporting surfaces: `pm_get_priority_queue`, `pm_get_blockers`, `pm_get_workflow_state`, `pm_transition_work_item`, `services/task-orchestrator/app/main.py` workflow routes.
- mirror/adapter surfaces: dopecon-bridge task/status routes fail closed for workflow-significant mutations.
- allowed reads: queue, blockers, workflow state, allowed transitions.
- allowed writes: guarded transitions to `start`, `block`, `done` through task-orchestrator client path in `pm_transition_work_item`.
- forbidden UI implication: do not route transition buttons through bridge; do not show transition as available when `allowed_transitions` is unavailable/UNKNOWN.
- evidence paths: `src/dopemux/pm/reads.py`, `src/dopemux/pm/writes.py`, `services/task-orchestrator/app/main.py`, `services/dopecon-bridge/dopecon_bridge/routes.py`.

### Decisions/progress

- canonical owner: ConPort for structured decisions/progress.
- supporting surfaces: `pm_get_decision_context`, `pm_log_progress`, `pm_log_decision`, ConPort MCP/HTTP tools, dopecon-bridge `/kg/decisions` and `/kg/progress` proxy routes.
- mirror/adapter surfaces: dopecon-bridge proxies to ConPort; dope-memory mirrors chronicle receipt from PM writes.
- allowed reads: decisions, progress, decision search.
- allowed writes: progress/decision logs through ConPort canonical client.
- forbidden UI implication: do not treat bridge `/kg/*` as decision authority; label it as proxy if displayed.
- evidence paths: `src/dopemux/pm/reads.py`, `src/dopemux/pm/writes.py`, `src/conport/memory_server.py`, `services/dopecon-bridge/dopecon_bridge/routes.py`.

### Chronicle/evidence

- canonical owner: dope-memory chronicle/evidence runtime, with dope-memory mirror receipt from PM writes.
- supporting surfaces: working-memory-assistant chronicle store, dope-memory main service, dope-memory mirror receipt in `CanonicalReceipt`.
- mirror/adapter surfaces: WMA MCP transport canonicality is unresolved; dope-memory mirror is not PM status authority.
- allowed reads: chronicle/evidence history where dope-memory runtime exists.
- allowed writes: append chronicle/evidence as mirror receipt when ConPort progress/decision succeeds.
- forbidden UI implication: do not show mirror success as canonical PM write success unless canonical ConPort write also succeeded.
- evidence paths: `src/dopemux/pm/writes.py`, `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/chronicle/store.py`, `docs/03-reference/truth/truth-canonicals.md`.

### Retrieval

- canonical owner: dope-context for deterministic code/docs retrieval; ConPort for decision context; Serena technical context canonicality remains UNKNOWN.
- supporting surfaces: `pm_search_project_knowledge`, `pm_get_technical_context`, dope-context MCP search tools, Serena proxy config.
- mirror/adapter surfaces: dopecon-bridge decision search proxy is adapter-only.
- allowed reads: project knowledge, technical context, decisions.
- allowed writes: none for first PM/Implementer redesign.
- forbidden UI implication: do not make retrieval panes look like PM state editors.
- evidence paths: `src/dopemux/pm/reads.py`, `services/dope-context/src/mcp/server.py`, `services/dope-context/README.md`, `docs/03-reference/truth/truth-gaps.md`.

### Bridge/proxy

- canonical owner: none for PM truth; bridge is adapter/proxy only.
- supporting surfaces: `/route/pm`, `/kg/*`, `/ddg/*`, `/events/*`.
- mirror/adapter surfaces: all bridge PM/ConPort adjacent operations remain adapter/proxy.
- allowed reads: normalized proxy reads to Leantime/ConPort where authenticated.
- allowed writes: adapter-safe PM metadata routing and ConPort proxy writes only when downstream canonical owner accepts them; workflow-significant writes fail closed.
- forbidden UI implication: no bridge-as-authority pane, chip, or workflow transition control.
- evidence paths: `services/dopecon-bridge/dopecon_bridge/routes.py`, `services/dopecon-bridge/main.py`, `docs/03-reference/truth/truth-gaps.md`.

### Execution handoff

- canonical owner: external `dopetask` runtime via repo wrapper `scripts/dopetask`; `scripts/taskx` is compatibility shim.
- supporting surfaces: `dopemux kernel` command group, task packet index, proof artifacts.
- mirror/adapter surfaces: TaskX naming remains compatibility/deprecated language.
- allowed reads: task packet/proof state from repository files.
- allowed writes: none in first design brief; later implementation packet may define renderer behavior.
- forbidden UI implication: do not imply the cockpit owns packet execution truth.
- evidence paths: `docs/03-reference/truth/truth-canonicals.md`, `scripts/dopetask`, `scripts/taskx`, `src/dopemux/commands/kernel_commands.py`.

### ADHD/operator support

- canonical owner: support-only for this redesign; task-orchestrator MCP has ADHD-oriented tools, and dope-context has ADHD retrieval features.
- supporting surfaces: `get_adhd_state`, `record_break`, task recommendations, dope-context progressive disclosure docs.
- mirror/adapter surfaces: mobile/happy/ADHD services are outside primary PM/Implementer authority.
- allowed reads: support signals if available.
- allowed writes: deferred.
- forbidden UI implication: do not make ADHD support a new top-level mode or new chip set.
- evidence paths: `services/task-orchestrator/task_orchestrator/mcp/__init__.py`, `services/dope-context/README.md`.

### UNKNOWNs

- Task-orchestrator active Python runtime points to services/task-orchestrator/app/main.py, but Docker/runtime packaging drift remains unresolved.
- Serena canonical surface is UNKNOWN because repo contains in-repo service code and external Docker wrapper/proxy config.
- Active MCP server configs list external/proxy servers whose live tool inventories were not queried by packet rule; only repo-observed tool declarations are inventoried.
- Bridge routes expose PM/ConPort-adjacent operations but are adapter/proxy only; UI must not upgrade them to authority.
- Working-memory-assistant and dope-memory surfaces overlap; dope_memory_main.py is canonical for dope-memory, WMA MCP transport canonicality remains unresolved.
- Current checkout has unrelated pre-existing runtime/test changes on codex/rte-wizard-prescan-telemetry; packet artifacts are limited to allowlisted docs/proof/task-packet files.

## 3. Callable Surface Inventory

### Raw Inventory Summary

- total_mcp_tools: 123
- total_http_routes: 484
- total_cli_commands: 248
- total_service_functions: 605
- total_adapter_functions: 386
- unknown_count: 870

Full raw tables are in `docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md`.

### Top PM-Relevant Capabilities

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

### Top Implementer-Relevant Capabilities

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

### Deferred Capability Groups

- retrieval-only: dope-context and Serena surfaces not required for first layout beyond read-only evidence panes.
- bridge/admin: bridge health, auth, event stream, route/proxy controls.
- RTE/audit: extractor and validation commands remain child/workload surfaces; RTE extraction was not run.
- ADHD/operator support: task recommendations, break/session support, progressive disclosure.
- ingress/config: MCP proxy config, service launch, routing config.
- legacy/deprecated: `taskx` naming, hard-failing task-orchestrator module, duplicate service residues.
- unknown: unresolved active server tool inventories for external/proxy-only configs.

## 4. Operator workflows

### 1. PM creates or triages story

- trigger: PM opens cockpit to plan/triage work.
- operator goal: see work item metadata, queue/blockers, decisions, and next action without conflating sources.
- canonical source: Leantime for passive metadata; task-orchestrator for queue/blockers/workflow state; ConPort for decisions.
- supporting sources: dope-context retrieval, dope-memory chronicle mirror.
- visible state: story title/description/assignee `SRC=leantime`, queue/blockers `SRC=task-orchestrator`, decisions `SRC=conport`.
- allowed actions: read, edit passive metadata, request transition route if allowed.
- forbidden actions: bridge-local status mutation, unified PM save, workflow status edit through Leantime metadata.
- failure mode: task-orchestrator unavailable yields `legality_result=unavailable` in read envelope.
- next action: show UNKNOWN/unavailable and block transition controls.
- UI implication: three authority-labeled panes instead of one overloaded PM card.

### 2. PM sends handoff

- trigger: PM decides a work item is ready for implementation.
- operator goal: hand off enough context without creating new authority.
- canonical source: task-orchestrator workflow state plus task packet/proof files for execution handoff.
- supporting sources: ConPort decisions, dope-context evidence, Leantime metadata.
- visible state: active workflow state, blockers, acceptance/evidence refs.
- allowed actions: produce or reference handoff packet, transition via task-orchestrator if allowed.
- forbidden actions: direct bridge transition or ad hoc adapter write.
- failure mode: allowed transition missing/UNKNOWN.
- next action: ask PM to resolve blocker or generate implementation packet in later TP.
- UI implication: handoff panel must show canonical transition target and evidence refs.

### 3. Implementer receives/focuses

- trigger: Implementer mode opens on assigned packet/work item.
- operator goal: identify current task, source authority, blockers, and first evidence step.
- canonical source: task-orchestrator state/queue and repo task packet/proof files.
- supporting sources: ConPort decisions, dope-context, Serena technical retrieval.
- visible state: work item, blockers, next action, authority labels.
- allowed actions: read context, inspect repo, run declared validation when implementation packet allows it.
- forbidden actions: PM metadata writes, bridge transition, live service writes.
- failure mode: packet status and task-orchestrator state disagree.
- next action: show drift banner and require PM review.
- UI implication: focus panel should prioritize one work item, Top-3 evidence refs, and continuation token.

### 4. Implementer gathers evidence

- trigger: implementer needs context before making changes.
- operator goal: retrieve code/docs/decision context without changing PM state.
- canonical source: dope-context for retrieval, ConPort for decisions, repo files for runtime truth.
- supporting sources: Serena technical context if available; dope-memory chronicle history.
- visible state: Top-3 evidence refs with `SRC` and `authority:`.
- allowed actions: read-only search/inspect.
- forbidden actions: run RTE extraction, call live services, or mutate PM state in this packet.
- failure mode: retrieval source unavailable or canonicality UNKNOWN.
- next action: fall back to repo inspection and mark UNKNOWN.
- UI implication: retrieval pane is read-only, bounded, and source-labeled.

### 5. Implementer sends handback

- trigger: implementation/evidence packet is ready for PM review.
- operator goal: report what changed, validation, proof refs, and remaining uncertainty.
- canonical source: proof artifacts in repo and ConPort progress/decision logs when writes are allowed by a later packet.
- supporting sources: dope-memory mirror receipt.
- visible state: validation results, files touched, proof path, handback notes.
- allowed actions: create file-based proof in this evidence-only packet; later packets may log progress.
- forbidden actions: claim completion without validation or invent proof metadata.
- failure mode: validation not run or proof JSON invalid.
- next action: block handback acceptance until proof is valid.
- UI implication: handback panel needs validation status and remaining uncertainty, not a success-only summary.

### 6. PM reviews/accepts/transitions

- trigger: PM receives handback.
- operator goal: compare requested acceptance against evidence and transition only if authority allows it.
- canonical source: task-orchestrator transition route for workflow; proof JSON/docs for evidence; ConPort for decisions/progress.
- supporting sources: Leantime metadata and dope-memory mirror.
- visible state: diff/proof status, transition eligibility, blockers.
- allowed actions: accept, block, request changes through task-orchestrator path.
- forbidden actions: direct bridge status patch, Leantime status-as-workflow shortcut.
- failure mode: proof passes but workflow transition unavailable.
- next action: leave state unchanged and record blocker.
- UI implication: PM review requires separate Evidence, Decision, and Transition controls.

### 7. Bridge-risk blocker case

- trigger: operator sees a convenient bridge route that appears to update PM/task state.
- operator goal: avoid accidental authority collapse.
- canonical source: `services/dopecon-bridge/dopecon_bridge/routes.py` contract and failure behavior.
- supporting sources: truth gaps docs.
- visible state: bridge route marked adapter/proxy; workflow-significant operations blocked.
- allowed actions: adapter-safe reads/proxy calls where appropriate.
- forbidden actions: bridge-as-authority, bridge-local task creation/status update.
- failure mode: design presents bridge controls beside canonical controls without distinction.
- next action: segregate bridge/admin surfaces and require authority label.
- UI implication: bridge panel is diagnostic/support-only, not PM action center.

## 5. Current PM/Implementer mock critique

### Architecture violations

- Any mock that presents PM state as a single backend violates `src/dopemux/pm/reads.py` and `src/dopemux/pm/writes.py` authority split.
- Any bridge action rendered as canonical workflow control violates `services/dopecon-bridge/dopecon_bridge/routes.py`.
- Any RTE extraction affordance in this workflow must remain child/workload, not PM/Implementer state authority.

### Authority ambiguity

- Pane titles must include `authority:` because the same semantic object can be seen through Leantime, task-orchestrator, ConPort, dope-memory, dope-context, or bridge proxy.
- Rows must include `SRC` so a designer cannot silently merge decisions, metadata, workflow state, and chronicle receipts.

### Cognitive-load risks

- Raw MCP/HTTP/CLI inventory is too large for PM or Implementer first-screen use: 123 MCP tools, 484 routes, 248 CLI surfaces, and 991 included functions.
- Top-3 plus continuation token is required for PM priorities, Implementer evidence, design risks, and deferred surfaces.

### Layout/geometry issues

- A dense cockpit can work only if it separates state panes by authority owner. Overcrowding multiple source planes into one pane creates false certainty.
- 80x24 adaptation must preserve source labels even if secondary metadata is collapsed.

### Command/action ambiguity

- `update`, `transition`, `log`, `route`, and `mirror` are different action classes. Button/keybinding labels must not hide the side-effect class.
- Bridge and MCP exposure should never be used as visual proof of authority.

### Visual preference only

- Color, border style, and pane density are design choices only after authority labels, SRC rows, and forbidden action segregation are preserved.

## 6. Top-3 redesign priorities

```yaml
items:
  - id: P1
    priority: Preserve authority/SRC labels everywhere
    evidence: src/dopemux/pm/reads.py emits canonical_backend per result; dopecon-bridge declares adapter-only runtime.
    risk_if_unfixed: PM and Implementer users will trust the wrong source or perform forbidden bridge/metadata workflow actions.
    design_direction: Every pane title includes authority; every row includes SRC; UNKNOWN remains text not chip.
  - id: P2
    priority: Split handoff and handback from general task state
    evidence: task-orchestrator owns workflow state; dopetask wrapper owns execution handoff boundary; proof artifacts are file-based.
    risk_if_unfixed: The cockpit implies it owns execution or PM truth when it only displays/adjudicates bounded surfaces.
    design_direction: Separate Handoff, Evidence, Validation, and Transition panels with explicit allowed/forbidden actions.
  - id: P3
    priority: Compress callable surfaces into Top-3 capability groups
    evidence: static inventory found broad MCP/HTTP/CLI/function surface counts that exceed first-screen operator needs.
    risk_if_unfixed: Raw tools become UI content and crowd out real PM/Implementer workflows.
    design_direction: Show Top-3 capability groups plus more_count and next_token; keep raw inventory out of Claude Design UI content.
more_count: 4
next_token: redesign-deferred-risks
```

## 7. Constraints for design

- must preserve: split PM authority, `authority:` pane labels, row-level `SRC`, bridge adapter-only status, task-orchestrator workflow transition boundary, ConPort decision/progress authority, dope-memory mirror distinction, RTE as child/workload surface.
- may change: pane ordering, labels, keyboard shortcuts, density, 120x40/100x32/80x24 adaptation, visual hierarchy, grouping of deferred support surfaces.
- must not change: architecture, backend authority, top-level modes, status chips, bridge-as-authority, unified PM record, live writes, web UI, raw callable inventory as UI content.
- UNKNOWN: task-orchestrator Docker runtime alignment, Serena canonicality, external/proxy MCP tool inventories not statically present, WMA MCP transport canonicality.

## 8. Appendix: raw evidence ledger

- Repo identity commands: `git rev-parse --show-toplevel`, `test -f .dopetaskroot`, `git remote -v`, `git branch --show-current`, `git status --short --branch`, `git branch -vv`.
- Stack state command: `gh pr list --state all --limit 100 --search "cockpit static" --json number,title,headRefName,baseRefName,state,isDraft,mergedAt,url`.
- Callable scan command: `rg -n "@mcp\.tool|FastMCP|Server\(|@app\.|APIRouter\(|@router\.|click\.group|click\.command|@click\.group|@click\.command|def .*\(" src services scripts docker/mcp-servers-source docker/mcp-servers mcp-proxy-config*.yaml mcp-proxy-config*.json`.
- File list command: `find src services scripts docker/mcp-servers-source docker/mcp-servers -type f (...) | sort`.
- AST evidence: `/tmp/cockpit-callable-functions.json` with 4961 raw rows before filtering.
- Normalized inventory evidence: `/tmp/cockpit-inventory-summary.json`.
- Primary runtime evidence: `src/dopemux/pm/reads.py`, `src/dopemux/pm/writes.py`, `services/task-orchestrator/app/main.py`, `services/dopecon-bridge/dopecon_bridge/routes.py`, `src/conport/memory_server.py`, `services/working-memory-assistant/dope_memory_main.py`, `services/dope-context/src/mcp/server.py`.
