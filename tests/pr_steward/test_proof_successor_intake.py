"""Proof-only-successor acceptance through the collector -> classifier
intake path (TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A15).

Complements tests/dopemux_cli/test_pr_steward_audit_successor.py, which
covers the standalone ``pr-steward audit`` hard gate. This file covers the
second, independent consumer: ``pr-steward intake --strict``, which goes
through ``tools.pr_steward.collector._proof_freshness`` and
``tools.pr_steward.classifier._proof`` / ``build_artifacts``. Both consumers
must accept the same proof-only successor shape without weakening
proof-only path closure.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.pr_steward import collector
from tools.pr_steward.classifier import build_artifacts

REPO = "DDD-Enterprises/dopemux-mvp"
PR_NUMBER = 704


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


def _base_harvest(head_sha: str) -> dict:
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": {
            "number": PR_NUMBER,
            "url": f"https://github.com/{REPO}/pull/{PR_NUMBER}",
            "state": "OPEN",
            "isDraft": False,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": "APPROVED",
            "baseRefName": "main",
            "baseRefOid": "base000000000000000000000000000000000000",
            "headRefName": "codex/test",
            "headRefOid": head_sha,
            "author": {"login": "hu3mann"},
            "createdAt": "2026-05-26T01:00:00Z",
            "updatedAt": "2026-05-26T02:00:00Z",
        },
        "changed_files": [{"path": "src/app.py", "additions": 1}],
        "commits": [{"oid": head_sha, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [],
    }


@pytest.fixture()
def successor_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    _init_repo(repo)

    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    audited_sha = _commit(repo, "audited content")

    (repo / "proof").mkdir()
    (repo / "proof" / "PROOF.json").write_text(
        json.dumps(_proof_payload(head_sha=audited_sha)), encoding="utf-8"
    )
    live_sha = _commit(repo, "proof-only successor")

    return repo, audited_sha, live_sha


class TestCollectorProofFreshnessSuccessor:
    def test_verified_successor_reports_verified_successor_status(
        self, monkeypatch: pytest.MonkeyPatch, successor_repo: tuple[Path, str, str]
    ) -> None:
        repo, audited_sha, live_sha = successor_repo
        monkeypatch.chdir(repo)

        proof_payload = _proof_payload(head_sha=audited_sha)
        freshness = collector._proof_freshness(proof_payload, audited_sha, live_sha)

        assert freshness["status"] == "VERIFIED_SUCCESSOR"
        assert freshness["matches_pr_head"] is False

    def test_non_ancestor_head_stays_stale(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("a\n", encoding="utf-8")
        audited_sha = _commit(repo, "audited content")
        _git(repo, "checkout", "-q", "--orphan", "other")
        _git(repo, "rm", "-rf", "-q", ".")
        (repo / "x.txt").write_text("x\n", encoding="utf-8")
        live_sha = _commit(repo, "unrelated")
        monkeypatch.chdir(repo)

        proof_payload = _proof_payload(head_sha=audited_sha)
        freshness = collector._proof_freshness(proof_payload, audited_sha, live_sha)

        assert freshness["status"] == "STALE"


@pytest.fixture()
def custom_path_successor_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Same shape as ``successor_repo`` but with the proof committed at a
    non-default, nested path -- TP-DMX-...-A15-R1 F2 regression coverage."""
    repo = tmp_path / "repo"
    _init_repo(repo)

    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    audited_sha = _commit(repo, "audited content")

    custom_dir = repo / "proof" / "TP-TEST"
    custom_dir.mkdir(parents=True)
    (custom_dir / "PROOF.json").write_text(
        json.dumps(_proof_payload(head_sha=audited_sha)), encoding="utf-8"
    )
    live_sha = _commit(repo, "proof-only successor at custom path")

    return repo, audited_sha, live_sha


class TestCollectorCustomProofSourcePath:
    def test_custom_proof_source_path_reports_verified_successor(
        self,
        monkeypatch: pytest.MonkeyPatch,
        custom_path_successor_repo: tuple[Path, str, str],
    ) -> None:
        repo, audited_sha, live_sha = custom_path_successor_repo
        monkeypatch.chdir(repo)

        proof_payload = _proof_payload(head_sha=audited_sha)
        freshness = collector._proof_freshness(
            proof_payload,
            audited_sha,
            live_sha,
            proof_source_path="proof/TP-TEST/PROOF.json",
        )

        assert freshness["status"] == "VERIFIED_SUCCESSOR"

    def test_default_proof_source_path_rejects_custom_path_successor(
        self,
        monkeypatch: pytest.MonkeyPatch,
        custom_path_successor_repo: tuple[Path, str, str],
    ) -> None:
        """Without the correct proof_source_path, the allow-list is built
        from the wrong path and a genuinely valid custom-path successor is
        incorrectly rejected as STALE -- proving the threading is
        load-bearing, not cosmetic."""
        repo, audited_sha, live_sha = custom_path_successor_repo
        monkeypatch.chdir(repo)

        proof_payload = _proof_payload(head_sha=audited_sha)
        freshness = collector._proof_freshness(proof_payload, audited_sha, live_sha)

        assert freshness["status"] == "STALE"


