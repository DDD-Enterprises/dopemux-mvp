"""Tests for scripts/audit/build_evidence_bundle.py."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import jsonschema
import pytest

from scripts.audit.build_evidence_bundle import (
    FileRecord,
    BundleResult,
    build_bundle,
    _scan_for_secrets,
    _check_path_safe,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "audit" / "fixtures"
SCHEMA_PATH = ROOT / "schemas" / "audit" / "bundle_manifest.schema.json"

# Synthetic secret tokens (concatenated to avoid tripping repo scanners)
FAKE_GHP = "ghp_" + "F" * 36  # SYNTHETIC — never a real token
FAKE_AWS = "AKIA" + "A" * 16   # SYNTHETIC — never a real key
FAKE_ANT = "sk-ant-" + "X" * 24  # SYNTHETIC — never a real key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_root(tmp_path: Path) -> Path:
    """A temp dir acting as allowed_root with a clean file inside."""
    f = tmp_path / "clean.txt"
    f.write_text("hello world\n")
    return tmp_path


@pytest.fixture()
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _validate_manifest(manifest_path: Path, schema: dict) -> None:
    data = json.loads(manifest_path.read_text())
    jsonschema.validate(data, schema)


# ---------------------------------------------------------------------------
# _scan_for_secrets
# ---------------------------------------------------------------------------

class TestScanForSecrets:
    def test_clean_returns_none(self):
        assert _scan_for_secrets("no secrets here") is None

    def test_detects_ghp(self):
        assert _scan_for_secrets(f"token={FAKE_GHP}") == "github_token_ghp"

    def test_detects_aws(self):
        assert _scan_for_secrets(FAKE_AWS) == "aws_access_key"

    def test_detects_anthropic(self):
        assert _scan_for_secrets(FAKE_ANT) == "anthropic_key"

    def test_detects_generic_api_key(self):
        # Long enough value (>=16 chars) triggers generic pattern
        assert _scan_for_secrets("api_key=supersecretvalue1234") is not None

    def test_short_generic_value_not_flagged(self):
        # Values under 16 chars should not trigger generic pattern
        assert _scan_for_secrets("api_key=short") is None


# ---------------------------------------------------------------------------
# _check_path_safe
# ---------------------------------------------------------------------------

class TestCheckPathSafe:
    def test_safe_path_passes(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("ok")
        _check_path_safe(f, tmp_path)  # should not raise

    def test_path_escape_raises(self, tmp_path: Path):
        outside = tmp_path.parent / "escape.txt"
        outside.write_text("outside")
        with pytest.raises(ValueError, match="path escape"):
            _check_path_safe(outside, tmp_path)

    def test_symlink_raises(self, tmp_path: Path):
        real = tmp_path / "real.txt"
        real.write_text("real")
        link = tmp_path / "link.txt"
        link.symlink_to(real)
        with pytest.raises(ValueError, match="symlink"):
            _check_path_safe(link, tmp_path)


# ---------------------------------------------------------------------------
# build_bundle — normal include
# ---------------------------------------------------------------------------

class TestBuildBundleInclude:
    def test_clean_file_included(self, tmp_root: Path, tmp_path: Path, schema: dict):
        dest = tmp_path / "bundle"
        result = build_bundle(
            [tmp_root / "clean.txt"],
            dest,
            allowed_root=tmp_root,
            tp_id="TP-TEST-001",
            created_at="2026-01-01T00:00:00+00:00",
        )

        assert result.manifest_path.exists()
        assert result.request_path.exists()
        assert result.checksums_path.exists()
        assert result.redactions_path.exists()

        assert len(result.files) == 1
        assert result.files[0].kind == "included"
        assert result.files[0].path == "clean.txt"
        assert len(result.rejected) == 0

    def test_manifest_validates_schema(self, tmp_root: Path, tmp_path: Path, schema: dict):
        dest = tmp_path / "bundle"
        result = build_bundle(
            [tmp_root / "clean.txt"],
            dest,
            allowed_root=tmp_root,
            created_at="2026-01-01T00:00:00+00:00",
        )
        _validate_manifest(result.manifest_path, schema)

    def test_checksums_format(self, tmp_root: Path, tmp_path: Path):
        dest = tmp_path / "bundle"
        result = build_bundle(
            [tmp_root / "clean.txt"],
            dest,
            allowed_root=tmp_root,
            created_at="2026-01-01T00:00:00+00:00",
        )
        lines = result.checksums_path.read_text().strip().splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("sha256:")
        parts = lines[0].split("  ", 1)
        assert len(parts) == 2
        hex_part = parts[0][len("sha256:"):]
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_request_json_contains_content(self, tmp_root: Path, tmp_path: Path):
        dest = tmp_path / "bundle"
        result = build_bundle(
            [tmp_root / "clean.txt"],
            dest,
            allowed_root=tmp_root,
            created_at="2026-01-01T00:00:00+00:00",
        )
        request = json.loads(result.request_path.read_text())
        assert "clean.txt" in request
        assert "hello world" in request["clean.txt"]

    def test_deterministic_ordering(self, tmp_path: Path):
        """Multiple files must appear sorted by path regardless of input order."""
        root = tmp_path / "src"
        root.mkdir()
        (root / "z_last.txt").write_text("z")
        (root / "a_first.txt").write_text("a")
        (root / "m_middle.txt").write_text("m")

        dest = tmp_path / "bundle"
        result = build_bundle(
            # Deliberately unsorted
            [root / "z_last.txt", root / "a_first.txt", root / "m_middle.txt"],
            dest,
            allowed_root=root,
            created_at="2026-01-01T00:00:00+00:00",
        )

        paths = [r.path for r in result.files]
        assert paths == sorted(paths)

    def test_dest_already_exists_raises(self, tmp_root: Path, tmp_path: Path):
        dest = tmp_path / "bundle"
        dest.mkdir()
        with pytest.raises(FileExistsError):
            build_bundle(
                [tmp_root / "clean.txt"],
                dest,
                allowed_root=tmp_root,
            )


# ---------------------------------------------------------------------------
# Symlink rejection
# ---------------------------------------------------------------------------

class TestSymlinkRejection:
    def test_symlink_rejected(self, tmp_path: Path):
        root = tmp_path / "src"
        root.mkdir()
        real = root / "real.txt"
        real.write_text("real content")
        link = root / "link.txt"
        link.symlink_to(real)

        dest = tmp_path / "bundle"
        result = build_bundle(
            [link],
            dest,
            allowed_root=root,
            created_at="2026-01-01T00:00:00+00:00",
        )

        assert len(result.rejected) == 1
        assert result.rejected[0].exclusion_reason == "symlink"
        assert result.rejected[0].kind == "excluded"
        # real file not listed in rejected, just the symlink
        included_paths = [r.path for r in result.files]
        assert "link.txt" not in included_paths


# ---------------------------------------------------------------------------
# Path escape rejection
# ---------------------------------------------------------------------------

class TestPathEscapeRejection:
    def test_path_escape_rejected(self, tmp_path: Path):
        root = tmp_path / "src"
        root.mkdir()
        outside = tmp_path / "outside.txt"
        outside.write_text("should not appear")

        dest = tmp_path / "bundle"
        result = build_bundle(
            [outside],
            dest,
            allowed_root=root,
            created_at="2026-01-01T00:00:00+00:00",
        )

        assert len(result.rejected) == 1
        assert result.rejected[0].exclusion_reason == "path_escape"


# ---------------------------------------------------------------------------
# Secret rejection (fail-closed default)
# ---------------------------------------------------------------------------

class TestSecretRejection:
    def test_secret_file_rejected_by_default(self, tmp_path: Path):
        root = tmp_path / "src"
        root.mkdir()
        secret_file = root / "config.env"
        secret_file.write_text(f"token={FAKE_GHP}\n")

        dest = tmp_path / "bundle"
        result = build_bundle(
            [secret_file],
            dest,
            allowed_root=root,
            created_at="2026-01-01T00:00:00+00:00",
            allow_redact=False,
        )

        assert len(result.rejected) == 1
        assert "secret_pattern" in result.rejected[0].exclusion_reason
        # Not in request.json
        request = json.loads(result.request_path.read_text())
        assert "config.env" not in request

    def test_secret_file_redacted_with_allow_redact(self, tmp_path: Path):
        root = tmp_path / "src"
        root.mkdir()
        secret_file = root / "config.env"
        secret_file.write_text(f"token={FAKE_GHP}\n")

        dest = tmp_path / "bundle"
        result = build_bundle(
            [secret_file],
            dest,
            allowed_root=root,
            created_at="2026-01-01T00:00:00+00:00",
            allow_redact=True,
        )

        assert len(result.rejected) == 0
        assert len(result.files) == 1
        assert result.files[0].kind == "redacted"
        assert "secret_pattern" in result.files[0].redaction_reason
        # In request.json but as placeholder
        request = json.loads(result.request_path.read_text())
        assert "config.env" in request
        assert "<redacted:" in request["config.env"]


# ---------------------------------------------------------------------------
# Missing file rejected
# ---------------------------------------------------------------------------

class TestMissingFile:
    def test_missing_file_rejected(self, tmp_path: Path):
        root = tmp_path / "src"
        root.mkdir()
        missing = root / "does_not_exist.txt"

        dest = tmp_path / "bundle"
        result = build_bundle(
            [missing],
            dest,
            allowed_root=root,
            created_at="2026-01-01T00:00:00+00:00",
        )

        assert len(result.rejected) == 1
        assert result.rejected[0].exclusion_reason == "file_not_found"


# ---------------------------------------------------------------------------
# Manifest schema validation for edge cases
# ---------------------------------------------------------------------------

class TestManifestSchemaEdgeCases:
    def test_empty_sources_manifest_valid(self, tmp_path: Path, schema: dict):
        root = tmp_path / "src"
        root.mkdir()
        dest = tmp_path / "bundle"
        result = build_bundle(
            [],
            dest,
            allowed_root=root,
            tp_id="TP-TEST-EMPTY",
            created_at="2026-01-01T00:00:00+00:00",
        )
        _validate_manifest(result.manifest_path, schema)

    def test_mixed_sources_manifest_valid(self, tmp_path: Path, schema: dict):
        root = tmp_path / "src"
        root.mkdir()
        clean = root / "clean.txt"
        clean.write_text("safe")
        secret = root / "secret.env"
        secret.write_text(f"key={FAKE_AWS}\n")

        dest = tmp_path / "bundle"
        result = build_bundle(
            [clean, secret],
            dest,
            allowed_root=root,
            tp_id="TP-TEST-MIXED",
            created_at="2026-01-01T00:00:00+00:00",
        )
        _validate_manifest(result.manifest_path, schema)
        # clean included, secret rejected
        assert any(r.kind == "included" for r in result.files)
        assert len(result.rejected) == 1
