from __future__ import annotations

import copy
import io
import json
import stat
import subprocess
import zipfile
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux_pr_merge_specialist.github_api import GitHubClient
from dopemux_pr_merge_specialist.runtime import CommandResult
from dopemux_pr_merge_specialist.workflow_artifact_verifier import (
    MAX_PROOF_BYTES,
    WORKFLOW_PATH,
    WorkflowArtifactError,
    verify_workflow_artifact,
)
from scripts.audit.run_embedded_audit import build_evidence_gate_proof

REPO = "DDD-Enterprises/dopemux-mvp"
HEAD = "a" * 40
BASE = "b" * 40


def proof_bytes() -> bytes:
    return json.dumps(build_evidence_gate_proof(
        packet_id="TP-ARTIFACT-AUTHENTICITY", repo=REPO, pr_number=1330,
        head_sha=HEAD, base_sha=BASE,
        change_contract={"status": "PASS", "model_audit_required": False, "max_lane": "L0"},
        local_attestation=None, generated_at="2026-09-07T12:00:00Z",
    )).encode()


def zip_bytes(members: list[tuple[str | zipfile.ZipInfo, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in members:
            archive.writestr(name, contents)
    return buffer.getvalue()


class ArtifactTransport:
    """Independent, immutable-at-fetch GitHub responses for consumer tests."""

    def __init__(self, remote_proof: bytes):
        proof = json.loads(remote_proof)
        self.repo = proof["repo"]
        self.remote_proof = remote_proof
        self.workflow = {"id": 17, "name": "embedded-audit", "path": WORKFLOW_PATH}
        self.run = {
            "id": 23, "workflow_id": 17, "name": "embedded-audit", "path": WORKFLOW_PATH,
            "repository": {"full_name": self.repo, "default_branch": "main"},
            "status": "completed", "conclusion": "success", "run_attempt": 1,
            "event": "pull_request_target", "head_sha": "c" * 40, "head_branch": "main",
            "run_started_at": "2026-09-07T11:59:00Z",
        }
        self.pr = {
            "number": proof["pr_number"], "state": "open",
            "head": {"sha": proof["head_sha"]},
            "base": {"sha": proof["provenance"]["change_contract"]["base_sha"],
                     "ref": "main", "repo": {"full_name": self.repo}},
        }
        self.artifact = {
            "id": 31, "expired": False,
            "name": f"embedded-audit-pr-{proof['pr_number']}-head-{proof['head_sha']}-proof",
            "workflow_run": {"id": 23, "head_sha": "c" * 40},
            "created_at": "2026-09-07T12:00:00Z",
        }
        self.set_archive(zip_bytes([("PROOF.json", remote_proof), ("report.txt", b"report")]))
        self.calls = []
        self.after_download = None

    def set_archive(self, archive: bytes):
        self.archive = archive
        self.artifact.update(size_in_bytes=len(archive), digest="sha256:" + sha256(archive).hexdigest())

    def fetch_audit_workflow(self):
        self.calls.append("workflow")
        return copy.deepcopy(self.workflow)

    def fetch_audit_artifacts(self, name, run_id=None):
        self.calls.append(("artifacts", name, run_id))
        return [copy.deepcopy(self.artifact)]

    def fetch_audit_run(self, run_id):
        self.calls.append(("run", run_id))
        return copy.deepcopy(self.run)

    def fetch_audit_pr(self, pr_id):
        self.calls.append(("pr", pr_id))
        return copy.deepcopy(self.pr)

    def download_audit_artifact(self, artifact_id):
        self.calls.append(("download", artifact_id))
        if self.after_download:
            self.after_download()
        return self.archive


def install_artifact_transport(monkeypatch, remote_proof: bytes) -> ArtifactTransport:
    transport = ArtifactTransport(remote_proof)
    for name in ("fetch_audit_workflow", "fetch_audit_run", "fetch_audit_artifacts",
                 "fetch_audit_pr", "download_audit_artifact"):
        method = getattr(transport, name)
        monkeypatch.setattr(GitHubClient, name, lambda self, *args, _method=method: _method(*args))
    return transport


def verify(transport, local=None, **overrides):
    return verify_workflow_artifact(
        proof_bytes() if local is None else local, github_client=transport,
        **{"expected_repo": REPO, "expected_pr": 1330,
           "expected_head_sha": HEAD, "expected_base_sha": BASE, **overrides},
    )


@pytest.mark.parametrize("event", ["pull_request_target", "workflow_dispatch"])
@pytest.mark.parametrize("pin", [None, 23])
def test_exact_authenticated_artifact_binds_bytes_and_full_tuple(event, pin):
    transport = ArtifactTransport(proof_bytes())
    transport.run["event"] = event
    result = verify(transport, audit_run_id=pin)
    assert result["local_proof_sha256"] == result["downloaded_proof_sha256"] == sha256(proof_bytes()).hexdigest()
    assert result["workflow_run_id"] == 23 and result["artifact_id"] == 31
    assert result["repository"] == REPO and result["pr_number"] == 1330
    assert result["head_sha"] == HEAD and result["base_sha"] == BASE
    assert result["workflow_path"] == WORKFLOW_PATH
    assert result["proof_member"] == "PROOF.json"
    assert result["run_status"] == "completed" and result["run_conclusion"] == "success"
    assert result["artifact_digest"] == "sha256:" + sha256(transport.archive).hexdigest()
    assert transport.calls.count(("run", 23)) == 2


@pytest.mark.parametrize("section,field,value", [
    ("workflow", "id", 99), ("workflow", "path", ".github/workflows/other-embedded-audit.yml"),
    ("run", "repository", {"full_name": "attacker/repo"}), ("run", "id", 99),
    ("run", "workflow_id", 99), ("run", "path", ".github/workflows/forged.yml"),
    ("run", "name", "other"), ("run", "event", "pull_request"),
    ("run", "event", "push"), ("run", "status", "in_progress"),
    ("run", "conclusion", "failure"), ("run", "conclusion", "skipped"),
    ("run", "run_attempt", None), ("run", "head_sha", "d" * 40),
    ("run", "run_started_at", "2026-09-07T12:01:00Z"),
    ("artifact", "workflow_run", {"id": 99, "head_sha": "c" * 40}),
    ("artifact", "name", "prefix-embedded-audit-pr-1330-head-" + HEAD + "-proof"),
    ("artifact", "id", True), ("artifact", "expired", True),
    ("artifact", "expired", None), ("artifact", "size_in_bytes", 0),
    ("artifact", "digest", "sha256:" + "0" * 64), ("artifact", "digest", ""),
    ("artifact", "created_at", "2026-09-07T12:00:00"),
    ("pr", "number", 1331), ("pr", "state", "closed"),
    ("pr", "head", {"sha": "d" * 40}),
    ("pr", "base", {"sha": "d" * 40, "repo": {"full_name": REPO}}),
    ("pr", "base", {"sha": BASE, "repo": {"full_name": "attacker/repo"}}),
])
def test_wrong_or_missing_authenticated_binding_denies(section, field, value):
    transport = ArtifactTransport(proof_bytes())
    getattr(transport, section)[field] = value
    with pytest.raises(WorkflowArtifactError):
        verify(transport)


@pytest.mark.parametrize("members", [
    [], [("nested/PROOF.json", b"same")], [("../PROOF.json", b"same")],
    [("PROOF.json", b"same"), ("nested/PROOF.json", b"same")],
    [("PROOF.json", b"same"), ("proof.json", b"same")],
    [("PROOF.json", b"same"), ("PROOF.json", b"same")],
])
def test_exact_single_proof_member_required(members):
    transport = ArtifactTransport(proof_bytes())
    transport.set_archive(zip_bytes(members))
    with pytest.raises(WorkflowArtifactError, match="exact_single_proof_member_required"):
        verify(transport)


def test_symlink_and_oversized_proof_members_deny():
    transport = ArtifactTransport(proof_bytes())
    link = zipfile.ZipInfo("PROOF.json")
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    for member, contents in [(link, proof_bytes()), ("PROOF.json", b"x" * (MAX_PROOF_BYTES + 1))]:
        transport.set_archive(zip_bytes([(member, contents)]))
        with pytest.raises(WorkflowArtifactError, match="proof_member_invalid"):
            verify(transport)


def test_same_json_different_bytes_denied():
    transport = ArtifactTransport(proof_bytes())
    different_bytes = json.dumps(json.loads(proof_bytes()), indent=2).encode()
    with pytest.raises(WorkflowArtifactError, match="local_proof_bytes_mismatch"):
        verify(transport, different_bytes)


def test_digest_absence_still_requires_authenticated_download_and_exact_bytes():
    transport = ArtifactTransport(proof_bytes())
    transport.artifact.pop("digest")
    assert verify(transport)["artifact_digest"] is None
    with pytest.raises(WorkflowArtifactError):
        verify(transport, proof_bytes() + b"\n")


@pytest.mark.parametrize("count", [0, 2])
def test_missing_or_ambiguous_artifacts_deny(count):
    transport = ArtifactTransport(proof_bytes())
    transport.fetch_audit_artifacts = lambda *args: [transport.artifact] * count
    with pytest.raises(WorkflowArtifactError, match="exact_single_artifact_required"):
        verify(transport)


@pytest.mark.parametrize("method", ["fetch_audit_workflow", "fetch_audit_run",
                                   "fetch_audit_artifacts", "fetch_audit_pr", "download_audit_artifact"])
def test_retrieval_failure_has_no_offline_fallback(method):
    transport = ArtifactTransport(proof_bytes())
    def fail(*args):
        raise RuntimeError("unavailable")
    setattr(transport, method, fail)
    with pytest.raises(RuntimeError, match="unavailable"):
        verify(transport)


@pytest.mark.parametrize("section,changes", [
    ("run", {"run_attempt": 2}), ("run", {"status": "queued"}),
    ("artifact", {"expired": True}), ("artifact", {"id": 32}),
    ("pr", {"head": {"sha": "d" * 40}}),
])
def test_download_race_denies(section, changes):
    transport = ArtifactTransport(proof_bytes())
    transport.after_download = lambda: getattr(transport, section).update(changes)
    with pytest.raises(WorkflowArtifactError):
        verify(transport)


def test_workflow_dispatch_from_untrusted_ref_denies():
    transport = ArtifactTransport(proof_bytes())
    transport.run.update(event="workflow_dispatch", head_branch="attacker")
    with pytest.raises(WorkflowArtifactError, match="dispatch_ref_untrusted"):
        verify(transport)


def test_pinned_run_is_only_a_locator():
    with pytest.raises(WorkflowArtifactError, match="artifact_run_mismatch"):
        verify(ArtifactTransport(proof_bytes()), audit_run_id=24)


def test_existing_github_client_uses_fixed_get_routes_and_preserves_zip_bytes(monkeypatch, tmp_path):
    client = GitHubClient(repo=REPO, repo_root=tmp_path, policy={})
    commands = []
    responses = iter(['{}', '{}', '{}', '[{"artifacts": [{"id": 1}]}, {"artifacts": [{"id": 2}]}]'])
    def run(command):
        commands.append(command)
        return CommandResult(command, 0, next(responses), "")
    monkeypatch.setattr(client, "_run", run)
    client.fetch_audit_workflow()
    client.fetch_audit_run(23)
    client.fetch_audit_pr(1330)
    assert client.fetch_audit_artifacts("exact-name", 23) == [{"id": 1}, {"id": 2}]
    binary = b"PK\xff\x00\r\n"
    def download(command, **kwargs):
        commands.append(command)
        assert kwargs["cwd"] == tmp_path and "text" not in kwargs
        return SimpleNamespace(returncode=0, stdout=binary)
    monkeypatch.setattr(subprocess, "run", download)
    assert client.download_audit_artifact(31) == binary
    assert all(command[:6] == ["gh", "api", "--hostname", "github.com", "--method", "GET"]
               for command in commands)
    assert commands[-1][-1] == f"repos/{REPO}/actions/artifacts/31/zip"
    assert commands[-2][-2:] == ["--paginate", "--slurp"]


def test_workflow_uses_same_verifier_and_trusted_run_locator():
    import ast
    import yaml
    workflow = yaml.safe_load((Path(__file__).resolve().parents[2] / ".github/workflows/pr-steward.yml").read_text())
    step = next(s for s in workflow["jobs"]["pr-steward"]["steps"]
                if s["name"] == "Select and download independent audit artifact")
    snippets = step["run"].split("python - <<'PY'\n")[1:]
    calls = [node for snippet in snippets for node in ast.walk(ast.parse(snippet.split("\nPY", 1)[0]))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "verify_workflow_artifact"]
    assert len(calls) == 1
    assert {kw.arg for kw in calls[0].keywords} == {
        "expected_pr", "expected_head_sha", "expected_repo", "expected_base_sha", "audit_run_id",
    }
    assert step["env"]["AUDIT_RUN_ID"] == "${{ steps.audit_run.outputs.id }}"
