# Cockpit Design Input Merged Brief - 2026-04-24

Mode: paste-ready synthesis/design input. This is not an implementation plan.

## 1. Input Stack

Use these as separate evidence layers:

1. Runtime/authority layer:
   - `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md`
   - `docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md`
   - `proof/cockpit-pm-implementer-processing-pack-2026-04-24.proof.json`
2. Archived/planned intent layer:
   - `docs/05-audit-reports/cockpit-archive-intent-pack-2026-04-24.md`
   - `docs/05-audit-reports/cockpit-adhd-lifestyle-feature-map-2026-04-24.md`
   - `proof/cockpit-archive-intent-pack-2026-04-24.proof.json`

Evidence tier rule: runtime/authority layer wins over active docs, active docs win over archived docs, and archived docs are product/design intent only.

## 2. GPT-5.5 Pro Prompt

You are GPT-5.5 Pro analyzing a repo-grounded Dopemux PM/Implementer cockpit evidence pack plus a clearly separated archive/planned-intent layer.

Task: synthesize design guidance only. Do not generate final UI mocks. Do not propose runtime changes, service changes, adapters, new writes, data migrations, or architecture consolidation.

Inputs:

- PM/Implementer runtime-authority pack:
  - `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md`
  - `docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md`
  - `proof/cockpit-pm-implementer-processing-pack-2026-04-24.proof.json`
- Archive/planned intent pack:
  - `docs/05-audit-reports/cockpit-archive-intent-pack-2026-04-24.md`
  - `docs/05-audit-reports/cockpit-adhd-lifestyle-feature-map-2026-04-24.md`
  - `proof/cockpit-archive-intent-pack-2026-04-24.proof.json`

Hard constraints:

1. Preserve architecture boundaries:
   - Leantime metadata.
   - task-orchestrator workflow.
   - ConPort decisions/progress/context.
   - dope-memory chronicle/evidence mirror.
   - dope-context retrieval.
   - Serena UNKNOWN/candidate.
   - dopecon-bridge adapter-only.
2. Do not treat archived docs as runtime truth.
3. Do not convert planned-only ADHD/lifestyle features into implemented cockpit capability.
4. Decide whether ADHD/lifestyle intent should affect:
   - PM/Implementer layout directly.
   - a narrow shared support rail.
   - a separate Operator Support mode.
   - deferred product research only.
5. Keep PM and Implementer primary workflows free of lifestyle clutter unless a feature supports a concrete operator workflow.
6. Preserve `authority:` in pane titles and `SRC` in rows for any design guidance inherited from the previous pack.
7. `UNKNOWN` remains text; do not turn it into a status chip or visual certainty.

Questions to answer:

1. Which archive-intent features should influence the PM layout, and why?
2. Which archive-intent features should influence the Implementer layout, and why?
3. Which features belong in a support rail rather than primary panes?
4. Which features should become a separate Operator Support mode?
5. Which features should be excluded or deferred?
6. What should Claude Design explicitly avoid when making TUI mocks?

Expected GPT-5.5 Pro output:

- authority constraint recap
- PM Top-3 priorities after considering archive intent
- Implementer Top-3 priorities after considering archive intent
- Operator Support rail recommendation with `items`, `more_count`, `next_token`
- deferred/excluded capability list
- exact Claude Design prompt amendments
- acceptance checklist for future static renderer/Textual feasibility

## 3. Claude Design Prompt

You are Claude Design. Produce revised terminal cockpit mocks for Dopemux PM and Implementer modes using the runtime-authority pack plus the archive/planned-intent layer. Treat the archive/planned-intent layer as design input only.

Hard constraints:

- no architecture changes
- no new backend contracts
- no service/adaptor additions
- no web UI
- no live writes
- no bridge-as-authority
- no unified PM record
- no raw callable inventory rows as UI content
- preserve `authority:` in every pane title
- preserve `SRC` on every list row
- preserve RTE as child/workload surface
- segregate bridge/proxy/admin actions from canonical PM and Implementer actions
- `UNKNOWN` may appear only as text, not as a status chip
- do not design planned-only ADHD/lifestyle features as if they are implemented

Design target:

