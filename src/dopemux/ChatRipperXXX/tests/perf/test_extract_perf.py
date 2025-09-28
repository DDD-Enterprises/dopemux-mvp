"""Performance smoke tests for iMessage extraction."""

import os
import sqlite3
import time
from pathlib import Path

import pytest

from chatx.imessage.extract import extract_messages


class TestExtractionPerformance:
    """Test extraction performance meets targets."""

    def _make_synth_db(self, db_path: Path, n_messages: int) -> None:
        """Create a synthetic iMessage-like DB with N messages for a single contact."""
        conn = sqlite3.connect(db_path)
        # Minimal schema needed by extractor
        conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
        conn.execute(
            """
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, attributedBody BLOB,
                is_from_me INTEGER, handle_id INTEGER, service TEXT DEFAULT 'iMessage',
                date INTEGER,
                associated_message_guid TEXT,
                associated_message_type INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE TABLE message_attachment_join (message_id INTEGER, attachment_id INTEGER)"
        )
        conn.execute(
            "CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)"
        )

        # Seed one contact and chat
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
        chat_guid = "iMessage;-;+15551234567"
        conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, ?)", (chat_guid,))

        # Insert N synthetic messages (alternating sender)
        base_ts = 1_000_000_000  # arbitrary Apple epoch nanoseconds
        rows = []
        cmj_rows = []
        for i in range(1, n_messages + 1):
            guid = f"msg-{i}"
            is_me = 1 if (i % 2 == 0) else 0
            handle_id = None if is_me else 1
            text = f"hello {i}"
            date = base_ts + i * 1_000_000_000  # +1s each
            rows.append((i, guid, text, None, is_me, handle_id, 'iMessage', date, None, 0))
            cmj_rows.append((1, i))

        conn.executemany(
            """
            INSERT INTO message (
                ROWID,
                guid,
                text,
                attributedBody,
                is_from_me,
                handle_id,
                service,
                date,
                associated_message_guid,
                associated_message_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.executemany(
            "INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)",
            cmj_rows,
        )
        conn.commit()
        conn.close()

    @pytest.mark.perf
    def test_extract_throughput_smoke(self, tmp_path):
        """Generate synthetic rows and measure extraction throughput.

        Skips by default unless CHATX_RUN_PERF=1.
        Prints msgs/min for quick regression spotting when enabled.
        """
        if os.environ.get("CHATX_RUN_PERF") != "1":
            pytest.skip("Perf smoke disabled (set CHATX_RUN_PERF=1 to run)")

        db_path = tmp_path / "chat.db"
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        n = int(os.environ.get("CHATX_PERF_N", "3000"))
        self._make_synth_db(db_path, n)

        t0 = time.perf_counter()
        msgs = list(
            extract_messages(
                db_path=db_path,
                contact="+15551234567",
                include_attachments=False,
                copy_binaries=False,
                transcribe_audio="off",
                out_dir=out_dir,
            )
        )
        elapsed = time.perf_counter() - t0
        rate = (len(msgs) / max(elapsed, 1e-6)) * 60.0

        # Emit a metrics line for visibility (non-assertive)
        print(f"[PERF] extracted={len(msgs)} elapsed_s={elapsed:.3f} rate_msgs_per_min={rate:.0f}")

        # Basic sanity: extracted exactly n rows
        assert len(msgs) == n
