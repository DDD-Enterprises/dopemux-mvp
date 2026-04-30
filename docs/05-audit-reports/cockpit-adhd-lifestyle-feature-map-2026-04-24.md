# Cockpit ADHD/Lifestyle Feature Map - 2026-04-24

Mode: design-input extraction only. This file does not promote archived docs to runtime truth and does not request implementation.

## Evidence Classes

- `runtime`: directly observed in current code, tests, or service declarations.
- `active-doc`: current non-archive documentation; secondary to runtime.
- `archived-doc`: archived, historical, deprecated, or recovered documentation.
- `roadmap`: active or archived plan/roadmap content, not proof of runtime behavior.
- `speculative`: product idea without inspected runtime backing.
- `duplicate`: repeated or overlapping claim.
- `deprecated`: source path or claim is marked deprecated or superseded.
- `UNKNOWN`: source or canonicality could not be established from inspected evidence.

## Implementation Status Classes

- `implemented`: runtime behavior is directly established for the scoped feature.
- `partially implemented`: code or callable surface exists, but full runtime integration, cockpit integration, or live service behavior was not proven.
- `planned-only`: feature appears only in plans, docs, or archives.
- `deprecated`: feature/source is marked deprecated or superseded.
- `conflicting`: claim conflicts with current authority boundaries or repo-truth docs.
- `UNKNOWN`: insufficient inspected evidence.

## Feature Map

