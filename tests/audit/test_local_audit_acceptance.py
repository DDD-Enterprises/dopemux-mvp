"""Tests for fail-closed acceptance of locally-signed embedded-audit proofs."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from scripts.audit import local_audit_acceptance
from scripts.audit.local_audit_acceptance import (
    SIGNATURE_NAMESPACE,
    evaluate_local_audit,
    policy_errors,
    schema_validation_errors,
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


# The trusted schema permits exactly one directory under proof/:
#   ^proof/[^/]+/AUDITOR(_REPAIR(_[0-9]+)?)?_REPORT\.md$
# This fixture previously carried a two-directory pr_merge path, which the
# canonical validator rejects. The old hand-rolled acceptance validator
# exempted report_path, so the fixture passed and the exemption looked safe.
PACKET_ID = "TP-DMX-TEST-LOCAL-AUDIT-ACCEPTANCE"
REPORT_PATH = f"proof/{PACKET_ID}/AUDITOR_REPORT.md"


def _local_embedded_audit(status: str = "PASS", tool: str = "pal-mcp-clink") -> dict:
    return {
        "required": True,
        "status": status,
        "auditor_tool": tool,
        "auditor_model": "sonnet",
        "invocation": "local pr-merge audit via PAL clink",
        "exit_code": 0,
        "report_path": REPORT_PATH,
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
        self.packet_dir = self.repo / f"proof/{PACKET_ID}"

    def write_packet_bundle(
        self,
        *,
        packet_embedded: dict | None = None,
        packet_audited_sha: str | None = None,
        include_report: bool = True,
        include_review_bundle: bool = True,
        commit: bool = True,
    ) -> None:
        """Write the canonical AGENTS.md 9.1 packet proof bundle.

        Separate from ``write_and_sign_proof`` so tests can omit or corrupt
        individual pieces (report, review_bundle, packet PROOF.json fields)
        to exercise each new fail-closed check independently.
        """
        self.packet_dir.mkdir(parents=True, exist_ok=True)
        packet_proof = {
            "packet_id": PACKET_ID,
            "repo": REPO,
            "head_sha": packet_audited_sha or self.audited_sha,
            "embedded_audit": packet_embedded or _local_embedded_audit(),
        }
        (self.packet_dir / "PROOF.json").write_text(
            json.dumps(packet_proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if include_report:
            (self.packet_dir / "AUDITOR_REPORT.md").write_text(
                "# Auditor report\n\nPASS.\n", encoding="utf-8"
            )
        if include_review_bundle:
            bundle_dir = self.packet_dir / "review_bundle"
            bundle_dir.mkdir(parents=True, exist_ok=True)
            (bundle_dir / "evidence.txt").write_text("raw transcript\n", encoding="utf-8")
        if commit:
            _git(self.repo, "add", str(self.packet_dir.relative_to(self.repo)))
            _git(self.repo, "commit", "--quiet", "-m", "proof(audit): packet bundle")

    def write_and_sign_proof(
        self,
        *,
        embedded: dict | None = None,
        pr_number: int = PR_NUMBER,
        audited_sha: str | None = None,
        namespace: str = SIGNATURE_NAMESPACE,
        key: Path | None = None,
        tamper_after_signing: bool = False,
        write_packet_bundle: bool = True,
    ) -> None:
        if write_packet_bundle and not (self.packet_dir / "PROOF.json").exists():
            self.write_packet_bundle(packet_audited_sha=audited_sha or self.audited_sha)
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
        r.startswith("local_audit_schema_invalid: /auditor_tool")
        for r in attestation["reasons"]
    )


# ---------------------------------------------------------------------------
# head_sha <-> PACKET_ID binding (TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001)
#
# These prove the repair for the gap PR #1235's review caught: a signed
# proof's head_sha must be the commit an auditor actually examined, not a
# later "evidence head" that only adds report files, and the canonical
# packet proof bundle (AGENTS.md 9.1) must exist at the PR head and agree
# with the signed proof on the audited commit and controlling verdict.
# ---------------------------------------------------------------------------


def test_evidence_head_masquerading_as_audited_sha_is_rejected(tmp_path: Path) -> None:
    """head_sha pointing at a report-adding successor, not the real audited
    commit, must fail -- this is the exact defect the review caught on
    PR #1235's first signed proof."""
    fixture = LocalAuditFixture(tmp_path)
    real_audited_sha = fixture.audited_sha
    # Evidence-head commit: adds only the packet bundle on top of the real
    # audited commit, mirroring the two-commit bridge pattern.
    fixture.write_packet_bundle(packet_audited_sha=real_audited_sha)
    evidence_head_sha = fixture.head()
    # Sign with head_sha pointing at the evidence head, not real_audited_sha.
    fixture.write_and_sign_proof(
        audited_sha=evidence_head_sha, write_packet_bundle=False
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    # The evidence-head commit itself only added proof/<PACKET_ID>/**, so the
    # diff-scope check alone would not catch this -- the packet PROOF.json's
    # own head_sha (real_audited_sha) disagreeing with the signed proof's
    # head_sha (evidence_head_sha) is what catches it.
    assert any(
        r.startswith("packet_proof_head_sha_mismatch") for r in attestation["reasons"]
    )


def test_canonical_packet_proof_successor_plus_pr_proof_successor_passes(
    tmp_path: Path,
) -> None:
    """The doctrine-correct shape: head_sha = the real audited commit, packet
    bundle and PR proof both land as proof-only deltas after it, agreeing on
    audited SHA and verdict identity."""
    fixture = LocalAuditFixture(tmp_path)
    real_audited_sha = fixture.audited_sha
    fixture.write_packet_bundle(packet_audited_sha=real_audited_sha)
    fixture.write_and_sign_proof(
        audited_sha=real_audited_sha, write_packet_bundle=False
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is True, attestation["reasons"]
    assert attestation["packet_id"] == PACKET_ID


def test_missing_packet_proof_json_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_proof_absent") for r in attestation["reasons"])


def test_missing_or_empty_review_bundle_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_review_bundle=False)
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_review_bundle_missing_or_empty")
        for r in attestation["reasons"]
    )


