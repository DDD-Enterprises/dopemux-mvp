#!/usr/bin/env python3
"""Independent embedded-audit proof emitter.

This entrypoint is intended for the embedded-audit CI workflow. It normalizes a
captured PAL clink audit output into the canonical embedded_audit proof object
and records provenance without serializing token values.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.audit.pal_clink_runner import _render_audit_report
from tools.auditor_router.pal_clink import normalize_pal_clink_audit_output


TOKEN_ENV_VAR = "EMBEDDED_AUDIT_TOKEN"
PROOF_AUTHOR = "independent-embedded-audit"


def _utc_now_seconds() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_embedded_audit_proof(
    *,
    packet_id: str,
    repo: str,
    pr_number: int,
    head_sha: str,
    route: Mapping[str, Any],
    pal_output: Mapping[str, Any] | None,
    token_present: bool,
    token_source: str,
    route_error: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a top-level proof bundle with canonical embedded_audit object."""
    report_path = f"proof/{packet_id}/AUDITOR_REPORT.md"
    if route_error:
        embedded_audit = _skipped_audit(
            report_path=report_path,
            reason=(
                "Independent embedded audit skipped because auditor route JSON "
                f"is missing or invalid: {route_error}"
            ),
        )
        trusted_token_status = "AVAILABLE" if token_present else "UNKNOWN"
    elif not token_present:
        embedded_audit = _skipped_audit(
            report_path=report_path,
            reason=(
                "Independent embedded audit skipped because the separate "
                "least-privilege token is unavailable or UNKNOWN."
            ),
        )
        trusted_token_status = "UNKNOWN"
    elif pal_output is None:
        embedded_audit = _skipped_audit(
            report_path=report_path,
            reason=(
                "Independent embedded audit skipped because PAL clink output "
                "is missing."
            ),
        )
        trusted_token_status = "AVAILABLE"
    else:
        embedded_audit = normalize_pal_clink_audit_output(
            dict(pal_output),
            route=dict(route),
            report_path=report_path,
        )
        trusted_token_status = "AVAILABLE"

    return {
        "packet_id": packet_id,
        "repo": repo,
        "pr_number": int(pr_number),
        "head_sha": head_sha,
        "generated_at": generated_at or _utc_now_seconds(),
        "mutation_performed": False,
        "github_mutation_route_added": False,
        "embedded_audit": embedded_audit,
        "provenance": {
            "proof_author": PROOF_AUTHOR,
            "workflow": "embedded-audit.yml",
            "trusted_token_status": trusted_token_status,
            "token_source": token_source,
            "token_value_recorded": False,
            "permissions": {
                "actions": "read",
                "checks": "read",
                "contents": "read",
                "pull-requests": "read",
                "statuses": "read",
            },
            "engine_authored_proof": False,
            "engine_requested_only": True,
        },
    }


def _skipped_audit(*, report_path: str, reason: str) -> dict[str, Any]:
    return {
        "required": True,
        "status": "SKIPPED",
        "auditor_tool": "none",
        "auditor_model": "unknown",
        "invocation": None,
        "exit_code": None,
        "report_path": report_path,
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [reason],
        "skip_reason": reason,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit an independent embedded-audit PROOF.json artifact."
    )
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--route-json", required=True, type=Path)
    parser.add_argument("--pal-output-json", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--generated-at")
    return parser


def run_cli(
    argv: list[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    environ = os.environ if env is None else env
    route, route_error = _read_optional_json_object(args.route_json)
    pal_output = (
        _read_json_object(args.pal_output_json) if args.pal_output_json else None
    )
    proof = build_embedded_audit_proof(
        packet_id=args.packet_id,
        repo=args.repo,
        pr_number=args.pr,
        head_sha=args.head_sha,
        route=route,
        pal_output=pal_output,
        token_present=bool(environ.get(TOKEN_ENV_VAR)),
        token_source=TOKEN_ENV_VAR,
        route_error=route_error,
        generated_at=args.generated_at,
    )
    _write_outputs(args.out, proof)
    return 0


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _read_optional_json_object(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        return _read_json_object(path), None
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        return {}, str(exc)


def _write_outputs(out_dir: Path, proof: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "PROOF.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path = Path(proof["embedded_audit"]["report_path"])
    report_file = out_dir / report_path
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_text = _render_audit_report(proof["embedded_audit"])
    report_file.write_text(report_text, encoding="utf-8")
    root_report_file = out_dir / "AUDITOR_REPORT.md"
    if root_report_file != report_file:
        root_report_file.write_text(report_text, encoding="utf-8")


def main() -> int:
    try:
        return run_cli()
    except Exception as exc:
        print(f"run_embedded_audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
