#!/usr/bin/env python3
"""Render and submit PM-plane Jules task packets safely.

This script encodes the PM-plane Jules packet set so operators can:
- inspect packet groups and dependencies
- render packet prompts deterministically
- dry-run the next submission wave
- submit selected packets to Jules once the merge-wave precondition is satisfied

The script fails closed for real submissions unless the operator explicitly
acknowledges that the post-merge-wave precondition is satisfied.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


DEFAULT_REPO = "DDD-Enterprises/dopemux-mvp"
DEFAULT_JULES_BIN = "jules"
SESSION_LIMIT = 5
COMMON_INVARIANTS = (
    "Do not redesign the PM-plane authority model. Implement the documented target only.",
    "Touch only owned paths and directly adjacent tests/docs for those paths. If additional subsystem files are required, stop and report.",
    "Preserve fail-closed behavior and explicit provenance. Do not introduce silent fallbacks or shadow authority.",
)

COMMON_STOP_CONDITIONS = (
    "Required file or runtime surface is missing from the owned paths.",
    "Completing the packet requires non-owned subsystem edits beyond directly adjacent tests/docs.",
    "Tests fail outside packet scope and the failure appears unrelated to the owned change.",
)


DOCS_COMMANDS = (
    "git status --short",
    "rg -n \"Leantime|Task Orchestrator|ConPort|dope-memory|dopecon-bridge|workflow authority|canonical\" docs/planes/pm docs/90-adr docs/03-reference/services -S",
    "python3 scripts/docs_validator.py",
    "python3 scripts/docs_frontmatter_guard.py",
    "python3 scripts/check_root_hygiene.py",
)

TO_COMMANDS = (
    "git status --short",
    "rg -n \"workflow|transition|role|blocker|next\" services/task-orchestrator -S",
    "python3 -m compileall -q services/task-orchestrator",
    "python3 -m pytest -q services/task-orchestrator/tests",
)

BRIDGE_COMMANDS = (
    "git status --short",
    "rg -n \"task|ddg|route_pm|next action|progress|decision\" services/dopecon-bridge -S",
    "python3 -m compileall -q services/dopecon-bridge",
    "python3 -m pytest -q services/dopecon-bridge/tests",
)

TASKMASTER_COMMANDS = (
    "git status --short",
    "rg -n \"taskmaster|route_pm|status|progress|task_id\" services/taskmaster src/dopemux/pm -S",
    "python3 -m compileall -q services/taskmaster src/dopemux",
    "python3 -m pytest -q services/taskmaster tests",
)

CLI_COMMANDS = (
    "git status --short",
    "rg -n \"TaskRecord|tasks.json|task_decomposer|pm_\" src/dopemux -S",
    "python3 -m compileall -q src/dopemux",
    "python3 -m pytest -q tests",
)

PM_SHARED_COMMANDS = (
    "git status --short",
    "rg -n \"TaskStatus|TaskRecord|pm_|canonical|idempotency|workflow_state\" src/dopemux services/task-orchestrator services/taskmaster services/dopecon-bridge -S",
    "python3 -m compileall -q src/dopemux services/task-orchestrator services/taskmaster services/dopecon-bridge",
    "python3 -m pytest -q tests services/task-orchestrator/tests services/dopecon-bridge/tests",
)

INTEGRATION_COMMANDS = (
    "git status --short",
    "rg -n \"pm_get_|pm_transition_|pm_log_progress|reconciliation|chronicle|decision context\" src services docs -S",
    "python3 -m compileall -q src/dopemux services/task-orchestrator services/dopecon-bridge services/taskmaster",
    "python3 -m pytest -q tests services/task-orchestrator/tests services/dopecon-bridge/tests",
)


@dataclass(frozen=True)
class Packet:
    id: str
    title: str
    group: str
    submit_after: tuple[str, ...]
    objective: str
    scope_in: tuple[str, ...]
    scope_out: tuple[str, ...]
    owned_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    steps: tuple[str, ...]
    acceptance: tuple[str, ...]
    commands: tuple[str, ...]


PACKETS: tuple[Packet, ...] = (
    Packet(
        id="PM-INT-00",
        title="post-merge PM-plane implementation ledger",
        group="wave0",
        submit_after=(),
        objective="Re-baseline main after the PR merge wave and produce one evidence-backed PM-plane implementation ledger.",
        scope_in=(
            "Audit normalized PM-plane tools and mark each as implemented, partial, or missing.",
            "Identify active Task Orchestrator runtime variants, workflow bypass paths, bridge shadow-authority paths, taskmaster traceability gaps, and CLI orphan-state gaps.",
            "Publish one authoritative post-merge implementation ledger for downstream packets.",
        ),
        scope_out=(
            "Service code changes outside directly related docs or inventory artifacts.",
            "Architecture redesign.",
        ),
        owned_paths=("docs/planes/pm/", "docs/90-adr/"),
        forbidden_paths=(
            "services/task-orchestrator/",
            "services/dopecon-bridge/",
            "services/taskmaster/",
            "src/dopemux/",
        ),
        steps=(
            "Audit the documented PM-plane target against current runtime truth on main.",
            "Mark each normalized PM-plane tool as implemented, partial, or missing.",
            "Record the active Task Orchestrator runtime and any competing variants.",
            "Record workflow bypass paths, bridge shadow-authority paths, taskmaster traceability gaps, and CLI orphan-state gaps.",
            "Publish a single implementation ledger that downstream packets can cite.",
        ),
        acceptance=(
            "One implementation ledger replaces the older Phase 0 gap view.",
            "Every downstream packet can cite the ledger instead of rediscovering current state.",
            "No claim is made without file-path evidence.",
        ),
        commands=DOCS_COMMANDS,
    ),
    Packet(
        id="PM-INT-01",
        title="freeze PM-plane contract docs",
        group="wave0",
        submit_after=("PM-INT-00",),
        objective="Freeze one canonical PM-plane implementation contract across active docs and ADRs.",
        scope_in=(
            "Normalize PM-plane docs to one authority wording.",
            "Remove or deprecate stale claims that Leantime is workflow authority.",
            "Remove or deprecate stale claims that dopecon-bridge local state is canonical.",
            "Add one explicit current-runtime-gaps section downstream packets must honor.",
        ),
        scope_out=(
            "Runtime service code changes.",
            "New architecture decisions.",
        ),
        owned_paths=("docs/planes/pm/", "docs/90-adr/", "docs/03-reference/services/"),
        forbidden_paths=("services/", "src/"),
        steps=(
            "Promote one canonical authority summary from the existing ADR/doc set.",
            "Normalize active PM-plane docs to the same authority wording.",
            "Remove or deprecate stale claims about Leantime workflow authority and bridge-local canonical state.",
            "Add one explicit current-runtime-gaps section and update indexes/cross-links.",
        ),
        acceptance=(
            "One active PM-plane contract exists without contradictory authority claims.",
            "Docs name the same forbidden direct paths everywhere.",
            "Downstream packets can cite one contract source.",
        ),
        commands=DOCS_COMMANDS,
    ),
    Packet(
        id="PM-INT-10",
        title="lock Task Orchestrator runtime for PM plane",
        group="wave1-core",
        submit_after=("PM-INT-00",),
        objective="Select and enforce the one Task Orchestrator runtime path the PM plane may use.",
        scope_in=(
            "Pick the one supported Task Orchestrator runtime path based on the implementation ledger.",
            "Remove PM-plane routing to unsupported runtime variants or hard-fail those paths.",
            "Normalize readiness and port behavior for the chosen runtime.",
            "Update tool and API exposure to reference the chosen runtime only.",
        ),
        scope_out=(
            "Workflow API expansion.",
            "Bridge, taskmaster, or CLI edits.",
        ),
        owned_paths=("services/task-orchestrator/",),
        forbidden_paths=("services/dopecon-bridge/", "services/taskmaster/", "src/dopemux/"),
        steps=(
            "Select the canonical Task Orchestrator runtime for PM-plane use.",
            "Remove or block routing to unsupported runtime variants.",
            "Normalize readiness and port behavior for the chosen runtime.",
            "Update tool/API exposure and docs to reference the chosen runtime only.",
            "Add tests for readiness, port defaults, overrides, and rejection of non-canonical runtime paths.",
        ),
        acceptance=(
            "PM-plane integrations can target only one Task Orchestrator runtime.",
            "Readiness and port behavior are deterministic.",
            "Docs and tests match runtime truth.",
        ),
        commands=TO_COMMANDS,
    ),
    Packet(
        id="PM-INT-11",
        title="remove Task Orchestrator workflow bypasses",
        group="wave1-followup",
        submit_after=("PM-INT-10",),
        objective="Remove or block direct workflow-significant mutation outside sanctioned Task Orchestrator transition paths.",
        scope_in=(
            "Identify direct role or state mutation paths in the chosen runtime.",
            "Block or remove workflow-significant mutation that bypasses sanctioned transition APIs.",
            "Ensure legal transitions flow through one sanctioned transition path.",
            "Make transition audit persistence required for success.",
        ),
        scope_out=(
            "PM-plane read/write facade code.",
            "Bridge, Leantime integration, ConPort, or dope-memory adapter work.",
        ),
        owned_paths=("services/task-orchestrator/",),
        forbidden_paths=("services/dopecon-bridge/", "services/taskmaster/", "src/dopemux/"),
        steps=(
            "Identify all direct workflow-significant state mutation paths in the selected runtime.",
            "Remove or block raw workflow-significant mutation outside sanctioned transition APIs.",
            "Ensure transition audit persistence is part of the success contract.",
            "Add positive transition tests, bypass rejection tests, and audit-failure tests.",
        ),
        acceptance=(
            "Task Orchestrator cannot split against itself for PM-plane callers.",
            "Direct workflow bypasses are removed or blocked.",
            "Audit persistence is required for success.",
        ),
        commands=TO_COMMANDS,
    ),
    Packet(
        id="PM-INT-12",
        title="add project-scoped workflow APIs to Task Orchestrator",
        group="wave1-followup",
        submit_after=("PM-INT-11",),
        objective="Add the project-scoped Task Orchestrator workflow surfaces required by the normalized PM-plane contract.",
        scope_in=(
            "Add project-scoped workflow read surfaces for priority queue, blockers, and workflow state.",
            "Add a project-scoped transition surface.",
            "Return a canonical workflow result envelope with workflow IDs, linked PM IDs where available, legality result, blocker data, and next-action data where relevant.",
            "Fail closed if required workflow data is unavailable.",
        ),
        scope_out=(
            "Bridge adapter implementation.",
            "Taskmaster and CLI migration.",
        ),
        owned_paths=("services/task-orchestrator/",),
        forbidden_paths=("services/dopecon-bridge/", "services/taskmaster/", "src/dopemux/"),
        steps=(
            "Implement project-scoped workflow read surfaces for queue, blockers, and workflow state.",
            "Implement the project-scoped transition request surface.",
            "Add the canonical workflow result envelope with provenance-ready fields.",
            "Update manifests and docs.",
            "Add API/tool contract tests and fail-closed tests.",
        ),
        acceptance=(
            "PM-plane workflow tools have real Task Orchestrator backends.",
            "Task Orchestrator exposes the workflow surfaces the PM plane expects.",
            "API/tool contracts and manifests are validated.",
        ),
        commands=TO_COMMANDS,
    ),
    Packet(
        id="PM-INT-13",
        title="implement canonical task object and status normalization",
        group="wave1-core",
        submit_after=("PM-INT-00",),
        objective="Implement the PM-plane canonical task object and lifecycle boundary described by ADR-PM-001.",
        scope_in=(
            "Add one canonical status enum: TODO, IN_PROGRESS, BLOCKED, DONE, CANCELED.",
            "Add one status mapping layer for Task Orchestrator, taskmaster, CLI, and bridge dialects.",
            "Add stable linked-ID behavior across systems.",
            "Add idempotency-key and monotonic version invariants for lifecycle writes.",
        ),
        scope_out=(
            "Bridge-local endpoint behavior.",
            "Broad Task Orchestrator API edits.",
            "Leantime sync behavior.",
        ),
        owned_paths=("src/dopemux/pm/", "src/dopemux/adhd/", "services/task-orchestrator/", "services/taskmaster/", "services/dopecon-bridge/"),
        forbidden_paths=("services/working-memory-assistant/",),
        steps=(
            "Add the canonical task object at the PM-plane boundary.",
            "Add the one allowed status mapping table across producer dialects.",
            "Add linked-ID/reference fields, version, and idempotency invariants.",
            "Refuse unmappable or stale writes.",
            "Add round-trip mapping tests and update lifecycle docs.",
        ),
        acceptance=(
            "Downstream packets can import one canonical lifecycle contract.",
            "All producer dialects map into the canonical task object.",
            "Stale or invalid writes are rejected.",
        ),
        commands=PM_SHARED_COMMANDS,
    ),
    Packet(
        id="PM-INT-14",
        title="harden Leantime reflection and reconciliation",
        group="wave1-followup",
        submit_after=("PM-INT-12", "PM-INT-13"),
        objective="Make Leantime reflection and reconciliation explicit so Leantime remains PM record authority but never workflow law.",
        scope_in=(
            "Separate direct PM metadata writes from workflow-significant writes.",
            "Route workflow-significant writes to Task Orchestrator adjudication first.",
            "Reflect accepted workflow outcomes into Leantime with provenance metadata.",
            "Treat direct Leantime workflow drift as reconciliation-only.",
        ),
        scope_out=(
            "Task Orchestrator core workflow logic.",
            "ConPort or dope-memory ownership rules.",
            "Taskmaster or CLI migration.",
        ),
        owned_paths=("services/task-orchestrator/", "src/dopemux/", "docs/planes/pm/"),
        forbidden_paths=("services/dopecon-bridge/", "services/taskmaster/"),
        steps=(
            "Separate direct PM metadata writes from workflow-significant writes in Leantime-facing integration paths.",
            "Add explicit reflection, mirror receipt, and reconciliation state handling.",
            "Define degraded mirror behavior and conflict handling.",
            "Add tests for reflection success, reflection failure, and direct-drift detection.",
        ),
        acceptance=(
            "Leantime mirrors workflow outcomes but does not self-authorize workflow legality.",
            "Leantime remains canonical PM record for PM metadata only.",
            "Reflection, conflict, and degraded mirror behaviors are tested.",
        ),
        commands=INTEGRATION_COMMANDS,
    ),
    Packet(
        id="PM-INT-15",
        title="make ConPort the live PM-plane context backend",
        group="wave1-core",
        submit_after=("PM-INT-13",),
        objective="Make ConPort the concrete PM-plane backend for decisions, progress, and durable context.",
        scope_in=(
            "Choose one preferred callable surface for PM-plane ConPort operations.",
            "Normalize decision, progress, and context payloads behind that adapter.",
            "Ensure PM-plane writes for these object classes resolve to ConPort.",
            "Add canonical receipt shapes for decision and progress writes.",
        ),
        scope_out=(
            "dope-memory code.",
            "Task Orchestrator workflow code.",
            "Bridge-local DDG state beyond adapter-routing changes required here.",
        ),
        owned_paths=("services/shared/conport_client/", "services/task-orchestrator/", "services/dopecon-bridge/", "src/dopemux/"),
        forbidden_paths=("services/working-memory-assistant/",),
        steps=(
            "Choose the preferred callable surface for PM-plane ConPort operations.",
            "Normalize decision, progress, and context payloads behind that adapter.",
            "Add canonical receipt and read-back shapes.",
            "Add degraded-mode behavior when ConPort is unavailable.",
            "Add contract and failure tests.",
        ),
        acceptance=(
            "Decisions, progress, and context writes resolve to ConPort and nowhere else.",
            "ConPort is the live backend for PM-plane context lanes.",
            "Contract and backend-unavailable behavior are tested.",
        ),
        commands=PM_SHARED_COMMANDS,
    ),
    Packet(
        id="PM-INT-16",
        title="implement dope-memory chronicle lane",
        group="wave1-core",
        submit_after=("PM-INT-13",),
        objective="Implement dope-memory as the PM-plane chronicle backend.",
        scope_in=(
            "Add PM-plane chronicle read integration.",
            "Add append/correct chronicle write integration.",
            "Link chronicle records to canonical work, workflow, and decision references.",
            "Preserve chronicle provenance and source-plane identity.",
        ),
        scope_out=(
            "Decision/progress ownership code.",
            "Task Orchestrator workflow code.",
            "Bridge endpoint behavior except adapter calls.",
        ),
        owned_paths=("services/working-memory-assistant/", "src/dopemux/", "docs/planes/pm/"),
        forbidden_paths=("services/dopecon-bridge/", "services/taskmaster/"),
        steps=(
            "Add PM-plane chronicle read integration.",
            "Add append/correct chronicle write integration.",
            "Link chronicle records to canonical work, workflow, and decision references.",
            "Add read/write tests and failure tests for missing provenance or broken links.",
        ),
        acceptance=(
            "pm_get_work_chronicle and chronicle-linked write flows resolve to dope-memory.",
            "Chronicle provenance is preserved.",
            "Broken-link and missing-provenance cases are tested.",
        ),
        commands=INTEGRATION_COMMANDS,
    ),
    Packet(
        id="PM-INT-20",
        title="narrow dopecon-bridge to adapter-only role",
        group="wave2-core",
        submit_after=("PM-INT-10", "PM-INT-11", "PM-INT-15", "PM-INT-16"),
        objective="Remove or de-authorize bridge-local PM/workflow/decision shadow authority so the bridge is adapter/routing only.",
        scope_in=(
            "Inventory bridge-local task, next-action, workflow, and DDG authority behavior in active runtime code.",
            "Remove, quarantine, or explicitly mark local task/DDG state as non-canonical projection/cache only.",
            "Route task/workflow/decision/progress operations to canonical backends.",
            "Add mandatory policy wrapping for side-effectful writes.",
        ),
        scope_out=(
            "Task Orchestrator runtime code.",
            "taskmaster or CLI migration.",
        ),
        owned_paths=("services/dopecon-bridge/",),
        forbidden_paths=("services/task-orchestrator/", "services/taskmaster/", "src/dopemux/"),
        steps=(
            "Inventory and remove or de-authorize bridge-local shadow authority behaviors.",
            "Route task, workflow, decision, and progress operations to canonical backends.",
            "Add mandatory policy wrapping and block ambiguous or unauthenticated side-effect paths.",
            "Update route contracts/docs and add negative authority tests.",
        ),
        acceptance=(
            "dopecon-bridge is translation/routing only for PM-plane concerns.",
            "Bridge-local shadow authority is removed or clearly non-canonical.",
            "Endpoint policy and auth behavior are tested.",
        ),
        commands=BRIDGE_COMMANDS,
    ),
    Packet(
        id="PM-INT-21",
        title="implement normalized PM-plane reads",
        group="wave2-core",
        submit_after=("PM-INT-12", "PM-INT-13", "PM-INT-15", "PM-INT-16", "PM-INT-20"),
        objective="Implement the normalized PM-plane read surfaces over canonical backends.",
        scope_in=(
            "Implement pm_get_project_context, pm_get_priority_queue, pm_get_blockers, pm_get_workflow_state, pm_get_sprint_snapshot, pm_get_decision_context, and pm_get_work_chronicle.",
            "Use exactly one canonical source per tool and annotate supporting sources as mirrored, indexed, or derived.",
            "Normalize all responses to PM-plane shapes and add provenance markers.",
        ),
        scope_out=(
            "Write-path logic beyond shared response helpers.",
        ),
        owned_paths=("src/dopemux/pm/", "services/task-orchestrator/", "services/dopecon-bridge/", "services/working-memory-assistant/"),
        forbidden_paths=("services/taskmaster/", "src/dopemux/adhd/"),
        steps=(
            "Implement normalized PM-plane read surfaces over canonical backends.",
            "Add provenance markers and canonical source annotations.",
            "Fail closed when canonical backends are unavailable.",
            "Add docs/examples and contract tests.",
        ),
        acceptance=(
            "All read tools exist behind the normalized PM-plane contract.",
            "PM-plane consumers can stop calling raw subsystem-native read surfaces.",
            "Per-tool contract, provenance, and fail-closed behavior are tested.",
        ),
        commands=INTEGRATION_COMMANDS,
    ),
    Packet(
        id="PM-INT-22",
        title="implement normalized PM-plane writes",
        group="wave2-core",
        submit_after=("PM-INT-12", "PM-INT-13", "PM-INT-14", "PM-INT-15", "PM-INT-16", "PM-INT-20"),
        objective="Implement the normalized PM-plane write surfaces with canonical receipts, mirror receipts, and reconciliation state.",
        scope_in=(
            "Implement pm_update_work_item, pm_transition_work_item, and pm_log_progress.",
            "Enforce canonical writer routing and reject workflow-significant payloads on pm_update_work_item unless separately adjudicated.",
            "Add canonical receipt shape, mirror receipt shape, idempotency handling, and partial-failure handling.",
        ),
        scope_out=(
            "Bridge-local shadow storage.",
            "Raw backend-native surface redesign outside adapter needs.",
        ),
        owned_paths=("src/dopemux/pm/", "services/task-orchestrator/", "services/dopecon-bridge/", "services/working-memory-assistant/"),
        forbidden_paths=("services/taskmaster/", "src/dopemux/adhd/"),
        steps=(
            "Implement canonical writer routing for normalized PM-plane writes.",
            "Add canonical receipt, mirror receipt, reconciliation state, and idempotency handling.",
            "Add partial-failure handling and docs/examples.",
            "Add end-to-end write tests.",
        ),
        acceptance=(
            "Normalized PM-plane writes enforce authority boundaries at runtime.",
            "PM-plane writes are live and authoritative.",
            "End-to-end, idempotency, and partial-failure behavior are tested.",
        ),
        commands=INTEGRATION_COMMANDS,
    ),
    Packet(
        id="PM-INT-23",
        title="migrate taskmaster onto canonical PM-plane contract",
        group="wave2-consumers",
        submit_after=("PM-INT-13", "PM-INT-15", "PM-INT-20", "PM-INT-21", "PM-INT-22"),
        objective="Migrate taskmaster producer behavior onto the canonical PM-plane contract and close the documented taskmaster traceability gap.",
        scope_in=(
            "Replace free-form taskmaster lifecycle/status behavior with canonical PM-plane mapping.",
            "Ensure taskmaster-created work carries stable linked IDs and provenance.",
            "Route taskmaster sync/update flows through canonical PM-plane APIs instead of shadow bridge behavior.",
            "Create a real taskmaster test suite under services/taskmaster/tests.",
        ),
        scope_out=(
            "Task Orchestrator core workflow logic.",
            "Bridge runtime beyond consuming its finalized adapter contract.",
        ),
        owned_paths=("services/taskmaster/",),
        forbidden_paths=("services/task-orchestrator/", "services/dopecon-bridge/", "src/dopemux/"),
        steps=(
            "Replace free-form taskmaster lifecycle/status behavior with canonical PM-plane mapping.",
            "Add stable linked IDs, provenance, and concrete decision/progress traceability.",
            "Route taskmaster sync/update through canonical PM-plane APIs.",
            "Create taskmaster tests for create, update, sync, traceability, and wrapper failure.",
            "Update taskmaster docs.",
        ),
        acceptance=(
            "taskmaster is a compliant PM-plane producer with tests and traceability.",
            "Taskmaster no longer emits untracked PM-state drift.",
            "Wrapper failure and sync behavior are tested.",
        ),
        commands=TASKMASTER_COMMANDS,
    ),
    Packet(
        id="PM-INT-24",
        title="migrate CLI TaskRecord flow onto canonical PM plane",
        group="wave2-consumers",
        submit_after=("PM-INT-13", "PM-INT-15", "PM-INT-21", "PM-INT-22"),
        objective="Replace CLI TaskRecord orphan-state behavior with canonical PM-plane-backed lifecycle operations.",
        scope_in=(
            "Replace filesystem-only lifecycle truth with canonical PM-plane-backed create/update flows.",
            "Keep local disk only as cache/offline queue if needed, never as canonical truth.",
            "Add importer/backfill logic for existing .dopemux/tasks/tasks.json records.",
            "Add degraded-mode behavior when canonical backends are unavailable.",
        ),
        scope_out=(
            "taskmaster behavior.",
            "bridge runtime internals.",
            "Task Orchestrator core workflow logic.",
        ),
        owned_paths=("src/dopemux/adhd/", "src/dopemux/pm/",),
        forbidden_paths=("services/taskmaster/", "services/dopecon-bridge/", "services/task-orchestrator/"),
        steps=(
            "Replace filesystem-only lifecycle truth with canonical PM-plane-backed create/update flows.",
            "Keep local disk only as cache/offline queue if needed.",
            "Add importer/backfill logic for existing local task records.",
            "Add tests for create/start/complete/update/backfill/offline replay.",
            "Update CLI docs/examples.",
        ),
        acceptance=(
            "CLI tasks are no longer orphaned from the canonical PM plane.",
            "CLI task lifecycle routes through canonical PM-plane contracts.",
            "Backfill and offline replay behavior are tested.",
        ),
        commands=CLI_COMMANDS,
    ),
    Packet(
        id="PM-INT-25",
        title="normalize PM-plane event taxonomy",
        group="wave2-events",
        submit_after=("PM-INT-13", "PM-INT-23", "PM-INT-24"),
        objective="Normalize PM event naming and payload taxonomy across Task Orchestrator, taskmaster, CLI, and bridge emissions.",
        scope_in=(
            "Define the one PM-plane event taxonomy all producers use.",
            "Normalize taskmaster, orchestrator, and CLI emissions into that taxonomy.",
            "Enforce canonical envelope shape with provenance and idempotency.",
        ),
        scope_out=(
            "Unrelated service logic.",
            "Raw workflow legality implementation.",
        ),
        owned_paths=("src/dopemux/pm/", "src/dopemux/events/", "services/taskmaster/", "services/task-orchestrator/", "services/dopecon-bridge/"),
        forbidden_paths=("services/working-memory-assistant/",),
        steps=(
            "Define the one PM-plane event taxonomy and canonical envelope.",
            "Normalize taskmaster, orchestrator, and CLI emissions into that taxonomy.",
            "Enforce provenance and idempotency rules.",
            "Add producer-to-envelope mapping tests, duplicate/idempotency tests, and update docs.",
        ),
        acceptance=(
            "All PM event producers speak one taxonomy.",
            "Cross-service PM events are deterministic and normalized.",
            "Mapping, duplicate/idempotency, and provenance behavior are tested.",
        ),
        commands=PM_SHARED_COMMANDS,
    ),
    Packet(
        id="PM-INT-30",
        title="build PM-plane end-to-end integration suite",
        group="wave3",
        submit_after=("PM-INT-14", "PM-INT-22", "PM-INT-23", "PM-INT-24", "PM-INT-25"),
        objective="Build the end-to-end suite that proves the PM-plane authority split and reconciliation behavior are real at runtime.",
        scope_in=(
            "Build a local-stack integration harness for Leantime, Task Orchestrator, ConPort, dope-memory, bridge, taskmaster, and CLI PM paths where applicable.",
            "Add happy-path tests for create/update/transition/progress/chronicle flows.",
            "Add failure tests for backend unavailable, mirror unavailable, illegal transition, duplicate retry, and reconciliation.",
            "Wire the suite into CI and publish a repro runbook.",
        ),
        scope_out=(
            "New runtime contract design.",
            "Large service refactors beyond test hooks.",
        ),
        owned_paths=("tests/", "services/task-orchestrator/tests/", "services/dopecon-bridge/tests/", "services/taskmaster/tests/", "docs/"),
        forbidden_paths=("services/task-orchestrator/app/", "services/dopecon-bridge/dopecon_bridge/"),
        steps=(
            "Build the local-stack integration harness for all relevant PM-plane components.",
            "Add happy-path and failure-path tests for canonical create/update/transition/progress/chronicle flows.",
            "Add taskmaster and CLI producer integration coverage.",
            "Wire the suite into CI and publish a repro runbook.",
        ),
        acceptance=(
            "PM-plane authority and reconciliation behavior are covered by CI.",
            "End-to-end PM-plane integration is test-gated.",
            "A local repro runbook exists.",
        ),
        commands=INTEGRATION_COMMANDS,
    ),
    Packet(
        id="PM-INT-31",
        title="add PM-plane readiness and observability",
        group="wave3",
        submit_after=("PM-INT-10", "PM-INT-14", "PM-INT-22"),
        objective="Make canonical success, mirror failure, and reconciliation state visible to operators.",
        scope_in=(
            "Standardize readiness contracts across the chosen PM-plane services.",
            "Surface canonical success vs degraded mirror success explicitly.",
            "Surface pending reconciliation explicitly.",
            "Add structured logs/metrics for canonical write, mirror write, retry, and reconciliation.",
            "Add runbooks for rogue runtime detection and cleanup.",
        ),
        scope_out=(
            "Core lifecycle contract redesign.",
        ),
        owned_paths=("services/task-orchestrator/", "services/dopecon-bridge/", "src/dopemux/", "docs/"),
        forbidden_paths=("services/taskmaster/",),
        steps=(
            "Standardize readiness contracts across the chosen PM-plane services.",
            "Surface canonical success vs degraded mirror success and pending reconciliation explicitly.",
            "Add structured logs and metrics for canonical write, mirror write, retry, and reconciliation.",
            "Add runbooks for rogue runtime detection and cleanup.",
            "Add readiness drift and warning-propagation tests, and close or supersede PM-TO-001 through PM-TO-006.",
        ),
        acceptance=(
            "Operators can tell exactly what succeeded, what mirrored, and what needs reconciliation.",
            "PM-plane operational truth is visible and auditable.",
            "Readiness, warning propagation, and operator-output behavior are tested.",
        ),
        commands=INTEGRATION_COMMANDS,
    ),
    Packet(
        id="PM-INT-32",
        title="rollout and deprecate legacy PM-plane surfaces",
        group="wave3",
        submit_after=("PM-INT-30", "PM-INT-31"),
        objective="Ship the PM plane in stages and deprecate raw/native PM-adjacent surfaces safely.",
        scope_in=(
            "Add staged rollout gates for read-only PM-plane, then metadata writes, then workflow writes.",
            "Add deprecation notices for raw backend-native PM-plane-adjacent surfaces.",
            "Add migration notes for internal callers and tools.",
            "Add rollback rules and go/no-go checklist.",
            "Add backward-compat smoke tests and final docs for supported entrypoints.",
        ),
        scope_out=(
            "New feature work outside rollout and deprecation.",
        ),
        owned_paths=("docs/", "src/dopemux/", "services/"),
        forbidden_paths=(),
        steps=(
            "Add staged rollout gates for the PM-plane read-only, metadata-write, and workflow-write phases.",
            "Add deprecation notices and migration notes for raw backend-native PM-plane-adjacent surfaces.",
            "Add rollback rules, go/no-go checklist, and backward-compat smoke tests.",
            "Publish final docs for supported PM-plane entrypoints and freeze deprecated paths after rollout proof.",
        ),
        acceptance=(
            "There is one supported PM-plane contract and a clear path off legacy raw surfaces.",
            "The PM plane has a staged rollout plan and legacy deprecation path.",
            "Feature-flag, backward-compat, and rollout-checklist behavior are tested.",
        ),
        commands=DOCS_COMMANDS + ("python3 -m pytest -q tests",),
    ),
)


PACKET_BY_ID = {packet.id: packet for packet in PACKETS}

GROUPS: dict[str, tuple[str, ...]] = {
    "wave0": ("PM-INT-00", "PM-INT-01"),
    "wave1-core": ("PM-INT-10", "PM-INT-13", "PM-INT-15", "PM-INT-16"),
    "wave1-followup": ("PM-INT-11", "PM-INT-12", "PM-INT-14"),
    "wave2-core": ("PM-INT-20", "PM-INT-21", "PM-INT-22"),
    "wave2-consumers": ("PM-INT-23", "PM-INT-24"),
    "wave2-events": ("PM-INT-25",),
    "wave3": ("PM-INT-30", "PM-INT-31", "PM-INT-32"),
}


def _bullet_block(items: Iterable[str], empty: str = "* none") -> str:
    values = [f"* {item}" for item in items]
    return "\n".join(values) if values else empty


def render_packet(packet: Packet) -> str:
    depends = ", ".join(packet.submit_after) if packet.submit_after else "none"
    plan_block = "\n".join(
        f"{idx}. {step}" for idx, step in enumerate(packet.steps, start=1)
    )
    return textwrap.dedent(
        f"""\
        # Task Packet: {packet.id} · PM Plane · {packet.title}

        ════════════════════════════════════════════════════════════

        ## Objective

        {packet.objective}

        ────────────────────────────────────────────────────────────

        ## Scope

        IN:

        {_bullet_block(packet.scope_in)}

        OUT:

        {_bullet_block(packet.scope_out)}

        ────────────────────────────────────────────────────────────

        ## Invariants (Must Remain True)

        {_bullet_block(COMMON_INVARIANTS)}

        * Submission dependency status for this packet: {depends}

        If an invariant appears impossible, stop and report.

        ────────────────────────────────────────────────────────────

        ## Plan (Numbered)

        {plan_block}

        Keep steps mechanical and verifiable.

        ────────────────────────────────────────────────────────────

        ## Files to Touch

        {_bullet_block(packet.owned_paths)}

        Forbidden direct paths:

        {_bullet_block(packet.forbidden_paths)}

        If additional files are needed outside the owned paths or directly adjacent tests/docs, stop and report.

        ────────────────────────────────────────────────────────────

        ## Exact Commands to Run

        {_bullet_block(packet.commands)}

        ────────────────────────────────────────────────────────────

        ## Output Capture Rules (Verbatim)

        Implementer must return:

        * git diff --stat
        * git diff
        * Command outputs verbatim
        * Exit codes
        * Any requested logs/artifacts

        ────────────────────────────────────────────────────────────

        ## Acceptance Criteria

        {_bullet_block(packet.acceptance)}

        ────────────────────────────────────────────────────────────

        ## Rollback Steps

        * Revert the packet branch or patch cleanly if the acceptance criteria are not met.
        * Restore the last known-good behavior for the owned paths and rerun the required validation commands.

        ────────────────────────────────────────────────────────────

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        STOP CONDITIONS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Stop immediately if:

        {_bullet_block(COMMON_STOP_CONDITIONS)}

        If stopped, return:

        * What you attempted
        * Evidence collected
        * What output is needed next

        ────────────────────────────────────────────────────────────

        ## Jules Session Metadata

        * Repo: {DEFAULT_REPO}
        * Packet ID: {packet.id}
        * Group: {packet.group}
        * Submit after: {depends}
        """
    ).strip() + "\n"


def fetch_open_pr_count(repo: str, token: str | None) -> int | None:
    url = f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "codex-pm-plane-jules-submit",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return len(__import__("json").load(response))
    except (urllib.error.URLError, TimeoutError):
        return None
DEFAULT_JULES_BIN = "jules"
SESSION_LIMIT = 5

def list_remote_sessions(jules_bin: str) -> str:
    result = subprocess.run(
        [jules_bin, "remote", "list", "--session"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise SystemExit(
            "Failed to list remote Jules sessions "
            f"(exit code {result.returncode}) for command "
            f'"{jules_bin} remote list --session".\n'
            f"Output:\n{output.strip()}"
        )
    return output


def packet_ids_in_remote_sessions(jules_bin: str) -> set[str]:
    output = list_remote_sessions(jules_bin)
    found: set[str] = set()
    for packet in PACKETS:
        if packet.id in output:
            found.add(packet.id)
    return found


def select_packets(packet_ids: list[str], groups: list[str]) -> list[Packet]:
    selected_ids: list[str] = []
    for group in groups:
        if group not in GROUPS:
            raise SystemExit(f"Unknown group: {group}")
        selected_ids.extend(GROUPS[group])
    selected_ids.extend(packet_ids)
    if not selected_ids:
        raise SystemExit("No packets selected. Use --group or --packet.")
    deduped: list[str] = []
    seen: set[str] = set()
    for packet_id in selected_ids:
        if packet_id not in PACKET_BY_ID:
            raise SystemExit(f"Unknown packet id: {packet_id}")
        if packet_id not in seen:
            deduped.append(packet_id)
            seen.add(packet_id)
    return [PACKET_BY_ID[packet_id] for packet_id in deduped]


def submit_packet(jules_bin: str, repo: str, packet: Packet) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [jules_bin, "new", "--repo", repo],
        input=render_packet(packet),
        capture_output=True,
        text=True,
        check=False,
    )


def print_listing() -> None:
    print("PM-plane Jules packet groups")
    for group, packet_ids in GROUPS.items():
        print(f"- {group}")
        for packet_id in packet_ids:
            packet = PACKET_BY_ID[packet_id]
            deps = ", ".join(packet.submit_after) if packet.submit_after else "none"
            print(f"  - {packet.id}: {packet.title} | submit_after={deps}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo for Jules sessions.")
    parser.add_argument("--jules-bin", default=DEFAULT_JULES_BIN, help="Path to the Jules CLI binary.")
    parser.add_argument("--group", action="append", default=[], help="Packet group to select. Repeatable.")
    parser.add_argument("--packet", action="append", default=[], help="Packet id to select. Repeatable.")
    parser.add_argument("--list", action="store_true", help="List packet groups and packet ids.")
    parser.add_argument("--render", action="store_true", help="Render the selected packet prompt(s) to stdout.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be submitted without creating Jules sessions.")
    parser.add_argument("--submit", action="store_true", help="Submit the selected packet(s) to Jules.")
    parser.add_argument(
        "--ack-merge-wave-complete",
        action="store_true",
        help="Required for real submission. Explicitly acknowledge the post-merge-wave precondition.",
    )
    parser.add_argument(
        "--require-open-pr-count-at-most",
        type=int,
        default=None,
        help="Optional GitHub open-PR count gate for real submission.",
    )
    args = parser.parse_args(argv)

    if args.list:
        print_listing()
        if not (args.render or args.dry_run or args.submit):
            return 0

    if not any((args.render, args.dry_run, args.submit)):
        parser.print_help(sys.stderr)
        return 2

    if not os.path.exists(args.jules_bin):
        print(f"Jules CLI not found: {args.jules_bin}", file=sys.stderr)
        return 2

    packets = select_packets(args.packet, args.group)

    if len(packets) > SESSION_LIMIT and args.submit:
        print(
            f"Refusing to submit {len(packets)} sessions at once. "
            f"Max safe concurrent submissions is {SESSION_LIMIT}.",
            file=sys.stderr,
        )
        return 2

    open_pr_count = fetch_open_pr_count(args.repo, os.environ.get("GH_TOKEN"))
    if open_pr_count is not None:
        print(f"GitHub open PR count for {args.repo}: {open_pr_count}")
    else:
        print(f"GitHub open PR count for {args.repo}: unavailable")

    existing_remote = packet_ids_in_remote_sessions(args.jules_bin)
    if existing_remote:
        print("Existing packet-like Jules sessions detected:")
        for packet_id in sorted(existing_remote):
            print(f"- {packet_id}")

    if args.render:
        for packet in packets:
            sys.stdout.write(render_packet(packet))
            sys.stdout.write("\n")

    if args.dry_run:
        print("Dry run:")
        for packet in packets:
            status = "already_exists" if packet.id in existing_remote else "ready_to_submit"
            print(
                f"- {packet.id} | {packet.title} | group={packet.group} | "
                f"submit_after={','.join(packet.submit_after) or 'none'} | status={status}"
            )
        return 0

    if args.submit:
        if not args.ack_merge_wave_complete:
            print(
                "Refusing real submission without --ack-merge-wave-complete. "
                "The packet plan is explicitly gated on the post-merge-wave baseline.",
                file=sys.stderr,
            )
            return 2
        if (
            args.require_open_pr_count_at_most is not None
            and open_pr_count is not None
            and open_pr_count > args.require_open_pr_count_at_most
        ):
            print(
                f"Refusing to submit: too many open PRs ({open_pr_count} > {args.require_open_pr_count_at_most}).",
                file=sys.stderr,
            )
            return 2
# Track packets that are known to exist remotely or have been submitted
        submitted_ids: set[str] = set()
        for packet in packets:
            if packet.id in existing_remote:
                print(f"Skipping {packet.id}: matching Jules session already exists.")
                submitted_ids.add(packet.id)
                continue

            # Enforce submit_after dependencies: each dependency must either already
            # exist remotely or have been submitted earlier in this run.
            missing_dependencies = [
                dep
                for dep in packet.submit_after
                if dep not in existing_remote and dep not in submitted_ids
            ]
            if missing_dependencies:
                print(
                    "Refusing to submit "
                    f"{packet.id}: submit_after dependencies not satisfied: "
                    f"{', '.join(missing_dependencies)}",
                    file=sys.stderr,
                )
                # Preserve any previous non-zero exit code if present; otherwise use 2
                if exit_code == 0:
                    exit_code = 2
                continue

            print(f"Submitting {packet.id} to Jules...")
            result = submit_packet(args.jules_bin, args.repo, packet)
            combined = ((result.stdout or "") + (result.stderr or "")).strip()
            print(f"Submission result for {packet.id}:")
            print(combined or "<no output>")
            if result.returncode == 0:
                submitted_ids.add(packet.id)
            else:
                continue
# Preserve any previous non-zero exit code if present; otherwise use the
                # jules submission return code.
                if exit_code == 0:
                    exit_code = result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
