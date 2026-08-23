from __future__ import annotations

import importlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from .models import ProjectExtensionAdapter


def load_extension_adapters(
    manifest_paths: Sequence[Path],
) -> tuple[ProjectExtensionAdapter, ...]:
    """Load one additive adapter per manifest and reject ambiguous mappings."""

    adapters: list[ProjectExtensionAdapter] = []
    seen: set[str] = set()
    for manifest_path in manifest_paths:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            extension_id = manifest["extension_id"]
            mappings = manifest["capabilities"]["adapter_mappings"]
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
        if adapter.extension_id != extension_id:
            raise ValueError("adapter extension_id does not match manifest")
        seen.add(extension_id)
        adapters.append(cast(ProjectExtensionAdapter, adapter))
    return tuple(adapters)
