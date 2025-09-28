"""Integration tests for audio transcription with message extraction (PR-5)."""

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from chatx.imessage.extract import extract_messages
from chatx.imessage.transcribe import collect_transcription_stats


class TestTranscriptionIntegration:
    """Test audio transcription integration with message extraction."""
    
    @pytest.fixture
    def test_db_with_audio(self, tmp_path):
        """Create test database with audio attachments."""
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
        
        # Insert test messages with audio attachments
        conn.execute("""
            INSERT INTO message (ROWID, guid, text, is_from_me, handle_id, date) VALUES
            (1, 'msg-with-audio', '\\ufffc', 1, NULL, 1000),
            (2, 'msg-regular', 'Regular text message', 0, 1, 2000),
            (3, 'msg-with-multiple-audio', '\\ufffc\\ufffc', 0, 1, 3000)
        """)
        
        # Insert audio attachments
        conn.execute("""
            INSERT INTO attachment (ROWID, filename, uti, mime_type) VALUES
            (1, 'voice_message.m4a', 'com.apple.m4a-audio', 'audio/m4a'),
            (2, 'recording.caf', 'com.apple.coreaudio-format', 'audio/x-caf'),
            (3, 'song.mp3', 'public.mp3', 'audio/mp3')
        """)
        
        # Link attachments to messages
        conn.execute("INSERT INTO message_attachment_join VALUES (1, 1), (3, 2), (3, 3)")
        conn.execute("INSERT INTO chat_message_join VALUES (1, 1), (1, 2), (1, 3)")
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def test_extraction_without_transcription(self, test_db_with_audio, tmp_path):
        """Test that extraction works normally when transcription is disabled."""
        out_dir = tmp_path / "output"
        
        messages = list(extract_messages(
            db_path=test_db_with_audio,
            contact="+15551234567",
            include_attachments=True,
            copy_binaries=False,
            transcribe_audio="off",
            out_dir=out_dir,
        ))
        
        # Should have 3 messages
        assert len(messages) == 3
        
        # Find message with audio attachment
        audio_message = next((m for m in messages if m.msg_id == "msg_1"), None)
        assert audio_message is not None
        assert len(audio_message.attachments) == 1
        assert audio_message.attachments[0].filename == "voice_message.m4a"
        
        # Should not have transcripts in source_meta
        assert "transcripts" not in audio_message.source_meta
    
    @patch('chatx.imessage.transcribe.check_attachment_file_exists')
    def test_extraction_with_mock_transcription(self, mock_file_exists, test_db_with_audio, tmp_path):
        """Test extraction with mock transcription engine."""
        # Mock that files don't exist (will use mock transcription)
        mock_file_exists.return_value = False
        
        out_dir = tmp_path / "output"
        
        messages = list(extract_messages(
            db_path=test_db_with_audio,
            contact="+15551234567",
            include_attachments=True,
            copy_binaries=False,
            transcribe_audio="mock", 
            out_dir=out_dir,
        ))
        
        # Should have messages
        assert len(messages) == 3
        
        # Check transcription statistics
        stats = collect_transcription_stats(messages)
        # Note: Since files don't exist, no transcription should occur
        # This is the correct behavior for non-existent files
        assert stats["total_transcripts"] == 0
    
    def test_extraction_with_whisper_transcription(self, test_db_with_audio, tmp_path):
        """Test extraction with Whisper transcription."""
        # Create mock audio files
        attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
        attachments_dir.mkdir(parents=True)
        
        audio_files = ["voice_message.m4a", "recording.caf", "song.mp3"]
        for filename in audio_files:
            (attachments_dir / filename).write_bytes(b"fake audio content")
        
        # Mock Whisper
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {
            "text": "This is a transcribed voice message.",
            "segments": [{"no_speech_prob": 0.1}]
        }
        
        # Mock Path.home to point to our test directory
        with patch('pathlib.Path.home', return_value=tmp_path), \
             patch.dict('sys.modules', {'whisper': mock_whisper}):
            out_dir = tmp_path / "output"
            
            messages = list(extract_messages(
                db_path=test_db_with_audio,
                contact="+15551234567",
                include_attachments=True,
                copy_binaries=False,
                transcribe_audio="local",
                out_dir=out_dir,
            ))
        
        # Should have messages
        assert len(messages) == 3
        
        # Check that transcription occurred
        stats = collect_transcription_stats(messages)
        assert stats["total_transcripts"] == 3  # 3 audio attachments
        assert stats["by_engine"]["whisper-base"] == 3
        assert stats["by_confidence"]["high"] == 3
        
        # Verify transcript data in source_meta
        audio_messages = [m for m in messages if "transcripts" in m.source_meta]
        assert len(audio_messages) == 2  # 2 messages have audio attachments
        
        # Check individual transcripts
        for message in audio_messages:
            assert "transcripts" in message.source_meta
            for transcript in message.source_meta["transcripts"]:
                assert transcript["transcript"] == "This is a transcribed voice message."
                assert transcript["engine"] == "whisper-base"
                assert transcript["confidence"] == "high"
                assert transcript["filename"] in audio_files
    
    def test_extraction_with_copy_binaries_and_transcription(self, test_db_with_audio, tmp_path):
        """Test extraction when copying binaries and transcribing."""
        # Create mock audio files in Messages directory
        messages_dir = tmp_path / "Library" / "Messages" / "Attachments"
        messages_dir.mkdir(parents=True)
        
        audio_file = messages_dir / "voice_message.m4a"
        audio_file.write_bytes(b"fake audio content")
        
        # Mock Whisper
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {
            "text": "Transcribed from copied file.",
            "segments": [{"no_speech_prob": 0.3}]
        }
        
        with patch('pathlib.Path.home', return_value=tmp_path), \
             patch.dict('sys.modules', {'whisper': mock_whisper}):
            out_dir = tmp_path / "output"
            
            messages = list(extract_messages(
                db_path=test_db_with_audio,
                contact="+15551234567", 
                include_attachments=True,
                copy_binaries=True,
                transcribe_audio="local",
                out_dir=out_dir,
            ))
        
        # Should have messages
        assert len(messages) == 3
        
        # Find message with copied audio file
        audio_message = next((m for m in messages if m.msg_id == "msg_1"), None)
        assert audio_message is not None
        
        # Should have attachment with copied abs_path
        attachment = audio_message.attachments[0]
        assert attachment.abs_path is not None
        assert Path(attachment.abs_path).exists()
        
        # Should have transcript
        assert "transcripts" in audio_message.source_meta
        transcript = audio_message.source_meta["transcripts"][0]
        assert transcript["transcript"] == "Transcribed from copied file."
        assert transcript["confidence"] == "medium"  # 0.3 -> 0.7 confidence -> medium
    
    def test_extraction_handles_transcription_failures(self, test_db_with_audio, tmp_path):
        """Test that transcription failures don't break extraction."""
        # Don't create audio files - this will cause transcription to fail gracefully
        
        out_dir = tmp_path / "output"
        
        # Should not raise any exceptions
        messages = list(extract_messages(
            db_path=test_db_with_audio,
            contact="+15551234567",
            include_attachments=True, 
            copy_binaries=False,
            transcribe_audio="local",
            out_dir=out_dir,
        ))
        
        # Should still extract messages successfully
        assert len(messages) == 3
        
        # Should not have any transcripts (files don't exist)
        stats = collect_transcription_stats(messages)
        assert stats["total_transcripts"] == 0
    
    def test_extraction_mixed_audio_and_non_audio_attachments(self, test_db_with_audio, tmp_path):
        """Test extraction with mixed audio and non-audio attachments."""
        # Add non-audio attachment to database
        conn = sqlite3.connect(test_db_with_audio)
        
        # Add an image attachment
        conn.execute("""
            INSERT INTO attachment (ROWID, filename, uti, mime_type) VALUES
            (4, 'photo.jpg', 'public.jpeg', 'image/jpeg')
        """)
        
        # Link to a message
        conn.execute("INSERT INTO message_attachment_join VALUES (2, 4)")
        conn.commit()
        conn.close()
        
        # Create only audio files
        attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
        attachments_dir.mkdir(parents=True)
        (attachments_dir / "voice_message.m4a").write_bytes(b"audio")
        # Note: Don't create photo.jpg - it's not audio anyway
        
        # Mock Whisper for audio files only
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {
            "text": "Audio only transcription.",
            "segments": []
        }
        
        with patch('pathlib.Path.home', return_value=tmp_path), \
             patch.dict('sys.modules', {'whisper': mock_whisper}):
            out_dir = tmp_path / "output"
            
            messages = list(extract_messages(
                db_path=test_db_with_audio,
                contact="+15551234567",
                include_attachments=True,
                copy_binaries=False, 
                transcribe_audio="local",
                out_dir=out_dir,
            ))
        
        # Should have all messages
        assert len(messages) == 3
        
        # Should only transcribe audio attachments
        stats = collect_transcription_stats(messages)
        assert stats["total_transcripts"] == 1  # Only 1 audio file exists
        
        # Verify that non-audio attachments are not transcribed
        regular_message = next((m for m in messages if m.msg_id == "msg_2"), None)
        assert regular_message is not None
        assert len(regular_message.attachments) == 1
        assert regular_message.attachments[0].filename == "photo.jpg"
        assert "transcripts" not in regular_message.source_meta
