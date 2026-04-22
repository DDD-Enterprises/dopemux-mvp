from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.engine import PrescanEngine
from lib.prescan.models import PrescanConfig
from lib.prescan.provider_catalog import NO_LIVE_LANE


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Codex Test")
    _git(repo, "config", "user.email", "codex@example.com")
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("def alpha() -> int:\n    return 1\n", encoding="utf-8")
    _commit_all(repo, "initial fixture")
    return repo


def _make_config(repo: Path, output_dir: Path, **overrides: object) -> PrescanConfig:
    config = PrescanConfig(
        repo_root=repo,
        output_dir=output_dir,
        enable_git_enrichment=False,
        batch_mode=False,
        cost_estimate=False,
    )
    config.allow_online_llm = True
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def test_authorized_live_lane_writes_success_artifact_and_uses_selected_route(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "out"
    engine = PrescanEngine(_make_config(repo, output_dir))

    selected_candidate = {
        "provider": "openrouter",
        "model_id": "openai/gpt-5-nano",
        "api_key_env": "OPENROUTER_API_KEY",
        "prescan_tier": "cheap_structured",
        "dependency_class": "proxy",
        "economic_surface": "openrouter",
        "execution_transport": "openai_sdk",
        "pricing": {"input_1m_usd": 1.0, "output_1m_usd": 4.0},
    }
    selected_route = {
        "pass_id": "dedup",
        "required_tier": "cheap_structured",
        "selected_tier": "cheap_structured",
        "tier_adjustment": "exact",
        "provider": "openrouter",
        "model_id": "openai/gpt-5-nano",
        "api_key_env": "OPENROUTER_API_KEY",
        "dependency_class": "proxy",
        "economic_surface": "openrouter",
        "selection_basis": "lowest_estimated_cost_within_allowed_tier_band_after_readiness",
        "pricing": {"input_1m_usd": 1.0, "output_1m_usd": 4.0},
        "legacy_route_changed": True,
    }

    monkeypatch.setattr(
        "lib.prescan.engine.build_provider_model_catalog",
        lambda config: {"routes": [selected_candidate]},
    )
    monkeypatch.setattr(
        "lib.prescan.engine.build_provider_readiness_matrix",
        lambda config, catalog: {
            "status": "PASS",
            "routes": [
                {
                    "provider": "openrouter",
                    "model_id": "openai/gpt-5-nano",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "ready": True,
                    "exclusion_reason": None,
                }
            ],
        },
    )
    monkeypatch.setattr(
        "lib.prescan.engine.build_prescan_routing_plan",
        lambda config, catalog, readiness, passes: {
            "requested_passes": ["dedup"],
            "status": "PASS",
            "halt_before_stage_1": False,
            "failures": [],
            "candidate_routes": {"dedup": [selected_candidate]},
            "selected_routes": {"dedup": selected_route},
            "fallback_decisions": {"dedup": []},
            "provider_readiness_status": "PASS",
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_call_grok(self, pass_id, payload, candidate, attempt):
        assert candidate["provider"] == "openrouter"
        assert candidate["model_id"] == "openai/gpt-5-nano"
        return {"duplicate_assessments": []}

    monkeypatch.setattr("lib.prescan.grok_passes.GrokPassRunner._call_grok", fake_call_grok)

    result = engine.run(passes=["dedup"])

    assert result.success is True
    assert result.metadata["stage0"]["routing_plan_status"] == "PASS"
    success_artifact = output_dir / "prescan_live_lane_success.json"
    assert success_artifact.exists()
    assert not (output_dir / "prescan_no_live_lane.json").exists()
    payload = json.loads(success_artifact.read_text(encoding="utf-8"))
    assert payload["status"] == "LIVE_LANE_READY"
    assert payload["selected_routes"]["dedup"]["provider"] == "openrouter"
    attempts = json.loads((output_dir / "prescan_llm_attempts.json").read_text(encoding="utf-8"))
    assert attempts["evidence"][0]["attempts"][0]["provider"] == "openrouter"


def test_no_live_lane_halts_before_stage_1_and_writes_halt_artifact(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "out"
    engine = PrescanEngine(_make_config(repo, output_dir))

    monkeypatch.setattr(
        "lib.prescan.engine.build_provider_model_catalog",
        lambda config: {"routes": []},
    )
    monkeypatch.setattr(
        "lib.prescan.engine.build_provider_readiness_matrix",
        lambda config, catalog: {"status": "FAIL", "routes": [], "failed_blocker_codes": ["ONLINE_LLM_NOT_AUTHORIZED"]},
    )
    monkeypatch.setattr(
        "lib.prescan.engine.build_prescan_routing_plan",
        lambda config, catalog, readiness, passes: {
            "requested_passes": ["dedup"],
            "status": NO_LIVE_LANE,
            "halt_before_stage_1": True,
            "failures": [{"pass_id": "dedup", "required_tier": "cheap_structured", "reason": "no_executable_route_after_provider_readiness"}],
            "candidate_routes": {},
            "selected_routes": {},
            "fallback_decisions": {},
            "provider_readiness_status": "FAIL",
        },
    )

    called = {"value": False}

    def fake_call_grok(self, pass_id, payload, candidate, attempt):
        called["value"] = True
        return {"duplicate_assessments": []}

    monkeypatch.setattr("lib.prescan.grok_passes.GrokPassRunner._call_grok", fake_call_grok)

    result = engine.run(passes=["dedup"])

    assert result.success is False
    assert called["value"] is False
    halt_artifact = output_dir / "prescan_no_live_lane.json"
    assert halt_artifact.exists()
    assert not (output_dir / "prescan_live_lane_success.json").exists()
    payload = json.loads(halt_artifact.read_text(encoding="utf-8"))
    assert payload["status"] == NO_LIVE_LANE
    assert payload["halt_before_stage_1"] is True
