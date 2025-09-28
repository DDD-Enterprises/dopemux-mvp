"""Integration tests for reactions and replies folding (PR-2)."""

import sqlite3
from pathlib import Path

import pytest

from chatx.imessage.extract import extract_messages


class TestReactionsRepliesIntegration:
    """Test end-to-end reactions and replies processing."""
    
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
    
    def test_reactions_folded_into_messages(self, test_db, tmp_path):
        """Test that reactions are properly folded into parent messages."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Find messages with reactions
        messages_by_guid = {msg.source_ref.guid: msg for msg in messages}
        
        # Check that msg-001 ("Hello there!") has an "emphasize" reaction
        msg_001 = messages_by_guid.get("msg-001")
        assert msg_001 is not None
        assert len(msg_001.reactions) == 1
        assert msg_001.reactions[0].kind == "emphasize"
        assert msg_001.reactions[0].from_ == "me"
        
        # Check that msg-002 ("Hey! How are you?") has a "laugh" reaction  
        msg_002 = messages_by_guid.get("msg-002")
        assert msg_002 is not None
        assert len(msg_002.reactions) == 1
        assert msg_002.reactions[0].kind == "laugh"
        assert msg_002.reactions[0].from_ == "+15551234567"
        
        # Check that msg-003 has a "love" reaction
        msg_003 = messages_by_guid.get("msg-003")
        assert msg_003 is not None
        assert len(msg_003.reactions) == 1
        assert msg_003.reactions[0].kind == "love"
        assert msg_003.reactions[0].from_ == "me"
        
        # Check that msg-006 has a "like" reaction
        msg_006 = messages_by_guid.get("msg-006")
        assert msg_006 is not None
        assert len(msg_006.reactions) == 1
        assert msg_006.reactions[0].kind == "like"
        assert msg_006.reactions[0].from_ == "+15551234567"
    
    def test_reply_threading_resolved(self, test_db, tmp_path):
        """Test that reply threading is properly resolved."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Find reply messages
        messages_by_guid = {msg.source_ref.guid: msg for msg in messages}
        messages_by_id = {msg.msg_id: msg for msg in messages}
        
        # msg-005 ("Sure! How about tomorrow?") should reply to msg-004
        msg_005 = messages_by_guid.get("msg-005")
        assert msg_005 is not None
        assert msg_005.reply_to_msg_id is not None
        
        # Resolve the reply target
        parent_msg = messages_by_id.get(msg_005.reply_to_msg_id)
        assert parent_msg is not None
        assert parent_msg.source_ref.guid == "msg-004"
        assert "lunch" in parent_msg.text.lower()
        
        # msg-006 ("Perfect! Let's meet at noon.") should reply to msg-005
        msg_006 = messages_by_guid.get("msg-006")
        assert msg_006 is not None
        assert msg_006.reply_to_msg_id is not None
        
        # Resolve the reply target
        parent_msg = messages_by_id.get(msg_006.reply_to_msg_id)
        assert parent_msg is not None
        assert parent_msg.source_ref.guid == "msg-005"
        assert "tomorrow" in parent_msg.text.lower()
    
    def test_reactions_not_in_main_message_list(self, test_db, tmp_path):
        """Test that reaction messages don't appear as standalone messages."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Check that reaction GUIDs don't appear as main messages
        reaction_guids = {"react-001", "react-002", "react-003", "react-004", "react-orphan"}
        message_guids = {msg.source_ref.guid for msg in messages}
        
        # No reaction GUIDs should appear in the main message list
        assert not (reaction_guids & message_guids), "Reaction messages should not appear as standalone messages"
    
    def test_orphaned_reactions_handled_gracefully(self, test_db, tmp_path):
        """Test that reactions to non-existent messages are handled gracefully."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        # Should not raise exception even with orphaned reactions in test data
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Should still extract messages successfully
        assert len(messages) > 0
    
    def test_reaction_timestamps_preserved(self, test_db, tmp_path):
        """Test that reaction timestamps are preserved correctly."""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        
        messages = list(extract_messages(
            db_path=test_db,
            contact="+15551234567",
            out_dir=out_dir
        ))
        
        # Find a message with reactions
        messages_with_reactions = [msg for msg in messages if msg.reactions]
        assert len(messages_with_reactions) > 0
        
        for msg in messages_with_reactions:
            for reaction in msg.reactions:
                # Reaction should have valid timestamp
                assert reaction.ts is not None
                # Should be timezone aware
                assert reaction.ts.tzinfo is not None