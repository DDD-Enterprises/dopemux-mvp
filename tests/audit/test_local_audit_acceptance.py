"""Tests for fail-closed acceptance of locally-signed embedded-audit proofs."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema

from scripts.audit.local_audit_acceptance import (
    SIGNATURE_NAMESPACE,
    evaluate_local_audit,
)
from scripts.audit.run_embedded_audit import (
    build_embedded_audit_proof,
    enforce_independent_audit_proof,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"
REPO = "DDD-Enterprises/dopemux-mvp"
PR_NUMBER = 4242
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "embedded-audit.yml"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _local_embedded_audit(status: str = "PASS", tool: str = "pal-mcp-clink") -> dict:
    return {
        "required": True,
        "status": status,
        "auditor_tool": tool,
        "auditor_model": "sonnet",
        "invocation": "local pr-merge audit via PAL clink",
        "exit_code": 0,
        "report_path": f"proof/pr_merge/embedded-audit/pr-{PR_NUMBER}/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": None,
    }


class LocalAuditFixture:
    """Temp git repo with an audited commit, a signed proof commit, and keys."""

    def __init__(self, tmp_path: Path) -> None:
        self.repo = tmp_path / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "--quiet", "--initial-branch=main")
        _git(self.repo, "config", "user.email", "tester@example.invalid")
        _git(self.repo, "config", "user.name", "Tester")

        (self.repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        _git(self.repo, "add", "app.py")
        _git(self.repo, "commit", "--quiet", "-m", "code under audit")
        self.audited_sha = _git(self.repo, "rev-parse", "HEAD")

        self.key = tmp_path / "signing_key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.key)],
            check=True,
            capture_output=True,
        )
        pub = (tmp_path / "signing_key.pub").read_text(encoding="utf-8").split()
        self.allowed_signers = tmp_path / "allowed_signers"
        self.allowed_signers.write_text(
            f"tester@example {pub[0]} {pub[1]}\n", encoding="utf-8"
        )

        self.proof_dir = self.repo / f"proof/pr_merge/embedded-audit/pr-{PR_NUMBER}"

    def write_and_sign_proof(
        self,
        *,
        embedded: dict | None = None,
        pr_number: int = PR_NUMBER,
        audited_sha: str | None = None,
        namespace: str = SIGNATURE_NAMESPACE,
        key: Path | None = None,
        tamper_after_signing: bool = False,
    ) -> None:
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        proof = {
            "packet_id": f"PR-MERGE-STEWARD-{pr_number}",
            "repo": REPO,
            "pr_number": pr_number,
            "head_sha": audited_sha or self.audited_sha,
            "generated_at": "2026-07-16T00:00:00Z",
            "executed": True,
            "mutation_performed": False,
            "github_mutation_route_added": False,
            "embedded_audit": embedded or _local_embedded_audit(),
        }
        proof_file = self.proof_dir / "PROOF.json"
        proof_file.write_text(
            json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "sign",
                "-f",
                str(key or self.key),
                "-n",
                namespace,
                str(proof_file),
            ],
            check=True,
            capture_output=True,
        )
        if tamper_after_signing:
            proof["generated_at"] = "2026-07-16T00:00:01Z"
            proof_file.write_text(
                json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        _git(self.repo, "add", str(self.proof_dir.relative_to(self.repo)))
        _git(self.repo, "commit", "--quiet", "-m", "proof(audit): signed attestation")

    def head(self) -> str:
        return _git(self.repo, "rev-parse", "HEAD")

    def evaluate(self, **overrides) -> dict:
        kwargs = dict(
            repo_root=self.repo,
            repo=REPO,
            pr_number=PR_NUMBER,
            head_sha=self.head(),
            allowed_signers=self.allowed_signers,
            schema_path=SCHEMA_PATH,
        )
        kwargs.update(overrides)
        return evaluate_local_audit(**kwargs)


def test_accepts_signed_proof_only_delta(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof()
    attestation = fixture.evaluate()
    assert attestation["accepted"] is True, attestation["reasons"]
    assert attestation["principal"] == "tester@example"
    assert attestation["audited_sha"] == fixture.audited_sha
    assert attestation["embedded_audit"]["status"] == "PASS"


def test_rejects_tampered_proof(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(tamper_after_signing=True)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("signature_invalid") for r in attestation["reasons"])


def test_rejects_signer_not_in_allowed_signers(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    rogue = tmp_path / "rogue_key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(rogue)],
        check=True,
        capture_output=True,
    )
    fixture.write_and_sign_proof(key=rogue)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("signature_principal_not_allowed") for r in attestation["reasons"]
    )


def test_rejects_wrong_namespace(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(namespace="file")
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("signature_invalid") for r in attestation["reasons"])


def test_rejects_missing_allowed_signers_file(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof()
    attestation = fixture.evaluate(allowed_signers=tmp_path / "missing_signers")
    assert attestation["accepted"] is False
    assert any(r.startswith("allowed_signers_missing") for r in attestation["reasons"])


def test_rejects_absent_proof(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("local_proof_absent") for r in attestation["reasons"])


def test_rejects_delta_touching_code(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof()
    (fixture.repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(fixture.repo, "add", "app.py")
    _git(fixture.repo, "commit", "--quiet", "-m", "sneak in code after audit")
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("delta_touches_code") for r in attestation["reasons"])


def test_rejects_rename_smuggled_into_proof_dir(tmp_path: Path) -> None:
    """A rename whose destination is inside the proof dir must still be caught.

    With default rename detection, --name-only can list only the destination
    path — hiding the source deletion. --no-renames closes that hole.
    """
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof()
    _git(fixture.repo, "-c", "diff.renames=true", "mv", "app.py",
         str(fixture.proof_dir.relative_to(fixture.repo) / "app.py"))
    _git(fixture.repo, "commit", "--quiet", "-m", "rename code into proof dir")
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("delta_touches_code") for r in attestation["reasons"])


def test_rejects_non_ancestor_audited_sha(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    original_audited = fixture.audited_sha
    # Rewrite history so the audited commit is no longer an ancestor of head,
    # while its object remains present in the repository.
    (fixture.repo / "app.py").write_text("VALUE = 99\n", encoding="utf-8")
    _git(fixture.repo, "add", "app.py")
    _git(fixture.repo, "commit", "--quiet", "--amend", "-m", "rewritten history")
    fixture.write_and_sign_proof(audited_sha=original_audited)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith(("audited_sha_not_ancestor", "objects_unreachable"))
        for r in attestation["reasons"]
    )


def test_rejects_pr_number_mismatch(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(pr_number=PR_NUMBER + 1)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("local_proof_pr_mismatch") for r in attestation["reasons"])


def test_rejects_non_passing_local_status(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    failing = _local_embedded_audit(status="FAIL")
    failing["exit_code"] = 1
    fixture.write_and_sign_proof(embedded=failing)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("local_audit_not_passing") for r in attestation["reasons"])


def test_rejects_auditor_tool_outside_schema_enum(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(
        embedded=_local_embedded_audit(tool="human_integrator")
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("local_audit_tool_not_in_schema") for r in attestation["reasons"]
    )


# ---------------------------------------------------------------------------
# Emitter integration: attestation feeding build_embedded_audit_proof
# ---------------------------------------------------------------------------


def _route() -> dict:
    return {
        "tool": "pal-mcp-clink",
        "underlying_cli": "claude",
        "clink_client_name": "claude-audit",
        "audit_safe_config_proven": True,
        "clink_mutation_flags_detected": [],
        "invocation_template": "pal-clink --client claude-audit --role codereviewer",
    }


def _accepted_attestation() -> dict:
    return {
        "accepted": True,
        "reasons": [],
        "repo": REPO,
        "pr_number": PR_NUMBER,
        "head_sha": "b" * 40,
        "audited_sha": "a" * 40,
        "principal": "tester@example",
        "proof_path": f"proof/pr_merge/embedded-audit/pr-{PR_NUMBER}/PROOF.json",
        "signature_namespace": SIGNATURE_NAMESPACE,
        "embedded_audit": _local_embedded_audit(),
    }


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _build(pal_output: dict | None, attestation: dict | None, token: bool = True) -> dict:
    return build_embedded_audit_proof(
        packet_id="TP-DMX-AUDIT-CI-PROVENANCE-104",
        repo=REPO,
        pr_number=PR_NUMBER,
        head_sha="b" * 40,
        route=_route(),
        pal_output=pal_output,
        token_present=token,
        token_source="EMBEDDED_AUDIT_TOKEN",
        local_attestation=attestation,
    )


def test_local_attestation_fills_ci_gap_and_passes_enforcement() -> None:
    error_output = {"status": "error", "content": "", "risks": ["command not found"]}
    proof = _build(error_output, _accepted_attestation())

    assert proof["executed"] is True
    embedded = proof["embedded_audit"]
    assert embedded["status"] == "PASS"
    assert embedded["report_path"] == (
        "proof/TP-DMX-AUDIT-CI-PROVENANCE-104/AUDITOR_REPORT.md"
    )
    assert any("signed" in risk for risk in embedded["remaining_risks"])
    provenance = proof["provenance"]
    assert provenance["audit_source"] == "local-signed-attestation"
    assert provenance["local_attestation"]["principal"] == "tester@example"
    assert provenance["local_attestation"]["signature_verified"] is True

    jsonschema.Draft7Validator(_schema()).validate(embedded)
    enforce_independent_audit_proof(
        proof,
        expected_pr=PR_NUMBER,
        expected_head_sha="b" * 40,
        expected_repo=REPO,
    )


def test_ci_fail_verdict_outranks_local_attestation() -> None:
    fail_output = {"status": "success", "verdict": "FAIL", "findings": [], "risks": []}
    proof = _build(fail_output, _accepted_attestation())
    assert proof["embedded_audit"]["status"] == "FAIL"
    assert proof["provenance"]["audit_source"] == "ci-executed"
    assert "local_attestation" not in proof["provenance"]


def test_ci_pass_verdict_outranks_local_attestation() -> None:
    pass_output = {
        "status": "success",
        "verdict": "PASS",
        "findings": [],
        "risks": [],
        "rationale": "CI auditor inspected the PR head; local attestation is outranked.",
        "inspected_paths": ["scripts/audit/local_audit_acceptance.py"],
        "evidence_refs": ["ci:pal-clink"],
        "validation_status": "NOT_RUN",
    }
    proof = _build(pass_output, _accepted_attestation())
    assert proof["embedded_audit"]["status"] == "PASS"
    assert proof["provenance"]["audit_source"] == "ci-executed"
    assert "local_attestation" not in proof["provenance"]


def test_local_attestation_requires_trusted_token() -> None:
    error_output = {"status": "error", "content": "", "risks": []}
    proof = _build(error_output, _accepted_attestation(), token=False)
    assert proof["executed"] is False
    assert proof["embedded_audit"]["status"] == "SKIPPED"
    assert "local_attestation" not in proof["provenance"]


def test_rejected_attestation_leaves_supervisor_path_unchanged() -> None:
    error_output = {"status": "error", "content": "", "risks": []}
    rejected = _accepted_attestation()
    rejected["accepted"] = False
    proof = _build(error_output, rejected)
    assert proof["embedded_audit"]["status"] == "NEEDS_SUPERVISOR"
    assert proof["provenance"]["audit_source"] == "ci-executed"
    assert "local_attestation" not in proof["provenance"]


# ---------------------------------------------------------------------------
# Workflow shape
# ---------------------------------------------------------------------------


def test_workflow_evaluates_attestation_from_trusted_source() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "Evaluate local signed audit attestation" in text
    assert "python -m scripts.audit.local_audit_acceptance" in text
    assert "--allowed-signers config/audit/embedded-audit-allowed-signers" in text
    assert (
        "--local-attestation-json ../embedded-audit-artifacts/LOCAL_AUDIT_ATTESTATION.json"
        in text
    )

