"""Tests for audio transcription functionality (PR-5)."""

import sys
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from chatx.imessage.transcribe import (
    transcribe_local,
    is_audio_attachment, 
    is_audio_file,
    collect_transcription_stats,
    get_transcription_summary,
    VOICE_MESSAGE_EXTENSIONS,
    AUDIO_MIME_TYPES,
    AUDIO_UTIS
)


class TestTranscribeLocal:
    """Test local audio transcription."""
    
    def test_transcribe_local_mock_engine(self, tmp_path):
        """Test mock transcription engine."""
        # Create dummy audio file
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")
        
        result = transcribe_local(audio_file, engine="mock")
        
        assert result is not None
        assert result["transcript"] == "[MOCK TRANSCRIPT] Audio from test.m4a"
        assert result["engine"] == "mock"
        assert result["confidence"] == "mock"
    
    def test_transcribe_local_nonexistent_file(self, tmp_path):
        """Test with non-existent file."""
        audio_file = tmp_path / "nonexistent.m4a"
        
        result = transcribe_local(audio_file, engine="mock")
        
        assert result is None
    
    def test_transcribe_local_non_audio_file(self, tmp_path):
        """Test with non-audio file."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("not audio")
        
        result = transcribe_local(text_file, engine="mock")
        
        assert result is None
    
    def test_transcribe_local_whisper_success(self, tmp_path):
        """Test successful Whisper transcription."""
        # Mock Whisper module at import time
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcription result
        mock_model.transcribe.return_value = {
            "text": "Hello, this is a test voice message.",
            "segments": [
                {"no_speech_prob": 0.1},  # High confidence (low no_speech_prob)
                {"no_speech_prob": 0.2}
            ]
        }
        
        # Create dummy audio file
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")
        
        with patch.dict('sys.modules', {'whisper': mock_whisper}):
            result = transcribe_local(audio_file, engine="whisper")
        
        assert result is not None
        assert result["transcript"] == "Hello, this is a test voice message."
        assert result["engine"] == "whisper-base"
        assert result["confidence"] == "high"  # Average no_speech_prob: 0.15, confidence: 0.85 > 0.8
        
        mock_whisper.load_model.assert_called_once_with("base")
        mock_model.transcribe.assert_called_once_with(str(audio_file))
    
    def test_transcribe_local_whisper_medium_confidence(self, tmp_path):
        """Test Whisper transcription with medium confidence."""
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        mock_model.transcribe.return_value = {
            "text": "Unclear audio message.",
            "segments": [
                {"no_speech_prob": 0.4},
                {"no_speech_prob": 0.3}
            ]
        }
        
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")
        
        with patch.dict('sys.modules', {'whisper': mock_whisper}):
            result = transcribe_local(audio_file, engine="whisper")
        
        assert result["confidence"] == "medium"  # Average: 0.35, confidence: 0.65 (0.5 < x <= 0.8)
    
    def test_transcribe_local_whisper_low_confidence(self, tmp_path):
        """Test Whisper transcription with low confidence."""
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        mock_model.transcribe.return_value = {
            "text": "Very unclear.",
            "segments": [
                {"no_speech_prob": 0.8},
                {"no_speech_prob": 0.9}
            ]
        }
        
        audio_file = tmp_path / "test.caf"
        audio_file.write_bytes(b"fake audio")
        
        with patch.dict('sys.modules', {'whisper': mock_whisper}):
            result = transcribe_local(audio_file, engine="whisper")
        
        assert result["confidence"] == "low"  # Average: 0.85, confidence: 0.15 <= 0.5
    
    def test_transcribe_local_whisper_no_segments(self, tmp_path):
        """Test Whisper transcription with no segments."""
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        mock_model.transcribe.return_value = {
            "text": "Short message.",
            "segments": []
        }
        
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")
        
        with patch.dict('sys.modules', {'whisper': mock_whisper}):
            result = transcribe_local(audio_file, engine="whisper")
        
        assert result["confidence"] == "unknown"
    
    def test_transcribe_local_whisper_empty_text(self, tmp_path):
        """Test Whisper with empty transcript."""
        mock_whisper = Mock()
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        mock_model.transcribe.return_value = {
            "text": "   ",  # Only whitespace
            "segments": []
        }
        
        audio_file = tmp_path / "test.aac"
        audio_file.write_bytes(b"fake audio")
        
        with patch.dict('sys.modules', {'whisper': mock_whisper}):
            result = transcribe_local(audio_file, engine="whisper")
        
        assert result is None
    
    def test_transcribe_local_whisper_import_error(self, tmp_path):
        """Test behavior when Whisper is not available."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio")
        
        # Simulate whisper not being installed
        with patch.dict('sys.modules', {}, clear=False):
            if 'whisper' in sys.modules:
                del sys.modules['whisper']
            result = transcribe_local(audio_file, engine="whisper")
            
        assert result is None
    
    def test_transcribe_local_whisper_exception(self, tmp_path):
        """Test behavior when Whisper throws an exception."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio")
        
        mock_whisper = Mock()
        mock_whisper.load_model.side_effect = RuntimeError("Whisper error")
        
        with patch.dict('sys.modules', {'whisper': mock_whisper}):
            result = transcribe_local(audio_file, engine="whisper")
            
        assert result is None
    
    def test_transcribe_local_unknown_engine(self, tmp_path):
        """Test with unknown engine falls back to mock."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio")
        
        result = transcribe_local(audio_file, engine="unknown_engine")
        
        assert result is not None
        assert result["engine"] == "mock"


