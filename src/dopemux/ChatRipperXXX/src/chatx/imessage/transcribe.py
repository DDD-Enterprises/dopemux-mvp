"""Local-only audio transcription for voice notes."""

import tempfile
from pathlib import Path
from typing import Dict, Optional

# Audio file extensions that commonly contain voice messages
VOICE_MESSAGE_EXTENSIONS = {'.m4a', '.caf', '.mp3', '.wav', '.aac', '.opus'}

# Audio UTIs that indicate voice messages or audio content
AUDIO_UTIS = {
    'public.audio',
    'public.mp3', 
    'public.mpeg-4-audio',
    'com.apple.coreaudio-format',
    'public.aiff-audio',
    'public.wav',
    'com.apple.m4a-audio'
}

# Audio MIME types
AUDIO_MIME_TYPES = {
    'audio/mp3',
    'audio/mpeg',
    'audio/mp4',
    'audio/m4a',
    'audio/wav',
    'audio/aiff',
    'audio/x-caf'
}


def transcribe_local(audio_file_path: Path, engine: str = "whisper") -> Optional[Dict[str, str]]:
    """Transcribe audio file using local transcription engine.
    
    Args:
        audio_file_path: Path to audio file to transcribe
        engine: Transcription engine to use ("whisper" or "mock")
        
    Returns:
        Dictionary with transcript and metadata, None if failed
        Format: {"transcript": "text", "engine": "whisper", "confidence": "high"}
        
    Note:
        Uses local-only transcription engines. Never sends data to cloud services.
        Supports deterministic mock mode for testing.
    """
    if not audio_file_path.exists():
        return None
    
    # For mock engine and CLI calls, enforce a conservative extension check.
    # Whisper path can handle more formats and hashed filenames when upstream marked audio.
    if engine == "mock":
        if not is_audio_file(audio_file_path):
            return None
        return _transcribe_mock(audio_file_path)
    elif engine == "whisper":
        # Prefer faster-whisper plugin when available, fall back to classic
        try:
            from chatx.transcribe.local_whisper import transcribe as fw_transcribe
            out = fw_transcribe(audio_file_path)
            if out:
                return out
        except ImportError:
            pass
        return _transcribe_whisper(audio_file_path)
    else:
        # Unknown engine, fall back to mock
        return _transcribe_mock(audio_file_path)


def _transcribe_mock(audio_file_path: Path) -> Dict[str, str]:
    """Mock transcription for testing purposes."""
    return {
        "transcript": f"[MOCK TRANSCRIPT] Audio from {audio_file_path.name}",
        "engine": "mock",
        "confidence": "mock"
    }


def _transcribe_whisper(audio_file_path: Path) -> Optional[Dict[str, str]]:
    """Transcribe using OpenAI Whisper (local inference only).
    
    Returns:
        Transcript dictionary or None if transcription failed
    """
    try:
        import whisper
        
        # Load the smallest Whisper model for speed (can be made configurable)
        # base model is a good balance of speed vs accuracy for voice messages
        model = whisper.load_model("base")
        
        # Transcribe the audio file
        # Whisper handles many audio formats automatically
        result = model.transcribe(str(audio_file_path))
        
        # Extract transcript text
        transcript_text = result.get("text", "").strip()
        
        if not transcript_text:
            return None
        
        # Estimate confidence based on average segment confidence
        segments = result.get("segments", [])
        if segments:
            # Calculate average confidence from segments that have it
            confidences = [seg.get("no_speech_prob", 0.5) for seg in segments if "no_speech_prob" in seg]
            if confidences:
                # Convert no_speech_prob to confidence (invert and normalize)
                avg_no_speech = sum(confidences) / len(confidences)
                confidence_score = 1.0 - avg_no_speech
                
                if confidence_score > 0.8:
                    confidence = "high"
                elif confidence_score > 0.5:
                    confidence = "medium"
                else:
                    confidence = "low"
            else:
                confidence = "unknown"
        else:
            confidence = "unknown"
        
        return {
            "transcript": transcript_text,
            "engine": "whisper-base",
            "confidence": confidence
        }
        
    except ImportError:
        # Whisper not available, return None
        return None
    except Exception:
        # Transcription failed for some reason
        # Log error but don't raise exception (graceful degradation)
        return None


def is_audio_attachment(mime_type: Optional[str], uti: Optional[str], filename: Optional[str] = None) -> bool:
    """Check if attachment is an audio file suitable for transcription.
    
    Args:
        mime_type: MIME type from attachment metadata
        uti: Uniform Type Identifier from attachment metadata
        filename: Optional filename for extension-based detection
        
    Returns:
        True if attachment appears to be audio suitable for transcription
    """
    # Check MIME type first
    if mime_type and mime_type in AUDIO_MIME_TYPES:
        return True
        
    # Check UTI
    if uti and uti in AUDIO_UTIS:
        return True
    
    # Check filename extension as fallback
    if filename:
        extension = Path(filename).suffix.lower()
        if extension in VOICE_MESSAGE_EXTENSIONS:
            return True
        
    return False


def is_audio_file(file_path: Path) -> bool:
    """Check if file is likely an audio file based on extension.
    
    Args:
        file_path: Path to file to check
        
    Returns:
        True if file extension indicates audio content
    """
    extension = file_path.suffix.lower()
    return extension in VOICE_MESSAGE_EXTENSIONS


def check_attachment_file_exists(filename: Optional[str]) -> bool:
    """Check if an attachment file exists in common iMessage locations.

    This mirrors the logic used by the missing-attachments report, but is
    defined here to avoid circular imports during extraction/transcription.

    Args:
        filename: Attachment filename

    Returns:
        True if a plausible attachment path exists on disk.
    """
    if not filename:
        return False

    attachments_dir = Path.home() / "Library" / "Messages" / "Attachments"
    potential_paths = [
        attachments_dir / filename,
        attachments_dir / "Attachments" / filename,
        Path(filename),
    ]

    for path in potential_paths:
        if path.exists():
            return True

    return False


def get_transcription_summary(attachments_with_transcripts: int, failed_transcriptions: int) -> Dict[str, int]:
    """Generate summary statistics for transcription process.
    
    Args:
        attachments_with_transcripts: Number of attachments successfully transcribed
        failed_transcriptions: Number of transcription failures
        
    Returns:
        Dictionary with transcription statistics
    """
    return {
        "total_audio_attachments": attachments_with_transcripts + failed_transcriptions,
        "successful_transcriptions": attachments_with_transcripts,
        "failed_transcriptions": failed_transcriptions,
        "success_rate": (attachments_with_transcripts / max(1, attachments_with_transcripts + failed_transcriptions)) * 100
    }


def collect_transcription_stats(messages) -> Dict[str, int]:
    """Collect transcription statistics from extracted messages.
    
    Args:
        messages: List of CanonicalMessage objects
        
    Returns:
        Dictionary with transcription statistics
    """
    total_transcripts = 0
    engine_counts = {}
    confidence_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0, "mock": 0}
    
    for message in messages:
        if "transcripts" in message.source_meta:
            for transcript in message.source_meta["transcripts"]:
                total_transcripts += 1
                
                # Count by engine
                engine = transcript.get("engine", "unknown")
                engine_counts[engine] = engine_counts.get(engine, 0) + 1
                
                # Count by confidence
                confidence = transcript.get("confidence", "unknown")
                if confidence in confidence_counts:
                    confidence_counts[confidence] += 1
    
    return {
        "total_transcripts": total_transcripts,
        "by_engine": engine_counts,
        "by_confidence": confidence_counts
    }
