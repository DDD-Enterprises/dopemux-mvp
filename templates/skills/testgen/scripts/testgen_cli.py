#!/usr/bin/env python3
"""CLI wrapper for deterministic testgen workflow planning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from testgen_workflow import (
    CoverageResolutionError,
    ScopeResolutionError,
    TestgenRequest,
    ToolAvailability,
    ToolingResolutionError,
    generate_testgen_plan,
)


def _load_text_payload(payload: Optional[str], payload_file: Optional[str]) -> str:
    if payload and payload_file:
        raise ValueError("Provide either --payload or --payload-file, not both")
    if payload_file:
        return Path(payload_file).read_text(encoding="utf-8")
    if payload:
        return payload
    raise ValueError("Missing payload; provide --payload or --payload-file")


def _load_json_list(raw: Optional[str]) -> Optional[List[str]]:
    if raw is None:
        return None
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("JSON list expected")
    return [str(item) for item in data]


def _load_tool_matrix(raw: Optional[str]) -> ToolAvailability:
    if raw is None:
        return ToolAvailability()
    matrix: Dict[str, Any] = json.loads(raw)
    return ToolAvailability.from_dict(matrix)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic testgen workflow plans")
    parser.add_argument("--mode", required=True, choices=["tdd-driver", "post-impl-generator"])
    parser.add_argument("--source", required=True, choices=["feature-list", "task-packet"])
    parser.add_argument("--payload")
    parser.add_argument("--payload-file")
    parser.add_argument("--coverage-target", type=int, default=90)
    parser.add_argument("--preferred-cli", default="auto", choices=["auto", "gemini", "copilot", "claude"])
    parser.add_argument("--use-pal-testgen", default="auto", choices=["auto", "on", "off"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--base-ref")
    parser.add_argument("--coverage-xml")
    parser.add_argument("--touched-file", action="append", default=[])
    parser.add_argument("--feature-file-map-json")
    parser.add_argument("--tool-matrix-json")
    parser.add_argument("--strict-reasoning-tools", action="store_true")
    parser.add_argument("--out")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        payload = _load_text_payload(args.payload, args.payload_file)
        feature_file_map = _load_json_list(args.feature_file_map_json)
        tool_availability = _load_tool_matrix(args.tool_matrix_json)

        request = TestgenRequest(
            mode=args.mode,
            source=args.source,
            payload=payload,
            coverage_target=args.coverage_target,
            preferred_cli=args.preferred_cli,
            use_pal_testgen=args.use_pal_testgen,
        )

        report = generate_testgen_plan(
            request=request,
            repo_root=Path(args.repo_root).resolve(),
            tool_availability=tool_availability,
            coverage_xml=Path(args.coverage_xml).resolve() if args.coverage_xml else None,
            explicit_touched=args.touched_file,
            base_ref=args.base_ref,
            feature_file_map=feature_file_map,
            allow_local_reasoning_fallback=not args.strict_reasoning_tools,
        )

        output = json.dumps(report, indent=2, sort_keys=True)
        if args.out:
            Path(args.out).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0

    except (ValueError, ScopeResolutionError, CoverageResolutionError, ToolingResolutionError, json.JSONDecodeError) as exc:
        error = {"status": "error", "error": str(exc)}
        print(json.dumps(error, indent=2, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
