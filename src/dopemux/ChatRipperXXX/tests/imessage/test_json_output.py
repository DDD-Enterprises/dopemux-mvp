"""Tests for JSON output functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from chatx.imessage.extract import extract_messages
from chatx.utils.json_output import write_messages_with_validation


class TestJsonOutput:
    """Test JSON output with schema validation."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database from fixture SQL."""
        import sqlite3
        db_path = tmp_path / "chat.db"
        
        # Read and execute the fixture SQL
        fixture_sql = Path(__file__).parent.parent / "fixtures" / "imessage_test_data.sql"
        
        conn = sqlite3.connect(db_path)
        with open(fixture_sql, 'r') as f:
            conn.executescript(f.read())
        conn.close()
        
        return db_path
    
    def test_json_output_generation(self, test_db, tmp_path):
        """Test that JSON output is generated correctly."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        # Extract messages
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Write JSON output
        output_file = tmp_path / "test_output.json"
        write_messages_with_validation(messages, output_file)
        
        # Verify file exists and has content
        assert output_file.exists()
        
        # Parse and validate JSON structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "messages" in data
        assert "total_count" in data
        assert "schema_version" in data
        assert data["total_count"] == len(messages)
        assert len(data["messages"]) == len(messages)
        
        # Verify first message structure
        if messages:
            msg_data = data["messages"][0]
            assert "msg_id" in msg_data
            assert "conv_id" in msg_data
            assert "platform" in msg_data
            assert "timestamp" in msg_data
            assert "sender" in msg_data
            assert "sender_id" in msg_data
            assert "is_me" in msg_data
            assert "source_ref" in msg_data
            assert msg_data["platform"] == "imessage"
    
    def test_json_output_with_no_messages(self, tmp_path):
        """Test JSON output with empty message list."""
        output_file = tmp_path / "empty_output.json"
        write_messages_with_validation([], output_file)
        
        # Verify file exists
        assert output_file.exists()
        
        # Parse and validate JSON structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["total_count"] == 0
        assert len(data["messages"]) == 0
        assert data["schema_version"] == "1.0"