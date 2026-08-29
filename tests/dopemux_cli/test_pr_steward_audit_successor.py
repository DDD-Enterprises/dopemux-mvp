"""Proof-only-successor acceptance for ``dopemux.cli pr-steward audit``.

Regression coverage for TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A15:
the packaged embedded-audit template + CLI historically required a
committed proof's ``head_sha`` to equal the live PR head exactly, which
rejects the legitimate pattern where an audited content commit ``A`` is
followed by later commits that add ONLY proof evidence on top (``H``).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from dopemux_pr_steward.cli import main as steward_main

REPO = "DDD-Enterprises/dopemux-mvp"
PR_NUMBER = 1287


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed: {result.stdout}\n{result.stderr}"
    )
    return result


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _proof_payload(*, head_sha: str) -> dict:
    return {
        "repo": REPO,
        "pr_number": PR_NUMBER,
        "head_sha": head_sha,
        "executed": True,
        "provenance": {
            "proof_author": "independent-embedded-audit",
            "workflow": "embedded-audit.yml",
        },
        "embedded_audit": {
            "status": "PASS",
            "report_path": "proof/AUDITOR_REPORT.md",
        },
    }


@pytest.fixture()
def successor_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Repo with audited content commit A, then a proof-only successor H."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    audited_sha = _commit(repo, "audited content")

    (repo / "proof").mkdir()
    proof_path = repo / "proof" / "PROOF.json"
    proof_path.write_text(
        json.dumps(_proof_payload(head_sha=audited_sha)), encoding="utf-8"
    )
    live_sha = _commit(repo, "proof-only successor")

    return repo, audited_sha, live_sha


def _run_audit(
    repo_root: Path,
    proof_file: Path,
    *,
    head: str,
    proof_source_path: str = "proof/PROOF.json",
) -> int:
    return steward_main(
        [
            "audit",
            "--proof",
            str(proof_file),
            "--repo",
            REPO,
            "--pr",
            str(PR_NUMBER),
            "--head",
            head,
            "--repo-root",
            str(repo_root),
            "--proof-source-path",
            proof_source_path,
        ]
    )


class TestProofOnlySuccessorAcceptance:
    def test_legacy_exact_head_still_passes(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "proof").mkdir()
        proof_path = repo / "proof" / "PROOF.json"
        # Legacy case: the proof's head_sha names the exact commit that
        # carries it (self-referential but not via a successor chain --
        # simulated here by writing content, committing, then amending the
        # same commit to also carry a proof naming its own final SHA is not
        # representable with plain git without a fixup; instead assert the
        # simpler exact-match contract directly: head_sha == live head.
        (repo / "src.txt").write_text("placeholder\n", encoding="utf-8")
        sha = _commit(repo, "content")
        proof_path.write_text(json.dumps(_proof_payload(head_sha=sha)), encoding="utf-8")

        rc = _run_audit(repo, proof_path, head=sha)

        assert rc == 0

    def test_verified_proof_only_successor_passes(
        self, successor_repo: tuple[Path, str, str]
    ) -> None:
        repo, audited_sha, live_sha = successor_repo
        proof_file = repo / "proof" / "PROOF.json"

        rc = _run_audit(repo, proof_file, head=live_sha)

        assert rc == 0

    def test_audited_head_not_ancestor_of_live_head_is_rejected(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("a\n", encoding="utf-8")
        audited_sha = _commit(repo, "audited content")

        # Divergent branch, not a descendant of audited_sha.
        _git(repo, "checkout", "-q", "--orphan", "other")
        _git(repo, "rm", "-rf", "-q", ".")
        (repo / "proof").mkdir()
        proof_file = repo / "proof" / "PROOF.json"
        proof_file.write_text(
            json.dumps(_proof_payload(head_sha=audited_sha)), encoding="utf-8"
        )
        live_sha = _commit(repo, "unrelated history")

        rc = _run_audit(repo, proof_file, head=live_sha)

        assert rc == 2

    def test_code_bearing_successor_delta_is_rejected(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
        audited_sha = _commit(repo, "audited content")

        (repo / "proof").mkdir()
        proof_file = repo / "proof" / "PROOF.json"
        proof_file.write_text(
            json.dumps(_proof_payload(head_sha=audited_sha)), encoding="utf-8"
        )
        # Successor smuggles a code change alongside the proof file.
        (repo / "src" / "app.py").write_text("print(2)\n", encoding="utf-8")
        live_sha = _commit(repo, "proof + smuggled code change")

        rc = _run_audit(repo, proof_file, head=live_sha)

        assert rc == 2

    def test_wrong_pr_number_is_rejected_even_with_valid_successor(
        self, successor_repo: tuple[Path, str, str]
    ) -> None:
        repo, audited_sha, live_sha = successor_repo
        proof_file = repo / "proof" / "PROOF.json"

        rc = steward_main(
            [
                "audit",
                "--proof",
                str(proof_file),
                "--repo",
                REPO,
                "--pr",
                "9999",
                "--head",
                live_sha,
                "--repo-root",
                str(repo),
                "--proof-source-path",
                "proof/PROOF.json",
            ]
        )

        assert rc == 2

    def test_missing_provenance_still_rejected(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("a\n", encoding="utf-8")
        audited_sha = _commit(repo, "audited content")

        (repo / "proof").mkdir()
        proof_file = repo / "proof" / "PROOF.json"
        payload = _proof_payload(head_sha=audited_sha)
        del payload["provenance"]
        proof_file.write_text(json.dumps(payload), encoding="utf-8")
        live_sha = _commit(repo, "proof-only successor")

        rc = _run_audit(repo, proof_file, head=live_sha)

        assert rc == 2

    def test_nonpassing_audit_status_still_rejected(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("a\n", encoding="utf-8")
        audited_sha = _commit(repo, "audited content")

        (repo / "proof").mkdir()
        proof_file = repo / "proof" / "PROOF.json"
        payload = _proof_payload(head_sha=audited_sha)
        payload["embedded_audit"]["status"] = "FAIL"
        proof_file.write_text(json.dumps(payload), encoding="utf-8")
        live_sha = _commit(repo, "proof-only successor")

        rc = _run_audit(repo, proof_file, head=live_sha)

        assert rc == 2
