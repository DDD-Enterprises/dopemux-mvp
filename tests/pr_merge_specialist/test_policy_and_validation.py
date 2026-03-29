from __future__ import annotations

from pathlib import Path

import pytest

from dopemux_pr_merge_specialist.policy import PolicyError, load_effective_policy, policy_artifact_payload
from dopemux_pr_merge_specialist.runtime import CommandResult, append_live_log
from dopemux_pr_merge_specialist.schema import ValidationStatus
from dopemux_pr_merge_specialist.validation import run_validation


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_policy_loads_and_has_fingerprint():
    policy = load_effective_policy(REPO_ROOT)
    payload = policy_artifact_payload(policy)
    assert payload["policy_schema_version"] == 1
    assert payload["policy_fingerprint"]
    assert payload["policy_source"] in {"repo", "bundled", "explicit"}
    assert policy["remote_check_repro"]["steps"]


def test_invalid_policy_fails_closed(tmp_path: Path):
    bad = tmp_path / "bad-policy.yaml"
    bad.write_text(
        "version: 1\nvalidation:\n  steps:\n    - name: broken\n      command: nope\n",
        encoding="utf-8",
    )
    with pytest.raises(PolicyError):
        load_effective_policy(REPO_ROOT, explicit_path=str(bad))


def test_invalid_remote_check_repro_step_fails_closed(tmp_path: Path):
    bad = tmp_path / "bad-policy.yaml"
    bad.write_text(
        """
version: 1
platform:
  supported: [darwin]
  unsupported: [windows]
  shell: posix
timeouts:
  subprocess_seconds: 30
  gh_seconds: 30
  phase_seconds: 30
validation:
  require_local_validation_for_merge_ready: true
  steps: []
remote_check_repro:
  steps:
    - command: [pytest, tests/]
      scope: repo
gates: {}
thread_rules: {}
check_rules: {}
conflict_rules: {}
safety:
  negative_allowlist: []
retry: {}
merge: {}
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(PolicyError, match="check_name"):
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


def test_append_live_log_creates_append_only_stable_lines(tmp_path: Path):
    log_path = tmp_path / "LIVE_LOG.txt"

    append_live_log(
        log_path,
        level="info",
        scope="queue",
        message="first line\nwith newline",
    )
    append_live_log(
        log_path,
        level="warning",
        scope="pr:42",
        message="second line",
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].endswith("[INFO] queue: first line with newline")
    assert lines[1].endswith("[WARNING] pr:42: second line")


def test_validation_scopes_commands_to_changed_pr_files(monkeypatch, tmp_path: Path):
    recorded_commands = []

    def fake_run_command(cmd, *, cwd=None, env=None, timeout_seconds=600):
        command = list(cmd)
        if command[:4] == ["git", "diff", "--name-only", "--diff-filter=ACMR"]:
            if command[-1].endswith("...HEAD"):
                return CommandResult(
                    command,
                    0,
                    "src/app.py\ndocs/02-how-to/guide.md\ntask-packets/packet.md\n",
                    "",
                )
            return CommandResult(command, 0, "src/local-only.py\n", "")
        if command[:4] == ["git", "ls-files", "--others", "--exclude-standard"]:
            return CommandResult(command, 0, "notes.tmp\n", "")
        raise AssertionError(f"Unexpected helper command: {command}")

    def fake_execute_or_dry_run(
        cmd, *, execute, cwd, commands_log, timeout_seconds=600
    ):
        recorded_commands.append(list(cmd))
        return CommandResult(list(cmd), 0, "", "")

    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.validation.run_command", fake_run_command
    )
    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.validation.execute_or_dry_run",
        fake_execute_or_dry_run,
    )

    policy = {
        "timeouts": {"subprocess_seconds": 30},
        "validation": {
            "require_local_validation_for_merge_ready": True,
            "steps": [
                {"name": "pre-commit", "command": ["pre-commit", "run"], "scope": "changed_files"},
                {
                    "name": "docs-frontmatter-fix",
                    "command": ["python", "scripts/docs_frontmatter_guard.py", "--fix"],
                    "scope": "docs_frontmatter_files",
                },
                {
                    "name": "docs-validator",
                    "command": ["python", "scripts/docs_validator.py"],
                    "scope": "docs_validator_files",
                },
            ],
        },
    }

    report = run_validation(
        repo_root=REPO_ROOT,
        worktree_path=tmp_path,
        policy=policy,
        execute=True,
        commands_log=tmp_path / "commands.txt",
        pr_id=1,
        head_sha="headsha",
        base_sha="basesha",
        policy_fingerprint="fingerprint",
        lifecycle_state="planned",
    )

    assert report.status == ValidationStatus.PASSED
    assert recorded_commands == [
        [
            "pre-commit",
            "run",
            "--files",
            "docs/02-how-to/guide.md",
            "notes.tmp",
            "src/app.py",
            "src/local-only.py",
            "task-packets/packet.md",
        ],
        [
            "python",
            "scripts/docs_frontmatter_guard.py",
            "--fix",
            "docs/02-how-to/guide.md",
            "task-packets/packet.md",
        ],
        [
            "python",
            "scripts/docs_validator.py",
            "docs/02-how-to/guide.md",
            "task-packets/packet.md",
        ],
    ]


def test_validation_skips_docs_steps_when_no_docs_changed(monkeypatch, tmp_path: Path):
    recorded_commands = []

    def fake_run_command(cmd, *, cwd=None, env=None, timeout_seconds=600):
        command = list(cmd)
        if command[:4] == ["git", "diff", "--name-only", "--diff-filter=ACMR"]:
            return CommandResult(command, 0, "src/app.py\n", "")
        if command[:4] == ["git", "ls-files", "--others", "--exclude-standard"]:
            return CommandResult(command, 0, "", "")
        raise AssertionError(f"Unexpected helper command: {command}")

    def fake_execute_or_dry_run(
        cmd, *, execute, cwd, commands_log, timeout_seconds=600
    ):
        recorded_commands.append(list(cmd))
        return CommandResult(list(cmd), 0, "", "")

    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.validation.run_command", fake_run_command
    )
    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.validation.execute_or_dry_run",
        fake_execute_or_dry_run,
    )

    policy = {
        "timeouts": {"subprocess_seconds": 30},
        "validation": {
            "require_local_validation_for_merge_ready": True,
            "steps": [
                {"name": "pre-commit", "command": ["pre-commit", "run"], "scope": "changed_files"},
                {
                    "name": "docs-validator",
                    "command": ["python", "scripts/docs_validator.py"],
                    "scope": "docs_validator_files",
                },
            ],
        },
    }

    report = run_validation(
        repo_root=REPO_ROOT,
        worktree_path=tmp_path,
        policy=policy,
        execute=True,
        commands_log=tmp_path / "commands.txt",
        pr_id=1,
        head_sha="headsha",
        base_sha="basesha",
        policy_fingerprint="fingerprint",
        lifecycle_state="planned",
    )

    assert report.status == ValidationStatus.PASSED
    assert recorded_commands == [["pre-commit", "run", "--files", "src/app.py"]]
    assert [step.status for step in report.steps] == ["passed", "skipped"]
