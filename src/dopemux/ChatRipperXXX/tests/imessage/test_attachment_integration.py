"""Integration tests for attachment metadata extraction (PR-3)."""

import sqlite3
from pathlib import Path

import pytest

from chatx.imessage.extract import extract_messages


class TestAttachmentIntegration:
    """Test end-to-end attachment processing."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database from fixture SQL."""
        db_path = tmp_path / "chat.db"
        
        # Read and execute the fixture SQL
        fixture_sql = Path(__file__).parent.parent / "fixtures" / "imessage_test_data.sql"
        
        conn = sqlite3.connect(db_path)
        with open(fixture_sql) as f:
            conn.executescript(f.read())
        conn.close()
        
        return db_path
    
    def test_attachment_metadata_extraction(self, test_db, tmp_path):
        """Test that attachment metadata is properly extracted."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir,
            include_attachments=True
        ))
        
        # Find message with attachment (msg_14)
        messages_by_guid = {msg.source_ref.guid: msg for msg in messages}
        
        attach_msg = messages_by_guid.get("msg-attach-001")
        assert attach_msg is not None
        assert "photo" in attach_msg.text.lower()
        
        # Should have one attachment
        assert len(attach_msg.attachments) == 1
        
        attachment = attach_msg.attachments[0]
        assert attachment.type == "image"
        assert attachment.filename == "photo.jpg"
        assert attachment.mime_type == "image/jpeg"
        assert attachment.uti == "public.jpeg"
        assert attachment.transfer_name == "IMG_001.jpeg"
        assert attachment.abs_path is None  # No actual file to copy
    
    def test_no_attachments_when_disabled(self, test_db, tmp_path):
        """Test that attachments are not extracted when include_attachments=False."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir,
            include_attachments=False
        ))
        
        # All messages should have empty attachments
        for msg in messages:
            assert len(msg.attachments) == 0
    
    def test_multiple_attachment_types(self, tmp_path):
        """Test handling of different attachment types."""
        db_path = tmp_path / "chat.db"
        
        # Create test database with multiple attachment types
        conn = sqlite3.connect(db_path)
        
        # Create schema
        conn.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
        
        conn.execute("CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT)")
        conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, 'iMessage;-;+15551234567')")
        
        conn.execute(
            """
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, attributedBody BLOB,
                is_from_me INTEGER, handle_id INTEGER, service TEXT DEFAULT 'iMessage',
                date INTEGER, associated_message_guid TEXT,
                associated_message_type INTEGER DEFAULT 0
            )
            """
        )
        
        conn.execute("""
            CREATE TABLE attachment (
                ROWID INTEGER PRIMARY KEY, filename TEXT, uti TEXT, mime_type TEXT,
                transfer_name TEXT, total_bytes INTEGER, created_date INTEGER, start_date INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE message_attachment_join (
                message_id INTEGER, attachment_id INTEGER
            )
        """)
        
        conn.execute("CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER)")
        
        # Insert test message
        conn.execute(
            """
            INSERT INTO message (ROWID, guid, text, is_from_me, date)
            VALUES (1, 'multi-attach', 'Multiple attachments', 1, 1000)
            """
        )
        
        # Insert different attachment types
        conn.execute("""
            INSERT INTO attachment (ROWID, filename, uti, mime_type, transfer_name) VALUES
            (1, 'image.jpg', 'public.jpeg', 'image/jpeg', 'IMG_001.jpg'),
            (2, 'video.mp4', 'public.mpeg-4', 'video/mp4', 'MOV_001.mp4'),
            (3, 'audio.m4a', 'public.mpeg-4-audio', 'audio/mp4', 'AUD_001.m4a'),
            (4, 'document.pdf', 'com.adobe.pdf', 'application/pdf', 'DOC_001.pdf'),
            (5, 'unknown.xyz', NULL, NULL, 'UNK_001.xyz')
        """)
        
        # Link all attachments to the message
        for att_id in range(1, 6):
            conn.execute(
                "INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (1, ?)",
                (att_id,),
            )
        
        conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1)")
        
        conn.commit()
        conn.close()
        
        # Test extraction
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=db_path,
            contact="+15551234567",
            out_dir=out_dir,
            include_attachments=True
        ))
        
        assert len(messages) == 1
        message = messages[0]
        assert len(message.attachments) == 5
        
        # Verify attachment types
        attachment_types = {att.filename: att.type for att in message.attachments}
        assert attachment_types["image.jpg"] == "image"
        assert attachment_types["video.mp4"] == "video"
        assert attachment_types["audio.m4a"] == "audio"
        assert attachment_types["document.pdf"] == "file"
        assert attachment_types["unknown.xyz"] == "unknown"
    
    def test_attachment_binary_copying(self, test_db, tmp_path):
        """Test binary file copying behavior."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        # Create a fake attachment file to copy
        fake_attachments_dir = tmp_path / "fake_attachments"
        fake_attachments_dir.mkdir()
        fake_file = fake_attachments_dir / "photo.jpg"
        fake_file.write_bytes(b"fake image data")
        
        # Temporarily patch the attachments directory
        import chatx.imessage.attachments as att_module
        original_copy_func = att_module.copy_attachment_files
     
        def patched_copy_func(attachments, out_dir, backup_dir=None, *, dedupe_map=None):

            updated_attachments = []
            for att in attachments:
                if att.filename == "photo.jpg":
                    dest_path = out_dir / "attachments" / "fake" / "copied_photo.jpg"
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    dest_path.write_bytes(fake_file.read_bytes())
                    att.abs_path = str(dest_path)
                    att.source_meta.setdefault("hash", {})["sha256"] = "deadbeef"
                updated_attachments.append(att)
            return updated_attachments, dedupe_map or {}
        
        # Patch the function temporarily
        att_module.copy_attachment_files = patched_copy_func
        
        try:
            messages = list(extract_messages(
                db_path=test_db,
                contact="+15551234567",
                out_dir=out_dir,
                include_attachments=True,
                copy_binaries=True
            ))
            
            # Find message with attachment
            messages_with_attachments = [msg for msg in messages if msg.attachments]
            assert len(messages_with_attachments) > 0
            
            # Check that abs_path is set for copied files
            attachment = messages_with_attachments[0].attachments[0]
            assert attachment.abs_path is not None
            assert "copied_photo.jpg" in attachment.abs_path
            
            # Verify copied file exists
            copied_file = Path(attachment.abs_path)
            assert copied_file.exists()
            
        finally:
            # Restore original function
            att_module.copy_attachment_files = original_copy_func
    
    def test_messages_without_attachments_unaffected(self, test_db, tmp_path):
        """Test that messages without attachments are not affected by attachment processing."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir,
            include_attachments=True
        ))
        
        # Most messages should have no attachments
        messages_without_attachments = [msg for msg in messages if not msg.attachments]
        messages_with_attachments = [msg for msg in messages if msg.attachments]
        
        # Should have more messages without attachments than with
        assert len(messages_without_attachments) > len(messages_with_attachments)
        
        # Messages without attachments should still have proper structure
        for msg in messages_without_attachments[:3]:  # Check first few
            assert msg.msg_id
            assert msg.platform == "imessage"
            assert msg.timestamp
            assert isinstance(msg.attachments, list)
            assert len(msg.attachments) == 0
