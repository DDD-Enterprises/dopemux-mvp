from __future__ import annotations

import importlib
import inspect
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

from .models import ProjectExtensionAdapter, SourceSnapshot

_ADAPTER_NAMESPACE = "dopemux.repository_planner.adapters."
_MANIFEST_SCHEMA = (
    Path(__file__).parents[3]
    / "schemas"
    / "project_control_plane"
    / "extension_manifest.schema.json"
)


@dataclass(frozen=True, slots=True)
class _ValidatedAdapter:
    extension_id: str
    delegate: object

    def matches(self, generic_export) -> bool:
        result = self.delegate.matches(generic_export)  # type: ignore[attr-defined]
        if not isinstance(result, bool):
            raise ValueError("adapter matches must return bool")
        return result

    def enrich(self, generic_export, source_root: Path) -> SourceSnapshot:
        result = self.delegate.enrich(generic_export, source_root)  # type: ignore[attr-defined]
        if not isinstance(result, SourceSnapshot):
            raise ValueError("adapter enrich must return SourceSnapshot")
        return SourceSnapshot(
            schema_version=result.schema_version,
            project_id=result.project_id,
            authority=result.authority,
            surface_class=result.surface_class,
            is_proof=result.is_proof,
            evidence_class=result.evidence_class,
            observed_head=result.observed_head,
            fetched_at=result.fetched_at,
            freshness=result.freshness,
            claims=result.claims,
            lanes=result.lanes,
        )


def _validate_method(
    adapter: object, name: str, parameter_names: tuple[str, ...]
) -> None:
    method = getattr(adapter, name, None)
    if not callable(method):
        raise ValueError(f"adapter {name} signature is invalid")
    parameters = tuple(inspect.signature(method).parameters.values())
    if len(parameters) != len(parameter_names) or any(
        parameter.name != expected
        or parameter.kind
        not in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
        or parameter.default is not inspect.Parameter.empty
        for parameter, expected in zip(parameters, parameter_names)
    ):
        raise ValueError(f"adapter {name} signature is invalid")


def load_extension_adapters(
    manifest_paths: Sequence[Path],
) -> tuple[ProjectExtensionAdapter, ...]:
    """Load one additive adapter per manifest and reject ambiguous mappings."""

    adapters: list[ProjectExtensionAdapter] = []
    seen: set[str] = set()
    try:
        schema = json.loads(_MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("extension manifest schema is unavailable") from exc
    validator = Draft202012Validator(schema)
    for manifest_path in manifest_paths:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            errors = sorted(
                validator.iter_errors(manifest), key=lambda error: list(error.path)
            )
            if errors:
                raise ValueError(
                    f"manifest schema validation failed: {errors[0].message}"
                )
            extension_id = manifest["extension_id"]
            mappings = manifest["capabilities"]["adapter_mappings"]
        except ValueError:
            raise
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"invalid extension manifest: {manifest_path}") from exc
        if not isinstance(extension_id, str) or not extension_id:
            raise ValueError("extension_id must be a non-empty string")
        if extension_id in seen:
            raise ValueError(f"duplicate extension_id: {extension_id}")
        if not isinstance(mappings, list) or len(mappings) != 1:
            raise ValueError("adapter_mappings must contain exactly one mapping")
        mapping = mappings[0]
        if not isinstance(mapping, str) or mapping.count(":") != 1:
            raise ValueError("adapter mapping must use module:Class")
        module_name, class_name = mapping.split(":", 1)
        if not module_name.startswith(_ADAPTER_NAMESPACE):
            raise ValueError(
                f"adapter module is outside closed namespace: {module_name}"
            )
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise ValueError(f"cannot import adapter module: {module_name}") from exc
        adapter_class = getattr(module, class_name, None)
        if not isinstance(adapter_class, type):
            raise ValueError(f"adapter class does not exist: {mapping}")
        adapter = adapter_class()
        if not isinstance(adapter, ProjectExtensionAdapter):
            raise ValueError(f"adapter class does not satisfy protocol: {mapping}")
        _validate_method(adapter, "matches", ("generic_export",))
        _validate_method(adapter, "enrich", ("generic_export", "source_root"))
        if adapter.extension_id != extension_id:
            raise ValueError("adapter extension_id does not match manifest")
        seen.add(extension_id)
        adapters.append(
            cast(ProjectExtensionAdapter, _ValidatedAdapter(extension_id, adapter))
        )
    return tuple(
        sorted(adapters, key=lambda adapter: adapter.extension_id.encode("utf-8"))
    )
