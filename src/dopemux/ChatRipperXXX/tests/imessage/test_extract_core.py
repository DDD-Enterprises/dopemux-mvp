"""Tests for core iMessage extraction functionality."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from chatx.imessage.extract import apple_timestamp_to_iso, resolve_contact_handles


class TestAppleTimestampConversion:
    """Test Apple Core Data timestamp conversion."""
    
    def test_apple_epoch_conversion(self):
        """Test conversion of Apple epoch (2001-01-01 00:00:00 UTC)."""
        # Apple epoch in nanoseconds is 0
        result = apple_timestamp_to_iso(0)
        assert result == "2001-01-01T00:00:00Z"
    
    def test_known_timestamp_conversion(self):
        """Test conversion of a known timestamp."""
        # Jan 1, 2024 00:00:00 UTC = 23 years after Apple epoch
        # 23 years * 365.25 days/year * 24 hours/day * 3600 seconds/hour * 1e9 nanoseconds/second
        ns_since_apple_epoch = int(23 * 365.25 * 24 * 3600 * 1_000_000_000)
        result = apple_timestamp_to_iso(ns_since_apple_epoch)
        assert result.startswith("2024-01-01T")
    
    def test_negative_timestamp(self):
        """Test handling of negative timestamps (before Apple epoch)."""
        # 1 day before Apple epoch
        ns_before_epoch = -24 * 3600 * 1_000_000_000
        result = apple_timestamp_to_iso(ns_before_epoch)
        assert result == "2000-12-31T00:00:00Z"


class TestContactHandleResolution:
    """Test contact identifier resolution to handle IDs."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database with handle data."""
        import sqlite3
        db_path = tmp_path / "chat.db"
        
        # Create minimal handle table for testing
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE handle (
                ROWID INTEGER PRIMARY KEY,
                id TEXT,
                service TEXT DEFAULT 'iMessage'
            )
        """)
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (2, 'test@example.com')")
        conn.commit()
        conn.close()
        
        return db_path
    
    def test_exact_match_resolution(self, test_db):
        """Test exact contact resolution."""
        import sqlite3
        conn = sqlite3.connect(test_db)
        try:
            result = resolve_contact_handles(conn, "test@example.com")
            assert result == [2]
        finally:
            conn.close()
    
    def test_no_match_resolution(self, test_db):
        """Test resolution for non-existent contact."""
        import sqlite3
        conn = sqlite3.connect(test_db)
        try:
            result = resolve_contact_handles(conn, "nonexistent@example.com")
            assert result == []
        finally:
            conn.close()


class TestExtractMessages:
    """Test main message extraction function."""
    
    def test_extract_empty_database(self, tmp_path):
        """Test extraction from empty database."""
        from chatx.imessage.extract import extract_messages
        import sqlite3
        
        # Create empty database with proper schema
        fake_db = tmp_path / "chat.db"
        conn = sqlite3.connect(fake_db)
        # Create minimal schema
        conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        conn.execute("CREATE TABLE message (ROWID INTEGER PRIMARY KEY, guid TEXT)")
        conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")  
        conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
        conn.commit()
        conn.close()
        
        # Should return empty iterator for non-existent contact
        messages = list(extract_messages(
            db_path=fake_db,
            contact="test@example.com",
            out_dir=tmp_path
        ))
        assert len(messages) == 0