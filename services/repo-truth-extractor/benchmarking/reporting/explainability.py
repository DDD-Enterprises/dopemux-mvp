from __future__ import annotations

from typing import Any

from ..models.enums import EvidenceClass


def candidate_key(recommendation: dict[str, Any]) -> str:
    return "__".join(
        [
            str(recommendation.get("benchmark_mode") or "runtime_route"),
            str(recommendation.get("candidate_type") or "route_candidate"),
            str(recommendation.get("route_id")),
            str(recommendation.get("surface_id")),
            str(recommendation.get("archetype_id")),
            str(recommendation.get("profile_id")),
        ]
    )


def evidence_claim(statement: str, evidence_class: str, refs: list[str]) -> dict[str, Any]:
    return {
        "statement": statement,
        "evidence_class": evidence_class,
        "refs": refs,
    }


def build_explanation_chain(
    recommendation: dict[str, Any],
    governance_packet: dict[str, Any],
    attempt: dict[str, Any],
    bundle: dict[str, Any],
    case_set_rollup: dict[str, Any],
    archetype_rollup: dict[str, Any],
    profile_fit: dict[str, Any],
    control_deltas: list[dict[str, Any]],
    latest_governance_decision: dict[str, Any] | None,
) -> dict[str, Any]:
    refs = [
        recommendation["recommendation_id"],
        attempt["case_attempt_id"],
        bundle["bundle_id"],
    ]
    chain = [
        {
            "node_type": "recommendation_state",
            "ref": recommendation["recommendation_id"],
            "evidence_class": EvidenceClass.GOVERNANCE_DERIVED.value,
        },
        {
            "node_type": "profile_fit",
            "ref": f"PROFILE_FIT__{recommendation['profile_id']}",
            "evidence_class": EvidenceClass.BENCHMARK_DERIVED.value,
        },
        {
            "node_type": "rollup_case_set",
            "ref": f"CASESET_ROLLUP__{attempt['case_set_id']}",
            "evidence_class": EvidenceClass.BENCHMARK_DERIVED.value,
        },
        {
            "node_type": "rollup_archetype",
            "ref": f"ARCHETYPE_ROLLUP__{attempt['archetype_id']}",
            "evidence_class": EvidenceClass.BENCHMARK_DERIVED.value,
        },
        {
            "node_type": "control_deltas",
            "ref": attempt["case_attempt_id"],
            "evidence_class": EvidenceClass.BENCHMARK_DERIVED.value,
        },
        {
            "node_type": "benchmark_case_attempt",
            "ref": attempt["case_attempt_id"],
            "evidence_class": EvidenceClass.BENCHMARK_DERIVED.value,
        },
        {
            "node_type": "evidence_bundle",
            "ref": bundle["bundle_id"],
            "evidence_class": EvidenceClass.BENCHMARK_DERIVED.value,
        },
    ]
    if latest_governance_decision is not None:
        chain.append(
            {
                "node_type": "governance_decision",
                "ref": latest_governance_decision["decision_id"],
                "evidence_class": EvidenceClass.GOVERNANCE_DERIVED.value,
            }
        )

    claims = [
        evidence_claim(
            statement=f"Recommendation state {recommendation['recommendation_state']} is policy-derived from benchmark evidence and governance rules.",
            evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
            refs=[recommendation["recommendation_id"]],
        ),
        evidence_claim(
            statement=f"Case-set rollup contract pass rate is {case_set_rollup.get('contract_pass_rate')}.",
            evidence_class=EvidenceClass.BENCHMARK_DERIVED.value,
            refs=[f"CASESET_ROLLUP__{attempt['case_set_id']}"],
        ),
        evidence_claim(
            statement=f"Profile fit for {recommendation['profile_id']} has attempt_total={profile_fit.get('attempt_total')}.",
            evidence_class=EvidenceClass.BENCHMARK_DERIVED.value,
            refs=[f"PROFILE_FIT__{recommendation['profile_id']}"],
        ),
        evidence_claim(
            statement=f"Control delta count is {len(control_deltas)} for this attempt.",
            evidence_class=EvidenceClass.BENCHMARK_DERIVED.value,
            refs=[attempt["case_attempt_id"]],
        ),
        evidence_claim(
            statement=f"Surface identity {recommendation['surface_id']} is metadata only and does not prove suitability.",
            evidence_class=EvidenceClass.METADATA_ONLY.value,
            refs=[recommendation["surface_id"]],
        ),
        evidence_claim(
            statement=f"Benchmark lane {attempt.get('benchmark_mode')} remains distinct from direct_model evidence and downstream profile synthesis inputs.",
            evidence_class=EvidenceClass.BENCHMARK_DERIVED.value,
            refs=[attempt["case_attempt_id"]],
        ),
        evidence_claim(
            statement=f"Governance packet blocker count is {len(governance_packet.get('failed_gates', []))}.",
            evidence_class=EvidenceClass.MIXED_EVIDENCE.value,
            refs=refs,
        ),
    ]
    if latest_governance_decision is not None:
        claims.append(
            evidence_claim(
                statement=f"Latest governance decision is {latest_governance_decision['decision_type']}.",
                evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                refs=[latest_governance_decision["decision_id"]],
            )
        )
    return {"candidate_key": candidate_key(recommendation), "chain": chain, "claims": claims}
