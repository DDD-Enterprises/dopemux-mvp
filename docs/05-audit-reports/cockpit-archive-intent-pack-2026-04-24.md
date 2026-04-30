# Cockpit Archive Intent Pack - 2026-04-24

Mode: evidence pack for GPT-5.5 Pro synthesis and Claude Design. No runtime code, UI, service, or adapter changes are requested by this artifact.

## 1. Repo Identity and Scope

- repo root observed: `/Users/hue/code/dopemux-mvp`
- repo marker observed: `.dopetaskroot`
- origin observed: `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- requested branch: `codex/cockpit-archive-intent-pack`
- actual branch during inspection: `codex/rte-wizard-prescan-telemetry`
- branch creation result: failed because the sandbox could not create `.git/refs/heads/codex/cockpit-archive-intent-pack.lock`
- pre-existing drift: unrelated runtime/test/generated changes were already present before this packet

This pack treats archived docs as design input only. Runtime truth remains code, schemas, tests, configs, and current repo-truth docs.

## 2. Authority Boundaries Preserved

The cockpit design must preserve these current boundaries:

| Boundary | Current authority treatment | Evidence |
| --- | --- | --- |
| Dopemux control surface | operator CLI/control plane | `docs/03-reference/truth/truth-systems.md`; `src/dopemux/cli.py` |
| task-orchestrator | workflow coordination and PM workflow authority candidate | `docs/03-reference/truth/truth-systems.md`; `services/task-orchestrator/app/main.py`; `services/task-orchestrator/task_orchestrator/mcp/__init__.py` |
| ConPort | structured decisions/progress/context | `docs/03-reference/truth/truth-systems.md`; `src/conport/memory_server.py` |
| dope-memory | durable chronicle/evidence sink, not PM status authority | `docs/03-reference/truth/truth-systems.md`; `services/working-memory-assistant/dope_memory_main.py` |
| dope-context | deterministic code/docs retrieval | `docs/03-reference/truth/truth-systems.md`; `services/dope-context/src/mcp/server.py` |
| dopecon-bridge | adapter/proxy only, not PM/workflow/decision authority | `docs/03-reference/truth/truth-systems.md`; `docs/03-reference/truth/truth-gaps.md`; `services/dopecon-bridge/dopecon_bridge/routes.py` |

## 3. Source Search Scope

Commands run or evidence files produced:

- `git rev-parse --show-toplevel`
- `test -f .dopetaskroot`
- `git remote -v`
- `git branch --show-current`
- `git status --short --branch`
- `find . -type f (name filters for adhd/lifestyle/wellness/habit/energy/focus/context/operator/roadmap/archive/planned)`
- `find docs archive archives archived old tmp task-packets -type f 2>/dev/null | sort | tee /tmp/cockpit-archive-docs.txt`
- `rg -n -i "adhd|lifestyle|wellness|habit|routine|energy|focus|attention|break|recovery|calendar|schedule|notification|reminder|context|operator support|cognitive|executive|dopamine|health|sleep|exercise|meal|mood|personal|planner|ritual|aftercare" docs archive archives archived old tmp task-packets services src 2>/dev/null | tee /tmp/cockpit-adhd-lifestyle-rg.txt`
- `rg -n -i "adhd|energy|attention|break|focus|context|unfinished|progress|activity|cognitive|recommendation|schedule|calendar|notification|reminder" services src tests docs/05-audit-reports 2>/dev/null`

Important source paths inspected:

- `docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md`
- `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md`
- `docs/05-audit-reports/cockpit-pm-implementer-design-brief-2026-04-24.md`
- `docs/03-reference/truth/truth-systems.md`
- `docs/03-reference/truth/truth-gaps.md`
- `docs/03-reference/planes/pm/pm-plane.md`
- `docs/systems/adhd-features/readme-2.md`
- `docs/systems/task-orchestrator-analysis.md`
- `docs/planes/pm/pm-friction-map.md`
- `docs/planes/pm/dopemux-public-release-master-plan.md`
- `docs/03-reference/features/f-new-9-energy-task-router.md`
- `services/task-orchestrator/task_orchestrator/mcp/__init__.py`
- `src/dopemux/adhd/context_manager.py`
- `src/dopemux/adhd/attention_monitor.py`
- `src/dopemux/adhd/task_decomposer.py`
- `src/dopemux/adhd/workflow_manager.py`
- `services/adhd_engine/ml/energy_predictor.py`
- `services/adhd_engine/domains/attention/context_preserver.py`
- `services/adhd_engine/domains/attention/overwhelm_detector.py`
- `services/adhd_engine/domains/attention/hyperfocus_guard.py`
- `services/adhd_engine/domains/attention/procrastination_detector.py`
- `services/adhd-notifier/mobile_push.py`
- `services/adhd-notifier/daily_reporter.py`
- `services/adhd-dashboard/README.md`
- `docs/archive/history/sourceFiles/docs__ADHD_FEATURES.md`
- `docs/archive/history/sourceFiles/docs__04-explanation__features__adhd-finishing-helpers.md`
- `docs/archive/history/sourceFiles/docs__04-explanation__features__adhd-optimizations.md`
- `docs/archive/history/sourceFiles/output__individual_files__DOPEMUX_LIFE_AUTOMATION_FEATURES_docs.md`
- `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md`

## 4. Extracted Intent Layer

### Runtime-backed or partially backed operator support

These features have inspected runtime code or tool declarations, but this pack does not prove live service deployment or cockpit integration:

- Context preservation and restoration.
- Attention state tracking.
- ADHD-friendly task decomposition and batching.
- Energy-aware task recommendation.
- Break recording and recommendation.
- Overwhelm detection.
- Hyperfocus protection.
- Energy pattern prediction.
- Mobile push notification adapters.
- Daily ADHD reporting.
- Procrastination detection and micro-task intervention.

Design implication: these may inform an Operator Support rail only when source-labeled and bounded. They do not become PM status, workflow state, implementation success, or bridge authority.

### Archive/roadmap intent with high cockpit relevance

- Finishing helpers and unfinished-work visibility.
- Completion detection and closeout support.
- Interruption recovery after task ID/context loss.
- Focus-safe output shaping.

Design implication: useful as questions for GPT-5.5 Pro and Claude Design, not as implemented capability. The strongest cockpit relevance is unfinished-work visibility because it directly supports PM triage and Implementer re-entry.

### Lifestyle/personal automation intent

- Daily briefing with calendar, tasks, and weather.
- Email-to-task triage.
- Meal planning and grocery list generation.
- Personal calendar routines, exercise nudges, travel planning.
- Personal metrics for sleep, mood, health, and productivity adaptation.
- Social/content automation.
- Finance/crypto assistant.
- Relationship/psychology analysis.

Design implication: excluded from PM/Implementer cockpit. These are not current PM/Implementer operator workflows and require product, privacy, security, integration, and authority decisions.

## 5. Top-3 Operator Support Recommendations

```yaml
items:
  - capability: Source-labeled Operator Support rail
    evidence_class: runtime + active-doc
    implementation_status: partially implemented
    authority: task-orchestrator/ADHD surfaces as support signals only
    sources:
      - services/task-orchestrator/task_orchestrator/mcp/__init__.py
      - src/dopemux/adhd/attention_monitor.py
      - src/dopemux/adhd/workflow_manager.py
    cockpit_integration: shared support rail, not PM or Implementer primary pane
    design_rule: show energy/attention/break/overwhelm as SRC-labeled cues; do not make them status chips or gates
  - capability: Interruption recovery and unfinished-work visibility
    evidence_class: runtime + roadmap + archived-doc
    implementation_status: planned-only for finishing helpers; partially implemented for context preservation
    authority: task-orchestrator state, ConPort decisions, dope-context retrieval, proof/task-packet files
    sources:
      - src/dopemux/adhd/context_manager.py
      - services/adhd_engine/domains/attention/context_preserver.py
      - docs/archive/history/sourceFiles/docs__04-explanation__features__adhd-finishing-helpers.md
      - docs/planes/pm/pm-friction-map.md
    cockpit_integration: PM triage cue and Implementer re-entry cue
    design_rule: expose "unfinished/needs recovery" only when tied to concrete task/workflow/evidence source
  - capability: Bounded next-task recommendation
    evidence_class: runtime + roadmap
    implementation_status: partially implemented
    authority: task-orchestrator recommendation tool when available; otherwise UNKNOWN/degraded
    sources:
      - services/task-orchestrator/task_orchestrator/mcp/__init__.py
      - src/dopemux/adhd/task_decomposer.py
      - docs/03-reference/features/f-new-9-energy-task-router.md
    cockpit_integration: Implementer support panel capped at Top-3
    design_rule: recommendations are advisory and must never override PM workflow authority
