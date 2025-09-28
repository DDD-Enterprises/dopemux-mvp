from __future__ import annotations

import sqlite3
from pathlib import Path

from PIL import Image

from chatx.imessage.extract import extract_messages
from chatx.imessage.attachments import compute_file_hash


def test_thumbnail_generation(tmp_path: Path) -> None:
    # Create test database with one image attachment
    db = tmp_path / "chat.db"
    conn = sqlite3.connect(db)
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
        "INSERT INTO message (ROWID, guid, text, is_from_me, date) VALUES (1, 'guid-1', 'img', 1, 1000)"
    )
    conn.execute(
        "INSERT INTO attachment (ROWID, filename, uti, mime_type, transfer_name) VALUES (1, 'photo.jpg', 'public.jpeg', 'image/jpeg', 'IMG.jpg')"
    )
    conn.execute("INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (1, 1)")
    conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1)")
    conn.commit()
    conn.close()

    # Create a small image file in default attachments location
    attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
    attachments_dir.mkdir(parents=True)
    img_path = attachments_dir / "photo.jpg"
    Image.new("RGB", (64, 32), color="red").save(img_path)

    # Patch Path.home to tmp_path
    import chatx.imessage.attachments as att_module
    original_home = att_module.Path.home
    att_module.Path.home = lambda: tmp_path
    try:
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        messages = list(
            extract_messages(
                db_path=db,
                contact="+15551234567",
                include_attachments=True,
                copy_binaries=False,
                thumbnails=True,
                transcribe_audio="off",
                out_dir=out_dir,
            )
        )
        assert messages
        msg = messages[0]
        thumb_hash = compute_file_hash(img_path)
        expected_thumb = out_dir / "thumbnails" / thumb_hash[:2] / f"{thumb_hash}.jpg"
        assert expected_thumb.exists()
        with Image.open(expected_thumb) as thumb:
            assert max(thumb.size) <= 256
        assert msg.source_meta.get("image", {}).get("thumb_path") == str(expected_thumb)
    finally:
        att_module.Path.home = original_home