class TestIntakeProofSuccessorReadiness:
    def test_verified_successor_no_proof_stale_blocker(
        self, monkeypatch: pytest.MonkeyPatch, successor_repo: tuple[Path, str, str]
    ) -> None:
        repo, audited_sha, live_sha = successor_repo
        monkeypatch.chdir(repo)

        harvest = _base_harvest(live_sha)
        harvest["embedded_audit"] = {
            "status": "PASS",
            "report_path": "proof/AUDITOR_REPORT.md",
        }
        harvest["proof"] = {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": audited_sha,
            "matches_pr_head": False,
            "proof_freshness": collector._proof_freshness(
                _proof_payload(head_sha=audited_sha), audited_sha, live_sha
            ),
        }

        artifacts = build_artifacts(
            harvest,
            repo=REPO,
            pr_number=PR_NUMBER,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]

        assert "PROOF_STALE" not in readiness["blockers"]
        assert "PROOF_STALE_OR_MISSING" not in readiness["blockers"]
        assert readiness["proof"]["proof_freshness"] == "VERIFIED_SUCCESSOR"

    def test_forged_successor_status_without_real_ancestry_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A harvest that CLAIMS VERIFIED_SUCCESSOR must not be trusted
        as-is -- classifier independently re-verifies from its own
        checkout and must fall back to STALE when that re-check fails."""
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "x.txt").write_text("x\n", encoding="utf-8")
        _commit(repo, "unrelated repo, no real ancestry")
        monkeypatch.chdir(repo)

        harvest = _base_harvest("f" * 40)
        harvest["embedded_audit"] = {"status": "PASS", "report_path": "proof/AUDITOR_REPORT.md"}
        harvest["proof"] = {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "a" * 40,
            "matches_pr_head": False,
            "proof_freshness": {
                "status": "VERIFIED_SUCCESSOR",
                "matches_pr_head": False,
                "reason": "forged claim",
                "proof_recorded_sha": "a" * 40,
                "pr_head_sha": "f" * 40,
                "self_reference_exception": None,
            },
        }

        artifacts = build_artifacts(
            harvest,
            repo=REPO,
            pr_number=PR_NUMBER,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]

        assert readiness["proof"]["proof_freshness"] == "STALE"


class TestClassifierCustomProofSourcePathRevalidation:
    """TP-DMX-...-A15-R1 F2: classifier._revalidate_proof_successor must use
    the harvest-carried proof_source_path, not silently assume the default,
    when independently re-verifying a VERIFIED_SUCCESSOR claim."""

    def test_custom_source_path_from_harvest_revalidates_successfully(
        self,
        monkeypatch: pytest.MonkeyPatch,
        custom_path_successor_repo: tuple[Path, str, str],
    ) -> None:
        repo, audited_sha, live_sha = custom_path_successor_repo
        monkeypatch.chdir(repo)

        harvest = _base_harvest(live_sha)
        harvest["embedded_audit"] = {
            "status": "PASS",
            "report_path": "proof/TP-TEST/AUDITOR_REPORT.md",
        }
        harvest["proof"] = {
            "proof_path": "proof/TP-TEST/PROOF.json",
            "proof_source_path": "proof/TP-TEST/PROOF.json",
            "proof_head_sha": audited_sha,
            "matches_pr_head": False,
            "proof_freshness": {
                "status": "VERIFIED_SUCCESSOR",
                "matches_pr_head": False,
                "reason": "claimed",
                "proof_recorded_sha": audited_sha,
                "pr_head_sha": live_sha,
                "self_reference_exception": None,
            },
        }

        artifacts = build_artifacts(
            harvest,
            repo=REPO,
            pr_number=PR_NUMBER,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]

        assert readiness["proof"]["proof_freshness"] == "VERIFIED_SUCCESSOR"

    def test_missing_source_path_in_harvest_falls_back_to_default_and_rejects(
        self,
        monkeypatch: pytest.MonkeyPatch,
        custom_path_successor_repo: tuple[Path, str, str],
    ) -> None:
        """If the harvest omits proof_source_path (e.g. an older collector
        that never learned the custom path), revalidation must fail closed
        -- not silently accept using the wrong default path."""
        repo, audited_sha, live_sha = custom_path_successor_repo
        monkeypatch.chdir(repo)

        harvest = _base_harvest(live_sha)
        harvest["embedded_audit"] = {
            "status": "PASS",
            "report_path": "proof/TP-TEST/AUDITOR_REPORT.md",
        }
        harvest["proof"] = {
            "proof_path": "proof/TP-TEST/PROOF.json",
            "proof_head_sha": audited_sha,
            "matches_pr_head": False,
            "proof_freshness": {
                "status": "VERIFIED_SUCCESSOR",
                "matches_pr_head": False,
                "reason": "claimed",
                "proof_recorded_sha": audited_sha,
                "pr_head_sha": live_sha,
                "self_reference_exception": None,
            },
        }

        artifacts = build_artifacts(
            harvest,
            repo=REPO,
            pr_number=PR_NUMBER,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]

        assert readiness["proof"]["proof_freshness"] == "STALE"
