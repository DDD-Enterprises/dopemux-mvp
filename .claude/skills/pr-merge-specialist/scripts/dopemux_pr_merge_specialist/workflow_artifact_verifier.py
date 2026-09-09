"""Authenticate local evidence against an exact GitHub Actions artifact."""
from __future__ import annotations

import io
import json
import re
import stat
import zipfile
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .github_api import GITHUB_ACTIONS_DETAILS_URL_RE, GitHubClient

WORKFLOW_PATH = ".github/workflows/embedded-audit.yml"
PR_STEWARD_WORKFLOW_PATH = ".github/workflows/pr-steward.yml"
PR_STEWARD_READINESS_CONTEXT = "PR Steward / final readiness"
PROOF_MEMBER = "PROOF.json"
READINESS_MEMBER = "MERGE_READINESS.json"
SOURCE_RECEIPT_MEMBER = "PR_STEWARD_SOURCE_RECEIPT.json"
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_PROOF_BYTES = 2 * 1024 * 1024
MAX_READINESS_BYTES = 2 * 1024 * 1024
MAX_SOURCE_RECEIPT_BYTES = 64 * 1024


class WorkflowArtifactError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise WorkflowArtifactError(reason)


def _object(value: Any) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), "metadata_object_required")
    return value


def _positive_id(value: Any) -> bool:
    return type(value) is int and value > 0


def _timestamp(value: Any) -> datetime:
    _require(isinstance(value, str), "artifact_timestamp_missing")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    _require(result.tzinfo is not None, "artifact_timestamp_timezone_missing")
    return result


def _select_artifact(artifacts: Any, name: str) -> Mapping[str, Any]:
    _require(isinstance(artifacts, list), "artifact_list_invalid")
    matches = [item for item in artifacts if _object(item).get("name") == name]
    _require(len(matches) == 1, "exact_single_artifact_required")
    artifact = matches[0]
    _require(_positive_id(artifact.get("id")), "artifact_id_invalid")
    _require(artifact.get("expired") is False, "artifact_expired_or_unknown")
    size = artifact.get("size_in_bytes")
    _require(type(size) is int and 0 < size <= MAX_ARCHIVE_BYTES, "artifact_size_invalid")
    return artifact


def _validate_repo_slug(expected_repo: str) -> None:
    _require(isinstance(expected_repo, str) and re.fullmatch(
        r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", expected_repo
    ) is not None and expected_repo.split("/")[1] not in {".", ".."}, "repo_invalid")


def _validate_identity(
    *,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    expected_base_sha: str,
) -> None:
    _validate_repo_slug(expected_repo)
    _require(_positive_id(expected_pr), "pr_invalid")
    for value in (expected_head_sha, expected_base_sha):
        _require(
            isinstance(value, str)
            and re.fullmatch(r"[0-9a-f]{40}", value) is not None,
            "sha_invalid",
        )


def _archive_member_bytes(
    archive_bytes: bytes,
    *,
    member_name: str,
    max_member_bytes: int,
    reason_prefix: str,
) -> bytes:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        members = archive.infolist()
        for member in members:
            filename = member.filename.replace("\\", "/")
            parts = filename.rstrip("/").split("/")
            _require(
                filename
                and not filename.startswith("/")
                and ".." not in parts
                and member.orig_filename == member.filename,
                f"{reason_prefix}_archive_member_unsafe",
            )
        matching = [
            member for member in members
            if member.filename.replace("\\", "/").rstrip("/").split("/")[-1].casefold()
            == member_name.casefold()
        ]
        _require(
            len(matching) == 1
            and matching[0].filename == member_name
            and matching[0].orig_filename == member_name,
            f"exact_single_{reason_prefix}_member_required",
        )
        member = matching[0]
        _require(
            not member.is_dir()
            and not stat.S_ISLNK(member.external_attr >> 16)
            and 0 < member.file_size <= max_member_bytes,
            f"{reason_prefix}_member_invalid",
        )
        for other in members:
            if other is not member:
                _require(
                    not stat.S_ISLNK(other.external_attr >> 16),
                    f"{reason_prefix}_archive_member_unsafe",
                )
        with archive.open(member) as stream:
            return stream.read(max_member_bytes + 1)


