from __future__ import annotations

from pathlib import Path

import pytest

from dopemux_pr_merge_specialist.policy import PolicyError, load_effective_policy, policy_artifact_payload
from dopemux_pr_merge_specialist.schema import ValidationStatus
from dopemux_pr_merge_specialist.validation import run_validation


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_policy_loads_and_has_fingerprint():
    policy = load_effective_policy(REPO_ROOT)
    payload = policy_artifact_payload(policy)
    assert payload["policy_schema_version"] == 1
    assert payload["policy_fingerprint"]
    assert payload["policy_source"] in {"repo", "bundled", "explicit"}


def test_invalid_policy_fails_closed(tmp_path: Path):
    bad = tmp_path / "bad-policy.yaml"
    bad.write_text(
        "version: 1\nvalidation:\n  steps:\n    - name: broken\n      command: nope\n",
        encoding="utf-8",
    )
    with pytest.raises(PolicyError):
        load_effective_policy(REPO_ROOT, explicit_path=str(bad))


def test_validation_dry_run_is_not_executed(tmp_path: Path):
    policy = load_effective_policy(REPO_ROOT)
    report = run_validation(
        repo_root=REPO_ROOT,
        worktree_path=tmp_path,
        policy=policy,
        execute=False,
        commands_log=tmp_path / "commands.txt",
        pr_id=1,
        head_sha="headsha",
        base_sha="basesha",
        policy_fingerprint=policy["_meta"]["fingerprint"],
        lifecycle_state="planned",
    )
    assert report.status == ValidationStatus.NOT_EXECUTED
    assert report.passed is False
    assert report.steps
    assert all(step.status == "planned" for step in report.steps)
