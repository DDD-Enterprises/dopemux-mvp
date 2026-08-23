from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.repository_planner.extensions import load_extension_adapters


def _write_module(root: Path, *, class_name: str = "Adapter") -> None:
    (root / "fixture_adapter.py").write_text(
        "\n".join(
            [
                "class Adapter:",
                "    extension_id = 'fixture-extension'",
                "    def matches(self, generic_export): return True",
                "    def enrich(self, generic_export, source_root): return generic_export",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_manifest(path: Path, mapping: str, *, extension_id: str = "fixture-extension") -> None:
    path.write_text(
        json.dumps(
            {
                "extension_id": extension_id,
                "capabilities": {"adapter_mappings": [mapping]},
            }
        ),
        encoding="utf-8",
    )


def test_loads_real_adapter_from_manifest_mapping(tmp_path: Path, monkeypatch) -> None:
    _write_module(tmp_path)
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, "fixture_adapter:Adapter")
    monkeypatch.syspath_prepend(str(tmp_path))

    adapters = load_extension_adapters([manifest])

    assert len(adapters) == 1
    assert adapters[0].extension_id == "fixture-extension"
    assert adapters[0].matches({}) is True


def test_unknown_adapter_module_fails_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, "module_that_does_not_exist:Adapter")
    with pytest.raises(ValueError, match="cannot import adapter module"):
        load_extension_adapters([manifest])


def test_duplicate_extension_ids_fail_closed(tmp_path: Path, monkeypatch) -> None:
    _write_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_manifest(first, "fixture_adapter:Adapter")
    _write_manifest(second, "fixture_adapter:Adapter")

    with pytest.raises(ValueError, match="duplicate extension_id"):
        load_extension_adapters([first, second])


def test_unknown_adapter_class_fails_closed(tmp_path: Path, monkeypatch) -> None:
    _write_module(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, "fixture_adapter:Missing")
    with pytest.raises(ValueError, match="adapter class"):
        load_extension_adapters([manifest])
