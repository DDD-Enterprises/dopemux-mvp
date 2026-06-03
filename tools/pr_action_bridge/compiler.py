"""Read-only PR Action Bridge compiler.

Compiles PR Steward artifacts into ACTION_PLAN.json and REPAIR_PACKET.md.
No filesystem I/O. No GitHub mutation. No import of tools.pr_merge.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "1.0.0"

# Blocker → (category, target_role) locked to classifier._readiness() taxonomy.
# EMBEDDED_AUDIT_* prefix is handled separately (see _blocker_to_action).
_BLOCKER_MAP: dict[str, tuple[str, str]] = {
    "HARVEST_INCOMPLETE": ("harvest-incomplete", "supervisor"),
    "PR_IS_DRAFT": ("pr-is-draft", "supervisor"),
    "PR_CLOSED": ("pr-closed", "supervisor"),
    "MIXED_SHA_ARTIFACT_SET": ("mixed-sha", "supervisor"),
    "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION": ("unknown-reviewer", "supervisor"),
    "PROOF_STALE": ("proof-stale", "supervisor"),
    "PROOF_MISSING": ("proof-missing", "supervisor"),
    "UNKNOWN_PR_AUTHOR": ("unknown-pr-author", "supervisor"),
    "UNKNOWN_CHECK": ("unknown-check", "supervisor"),
    "REVIEW_ITEM_NEEDS_SUPERVISOR": ("needs-supervisor", "supervisor"),
    "UNRESOLVED_REVIEW_THREAD": ("unresolved-thread", "implementer"),
    "FAILED_CHECK": ("failed-check", "implementer"),
    "REQUEST_CHANGES": ("request-changes", "implementer"),
    "REVIEW_ITEM_MUST_FIX": ("must-fix", "implementer"),
    "PENDING_CHECK": ("pending-check", "ci"),
}

_ROLE_ORDER = ("supervisor", "implementer", "ci")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _blocker_to_action(
    blocker: str,
) -> tuple[str, str] | None:
    """Return (category, target_role) for a blocker string, or None if unrecognised."""
    if blocker.startswith("EMBEDDED_AUDIT_"):
        return ("embedded-audit-failed", "supervisor")
    return _BLOCKER_MAP.get(blocker)


def _find_source_item_id(
    blocker: str,
    review_ledger: dict[str, Any],
    thread_dispositions: dict[str, Any],
    ci_triage: dict[str, Any],
) -> str | None:
    """Return the first item ID that matches this blocker, or None."""
    def _item_id(item: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            val = item.get(key)
            if val:
                return str(val)
        return None

    if blocker in {"UNRESOLVED_REVIEW_THREAD", "REVIEW_ITEM_NEEDS_SUPERVISOR", "REVIEW_ITEM_MUST_FIX"}:
        for item in review_ledger.get("items", []):
            blockers_for_item = item.get("blockers") or []
            if blocker in blockers_for_item:
                result = _item_id(item, "id", "node_id")
                if result:
                    return result

    if blocker == "UNRESOLVED_REVIEW_THREAD":
        for thread in thread_dispositions.get("threads", []):
            is_resolved = thread.get("is_resolved", thread.get("resolved", True))
            if not is_resolved:
                result = _item_id(thread, "id", "thread_id")
                if result:
                    return result

    if blocker in {"FAILED_CHECK", "PENDING_CHECK", "UNKNOWN_CHECK"}:
        for check in ci_triage.get("checks", []):
            check_blockers = check.get("blockers") or []
            if blocker in check_blockers:
                result = _item_id(check, "id", "name")
                if result:
                    return result

    if blocker == "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION":
        for item in review_ledger.get("items", []):
            if "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION" in (item.get("blockers") or []):
                result = _item_id(item, "id", "node_id")
                if result:
                    return result

    return None


def _build_rationale(blocker: str, category: str, target_role: str) -> str:
    messages: dict[str, str] = {
        "harvest-incomplete": "Harvest did not complete; re-run harvester before re-evaluating.",
        "pr-is-draft": "PR is in draft state; author must mark ready for review.",
        "pr-closed": "PR is closed; supervisor must verify intent before proceeding.",
        "mixed-sha": "Artifact set contains mixed SHAs; supervisor must re-harvest at consistent SHA.",
        "unknown-reviewer": "Reviewer is not in known_reviewers.json; supervisor must classify.",
        "proof-stale": "Proof bundle is stale; supervisor must re-run proof/audit at current head SHA.",
        "proof-missing": "Proof bundle is missing; supervisor must produce proof/audit bundle before proceeding.",
        "unknown-pr-author": "PR author is not in known_reviewers.json; supervisor must verify author before proceeding.",
        "unknown-check": "CI check is not in known checks registry; supervisor must classify.",
        "needs-supervisor": "Review item requires supervisor classification before proceeding.",
        "embedded-audit-failed": "Embedded audit did not pass; supervisor must review audit findings.",
        "unresolved-thread": "Review thread is unresolved; implementer must address and resolve.",
        "failed-check": "CI check failed; implementer must investigate and fix.",
        "request-changes": "Reviewer requested changes; implementer must address review feedback.",
        "must-fix": "Review item marked must-fix; implementer must resolve before merge.",
        "pending-check": "CI check is pending; wait for check to complete before re-evaluating.",
    }
    return messages.get(category, f"Blocker {blocker!r} requires {target_role} attention.")


def compile_action_plan(
    merge_readiness: dict[str, Any],
    review_ledger: dict[str, Any],
    thread_dispositions: dict[str, Any],
    ci_triage: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Pure function. No filesystem I/O. No GitHub mutation.

    Returns (action_plan_dict, repair_packet_md).
    """
    if "readiness" not in merge_readiness:
        raise KeyError("merge_readiness.readiness is required")

    generated = generated_at or _utc_now()

    # Support both the nested classifier shape (merge_readiness["pr"]["number"]) and
    # the legacy flat shape (merge_readiness["pr_number"] / merge_readiness["repo"]).
    if "pr" in merge_readiness:
        pr_obj = merge_readiness["pr"]
        pr_number = int(pr_obj["number"])
        # Extract owner/repo from GitHub PR URL: https://github.com/owner/repo/pull/N
        url_parts = str(pr_obj.get("url", "")).rstrip("/").split("/")
        repo = f"{url_parts[-4]}/{url_parts[-3]}" if len(url_parts) >= 5 else "unknown/unknown"
    elif "pr_number" in merge_readiness and "repo" in merge_readiness:
        pr_number = int(merge_readiness["pr_number"])
        repo = str(merge_readiness["repo"])
    else:
        raise KeyError(
            "merge_readiness must contain 'pr' (nested classifier shape) "
            "or both 'pr_number' and 'repo' (flat shape)"
        )

    readiness = str(merge_readiness["readiness"])
    blockers: list[str] = list(merge_readiness.get("blockers") or [])

    actions: list[dict[str, Any]] = []

    if readiness != "READY":
        action_num = 0
        for blocker in blockers:
            action_num += 1
            mapping = _blocker_to_action(blocker)
            if mapping:
                category, target_role = mapping
            else:
                # Unknown blocker: fail-closed to supervisor
                category, target_role = ("unknown-blocker", "supervisor")
            source_item_id = _find_source_item_id(
                blocker, review_ledger, thread_dispositions, ci_triage
            )
            actions.append(
                {
                    "id": f"action-{action_num:04d}",
                    "category": category,
                    "target_role": target_role,
                    "source_blocker": blocker,
                    "source_item_id": source_item_id or None,
                    "rationale": _build_rationale(blocker, category, target_role),
                }
            )

    action_plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "pr_number": pr_number,
        "repo": repo,
        "readiness": readiness,
        "actions": actions,
        "mutation_performed": False,
    }

    repair_packet = _render_repair_packet(action_plan)
    return action_plan, repair_packet