def _validate_artifact_digest(
    artifact: Mapping[str, Any],
    archive_bytes: bytes,
) -> str | None:
    archive_digest = "sha256:" + sha256(archive_bytes).hexdigest()
    digest = artifact.get("digest")
    if digest is not None:
        _require(
            isinstance(digest, str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None,
            "artifact_digest_invalid",
        )
        _require(digest == archive_digest, "artifact_digest_mismatch")
    return digest


def _expected_steward_artifact_name(*, expected_pr: int, expected_head_sha: str) -> str:
    return f"pr-steward-pr-{expected_pr}-head-{expected_head_sha}-readiness"


def _expected_audit_artifact_name(*, expected_pr: int, expected_head_sha: str) -> str:
    return f"embedded-audit-pr-{expected_pr}-head-{expected_head_sha}-proof"


def _resolve_steward_run_id_from_readiness_status(
    client: GitHubClient,
    *,
    expected_head_sha: str,
) -> int:
    status_payload = _object(client.fetch_steward_readiness_status(expected_head_sha))
    _require(
        status_payload.get("sha") == expected_head_sha,
        "steward_status_head_mismatch",
    )
    statuses = status_payload.get("statuses")
    _require(isinstance(statuses, list), "steward_status_list_invalid")
    matches: list[tuple[datetime, Mapping[str, Any]]] = []
    for item in statuses:
        status = _object(item)
        if (
            status.get("context") != PR_STEWARD_READINESS_CONTEXT
            and status.get("name") != PR_STEWARD_READINESS_CONTEXT
        ):
            continue
        timestamp_value = status.get("updated_at") or status.get("created_at")
        _require(isinstance(timestamp_value, str), "steward_status_timestamp_missing")
        try:
            timestamp = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise WorkflowArtifactError("steward_status_timestamp_invalid") from exc
        _require(timestamp.tzinfo is not None, "steward_status_timestamp_timezone_missing")
        matches.append((timestamp, status))
    _require(matches, "steward_status_context_missing")
    latest_timestamp = max(timestamp for timestamp, _ in matches)
    latest_matches = [
        status for timestamp, status in matches if timestamp == latest_timestamp
    ]
    _require(len(latest_matches) == 1, "steward_status_latest_ambiguous")
    status = latest_matches[0]
    outcome = str(status.get("state") or status.get("conclusion") or "").upper()
    _require(outcome == "SUCCESS", "steward_status_not_successful")
    target_url = str(
        status.get("target_url")
        or status.get("targetUrl")
        or status.get("details_url")
        or status.get("detailsUrl")
        or ""
    ).strip()
    match = GITHUB_ACTIONS_DETAILS_URL_RE.match(target_url)
    _require(match is not None, "steward_status_target_url_invalid")
    run_id = int(match.group("run_id"))
    _require(_positive_id(run_id), "steward_status_run_id_invalid")
    return run_id


def verify_pr_steward_readiness_artifact(
    local_readiness_bytes: bytes,
    *,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    expected_base_sha: str,
    github_client: GitHubClient | None = None,
) -> dict[str, Any]:
    """Authenticate local MERGE_READINESS.json against the PR Steward artifact."""

    _validate_identity(
        expected_repo=expected_repo,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
        expected_base_sha=expected_base_sha,
    )
    _require(
        isinstance(local_readiness_bytes, bytes)
        and 0 < len(local_readiness_bytes) <= MAX_READINESS_BYTES,
        "local_readiness_size_invalid",
    )
    readiness = _object(json.loads(local_readiness_bytes))
    pr = _object(readiness.get("pr"))
    _object(readiness.get("proof"))
    _require(
        type(pr.get("number")) is int and pr["number"] == expected_pr
        and pr.get("head_sha") == expected_head_sha,
        "readiness_identity_mismatch",
    )

    client = github_client or GitHubClient(
        repo=expected_repo,
        repo_root=Path.cwd(),
        policy={},
    )
    _require(client.repo == expected_repo, "client_repo_mismatch")
    workflow = _object(client.fetch_steward_workflow())
    _require(
        workflow.get("path") == PR_STEWARD_WORKFLOW_PATH
        and workflow.get("name") == "PR Steward"
        and _positive_id(workflow.get("id")),
        "steward_workflow_identity_mismatch",
    )
    name = _expected_steward_artifact_name(
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
    )
    run_id = _resolve_steward_run_id_from_readiness_status(
        client,
        expected_head_sha=expected_head_sha,
    )
    artifact = _select_artifact(client.fetch_steward_artifacts(name, run_id), name)
    artifact_run = _object(artifact.get("workflow_run"))
    _require(artifact_run.get("id") == run_id, "steward_artifact_run_mismatch")
    run = _object(client.fetch_steward_run(run_id))
    repository = _object(run.get("repository"))
    _require(
        repository.get("full_name") == expected_repo,
        "steward_run_repository_mismatch",
    )
    _require(
        _positive_id(run.get("id")) and run["id"] == run_id
        and _positive_id(run.get("workflow_id")) and run["workflow_id"] == workflow["id"]
        and run.get("path") == PR_STEWARD_WORKFLOW_PATH
        and run.get("name") == "PR Steward",
        "steward_run_workflow_mismatch",
    )
    _require(run.get("status") == "completed" and run.get("conclusion") == "success",
             "steward_run_not_successful")
    _require(_positive_id(run.get("run_attempt")), "steward_run_attempt_invalid")
    _require(run.get("event") in {"workflow_run", "workflow_dispatch"},
             "steward_run_event_untrusted")
    _require(isinstance(run.get("head_sha"), str)
             and re.fullmatch(r"[0-9a-f]{40}", run["head_sha"]) is not None,
             "steward_run_head_invalid")
    _require(
        artifact_run.get("head_sha") == run["head_sha"],
        "steward_artifact_run_head_mismatch",
    )
    _require(
        _timestamp(artifact.get("created_at"))
        >= _timestamp(run.get("run_started_at")),
        "steward_artifact_from_prior_attempt",
    )

    archive_bytes = client.download_steward_artifact(artifact["id"])
    _require(
        isinstance(archive_bytes, bytes)
        and 0 < len(archive_bytes) <= MAX_ARCHIVE_BYTES,
        "download_size_invalid",
    )
    digest = _validate_artifact_digest(artifact, archive_bytes)
    archive_digest = "sha256:" + sha256(archive_bytes).hexdigest()
    downloaded_readiness_bytes = _archive_member_bytes(
        archive_bytes,
        member_name=READINESS_MEMBER,
        max_member_bytes=MAX_READINESS_BYTES,
        reason_prefix="readiness",
    )
    source_receipt_bytes = _archive_member_bytes(
        archive_bytes,
        member_name=SOURCE_RECEIPT_MEMBER,
        max_member_bytes=MAX_SOURCE_RECEIPT_BYTES,
        reason_prefix="source_receipt",
    )
    _require(
        downloaded_readiness_bytes == local_readiness_bytes,
        "local_readiness_bytes_mismatch",
    )

    receipt = _object(json.loads(source_receipt_bytes))
    audit_run_id = receipt.get("audit_run_id")
    _require(
        receipt.get("steward_run_id") == run_id,
        "source_receipt_steward_run_mismatch",
    )
    _require(
        receipt.get("repo") == expected_repo
        and type(receipt.get("pr")) is int and receipt["pr"] == expected_pr
        and receipt.get("head_sha") == expected_head_sha
        and receipt.get("base_sha") == expected_base_sha
        and _positive_id(audit_run_id)
        and receipt.get("steward_workflow") == PR_STEWARD_WORKFLOW_PATH
        and receipt.get("audit_workflow") == WORKFLOW_PATH
        and receipt.get("readiness_artifact_name") == name
        and receipt.get("audit_artifact_name") == _expected_audit_artifact_name(
            expected_pr=expected_pr,
            expected_head_sha=expected_head_sha,
        ),
        "source_receipt_identity_mismatch",
    )

    refreshed = _select_artifact(client.fetch_steward_artifacts(name, run_id), name)
    _require(refreshed == artifact, "steward_artifact_changed_during_verification")
    current_run = _object(client.fetch_steward_run(run_id))
    _require(current_run == run, "steward_run_changed_during_verification")
    live_pr = _object(client.fetch_steward_pr(expected_pr))
    base = _object(live_pr.get("base"))
    _require(type(live_pr.get("number")) is int and live_pr["number"] == expected_pr
             and live_pr.get("state") == "open"
             and _object(live_pr.get("head")).get("sha") == expected_head_sha
             and base.get("sha") == expected_base_sha
             and _object(base.get("repo")).get("full_name") == expected_repo,
             "live_pr_identity_mismatch")
    if run["event"] == "workflow_dispatch":
        default_branch = repository.get("default_branch")
        _require(isinstance(default_branch, str) and bool(default_branch)
                 and run.get("head_branch") == default_branch
                 and base.get("ref") == default_branch, "dispatch_ref_untrusted")

    return {
        "repository": expected_repo,
        "pr_number": expected_pr,
        "head_sha": expected_head_sha,
        "base_sha": expected_base_sha,
        "workflow_id": workflow["id"],
        "workflow_path": PR_STEWARD_WORKFLOW_PATH,
        "workflow_run_id": run_id,
        "run_attempt": run["run_attempt"],
        "run_status": run["status"],
        "run_conclusion": run["conclusion"],
        "artifact_id": artifact["id"],
        "artifact_name": name,
        "artifact_digest": digest,
        "downloaded_archive_digest": archive_digest,
        "readiness_member": READINESS_MEMBER,
        "source_receipt_member": SOURCE_RECEIPT_MEMBER,
        "downloaded_readiness_sha256": sha256(downloaded_readiness_bytes).hexdigest(),
        "local_readiness_sha256": sha256(local_readiness_bytes).hexdigest(),
        "source_receipt_sha256": sha256(source_receipt_bytes).hexdigest(),
        "source_receipt": dict(receipt),
        "audit_run_id": audit_run_id,
    }


def verify_workflow_artifact(
    local_proof_bytes: bytes,
    *,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    expected_base_sha: str,
    github_client: GitHubClient | None = None,
    audit_run_id: int | None = None,
) -> dict[str, Any]:
    """Return authenticated identity or raise; never accept an offline receipt.

    An optional run ID is a locator, not authority. Without one, discovery must
    yield one exact artifact name; ambiguous runs fail closed.
    """
    _validate_identity(
        expected_repo=expected_repo,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
        expected_base_sha=expected_base_sha,
    )
    _require(audit_run_id is None or _positive_id(audit_run_id), "run_id_invalid")
    _require(isinstance(local_proof_bytes, bytes) and 0 < len(local_proof_bytes) <= MAX_PROOF_BYTES,
             "local_proof_size_invalid")
    proof = _object(json.loads(local_proof_bytes))
    from scripts.audit.run_embedded_audit import independent_audit_errors

    _require(not independent_audit_errors(
        proof, expected_repo=expected_repo, expected_pr=expected_pr,
        expected_head_sha=expected_head_sha, expected_base_sha=expected_base_sha,
    ), "proof_semantics_invalid")
    contract = _object(_object(proof.get("provenance")).get("change_contract"))
    _require(proof.get("repo") == expected_repo
             and type(proof.get("pr_number")) is int and proof["pr_number"] == expected_pr
             and proof.get("head_sha") == expected_head_sha
             and contract.get("head_sha") == expected_head_sha
             and contract.get("base_sha") == expected_base_sha, "proof_identity_mismatch")

    client = github_client or GitHubClient(
        repo=expected_repo,
        repo_root=Path.cwd(),
        policy={},
    )
    _require(client.repo == expected_repo, "client_repo_mismatch")
    workflow = _object(client.fetch_audit_workflow())
    _require(workflow.get("path") == WORKFLOW_PATH and workflow.get("name") == "embedded-audit"
             and _positive_id(workflow.get("id")), "workflow_identity_mismatch")
    name = _expected_audit_artifact_name(
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
    )
    artifact = _select_artifact(client.fetch_audit_artifacts(name, audit_run_id), name)
    artifact_run = _object(artifact.get("workflow_run"))
    run_id = artifact_run.get("id")
    _require(_positive_id(run_id) and (audit_run_id is None or run_id == audit_run_id),
             "artifact_run_mismatch")
    run = _object(client.fetch_audit_run(run_id))
    repository = _object(run.get("repository"))
    _require(repository.get("full_name") == expected_repo, "run_repository_mismatch")
    _require(_positive_id(run.get("id")) and run["id"] == run_id
             and _positive_id(run.get("workflow_id")) and run["workflow_id"] == workflow["id"]
             and run.get("path") == WORKFLOW_PATH and run.get("name") == "embedded-audit",
             "run_workflow_mismatch")
    _require(run.get("status") == "completed" and run.get("conclusion") == "success",
             "run_not_successful")
    _require(_positive_id(run.get("run_attempt")), "run_attempt_invalid")
    _require(run.get("event") in {"pull_request_target", "workflow_dispatch"},
             "run_event_untrusted")
    _require(isinstance(run.get("head_sha"), str)
             and re.fullmatch(r"[0-9a-f]{40}", run["head_sha"]) is not None,
             "run_head_invalid")
    _require(artifact_run.get("head_sha") == run["head_sha"], "artifact_run_head_mismatch")
    _require(_timestamp(artifact.get("created_at")) >= _timestamp(run.get("run_started_at")),
             "artifact_from_prior_attempt")

    archive_bytes = client.download_audit_artifact(artifact["id"])
    _require(isinstance(archive_bytes, bytes) and 0 < len(archive_bytes) <= MAX_ARCHIVE_BYTES,
             "download_size_invalid")
    digest = _validate_artifact_digest(artifact, archive_bytes)
    archive_digest = "sha256:" + sha256(archive_bytes).hexdigest()
    downloaded_proof_bytes = _archive_member_bytes(
        archive_bytes,
        member_name=PROOF_MEMBER,
        max_member_bytes=MAX_PROOF_BYTES,
        reason_prefix="proof",
    )
    _require(downloaded_proof_bytes == local_proof_bytes, "local_proof_bytes_mismatch")

    # Recheck uncached metadata after download, including reruns and PR movement.
    refreshed = _select_artifact(client.fetch_audit_artifacts(name, run_id), name)
    _require(refreshed == artifact, "artifact_changed_during_verification")
    current_run = _object(client.fetch_audit_run(run_id))
    _require(current_run == run, "run_changed_during_verification")
    pr = _object(client.fetch_audit_pr(expected_pr))
    base = _object(pr.get("base"))
    _require(type(pr.get("number")) is int and pr["number"] == expected_pr
             and pr.get("state") == "open"
             and _object(pr.get("head")).get("sha") == expected_head_sha
             and base.get("sha") == expected_base_sha
             and _object(base.get("repo")).get("full_name") == expected_repo,
             "live_pr_identity_mismatch")
    if run["event"] == "workflow_dispatch":
        default_branch = repository.get("default_branch")
        _require(isinstance(default_branch, str) and bool(default_branch)
                 and run.get("head_branch") == default_branch
                 and base.get("ref") == default_branch, "dispatch_ref_untrusted")

    return {
        "repository": expected_repo, "pr_number": expected_pr,
        "head_sha": expected_head_sha, "base_sha": expected_base_sha,
        "workflow_id": workflow["id"], "workflow_path": WORKFLOW_PATH,
        "workflow_run_id": run_id, "run_attempt": run["run_attempt"],
        "run_status": run["status"], "run_conclusion": run["conclusion"],
        "artifact_id": artifact["id"], "artifact_name": name,
        "artifact_digest": digest, "downloaded_archive_digest": archive_digest,
        "proof_member": PROOF_MEMBER,
        "downloaded_proof_sha256": sha256(downloaded_proof_bytes).hexdigest(),
        "local_proof_sha256": sha256(local_proof_bytes).hexdigest(),
    }