class TestAudioDetection:
    """Test audio file and attachment detection."""
    
    def test_is_audio_attachment_by_mime_type(self):
        """Test audio detection by MIME type."""
        assert is_audio_attachment("audio/mp3", None, None)
        assert is_audio_attachment("audio/m4a", None, None)
        assert is_audio_attachment("audio/wav", None, None)
        assert not is_audio_attachment("image/jpeg", None, None)
        assert not is_audio_attachment("text/plain", None, None)
    
    def test_is_audio_attachment_by_uti(self):
        """Test audio detection by UTI."""
        assert is_audio_attachment(None, "public.audio", None)
        assert is_audio_attachment(None, "public.mp3", None)
        assert is_audio_attachment(None, "com.apple.m4a-audio", None)
        assert not is_audio_attachment(None, "public.jpeg", None)
        assert not is_audio_attachment(None, "public.plain-text", None)
    
    def test_is_audio_attachment_by_filename(self):
        """Test audio detection by filename extension."""
        assert is_audio_attachment(None, None, "voice.m4a")
        assert is_audio_attachment(None, None, "recording.wav")
        assert is_audio_attachment(None, None, "song.mp3")
        assert is_audio_attachment(None, None, "message.caf")
        assert not is_audio_attachment(None, None, "photo.jpg")
        assert not is_audio_attachment(None, None, "document.pdf")
    
    def test_is_audio_attachment_priority(self):
        """Test that MIME type takes priority over other indicators."""
        # MIME type indicates audio, others don't - should be True
        assert is_audio_attachment("audio/mp3", "public.jpeg", "document.pdf")
        
        # MIME type doesn't indicate audio, but UTI does - should be True
        assert is_audio_attachment("text/plain", "public.audio", "document.pdf")
        
        # Only filename indicates audio - should be True
        assert is_audio_attachment("text/plain", "public.plain-text", "voice.m4a")
    
    def test_is_audio_attachment_none_values(self):
        """Test with None values."""
        assert not is_audio_attachment(None, None, None)
        assert not is_audio_attachment("", "", "")
    
    def test_is_audio_file(self, tmp_path):
        """Test file-based audio detection."""
        # Audio files
        audio_file = tmp_path / "test.m4a"
        assert is_audio_file(audio_file)
        
        wav_file = tmp_path / "recording.wav"
        assert is_audio_file(wav_file)
        
        # Non-audio files
        image_file = tmp_path / "photo.jpg"
        assert not is_audio_file(image_file)
        
        text_file = tmp_path / "readme.txt"
        assert not is_audio_file(text_file)
    
    def test_voice_message_extensions_completeness(self):
        """Test that we support common voice message extensions."""
        expected_extensions = {'.m4a', '.caf', '.mp3', '.wav', '.aac', '.opus'}
        assert VOICE_MESSAGE_EXTENSIONS == expected_extensions
    
    def test_audio_mime_types_completeness(self):
        """Test audio MIME type coverage."""
        expected_types = {
            'audio/mp3', 'audio/mpeg', 'audio/mp4', 'audio/m4a',
            'audio/wav', 'audio/aiff', 'audio/x-caf'
        }
        assert AUDIO_MIME_TYPES == expected_types
    
    def test_audio_utis_completeness(self):
        """Test audio UTI coverage."""
        expected_utis = {
            'public.audio', 'public.mp3', 'public.mpeg-4-audio',
            'com.apple.coreaudio-format', 'public.aiff-audio',
            'public.wav', 'com.apple.m4a-audio'
        }
        assert AUDIO_UTIS == expected_utis