more_count: 8
next_token: cockpit-operator-support-deferred-list
```

## 6. Deferred Capability List

```yaml
items:
  - mobile notifications and external alert channels
  - ADHD dashboard as a separate dashboard mode
  - weekly reports and historical pattern analytics
  - completion rewards and celebration loops
  - end-of-day wind-down ritual
  - personal calendar/routine/health/lifestyle automations
  - social/content automation
  - finance/crypto automation
  - relationship/psychology analysis
  - broad Go/EKS/RabbitMQ automation engine
  - bridge-authority claims from archived dopeconbridge docs
more_count: 0
next_token: null
```

## 7. PM/Implementer Design Decision

### PM mode

- Primary: PM triage, workflow adjudication, decisions/progress, authority split.
- Support-only: unfinished-work cue, source-labeled risk/recovery cue, Top-3 task selection context when it helps planning.
- Excluded: lifestyle, health, personal calendar, reward loops, mobile notifications.

### Implementer mode

- Primary: active packet, blockers, next action, evidence retrieval, handback/proof.
- Support-only: current energy/attention/break cue if it changes next-action choice, interruption recovery cue, Top-3 advisory next steps.
- Excluded: broad personal automation, psychological analysis, trading, social/media automation.

### Separate Operator Support mode

Candidate for future synthesis, not requested implementation:

- ADHD dashboard/reporting.
- hyperfocus/overwhelm session support.
- wind-down and daily/weekly reports.
- personal/lifestyle automation if product scope later approves it.

## 8. GPT-5.5 Pro Synthesis Question

Given the current PM/Implementer evidence pack and this archived intent layer, decide whether ADHD/operator-support intent should affect:

1. PM/Implementer layout directly.
2. A narrow shared support rail.
3. A separate Operator Support mode.
4. Deferred future product research only.

Constraints:

- Do not treat archived docs as runtime truth.
- Do not add new backend contracts.
- Do not design planned-only features as implemented.
- Preserve source labels and authority labels.
- Keep PM and Implementer authority separate from cognitive support signals.

## 9. Acceptance Checks

- Every planned feature in this extracted scope is classified in `docs/05-audit-reports/cockpit-adhd-lifestyle-feature-map-2026-04-24.md`.
- Every feature row includes source path evidence.
- Runtime-backed features are separated from archive-only intent.
- ADHD/lifestyle features are not forced into PM/Implementer primary views.
- Top-3 recommendations use `items`, `more_count`, and `next_token`.
- dopecon-bridge remains adapter-only.
- Remaining UNKNOWNs remain explicit.