def test_missing_packet_report_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_report=False)
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_report_absent") for r in attestation["reasons"])


def test_post_audit_non_proof_path_still_fails(tmp_path: Path) -> None:
    """The widened allow-list (proof dir + packet dir) must not become a
    general escape hatch -- any path outside both still fails closed."""
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle()
    fixture.write_and_sign_proof(write_packet_bundle=False)
    (fixture.repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(fixture.repo, "add", "app.py")
    _git(fixture.repo, "commit", "--quiet", "-m", "sneak in code after audit+proof")
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("delta_touches_code") for r in attestation["reasons"])


def test_wrong_packet_directory_is_rejected(tmp_path: Path) -> None:
    """report_path names one PACKET_ID but the packet bundle lives under a
    different directory -- must fail, not silently pass by coincidence."""
    fixture = LocalAuditFixture(tmp_path)
    # Packet bundle at a directory that does NOT match REPORT_PATH's packet id.
    wrong_dir = fixture.repo / "proof/TP-DMX-WRONG-PACKET"
    wrong_dir.mkdir(parents=True)
    (wrong_dir / "PROOF.json").write_text(
        json.dumps(
            {
                "packet_id": "TP-DMX-WRONG-PACKET",
                "repo": REPO,
                "head_sha": fixture.audited_sha,
                "embedded_audit": _local_embedded_audit(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (wrong_dir / "AUDITOR_REPORT.md").write_text("PASS.\n", encoding="utf-8")
    (wrong_dir / "review_bundle").mkdir()
    (wrong_dir / "review_bundle" / "evidence.txt").write_text("x\n", encoding="utf-8")
    _git(fixture.repo, "add", "proof/TP-DMX-WRONG-PACKET")
    _git(fixture.repo, "commit", "--quiet", "-m", "wrong packet dir")
    fixture.write_and_sign_proof(write_packet_bundle=False)  # report_path still PACKET_ID
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    # The wrong-directory commit isn't under either allowed prefix, so the
    # diff-scope check catches it before packet-bundle presence is even
    # checked -- still fail-closed, just via the earlier gate.
    assert any(
        r.startswith(("delta_touches_code", "packet_proof_absent"))
        for r in attestation["reasons"]
    )


def test_packet_proof_head_sha_mismatch_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    other_sha = "f" * 40
    fixture.write_packet_bundle(packet_audited_sha=other_sha)
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_proof_head_sha_mismatch") for r in attestation["reasons"]
    )


def test_packet_proof_verdict_identity_mismatch_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(
        packet_embedded=_local_embedded_audit(tool="claude-code-cli")
    )
    fixture.write_and_sign_proof(
        embedded=_local_embedded_audit(tool="pal-mcp-clink"), write_packet_bundle=False
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_proof_verdict_identity_mismatch")
        for r in attestation["reasons"]
    )


def test_packet_proof_itself_schema_invalid_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(
        packet_embedded=_local_embedded_audit(tool="not_a_real_tool")
    )
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_proof_local_audit_schema_invalid") for r in attestation["reasons"])


def test_head_mismatch_between_evaluate_arg_and_actual_head_still_fails(
    tmp_path: Path,
) -> None:
    """Sanity check that the pre-existing head-binding behaviour survives the
    refactor: evaluating against a stale head still fails closed."""
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle()
    fixture.write_and_sign_proof(write_packet_bundle=False)
    real_head = fixture.head()
    stale_head = fixture.audited_sha
    attestation = fixture.evaluate(head_sha=stale_head)
    assert attestation["accepted"] is False
    assert real_head != stale_head


def test_packet_proof_malformed_json_is_rejected(tmp_path: Path) -> None:
    """proof/<PACKET_ID>/PROOF.json present but not valid JSON must fail
    closed, not raise or pass through as absent."""
    fixture = LocalAuditFixture(tmp_path)
    fixture.packet_dir.mkdir(parents=True, exist_ok=True)
    (fixture.packet_dir / "PROOF.json").write_text("{not valid json", encoding="utf-8")
    (fixture.packet_dir / "AUDITOR_REPORT.md").write_text("PASS.\n", encoding="utf-8")
    bundle_dir = fixture.packet_dir / "review_bundle"
    bundle_dir.mkdir()
    (bundle_dir / "evidence.txt").write_text("x\n", encoding="utf-8")
    _git(fixture.repo, "add", str(fixture.packet_dir.relative_to(fixture.repo)))
    _git(fixture.repo, "commit", "--quiet", "-m", "malformed packet proof")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_proof_malformed") for r in attestation["reasons"])


def test_report_path_resolving_to_directory_is_rejected(tmp_path: Path) -> None:
    """AUDITOR_REPORT.md must be a real file (blob), not a directory that
    merely has some descendant blob under that string prefix.

    Regression for the R2 review finding: the prior check used
    ``git ls-tree -r`` name-prefix matching, so a directory named
    ``AUDITOR_REPORT.md`` containing e.g. ``evidence.txt`` would satisfy
    "has at least one descendant blob" while the required file itself never
    existed.
    """
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_report=False)
    report_as_dir = fixture.packet_dir / "AUDITOR_REPORT.md"
    report_as_dir.mkdir()
    (report_as_dir / "evidence.txt").write_text("not the report\n", encoding="utf-8")
    _git(fixture.repo, "add", str(fixture.packet_dir.relative_to(fixture.repo)))
    _git(fixture.repo, "commit", "--quiet", "-m", "report path is a directory")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_report_absent") for r in attestation["reasons"])


def test_review_bundle_as_a_file_is_rejected(tmp_path: Path) -> None:
    """review_bundle must be an actual directory (git tree), not a file or
    symlink whose name happens to match.

    Regression for the R2 review finding: the prior check accepted any path
    whose exact string appeared in ``git ls-tree -r --name-only`` output,
    which a regular file (blob) at that exact path also satisfies.
    """
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_review_bundle=False)
    bundle_as_file = fixture.packet_dir / "review_bundle"
    bundle_as_file.write_text("not a directory\n", encoding="utf-8")
    _git(fixture.repo, "add", str(fixture.packet_dir.relative_to(fixture.repo)))
    _git(fixture.repo, "commit", "--quiet", "-m", "review_bundle is a file")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_review_bundle_missing_or_empty")
        for r in attestation["reasons"]
    )


