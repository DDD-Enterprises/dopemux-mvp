"""Tests for iMessage reply relationship resolution."""

import sqlite3

import pytest


class TestReplyResolution:
    """Test reply-to message linking functionality."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database with reply chains."""
        db_path = tmp_path / "chat.db"
        
        # Create database with reply chain
        conn = sqlite3.connect(db_path)
        
        # Create minimal schema
        conn.execute("""
            CREATE TABLE handle (
                ROWID INTEGER PRIMARY KEY,
                id TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE chat (
                ROWID INTEGER PRIMARY KEY,
                guid TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY,
                guid TEXT,
                text TEXT,
                attributedBody BLOB,
                is_from_me INTEGER,
                handle_id INTEGER,
                service TEXT DEFAULT 'iMessage',
                date INTEGER,
                associated_message_guid TEXT,
                associated_message_type INTEGER DEFAULT 0
            )
        """)
        
        conn.execute("""
            CREATE TABLE chat_message_join (
                chat_id INTEGER,
                message_id INTEGER
            )
        """)
        
        # Insert test data
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
        conn.execute("INSERT INTO chat (ROWID, guid) VALUES (1, 'iMessage;-;+15551234567')")
        
        # Create reply chain: original -> reply1 -> reply2
        conn.execute("""
            INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, date) 
            VALUES (1, 'original', 'Original message', 0, 1, 1000)
        """)
        
        conn.execute("""
            INSERT INTO message (ROWID, guid, text, is_from_me, date, associated_message_guid, associated_message_type) 
            VALUES (2, 'reply1', 'First reply', 1, 2000, 'original', 0)
        """)
        
        conn.execute("""
            INSERT INTO message (ROWID, guid, text, is_from_me, date, associated_message_guid, associated_message_type) 
            VALUES (3, 'reply2', 'Second reply', 0, 3000, 'reply1', 0)
        """)
        
        # Link messages to chat
        conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1), (1, 2), (1, 3)")
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def test_reply_chain_resolution(self, test_db, tmp_path):
        """Test that reply chains are resolved correctly."""
        from chatx.imessage.extract import extract_messages
        
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Should have 3 messages
        assert len(messages) == 3
        
        # Build lookup maps
        messages_by_guid = {msg.source_ref.guid: msg for msg in messages}
        
        # Verify reply chain
        original = messages_by_guid["original"]
        reply1 = messages_by_guid["reply1"]
        reply2 = messages_by_guid["reply2"]
        
        # Original should have no parent
        assert original.reply_to_msg_id is None
        
        # Reply1 should point to original
        assert reply1.reply_to_msg_id == original.msg_id
        
        # Reply2 should point to reply1
        assert reply2.reply_to_msg_id == reply1.msg_id