"""Test configuration and fixtures."""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chatx.schemas.message import CanonicalMessage, SourceRef
from tests.fixtures import create_imessage_test_db, get_expected_messages


@pytest.fixture
def sample_message() -> CanonicalMessage:
    """Create a sample canonical message for testing."""
    return CanonicalMessage(
        msg_id="123",
        conv_id="conv_456",
        platform="imessage",
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        sender="Test User",
        sender_id="test@example.com",
        is_me=False,
        text="Hello, world!",
        source_ref=SourceRef(
            guid="test-chat-guid",
            path="/test/path/chat.db"
        )
    )


@pytest.fixture
def temp_chat_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database file for testing."""
    db_path = tmp_path / "test_chat.db"
    
    # Create an empty file (real tests would populate with SQLite data)
    db_path.touch()
    
    return db_path


@pytest.fixture
def sample_config_data() -> dict:
    """Sample configuration data for testing."""
    return {
        "verbose": False,
        "output_dir": "./output",
        "llm": {
            "provider": "local",
            "model": "llama2",
            "max_retries": 3,
            "timeout": 60
        },
        "redaction": {
            "strict_mode": True,
            "generate_report": True,
            "fail_on_leak": True
        },
        "batch_size": 10,
        "max_workers": 4
    }


@pytest.fixture
def imessage_test_db() -> Path:
    """Create a comprehensive iMessage test database with realistic data.
    
    Includes:
    - Basic messages
    - Reply chains
    - Reactions (tapbacks) of all types
    - Attachments
    - Different timestamp formats (seconds, microseconds, nanoseconds)
    - SMS vs iMessage
    - Edge cases (null text, missing handles, orphaned reactions)
    """
    return create_imessage_test_db()


@pytest.fixture
def expected_imessage_messages() -> list[dict]:
    """Get the expected canonical messages for the test database."""
    return get_expected_messages()


@pytest.fixture
def minimal_imessage_db(tmp_path: Path) -> Path:
    """Create a minimal iMessage database for basic testing."""
    db_path = tmp_path / "minimal_chat.db"
    
    # Create minimal test database with just essential tables and one message
    sql = """
    CREATE TABLE message (
        ROWID INTEGER PRIMARY KEY,
        guid TEXT,
        text TEXT,
        is_from_me INTEGER,
        date INTEGER
    );
    CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT);
    CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);
    CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);
    
    INSERT INTO handle (ROWID, id) VALUES (1, 'test@example.com');
    INSERT INTO chat (ROWID, guid) VALUES (1, 'test-chat-guid');
    INSERT INTO message (ROWID, guid, text, is_from_me, date)
    VALUES (1, 'test-msg', 'Hello', 0, 663360000);
    INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1);
    """
    
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        conn.commit()
        
    return db_path


@pytest.fixture
def invalid_imessage_db(tmp_path: Path) -> Path:
    """Create an invalid database missing required iMessage tables."""
    db_path = tmp_path / "invalid_chat.db"
    
    # Create database with wrong schema (missing required tables)
    sql = """
    CREATE TABLE wrong_table (id INTEGER PRIMARY KEY, data TEXT);
    INSERT INTO wrong_table (data) VALUES ('not an iMessage database');
    """
    
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        conn.commit()
        
    return db_path