SIGN_SCRIPT = ROOT / "scripts" / "audit" / "sign_local_audit_proof.sh"


def test_signer_preflight_rejects_packet_object_failing_policy_despite_matching_identity(
    tmp_path: Path,
) -> None:
    """The signer's preflight must run the packet embedded_audit object
    through the SAME canonical schema+policy validation the trusted
    acceptance engine runs, not merely compare status/auditor_tool/
    auditor_model. A packet object that agrees with the PR proof on those
    three fields but fails policy elsewhere (here: required=false) must be
    rejected at signing time, not silently signed and only caught later by
    CI. Regression for the R3 review finding."""
    import shutil

    scratch = tmp_path / "scratch"
    shutil.copytree(ROOT / "schemas", scratch / "schemas")

    packet_id = "TP-DMX-TEST-SIGNER-PREFLIGHT"
    packet_dir = scratch / "proof" / packet_id
    packet_dir.mkdir(parents=True)
    (packet_dir / "AUDITOR_REPORT.md").write_text("PASS\n", encoding="utf-8")
    bundle_dir = packet_dir / "review_bundle"
    bundle_dir.mkdir()
    (bundle_dir / "evidence.txt").write_text("x\n", encoding="utf-8")

    shared = {
        "status": "PASS",
        "auditor_tool": "agy",
        "auditor_model": "gemini-3.1-pro-high",
        "invocation": "agy --model gemini-3.1-pro-high",
        "exit_code": 0,
        "report_path": f"proof/{packet_id}/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": None,
    }
    # Packet object agrees on status/auditor_tool/auditor_model but declares
    # required=false -- schema-valid, policy-invalid.
    packet_embedded = dict(shared, required=False)
    (packet_dir / "PROOF.json").write_text(
        json.dumps(
            {
                "packet_id": packet_id,
                "repo": REPO,
                "head_sha": "a" * 40,
                "embedded_audit": packet_embedded,
            }
        ),
        encoding="utf-8",
    )

    pr_dir = scratch / "proof" / "pr_merge" / "embedded-audit" / "pr-9999"
    pr_dir.mkdir(parents=True)
    pr_embedded = dict(shared, required=True)
    (pr_dir / "PROOF.json").write_text(
        json.dumps(
            {"repo": REPO, "pr_number": 9999, "head_sha": "a" * 40, "embedded_audit": pr_embedded}
        ),
        encoding="utf-8",
    )

    # A dummy key file only needs to exist -- the script's own file-existence
    # precheck runs before the Python preflight this test targets, and the
    # rejected preflight exits before ever invoking ssh-keygen.
    fake_key = tmp_path / "unused_key"
    fake_key.write_text("not a real key\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), "9999", str(fake_key)],
        cwd=str(scratch),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "PYTHONPATH": str(ROOT)},
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "required" in result.stderr
    assert "REJECTED by CI" in result.stderr


