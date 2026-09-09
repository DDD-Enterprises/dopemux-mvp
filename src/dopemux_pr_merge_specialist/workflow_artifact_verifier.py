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

from .github_api import GitHubClient

WORKFLOW_PATH = ".github/workflows/embedded-audit.yml"
PROOF_MEMBER = "PROOF.json"
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_PROOF_BYTES = 2 * 1024 * 1024


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
    _require(isinstance(expected_repo, str) and re.fullmatch(
        r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", expected_repo
    ) is not None and expected_repo.split("/")[1] not in {".", ".."}, "repo_invalid")
    _require(_positive_id(expected_pr), "pr_invalid")
    for value in (expected_head_sha, expected_base_sha):
        _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None,
                 "sha_invalid")
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

    client = github_client or GitHubClient(repo=expected_repo, repo_root=Path.cwd(), policy={})
    _require(client.repo == expected_repo, "client_repo_mismatch")
    workflow = _object(client.fetch_audit_workflow())
    _require(workflow.get("path") == WORKFLOW_PATH and workflow.get("name") == "embedded-audit"
             and _positive_id(workflow.get("id")), "workflow_identity_mismatch")
    name = f"embedded-audit-pr-{expected_pr}-head-{expected_head_sha}-proof"
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
    archive_digest = "sha256:" + sha256(archive_bytes).hexdigest()
    digest = artifact.get("digest")
    if digest is not None:
        _require(isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None,
                 "artifact_digest_invalid")
        _require(digest == archive_digest, "artifact_digest_mismatch")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        members = [member for member in archive.infolist()
                   if member.filename.replace("\\", "/").rstrip("/").split("/")[-1].casefold()
                   == PROOF_MEMBER.casefold()]
        _require(len(members) == 1 and members[0].filename == PROOF_MEMBER
                 and members[0].orig_filename == PROOF_MEMBER,
                 "exact_single_proof_member_required")
        member = members[0]
        _require(not member.is_dir() and not stat.S_ISLNK(member.external_attr >> 16)
                 and 0 < member.file_size <= MAX_PROOF_BYTES, "proof_member_invalid")
        with archive.open(member) as stream:
            downloaded_proof_bytes = stream.read(MAX_PROOF_BYTES + 1)
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
