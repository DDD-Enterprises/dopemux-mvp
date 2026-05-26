from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "pr_steward"
SCHEMAS = ROOT / "schemas" / "pr_steward"


ARTIFACT_SCHEMAS = {
    "PR_STATE_SNAPSHOT.json": SCHEMAS / "pr_state_snapshot.schema.json",
    "REVIEW_ITEM_LEDGER.json": SCHEMAS / "review_item_ledger.schema.json",
    "THREAD_DISPOSITIONS.json": SCHEMAS / "thread_dispositions.schema.json",
    "CI_TRIAGE.json": SCHEMAS / "ci_triage.schema.json",
    "MERGE_READINESS.json": SCHEMAS / "merge_readiness.schema.json",
}


def run_intake(fixture_name: str, out_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_steward.intake",
            "--fixture-dir",
            str(FIXTURES / fixture_name),
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "704",
            "--out",
            str(out_dir),
            "--strict",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_artifacts(out_dir: Path) -> None:
    for artifact_name, schema_path in ARTIFACT_SCHEMAS.items():
        artifact = load_json(out_dir / artifact_name)
        schema = load_json(schema_path)
        Draft7Validator.check_schema(schema)
        errors = sorted(
            Draft7Validator(schema).iter_errors(artifact),
            key=lambda error: list(error.path),
        )
        assert errors == [], f"{artifact_name}: {[error.message for error in errors]}"


def test_ready_fixture_writes_all_artifacts_and_summary(tmp_path: Path) -> None:
    result = run_intake("ready_all_green", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    assert (tmp_path / "PR_STEWARD_SUMMARY.md").is_file()
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    assert readiness["readiness"] == "READY"
    assert readiness["mutation_performed"] is False
    snapshot = load_json(tmp_path / "PR_STATE_SNAPSHOT.json")
    assert snapshot["harvest_complete"] is True
    assert snapshot["mutation_performed"] is False


def test_ready_with_resolved_outdated_thread_records_nonblocking_evidence(
    tmp_path: Path,
) -> None:
    result = run_intake("ready_with_resolved_outdated_threads", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    threads = load_json(tmp_path / "THREAD_DISPOSITIONS.json")
    assert readiness["readiness"] == "READY"
    assert threads["unresolved_blocking_count"] == 0
    assert threads["threads"][0]["disposition"] == "AUTO_APPLIED"
    assert threads["threads"][0]["blocking"] is False


def test_forbidden_mutation_args_are_not_supported(tmp_path: Path) -> None:
    help_result = subprocess.run(
        [sys.executable, "-m", "tools.pr_steward.intake", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0
    for forbidden in (
        "--post-comment",
        "--resolve-thread",
        "--auto-merge",
        "--enqueue",
        "--apply-fixes",
    ):
        assert forbidden not in help_result.stdout

    mutation_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_steward.intake",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "704",
            "--out",
            str(tmp_path),
            "--fixture-dir",
            str(FIXTURES / "ready_all_green"),
            "--post-comment",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert mutation_result.returncode != 0
    assert "post-comment" in mutation_result.stderr


def test_script_wrapper_help() -> None:
    result = subprocess.run(
        [str(ROOT / "scripts" / "pr-steward"), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--fixture-dir" in result.stdout
    assert "--strict" in result.stdout


BLOCKING_CASES = [
    (
        "unknown_reviewer_blocks",
        "NEEDS_SUPERVISOR",
        "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
    ),
    ("unresolved_thread_blocks", "NEEDS_IMPLEMENTER", "UNRESOLVED_REVIEW_THREAD"),
    ("failed_check_blocks", "NEEDS_IMPLEMENTER", "FAILED_CHECK"),
    ("pending_check_not_ready", "NOT_READY", "PENDING_CHECK"),
    ("draft_pr_blocks", "BLOCKED", "PR_IS_DRAFT"),
    ("missing_auth_or_harvest_blocks", "BLOCKED", "HARVEST_INCOMPLETE"),
    ("skipped_required_audit_blocks", "NEEDS_SUPERVISOR", "EMBEDDED_AUDIT_SKIPPED"),
]


def test_blocking_fixtures_fail_closed(tmp_path: Path) -> None:
    for fixture_name, expected_readiness, expected_blocker in BLOCKING_CASES:
        out_dir = tmp_path / fixture_name
        result = run_intake(fixture_name, out_dir)

        assert result.returncode == 2, f"{fixture_name}: {result.stderr}"
        validate_artifacts(out_dir)
        readiness = load_json(out_dir / "MERGE_READINESS.json")
        ledger = load_json(out_dir / "REVIEW_ITEM_LEDGER.json")
        assert readiness["readiness"] == expected_readiness
        assert expected_blocker in readiness["blockers"]
        assert readiness["mutation_performed"] is False
        assert ledger["unclassified_count"] == 0