def test_review_bundle_gitlink_only_is_rejected(tmp_path: Path) -> None:
    """review_bundle must contain a real blob, not merely any named entry.

    Regression for the R3 review finding: a gitlink/submodule entry (git
    object type ``commit``) is a pointer to another repository's history,
    not in-repo evidence, but a bare ``ls-tree -r --name-only`` listing
    would print its path just like a real file, satisfying a presence-only
    check without any actual audit evidence existing in this repo.
    """
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_review_bundle=False)
    bundle_dir = fixture.packet_dir / "review_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    fake_submodule_sha = "a" * 40
    _git(
        fixture.repo,
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        fake_submodule_sha,
        str((bundle_dir / "fake-submodule").relative_to(fixture.repo)),
    )
    _git(fixture.repo, "commit", "--quiet", "-m", "gitlink-only review_bundle")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_review_bundle_missing_or_empty")
        for r in attestation["reasons"]
    )


def test_review_bundle_symlink_only_is_rejected(tmp_path: Path) -> None:
    """review_bundle must contain a real regular-file blob, not a symlink.

    Regression for the R5 review finding: git reports a symlink's mode as
    ``120000`` but its object TYPE is still ``blob`` (the blob content is the
    target path string, not stored audit evidence) -- the R3 gitlink fix
    checked object type alone, which a symlink-only review_bundle would
    still satisfy despite containing no real in-repository evidence.
    """
    import os

    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_review_bundle=False)
    bundle_dir = fixture.packet_dir / "review_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    os.symlink("/etc/passwd", bundle_dir / "evidence.txt")
    _git(fixture.repo, "add", str(bundle_dir.relative_to(fixture.repo)))
    _git(fixture.repo, "commit", "--quiet", "-m", "symlink-only review_bundle")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_review_bundle_missing_or_empty")
        for r in attestation["reasons"]
    )


