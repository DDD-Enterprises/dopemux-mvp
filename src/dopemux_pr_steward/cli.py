from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from dopemux_pr_merge_specialist.steward_gate import steward_gate

from . import CONTRACT_VERSION
from .doctor import format_result, run_doctor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dopemux-pr-steward",
        description="Versioned PR Steward command contract.",
    )
    parser.add_argument(
        "--contract-version",
        action="version",
        version=f"dopemux-pr-steward contract-version {CONTRACT_VERSION}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    intake = subparsers.add_parser("intake", help="Run check-only PR Steward intake.")
    intake.add_argument("--repo", required=True, help="GitHub repository owner/name.")
    intake.add_argument("--pr", required=True, type=int, help="Pull request number.")
    intake.add_argument("--out", required=True, type=Path, help="Output directory.")
    intake.add_argument(
        "--strict",
        action="store_true",
        help="Require final CI/check state before READY.",
    )
    intake.add_argument(
        "--fixture-dir",
        type=Path,
        help="Offline fixture directory containing harvest.json.",
    )
    intake.add_argument(
        "--proof-path",
        type=Path,
        help="Proof JSON path used in live mode to verify audit status and PR head SHA.",
    )
    intake.add_argument(
        "--allow-closed",
        action="store_true",
        help="Allow closed or merged PRs to be reported without PR_CLOSED blocker.",
    )
    intake.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Print JSON readiness or text summary.",
    )
    intake.set_defaults(handler=_run_intake)

    bridge = subparsers.add_parser(
        "bridge",
        help="Compile PR Steward artifacts into an action plan and repair packet.",
    )
    bridge.add_argument("--artifact-dir", required=True, type=Path)
    bridge.add_argument("--out", required=True, type=Path)
    bridge.set_defaults(handler=_run_bridge)

    gate = subparsers.add_parser(
        "gate",
        help="Evaluate packaged steward_gate over local artifacts.",
    )
    gate.add_argument("--head-sha", required=True)
    gate.add_argument(
        "--required-class",
        required=True,
        choices=["REMEDIATION", "FINALIZATION"],
    )
    gate.add_argument("--merge-readiness", required=True, type=Path)
    gate.add_argument("--audit-proof", required=True, type=Path)
    gate.add_argument("--ttl-seconds", default=3600, type=int)
    gate.add_argument("--now")
    gate.add_argument("--format", choices=["json", "text"], default="text")
    gate.set_defaults(handler=_run_gate)

    audit = subparsers.add_parser(
        "audit",
        help="Inspect embedded audit status in a proof bundle.",
    )
    audit.add_argument("--proof", required=True, type=Path)
    audit.add_argument("--format", choices=["json", "text"], default="text")
    audit.set_defaults(handler=_run_audit)

    doctor = subparsers.add_parser(
        "doctor",
        help="Run report-only PR Steward package/scaffold health checks.",
        description=(
            "Run report-only PR Steward package/scaffold health checks. "
            "No files are modified."
        ),
    )
    doctor.add_argument("--workspace", default=".", type=Path)
    doctor.add_argument("--schema", type=Path)
    doctor.add_argument("--format", choices=["json", "text"], default="text")
    doctor.set_defaults(handler=_run_doctor)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        return int(exc.code or 0)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return int(handler(args))


def _run_intake(args: argparse.Namespace) -> int:
    try:
        from tools.pr_steward.intake import main as intake_main
    except ModuleNotFoundError as exc:
        print(f"pr-steward intake unavailable: {exc}", file=sys.stderr)
        return 2
    forwarded = [
        "--repo",
        args.repo,
        "--pr",
        str(args.pr),
        "--out",
        str(args.out),
    ]
    if args.strict:
        forwarded.append("--strict")
    if args.fixture_dir is not None:
        forwarded.extend(["--fixture-dir", str(args.fixture_dir)])
    if args.proof_path is not None:
        forwarded.extend(["--proof-path", str(args.proof_path)])
    if args.allow_closed:
        forwarded.append("--allow-closed")
    forwarded.extend(["--format", args.format])
    return int(intake_main(forwarded))


def _run_bridge(args: argparse.Namespace) -> int:
    artifact_dir = args.artifact_dir
    out_dir = args.out
    try:
        from tools.pr_action_bridge.compiler import compile_action_plan

        merge_readiness = _load_json(artifact_dir / "MERGE_READINESS.json")
        review_ledger = _load_json(artifact_dir / "REVIEW_ITEM_LEDGER.json")
        thread_dispositions = _load_json(artifact_dir / "THREAD_DISPOSITIONS.json")
        ci_triage = _load_json(artifact_dir / "CI_TRIAGE.json")
        action_plan, repair_packet = compile_action_plan(
            merge_readiness,
            review_ledger,
            thread_dispositions,
            ci_triage,
        )
    except Exception as exc:
        print(f"pr-steward bridge failed: {exc}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ACTION_PLAN.json").write_text(
        json.dumps(action_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "REPAIR_PACKET.md").write_text(repair_packet, encoding="utf-8")
    print(f"Wrote {out_dir / 'ACTION_PLAN.json'}")
    print(f"Wrote {out_dir / 'REPAIR_PACKET.md'}")
    return 0


def _run_gate(args: argparse.Namespace) -> int:
    try:
        result = steward_gate(
            head_sha=args.head_sha,
            required_class=args.required_class,
            merge_readiness_path=args.merge_readiness,
            audit_proof_path=args.audit_proof,
            now=_parse_now(args.now),
            ttl_seconds=args.ttl_seconds,
        )
    except Exception as exc:
        print(f"pr-steward gate failed: {exc}", file=sys.stderr)
        return 2
    payload = {
        "allowed": result.allowed,
        "reason_code": result.reason_code,
        "required_class": result.required_class,
        "evidence": dict(result.evidence),
        "contract_version": CONTRACT_VERSION,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{payload['reason_code']} allowed={payload['allowed']}")
    return 0 if result.allowed else 2


def _run_audit(args: argparse.Namespace) -> int:
    try:
        proof = _load_json(args.proof)
    except Exception as exc:
        print(f"pr-steward audit failed: {exc}", file=sys.stderr)
        return 2
    audit = proof.get("embedded_audit")
    status = str(audit.get("status") if isinstance(audit, dict) else "").upper()
    payload: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "proof": str(args.proof),
        "embedded_audit_status": status or "UNKNOWN",
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"embedded_audit_status={payload['embedded_audit_status']}")
    return 0 if status in {"PASS", "PASS_WITH_RISKS"} else 2


def _run_doctor(args: argparse.Namespace) -> int:
    result = run_doctor(workspace=args.workspace, schema_path=args.schema)
    output = format_result(result, output_format=args.format)
    if args.format == "json" or result.ok:
        print(output)
    else:
        print(output, file=sys.stderr)
    return 0 if result.ok else 2


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _parse_now(value: str | None):
    if not value:
        return None
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


if __name__ == "__main__":
    raise SystemExit(main())
