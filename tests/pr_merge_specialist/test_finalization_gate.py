from __future__ import annotations

import json
from pathlib import Path

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


HEAD_SHA = "abc123"


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


def _merge_readiness(*, readiness: str = "READY", audit_status: str = "PASS") -> dict:
    return {
        "generated_at": "2026-05-31T12:00:00Z",
        "readiness": readiness,
        "blockers": [],
        "pr": {
            "number": 203,
            "head_sha": HEAD_SHA,
            "head_ref": "feature/finalize",
        },
        "proof": {
            "proof_head_sha": HEAD_SHA,
            "proof_path": "proof/TP/PROOF.json",
        },
        "embedded_audit": {
            "status": audit_status,
            "source": "independent",
        },
    }


def _audit_proof(*, embedded_status: str = "PASS") -> dict:
    return {
        "generated_at": "2026-05-31T12:00:00Z",
        "head_sha": HEAD_SHA,
        "embedded_audit": {
            "status": embedded_status,
            "source": "independent",
        },
    }


def _gate_policy(pr_dir: Path) -> dict:
    return {
        "steward_gate": {
            "artifact_ttl_seconds": 3600,
            "merge_readiness_path": str(pr_dir / "MERGE_READINESS.json"),
            "audit_proof_path": str(pr_dir / "PROOF.json"),
        }
    }


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