def test_report_path_as_symlink_is_rejected(tmp_path: Path) -> None:
    """AUDITOR_REPORT.md must be a real regular-file blob, not a symlink.

    Same class of bug as the review_bundle symlink case, applied to the
    exact-file check for report_path.
    """
    import os

    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(include_report=False)
    os.symlink(
        "/etc/passwd", fixture.packet_dir / "AUDITOR_REPORT.md"
    )
    _git(fixture.repo, "add", str(fixture.packet_dir.relative_to(fixture.repo)))
    _git(fixture.repo, "commit", "--quiet", "-m", "report path is a symlink")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_report_absent") for r in attestation["reasons"])


def test_signer_preflight_rejects_reserved_pr_merge_packet_id(tmp_path: Path) -> None:
    """The signer must reuse the ACTUAL _extract_packet_id, not a
    re-implemented parallel derivation, so it can never independently drift
    out of sync with the trusted acceptance engine's reserved-namespace
    rejection. Regression for the R5 review finding: after acceptance
    started rejecting PACKET_ID="pr_merge", the signer still derived it
    independently and would have signed "proof shape OK" for a proof that
    evaluate_local_audit() would then reject with packet_id_undecidable."""
    import shutil

    scratch = tmp_path / "scratch"
    shutil.copytree(ROOT / "schemas", scratch / "schemas")

    packet_dir = scratch / "proof" / "pr_merge"
    packet_dir.mkdir(parents=True)
    (packet_dir / "AUDITOR_REPORT.md").write_text("PASS\n", encoding="utf-8")
    bundle_dir = packet_dir / "review_bundle"
    bundle_dir.mkdir()
    (bundle_dir / "evidence.txt").write_text("x\n", encoding="utf-8")

    shared = {
        "status": "PASS",
        "auditor_tool": "agy",
        "auditor_model": "gemini-3.1-pro-high",
        "invocation": "agy --model gemini-3.1-pro-high",
        "exit_code": 0,
        "report_path": "proof/pr_merge/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": None,
    }
    (packet_dir / "PROOF.json").write_text(
        json.dumps(
            {"packet_id": "pr_merge", "repo": REPO, "head_sha": "a" * 40, "embedded_audit": shared}
        ),
        encoding="utf-8",
    )

    pr_dir = scratch / "proof" / "pr_merge" / "embedded-audit" / "pr-9999"
    pr_dir.mkdir(parents=True)
    (pr_dir / "PROOF.json").write_text(
        json.dumps(
            {"repo": REPO, "pr_number": 9999, "head_sha": "a" * 40, "embedded_audit": shared}
        ),
        encoding="utf-8",
    )

    fake_key = tmp_path / "unused_key"
    fake_key.write_text("not a real key\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), "9999", str(fake_key)],
        cwd=str(scratch),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "PYTHONPATH": str(ROOT)},
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "PACKET_ID" in result.stderr
    assert "REJECTED by CI" in result.stderr


def test_packet_proof_packet_id_mismatch_is_rejected(tmp_path: Path) -> None:
    """The packet PROOF.json's own declared packet_id must equal the
    PACKET_ID derived from the signed report_path -- path placement alone is
    not identity. Regression for the Copilot review finding on this PR."""
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle()
    packet_proof_path = fixture.packet_dir / "PROOF.json"
    packet_proof = json.loads(packet_proof_path.read_text(encoding="utf-8"))
    packet_proof["packet_id"] = "TP-DMX-SOME-OTHER-PACKET"
    packet_proof_path.write_text(
        json.dumps(packet_proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _git(fixture.repo, "add", str(fixture.packet_dir.relative_to(fixture.repo)))
    _git(fixture.repo, "commit", "--quiet", "--amend", "-m", "proof(audit): packet bundle")
    fixture.write_and_sign_proof(write_packet_bundle=False)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("packet_proof_packet_id_mismatch") for r in attestation["reasons"]
    )


def test_extract_packet_id_returns_none_for_non_matching_report_path() -> None:
    """Direct unit coverage of the defensive branch: a report_path that does
    not match the trusted schema's pattern yields no PACKET_ID at all. Once
    schema validation has already passed, the pattern's fixed 3-segment
    shape makes this unreachable through evaluate_local_audit -- covered
    here directly so the fail-closed branch itself is exercised."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert (
        local_audit_acceptance._extract_packet_id(
            "docs/not-a-proof-path.md", schema
        )
        is None
    )
    assert (
        local_audit_acceptance._extract_packet_id(
            "proof/too/many/segments/AUDITOR_REPORT.md", schema
        )
        is None
    )
    assert (
        local_audit_acceptance._extract_packet_id("proof/PKT/AUDITOR_REPORT.md", schema)
        == "PKT"
    )


def test_extract_packet_id_rejects_reserved_pr_merge_namespace() -> None:
    """A report_path of proof/pr_merge/AUDITOR_REPORT.md schema-matches the
    generic [^/]+ wildcard, deriving PACKET_ID="pr_merge" -- but proof/pr_merge/
    is the RESERVED root every PR's signed proof lives under
    (proof/pr_merge/embedded-audit/pr-<N>/), not one packet's own directory.
    Accepting it would widen the diff-scope allow-list to that whole shared
    namespace, letting a proof successor touch any other PR's signed
    attestation while still passing the proof-only-delta check. Regression
    for the R4 review finding."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert (
        local_audit_acceptance._extract_packet_id(
            "proof/pr_merge/AUDITOR_REPORT.md", schema
        )
        is None
    )


