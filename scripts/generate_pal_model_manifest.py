#!/usr/bin/env python3
"""Generate deterministic PAL manifests from Dopemux catalog inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dopemux.model_catalog import build_pal_manifest, render_pal_manifest  # noqa: E402


DEFAULT_OUTPUT_DIR = (
    ROOT / "docker/mcp-servers-source/pal/pal-mcp-server/conf"
)


def expected_outputs() -> dict[str, bytes]:
    routing = yaml.safe_load((ROOT / "templates/routing.yaml").read_text(encoding="utf-8"))
    snapshot = json.loads(
        (ROOT / "config/cheaperinference_models.snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    direct = render_pal_manifest(
        build_pal_manifest(routing, snapshot, projection="direct-ci")
    )
    compatibility = render_pal_manifest(
        build_pal_manifest(routing, snapshot, projection="compatibility")
    )
    gateway = render_pal_manifest(
        build_pal_manifest(routing, snapshot, projection="gateway")
    )
    return {
        "custom_models.json": compatibility,
        "custom_models.direct-ci.json": direct,
        "custom_models.gateway.json": gateway,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    stale: list[str] = []
    outputs = expected_outputs()
    for filename, content in outputs.items():
        path = args.output_dir / filename
        if not path.exists() or path.read_bytes() != content:
            stale.append(str(path))

    if args.check:
        if stale:
            print("stale PAL manifest(s): " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        (args.output_dir / filename).write_bytes(content)
    print(f"wrote {len(outputs)} PAL manifests to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
