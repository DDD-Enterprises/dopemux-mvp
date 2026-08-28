import json
from pathlib import Path

import yaml

from dopemux.model_catalog import build_pal_manifest, render_pal_manifest


ROOT = Path(__file__).resolve().parents[1]


def _catalog_inputs():
    routing = yaml.safe_load((ROOT / "templates/routing.yaml").read_text(encoding="utf-8"))
    snapshot = json.loads(
        (ROOT / "config/cheaperinference_models.snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    return routing, snapshot


def test_direct_ci_projection_uses_provider_model_ids_and_verified_capabilities():
    routing, snapshot = _catalog_inputs()

    manifest = build_pal_manifest(routing, snapshot, projection="direct-ci")
    models = {entry["model_name"]: entry for entry in manifest["models"]}

    assert "kimi-k3" in models
    assert "claude-fable-5" in models
    assert "kimi-k3-ci" not in models
    assert models["kimi-k3"]["context_window"] == 1_000_000
    assert models["kimi-k3"]["supports_extended_thinking"] is True
    assert "low/high/max" in models["kimi-k3"]["description"]
    assert models["claude-fable-5"]["context_window"] == 1_000_000
    assert models["claude-fable-5"]["max_output_tokens"] == 128_000
    assert "adaptive thinking always on" in models["claude-fable-5"]["description"].lower()


def test_gateway_projection_uses_active_qualified_routes_only():
    routing, snapshot = _catalog_inputs()

    manifest = build_pal_manifest(routing, snapshot, projection="gateway")
    names = {entry["model_name"] for entry in manifest["models"]}

    assert {"kimi-k3-ci", "fable-5-ci"} <= names
    assert not {
        "kimi-k3-or",
        "fable-5-or",
        "kimi-k3-direct",
        "fable-5-direct",
    } & names


def test_packaged_compatibility_projection_preserves_local_pal_entry():
    routing, snapshot = _catalog_inputs()

    manifest = build_pal_manifest(routing, snapshot, projection="compatibility")
    models = {entry["model_name"]: entry for entry in manifest["models"]}

    assert models["llama3.2"]["aliases"] == ["local-llama", "ollama-llama"]
    assert "llama3.2" not in {
        entry["model_name"]
        for entry in build_pal_manifest(
            routing, snapshot, projection="direct-ci"
        )["models"]
    }


def test_pal_manifest_render_is_deterministic_and_excludes_identity_noise():
    routing, snapshot = _catalog_inputs()
    manifest = build_pal_manifest(routing, snapshot, projection="direct-ci")

    first = render_pal_manifest(manifest)
    second = render_pal_manifest(manifest)

    assert first == second
    assert b"pricing" not in first
    assert b"api_key" not in first
    assert b"reasoning_efforts" not in first
