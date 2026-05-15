from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from lib.proof_contract import build_conformance_report
from lib.risk_dashboard import (
    REQUIRED_RISK_ITEM_IDS,
    build_rte_risk_dashboard,
    render_rte_risk_dashboard_markdown,
    write_rte_risk_dashboard_artifacts,
)


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _risk_item(dashboard: dict, item_id: str) -> dict:
    for item in dashboard["risk_items"]:
        if item["id"] == item_id:
            return item
    raise AssertionError(f"risk item not found: {item_id}")


def _partial_proof_contract_report() -> dict:
    return build_conformance_report(
        {
            "run_id": "run-static-001",
            "git_sha": "abc123",
            "runner_sha256": "runner-digest",
            "argv": ["run_extraction_v5.py", "--phase", "D", "--dry-run"],
            "cwd": "/repo",
            "updated_at": "2026-05-15T00:00:00Z",
            "phases": {"D": {"counts": {"raw": 1}}},
            "linked_artifacts": {"coverage_rollup": "/repo/COVERAGE_ROLLUP.json"},
        },
        artifact_path=(
            "services/repo-truth-extractor/extraction/repo-truth-extractor/"
            "v5/runs/run/PROOF_PACK.json"
        ),
    )


def _dashboard(**overrides: object) -> dict:
    inputs = {
        "run_id_if_available": "risk-fixture",
        "generated_at": "2026-05-15T00:00:00Z",
        "repo_root_if_available": "/repo",
        "git_sha_if_available": "abc123",
        "downloaded_jsonl_files": [],
        "proof_contract_report": _partial_proof_contract_report(),
        "accepted_packet_basis": {
            item_id: True for item_id in REQUIRED_RISK_ITEM_IDS
        },
        "live_validation_plan_exists": True,
        "live_validation_authorized": False,
        "live_provider_validated": False,
        "live_batch_validated": False,
    }
    inputs.update(overrides)
    return build_rte_risk_dashboard(inputs)


def test_risk_dashboard_shows_static_only_live_readiness() -> None:
    dashboard = _dashboard()

    assert dashboard["live_use_readiness"] == "READY_FOR_LIMITED_DRY_STATIC_USE"
    assert dashboard["live_validation_status"] == "BLOCKED"
    assert dashboard["provider_call_status"] == "LIVE_VALIDATION_REQUIRED"
    assert "production" not in dashboard["live_use_readiness"].lower()
    assert _risk_item(dashboard, "LIVE_GATE")["status"] == "STATIC_ONLY"


def test_risk_dashboard_provider_lanes_remain_live_validation_required() -> None:
    dashboard = _dashboard()
    provider_metadata = _risk_item(dashboard, "PROVIDER_METADATA")

    assert provider_metadata["status"] == "LIVE_VALIDATION_REQUIRED"
    assert provider_metadata["live_provider_shapes_required"] is True
    assert provider_metadata["provider_lanes"] == {
        "direct_xai": "LIVE_VALIDATION_REQUIRED",
        "gemini_compatible": "LIVE_VALIDATION_REQUIRED",
        "openai_compatible": "LIVE_VALIDATION_REQUIRED",
        "openrouter_xai": "LIVE_VALIDATION_REQUIRED",
    }


def test_risk_dashboard_batch_static_jsonl_missing_not_live_validated() -> None:
    dashboard = _dashboard(downloaded_jsonl_files=[])
    batch_static = _risk_item(dashboard, "BATCH_STATIC")

    assert batch_static["status"] == "PASS_WITH_RISK"
    assert batch_static["downloaded_jsonl_status"] == "MISSING"
    assert batch_static["not_live_validated"] is True
    assert batch_static["live_validation_required"] is True


def test_risk_dashboard_proof_contract_partial_status_is_visible() -> None:
    dashboard = _dashboard()
    proof_contract = _risk_item(dashboard, "PROOF_CONTRACT")
    pass1_identity = _risk_item(dashboard, "PASS1_IDENTITY")

    assert dashboard["proof_contract_status"] == "partial"
    assert proof_contract["status"] == "PASS_WITH_RISK"
    assert proof_contract["conformance_status"] == "partial"
    assert "authoritative_artifacts" in proof_contract["missing_or_partial_fields"]
    assert proof_contract["run_proof_vs_bundle_proof"] == (
        "run_proof_or_packet_evidence_not_full_bundle"
    )
    assert pass1_identity["status"] == "UNKNOWN"
    assert pass1_identity["exact_identity_known_or_unknown"] == "unknown"


