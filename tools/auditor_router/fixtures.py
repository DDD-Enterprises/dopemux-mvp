from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_fixture_probes(fixture_dir: Path) -> dict[str, Any]:
    probes_path = fixture_dir / "probes.json"
    if not probes_path.is_file():
        raise FileNotFoundError(f"Missing fixture probes.json: {probes_path}")
    payload = json.loads(probes_path.read_text(encoding="utf-8"))
    return {
        "direct_routes": list(payload.get("direct_routes") or []),
        "fallback_routes": list(payload.get("fallback_routes") or []),
    }


def clink_config_roots_for_fixture(fixture_dir: Path) -> list[Path]:
    return [fixture_dir / "clink_configs"]
