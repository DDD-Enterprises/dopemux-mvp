from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dopemux_pr_merge_specialist import merge, queue_drain
from dopemux_pr_merge_specialist.github_api import GitHubClient
from dopemux_pr_merge_specialist.runtime import CommandResult
from dopemux_pr_merge_specialist.schema import (
    BlockerType,
    Finding,
    FindingSeverity,
    MergeActionType,
    MergeDecision,
    PullRequestState,
    ValidationReport,
    ValidationStatus,
)
from dopemux_pr_merge_specialist.steward_gate import steward_gate


HEAD_SHA = "abc123"
_MISSING = object()
_NOT_REQUIRED_REASON = "AUDIT_NOT_REQUIRED_BY_TRUSTED_CHANGE_CONTRACT"


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _pr_state() -> PullRequestState:
    return PullRequestState(
        pr_id=203,
        title="finalize safely",
        author="dev",
        state="OPEN",
        base_ref="main",
        head_ref="feature/finalize",
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="APPROVED",
        head_sha=HEAD_SHA,
        base_sha="base123",
    )


def _merge_readiness(
    *,
    readiness: str = "READY",
    audit_status: object = "PASS",
    audit_required: object = _MISSING,
    audit_skip_reason: object = _MISSING,
    generated_at: str = "2026-05-31T12:00:00Z",
    head_sha: str = HEAD_SHA,
) -> dict:
    embedded_audit = {
        "status": audit_status,
        "source": "independent",
    }
    if audit_required is not _MISSING:
        embedded_audit["required"] = audit_required
    if audit_skip_reason is not _MISSING:
        embedded_audit["skip_reason"] = audit_skip_reason
    return {
        "generated_at": generated_at,
        "readiness": readiness,
        "blockers": [],
        "pr": {
            "number": 203,
            "head_sha": head_sha,
            "head_ref": "feature/finalize",
        },
        "proof": {
            "proof_head_sha": head_sha,
            "proof_path": "proof/TP/PROOF.json",
        },
        "embedded_audit": embedded_audit,
    }


def _audit_proof(
    *,
    embedded_status: object = "PASS",
    embedded_required: object = _MISSING,
    embedded_skip_reason: object = _MISSING,
    generated_at: str = "2026-05-31T12:00:00Z",
    head_sha: str = HEAD_SHA,
) -> dict:
    embedded_audit = {
        "status": embedded_status,
        "source": "independent",
    }
    if embedded_required is not _MISSING:
        embedded_audit["required"] = embedded_required
    if embedded_skip_reason is not _MISSING:
        embedded_audit["skip_reason"] = embedded_skip_reason
    return {
        "generated_at": generated_at,
        "head_sha": head_sha,
        "embedded_audit": embedded_audit,
    }


def _gate_policy(pr_dir: Path) -> dict:
    return {
        "steward_gate": {
            "artifact_ttl_seconds": 3600,
            "merge_readiness_path": str(pr_dir / "MERGE_READINESS.json"),
            "audit_proof_path": str(pr_dir / "PROOF.json"),
        }
    }


def _run_public_finalization_gate(
    gate_name: str,
    tmp_path: Path,
    *,
    readiness: dict | None = None,
    proof: dict | None = None,
):
    pr_dir = tmp_path / gate_name / "pr" / "203"
    readiness_path = _write_json(
        pr_dir / "MERGE_READINESS.json",
        readiness if readiness is not None else _merge_readiness(),
    )
    proof_path = _write_json(
        pr_dir / "PROOF.json",
        proof if proof is not None else _audit_proof(),
    )
    if gate_name == "steward_gate":
        return steward_gate(
            head_sha=HEAD_SHA,
            required_class="FINALIZATION",
            merge_readiness_path=readiness_path,
            audit_proof_path=proof_path,
            now=datetime(2026, 5, 31, 12, 30, tzinfo=timezone.utc),
            ttl_seconds=3600,
        )
    return queue_drain.require_steward_finalization_gate(
        pr=_pr_state(),
        policy=_gate_policy(pr_dir),
        pr_dir=pr_dir,
        now="2026-05-31T12:30:00Z",
    )


