from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..cli.benchmark_governance_smoke import run_governance_smoke
from ..cli.benchmark_route_separation_smoke import run_smoke as run_route_separation_smoke
from ..models.ids import synthetic_id
from ..reporting.profile_synthesis_summary import build_profile_synthesis_summary
from ..storage.hashing import stable_json_dumps
from ..storage.sqlite_repo import BenchmarkCatalogRepo
from .blocked_lanes import build_blocked_lane_rows
from .proposal_models import SynthesisProposal
from .review_packets import build_review_packet
from .routing_diff import build_routing_diff_proposals


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_dir(base: Path) -> Path:
    candidates = sorted(path for path in base.iterdir() if path.is_dir())
    if not candidates:
        raise RuntimeError(f"no proof runs found under {base}")
    return candidates[-1]


def _load_direct_model_inputs(repo_root: Path, run_dir: Path | None = None) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = run_dir or _latest_dir(repo_root / "proof" / "benchmarking" / "TP-RTE-BENCH-DMB-001")
    return (
        run_dir,
        _load_json(run_dir / "RUN_MANIFEST.json"),
        _load_json(run_dir / "DIRECT_MODEL_COMPARISON.json"),
    )


def _load_pricing_inputs(repo_root: Path, run_dir: Path | None = None) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = run_dir or _latest_dir(repo_root / "proof" / "benchmarking" / "TP-RTE-BENCH-PRICE-001")
    return (
        run_dir,
        _load_json(run_dir / "RUN_MANIFEST.json"),
        _load_json(run_dir / "pricing_coverage_report.json"),
    )


def _pricing_index(pricing_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["model_key"]): row for row in pricing_report.get("rows", [])}


def _direct_model_proposals(
    *,
    direct_model_run_dir: Path,
    comparison_payload: dict[str, Any],
    pricing_report: dict[str, Any],
) -> list[SynthesisProposal]:
    pricing_by_key = _pricing_index(pricing_report)
    proposals: list[SynthesisProposal] = []
    for row in comparison_payload.get("comparison_rows", []):
        model_key = str(row["model_key"])
        pricing = pricing_by_key.get(model_key, {})
        pricing_status = str(pricing.get("pricing_status") or "UNPRICED_UNKNOWN")
        pass_rate = float(row.get("validator_pass_rate") or 0.0)
        caveated = pricing_status == "PRICED_WITH_CAVEAT"
        blocked = []
        proposal_class = "admit_to_runtime_route_testing"
        target_profile = "balanced_profile"
        rationale = [
            "Direct-model evidence is admission-oriented only and cannot prove runtime-route truth.",
            f"Validator pass rate={pass_rate:.6f}.",
        ]
        notes = ["Derived from direct_model comparison artifacts only."]

        if pricing_status in {"UNPRICED_UNKNOWN", "STALE_NEEDS_REFRESH"}:
            proposal_class = "insufficient_evidence" if pass_rate > 0.0 else "experimental_only"
            blocked.append(pricing_status)
            target_profile = "pricing_blocked"
            rationale.append("Pricing truth is not sufficient for cost-aware synthesis.")
        elif caveated:
            proposal_class = "candidate_for_low_cost_profile"
            target_profile = "low_cost_profile"
            blocked.append("pricing_caveated")
            rationale.append("Pricing is caveated and must remain caveated in any low-cost proposal.")
        elif pass_rate <= 0.0:
            proposal_class = "experimental_only"
            target_profile = "experimental_profile"
            blocked.append("validator_zero_pass_rate")
            rationale.append("Direct-model evidence is too weak for admission despite confirmed pricing.")

        proposals.append(
            SynthesisProposal(
                proposal_id=synthetic_id("profile_proposal", model_key),
                proposal_class=proposal_class,
                subject_key=model_key,
                subject_kind="model",
                target_profile=target_profile,
                benchmark_mode="profile_synthesis_input",
                candidate_type="profile_candidate",
                pricing_status=pricing_status,
                caveated=caveated,
                blocked_reason_codes=blocked,
                evidence_refs=[
                    str(direct_model_run_dir / "DIRECT_MODEL_COMPARISON.json"),
                    str(direct_model_run_dir / "DIRECT_MODEL_CAMPAIGN_MANIFEST.json"),
                    "pricing_coverage_report.json",
                ],
                evidence_classes=["direct_model", "pricing"],
                unresolved_unknowns=list(blocked),
                rationale=rationale,
                notes=notes,
            )
        )
    return proposals


