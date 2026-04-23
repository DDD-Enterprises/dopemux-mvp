"""Authority-visible PM write confirmation and receipt text helpers."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from dopemux.pm.writes import PMActionKind

ACTION_AUTHORITY = {
    PMActionKind.METADATA_UPDATE: "leantime",
    PMActionKind.WORKFLOW_TRANSITION: "task-orchestrator",
    PMActionKind.PROGRESS_LOG: "conport",
    PMActionKind.DECISION_LOG: "conport",
}

ACTION_LABEL = {
    PMActionKind.METADATA_UPDATE: "update ticket metadata",
    PMActionKind.WORKFLOW_TRANSITION: "transition workflow state",
    PMActionKind.PROGRESS_LOG: "record progress",
    PMActionKind.DECISION_LOG: "commit decision",
}


def authority_label(action_kind: PMActionKind) -> str:
    """Return the canonical authority label for a PM action."""

    return ACTION_AUTHORITY[action_kind]


def render_write_confirmation(
    action_kind: PMActionKind,
    *,
    work_item_id: Optional[str] = None,
    project_id: Optional[str] = None,
    fields: Optional[Iterable[str]] = None,
    transition: Optional[str] = None,
    current_state: Optional[str] = None,
    mirror_note: Optional[str] = None,
) -> str:
    """Render strict operator-facing confirmation copy."""

    lines: List[str] = [
        f"WRITE -> {authority_label(action_kind)}: {ACTION_LABEL[action_kind]}"
    ]
    if work_item_id:
        lines.append(f"work item: {work_item_id}")
    if project_id:
        lines.append(f"project: {project_id}")
    if fields:
        lines.append(f"fields: {', '.join(sorted(str(field) for field in fields))}")
    if current_state:
        lines.append(f"current state: {current_state}")
    if transition:
        lines.append(f"requested transition: {transition}")
    if mirror_note:
        lines.append(f"mirror: {mirror_note}")
    lines.append("Enter commits")
    lines.append("Esc cancels")
    return "\n".join(lines)


def render_adapter_confirmation(action: str) -> str:
    """Render adapter-only confirmation copy."""

    return "\n".join(
        [
            f"ADAPTER -> dopecon-bridge: {action}",
            "Enter commits",
            "Esc cancels",
        ]
    )


def render_write_receipt(
    action_kind: PMActionKind,
    *,
    identifier: str,
    mirror_targets: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Render operator-visible result lines with mirrors separated."""

    if action_kind == PMActionKind.METADATA_UPDATE:
        lines = [f"Updated: leantime metadata for {identifier}"]
    elif action_kind == PMActionKind.WORKFLOW_TRANSITION:
        lines = [f"Transitioned: task-orchestrator workflow for {identifier}"]
    elif action_kind == PMActionKind.DECISION_LOG:
        lines = ["Logged: conport decision entry"]
    else:
        lines = ["Logged: conport progress entry"]

    for service, detail in (mirror_targets or {}).items():
        lines.append(f"Mirrored: {service} {detail}")
    return lines
