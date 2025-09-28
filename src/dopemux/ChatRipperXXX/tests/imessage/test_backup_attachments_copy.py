"""Tests for copying attachments from a MobileSync iPhone backup.

Validates that copy_attachment_files can resolve backup-stored attachments
via Manifest.db (HomeDomain/Library/SMS/Attachments/.. -> fileID -> xx/fileID).
"""

import sqlite3
from pathlib import Path

from chatx.imessage.attachments import compute_file_hash, copy_attachment_files
from chatx.schemas.message import Attachment


def _make_manifest_db(path: Path, mappings: list[tuple[str, str, str]]) -> None:
    """Create a minimal Manifest.db with a Files table and provided mappings.

    mappings: list of (domain, relativePath, fileID)
    """
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS Files (domain TEXT, relativePath TEXT, fileID TEXT)"
        )
        conn.executemany(
            "INSERT INTO Files(domain, relativePath, fileID) VALUES(?,?,?)",
            mappings,
        )
        conn.commit()
    finally:
        conn.close()


def test_copy_from_backup_manifest(tmp_path: Path) -> None:
    # Arrange: create fake backup with Manifest.db and hashed file
    backup = tmp_path / "Backup"
    backup.mkdir()
    manifest_db = backup / "Manifest.db"

    rel_path = "Library/SMS/Attachments/ab/xyz/file.jpg"
    file_id = "abdeadbeefcafebabe1234567890abcdef"

    _make_manifest_db(manifest_db, [("HomeDomain", rel_path, file_id)])

    # Create the hashed physical file under backup
    shard = file_id[:2]
    physical_dir = backup / shard
    physical_dir.mkdir(exist_ok=True)
    physical_file = physical_dir / file_id
    content = b"hello-attachment"
    physical_file.write_bytes(content)

    # Attachment metadata as it appears in sms.db (relative path)
    att = Attachment(
        type="image",
        filename=rel_path,  # typical sms.db relative path
        abs_path=None,
        mime_type="image/jpeg",
        uti="public.jpeg",
        transfer_name="file.jpg",
    )

    out_dir = tmp_path / "out"
    updated, _ = copy_attachment_files([att], out_dir, backup_dir=backup)

    assert len(updated) == 1
    new_att = updated[0]
    assert new_att.abs_path is not None

    copied_path = Path(new_att.abs_path)
    assert copied_path.exists()
    # Ensure hashing scheme used in destination path
    assert copied_path.name.endswith("_file.jpg")
    # Hash prefix matches content hash
    h = compute_file_hash(physical_file)
    assert copied_path.name.split("_", 1)[0] == h
    assert new_att.source_meta["hash"]["sha256"] == h

