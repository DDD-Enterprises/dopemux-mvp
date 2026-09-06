#!/usr/bin/env python3
"""Deterministic embedded-audit evidence-gate proof emitter.

The active CI path consumes trusted change-contract classification and optional
signed exact-head audit evidence. It never launches a model, provider, or audit
runner. Legacy captured-output normalization remains callable for existing
offline consumers; it only parses supplied files and has no execution fallback.
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

from tools.auditor_router.pal_clink import normalize_pal_clink_audit_output  # noqa: E402


TOKEN_ENV_VAR = "EMBEDDED_AUDIT_TOKEN"
PROOF_AUTHOR = "independent-embedded-audit"
WORKFLOW_NAME = "embedded-audit.yml"
PASSING_AUDIT_STATUSES = frozenset({"PASS", "PASS_WITH_RISKS"})
NOT_REQUIRED_REASON = "AUDIT_NOT_REQUIRED_BY_TRUSTED_CHANGE_CONTRACT"
NON_MODEL_AUDIT_LANES = frozenset({"L0", "L1"})


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

    embedded = payload.get("embedded_audit")
    provenance = payload.get("provenance")
    not_required_claimed = (
        isinstance(embedded, Mapping)
        and embedded.get("required") is False
    ) or (
        isinstance(provenance, Mapping)
        and provenance.get("audit_source") == "trusted-change-contract"
    )
    if not_required_claimed:
        errors.extend(_not_required_proof_errors(payload))
    elif payload.get("executed") is not True:
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


def _not_required_proof_errors(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    embedded = payload.get("embedded_audit")
    provenance = payload.get("provenance")
    if payload.get("executed") is not False:
        errors.append("audit_not_required_execution_invalid: executed must be false")
    if not isinstance(embedded, Mapping):
        return errors + ["audit_not_required_shape_invalid: embedded_audit missing"]
    expected = {
        "required": False,
        "status": "SKIPPED",
        "auditor_tool": "none",
        "auditor_model": "unknown",
        "invocation": None,
        "exit_code": None,
        "skip_reason": NOT_REQUIRED_REASON,
    }
    for field, value in expected.items():
        if embedded.get(field) != value:
            errors.append(
                f"audit_not_required_shape_invalid: embedded_audit.{field}="
                f"{embedded.get(field)!r} expected {value!r}"
            )
    if not isinstance(provenance, Mapping):
        return errors
    if provenance.get("audit_source") != "trusted-change-contract":
        errors.append(
            "audit_not_required_provenance_invalid: audit_source must be "
            "trusted-change-contract"
        )
    contract = provenance.get("change_contract")
    if not isinstance(contract, Mapping):
        errors.append("audit_not_required_contract_missing: change_contract required")
        return errors
    if contract.get("status") != "PASS":
        errors.append("audit_not_required_contract_invalid: status must be PASS")
    if contract.get("model_audit_required") is not False:
        errors.append(
            "audit_not_required_contract_invalid: model_audit_required must be false"
        )
    if contract.get("max_lane") not in NON_MODEL_AUDIT_LANES:
        errors.append("audit_not_required_contract_invalid: max_lane must be L0 or L1")
    return errors


def _passing_audit_errors(embedded: Mapping[str, Any]) -> list[str]:
    status = str(embedded.get("status") or "").upper()
    if status not in PASSING_AUDIT_STATUSES:
        return [f"Independent audit did not pass: {status or 'UNKNOWN'}"]
    if status == "PASS_WITH_RISKS":
        risks = embedded.get("remaining_risks")
        if not isinstance(risks, list) or not any(
            isinstance(risk, str) and risk.strip() for risk in risks
        ):
            return ["PASS_WITH_RISKS requires explicit remaining_risks"]
        findings = embedded.get("findings")
        if isinstance(findings, list) and any(
            isinstance(finding, Mapping)
            and finding.get("severity") == "BLOCKING"
            and finding.get("status") != "RESOLVED"
            for finding in findings
        ):
            return ["PASS_WITH_RISKS contains unresolved BLOCKING finding"]
    return []


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
        raise SystemExit("; ".join(errors))

    embedded = payload.get("embedded_audit")
    if not isinstance(embedded, Mapping):
        raise SystemExit("audit_status_missing: embedded_audit object required")
    if embedded.get("required") is False:
        return
    passing_errors = _passing_audit_errors(embedded)
    if passing_errors:
        raise SystemExit("; ".join(passing_errors))


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


def build_evidence_gate_proof(
    *,
    packet_id: str,
    repo: str,
    pr_number: int,
    head_sha: str,
    base_sha: str,
    change_contract: Mapping[str, Any],
    local_attestation: Mapping[str, Any] | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build proof from trusted classification and optional signed evidence."""
    report_path = f"proof/{packet_id}/AUDITOR_REPORT.md"
    contract_status = change_contract.get("status")
    model_required = change_contract.get("model_audit_required")
    lane = change_contract.get("max_lane")
    if (
        contract_status != "PASS"
        or not isinstance(model_required, bool)
        or lane not in {"L0", "L1", "L2", "L3"}
    ):
        return build_diagnostic_failure_proof(
            packet_id=packet_id,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            reason="TRUSTED_CHANGE_CONTRACT_INVALID",
            generated_at=generated_at,
        )

    contract_provenance = {
        "status": contract_status,
        "max_lane": lane,
        "model_audit_required": model_required,
        "base_sha": base_sha,
        "head_sha": head_sha,
    }
    provenance: dict[str, Any] = {
        "proof_author": PROOF_AUTHOR,
        "workflow": WORKFLOW_NAME,
        "audit_source": "trusted-change-contract",
        "change_contract": contract_provenance,
        "engine_authored_proof": False,
        "engine_requested_only": True,
        "permissions": {
            "actions": "read",
            "checks": "read",
            "contents": "read",
            "pull-requests": "read",
            "statuses": "read",
        },
    }

    if model_required is False:
        if lane not in NON_MODEL_AUDIT_LANES:
            return build_diagnostic_failure_proof(
                packet_id=packet_id,
                repo=repo,
                pr_number=pr_number,
                head_sha=head_sha,
                reason="TRUSTED_CHANGE_CONTRACT_LANE_CONFLICT",
                generated_at=generated_at,
            )
        embedded_audit = {
            "required": False,
            "status": "SKIPPED",
            "auditor_tool": "none",
            "auditor_model": "unknown",
            "invocation": None,
            "exit_code": None,
            "report_path": report_path,
            "findings": [],
            "fixes_applied": [],
            "remaining_risks": [],
            "skip_reason": NOT_REQUIRED_REASON,
        }
        return {
            "packet_id": packet_id,
            "repo": repo,
            "pr_number": int(pr_number),
            "head_sha": head_sha,
            "generated_at": generated_at or _utc_now_seconds(),
            "executed": False,
            "mutation_performed": False,
            "github_mutation_route_added": False,
            "embedded_audit": embedded_audit,
            "provenance": provenance,
        }

    accepted = _accepted_local_attestation(local_attestation)
    if accepted is None or not isinstance(accepted.get("audit_identity"), Mapping):
        return build_diagnostic_failure_proof(
            packet_id=packet_id,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            reason="SIGNED_IMPORTED_AUDIT_EVIDENCE_REQUIRED",
            generated_at=generated_at,
        )

    embedded_audit = dict(accepted["embedded_audit"])
    embedded_audit["report_path"] = report_path
    passing_errors = _passing_audit_errors(embedded_audit)
    if passing_errors:
        return build_diagnostic_failure_proof(
            packet_id=packet_id,
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            reason="SIGNED_IMPORTED_AUDIT_EVIDENCE_INVALID: " + "; ".join(passing_errors),
            generated_at=generated_at,
        )

    provenance["audit_source"] = "signed-imported-evidence"
    provenance["local_attestation"] = {
        "principal": accepted.get("principal"),
        "audited_sha": accepted.get("audited_sha"),
        "proof_path": accepted.get("proof_path"),
        "signature_namespace": accepted.get("signature_namespace"),
        "signature_verified": True,
    }
    return {
        "packet_id": packet_id,
        "repo": repo,
        "pr_number": int(pr_number),
        "head_sha": head_sha,
        "generated_at": generated_at or _utc_now_seconds(),
        "executed": True,
        "mutation_performed": False,
        "github_mutation_route_added": False,
        "embedded_audit": embedded_audit,
        "audit_identity": dict(accepted["audit_identity"]),
        "provenance": provenance,
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
    parser.add_argument("--base-sha")
    parser.add_argument("--change-contract-json", type=Path)
    parser.add_argument("--route-json", type=Path)
    parser.add_argument("--pal-output-json", type=Path)
    parser.add_argument(
        "--local-attestation-json",
        type=Path,
        help=(
            "Optional LOCAL_AUDIT_ATTESTATION.json produced by "
            "scripts/audit/local_audit_acceptance.py. Required evidence for a "
            "trusted change contract that classifies model_audit_required=true."
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
    if args.change_contract_json:
        if not args.base_sha:
            raise ValueError("--base-sha is required with --change-contract-json")
        change_contract = _read_json_object(args.change_contract_json)
        local_attestation: dict[str, Any] | None = None
        if args.local_attestation_json:
            local_attestation, _ = _read_optional_json_object(
                args.local_attestation_json
            )
        proof = build_evidence_gate_proof(
            packet_id=args.packet_id,
            repo=args.repo,
            pr_number=args.pr,
            head_sha=args.head_sha,
            base_sha=args.base_sha,
            change_contract=change_contract,
            local_attestation=local_attestation,
            generated_at=args.generated_at,
        )
        _write_outputs(args.out, proof)
        return 0

    if args.route_json is None:
        raise ValueError(
            "--route-json is required for legacy captured-output normalization"
        )
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
            "# Audit Evidence Gate Report",
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
