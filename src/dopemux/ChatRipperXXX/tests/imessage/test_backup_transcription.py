"""Transcription using files resolved from a MobileSync backup (no copy_binaries).

Ensures that when running with --from-backup and --transcribe-audio local,
the extractor resolves audio attachments via Manifest.db and passes the
physical hashed file to the local transcription engine.
"""

import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from chatx.imessage.extract import extract_messages


def _make_manifest_db(path: Path, mappings: list[tuple[str, str, str]]) -> None:
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


def _make_db_with_audio(db_path: Path, rel_path: str) -> None:
    conn = sqlite3.connect(db_path)
    # Minimal schema
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
            transfer_name TEXT, total_bytes INTEGER, created_date INTEGER, start_date INTEGER, user_info BLOB
        )
        """
    )
    conn.execute(
        "CREATE TABLE message_attachment_join (message_id INTEGER, attachment_id INTEGER)"
    )
    conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")

    # One message with an audio attachment
    conn.execute(
        """
        INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, date)
        VALUES (1, 'm1', '\ufffc', 1, NULL, 1000)
        """
    )
    conn.execute(
        """
        INSERT INTO attachment (ROWID, filename, uti, mime_type, transfer_name)
        VALUES (1, ?, 'com.apple.m4a-audio', 'audio/m4a', 'voice.m4a')
        """,
        (rel_path,),
    )
    conn.execute("INSERT INTO message_attachment_join VALUES (1, 1)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 1)")
    conn.commit()
    conn.close()


def test_backup_transcription_local_engine(tmp_path: Path) -> None:
    # Prepare fake MobileSync backup
    backup = tmp_path / "Backup"
    backup.mkdir()
    manifest_db = backup / "Manifest.db"

    rel = "Library/SMS/Attachments/ab/cd/voice.m4a"
    file_id = "abfeedfacecafebabe1234567890abcdef"
    _make_manifest_db(manifest_db, [("HomeDomain", rel, file_id)])

    # Create physical hashed file (no extension in backups)
    shard = file_id[:2]
    physical_file = backup / shard / file_id
    physical_file.parent.mkdir(exist_ok=True)
    physical_file.write_bytes(b"audio-bytes")

    # Create minimal chat.db referencing the relative path
    db_path = tmp_path / "chat.db"
    _make_db_with_audio(db_path, rel)

    # Mock Whisper to ensure transcription occurs
    mock_whisper = Mock()
    mock_model = Mock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.return_value = {
        "text": "from-backup transcript",
        "segments": [{"no_speech_prob": 0.2}],
    }

    with patch.dict('sys.modules', {'whisper': mock_whisper}):
        messages = list(
            extract_messages(
                db_path=db_path,
                contact="+15551234567",
                include_attachments=True,
                copy_binaries=False,
                transcribe_audio="local",
                out_dir=tmp_path / "out",
                backup_dir=backup,
            )
        )

    assert len(messages) == 1
    m = messages[0]
    assert "transcripts" in m.source_meta
    t0 = m.source_meta["transcripts"][0]
    assert t0["transcript"] == "from-backup transcript"
    assert t0["engine"].startswith("whisper")

