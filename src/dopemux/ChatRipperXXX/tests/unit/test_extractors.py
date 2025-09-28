"""Tests for extractor interfaces."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from chatx.extractors.base import BaseExtractor, detect_platform
from chatx.extractors.imessage import IMessageExtractor


class TestBaseExtractor:
    """Test the base extractor interface."""
    
    def test_abstract_methods(self):
        """Test that BaseExtractor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseExtractor("/fake/path")  # type: ignore
    
    def test_nonexistent_source(self):
        """Test that nonexistent source paths raise FileNotFoundError."""
        class TestExtractor(BaseExtractor):
            @property
            def platform(self) -> str:
                return "test"
            
            def validate_source(self) -> bool:
                return True
            
            def extract_messages(self):
                yield from []
        
        with pytest.raises(FileNotFoundError):
            TestExtractor("/nonexistent/path")


class TestPlatformDetection:
    """Test platform detection logic."""
    
    def test_detect_imessage(self):
        """Test iMessage detection."""
        assert detect_platform(Path("chat.db")) == "imessage"
        assert detect_platform(Path("sms.db")) == "imessage"
        assert detect_platform(Path("/path/to/chat.db")) == "imessage"
    
    def test_detect_instagram(self):
        """Test Instagram detection."""
        assert detect_platform(Path("instagram_messages.json")) == "instagram"
        assert detect_platform(Path("Instagram_Data.json")) == "instagram"
    
    def test_detect_whatsapp(self):
        """Test WhatsApp detection."""
        assert detect_platform(Path("WhatsApp_Chat.txt")) == "whatsapp"
        assert detect_platform(Path("whatsapp_export.txt")) == "whatsapp"
    
    def test_detect_generic_txt(self):
        """Test generic text file detection."""
        assert detect_platform(Path("conversation.txt")) == "txt"
        assert detect_platform(Path("chat_log.txt")) == "txt"
    
    def test_detect_unknown(self):
        """Test unknown file types."""
        assert detect_platform(Path("unknown.xyz")) is None
        assert detect_platform(Path("README.md")) is None


class TestIMessageExtractor:
    """Test iMessage extractor."""
    
    @patch('chatx.extractors.imessage.sqlite3')
    def test_validate_source_success(self, mock_sqlite):
        """Test successful source validation."""
        # Mock successful database connection and table check
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("message",), ("chat",), ("handle",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_sqlite.connect.return_value.__enter__.return_value = mock_conn
        
        # Create a temporary file to test with
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.suffix', '.db'):
            extractor = IMessageExtractor("fake_chat.db")
            assert extractor.validate_source() is True
    
    @patch('chatx.extractors.imessage.sqlite3')
    def test_validate_source_missing_tables(self, mock_sqlite):
        """Test source validation with missing tables."""
        # Mock database connection but missing required tables
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("message",)]  # Missing chat, handle
        mock_conn.cursor.return_value = mock_cursor
        mock_sqlite.connect.return_value.__enter__.return_value = mock_conn
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.suffix', '.db'):
            extractor = IMessageExtractor("fake_chat.db")
            assert extractor.validate_source() is False
    
    def test_validate_source_wrong_extension(self):
        """Test source validation with wrong file extension."""
        with patch('pathlib.Path.exists', return_value=True):
            extractor = IMessageExtractor("not_a_db.txt")
            assert extractor.validate_source() is False
    
    def test_platform_property(self):
        """Test platform property."""
        with patch('pathlib.Path.exists', return_value=True):
            extractor = IMessageExtractor("fake_chat.db")
            assert extractor.platform == "imessage"
    
    def test_apple_timestamp_conversion(self):
        """Test Apple timestamp conversion."""
        with patch('pathlib.Path.exists', return_value=True):
            extractor = IMessageExtractor("fake_chat.db")
            
            # Test None timestamp
            assert extractor._convert_apple_timestamp(None) is None
            
            # Test zero timestamp
            assert extractor._convert_apple_timestamp(0) is None
            
            # Test nanosecond timestamp (large number)
            # This is a rough test - exact conversion depends on implementation
            result = extractor._convert_apple_timestamp(1234567890000000000)
            assert result is not None
            
            # Test second timestamp (smaller number)
            result = extractor._convert_apple_timestamp(123456789)
            assert result is not None
