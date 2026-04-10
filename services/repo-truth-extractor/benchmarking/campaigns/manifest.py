from __future__ import annotations

from typing import Any

from ..policies.loader import load_policy_pack
from .selection import CampaignAssignment, CampaignPlan


def build_campaign_manifest(plan: CampaignPlan) -> dict[str, Any]:
    policy_versions = {}
    for file_name in plan.policy_pack_files:
        payload = load_policy_pack(file_name)
        policy_versions[file_name] = {
            "policy_id": payload.get("policy_id"),
            "policy_version": payload.get("policy_version"),
        }

    def serialize_assignment(kind: str, item: CampaignAssignment) -> dict[str, Any]:
        return {
            "assignment_kind": kind,
            "route_id": item.candidate.route_id,
            "cohort": item.candidate.cohort,
            "surface_class": item.candidate.surface_class,
            "surface_id": item.candidate.surface_id,
            "provider_name": item.candidate.provider_name,
            "model_key": item.candidate.model_key,
            "provider_model_id": item.candidate.provider_model_id,
            "case_id": item.case_id,
            "archetype_id": item.archetype_id,
            "profile_id": item.profile_id,
            "control_anchor_group_id": item.control_anchor_group_id,
            "live_execution": item.live_execution,
            "phase": item.phase,
            "repo_root": str(item.repo_root),
            "routing_override_model": item.routing_override_model,
            "admission_reason": item.candidate.admission_reason,
            "policy_note": item.candidate.policy_note,
            "operator_note": item.operator_note,
        }

    return {
        "campaign_id": plan.campaign_id,
        "runtime_version": plan.runtime_version,
        "contract_snapshot_id": plan.contract_snapshot_id,
        "case_set_id": plan.case_set_id,
        "repo_root": str(plan.repo_root),
        "control_candidates": [serialize_assignment("control", item) for item in plan.baseline_assignments],
        "campaign_candidates": [serialize_assignment("candidate", item) for item in plan.campaign_assignments],
        "policy_pack_versions": policy_versions,
        "notes": list(plan.notes),
    }