class TestTranscriptionStats:
    """Test transcription statistics collection."""
    
    def test_collect_transcription_stats_empty(self):
        """Test with no messages."""
        stats = collect_transcription_stats([])
        
        assert stats["total_transcripts"] == 0
        assert stats["by_engine"] == {}
        assert all(count == 0 for count in stats["by_confidence"].values())
    
    def test_collect_transcription_stats_no_transcripts(self):
        """Test with messages but no transcripts."""
        # Mock messages without transcripts
        messages = [
            Mock(source_meta={}),
            Mock(source_meta={"other_data": "value"})
        ]
        
        stats = collect_transcription_stats(messages)
        
        assert stats["total_transcripts"] == 0
    
    def test_collect_transcription_stats_with_transcripts(self):
        """Test with various transcripts."""
        messages = [
            Mock(source_meta={
                "transcripts": [
                    {
                        "filename": "voice1.m4a",
                        "transcript": "Hello world",
                        "engine": "whisper-base",
                        "confidence": "high"
                    },
                    {
                        "filename": "voice2.m4a", 
                        "transcript": "Another message",
                        "engine": "whisper-base",
                        "confidence": "medium"
                    }
                ]
            }),
            Mock(source_meta={
                "transcripts": [
                    {
                        "filename": "voice3.m4a",
                        "transcript": "Mock transcript",
                        "engine": "mock",
                        "confidence": "mock"
                    }
                ]
            }),
            Mock(source_meta={})  # No transcripts
        ]
        
        stats = collect_transcription_stats(messages)
        
        assert stats["total_transcripts"] == 3
        assert stats["by_engine"] == {"whisper-base": 2, "mock": 1}
        assert stats["by_confidence"]["high"] == 1
        assert stats["by_confidence"]["medium"] == 1 
        assert stats["by_confidence"]["mock"] == 1
        assert stats["by_confidence"]["low"] == 0
    
    def test_get_transcription_summary(self):
        """Test transcription summary generation."""
        summary = get_transcription_summary(
            attachments_with_transcripts=5,
            failed_transcriptions=2
        )
        
        expected = {
            "total_audio_attachments": 7,
            "successful_transcriptions": 5,
            "failed_transcriptions": 2,
            "success_rate": (5/7) * 100
        }
        
        assert summary == expected
    
    def test_get_transcription_summary_no_failures(self):
        """Test summary with no failures."""
        summary = get_transcription_summary(
            attachments_with_transcripts=3,
            failed_transcriptions=0
        )
        
        assert summary["success_rate"] == 100.0
    
    def test_get_transcription_summary_all_failures(self):
        """Test summary with all failures."""
        summary = get_transcription_summary(
            attachments_with_transcripts=0,
            failed_transcriptions=5
        )
        
        assert summary["success_rate"] == 0.0
    
    def test_get_transcription_summary_zero_division_protection(self):
        """Test summary with zero attachments."""
        summary = get_transcription_summary(
            attachments_with_transcripts=0,
            failed_transcriptions=0
        )
        
        assert summary["success_rate"] == 0.0  # Protected by max(1, ...)