def _render_repair_packet(action_plan: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# REPAIR_PACKET")
    lines.append("")
    lines.append(f"**PR**: {action_plan['repo']}#{action_plan['pr_number']}")
    lines.append(f"**Readiness**: {action_plan['readiness']}")
    lines.append(f"**Generated**: {action_plan['generated_at']}")
    lines.append("")

    actions = action_plan.get("actions") or []

    if not actions:
        lines.append("No actions required — PR is READY.")
        return "\n".join(lines) + "\n"

    # Group by role in canonical order
    by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in _ROLE_ORDER}
    for action in actions:
        role = action.get("target_role", "supervisor")
        if role in by_role:
            by_role[role].append(action)
        else:
            # Unknown role: fail closed to supervisor so the action is never silently dropped.
            by_role["supervisor"].append(action)

    role_headings = {
        "supervisor": "## Supervisor Actions",
        "implementer": "## Implementer Actions",
        "ci": "## CI / Wait Actions",
    }

    for role in _ROLE_ORDER:
        role_actions = by_role.get(role) or []
        if not role_actions:
            continue
        lines.append(role_headings.get(role, f"## {role.title()} Actions"))
        lines.append("")
        for action in role_actions:
            item_ref = f" (item: `{action['source_item_id']}`)" if action.get("source_item_id") else ""
            lines.append(f"- **[{action['id']}]** `{action['category']}`{item_ref}")
            lines.append(f"  - Blocker: `{action['source_blocker']}`")
            lines.append(f"  - {action['rationale']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
