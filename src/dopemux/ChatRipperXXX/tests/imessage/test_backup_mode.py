from __future__ import annotations

import sqlite3
from pathlib import Path
import plistlib

import pytest

from chatx.imessage.backup import (
    ensure_backup_accessible,
    stage_sms_db,
)
from chatx.imessage.extract import extract_messages


def _make_test_sms_db(db_path: Path, fixture_sql: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        with fixture_sql.open("r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def _init_manifest_db(manifest_db: Path) -> None:
    conn = sqlite3.connect(manifest_db)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS Files (fileID TEXT PRIMARY KEY, domain TEXT, relativePath TEXT, flags INTEGER)"
        )
        conn.commit()
    finally:
        conn.close()


def _insert_manifest_row(manifest_db: Path, file_id: str, domain: str, relative_path: str) -> None:
    conn = sqlite3.connect(manifest_db)
    try:
        conn.execute(
            "INSERT INTO Files (fileID, domain, relativePath, flags) VALUES (?, ?, ?, 1)",
            (file_id, domain, relative_path),
        )
        conn.commit()
    finally:
        conn.close()


def _place_hashed_file(backup_dir: Path, file_id: str, src_path: Path) -> Path:
    shard = file_id[:2]
    dest_dir = backup_dir / shard
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file_id
    dest.write_bytes(src_path.read_bytes())
    return dest


def test_backup_unencrypted_stages_and_extracts(tmp_path: Path) -> None:
    # Build a synthetic backup structure
    backup_dir = tmp_path / "Backup" / "SYNTH_UDID"
    backup_dir.mkdir(parents=True)
    manifest_db = backup_dir / "Manifest.db"
    _init_manifest_db(manifest_db)

    # Create a realistic sms.db from fixture SQL
    fixture_sql = Path(__file__).parent.parent / "fixtures" / "imessage_test_data.sql"
    src_db = tmp_path / "sms.db"
    _make_test_sms_db(src_db, fixture_sql)

    # Map HomeDomain/Library/SMS/sms.db → fileID and place at hashed path
    file_id = "ee" + "0" * 38  # any 40-char hex-like string
    _insert_manifest_row(manifest_db, file_id, "HomeDomain", "Library/SMS/sms.db")
    _place_hashed_file(backup_dir, file_id, src_db)

    # Should validate as accessible (unencrypted)
    ensure_backup_accessible(backup_dir)

    # Stage DB and extract a small sample
    with stage_sms_db(backup_dir) as staged_db:
        assert Path(staged_db).exists()
        # Extract a few messages via core extractor to prove plumbing works
        msgs = list(
            extract_messages(
                db_path=staged_db,
                contact="+15551234567",
                include_attachments=False,
                copy_binaries=False,
                transcribe_audio="off",
                out_dir=tmp_path / "out",
            )
        )
        assert len(msgs) > 0
        assert msgs[0].platform == "imessage"


def test_backup_encrypted_requires_password(tmp_path: Path) -> None:
    backup_dir = tmp_path / "Backup" / "ENCRYPTED_UDID"
    backup_dir.mkdir(parents=True)

    # Minimal Manifest.db presence
    _init_manifest_db(backup_dir / "Manifest.db")

    # Write a Status.plist indicating encryption
    with (backup_dir / "Status.plist").open("wb") as f:
        plistlib.dump({"IsEncrypted": True}, f)

    with pytest.raises(PermissionError):
        ensure_backup_accessible(backup_dir, backup_password=None)


def test_backup_encrypted_with_password(tmp_path: Path) -> None:
    """Providing a password for an encrypted backup should pass preflight."""
    backup_dir = tmp_path / "Backup" / "ENCRYPTED_OK"
    backup_dir.mkdir(parents=True)

    _init_manifest_db(backup_dir / "Manifest.db")
    with (backup_dir / "Status.plist").open("wb") as f:
        plistlib.dump({"IsEncrypted": True}, f)

    # Should not raise when password is supplied
    ensure_backup_accessible(backup_dir, backup_password="secret")