def _runtime_route_proposals(
    *,
    runtime_route_payload: dict[str, Any],
    repo: BenchmarkCatalogRepo,
    pricing_report: dict[str, Any],
) -> list[SynthesisProposal]:
    benchmark_run_id = str(runtime_route_payload["benchmark_run_id"])
    route_blocked = str(runtime_route_payload.get("bounded_admissibility_result", {}).get("status")) != "admissible"
    pricing_by_key = _pricing_index(pricing_report)
    proposals_by_key: dict[tuple[str, str], SynthesisProposal] = {}
    recommendations = [
        item for item in repo.list_promotion_recommendations() if str(item.get("benchmark_run_id")) == benchmark_run_id
    ]
    for recommendation in recommendations:
        route_id = str(recommendation["route_id"])
        state = str(recommendation["recommendation_state"])
        pricing = pricing_by_key.get(str(recommendation.get("route_id") or ""), {})
        pricing_status = str(pricing.get("pricing_status") or "NOT_APPLICABLE")
        proposal_class = "candidate_for_balanced_profile"
        blocked_reason_codes: list[str] = []
        rationale = [
            "Runtime-route evidence remains the only source that can support route/profile truth.",
            f"Governance state={state}.",
        ]
        if route_blocked:
            proposal_class = "blocked_lane"
            blocked_reason_codes.extend(
                list(runtime_route_payload.get("bounded_admissibility_result", {}).get("blocking_reason_codes", []))
            )
            rationale.append("Route admissibility or lane non-contestability blocks runtime optimization.")
        elif state == "experimental_only":
            proposal_class = "experimental_only"
        elif state in {"quarantined", "ineligible", "stale_disputed"}:
            proposal_class = "insufficient_evidence"
            blocked_reason_codes.append(state)

        key = (route_id, str(recommendation["profile_id"]))
        proposals_by_key[key] = SynthesisProposal(
            proposal_id=synthetic_id("profile_proposal", route_id),
            proposal_class=proposal_class,
            subject_key=route_id,
            subject_kind="route",
            target_profile=str(recommendation["profile_id"]),
            benchmark_mode="profile_synthesis_input",
            candidate_type="profile_candidate",
            pricing_status=pricing_status,
            caveated=False,
            blocked_reason_codes=blocked_reason_codes,
            evidence_refs=[
                "PROMOTION_RECOMMENDATIONS.json",
                "ROUTE_IDENTITY_ADMISSIBILITY.json",
                route_id,
            ],
            evidence_classes=["runtime_route", "governance", "pricing"],
            unresolved_unknowns=list(blocked_reason_codes),
            rationale=rationale,
            notes=["Derived from runtime_route governance and admissibility artifacts."],
        )
    return list(proposals_by_key.values())


def _build_preflight(
    *,
    direct_model_comparison: dict[str, Any],
    pricing_report: dict[str, Any],
    runtime_route_payload: dict[str, Any],
    repo: BenchmarkCatalogRepo,
) -> dict[str, Any]:
    pricing_by_key = _pricing_index(pricing_report)
    direct_rows = []
    for row in direct_model_comparison.get("comparison_rows", []):
        pricing = pricing_by_key.get(str(row["model_key"]), {})
        pricing_status = str(pricing.get("pricing_status") or "UNPRICED_UNKNOWN")
        direct_rows.append(
            {
                "subject_key": str(row["model_key"]),
                "lane": "direct_model",
                "pricing_status": pricing_status,
                "eligibility": (
                    "blocked_by_pricing"
                    if pricing_status in {"UNPRICED_UNKNOWN", "STALE_NEEDS_REFRESH"}
                    else ("caveated_only" if pricing_status == "PRICED_WITH_CAVEAT" else "eligible")
                ),
            }
        )

    benchmark_run_id = str(runtime_route_payload["benchmark_run_id"])
    route_rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    route_blocked = str(runtime_route_payload.get("bounded_admissibility_result", {}).get("status")) != "admissible"
    for recommendation in repo.list_promotion_recommendations():
        if str(recommendation.get("benchmark_run_id")) != benchmark_run_id:
            continue
        key = (str(recommendation["route_id"]), str(recommendation["profile_id"]))
        route_rows_by_key[key] = {
            "subject_key": str(recommendation["route_id"]),
            "lane": "runtime_route",
            "pricing_status": "NOT_APPLICABLE",
            "eligibility": (
                "blocked_by_admissibility"
                if route_blocked
                else (
                    "caveated_only"
                    if str(recommendation["recommendation_state"]) == "experimental_only"
                    else "eligible"
                )
            ),
        }
    route_rows = list(route_rows_by_key.values())
    return {
        "eligible_for_synthesis": [
            row["subject_key"] for row in direct_rows + route_rows if row["eligibility"] == "eligible"
        ],
        "blocked_by_pricing_uncertainty": [
            row["subject_key"] for row in direct_rows if row["eligibility"] == "blocked_by_pricing"
        ],
        "blocked_by_route_admissibility_or_non_contestability": [
            row["subject_key"] for row in route_rows if row["eligibility"] == "blocked_by_admissibility"
        ],
        "caveated_only": [
            row["subject_key"] for row in direct_rows + route_rows if row["eligibility"] == "caveated_only"
        ],
        "rows": direct_rows + route_rows,
    }


