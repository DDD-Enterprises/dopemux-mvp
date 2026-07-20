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

from tools.auditor_router.pal_clink import normalize_pal_clink_audit_output


TOKEN_ENV_VAR = "EMBEDDED_AUDIT_TOKEN"
PROOF_AUTHOR = "independent-embedded-audit"
WORKFLOW_NAME = "embedded-audit.yml"
PASSING_AUDIT_STATUSES = frozenset({"PASS", "PASS_WITH_RISKS"})


def _utc_now_seconds() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def independent_audit_errors(
    payload: Mapping[str, Any],
    *,
    expected_pr: int | None = None,
    expected_head_sha: str | None = None,
    expected_repo: str | None = None,
) -> list[str]:
    """Return fail-closed errors for an independent-audit proof payload.

    Shared by the embedded-audit workflow hard gate and PR Steward collector so
    both surfaces accept and reject the same proof shapes.
    """
    if not isinstance(payload, Mapping):
        return ["audit_proof_malformed: root is not an object"]

    errors: list[str] = []

    if "dry_run" in payload:
        dry_run = payload.get("dry_run")
        if dry_run is True:
            errors.append(
                "audit_proof_dry_run: final readiness requires an executed audit"
            )
        elif dry_run is not False:
            errors.append(
                "audit_proof_malformed_dry_run: dry_run must be a boolean when present"
            )

    if payload.get("executed") is not True:
        errors.append("audit_not_executed: final readiness requires executed=true")

    if expected_pr is not None:
        try:
            proof_pr = int(payload.get("pr_number"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            proof_pr = None
        if proof_pr != int(expected_pr):
            errors.append(
                f"audit_pr_mismatch: proof pr_number={payload.get('pr_number')!r} "
                f"expected={expected_pr}"
            )

    if expected_head_sha is not None:
        proof_head = str(payload.get("head_sha") or "")
        if proof_head != expected_head_sha:
            errors.append(
                f"audit_head_mismatch: proof head_sha={proof_head!r} "
                f"expected={expected_head_sha}"
            )

    if expected_repo is not None:
        proof_repo = str(payload.get("repo") or "").strip()
        if not proof_repo:
            errors.append(
                "audit_repo_missing: final readiness requires proof.repo when "
                "expected_repo is provided"
            )
        elif proof_repo != expected_repo:
            errors.append(
                f"audit_repo_mismatch: proof repo={proof_repo!r} "
                f"expected={expected_repo}"
            )

    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        errors.append(
            "audit_provenance_missing: final readiness requires trusted provenance"
        )
        return errors
    if provenance.get("proof_author") != PROOF_AUTHOR:
        errors.append("audit_provenance_untrusted: unexpected proof author")
    if provenance.get("workflow") != WORKFLOW_NAME:
        errors.append("audit_provenance_untrusted: unexpected workflow")
    return errors


def enforce_independent_audit_proof(
    payload: Mapping[str, Any],
    *,
    expected_pr: int | None = None,
    expected_head_sha: str | None = None,
    expected_repo: str | None = None,
) -> None:
    """Raise SystemExit unless the proof is a passing independent audit."""
    errors = independent_audit_errors(
        payload,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
        expected_repo=expected_repo,
    )
    if errors:
        print("Independent audit errors detected:", file=sys.stderr)
        print(json.dumps(errors, indent=2), file=sys.stderr)
        raise SystemExit("; ".join(errors))

    embedded = payload.get("embedded_audit")
    if not isinstance(embedded, Mapping):
        raise SystemExit("audit_status_missing: embedded_audit object required")
    status = str(embedded.get("status") or "").upper()
    if status not in PASSING_AUDIT_STATUSES:
        print("Independent audit details on failure:", file=sys.stderr)
        print(json.dumps(payload, indent=2), file=sys.stderr)
        raise SystemExit(f"Independent audit did not pass: {status or 'UNKNOWN'}")


def build_diagnostic_failure_proof(
    *,
    packet_id: str,
    repo: str,
    pr_number: int,
    head_sha: str,
    reason: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Emit a fail-closed diagnostic proof without trusted provenance.

    Used for workflow failure paths (missing emitter, head mismatch, etc.).
    Must not forge independent-embedded-audit provenance.

    Schema rule: auditor_tool=none / auditor_model=unknown are only valid with
    status=SKIPPED. Hard enforcement still rejects executed!=true, so SKIPPED
    remains red while the artifact stays schema-valid.
    """
    report_path = f"proof/{packet_id}/AUDITOR_REPORT.md"
    return {
        "packet_id": packet_id,
        "repo": repo,
        "pr_number": int(pr_number),
        "head_sha": head_sha,
        "generated_at": generated_at or _utc_now_seconds(),
        "executed": False,
        "mutation_performed": False,
        "github_mutation_route_added": False,
        "embedded_audit": _skipped_audit(report_path=report_path, reason=reason),
    }


def _accepted_local_attestation(
    local_attestation: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Return the attestation when it is an accepted local-signed audit."""
    if not isinstance(local_attestation, Mapping):
        return None
    if local_attestation.get("accepted") is not True:
        return None
    if not isinstance(local_attestation.get("embedded_audit"), Mapping):
        return None
    return local_attestation


def _executed_ci_verdict(embedded_audit: Mapping[str, Any]) -> bool:
    """True when the CI-run auditor produced a real verdict (incl. FAIL).

    A real CI verdict — even a failing one — always outranks a local
    attestation; the local path only fills the could-not-run gap
    (SKIPPED / NEEDS_SUPERVISOR).
    """
    return str(embedded_audit.get("status") or "").upper() in {
        "PASS",
        "PASS_WITH_RISKS",
        "FAIL",
    }


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
    pal_output_error: str | None = None,
    local_attestation: Mapping[str, Any] | None = None,
    instruction_like_content: Mapping[str, Any] | None = None,
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
    elif pal_output_error:
        embedded_audit = _skipped_audit(
            report_path=report_path,
            reason=(
                "Independent embedded audit skipped because PAL clink output "
                f"JSON is missing or invalid: {pal_output_error}"
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
            instruction_like_content=instruction_like_content,
        )
        trusted_token_status = "AVAILABLE"

    executed = bool(
        token_present
        and not route_error
        and not pal_output_error
        and pal_output is not None
    )

    # Local-signed attestation fills the could-not-run gap ONLY: a real
    # CI-executed verdict (PASS/PASS_WITH_RISKS/FAIL) always takes precedence,
    # and the least-privilege token must still be present so only trusted runs
    # emit executed proofs. The attestation was verified upstream by
    # scripts/audit/local_audit_acceptance.py (signature against the trusted
    # allowed-signers file, exact-head proof-only delta, schema-valid verdict).
    accepted_local = _accepted_local_attestation(local_attestation)
    local_used = bool(
        accepted_local
        and token_present
        and not _executed_ci_verdict(embedded_audit)
    )
    audit_source = "ci-executed" if executed else "ci-unavailable"
    if local_used and accepted_local is not None:
        embedded_audit = dict(accepted_local["embedded_audit"])
        embedded_audit["report_path"] = report_path
        remaining_risks = [str(risk) for risk in embedded_audit.get("remaining_risks") or []]
        remaining_risks.append(
            "Audit executed locally at "
            f"{accepted_local.get('audited_sha')} and accepted via signed "
            f"attestation by allow-listed principal "
            f"{accepted_local.get('principal')!r} (proof-only delta verified); "
            "not an independently executed CI audit."
        )
        embedded_audit["remaining_risks"] = remaining_risks
        executed = True
        audit_source = "local-signed-attestation"

    provenance: dict[str, Any] = {
        "proof_author": PROOF_AUTHOR,
        "workflow": "embedded-audit.yml",
        "trusted_token_status": trusted_token_status,
        "token_source": token_source,
        "token_value_recorded": False,
        "audit_source": audit_source,
        "permissions": {
            "actions": "read",
            "checks": "read",
            "contents": "read",
            "pull-requests": "read",
            "statuses": "read",
        },
        "engine_authored_proof": False,
        "engine_requested_only": True,
    }
    if local_used and accepted_local is not None:
        provenance["local_attestation"] = {
            "principal": accepted_local.get("principal"),
            "audited_sha": accepted_local.get("audited_sha"),
            "proof_path": accepted_local.get("proof_path"),
            "signature_namespace": accepted_local.get("signature_namespace"),
            "signature_verified": True,
        }

    return {
        "packet_id": packet_id,
        "repo": repo,
        "pr_number": int(pr_number),
        "head_sha": head_sha,
        "generated_at": generated_at or _utc_now_seconds(),
        "executed": executed,
        "mutation_performed": False,
        "github_mutation_route_added": False,
        "embedded_audit": embedded_audit,
        "provenance": provenance,
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
    parser.add_argument(
        "--local-attestation-json",
        type=Path,
        help=(
            "Optional LOCAL_AUDIT_ATTESTATION.json produced by "
            "scripts/audit/local_audit_acceptance.py; consumed only when the "
            "CI auditor produced no real verdict."
        ),
    )
    parser.add_argument(
        "--instruction-like-json",
        type=Path,
        help=(
            "Optional instruction-like content scan JSON produced by "
            "scripts.audit.pal_clink_runner --build-prompt. Merged into the "
            "normalized embedded_audit object as evidence (not raw candidate text)."
        ),
    )
    parser.add_argument(
        "--force-skip-reason",
        help=(
            "When set, emit a schema-valid non-executed SKIPPED proof with this "
            "reason (e.g. trusted prompt builder/scanner unavailable). Does not "
            "invoke or require PAL output."
        ),
    )
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
    pal_output, pal_output_error = (
        _read_optional_json_object(args.pal_output_json)
        if args.pal_output_json
        else (None, None)
    )
    if args.force_skip_reason:
        # Fail closed: no model output, no fabricated clean scan.
        pal_output = None
        pal_output_error = str(args.force_skip_reason).strip() or (
            "Trusted prompt builder/scanner unavailable."
        )
    local_attestation: dict[str, Any] | None = None
    if args.local_attestation_json:
        # Malformed/missing attestation degrades to None — fail-closed to the
        # existing SKIPPED path, never an error that masks the audit result.
        local_attestation, _ = _read_optional_json_object(args.local_attestation_json)
    instruction_like: dict[str, Any] | None = None
    if args.instruction_like_json and not args.force_skip_reason:
        instruction_like, _ = _read_optional_json_object(args.instruction_like_json)
        if not instruction_like:
            instruction_like = None
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
        pal_output_error=pal_output_error,
        local_attestation=local_attestation,
        instruction_like_content=instruction_like,
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
    report_text = _render_public_audit_report()
    report_file.write_text(report_text, encoding="utf-8")
    root_report_file = out_dir / "AUDITOR_REPORT.md"
    if root_report_file != report_file:
        root_report_file.write_text(report_text, encoding="utf-8")


def _render_public_audit_report() -> str:
    return "\n".join(
        [
            "# PAL Clink Audit Report",
            "",
            "The canonical embedded audit details are recorded in PROOF.json.",
            "This Markdown file intentionally omits raw finding and risk text.",
            "",
        ]
    )


def main() -> int:
    try:
        return run_cli()
    except Exception as exc:
        print(f"run_embedded_audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
