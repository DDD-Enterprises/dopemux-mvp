from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft7Validator

from tools.pr_steward import collector
from tools.pr_steward.classifier import build_artifacts


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


def test_resolved_thread_clears_review_comment_block(
    tmp_path: Path,
) -> None:
    result = run_intake("resolved_thread_clears_review_item", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    ledger = load_json(tmp_path / "REVIEW_ITEM_LEDGER.json")
    threads = load_json(tmp_path / "THREAD_DISPOSITIONS.json")
    review_comment_items = [
        item for item in ledger["items"] if item["source"] == "review_comment"
    ]
    assert readiness["readiness"] == "READY"
    assert "REVIEW_ITEM_MUST_FIX" not in readiness["blockers"]
    assert "UNRESOLVED_REVIEW_THREAD" not in readiness["blockers"]
    assert review_comment_items[0]["disposition"] == "AUTO_APPLIED"
    assert review_comment_items[0]["blocking"] is False
    assert threads["threads"][0]["disposition"] == "OPTIONAL_DEFERRED"


def test_outdated_resolved_thread_nonblocking(
    tmp_path: Path,
) -> None:
    result = run_intake("outdated_resolved_thread_nonblocking", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    ledger = load_json(tmp_path / "REVIEW_ITEM_LEDGER.json")
    threads = load_json(tmp_path / "THREAD_DISPOSITIONS.json")
    review_comment_items = [
        item for item in ledger["items"] if item["source"] == "review_comment"
    ]
    assert readiness["readiness"] == "READY"
    assert threads["threads"][0]["disposition"] == "AUTO_APPLIED"
    assert review_comment_items[0]["disposition"] == "AUTO_APPLIED"
    assert review_comment_items[0]["blocking"] is False


def test_raw_review_comment_without_thread_still_blocks(
    tmp_path: Path,
) -> None:
    result = run_intake("raw_review_comment_without_thread_still_blocks", tmp_path)

    assert result.returncode == 2, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    ledger = load_json(tmp_path / "REVIEW_ITEM_LEDGER.json")
    assert readiness["readiness"] == "NEEDS_IMPLEMENTER"
    assert "REVIEW_ITEM_MUST_FIX" in readiness["blockers"]
    assert ledger["items"][0]["disposition"] == "MUST_FIX"
    assert ledger["items"][0]["blocking"] is True


def test_unresolved_thread_still_blocks(
    tmp_path: Path,
) -> None:
    result = run_intake("unresolved_thread_still_blocks", tmp_path)

    assert result.returncode == 2, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    threads = load_json(tmp_path / "THREAD_DISPOSITIONS.json")
    assert readiness["readiness"] == "NEEDS_IMPLEMENTER"
    assert "UNRESOLVED_REVIEW_THREAD" in readiness["blockers"]
    assert threads["threads"][0]["disposition"] == "MUST_FIX"


def test_proof_current_exact_head_ready(tmp_path: Path) -> None:
    result = run_intake("proof_current_exact_head_ready", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    assert readiness["readiness"] == "READY"
    assert readiness["proof"]["proof_freshness"]["status"] == "CURRENT"
    assert readiness["proof"]["matches_pr_head"] is True


def test_proof_self_reference_exception_ready(tmp_path: Path) -> None:
    result = run_intake("proof_self_reference_exception_ready_or_needs_supervisor", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    assert readiness["readiness"] == "READY"
    assert (
        readiness["proof"]["proof_freshness"]["status"]
        == "CURRENT_WITH_SELF_REFERENCE_EXCEPTION"
    )
    assert readiness["proof"]["matches_pr_head"] is False


def test_proof_self_reference_exception_rejects_runtime_changes(
    tmp_path: Path,
) -> None:
    result = run_intake(
        "proof_self_reference_exception_rejects_runtime_changes",
        tmp_path,
    )

    assert result.returncode == 2, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    assert readiness["readiness"] == "NEEDS_SUPERVISOR"
    assert "PROOF_STALE_OR_MISSING" in readiness["blockers"]


def test_embedded_audit_pass_with_risks_nonblocking(tmp_path: Path) -> None:
    result = run_intake("embedded_audit_pass_with_risks_nonblocking", tmp_path)

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    assert readiness["readiness"] == "READY"
    assert readiness["embedded_audit"]["status"] == "PASS_WITH_RISKS"


def test_pr713_like_resolved_threads_with_pass_with_risks_audit(
    tmp_path: Path,
) -> None:
    result = run_intake(
        "pr713_like_resolved_threads_with_pass_with_risks_audit",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    validate_artifacts(tmp_path)
    readiness = load_json(tmp_path / "MERGE_READINESS.json")
    assert readiness["readiness"] == "READY"
    assert "REVIEW_ITEM_MUST_FIX" not in readiness["blockers"]
    assert "UNRESOLVED_REVIEW_THREAD" not in readiness["blockers"]


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
    assert "--proof-path" in result.stdout
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


def test_optional_checks_without_required_metadata_do_not_block_ready() -> None:
    harvest = base_ready_harvest()
    harvest["checks"] = [
        {"name": "optional-skipped", "status": "COMPLETED", "conclusion": "SKIPPED"},
        {"name": "optional-failed", "status": "COMPLETED", "conclusion": "FAILURE"},
        {"name": "optional-pending", "status": "IN_PROGRESS", "conclusion": None},
    ]

    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
    )

    readiness = artifacts["MERGE_READINESS.json"]
    assert isinstance(readiness, dict)
    ci_triage = artifacts["CI_TRIAGE.json"]
    assert isinstance(ci_triage, dict)
    assert readiness["readiness"] == "READY"
    assert readiness["blockers"] == []
    assert ci_triage["required_check_count"] == 0
    assert ci_triage["failed_required_count"] == 0
    assert ci_triage["pending_required_count"] == 0
    assert all(check["required"] is False for check in ci_triage["checks"])


def test_live_collection_uses_proof_path_for_ready_state(
    tmp_path: Path, monkeypatch
) -> None:
    pr_head = "a" * 40
    proof_path = tmp_path / "PROOF.json"
    proof_path.write_text(
        json.dumps(
            {
                "head_sha": pr_head,
                "embedded_audit": {
                    "status": "PASS_WITH_RISKS",
                    "report_path": "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md",
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:3] == ["gh", "pr", "view"]:
            return subprocess.CompletedProcess(
                args,
                0,
                json.dumps(base_pr_payload(head_sha=pr_head)),
                "",
            )
        raise AssertionError(f"unexpected gh command: {args}")

    monkeypatch.setattr(collector, "_run", fake_run)
    monkeypatch.setattr(collector, "_fetch_review_threads", lambda **_: ([], []))

    harvest = collector.collect_from_github(
        "DDD-Enterprises/dopemux-mvp",
        704,
        proof_path=proof_path,
    )
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
    )

    readiness = artifacts["MERGE_READINESS.json"]
    assert isinstance(readiness, dict)
    assert readiness["readiness"] == "READY"
    assert readiness["embedded_audit"]["status"] == "PASS_WITH_RISKS"
    assert readiness["proof"]["proof_head_sha"] == pr_head
    assert readiness["proof"]["matches_pr_head"] is True
    assert readiness["proof"]["proof_freshness"]["status"] == "CURRENT"


def test_trusted_author_association_is_nonblocking() -> None:
    harvest = base_ready_harvest()
    harvest["reviews"] = [
        {
            "id": "R_MEMBER",
            "author": {"login": "new-team-member"},
            "authorAssociation": "MEMBER",
            "state": "APPROVED",
            "body": "Looks fine.",
        }
    ]

    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
    )

    readiness = artifacts["MERGE_READINESS.json"]
    assert isinstance(readiness, dict)
    ledger = artifacts["REVIEW_ITEM_LEDGER.json"]
    assert isinstance(ledger, dict)
    assert readiness["readiness"] == "READY"
    assert "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION" not in readiness["blockers"]
    assert ledger["items"][0]["author"] == "new-team-member"
    assert ledger["items"][0]["blocking"] is False


def test_trusted_p1_review_body_blocks_readiness() -> None:
    harvest = base_ready_harvest()
    harvest["reviews"] = [
        {
            "id": "R_P1",
            "author": {"login": "hu3mann"},
            "state": "COMMENTED",
            "body": "P1: fix this before merge.",
        }
    ]

    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
    )

    readiness = artifacts["MERGE_READINESS.json"]
    assert isinstance(readiness, dict)
    ledger = artifacts["REVIEW_ITEM_LEDGER.json"]
    assert isinstance(ledger, dict)
    assert readiness["readiness"] == "NEEDS_IMPLEMENTER"
    assert "REVIEW_ITEM_MUST_FIX" in readiness["blockers"]
    assert ledger["items"][0]["disposition"] == "MUST_FIX"
    assert ledger["items"][0]["blocking"] is True


def test_needs_supervisor_comment_body_blocks_readiness() -> None:
    harvest = base_ready_harvest()
    harvest["issue_comments"] = [
        {
            "id": "IC_SUPERVISOR",
            "author": {"login": "hu3mann"},
            "body": "Needs supervisor before merge.",
        }
    ]

    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
    )

    readiness = artifacts["MERGE_READINESS.json"]
    assert isinstance(readiness, dict)
    assert readiness["readiness"] == "NEEDS_SUPERVISOR"
    assert "REVIEW_ITEM_NEEDS_SUPERVISOR" in readiness["blockers"]


def test_required_skipped_check_is_successful_nonblocking() -> None:
    harvest = base_ready_harvest()
    harvest["checks"] = [
        {
            "name": "required-skipped",
            "status": "COMPLETED",
            "conclusion": "SKIPPED",
            "required": True,
        }
    ]

    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
    )

    readiness = artifacts["MERGE_READINESS.json"]
    assert isinstance(readiness, dict)
    ci_triage = artifacts["CI_TRIAGE.json"]
    assert isinstance(ci_triage, dict)
    assert readiness["readiness"] == "READY"
    assert "FAILED_CHECK" not in readiness["blockers"]
    assert ci_triage["required_check_count"] == 1
    assert ci_triage["failed_required_count"] == 0


def base_ready_harvest() -> dict:
    head_sha = "head000000000000000000000000000000000000"
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": base_pr_payload(head_sha=head_sha),
        "changed_files": [{"path": "tools/pr_steward/intake.py", "additions": 1}],
        "commits": [{"oid": head_sha, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": head_sha,
            }
        ],
        "embedded_audit": {
            "status": "PASS",
            "report_path": "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md",
        },
        "proof": {
            "proof_path": "proof/TP-DMX-PR-STEWARD-001/PROOF.json",
            "proof_head_sha": head_sha,
            "matches_pr_head": True,
        },
    }


def base_pr_payload(*, head_sha: str) -> dict:
    return {
        "number": 704,
        "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/704",
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "APPROVED",
        "baseRefName": "main",
        "baseRefOid": "base000000000000000000000000000000000000",
        "headRefName": "codex/tp-dmx-pr-steward-001",
        "headRefOid": head_sha,
        "author": {"login": "hu3mann"},
        "createdAt": "2026-05-26T01:00:00Z",
        "updatedAt": "2026-05-26T02:00:00Z",
        "files": [{"path": "tools/pr_steward/intake.py", "additions": 1}],
        "commits": [{"oid": head_sha, "messageHeadline": "test"}],
        "reviews": [],
        "comments": [],
        "statusCheckRollup": [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": head_sha,
            }
        ],
    }
