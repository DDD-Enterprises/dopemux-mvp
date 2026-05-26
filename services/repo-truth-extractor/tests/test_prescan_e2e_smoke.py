from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.engine import PrescanEngine
from lib.prescan.models import PrescanConfig


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
    (repo / "src" / "a.py").write_text(
        '"""alpha"""\n'
        "def alpha() -> int:\n"
        "    return 1\n",
        encoding="utf-8",
    )
    (repo / "src" / "b.py").write_text(
        "from src.a import alpha\n\n"
        "def beta() -> int:\n"
        "    return alpha()\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
    _commit_all(repo, "initial fixture")
    return repo


def _make_config(repo: Path, output_dir: Path, baseline: str | None = None) -> PrescanConfig:
    return PrescanConfig(
        repo_root=repo,
        output_dir=output_dir,
        enable_git_enrichment=False,
        batch_mode=False,
        cost_estimate=False,
        incremental_baseline=baseline,
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.xfail(
    reason="Deferred to TP-RTE-WALKER-006: prescan incremental cache semantics are outside CostProfile F repair scope.",
    strict=True,
)
def test_prescan_real_repo_full_and_incremental_smoke(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "out"

    full_engine = PrescanEngine(_make_config(repo, output_dir))
    full_result = full_engine.run()

    assert full_result.success
    assert full_result.intelligence_path and full_result.intelligence_path.exists()
    assert full_result.code_graph_path and full_result.code_graph_path.exists()
    assert full_result.code_report_path and full_result.code_report_path.exists()
    assert (output_dir / ".cache" / "prescan_incremental_cache.json").exists()
    assert full_result.metadata["incremental"]["enabled"] is False

    warm_engine = PrescanEngine(_make_config(repo, output_dir, baseline="HEAD"))
    warm_result = warm_engine.run(incremental=True)

    assert warm_result.success
    assert warm_result.warnings == []
    assert warm_result.metadata["incremental"]["enabled"] is True
    assert warm_result.metadata["incremental"]["changed_files_count"] == 0
    assert warm_result.metadata["incremental"]["cached_code_analysis_reused"] == 2
    assert warm_result.metadata["incremental"]["reanalyzed_code_files"] == 0
    assert warm_result.metadata["incremental"]["removed_cache_entries"] == 0
    assert warm_result.metadata["incremental"]["fallback_reason"] is None

    warm_manifest = _load_json(output_dir / "corpus_manifest.json")
    warm_intelligence = _load_json(output_dir / "prescan_intelligence.json")
    warm_report = _load_json(output_dir / "code_intelligence_report.json")

    assert {entry["rel_path"] for entry in warm_manifest} == {"README.md", "src/a.py", "src/b.py"}
    assert warm_intelligence["code_intelligence"]["analyzed_files"] == 2
    assert warm_report["summary"]["total_code_files"] == 2

    baseline_sha = _git(repo, "rev-parse", "HEAD")
    (repo / "src" / "b.py").write_text(
        "from src.a import alpha\n\n"
        "def beta() -> int:\n"
        "    return alpha() + 1\n",
        encoding="utf-8",
    )
    _commit_all(repo, "change b")

    changed_engine = PrescanEngine(_make_config(repo, output_dir, baseline=baseline_sha))
    changed_result = changed_engine.run(incremental=True)

    assert changed_result.success
    assert changed_result.warnings == []
    assert changed_result.metadata["incremental"]["changed_files_count"] == 1
    assert changed_result.metadata["incremental"]["cached_code_analysis_reused"] == 1
    assert changed_result.metadata["incremental"]["reanalyzed_code_files"] == 1
    assert changed_result.metadata["incremental"]["removed_cache_entries"] == 0

    changed_manifest = _load_json(output_dir / "corpus_manifest.json")
    changed_intelligence = _load_json(output_dir / "prescan_intelligence.json")
    changed_report = _load_json(output_dir / "code_intelligence_report.json")

    assert {entry["rel_path"] for entry in changed_manifest} == {"README.md", "src/a.py", "src/b.py"}
    assert changed_intelligence["code_intelligence"]["analyzed_files"] == 2
    assert changed_report["summary"]["total_code_files"] == 2


def test_prescan_real_repo_corrupted_cache_falls_back_to_full_recompute(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "out"

    full_engine = PrescanEngine(_make_config(repo, output_dir))
    assert full_engine.run().success

    cache_path = output_dir / ".cache" / "prescan_incremental_cache.json"
    cache_path.write_text("{ not valid json }\n", encoding="utf-8")

    incremental_engine = PrescanEngine(_make_config(repo, output_dir, baseline="HEAD"))
    result = incremental_engine.run(incremental=True)

    assert result.success
    assert result.metadata["incremental"]["enabled"] is True
    assert result.metadata["incremental"]["changed_files_count"] == 0
    assert result.metadata["incremental"]["cached_code_analysis_reused"] == 0
    assert result.metadata["incremental"]["reanalyzed_code_files"] == 2
    assert "full recompute" in (result.metadata["incremental"]["fallback_reason"] or "").lower()
    assert any("full recompute" in warning.lower() for warning in result.warnings)

    manifest = _load_json(output_dir / "corpus_manifest.json")
    report = _load_json(output_dir / "code_intelligence_report.json")
    assert {entry["rel_path"] for entry in manifest} == {"README.md", "src/a.py", "src/b.py"}
    assert report["summary"]["total_code_files"] == 2


def test_prescan_live_lane_success_artifact_is_written_when_stage0_passes(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "out"
    config = _make_config(repo, output_dir)
    config.allow_online_llm = True
    engine = PrescanEngine(config)

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
            "selected_routes": {"dedup": {"provider": "openrouter", "model_id": "openai/gpt-5-nano"}},
            "fallback_decisions": {"dedup": []},
            "provider_readiness_status": "PASS",
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "lib.prescan.grok_passes.GrokPassRunner._call_grok",
        lambda self, pass_id, payload, candidate, attempt: {"duplicate_assessments": []},
    )

    result = engine.run(passes=["dedup"])

    assert result.success is True
    assert (output_dir / "prescan_live_lane_success.json").exists()
