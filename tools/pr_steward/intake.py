from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .classifier import build_artifacts
from .collector import collect_from_github, load_fixture


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-steward",
        description="Check-only PR Steward review intake.",
    )
    parser.add_argument("--repo", required=True, help="GitHub repository owner/name.")
    parser.add_argument("--pr", required=True, type=int, help="Pull request number.")
    parser.add_argument("--out", required=True, type=Path, help="Output directory.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require final CI/check state before READY.",
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="Offline fixture directory containing harvest.json.",
    )
    parser.add_argument(
        "--proof-path",
        type=Path,
        help="Proof JSON path used in live mode to verify audit status and PR head SHA.",
    )
    parser.add_argument(
        "--allow-closed",
        action="store_true",
        help="Allow closed or merged PRs to be reported without PR_CLOSED blocker.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Print JSON readiness or text summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        harvest = (
            load_fixture(args.fixture_dir)
            if args.fixture_dir
            else collect_from_github(args.repo, args.pr, proof_path=args.proof_path)
        )
        artifacts = build_artifacts(
            harvest,
            repo=args.repo,
            pr_number=args.pr,
            strict=args.strict,
            allow_closed=args.allow_closed,
        )
        write_artifacts(args.out, artifacts)
    except Exception as exc:
        print(f"pr-steward failed: {exc}", file=sys.stderr)
        return 2

    readiness = artifacts["MERGE_READINESS.json"]
    if not isinstance(readiness, dict):
        print("pr-steward failed: invalid readiness artifact", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(readiness, indent=2, sort_keys=True))
    else:
        print(artifacts["PR_STEWARD_SUMMARY.md"])
    if readiness.get("readiness") != "READY":
        return 2
    return 0


def write_artifacts(out_dir: Path, artifacts: dict[str, dict[str, Any] | str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in artifacts.items():
        path = out_dir / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    raise SystemExit(main())
