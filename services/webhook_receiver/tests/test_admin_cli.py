import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from ledger.interface import parse_db_url
from storage import build_event_store

from admin import cmd_dedupe_check, cmd_stats, cmd_tail, _get_connection


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        db_url = f"sqlite:///{db_path}"
        
        # Ensure schema exists by initializing EventStore (which is assumed to not auto-migrate, but let's just create tables or use actual server migrations)
        # Wait, ensure_migrations isn't called here. We'll manually create the minimal schema we need for tests.
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE webhook_events (
                id INTEGER PRIMARY KEY,
                provider TEXT,
                idempotency_key TEXT,
                event_type TEXT,
                event_id TEXT,
                received_at_utc TEXT,
                payload_json TEXT,
                headers_json TEXT,
                signature_valid INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE run_events (
                id INTEGER PRIMARY KEY,
                run_id TEXT,
                phase TEXT,
                step_id TEXT,
                partition_id TEXT,
                provider TEXT,
                event_type TEXT,
                event_id TEXT,
                provider_ref TEXT,
                webhook_event_id INTEGER,
                dedupe_key TEXT,
                orphaned INTEGER,
                created_at_utc TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE async_jobs (
                id INTEGER PRIMARY KEY,
                provider TEXT,
                job_kind TEXT,
                external_job_id TEXT,
                run_id TEXT,
                phase TEXT,
                step_id TEXT,
                partition_id TEXT,
                attempt INTEGER,
                status TEXT,
                last_error TEXT,
                created_at_utc TEXT,
                updated_at_utc TEXT
            )
        ''')
        
        # Insert some dummy data
        conn.execute('''
            INSERT INTO webhook_events(provider, idempotency_key, event_type, event_id, received_at_utc)
            VALUES 
            ('openai', 'del1', 't1', 'e1', '2026-02-21T00:00:01Z'),
            ('openai', 'del2', 't2', 'e2', '2026-02-21T00:00:02Z')
        ''')
        
        conn.execute('''
            INSERT INTO run_events(run_id, created_at_utc)
            VALUES 
            ('r1', '2026-02-21T00:00:01Z'),
            ('r2', '2026-02-21T00:00:02Z'),
            ('r3', '2026-02-21T00:00:03Z')
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_url


def test_admin_stats_output_has_keys(temp_db, capsys):
    with mock.patch("admin.resolve_webhook_db_url", return_value=temp_db):
        conn, backend = _get_connection(temp_db)
        cmd_stats(conn, backend, temp_db)
        conn.close()
        
    captured = capsys.readouterr().out
    assert "db_url:" in captured
    assert "count(*) provider_events: 2" in captured
    assert "count(*) run_events: 3" in captured
    assert "count(*) async_jobs: 0" in captured


def test_admin_tail_orders_desc(temp_db, capsys):
    with mock.patch("admin.resolve_webhook_db_url", return_value=temp_db):
        conn, backend = _get_connection(temp_db)
        cmd_tail(conn, backend, "provider_events", limit=20)
        conn.close()
        
    captured = capsys.readouterr().out
    lines = captured.strip().split("\n")
    # First line is header, subsequent lines are ordered by id DESC
    assert "received_at_utc\tprovider\tdelivery_id\tevent_type\tevent_id" in lines[0]
    
    # We inserted del1 then del2. Since it's DESC, del2 should appear before del1
    assert "del2" in lines[1]
    assert "del1" in lines[2]


def test_dedupe_check_detects_existing(temp_db, capsys):
    with mock.patch("admin.resolve_webhook_db_url", return_value=temp_db):
        conn, backend = _get_connection(temp_db)
        cmd_dedupe_check(conn, backend, "del1")
        conn.close()
        
    captured = capsys.readouterr().out
    assert "Delivery ID 'del1' EXISTS." in captured
    assert "event_type=t1" in captured

    with mock.patch("admin.resolve_webhook_db_url", return_value=temp_db):
        conn, backend = _get_connection(temp_db)
        cmd_dedupe_check(conn, backend, "missing_key")
        conn.close()
        
    captured2 = capsys.readouterr().out
    assert "Delivery ID 'missing_key' does NOT exist." in captured2
