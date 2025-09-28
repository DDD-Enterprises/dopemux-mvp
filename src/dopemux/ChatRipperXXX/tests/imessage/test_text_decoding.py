"""Unit tests for iMessage text decoding helpers.

Covers:
- attributedBody decoding via binary plist and UTF-8 heuristic
- message_summary_info decoding via binary plist and UTF-8 heuristic
"""

import plistlib
import sqlite3
from pathlib import Path

from chatx.extractors.imessage import IMessageExtractor


def test_decode_attributed_body_plist(tmp_path: Path) -> None:
    db_path = tmp_path / "chat.db"
    db_path.touch()
    extractor = IMessageExtractor(db_path)
    payload = plistlib.dumps({"string": "Hello world"})
    text = extractor._decode_attributed_body(payload)
    assert text == "Hello world"


def test_decode_attributed_body_utf8_fallback(tmp_path: Path) -> None:
    db_path = tmp_path / "chat.db"
    db_path.touch()
    extractor = IMessageExtractor(db_path)
    payload = "Some utf8 text with ✓".encode("utf-8")
    text = extractor._decode_attributed_body(payload)
    assert "Some utf8 text" in (text or "")


def test_decode_message_summary_info_plist(tmp_path: Path) -> None:
    # Create temp sqlite DB with message_summary_info table
    db_path = tmp_path / "msi.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE message_summary_info (message_rowid INTEGER, content BLOB)"
        )
        payload = plistlib.dumps({"text": "Edited content"})
        conn.execute(
            "INSERT INTO message_summary_info VALUES (?, ?)",
            (1, payload),
        )
        conn.commit()

        extractor = IMessageExtractor(db_path)
        text = extractor._decode_message_summary_info(conn, 1)
        assert text == "Edited content"
    finally:
        conn.close()


def test_decode_message_summary_info_utf8(tmp_path: Path) -> None:
    db_path = tmp_path / "msi2.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE message_summary_info (message_rowid INTEGER, content BLOB)"
        )
        payload = b"Raw edited"
        conn.execute(
            "INSERT INTO message_summary_info VALUES (?, ?)", (42, payload)
        )
        conn.commit()

        extractor = IMessageExtractor(db_path)
        text = extractor._decode_message_summary_info(conn, 42)
        assert text == "Raw edited"
    finally:
        conn.close()