| ID | Candidate feature | Evidence class | Implementation status | Source path evidence | Cockpit design treatment |
| --- | --- | --- | --- | --- | --- |
| F01 | Context preservation and resume support | runtime + archived-doc | partially implemented | `src/dopemux/adhd/context_manager.py`; `services/adhd_engine/domains/attention/context_preserver.py`; `docs/archive/history/sourceFiles/docs__ADHD_FEATURES.md` | Shared support rail / Implementer support. Show only as source-labeled recovery cue tied to active work, decisions, and evidence refs. |
| F02 | Attention monitoring and state classification | runtime + archived-doc | partially implemented | `src/dopemux/adhd/attention_monitor.py`; `tests/test_attention_monitor.py`; `docs/archive/history/sourceFiles/docs__ADHD_FEATURES.md` | Ambient cue only. Do not convert attention state into PM authority or workflow status. |
| F03 | Task decomposition and 25-minute batching | runtime + active-doc | partially implemented | `src/dopemux/adhd/task_decomposer.py`; `services/task-orchestrator/task_orchestrator/mcp/__init__.py`; `docs/systems/task-orchestrator-analysis.md` | Implementer support when it helps next-action focus. Keep PM workflow authority separate. |
| F04 | Energy-aware task recommendations | runtime + roadmap | partially implemented | `services/task-orchestrator/task_orchestrator/mcp/__init__.py`; `src/dopemux/adhd/task_decomposer.py`; `docs/03-reference/features/f-new-9-energy-task-router.md` | Top-3 recommendation panel only. Mark degraded/UNKNOWN if state source is unavailable. |
| F05 | Break recording and break recommendations | runtime + active-doc | partially implemented | `services/task-orchestrator/task_orchestrator/mcp/__init__.py`; `src/dopemux/adhd/workflow_manager.py`; `services/adhd-dashboard/README.md` | Support rail indicator. Avoid interruptive PM/Implementer blocking unless workflow explicitly depends on a break. |
| F06 | Overwhelm circuit breaker | runtime + active-doc | partially implemented | `services/adhd_engine/domains/attention/overwhelm_detector.py`; `docs/systems/adhd-features/readme-2.md` | Separate Operator Support concern. PM/Implementer may show a quiet warning only when it changes immediate operator workflow. |
| F07 | Hyperfocus protection | runtime + active-doc | partially implemented | `services/adhd_engine/domains/attention/hyperfocus_guard.py`; `docs/systems/adhd-features/readme-2.md`; `src/dopemux/adhd/attention_monitor.py` | Ambient support only. Do not make hyperfocus state a PM status or implementation gate. |
| F08 | ML energy pattern learning | runtime + active-doc | partially implemented | `services/adhd_engine/ml/energy_predictor.py`; `services/adhd_engine/tests/test_energy_predictor.py`; `docs/systems/adhd-features/readme-2.md` | Deferred for PM/Implementer layout. May inform future support rail if product decides freshness and privacy rules. |
| F09 | Mobile push notifications for breaks/focus/energy | runtime + active-doc | partially implemented | `services/adhd-notifier/mobile_push.py`; `services/adhd_notifier/mobile_push.py`; `docs/systems/adhd-features/readme-2.md` | Exclude from first cockpit. Notification channel is outside terminal PM/Implementer surface. |
| F10 | Daily ADHD report / pattern summaries | runtime + active-doc | partially implemented | `services/adhd-notifier/daily_reporter.py`; `docs/systems/adhd-features/readme-2.md` | Deferred. Could become separate Operator Support mode or report view, not PM/Implementer primary content. |
| F11 | Procrastination detection and micro-task intervention | runtime + active-doc | partially implemented | `services/adhd_engine/domains/attention/procrastination_detector.py`; `docs/systems/adhd-features/readme-2.md` | Defer from PM/Implementer primary panes. If surfaced, use gentle support text and source labels. |
| F12 | Finishing helpers / almost-done work visibility | archived-doc + roadmap | planned-only | `docs/archive/history/sourceFiles/docs__04-explanation__features__adhd-finishing-helpers.md`; `docs/planes/pm/dopemux-public-release-master-plan.md`; `docs/planes/pm/pm-friction-map.md` | High-value design input. Use only as a question for GPT-5.5 Pro: should unfinished work visibility become support rail or PM triage cue? |
| F13 | Completion detection engine and reward/celebration system | archived-doc | planned-only | `docs/archive/history/sourceFiles/docs__04-explanation__features__adhd-finishing-helpers.md` | Deferred. Do not design reward loops as implemented cockpit features. |
| F14 | End-of-day wind-down ritual | active-doc | planned-only | `docs/systems/adhd-features/readme-2.md` | Separate Operator Support mode candidate. Do not place in PM/Implementer unless tied to handback/closure workflow. |
| F15 | Weekly pattern report | active-doc | planned-only | `docs/systems/adhd-features/readme-2.md` | Deferred report capability. Not a PM/Implementer cockpit primary pane. |
| F16 | Daily briefing with calendar, priority tasks, and weather | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/output__individual_files__DOPEMUX_LIFE_AUTOMATION_FEATURES_docs.md` | Excluded from PM/Implementer. Could be future separate personal operator mode after product authority decision. |
| F17 | Smart email-to-task triage | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/output__individual_files__DOPEMUX_LIFE_AUTOMATION_FEATURES_docs.md`; `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md` | Excluded from first cockpit. Would require privacy, integration, and PM authority decisions. |
| F18 | Meal planning and grocery automation | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/output__individual_files__DOPEMUX_LIFE_AUTOMATION_FEATURES_docs.md` | Excluded from PM/Implementer; no concrete operator workflow for development cockpit. |
| F19 | Personal calendar routines, exercise nudges, travel planning | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md` | Excluded from PM/Implementer; future lifestyle mode only if product scope expands. |
| F20 | Personal metrics: sleep, mood, health, productivity adaptation | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md` | Excluded from first cockpit. Requires privacy and evidence-source product decisions. |
| F21 | Social media/content automation and trend response | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md` | Excluded. Not a PM/Implementer workflow. |
| F22 | Finance/crypto trading assistant | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md` | Excluded. High-risk domain and no inspected runtime authority. |
| F23 | Relationship/psychology analysis agent | archived-doc + speculative | planned-only | `docs/archive/history/sourceFiles/docs__HISTORICAL__preliminary-docs-normalized__research__architecture__life-automation-adhd-support.md` | Excluded. Sensitive personal-data domain outside PM/Implementer cockpit authority. |
| F24 | Broad Go/EKS/RabbitMQ automation engine | archived-doc + speculative | conflicting | `docs/archive/history/sourceFiles/output__individual_files__DOPEMUX_LIFE_AUTOMATION_FEATURES_docs.md`; current repo Python/service stack in `pyproject.toml`, `services/`, `src/dopemux/` | Do not use for cockpit design. It conflicts with current repo stack and authority surfaces. |
| F25 | Bridge as broad cognitive/PM authority | archived-doc + duplicate | conflicting | `docs/archive/completed-projects/dopeconbridge/dopeconbridge-final-summary.md`; current boundary in `docs/03-reference/truth/truth-systems.md`; `docs/03-reference/truth/truth-gaps.md` | Must be rejected. Current cockpit design must keep dopecon-bridge adapter-only. |
| F26 | ADHD dashboard as primary cockpit | active-doc + runtime | UNKNOWN | `services/adhd-dashboard/README.md`; `services/adhd-dashboard/backend.py` | Deferred. The service exists as a cognitive-plane dashboard, but this packet did not validate live deployment or make it PM/Implementer authority. |

## Status Summary

```yaml
items:
  - status: partially implemented
    count: 11
    meaning: runtime surfaces exist, but cockpit integration or live runtime behavior was not proven
  - status: planned-only
    count: 12
    meaning: feature appears in active docs, roadmaps, archives, or speculative research only
  - status: conflicting
    count: 2
    meaning: claim conflicts with current repo authority or stack evidence
  - status: UNKNOWN
    count: 1
    meaning: source exists but runtime/cockpit authority remains unresolved
more_count: 0
next_token: null
```

## Design Guardrail

The safe design input is not "add ADHD/lifestyle features to PM and Implementer." The safe design input is: "preserve PM/Implementer authority boundaries, then evaluate whether a small Operator Support rail should expose source-labeled energy, attention, break, unfinished-work, and context-recovery cues without becoming a new authority plane."
