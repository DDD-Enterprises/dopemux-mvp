from __future__ import annotations

import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from chatx.cli.main import app

runner = CliRunner()


def _make_db_with_attachment(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
    conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
    conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
    conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, 'iMessage;-;+15551234567')")
    conn.execute(
        """
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, attributedBody BLOB,
            is_from_me INTEGER, handle_id INTEGER, service TEXT DEFAULT 'iMessage',
            date INTEGER, associated_message_guid TEXT, associated_message_type INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE attachment (
            ROWID INTEGER PRIMARY KEY, filename TEXT, uti TEXT, mime_type TEXT,
            transfer_name TEXT, total_bytes INTEGER, created_date INTEGER, start_date INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE message_attachment_join (
            message_id INTEGER, attachment_id INTEGER
        )
        """
    )
    conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
    conn.execute(
        "INSERT INTO message (ROWID, guid, text, is_from_me, date) "
        "VALUES (1, 'g1', 'photo', 1, 1000)"
    )
    conn.execute(
        "INSERT INTO attachment (ROWID, filename, uti, mime_type, transfer_name) "
        "VALUES (1, 'missing.jpg', 'public.jpeg', 'image/jpeg', 'IMG.jpg')"
    )
    conn.execute("INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (1, 1)")
    conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1)")
    conn.commit()
    conn.close()


def test_cli_imessage_audit_reports_and_exits_zero(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "chat.db"
    _make_db_with_attachment(db)

    # Force file-missing behavior by monkeypatching the existence check
    import chatx.imessage.report as report_module

    def always_missing(filename: str) -> bool:  # type: ignore[override]
        return False

    monkeypatch.setattr(report_module, "check_attachment_file_exists", always_missing, raising=True)

    out_dir = tmp_path / "out"
    result = runner.invoke(app, ["imessage", "audit", "--db", str(db), "--out", str(out_dir)])

    assert result.exit_code == 0
    # Should write missing_attachments.json and mention guidance
    report_path = out_dir / "missing_attachments.json"
    assert report_path.exists()
    assert "Guidance" in result.stdout or "Guidance" in result.stderr

