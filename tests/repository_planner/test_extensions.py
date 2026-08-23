from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from dopemux.repository_planner.extensions import load_extension_adapters
from dopemux.repository_planner.models import SourceSnapshot
from dopemux.repository_planner.snapshot import load_source_snapshot

FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "repository_planner"
    / "foundation"
    / "dopemux.json"
)


def _manifest(extension_id: str, mapping: str) -> dict[str, object]:
    return {
        "schema_version": "pcp.extension_manifest.v0",
        "extension_id": extension_id,
        "extension_kind": "PROJECT",
        "extension_identity": {
            "project_id_patterns": [],
            "repo_markers": [],
            "discovery_hints": [],
        },
        "capabilities": {
            "authority_map_contributions": [],
            "red_lane_contributions": [],
            "evidence_export_sections": [],
            "proof_status_mappings": [],
            "runtime_mappings": [],
            "adapter_mappings": [mapping],
        },
        "schemas": {
            "owned_schema_ids": [],
            "core_schema_extensions": [],
            "forbidden_core_overrides": [],
        },
        "invariants": {
            "cannot_override_core_fail_closed": True,
            "cannot_weaken_proof_gates": True,
            "cannot_weaken_audit_gates": True,
            "cannot_promote_adapter_to_authority": True,
            "cannot_require_extension_for_baseline_core": True,
        },
    }


def _write_manifest(path: Path, extension_id: str, mapping: str) -> None:
    path.write_text(json.dumps(_manifest(extension_id, mapping)), encoding="utf-8")


def _install_module(
    monkeypatch, module_name: str, extension_id: str, *, invalid_output: bool = False
) -> None:
    module = types.ModuleType(module_name)

    class Adapter:
        def __init__(self) -> None:
            self.extension_id = extension_id

        def matches(self, generic_export):
            return True

        def enrich(self, generic_export, source_root):
            return (
                generic_export
                if invalid_output
                else load_source_snapshot(generic_export)
            )

    module.Adapter = Adapter
    monkeypatch.setitem(sys.modules, module_name, module)


def test_validates_full_manifest_and_returns_source_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    module = "dopemux.repository_planner.adapters.fixture"
    _install_module(monkeypatch, module, "fixture-extension")
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, "fixture-extension", f"{module}:Adapter")

    adapter = load_extension_adapters([manifest])[0]
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert adapter.matches(payload) is True
    assert isinstance(adapter.enrich(payload, tmp_path), SourceSnapshot)


def test_manifest_schema_and_namespace_fail_closed(tmp_path: Path, monkeypatch) -> None:
    module = "dopemux.repository_planner.adapters.fixture"
    _install_module(monkeypatch, module, "fixture-extension")
    malformed = tmp_path / "malformed.json"
    malformed.write_text(
        json.dumps(
            {
                "extension_id": "fixture-extension",
                "capabilities": {"adapter_mappings": [f"{module}:Adapter"]},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="manifest schema"):
        load_extension_adapters([malformed])

    outside = tmp_path / "outside.json"
    _write_manifest(outside, "outside", "untrusted.module:Adapter")
    with pytest.raises(ValueError, match="namespace"):
        load_extension_adapters([outside])


def test_adapter_output_contract_fails_closed(tmp_path: Path, monkeypatch) -> None:
    module = "dopemux.repository_planner.adapters.invalid"
    _install_module(monkeypatch, module, "invalid", invalid_output=True)
    manifest = tmp_path / "invalid.json"
    _write_manifest(manifest, "invalid", f"{module}:Adapter")
    adapter = load_extension_adapters([manifest])[0]
    with pytest.raises(ValueError, match="SourceSnapshot"):
        adapter.enrich({}, tmp_path)


def test_duplicate_ids_and_input_order_are_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    for extension_id in ("alpha", "zeta"):
        module = f"dopemux.repository_planner.adapters.{extension_id}"
        _install_module(monkeypatch, module, extension_id)
        _write_manifest(
            tmp_path / f"{extension_id}.json", extension_id, f"{module}:Adapter"
        )

    adapters = load_extension_adapters(
        [tmp_path / "zeta.json", tmp_path / "alpha.json"]
    )
    assert [adapter.extension_id for adapter in adapters] == ["alpha", "zeta"]
    with pytest.raises(ValueError, match="duplicate extension_id"):
        load_extension_adapters([tmp_path / "alpha.json", tmp_path / "alpha.json"])


def test_unknown_adapter_module_and_class_fail_closed(
    tmp_path: Path, monkeypatch
) -> None:
    missing_module = tmp_path / "missing-module.json"
    _write_manifest(
        missing_module, "missing", "dopemux.repository_planner.adapters.missing:Adapter"
    )
    with pytest.raises(ValueError, match="cannot import adapter module"):
        load_extension_adapters([missing_module])

    module_name = "dopemux.repository_planner.adapters.no_class"
    monkeypatch.setitem(sys.modules, module_name, types.ModuleType(module_name))
    missing_class = tmp_path / "missing-class.json"
    _write_manifest(missing_class, "missing-class", f"{module_name}:Missing")
    with pytest.raises(ValueError, match="adapter class"):
        load_extension_adapters([missing_class])