- terminal cockpit mocks
- primary size 120x40
- adaptations for 100x32 and 80x24
- PM mode and Implementer mode remain the primary deliverables
- any Operator Support rail must be narrow, source-labeled, and non-authoritative

## 4. Compressed Runtime Capability Groups

### PM

```yaml
items:
  - capability: PM triage and planning from split sources
    authority: Leantime metadata plus task-orchestrator queue/blockers plus ConPort decisions
    ui_implication: PM mode needs a triage panel with per-row SRC and authority labels, not a single PM record.
  - capability: Workflow adjudication and review
    authority: task-orchestrator for workflow transitions; bridge routes are adapter-only
    ui_implication: Transitions need guarded actions and visible blockers/allowed transitions; bridge controls must be segregated.
  - capability: Decision, progress, chronicle evidence
    authority: ConPort for decisions/progress; dope-memory as chronicle/evidence mirror receipt
    ui_implication: Use evidence/decision panes with canonical SRC and mirror receipt state.
more_count: 4
next_token: pm-deferred-capability-groups
```

### Implementer

```yaml
items:
  - capability: Focused handoff intake and next action
    authority: task-orchestrator workflow state plus dopetask execution handoff boundary
    ui_implication: Show active packet, blockers, next action, and execution boundary without creating task state.
  - capability: Evidence retrieval for implementation context
    authority: dope-context retrieval, Serena technical context UNKNOWN/candidate, ConPort decisions
    ui_implication: Context panes should be read-only, source-labeled, and capped to Top-3 with continuation token.
  - capability: Handback, progress, and proof logging
    authority: ConPort decision/progress canonical logs with dope-memory mirror receipts; proof artifacts remain file-based evidence
    ui_implication: Handback panel should capture evidence refs and validation status.
more_count: 4
next_token: implementer-deferred-capability-groups
```

## 5. Archive Intent Overlay

```yaml
items:
  - capability: Operator Support rail
    evidence_class: runtime + active-doc
    implementation_status: partially implemented
    source_paths:
      - services/task-orchestrator/task_orchestrator/mcp/__init__.py
      - src/dopemux/adhd/attention_monitor.py
      - src/dopemux/adhd/workflow_manager.py
    design_label: support signal, not PM/Implementer authority
  - capability: interruption recovery and unfinished-work visibility
    evidence_class: runtime + roadmap + archived-doc
    implementation_status: mixed; context preservation partially implemented, finishing helpers planned-only
    source_paths:
      - src/dopemux/adhd/context_manager.py
      - services/adhd_engine/domains/attention/context_preserver.py
      - docs/archive/history/sourceFiles/docs__04-explanation__features__adhd-finishing-helpers.md
      - docs/planes/pm/pm-friction-map.md
    design_label: valid question for PM/Implementer re-entry and handoff/handback support
  - capability: bounded next-task recommendation
    evidence_class: runtime + roadmap
    implementation_status: partially implemented
    source_paths:
      - services/task-orchestrator/task_orchestrator/mcp/__init__.py
      - src/dopemux/adhd/task_decomposer.py
      - docs/03-reference/features/f-new-9-energy-task-router.md
    design_label: advisory Top-3 only
more_count: 8
next_token: archive-intent-deferred-capabilities
```

## 6. Deferred / Excluded Archive Intent

```yaml
items:
  - daily briefing with calendar/weather
  - email-to-task automation
  - meal planning and grocery lists
  - exercise, sleep, mood, health, and personal metrics
  - social/content automation
  - finance/crypto automation
  - relationship/psychology analysis
  - broad Go/EKS/RabbitMQ automation engine
  - bridge-as-authority claims
more_count: 0
next_token: null
```

## 7. Acceptance Checks

- PM and Implementer remain authority-preserving, source-labeled, and separate.
- ADHD/operator support appears only where it reduces concrete operator friction.
- Lifestyle features are not inserted into PM or Implementer primary views.
- Planned-only capabilities are visually/design-labeled as future, speculative, or excluded.
- Claude Design output does not imply archived docs are live runtime.
- dopecon-bridge is not shown as authority.
- Any support rail is advisory and can degrade to UNKNOWN.
- Top-3 lists use `items`, `more_count`, and `next_token`.
