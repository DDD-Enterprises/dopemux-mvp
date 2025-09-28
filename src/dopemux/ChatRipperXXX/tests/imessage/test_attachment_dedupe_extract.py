from __future__ import annotations

import sqlite3
from pathlib import Path

from chatx.imessage.extract import extract_messages
from chatx.imessage.attachments import compute_file_hash


def _setup_db_with_two_msgs_and_same_attachment(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
    conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551239999')")
    conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
    conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, 'iMessage;-;+15551239999')")
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

    # Two messages in same chat
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date) VALUES (1, 'm1', 'pic', 1, 1000)")
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date) VALUES (2, 'm2', 'pic again', 0, 2000)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 1)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 2)")

    # One attachment row reused for both messages
    conn.execute(
        "INSERT INTO attachment (ROWID, filename, uti, mime_type, transfer_name) VALUES (10, 'photo.jpg', 'public.jpeg', 'image/jpeg', 'IMG.jpg')"
    )
    conn.execute("INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (1, 10)")
    conn.execute("INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (2, 10)")

    conn.commit()
    conn.close()


def test_dedupe_across_messages(tmp_path: Path) -> None:
    # Arrange DB and fake attachments dir
    db = tmp_path / "chat.db"
    _setup_db_with_two_msgs_and_same_attachment(db)

    # Patch Path.home for Messages/Attachments lookup
    import chatx.imessage.attachments as att_module
    original_home = att_module.Path.home
    att_module.Path.home = lambda: tmp_path
    try:
        attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
        attachments_dir.mkdir(parents=True)
        img_path = attachments_dir / "photo.jpg"
        img_bytes = b"same content"
        img_path.write_bytes(img_bytes)
        expected_hash = compute_file_hash(img_path)

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        messages = list(
            extract_messages(
                db_path=db,
                contact="+15551239999",
                include_attachments=True,
                copy_binaries=True,
                thumbnails=False,
                transcribe_audio="off",
                out_dir=out_dir,
            )
        )

        # Two messages extracted
        assert len(messages) == 2
        # Both should have attachments_info with same hash
        hashes = []
        for m in messages:
            infos = m.source_meta.get("attachments_info", [])
            assert infos
            hashes.append(infos[0]["hash"])
        assert hashes[0] == hashes[1] == expected_hash

        # Only one file stored in hashed layout
        stored = list((out_dir / "attachments").rglob(f"{expected_hash}_photo.jpg"))
        assert len(stored) == 1
    finally:
        att_module.Path.home = original_home

