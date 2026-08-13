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
REPORT_PATH = "proof/TP-DMX-TEST-LOCAL-AUDIT-ACCEPTANCE/AUDITOR_REPORT.md"


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
        r.startswith("local_audit_schema_invalid: /auditor_tool")
        for r in attestation["reasons"]
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
