"""iPhone backup mode helpers for iMessage extraction.

Resolves files from a MobileSync backup directory via Manifest.db and stages
`HomeDomain/Library/SMS/sms.db` (plus WAL/SHM if present) for read-only use.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory
from typing import Iterator, Optional
import plistlib
import re


@dataclass
class StagedBackupDB:
    tempdir: TemporaryDirectory
    db_path: Path

    # Support context manager to ensure cleanup
    def __enter__(self) -> Path:
        return self.db_path

    def __exit__(self, exc_type, exc, tb) -> None:
        # TemporaryDirectory cleans itself up when garbage collected; ensure close
        self.tempdir.cleanup()


def _manifest_db_path(backup_dir: Path) -> Path:
    path = backup_dir / "Manifest.db"
    if not path.exists():
        raise FileNotFoundError(
            f"Manifest.db not found in backup directory: {backup_dir}. "
            f"Hint: {canonical_mobilesync_hint()}"
        )
    return path


def backup_is_encrypted(backup_dir: Path) -> Optional[bool]:
    """Return True/False if determinable, else None.

    Checks common plists used by Finder/iTunes backups.
    """
    # Newer macOS places encryption flags in Status.plist
    status_plist = backup_dir / "Status.plist"
    for plist_path in (status_plist, backup_dir / "Manifest.plist", backup_dir / "Info.plist"):
        if plist_path.exists():
            try:
                with plist_path.open("rb") as f:
                    data = plistlib.load(f)
                for key in ("IsEncrypted", "Encrypted", "UsesEncryptedBackups"):
                    if key in data:
                        return bool(data[key])
            except Exception:
                # Ignore parse errors; fall through
                pass
    return None


def canonical_mobilesync_hint() -> str:
    """Return canonical macOS MobileSync backup dir hint string."""
    return "~/Library/Application Support/MobileSync/Backup/<UDID>"


def preflight_backup_structure(backup_dir: Path) -> dict:
    """Basic structure checks for a MobileSync backup directory.

    Returns a dict with presence flags; raises FileNotFoundError if critical
    artifacts are missing (Manifest.db).
    """
    result = {
        "manifest": False,
        "info_plist": False,
        "status_plist": False,
        "shards_present": False,
    }
    # Manifest (critical)
    _ = _manifest_db_path(backup_dir)
    result["manifest"] = True

    # Plists (optional but useful)
    if (backup_dir / "Info.plist").exists():
        result["info_plist"] = True
    if (backup_dir / "Status.plist").exists():
        result["status_plist"] = True

    # Shard dirs (00..ff)
    hex2 = re.compile(r"^[0-9a-fA-F]{2}$")
    for child in backup_dir.iterdir():
        if child.is_dir() and hex2.match(child.name):
            result["shards_present"] = True
            break

    if not result["shards_present"]:
        # Non-fatal: some backups may be flat, but warn via raised exception here for clarity
        # Callers may choose to catch and present as a warning.
        pass
    return result


def _query_manifest_fileid(backup_dir: Path, domain: str, relative_path: str) -> Optional[str]:
    """Query Manifest.db for the fileID corresponding to (domain, relative_path)."""
    mdb = _manifest_db_path(backup_dir)
    uri = f"file:{mdb}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    try:
        # iOS backups typically have a Files table with domain, relativePath, fileID
        # In some versions, table names/columns vary; try a couple of common shapes.
        queries = [
            ("SELECT fileID FROM Files WHERE domain=? AND relativePath=?", (domain, relative_path)),
            ("SELECT fileID FROM Files WHERE domain=? AND relativePath=?", (domain, relative_path.lstrip("/"))),
        ]
        for sql, params in queries:
            try:
                row = conn.execute(sql, params).fetchone()
            except sqlite3.Error:
                continue
            if row and row[0]:
                return str(row[0])
        return None
    finally:
        conn.close()


def _hashed_backup_path(backup_dir: Path, file_id: str) -> Path:
    """Given a fileID, return the on-disk hashed path (xx/fileID)."""
    shard = file_id[:2]
    return backup_dir / shard / file_id


def resolve_backup_file(backup_dir: Path, domain: str, relative_path: str) -> Path:
    """Resolve a file inside a MobileSync backup by domain+relative_path → real path."""
    file_id = _query_manifest_fileid(backup_dir, domain, relative_path)
    if not file_id:
        raise FileNotFoundError(
            f"Backup file not found in Manifest.db for {domain}:{relative_path}"
        )
    physical = _hashed_backup_path(backup_dir, file_id)
    if not physical.exists():
        raise FileNotFoundError(
            f"Physical file for fileID {file_id} not found at expected path: {physical}"
        )
    return physical


def stage_sms_db(backup_dir: Path) -> StagedBackupDB:
    """Copy sms.db (+wal/+shm if present) from backup into a temp staging dir.

    Returns a StagedBackupDB which can be used as a context manager.
    """
    tdir = TemporaryDirectory(prefix="chatx_imsg_backup_")
    tpath = Path(tdir.name)
    out_db = tpath / "sms.db"

    # Primary DB
    src_db = resolve_backup_file(
        backup_dir, "HomeDomain", "Library/SMS/sms.db"
    )
    copy2(src_db, out_db)

    # Optional WAL/SHM
    for suffix in ("-wal", "-shm"):
        try:
            src_aux = resolve_backup_file(
                backup_dir, "HomeDomain", f"Library/SMS/sms.db{suffix}"
            )
        except FileNotFoundError:
            continue
        copy2(src_aux, out_db.with_name(out_db.name + suffix))

    return StagedBackupDB(tempdir=tdir, db_path=out_db)


def ensure_backup_accessible(backup_dir: Path, backup_password: Optional[str] = None) -> None:
    """Validate backup accessibility and basic structure.

    - Ensure Manifest.db exists
    - If determinably encrypted and no password provided, raise a helpful error
    """
    preflight_backup_structure(backup_dir)  # will raise if missing manifest
    enc = backup_is_encrypted(backup_dir)
    if enc is True and not backup_password:
        raise PermissionError(
            "Encrypted backup detected. Provide --backup-password, or create a new unencrypted backup in Finder/iTunes."
        )