def synthesize_profile_proposals(
    *,
    repo_root: Path,
    benchmark_root: Path | None = None,
    direct_model_run_dir: Path | None = None,
    pricing_run_dir: Path | None = None,
) -> dict[str, Any]:
    direct_dir, direct_manifest, direct_comparison = _load_direct_model_inputs(repo_root, direct_model_run_dir)
    pricing_dir, pricing_manifest, pricing_report = _load_pricing_inputs(repo_root, pricing_run_dir)

    governance_payload = run_governance_smoke(root=benchmark_root, proof_dir=None)
    route_payload = run_route_separation_smoke(
        root=benchmark_root,
        proof_dir=None,
        benchmark_run_ids=[str(governance_payload["benchmark_run_id"])],
    )
    runtime_route_payload = {
        "benchmark_run_id": str(governance_payload["benchmark_run_id"]),
        "bounded_admissibility_result": route_payload["bounded_admissibility_result"],
        "admissibility": route_payload["admissibility"],
        "corrected_control_strategy": route_payload["corrected_control_strategy"],
    }
    repo = BenchmarkCatalogRepo.from_root(benchmark_root)
    preflight = _build_preflight(
        direct_model_comparison=direct_comparison,
        pricing_report=pricing_report,
        runtime_route_payload=runtime_route_payload,
        repo=repo,
    )
    blocked_lanes = build_blocked_lane_rows(
        runtime_route_payload=runtime_route_payload,
        pricing_report=pricing_report,
    )
    proposals = _direct_model_proposals(
        direct_model_run_dir=direct_dir,
        comparison_payload=direct_comparison,
        pricing_report=pricing_report,
    ) + _runtime_route_proposals(
        runtime_route_payload=runtime_route_payload,
        repo=repo,
        pricing_report=pricing_report,
    )
    routing_diffs = build_routing_diff_proposals(proposals)
    review_packets = [build_review_packet(proposal) for proposal in proposals]
    summary = build_profile_synthesis_summary(
        preflight=preflight,
        proposals=[item.to_dict() for item in proposals],
        routing_diffs=[item.to_dict() for item in routing_diffs],
        blocked_lanes=blocked_lanes,
    )
    synthesis_input_refs = {
        "direct_model_run": str(direct_dir),
        "pricing_run": str(pricing_dir),
        "runtime_route_run": str(governance_payload["benchmark_run_id"]),
    }
    return {
        "preflight": preflight,
        "direct_model_inputs": {
            "run_dir": str(direct_dir),
            "comparison_ref": str(direct_dir / "DIRECT_MODEL_COMPARISON.json"),
        },
        "pricing_inputs": {
            "run_dir": str(pricing_dir),
            "coverage_ref": str(pricing_dir / "pricing_coverage_report.json"),
        },
        "runtime_route_inputs": runtime_route_payload,
        "synthesis_input_refs": synthesis_input_refs,
        "proposals": [item.to_dict() for item in proposals],
        "routing_diffs": [item.to_dict() for item in routing_diffs],
        "blocked_lanes": blocked_lanes,
        "review_packets": [item.to_dict() for item in review_packets],
        "summary": summary,
    }


def write_profile_synthesis_artifacts(proof_dir: Path, payload: dict[str, Any]) -> None:
    proof_dir.mkdir(parents=True, exist_ok=True)
    (proof_dir / "PROFILE_SYNTHESIS_SUMMARY.json").write_text(
        stable_json_dumps(payload["summary"]) + "\n",
        encoding="utf-8",
    )
    (proof_dir / "BLOCKED_LANES.json").write_text(
        stable_json_dumps(payload["blocked_lanes"]) + "\n",
        encoding="utf-8",
    )
    (proof_dir / "synthesis_preflight.json").write_text(
        stable_json_dumps(payload["preflight"]) + "\n",
        encoding="utf-8",
    )
    for proposal in payload["proposals"]:
        path = proof_dir / f"PROFILE_PROPOSAL__{proposal['proposal_id']}.json"
        path.write_text(stable_json_dumps(proposal) + "\n", encoding="utf-8")
    for proposal in payload["routing_diffs"]:
        path = proof_dir / f"ROUTING_DIFF_PROPOSAL__{proposal['proposal_id']}.json"
        path.write_text(stable_json_dumps(proposal) + "\n", encoding="utf-8")
    for packet in payload["review_packets"]:
        path = proof_dir / f"PROFILE_REVIEW_PACKET__{packet['proposal_id']}.json"
        path.write_text(stable_json_dumps(packet) + "\n", encoding="utf-8")
