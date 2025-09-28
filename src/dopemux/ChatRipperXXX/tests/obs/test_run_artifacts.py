from __future__ import annotations

import hashlib
from pathlib import Path

from chatx.obs.run_artifacts import write_manifest


def test_write_manifest_includes_db_hash(tmp_path: Path) -> None:
    out = tmp_path / "out"
    db = tmp_path / "chat.db"
    content = b"hello-db"
    db.write_bytes(content)

    path = write_manifest(out_dir=out, db_path=db)
    assert path.exists()
    data = path.read_text(encoding="utf-8")

    h = hashlib.sha256(content).hexdigest()
    assert "db_sha256" in data and h in data
    assert str(db) in data