class RecordingClient:
    def __init__(self, payload: dict | None = None, result: CommandResult | None = None) -> None:
        self.payload = payload or {
            "id": "PR_node_id",
            "title": "Ready PR",
            "state": "OPEN",
            "headRefOid": HEAD_SHA,
        }
        self.result = result or CommandResult(
            command=["gh", "api", "graphql"],
            returncode=0,
            stdout='{"data":{"mergePullRequest":{"pullRequest":{"number":203,"merged":true}}}}',
            stderr="",
        )
        self.merge_calls: list[tuple[int, str, str]] = []

    def fetch_pr(self, pr_id: int) -> dict:
        return dict(self.payload)

    def invalidate(self, prefix: str) -> None:
        return None

    def merge_pull_request_expected_head(
        self,
        pr_id: int,
        *,
        expected_head_oid: str,
        method: str = "REBASE",
    ) -> CommandResult:
        self.merge_calls.append((pr_id, expected_head_oid, method))
        return self.result


class CapturingGitHubClient(GitHubClient):
    def __init__(self, tmp_path: Path) -> None:
        super().__init__(
            repo="DDD-Enterprises/dopemux-mvp",
            repo_root=tmp_path,
            policy={},
        )
        self.commands: list[list[str]] = []
        self.cache["pr:203"] = {
            "id": "PR_node_id",
            "headRefOid": HEAD_SHA,
        }

    def _run(self, cmd):
        self.commands.append(list(cmd))
        return CommandResult(list(cmd), 0, '{"data":{}}', "")


def _decision(action: MergeActionType = MergeActionType.REBASE_MERGE) -> MergeDecision:
    return MergeDecision(
        action=action,
        command=["gh", "pr", "merge", "203", "--rebase", "--delete-branch"],
        reason="ready",
        reason_code="rebase_merge_ready",
    )


def test_finalization_gate_allows_ready_with_strict_pass(tmp_path: Path):
    pr_dir = tmp_path / "pr" / "203"
    _write_json(pr_dir / "MERGE_READINESS.json", _merge_readiness())
    _write_json(pr_dir / "PROOF.json", _audit_proof())

    result = queue_drain.require_steward_finalization_gate(
        pr=_pr_state(),
        policy=_gate_policy(pr_dir),
        pr_dir=pr_dir,
        now="2026-05-31T12:30:00Z",
    )

    assert result.allowed is True
    assert result.reason_code == "ALLOW_FINALIZATION"
    assert result.evidence["merge_readiness"] == "READY"


def test_finalization_gate_does_not_double_prefix_rendered_relative_out_dir(
    monkeypatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)
    pr_dir = Path("proof/pr_merge/run_testrun/pr/203")
    _write_json(
        Path("proof/pr_merge/pr-steward/pr-203/MERGE_READINESS.json"),
        _merge_readiness(),
    )
    _write_json(Path("proof/pr_merge/embedded-audit/pr-203/PROOF.json"), _audit_proof())

    result = queue_drain.require_steward_finalization_gate(
        pr=_pr_state(),
        policy={
            "steward_gate": {
                "artifact_ttl_seconds": 3600,
                "merge_readiness_path": (
                    "{out_dir}/pr-steward/pr-{pr_id}/MERGE_READINESS.json"
                ),
                "audit_proof_path": "{out_dir}/embedded-audit/pr-{pr_id}/PROOF.json",
            }
        },
        pr_dir=pr_dir,
        now="2026-05-31T12:30:00Z",
    )

    assert result.allowed is True
    assert result.reason_code == "ALLOW_FINALIZATION"