def test_report_path_colliding_with_reserved_namespace_is_rejected_end_to_end(
    tmp_path: Path,
) -> None:
    """End-to-end: a signed proof whose report_path derives PACKET_ID="pr_merge"
    must fail closed via evaluate_local_audit, not merely at the unit level."""
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(
        embedded=_local_embedded_audit()
        | {"report_path": "proof/pr_merge/AUDITOR_REPORT.md"},
        write_packet_bundle=False,
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("packet_id_undecidable") for r in attestation["reasons"])


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


def test_workflow_provisions_the_canonical_schema_validator() -> None:
    """The acceptance gate fails closed without jsonschema, so the job must install it.

    This job installs no project dependencies, and a trust gate must not depend
    on an undeclared runner-image package.
    """
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    install = text.index("python -m pip install --quiet 'jsonschema>=4.20.0'")
    evaluate = text.index("python -m scripts.audit.local_audit_acceptance")
    assert install < evaluate, "validator must be installed before the gate runs"



# ---------------------------------------------------------------------------
# Canonical-schema parity
#
# The acceptance route must enforce exactly what the trusted schema says. A
# previous hand-rolled validator checked only `required`, a few enums, and a
# few types: it never walked `allOf`, so no conditional constraint was enforced
# on the signed local-attestation path, and it exempted `report_path` outright.
#
# These tests load the schema from the repository working tree. In CI the
# acceptance step loads the schema from the TRUSTED base ref instead, so a PR
# that adds an enum value cannot widen its own admission — that bootstrap
# property is asserted in tests/audit/test_agy_gemini31_model.py.
# ---------------------------------------------------------------------------


def _exact_model_audit(**overrides: Any) -> dict:
    audit = _local_embedded_audit()
    audit["auditor_model"] = "gemini-3.1-pro-high"
    audit["auditor_tool"] = "agy"
    audit["invocation"] = "agy --model gemini-3.1-pro-high --mode plan"
    audit.update(overrides)
    return audit


def _grok_audit(**overrides: Any) -> dict:
    audit = _local_embedded_audit()
    audit["auditor_model"] = "grok-4.5"
    audit["auditor_tool"] = "grok-cli"
    # Pins the model explicitly: the runner's default has moved off grok-4.5, and
    # the fixtures should model the recommended pinned usage.
    audit["invocation"] = "grok -m grok-4.5 --always-approve --output-format plain -p '<prompt>'"
    audit.update(overrides)
    return audit


def _skipped_audit(**overrides: Any) -> dict:
    audit = _local_embedded_audit(status="SKIPPED", tool="none")
    audit["auditor_model"] = "unknown"
    audit["invocation"] = None
    audit["exit_code"] = None
    audit["skip_reason"] = "No auditor credential provisioned."
    audit.update(overrides)
    return audit


def _canonical_errors(audit: dict) -> list[str]:
    return [err.message for err in jsonschema.Draft7Validator(_schema()).iter_errors(audit)]


