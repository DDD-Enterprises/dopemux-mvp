from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .fixtures import clink_config_roots_for_fixture, load_fixture_probes
from .models import normalize_route_record
from .pal_clink import classify_pal_clink_route
from .policy import select_preferred_route


DEFAULT_DIRECT_ROUTES = [
    {
        "tool": "agy",
        "status": "NEEDS_SUPERVISOR",
        "risk": "MEDIUM",
        "reason": "Direct CLI probing is not executed by this PAL clink router packet.",
    },
    {
        "tool": "claude-code-cli",
        "status": "NEEDS_SUPERVISOR",
        "risk": "MEDIUM",
        "reason": "Direct CLI probing is not executed by this PAL clink router packet.",
    },
    {
        "tool": "gemini-cli",
        "status": "NEEDS_SUPERVISOR",
        "risk": "MEDIUM",
        "reason": "Direct CLI probing is not executed by this PAL clink router packet.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auditor-preflight",
        description="Static embedded auditor route preflight.",
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="Offline fixture directory containing probes.json and clink_configs/.",
    )
    parser.add_argument("--out", required=True, type=Path, help="Output directory.")
    parser.add_argument("--packet-id", required=True, help="Task packet id.")
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="Allow explicit Copilot no-tools fallback when no better route exists.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Print selected route as JSON or a short text summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        route, probes = build_route_artifacts(
            fixture_dir=args.fixture_dir,
            packet_id=args.packet_id,
            allow_fallback=args.allow_fallback,
            repo_root=Path.cwd(),
        )
        write_artifacts(args.out, route, probes)
    except Exception as exc:
        print(f"auditor-preflight failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(route, indent=2, sort_keys=True))
    else:
        print(f"{route['tool']} {route['status']}: {route['reason']}")
    return 0 if route.get("status") in {"AVAILABLE", "AVAILABLE_WITH_RISKS"} else 2


def build_route_artifacts(
    *,
    fixture_dir: Path | None,
    packet_id: str,
    allow_fallback: bool,
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if fixture_dir:
        fixture = load_fixture_probes(fixture_dir)
        direct_routes = fixture["direct_routes"]
        fallback_routes = fixture["fallback_routes"]
        config_roots = clink_config_roots_for_fixture(fixture_dir)
    else:
        direct_routes = list(DEFAULT_DIRECT_ROUTES)
        fallback_routes: list[dict[str, Any]] = []
        config_roots = None

    pal_route = classify_pal_clink_route(repo_root=repo_root, config_roots=config_roots)
    selected = select_preferred_route(
        direct_routes=direct_routes,
        pal_routes=[pal_route],
        fallback_routes=fallback_routes,
        allow_fallback=allow_fallback,
    )
    route = normalize_route_record(selected)
    probes = {
        "packet_id": packet_id,
        "direct_routes": direct_routes,
        "pal_clink_routes": [pal_route],
        "fallback_routes": fallback_routes,
        "selected_tool": route.get("tool"),
        "selected_status": route.get("status"),
        "repo_context_sent": False,
        "pal_mcp_called": False,
        "external_cli_called_for_pal_clink": False,
    }
    return route, probes


def write_artifacts(
    out_dir: Path,
    route: dict[str, Any],
    probes: dict[str, Any],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "AUDITOR_ROUTE.json").write_text(
        json.dumps(route, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "ROUTE_PROBE_OUTPUTS.json").write_text(
        json.dumps(probes, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
