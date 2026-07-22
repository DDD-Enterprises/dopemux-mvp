from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "container_matrix.py"
SPEC = importlib.util.spec_from_file_location("container_matrix", SCRIPT)
assert SPEC and SPEC.loader
container_matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(container_matrix)


def test_checked_in_manifest_is_valid_and_paths_exist() -> None:
    manifest = container_matrix.load_manifest()
    container_matrix.validate_manifest(manifest)

    assert manifest["registry"] == "ghcr.io/ddd-enterprises/dopemux-mvp"
    assert manifest["platform"] == "linux/amd64"
    assert len(manifest["targets"]) >= 15


def test_matrix_preserves_publish_and_smoke_metadata() -> None:
    manifest = container_matrix.load_manifest()
    matrix = container_matrix.matrix_payload(manifest)
    entries = {entry["service"]: entry for entry in matrix["include"]}

    assert set(entries) == {target["service"] for target in manifest["targets"]}
    assert entries["dope-memory"]["smoke_test"] is True
    assert entries["dope-memory"]["smoke_port"] == "3020"
    assert entries["dopemux-backend"]["classification"] == "legacy-compatibility"
    assert all(entry["platform"] == "linux/amd64" for entry in entries.values())


def test_compose_alignment_accepts_every_declared_build_service() -> None:
    manifest = container_matrix.load_manifest()
    services = {}
    for target in manifest["targets"]:
        compose_context = target.get("compose_context", target["context"])
        compose_dockerfile = target.get("compose_dockerfile", target["dockerfile"])
        for compose_service in target["compose_services"]:
            services[compose_service] = {
                "build": {
                    "context": str((ROOT / compose_context).resolve()),
                    "dockerfile": str((ROOT / compose_dockerfile).resolve()),
                }
            }

    container_matrix.validate_compose_alignment(manifest, {"services": services})


def test_known_compose_wrapper_drift_is_explicit() -> None:
    manifest = container_matrix.load_manifest()

    assert container_matrix.compose_drift_targets(manifest) == ["conport", "litellm"]


def test_compose_alignment_fails_closed_on_unmapped_build_service() -> None:
    manifest = container_matrix.load_manifest()
    config = {
        "services": {
            "unknown-builder": {
                "build": {
                    "context": str(ROOT),
                    "dockerfile": str(ROOT / "Dockerfile"),
                }
            }
        }
    }

    with pytest.raises(container_matrix.ManifestError, match="missing from manifest"):
        container_matrix.validate_compose_alignment(manifest, config)


def test_manifest_rejects_duplicate_compose_ownership() -> None:
    manifest = container_matrix.load_manifest()
    duplicate = {
        **manifest,
        "targets": [dict(target) for target in manifest["targets"]],
    }
    duplicate["targets"][0] = {
        **duplicate["targets"][0],
        "compose_services": ["conport"],
    }

    with pytest.raises(container_matrix.ManifestError, match="mapped more than once"):
        container_matrix.validate_manifest(duplicate, check_paths=False)
