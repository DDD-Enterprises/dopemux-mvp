from __future__ import annotations

import sqlite3
from pathlib import Path

from chatx.imessage.extract import extract_messages


def _setup_min_db(db_path: Path) -> None:
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
    conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
    conn.commit()
    conn.close()


def test_reaction_deduplication(tmp_path: Path) -> None:
    db = tmp_path / "chat.db"
    _setup_min_db(db)
    conn = sqlite3.connect(db)
    # Parent message
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date) VALUES (1, 'parent-guid', 'Hello', 0, 1000)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 1)")
    # Duplicate reaction rows (like)
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date, associated_message_guid, associated_message_type, handle_id) VALUES (2, 'r1', '', 0, 1100, 'parent-guid', 2001, 1)")
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date, associated_message_guid, associated_message_type, handle_id) VALUES (3, 'r2', '', 0, 1100, 'parent-guid', 2001, 1)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 2)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 3)")
    conn.commit()
    conn.close()

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    messages = list(
        extract_messages(
            db_path=db,
            contact="+15551234567",
            out_dir=out_dir,
        )
    )
    assert len(messages) == 1
    m = messages[0]
    # Only one reaction folded
    assert len(m.reactions) == 1
    assert m.reactions[0].kind == "like"


def test_reply_resolution_order_independent(tmp_path: Path) -> None:
    db = tmp_path / "chat.db"
    _setup_min_db(db)
    conn = sqlite3.connect(db)
    # Insert reply first, then parent
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date, associated_message_guid) VALUES (2, 'child', 'Reply', 1, 2000, 'parent')")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 2)")
    conn.execute("INSERT INTO message (ROWID, guid, text, is_from_me, date) VALUES (1, 'parent', 'Hello', 0, 1000)")
    conn.execute("INSERT INTO chat_message_join VALUES (1, 1)")
    conn.commit()
    conn.close()

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    messages = list(
        extract_messages(
            db_path=db,
            contact="+15551234567",
            out_dir=out_dir,
        )
    )
    # Two non-reaction messages expected
    assert len(messages) == 2
    by_guid = {m.source_ref.guid: m for m in messages}
    assert by_guid["child"].reply_to_msg_id == by_guid["parent"].msg_id

