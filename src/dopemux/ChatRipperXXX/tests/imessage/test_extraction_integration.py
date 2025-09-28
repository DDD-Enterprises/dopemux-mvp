"""Integration tests for iMessage extraction with real database."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from chatx.imessage.extract import extract_messages


class TestExtractionIntegration:
    """Test end-to-end extraction with realistic database."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database from fixture SQL."""
        db_path = tmp_path / "chat.db"
        
        # Read and execute the fixture SQL
        fixture_sql = Path(__file__).parent.parent / "fixtures" / "imessage_test_data.sql"
        
        conn = sqlite3.connect(db_path)
        with open(fixture_sql, 'r') as f:
            conn.executescript(f.read())
        conn.close()
        
        return db_path
    
    def test_extract_phone_contact(self, test_db, tmp_path):
        """Test extracting messages for a phone number contact."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Should find messages for this contact
        assert len(messages) > 0
        
        # Check message structure
        msg = messages[0]
        assert msg.platform == "imessage"
        assert msg.source_ref.path == str(test_db)
        assert msg.msg_id.startswith("msg_")
        assert msg.conv_id
        assert msg.timestamp
        assert msg.sender
        assert msg.sender_id
        assert isinstance(msg.is_me, bool)
        
        # Should have provenance
        assert msg.source_ref.guid
        assert msg.source_meta["rowid"]
    
    def test_extract_email_contact(self, test_db, tmp_path):
        """Test extracting messages for an email contact.""" 
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="friend@example.com",
            out_dir=out_dir
        ))
        
        # Should find messages for this contact
        assert len(messages) > 0
        assert any("friend@example.com" in msg.sender_id for msg in messages)
    
    def test_extract_nonexistent_contact(self, test_db, tmp_path):
        """Test extracting for contact that doesn't exist."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="nonexistent@example.com",
            out_dir=out_dir
        ))
        
        # Should return no messages
        assert len(messages) == 0
    
    def test_apple_timestamp_conversion(self, test_db, tmp_path):
        """Test that Apple timestamps are converted correctly."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # All messages should have valid ISO timestamps
        for msg in messages:
            assert msg.timestamp
            # Should be UTC timezone aware
            assert msg.timestamp.tzinfo is not None