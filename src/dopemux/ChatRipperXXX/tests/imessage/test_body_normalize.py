from __future__ import annotations

import base64
import sqlite3
from pathlib import Path

from chatx.imessage.body_normalize import normalize_attributed_body
from chatx.imessage.extract import extract_messages


def test_normalize_attributed_body_basic() -> None:
    raw = b"Hello \xf0\x9f\x98\x80 <b>bold</b>\n"  # includes emoji and tag-like content
    cleaned = normalize_attributed_body(raw)
    assert cleaned is not None
    assert "Hello" in cleaned and "bold" in cleaned
    # No control newlines after normalization
    assert "\n" not in cleaned


def _setup_db_with_attributed_body(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
    conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551230000')")
    conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
    conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, 'iMessage;-;+15551230000')")
    conn.execute(
        """
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, attributedBody BLOB,
            is_from_me INTEGER, handle_id INTEGER, service TEXT DEFAULT 'iMessage',
            date INTEGER, associated_message_guid TEXT, associated_message_type INTEGER DEFAULT 0
        )
        """
    )
    conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
    # Insert one message with only attributedBody
    raw = b"Hello <b>world</b>"
    conn.execute(
        "INSERT INTO message (ROWID, guid, text, attributedBody, is_from_me, handle_id, date) VALUES (1, 'g1', NULL, ?, 1, 1, 1000)",
        (raw,),
    )
    conn.execute("INSERT INTO chat_message_join VALUES (1, 1)")
    conn.commit()
    conn.close()


def test_imessage_extract_preserves_raw_and_sets_text(tmp_path: Path) -> None:
    db = tmp_path / "chat.db"
    _setup_db_with_attributed_body(db)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    messages = list(
        extract_messages(
            db_path=db,
            contact="+15551230000",
            out_dir=out_dir,
        )
    )
    assert len(messages) == 1
    m = messages[0]
    # Text should be a non-empty string from normalization
    assert isinstance(m.text, str) and len(m.text) > 0
    # Raw attributed body should be preserved as base64 under source_meta.raw
    raw = m.source_meta.get("raw", {}).get("attributed_body")
    assert isinstance(raw, str)
    # Decodes back to original bytes
    assert base64.b64decode(raw) == b"Hello <b>world</b>"

