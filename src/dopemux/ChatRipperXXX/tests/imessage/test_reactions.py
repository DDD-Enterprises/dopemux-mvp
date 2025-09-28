"""Tests for reaction folding functionality."""

import pytest

from chatx.imessage.reactions import (
    get_reaction_type, is_reaction, is_reply, REACTION_TYPE_MAP
)


class TestReactionMapping:
    """Test reaction type mapping and detection."""
    
    def test_traditional_tapback_mapping(self):
        """Test traditional tapback type mapping."""
        assert get_reaction_type(2000) == "love"
        assert get_reaction_type(2001) == "like"
        assert get_reaction_type(2002) == "dislike"
        assert get_reaction_type(2003) == "laugh"
        assert get_reaction_type(2004) == "emphasize"
        assert get_reaction_type(2005) == "question"
    
    def test_custom_emoji_reaction_detection(self):
        """Test custom emoji reaction detection (iOS 16+)."""
        # Custom emoji reactions typically use codes 3000-3999 range
        assert get_reaction_type(3000) == "custom"
        assert get_reaction_type(3500) == "custom"
        assert get_reaction_type(3999) == "custom"
    
    def test_is_reaction_detection(self):
        """Test reaction message type detection."""
        # Traditional tapbacks
        assert is_reaction(2000) == True
        assert is_reaction(2001) == True
        assert is_reaction(2005) == True
        
        # Custom emoji reactions
        assert is_reaction(3000) == True
        assert is_reaction(3999) == True
        
        # Non-reactions
        assert is_reaction(0) == False
        assert is_reaction(1) == False
        assert is_reaction(1999) == False
    
    def test_is_reply_detection(self):
        """Test reply message detection."""
        # Reply with associated guid
        assert is_reply(0, True) == True
        
        # Not a reply (no associated guid)
        assert is_reply(0, False) == False
        
        # Reaction, not reply
        assert is_reply(2001, True) == False
    
    def test_unknown_reaction_type(self):
        """Test handling of unknown reaction types."""
        assert get_reaction_type(1999) is None
        assert get_reaction_type(9999) is None