def test_risk_dashboard_generated_artifacts_are_non_authoritative() -> None:
    dashboard = _dashboard()
    artifact_authority = _risk_item(dashboard, "GENERATED_ARTIFACT_AUTHORITY")

    assert artifact_authority["status"] == "ACCEPTED_WITH_RISK"
    assert (
        artifact_authority["non_authority_label"]
        == "generated artifacts are evidence, not runtime source truth"
    )
    assert artifact_authority["authority_order"][0]["classification"] == "runtime_authority"


def test_risk_dashboard_prescan_accepted_and_rejected_states_are_summarized() -> None:
    dashboard = _dashboard()
    staleness = _risk_item(dashboard, "PRESCAN_STALENESS")
    influence = _risk_item(dashboard, "PRESCAN_INFLUENCE")

    assert staleness["status"] == "ACCEPTED_WITH_RISK"
    assert "accepted only" in staleness["accepted_import_status"]
    assert "stale" in staleness["rejected_import_behavior"]
    assert influence["influence_applied_or_not"] == (
        "accepted influence must be explicitly labeled"
    )
    assert "advisory" in influence["advisory_model_derived_status"]


def test_risk_dashboard_provenance_and_truth_label_states_are_summarized() -> None:
    dashboard = _dashboard()
    provenance = _risk_item(dashboard, "PROVENANCE_FIELDS")
    truth_labels = _risk_item(dashboard, "TRUTH_LABELS")

    assert provenance["repaired_values_labeled"] is True
    assert provenance["sidefilled_values_labeled"] is True
    assert truth_labels["unknown_preservation"] is True
    assert truth_labels["conflicting_preservation"] is True


def test_risk_dashboard_redacts_unsafe_fields(tmp_path: Path) -> None:
    secret_value = "super-" + "secret-value"
    bearer_value = "hidden-" + "value"
    dashboard = _dashboard(
        warnings=[
            f"provider returned token={secret_value}",
            {"authorization": f"Bearer {bearer_value}"},
        ]
    )
    written = write_rte_risk_dashboard_artifacts(run_root=tmp_path, dashboard=dashboard)
    payload_text = Path(written["risk_dashboard_json"]).read_text(encoding="utf-8")
    markdown = render_rte_risk_dashboard_markdown(dashboard)

    assert secret_value not in payload_text
    assert bearer_value not in payload_text
    assert secret_value not in markdown
    assert bearer_value not in markdown
    assert "[REDACTED]" in payload_text


def test_risk_dashboard_generation_requires_no_provider_calls(
    tmp_path: Path, monkeypatch
) -> None:
    runner = _load_runner_module()

    def forbidden_provider_call(*args, **kwargs):  # pragma: no cover - failure path
        raise AssertionError("provider or batch call was invoked")

    for name in (
        "llm_runtime_call_llm",
        "llm_runtime_call_llm_with_ladder",
        "run_provider_preflight",
        "run_provider_doctor_probe",
        "BatchClient",
        "XAIBatchClient",
        "OpenAIBatchClient",
        "OpenRouterBatchClient",
        "GeminiBatchClient",
    ):
        if hasattr(runner, name):
            monkeypatch.setattr(runner, name, forbidden_provider_call)

    dirs = {"root": tmp_path}
    for phase in runner.PHASES:
        dirs[phase] = tmp_path / phase

    payload = runner.emit_run_dashboard_snapshot(
        run_id="risk-dashboard-no-provider",
        dirs=dirs,
        ui=None,
        source="test",
    )

    risk_path = tmp_path / "telemetry" / "RTE_RISK_DASHBOARD.json"
    assert payload["run_id"] == "risk-dashboard-no-provider"
    assert risk_path.exists()
    risk_payload = json.loads(risk_path.read_text(encoding="utf-8"))
    assert [item["id"] for item in risk_payload["risk_items"]] == list(
        REQUIRED_RISK_ITEM_IDS
    )