def test_finalization_gate_denies_pass_with_risks(tmp_path: Path):
    pr_dir = tmp_path / "pr" / "203"
    _write_json(pr_dir / "MERGE_READINESS.json", _merge_readiness(audit_status="PASS_WITH_RISKS"))
    _write_json(pr_dir / "PROOF.json", _audit_proof(embedded_status="PASS"))

    result = queue_drain.require_steward_finalization_gate(
        pr=_pr_state(),
        policy=_gate_policy(pr_dir),
        pr_dir=pr_dir,
        now="2026-05-31T12:30:00Z",
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_AUDIT_NOT_STRICT_PASS"


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
def test_public_finalization_gates_allow_strict_pass(gate_name: str, tmp_path: Path):
    result = _run_public_finalization_gate(gate_name, tmp_path)

    assert result.allowed is True
    assert result.reason_code == "ALLOW_FINALIZATION"


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
def test_public_finalization_gates_allow_exact_not_required(
    gate_name: str, tmp_path: Path
):
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=_merge_readiness(
            audit_status="SKIPPED",
            audit_required=False,
            audit_skip_reason=_NOT_REQUIRED_REASON,
        ),
        proof=_audit_proof(
            embedded_status="SKIPPED",
            embedded_required=False,
            embedded_skip_reason=_NOT_REQUIRED_REASON,
        ),
    )

    assert result.allowed is True
    assert result.reason_code == "ALLOW_FINALIZATION"


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
@pytest.mark.parametrize(
    ("merge_status", "proof_status"),
    [
        ("PASS_WITH_RISKS", "PASS"),
        ("PASS", "PASS_WITH_RISKS"),
    ],
)
def test_public_finalization_gates_deny_pass_with_risks(
    gate_name: str,
    merge_status: str,
    proof_status: str,
    tmp_path: Path,
):
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=_merge_readiness(audit_status=merge_status),
        proof=_audit_proof(embedded_status=proof_status),
    )

    assert result.allowed is False
    if gate_name == "queue_drain":
        assert result.reason_code == "DENY_AUDIT_NOT_STRICT_PASS"


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
@pytest.mark.parametrize("not_required_side", ["merge", "proof"])
def test_public_finalization_gates_deny_mixed_pass_and_not_required(
    gate_name: str,
    not_required_side: str,
    tmp_path: Path,
):
    readiness = _merge_readiness()
    proof = _audit_proof()
    if not_required_side == "merge":
        readiness = _merge_readiness(
            audit_status="SKIPPED",
            audit_required=False,
            audit_skip_reason=_NOT_REQUIRED_REASON,
        )
    else:
        proof = _audit_proof(
            embedded_status="SKIPPED",
            embedded_required=False,
            embedded_skip_reason=_NOT_REQUIRED_REASON,
        )

    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=readiness,
        proof=proof,
    )

    assert result.allowed is False


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
@pytest.mark.parametrize("artifact_side", ["merge", "proof"])
@pytest.mark.parametrize(
    "required",
    [_MISSING, True, None, 0, "false", [], {}],
    ids=["missing", "true", "null", "zero", "string", "list", "dict"],
)
def test_public_finalization_gates_deny_noncanonical_not_required_required(
    gate_name: str,
    artifact_side: str,
    required: object,
    tmp_path: Path,
):
    readiness = _merge_readiness(
        audit_status="SKIPPED",
        audit_required=False,
        audit_skip_reason=_NOT_REQUIRED_REASON,
    )
    proof = _audit_proof(
        embedded_status="SKIPPED",
        embedded_required=False,
        embedded_skip_reason=_NOT_REQUIRED_REASON,
    )
    if artifact_side == "merge":
        readiness = _merge_readiness(
            audit_status="SKIPPED",
            audit_required=required,
            audit_skip_reason=_NOT_REQUIRED_REASON,
        )
    else:
        proof = _audit_proof(
            embedded_status="SKIPPED",
            embedded_required=required,
            embedded_skip_reason=_NOT_REQUIRED_REASON,
        )
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=readiness,
        proof=proof,
    )

    assert result.allowed is False


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
@pytest.mark.parametrize("artifact_side", ["merge", "proof"])
@pytest.mark.parametrize(
    "skip_reason",
    [_MISSING, None, "", "AUDIT_NOT_REQUIRED", 0, [], {}],
    ids=["missing", "null", "empty", "wrong", "zero", "list", "dict"],
)
def test_public_finalization_gates_deny_noncanonical_not_required_reason(
    gate_name: str,
    artifact_side: str,
    skip_reason: object,
    tmp_path: Path,
):
    readiness = _merge_readiness(
        audit_status="SKIPPED",
        audit_required=False,
        audit_skip_reason=_NOT_REQUIRED_REASON,
    )
    proof = _audit_proof(
        embedded_status="SKIPPED",
        embedded_required=False,
        embedded_skip_reason=_NOT_REQUIRED_REASON,
    )
    if artifact_side == "merge":
        readiness = _merge_readiness(
            audit_status="SKIPPED",
            audit_required=False,
            audit_skip_reason=skip_reason,
        )
    else:
        proof = _audit_proof(
            embedded_status="SKIPPED",
            embedded_required=False,
            embedded_skip_reason=skip_reason,
        )
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=readiness,
        proof=proof,
    )

    assert result.allowed is False


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
@pytest.mark.parametrize("artifact_side", ["merge", "proof"])
@pytest.mark.parametrize(
    "status",
    [_MISSING, None, "", "pass", "skipped", "UNKNOWN", [], {}],
    ids=["missing", "null", "empty", "lower-pass", "lower-skipped", "unknown", "list", "dict"],
)
def test_public_finalization_gates_deny_noncanonical_or_malformed_status(
    gate_name: str,
    artifact_side: str,
    status: object,
    tmp_path: Path,
):
    readiness = _merge_readiness(
        audit_status="SKIPPED",
        audit_required=False,
        audit_skip_reason=_NOT_REQUIRED_REASON,
    )
    proof = _audit_proof(
        embedded_status="SKIPPED",
        embedded_required=False,
        embedded_skip_reason=_NOT_REQUIRED_REASON,
    )
    if artifact_side == "merge":
        readiness["embedded_audit"]["status"] = status
        if status is _MISSING:
            readiness["embedded_audit"].pop("status")
    else:
        proof["embedded_audit"]["status"] = status
        if status is _MISSING:
            proof["embedded_audit"].pop("status")
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=readiness,
        proof=proof,
    )

    assert result.allowed is False


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
def test_public_finalization_gates_preserve_raw_audit_metadata(
    gate_name: str, tmp_path: Path
):
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=_merge_readiness(
            audit_status="skipped",
            audit_required=0,
            audit_skip_reason=[_NOT_REQUIRED_REASON],
        ),
        proof=_audit_proof(
            embedded_status={"status": "SKIPPED"},
            embedded_required="false",
            embedded_skip_reason=None,
        ),
    )

    assert result.allowed is False
    assert result.evidence["merge_embedded_audit_status"] == "skipped"
    assert result.evidence["merge_embedded_audit_required"] == 0
    assert result.evidence["merge_embedded_audit_skip_reason"] == [
        _NOT_REQUIRED_REASON
    ]
    assert result.evidence["proof_embedded_audit_status"] == {"status": "SKIPPED"}
    assert result.evidence["proof_embedded_audit_required"] == "false"
    assert result.evidence["proof_embedded_audit_skip_reason"] is None


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
def test_public_finalization_gates_deny_stale_not_required_evidence(
    gate_name: str, tmp_path: Path
):
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=_merge_readiness(
            audit_status="SKIPPED",
            audit_required=False,
            audit_skip_reason=_NOT_REQUIRED_REASON,
            generated_at="2026-05-31T10:00:00Z",
        ),
        proof=_audit_proof(
            embedded_status="SKIPPED",
            embedded_required=False,
            embedded_skip_reason=_NOT_REQUIRED_REASON,
        ),
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_STALE_ARTIFACT"


