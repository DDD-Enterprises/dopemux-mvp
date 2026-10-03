"""Tests for scripts/audit/sign_local_audit_proof.sh.

Covers:
- Fail-closed behavior on missing PROOF.json or missing signing key.
- Pre-removal of stale .sig file.
- Rejection when packet bundle has uncommitted changes.
- Rejection when signing key is not listed in config/audit/embedded-audit-allowed-signers.
- Successful signing and post-sign verification against allowed-signers.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SIGN_SCRIPT = ROOT / "scripts" / "audit" / "sign_local_audit_proof.sh"
SCHEMA_SRC = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"

PACKET_ID = "TP-DMX-SIGN-TEST-001"
PR_NUMBER = 7777
REPO = "DDD-Enterprises/dopemux-mvp"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _setup_repo(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Sets up a temp git repo matching the expectations of sign_local_audit_proof.sh."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "--initial-branch=main")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "user.name", "Tester")

    # Initial commit to have a valid commit SHA
    (repo / "dummy.txt").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "dummy.txt")
    _git(repo, "commit", "-m", "initial commit")
    head_sha = _git(repo, "rev-parse", "HEAD")

    # Copy schema into repo
    schema_dest = repo / "schemas" / "proof" / "embedded_audit.schema.json"
    schema_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCHEMA_SRC, schema_dest)

    # Generate test ed25519 signing key
    key_path = tmp_path / "signing_key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
        check=True,
        capture_output=True,
    )
    pub_key_content = (tmp_path / "signing_key.pub").read_text(encoding="utf-8").strip()

    # Allowed signers
    allowed_signers = repo / "config" / "audit" / "embedded-audit-allowed-signers"
    allowed_signers.parent.mkdir(parents=True, exist_ok=True)
    allowed_signers.write_text(f"signer@example.com {pub_key_content}\n", encoding="utf-8")

    # Packet bundle
    packet_dir = repo / "proof" / PACKET_ID
    packet_dir.mkdir(parents=True, exist_ok=True)
    report_file = packet_dir / "AUDITOR_REPORT.md"
    report_file.write_text("# Auditor Report\nPASS\n", encoding="utf-8")
    review_bundle = packet_dir / "review_bundle"
    review_bundle.mkdir(parents=True, exist_ok=True)
    (review_bundle / "notes.txt").write_text("audit notes\n", encoding="utf-8")

    embedded_obj = {
        "required": True,
        "status": "PASS",
        "auditor_tool": "claude-code-cli",
        "auditor_model": "sonnet",
        "invocation": "claude",
        "exit_code": 0,
        "report_path": f"proof/{PACKET_ID}/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": None,
    }
    packet_proof = {
        "packet_id": PACKET_ID,
        "repo": REPO,
        "head_sha": head_sha,
        "embedded_audit": embedded_obj,
    }
    (packet_dir / "PROOF.json").write_text(json.dumps(packet_proof, indent=2), encoding="utf-8")

    # Commit support files first
    _git(repo, "add", "schemas/", "config/")
    _git(repo, "commit", "-m", "commit support files")
    audited_sha = _git(repo, "rev-parse", "HEAD")

    # Packet bundle audited at audited_sha
    packet_proof = {
        "packet_id": PACKET_ID,
        "repo": REPO,
        "head_sha": audited_sha,
        "embedded_audit": embedded_obj,
    }
    (packet_dir / "PROOF.json").write_text(json.dumps(packet_proof, indent=2), encoding="utf-8")

    # Commit the packet bundle as required by sign_local_audit_proof.sh
    _git(repo, "add", f"proof/{PACKET_ID}/")
    _git(repo, "commit", "-m", "commit canonical packet bundle")

    # PR proof (uncommitted in working tree, as expected by the script)
    pr_proof_dir = repo / f"proof/pr_merge/embedded-audit/pr-{PR_NUMBER}"
    pr_proof_dir.mkdir(parents=True, exist_ok=True)
    pr_proof = {
        "repo": REPO,
        "pr_number": PR_NUMBER,
        "head_sha": audited_sha,
        "embedded_audit": embedded_obj,
    }
    (pr_proof_dir / "PROOF.json").write_text(json.dumps(pr_proof, indent=2), encoding="utf-8")

    return repo, key_path, pr_proof_dir / "PROOF.json", allowed_signers


def test_sign_missing_proof_fails(tmp_path: Path) -> None:
    repo, key_path, _, _ = _setup_repo(tmp_path)
    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), "99999", str(key_path)],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr


def test_sign_missing_key_fails(tmp_path: Path) -> None:
    repo, _, _, _ = _setup_repo(tmp_path)
    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(PR_NUMBER), str(tmp_path / "nonexistent_key")],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "signing key" in result.stderr


def test_sign_uncommitted_packet_bundle_fails(tmp_path: Path) -> None:
    repo, key_path, _, _ = _setup_repo(tmp_path)
    # Dirty the packet bundle directory
    (repo / "proof" / PACKET_ID / "extra.txt").write_text("uncommitted dirty file\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(PR_NUMBER), str(key_path)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin", "PYTHONPATH": str(ROOT)},
    )
    assert result.returncode != 0
    assert "has uncommitted changes" in result.stderr


def test_sign_removes_stale_signature_and_succeeds(tmp_path: Path) -> None:
    """Verifies VSH-001: stale signature is removed and replaced by clean verified signature."""
    repo, key_path, pr_proof_file, _ = _setup_repo(tmp_path)
    stale_sig = pr_proof_file.with_name(f"{pr_proof_file.name}.sig")
    stale_sig.write_text("corrupted_stale_signature_bytes\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(PR_NUMBER), str(key_path)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin", "PYTHONPATH": str(ROOT)},
    )
    assert result.returncode == 0, f"Expected 0 exit, got: {result.stdout}\n{result.stderr}"
    assert stale_sig.is_file()
    new_sig_content = stale_sig.read_text(encoding="utf-8")
    assert "corrupted_stale_signature_bytes" not in new_sig_content
    assert "-----BEGIN SSH SIGNATURE-----" in new_sig_content


def test_sign_unallowed_signer_fails(tmp_path: Path) -> None:
    repo, _, _, allowed_signers = _setup_repo(tmp_path)
    # Generate an unallowed key
    rogue_key = tmp_path / "rogue_key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(rogue_key)],
        check=True,
        capture_output=True,
    )

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(PR_NUMBER), str(rogue_key)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin", "PYTHONPATH": str(ROOT)},
    )
    assert result.returncode != 0
    assert "signature was not produced by an allowed signer" in result.stderr
