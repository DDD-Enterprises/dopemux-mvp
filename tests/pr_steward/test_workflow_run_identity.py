"""Tests for TP-DMX-AUDIT-STEWARD-CONTRACT-HYGIENE-001 Slice 2:
extracted embedded-audit workflow-run identity validation.

These mirror, one-for-one, the branches of the inline Python previously
embedded in the "Validate audit workflow-run identity" step of
`.github/workflows/pr-steward.yml`. The workflow now calls
`validate_run_identity` directly; these tests are the behavioral contract
that extraction must not weaken.
"""
from __future__ import annotations

from tools.pr_steward.workflow_run_identity import validate_run_identity

EXPECTED_REPO = "DDD-Enterprises/dopemux-mvp"
EXPECTED_RUN_ID = 555


def _base_run(**overrides) -> dict:
    run = {
        "id": EXPECTED_RUN_ID,
        "repository": {"full_name": EXPECTED_REPO},
        "name": "embedded-audit",
        "path": ".github/workflows/embedded-audit.yml",
        "status": "completed",
        "head_sha": "a" * 40,
        "conclusion": "success",
    }
    run.update(overrides)
    return run


def _validate(run):
    return validate_run_identity(
        run, expected_run_id=EXPECTED_RUN_ID, expected_repo=EXPECTED_REPO
    )


class TestCorrectIdentity:
    def test_correct_workflow_and_repository_is_ok(self) -> None:
        result = _validate(_base_run())
        assert result.ok is True
        assert result.errors == ()
        assert result.run_head_sha == "a" * 40
        assert result.conclusion == "success"
        assert result.conclusion_ok is True
        assert result.workflow_name == "embedded-audit"
        assert result.workflow_path == ".github/workflows/embedded-audit.yml"

    def test_pr_number_extracted_when_available(self) -> None:
        run = _base_run(pull_requests=[{"number": 704}])
        result = _validate(run)
        assert result.pr_number == 704

    def test_pr_number_none_when_absent(self) -> None:
        result = _validate(_base_run())
        assert result.pr_number is None


class TestWorkflowMismatch:
    def test_wrong_workflow_name_fails(self) -> None:
        result = _validate(_base_run(name="some-other-workflow"))
        assert result.ok is False
        assert any(err.startswith("workflow_mismatch:") for err in result.errors)

    def test_wrong_workflow_path_fails(self) -> None:
        result = _validate(_base_run(path=".github/workflows/other.yml"))
        assert result.ok is False
        assert any(err.startswith("workflow_mismatch:") for err in result.errors)


class TestRepositoryMismatch:
    def test_wrong_repository_fails(self) -> None:
        result = _validate(_base_run(repository={"full_name": "someone-else/other-repo"}))
        assert result.ok is False
        assert any(err.startswith("repository_mismatch:") for err in result.errors)

    def test_missing_repository_fails(self) -> None:
        result = _validate(_base_run(repository={}))
        assert result.ok is False
        assert "repository_missing: actions run lacks repository.full_name" in result.errors

    def test_repository_not_a_mapping_treated_as_missing(self) -> None:
        result = _validate(_base_run(repository=None))
        assert result.ok is False
        assert "repository_missing: actions run lacks repository.full_name" in result.errors


class TestRunNotCompleted:
    def test_run_not_completed_fails(self) -> None:
        result = _validate(_base_run(status="in_progress"))
        assert result.ok is False
        assert any(err.startswith("run_not_completed:") for err in result.errors)


class TestMissingRequiredField:
    def test_missing_run_id_fails_mismatch(self) -> None:
        run = _base_run()
        del run["id"]
        result = _validate(run)
        assert result.ok is False
        assert any(err.startswith("run_id_mismatch:") for err in result.errors)

    def test_missing_head_sha_fails(self) -> None:
        run = _base_run()
        del run["head_sha"]
        result = _validate(run)
        assert result.ok is False
        assert "run_head_sha_missing" in result.errors

    def test_missing_conclusion_fails(self) -> None:
        run = _base_run()
        del run["conclusion"]
        result = _validate(run)
        assert result.ok is False
        assert "run_conclusion_missing" in result.errors


class TestMalformedPayload:
    def test_malformed_payload_not_a_mapping(self) -> None:
        result = _validate("not-a-mapping")
        assert result.ok is False
        assert result.errors == ("malformed_run_payload: run is not a mapping",)
        assert result.run_head_sha == ""
        assert result.conclusion == ""
        assert result.conclusion_ok is False
        assert result.pr_number is None

    def test_malformed_payload_none(self) -> None:
        result = _validate(None)
        assert result.ok is False
        assert result.errors == ("malformed_run_payload: run is not a mapping",)


class TestNonSuccessConclusionPreservesCandidateBinding:
    def test_failure_conclusion_still_binds_head_sha_and_reports_failure_posture(
        self,
    ) -> None:
        run = _base_run(conclusion="failure")
        result = _validate(run)
        # Identity itself is otherwise valid: workflow/repo/status/head_sha all
        # check out, so `ok` reflects only identity, not audit outcome.
        assert result.ok is True
        assert result.run_head_sha == "a" * 40
        assert result.conclusion == "failure"
        assert result.conclusion_ok is False

    def test_cancelled_conclusion_still_binds_head_sha(self) -> None:
        run = _base_run(conclusion="cancelled")
        result = _validate(run)
        assert result.ok is True
        assert result.run_head_sha == "a" * 40
        assert result.conclusion == "cancelled"
        assert result.conclusion_ok is False