@pytest.mark.parametrize("gate_name", ["steward_gate", "queue_drain"])
def test_public_finalization_gates_deny_head_mismatch_for_not_required_evidence(
    gate_name: str, tmp_path: Path
):
    result = _run_public_finalization_gate(
        gate_name,
        tmp_path,
        readiness=_merge_readiness(
            audit_status="SKIPPED",
            audit_required=False,
            audit_skip_reason=_NOT_REQUIRED_REASON,
        ),
        proof=_audit_proof(
            embedded_status="SKIPPED",
            embedded_required=False,
            embedded_skip_reason=_NOT_REQUIRED_REASON,
            head_sha="mismatched-head",
        ),
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_SHA_MISMATCH"


def test_remediation_gate_preserves_status_normalization_and_pass_with_risks(
    tmp_path: Path,
):
    readiness = _merge_readiness(
        readiness="NEEDS_IMPLEMENTER",
        audit_status="pass_with_risks",
    )
    proof = _audit_proof(embedded_status="pass")
    readiness_path = _write_json(tmp_path / "MERGE_READINESS.json", readiness)
    proof_path = _write_json(tmp_path / "PROOF.json", proof)

    result = steward_gate(
        head_sha=HEAD_SHA,
        required_class="REMEDIATION",
        merge_readiness_path=readiness_path,
        audit_proof_path=proof_path,
        now=datetime(2026, 5, 31, 12, 30, tzinfo=timezone.utc),
        ttl_seconds=3600,
    )

    assert result.allowed is True
    assert result.evidence["merge_embedded_audit_status"] == "PASS_WITH_RISKS"
    assert result.evidence["proof_embedded_audit_status"] == "PASS"


def test_run_merge_uses_graphql_expected_head_oid_without_shell_fallback(monkeypatch, tmp_path: Path):
    shell_calls = []
    monkeypatch.setattr(merge, "execute_or_dry_run", lambda *args, **kwargs: shell_calls.append(args) or CommandResult([], 0, "", ""))
    client = RecordingClient()

    result = merge.run_merge_with_fallback(
        decision=_decision(),
        pr_id=203,
        execute=True,
        repo=None,
        commands_log=tmp_path / "COMMANDS_RUN.txt",
        repo_root=tmp_path,
        policy={"timeouts": {"subprocess_seconds": 5}},
        client=client,
    )

    assert result.action == MergeActionType.REBASE_MERGE
    assert result.reason_code == "expected_head_merge_succeeded"
    assert client.merge_calls == [(203, HEAD_SHA, "REBASE")]
    assert shell_calls == []


def test_run_merge_uses_gated_expected_head_oid_when_pr_head_moves(monkeypatch, tmp_path: Path):
    shell_calls = []
    monkeypatch.setattr(merge, "execute_or_dry_run", lambda *args, **kwargs: shell_calls.append(args) or CommandResult([], 0, "", ""))
    client = RecordingClient(
        payload={
            "id": "PR_node_id",
            "title": "Ready PR",
            "state": "OPEN",
            "headRefOid": "new-unaudited-head",
        }
    )

    result = merge.run_merge_with_fallback(
        decision=_decision(),
        pr_id=203,
        execute=True,
        repo=None,
        commands_log=tmp_path / "COMMANDS_RUN.txt",
        repo_root=tmp_path,
        policy={"timeouts": {"subprocess_seconds": 5}},
        client=client,
        expected_head_oid=HEAD_SHA,
    )

    assert result.action == MergeActionType.REBASE_MERGE
    assert result.reason_code == "expected_head_merge_succeeded"
    assert client.merge_calls == [(203, HEAD_SHA, "REBASE")]
    assert shell_calls == []


def test_graphql_expected_head_merge_does_not_use_pr_command_repo_flag(tmp_path: Path):
    client = CapturingGitHubClient(tmp_path)

    result = client.merge_pull_request_expected_head(
        203,
        expected_head_oid=HEAD_SHA,
        method="REBASE",
    )

    assert result.returncode == 0
    assert client.commands
    assert client.commands[0][:3] == ["gh", "api", "graphql"]
    assert "--repo" not in client.commands[0]


def test_run_merge_blocks_when_expected_head_oid_is_unknown(monkeypatch, tmp_path: Path):
    shell_calls = []
    monkeypatch.setattr(merge, "execute_or_dry_run", lambda *args, **kwargs: shell_calls.append(args) or CommandResult([], 0, "", ""))
    client = RecordingClient(payload={"id": "PR_node_id", "title": "Ready PR", "state": "OPEN"})

    result = merge.run_merge_with_fallback(
        decision=_decision(),
        pr_id=203,
        execute=True,
        repo=None,
        commands_log=tmp_path / "COMMANDS_RUN.txt",
        repo_root=tmp_path,
        policy={},
        client=client,
    )

    assert result.action == MergeActionType.BLOCKED
    assert result.reason_code == "expected_head_oid_unknown"
    assert "UNKNOWN" in result.reason
    assert client.merge_calls == []
    assert shell_calls == []


def test_auto_merge_execution_is_disabled_by_default(tmp_path: Path):
    client = RecordingClient()

    result = merge.run_merge_with_fallback(
        decision=_decision(MergeActionType.AUTO_MERGE_FALLBACK),
        pr_id=203,
        execute=True,
        repo=None,
        commands_log=tmp_path / "COMMANDS_RUN.txt",
        repo_root=tmp_path,
        policy={},
        client=client,
    )

    assert result.action == MergeActionType.BLOCKED
    assert result.reason_code == "governed_automerge_disabled"


def test_governed_auto_merge_uses_gated_expected_head_oid(monkeypatch, tmp_path: Path):
    calls = []

    def fake_execute(command, **kwargs):
        calls.append((list(command), kwargs))
        return CommandResult(list(command), 0, "", "")

    monkeypatch.setattr(merge, "execute_or_dry_run", fake_execute)
    client = RecordingClient(
        payload={
            "id": "PR_node_id",
            "title": "Ready PR",
            "state": "OPEN",
            "headRefOid": "new-unaudited-head",
        }
    )

    result = merge.run_merge_with_fallback(
        decision=_decision(MergeActionType.AUTO_MERGE_FALLBACK),
        pr_id=203,
        execute=True,
        repo="DDD-Enterprises/dopemux-mvp",
        commands_log=tmp_path / "COMMANDS_RUN.txt",
        repo_root=tmp_path,
        policy={
            "merge": {"allow_governed_automerge": True},
            "timeouts": {"subprocess_seconds": 5},
        },
        client=client,
        expected_head_oid=HEAD_SHA,
    )

    assert result.action == MergeActionType.AUTO_MERGE_FALLBACK
    assert calls
    command = calls[0][0]
    assert command == [
        "gh",
        "pr",
        "merge",
        "203",
        "--auto",
        "--rebase",
        "--match-head-commit",
        HEAD_SHA,
        "--repo",
        "DDD-Enterprises/dopemux-mvp",
    ]


def test_governed_auto_merge_blocks_without_expected_head_oid(monkeypatch, tmp_path: Path):
    calls = []
    monkeypatch.setattr(
        merge,
        "execute_or_dry_run",
        lambda *args, **kwargs: calls.append((args, kwargs)) or CommandResult([], 0, "", ""),
    )
    client = RecordingClient()

    result = merge.run_merge_with_fallback(
        decision=_decision(MergeActionType.AUTO_MERGE_FALLBACK),
        pr_id=203,
        execute=True,
        repo=None,
        commands_log=tmp_path / "COMMANDS_RUN.txt",
        repo_root=tmp_path,
        policy={"merge": {"allow_governed_automerge": True}},
        client=client,
    )

    assert result.action == MergeActionType.BLOCKED
    assert result.reason_code == "expected_head_oid_unknown"
    assert calls == []


def test_approval_missing_does_not_admin_bypass_without_supervisor():
    report = ValidationReport(
        status=ValidationStatus.PASSED,
        required_for_merge_ready=True,
        steps=[],
        attempts=1,
        remediation_applied=False,
    )
    findings = [
        Finding(
            kind=FindingSeverity.BLOCKER,
            finding_type=BlockerType.APPROVAL_MISSING.value,
            message="Approval missing",
        )
    ]

    result = merge.decide_merge_action(
        pr=_pr_state(),
        findings=findings,
        validation_report=report,
    )

    assert result.action == MergeActionType.BLOCKED
    assert result.reason_code == "supervisor_required_for_admin_bypass"