# (name, audit object, expected schema-valid under the canonical validator)
PARITY_CORPUS: list[tuple[str, dict, bool]] = [
    ("generic gemini bootstrap", _local_embedded_audit(tool="agy"), True),
    ("exact model bound to agy", _exact_model_audit(), True),
    ("exact model with wrong tool", _exact_model_audit(auditor_tool="claude-code-cli"), False),
    ("exact model with gemini-cli", _exact_model_audit(auditor_tool="gemini-cli"), False),
    ("grok pair bound both ways", _grok_audit(), True),
    ("grok model with wrong tool", _grok_audit(auditor_tool="claude-code-cli"), False),
    ("grok tool with wrong model", _grok_audit(auditor_model="gemini"), False),
    ("grok build label is not a model", _grok_audit(auditor_model="grok-4.5-build"), False),
    ("skipped diagnostic", _skipped_audit(), True),
    ("skipped without skip_reason", _skipped_audit(skip_reason=None), False),
    ("skipped with a live tool", _skipped_audit(auditor_tool="agy"), False),
    ("non-skipped claiming tool none", _local_embedded_audit(tool="none"), False),
    ("non-skipped claiming model unknown", _local_embedded_audit(tool="agy") | {"auditor_model": "unknown"}, False),
    ("tool outside the enum", _local_embedded_audit(tool="human_integrator"), False),
    ("malformed report_path", _local_embedded_audit() | {"report_path": f"proof/pr_merge/embedded-audit/pr-{PR_NUMBER}/AUDITOR_REPORT.md"}, False),
    ("unknown top-level key", _local_embedded_audit() | {"audited_by_operator": True}, False),
    ("missing auditor_tool", {k: v for k, v in _exact_model_audit().items() if k != "auditor_tool"}, False),
    ("finding with a bad severity", _local_embedded_audit() | {"findings": [{"id": "F-1", "severity": "CATASTROPHIC", "title": "t", "status": "OPEN", "body": "b"}]}, False),
]


@pytest.mark.parametrize(
    "name,audit,schema_valid", PARITY_CORPUS, ids=[row[0] for row in PARITY_CORPUS]
)
def test_local_validator_agrees_with_canonical_draft7(
    name: str, audit: dict, schema_valid: bool
) -> None:
    """The local route and jsonschema must agree on every fixture.

    Parity is asserted at the schema layer only: verdict policy (a passing
    status) is a separate acceptance gate, so a schema-valid SKIPPED proof is
    expected to be schema-clean here and rejected by policy elsewhere.
    """
    canonical = _canonical_errors(audit)
    local = schema_validation_errors(audit, _schema())
    assert bool(canonical) is bool(local), (
        f"{name}: canonical={canonical} local={local}"
    )
    assert bool(canonical) is not schema_valid, f"{name}: corpus expectation is stale"


def test_exact_model_with_wrong_tool_is_rejected_end_to_end(tmp_path: Path) -> None:
    """The defect this repair closes, exercised through the signed path.

    Before the repair this proof was ACCEPTED by the acceptance route while the
    canonical validator rejected it — a trusted signer could declare a
    tool/model pairing the schema forbids.
    """
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(
        embedded=_exact_model_audit(auditor_tool="claude-code-cli")
    )
    attestation = fixture.evaluate()

    assert attestation["accepted"] is False
    assert any(
        r.startswith("local_audit_schema_invalid: /auditor_tool")
        for r in attestation["reasons"]
    )
    assert _canonical_errors(_exact_model_audit(auditor_tool="claude-code-cli"))


def test_exact_model_bound_to_agy_is_accepted_end_to_end(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_packet_bundle(packet_embedded=_exact_model_audit())
    fixture.write_and_sign_proof(embedded=_exact_model_audit())
    attestation = fixture.evaluate()
    assert attestation["accepted"] is True, attestation["reasons"]


def test_rejects_report_path_outside_schema_pattern(tmp_path: Path) -> None:
    """report_path is no longer exempt.

    PR #1165's first published proof carried a two-directory pr_merge path that
    the canonical validator rejects; the acceptance route did not look, and a
    separate sweep-scope gap meant CI never looked either.
    """
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(
        embedded=_local_embedded_audit()
        | {"report_path": f"proof/pr_merge/embedded-audit/pr-{PR_NUMBER}/AUDITOR_REPORT.md"}
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("local_audit_schema_invalid: /report_path")
        for r in attestation["reasons"]
    )


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(
        embedded=_local_embedded_audit() | {"operator_override": True}
    )
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("local_audit_schema_invalid") for r in attestation["reasons"]
    )


