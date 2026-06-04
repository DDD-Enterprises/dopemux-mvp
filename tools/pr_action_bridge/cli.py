"""Read-only filesystem CLI for the PR Action Bridge compiler."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import sys
from pathlib import Path
from typing import Any

from .compiler import compile_action_plan


REQUIRED_ARTIFACTS = {
    "merge_readiness": "MERGE_READINESS.json",
    "review_ledger": "REVIEW_ITEM_LEDGER.json",
    "thread_dispositions": "THREAD_DISPOSITIONS.json",
    "ci_triage": "CI_TRIAGE.json",
}


class CliError(RuntimeError):
    """Expected CLI failure that should return a non-zero exit code."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-action-bridge",
        description=(
            "Compile PR Steward artifacts into ACTION_PLAN.json and "
            "REPAIR_PACKET.md without mutating GitHub."
        ),
    )
    parser.add_argument(
        "--artifact-dir",
        required=True,
        type=Path,
        help="Directory containing PR Steward JSON artifacts.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory for ACTION_PLAN.json and REPAIR_PACKET.md.",
    )
    parser.add_argument(
        "--generated-at",
        help="Optional ISO 8601 timestamp for deterministic output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_generated_at(args.generated_at)
        artifacts = load_artifacts(args.artifact_dir)
        action_plan, repair_packet = compile_action_plan(
            artifacts["merge_readiness"],
            artifacts["review_ledger"],
            artifacts["thread_dispositions"],
            artifacts["ci_triage"],
            generated_at=args.generated_at,
        )
        write_outputs(args.out, action_plan, repair_packet)
    except Exception as exc:
        print(f"pr-action-bridge failed: {exc}", file=sys.stderr)
        return 2

    print(f"wrote {args.out / 'ACTION_PLAN.json'}")
    print(f"wrote {args.out / 'REPAIR_PACKET.md'}")
    return 0


def validate_generated_at(generated_at: str | None) -> None:
    if generated_at is None:
        return
    if "T" not in generated_at:
        raise CliError("--generated-at must be an ISO 8601 timestamp")
    value = generated_at[:-1] + "+00:00" if generated_at.endswith("Z") else generated_at
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise CliError("--generated-at must be an ISO 8601 timestamp") from exc


def load_artifacts(artifact_dir: Path) -> dict[str, dict[str, Any]]:
    if not artifact_dir.is_dir():
        raise CliError(f"artifact directory not found: {artifact_dir}")

    artifacts: dict[str, dict[str, Any]] = {}
    for key, filename in REQUIRED_ARTIFACTS.items():
        path = artifact_dir / filename
        if not path.is_file():
            raise CliError(f"required artifact missing: {filename}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CliError(f"invalid JSON in {filename}: {exc}") from exc
        if not isinstance(payload, dict):
            raise CliError(f"artifact must be a JSON object: {filename}")
        artifacts[key] = payload
    return artifacts


def write_outputs(
    out_dir: Path,
    action_plan: dict[str, Any],
    repair_packet: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ACTION_PLAN.json").write_text(
        json.dumps(action_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "REPAIR_PACKET.md").write_text(repair_packet, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
