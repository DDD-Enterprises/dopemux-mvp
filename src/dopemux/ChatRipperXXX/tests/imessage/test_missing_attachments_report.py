"""Tests for missing attachments reporting functionality (PR-4)."""

import json
import sqlite3
from pathlib import Path

import pytest

from chatx.imessage.report import (
    check_attachment_file_exists,
    scan_for_missing_attachments, 
    generate_missing_attachments_report,
    validate_missing_attachments_report
)


class TestMissingAttachmentsReport:
    """Test missing attachment detection and reporting."""
    
    @pytest.fixture
    def test_db_with_attachments(self, tmp_path):
        """Create test database with attachment references."""
        db_path = tmp_path / "chat.db"
        
        conn = sqlite3.connect(db_path)
        
        # Create schema
        conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
        
        conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
        conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, 'iMessage;-;+15551234567')")
        
        conn.execute("""
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, attributedBody BLOB,
                is_from_me INTEGER, handle_id INTEGER, service TEXT DEFAULT 'iMessage',
                date INTEGER, associated_message_guid TEXT, associated_message_type INTEGER DEFAULT 0
            )
        """)
        
        conn.execute("""
            CREATE TABLE attachment (
                ROWID INTEGER PRIMARY KEY, filename TEXT, uti TEXT, mime_type TEXT,
                transfer_name TEXT, total_bytes INTEGER, created_date INTEGER, start_date INTEGER, user_info BLOB
            )
        """)
        
        conn.execute("""
            CREATE TABLE message_attachment_join (message_id INTEGER, attachment_id INTEGER)
        """)
        
        conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
        
        # Insert test messages
        conn.execute("""
            INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, date) VALUES
            (1, 'msg-with-attachment', 'Check this out!', 1, NULL, 1000),
            (2, 'msg-missing-attachment', 'Photo is gone', 0, 1, 2000)
        """)
        
        # Insert attachments - some exist, some don't
        conn.execute("""
            INSERT INTO attachment (ROWID, filename, uti, mime_type) VALUES
            (1, 'existing_file.jpg', 'public.jpeg', 'image/jpeg'),
            (2, 'missing_file.jpg', 'public.jpeg', 'image/jpeg'),
            (3, 'another_missing.pdf', 'com.adobe.pdf', 'application/pdf')
        """)
        
        # Link attachments to messages
        conn.execute("INSERT INTO message_attachment_join VALUES (1, 1), (2, 2), (2, 3)")
        conn.execute("INSERT INTO chat_message_join VALUES (1, 1), (1, 2)")
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def test_check_attachment_file_exists(self, tmp_path):
        """Test file existence checking."""
        # Create a test file
        test_file = tmp_path / "test_attachment.jpg"
        test_file.write_bytes(b"test content")
        
        # Mock Path.home to point to our test directory
        import chatx.imessage.report as report_module
        original_home = Path.home()
        
        def mock_home():
            return tmp_path
        
        report_module.Path.home = mock_home
        
        # Create expected Messages structure
        messages_dir = tmp_path / "Library" / "Messages" / "Attachments"
        messages_dir.mkdir(parents=True)
        (messages_dir / "test_attachment.jpg").write_bytes(b"test content")
        
        try:
            # Should find existing file
            assert check_attachment_file_exists("test_attachment.jpg") == True
            
            # Should not find non-existent file
            assert check_attachment_file_exists("nonexistent.jpg") == False
            
            # Should handle None/empty filename
            assert check_attachment_file_exists(None) == False
            assert check_attachment_file_exists("") == False
            
        finally:
            # Restore original home
            report_module.Path.home = lambda: original_home
    
    def test_scan_for_missing_attachments(self, test_db_with_attachments, tmp_path):
        """Test scanning for missing attachments."""
        # Mock file system - only "existing_file.jpg" exists
        import chatx.imessage.report as report_module
        original_home = Path.home()
        
        def mock_home():
            return tmp_path
        
        report_module.Path.home = mock_home
        
        messages_dir = tmp_path / "Library" / "Messages" / "Attachments"
        messages_dir.mkdir(parents=True)
        (messages_dir / "existing_file.jpg").write_bytes(b"exists")
        # missing_file.jpg and another_missing.pdf intentionally not created
        
        try:
            conn = sqlite3.connect(test_db_with_attachments)
            
            # Scan for missing attachments
            missing_items = scan_for_missing_attachments(conn, "+15551234567")
            
            # Should find 2 missing files
            assert len(missing_items) == 2
            
            missing_filenames = {item.filename for item in missing_items}
            assert "missing_file.jpg" in missing_filenames
            assert "another_missing.pdf" in missing_filenames
            assert "existing_file.jpg" not in missing_filenames
            
            # Check item structure
            for item in missing_items:
                assert item.conv_guid == "iMessage;-;+15551234567"
                assert item.msg_id.startswith("msg_")
                assert item.filename in ["missing_file.jpg", "another_missing.pdf"]
            
            conn.close()
            
        finally:
            report_module.Path.home = lambda: original_home
    
    def test_generate_missing_attachments_report(self, test_db_with_attachments, tmp_path):
        """Test full report generation."""
        # Mock file system - no files exist
        import chatx.imessage.report as report_module
        original_home = Path.home()
        
        def mock_home():
            return tmp_path
        
        report_module.Path.home = mock_home
        
        # Don't create any attachment files - all should be missing
        messages_dir = tmp_path / "Library" / "Messages" / "Attachments"
        messages_dir.mkdir(parents=True)
        
        try:
            conn = sqlite3.connect(test_db_with_attachments)
            out_dir = tmp_path / "output"
            
            # Generate report
            missing_counts = generate_missing_attachments_report(conn, out_dir, "+15551234567")
            
            # Should report missing files
            assert len(missing_counts) > 0
            assert "iMessage;-;+15551234567" in missing_counts
            
            # Report file should exist
            report_path = out_dir / "missing_attachments.json"
            assert report_path.exists()
            
            # Verify report structure
            with open(report_path) as f:
                report_data = json.load(f)
            
            assert "generated_at" in report_data
            assert report_data["contact"] == "+15551234567"
            assert "items" in report_data
            assert "summary" in report_data
            assert "remediation_guidance" in report_data
            
            # Check summary
            summary = report_data["summary"]
            assert summary["total_missing"] == 3  # All 3 attachments missing
            assert "per_conversation" in summary
            assert summary["per_conversation"]["iMessage;-;+15551234567"] == 3
            
            # Check items
            assert len(report_data["items"]) == 3
            for item in report_data["items"]:
                assert "conv_guid" in item
                assert "msg_id" in item
                assert "filename" in item
            
            # Check remediation guidance
            guidance = report_data["remediation_guidance"]
            assert "manual_steps" in guidance
            assert len(guidance["manual_steps"]) > 0
            assert any("Messages app" in step for step in guidance["manual_steps"])
            
            conn.close()
            
        finally:
            report_module.Path.home = lambda: original_home
    
    def test_report_with_no_missing_attachments(self, tmp_path):
        """Test report generation when no attachments are missing."""
        db_path = tmp_path / "chat.db"
        
        # Create minimal DB with no attachments
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
        conn.execute("CREATE TABLE message (ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, is_from_me INTEGER, handle_id INTEGER, date INTEGER)")
        conn.execute("""
            CREATE TABLE attachment (
                ROWID INTEGER PRIMARY KEY, filename TEXT, uti TEXT, mime_type TEXT,
                transfer_name TEXT, total_bytes INTEGER, created_date INTEGER, start_date INTEGER, user_info BLOB
            )
        """)
        conn.execute("CREATE TABLE message_attachment_join (message_id INTEGER, attachment_id INTEGER)")
        conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
        conn.commit()
        
        out_dir = tmp_path / "output"
        
        # Generate report
        missing_counts = generate_missing_attachments_report(conn, out_dir, "+15551234567")
        
        # Should be empty
        assert len(missing_counts) == 0
        
        # Report should still be generated
        report_path = out_dir / "missing_attachments.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report_data = json.load(f)
        
        assert report_data["summary"]["total_missing"] == 0
        assert len(report_data["items"]) == 0
        
        conn.close()
    
    def test_validate_missing_attachments_report_schema(self, tmp_path):
        """Test JSON schema validation of generated reports."""
        # Create a valid report
        report_data = {
            "generated_at": "2024-01-01T00:00:00Z",
            "contact": "+15551234567",
            "items": [
                {
                    "conv_guid": "iMessage;-;+15551234567",
                    "msg_id": "msg_1",
                    "filename": "missing.jpg"
                }
            ],
            "summary": {
                "total_missing": 1,
                "per_conversation": {
                    "iMessage;-;+15551234567": 1
                }
            },
            "remediation_guidance": {
                "manual_steps": [
                    "Open Messages app",
                    "Download attachments"
                ]
            }
        }
        
        report_path = tmp_path / "report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        # Should validate successfully
        is_valid = validate_missing_attachments_report(report_path)
        assert is_valid == True
    
    def test_all_attachments_found_scenario(self, test_db_with_attachments, tmp_path):
        """Test scenario where all attachment files are found."""
        # Mock file system - create all attachment files
        import chatx.imessage.report as report_module
        original_home = Path.home()
        
        def mock_home():
            return tmp_path
        
        report_module.Path.home = mock_home
        
        messages_dir = tmp_path / "Library" / "Messages" / "Attachments"
        messages_dir.mkdir(parents=True)
        
        # Create all attachment files
        (messages_dir / "existing_file.jpg").write_bytes(b"content1")
        (messages_dir / "missing_file.jpg").write_bytes(b"content2")
        (messages_dir / "another_missing.pdf").write_bytes(b"content3")
        
        try:
            conn = sqlite3.connect(test_db_with_attachments)
            
            missing_items = scan_for_missing_attachments(conn, "+15551234567")
            
            # Should find no missing files
            assert len(missing_items) == 0
            
            conn.close()
            
        finally:
            report_module.Path.home = lambda: original_home