def test_skipped_proof_is_schema_valid_but_policy_rejected(tmp_path: Path) -> None:
    assert schema_validation_errors(_skipped_audit(), _schema()) == []
    assert policy_errors(_skipped_audit()) == ["local_audit_not_passing: 'SKIPPED'"]

    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(embedded=_skipped_audit())
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(r.startswith("local_audit_not_passing") for r in attestation["reasons"])


def test_missing_jsonschema_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """No silent fallback to a partial validator when the engine is absent."""
    monkeypatch.setattr(local_audit_acceptance, "Draft7Validator", None)
    errors = schema_validation_errors(_local_embedded_audit(tool="agy"), _schema())
    assert errors
    assert errors[0].startswith("schema_validator_unavailable")


def test_every_schema_conditional_is_exercised_by_the_corpus() -> None:
    """Guard against a future conditional silently becoming unenforced.

    If someone adds an ``allOf`` branch to the trusted schema, this fails until
    the parity corpus grows a fixture that violates it. Parity is structural —
    the corpus is what proves the canonical engine is actually running.
    """
    conditionals = _schema().get("allOf", [])
    assert len(conditionals) == 5, (
        "The trusted schema's allOf set changed. Add parity fixtures covering the "
        "new conditional to PARITY_CORPUS, then update this count."
    )
    violating = [row for row in PARITY_CORPUS if row[2] is False]
    assert len(violating) >= len(conditionals)


# ---------------------------------------------------------------------------
# Non-schema acceptance policy
#
# The trusted schema is deliberately more permissive than acceptance, because it
# also describes CI-emitted diagnostic proofs. Gates the schema cannot express
# live in policy_errors(), and replacing the structural validator must never
# quietly remove one — which is exactly what happened to the `required` flag
# when the canonical-schema refactor first landed.
# ---------------------------------------------------------------------------


def test_rejects_required_false_even_though_schema_allows_it(tmp_path: Path) -> None:
    """`required: false` is schema-valid and must still be rejected.

    A downstream emitter promotes an accepted attestation to `executed: true`
    while final enforcement checks the verdict and not this flag, so accepting
    it would let the mandatory embedded-audit gate go green for a proof that
    declares the audit was not required.
    """
    audit = _local_embedded_audit() | {"required": False}
    assert schema_validation_errors(audit, _schema()) == [], "fixture must be schema-valid"
    assert policy_errors(audit) == [
        "local_audit_required_flag: embedded_audit.required must be true"
    ]

    fixture = LocalAuditFixture(tmp_path)
    fixture.write_and_sign_proof(embedded=audit)
    attestation = fixture.evaluate()
    assert attestation["accepted"] is False
    assert any(
        r.startswith("local_audit_required_flag") for r in attestation["reasons"]
    )


def test_policy_reports_every_violated_gate_at_once() -> None:
    audit = _local_embedded_audit(status="FAIL") | {"required": False, "exit_code": 1}
    assert sorted(policy_errors(audit)) == [
        "local_audit_not_passing: 'FAIL'",
        "local_audit_required_flag: embedded_audit.required must be true",
    ]


# Fixtures the trusted schema accepts but acceptance policy must not.
# Each entry is a gate the schema cannot express; losing one is a silent
# weakening of the trust contract, so it is asserted rather than assumed.
POLICY_ONLY_REJECTIONS: list[tuple[str, dict, str]] = [
    ("non-passing verdict", _local_embedded_audit(status="FAIL") | {"exit_code": 1},
     "local_audit_not_passing"),
    ("audit declared not required", _local_embedded_audit() | {"required": False},
     "local_audit_required_flag"),
]


@pytest.mark.parametrize(
    "name,audit,reason_prefix",
    POLICY_ONLY_REJECTIONS,
    ids=[row[0] for row in POLICY_ONLY_REJECTIONS],
)
def test_schema_valid_but_policy_rejected(
    name: str, audit: dict, reason_prefix: str
) -> None:
    assert schema_validation_errors(audit, _schema()) == [], (
        f"{name}: fixture is meant to be schema-valid, so only policy can reject it"
    )
    assert any(err.startswith(reason_prefix) for err in policy_errors(audit)), name
