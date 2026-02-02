"""
Session ID Generator - F002 Component 1

Generates unique, collision-resistant session IDs for multi-session support.
Uses transcript-based naming with millisecond timestamps for uniqueness.

Part of F002: Multi-Session Support
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class SessionIDGenerator:
    """
    Generate unique session IDs for multi-session tracking.

    Strategy: Transcript-based with timestamp suffix
    Format: session_{transcript_id}_{timestamp_ms}
    Fallback: session_{uuid}_{timestamp_ms}

    ADHD Benefit: Human-readable session IDs aid memory and debugging
    """

    @staticmethod
    def generate(transcript_path: Optional[str] = None) -> str:
        """
        Generate unique collision-resistant session ID.

        Args:
            transcript_path: Path to Claude Code transcript directory (optional)

        Returns:
            session_abc123_1729367895123 (transcript-based)
            or session_a1b2c3d4e5f6_1729367895123 (UUID fallback)

        Collision Resistance:
            - Millisecond timestamp ensures temporal uniqueness
            - Even simultaneous starts differ by milliseconds
            - UUID fallback for non-transcript environments
        """
        timestamp_ms = int(datetime.now().timestamp() * 1000)

        # Try transcript-based ID first
        if transcript_path:
            try:
                transcript_id = SessionIDGenerator._extract_transcript_id(transcript_path)
                if transcript_id:
                    session_id = f"session_{transcript_id}_{timestamp_ms}"
                    logger.debug(f"Generated transcript-based session ID: {session_id}")
                    return session_id
            except Exception as e:
                logger.debug(f"Transcript ID extraction failed: {e}, using UUID fallback")

        # Fallback to UUID
        uuid_short = uuid.uuid4().hex[:12]
        session_id = f"session_{uuid_short}_{timestamp_ms}"
        logger.debug(f"Generated UUID-based session ID: {session_id}")
        return session_id

    @staticmethod
    def _extract_transcript_id(transcript_path: str) -> Optional[str]:
        """
        Extract transcript ID from Claude Code transcript path.

        Claude Code transcript structure:
        ~/.claude/transcripts/{session_id}/transcript.jsonl

        Args:
            transcript_path: Path to transcript file or directory

        Returns:
            Extracted session ID or None
        """
        try:
            path = Path(transcript_path).resolve()

            # If it's a file, get parent directory name
            if path.is_file():
                transcript_id = path.parent.name
            else:
                # If it's already a directory, use its name
                transcript_id = path.name

            # Validate it looks like a session ID (alphanumeric)
            if transcript_id and transcript_id.replace('_', '').replace('-', '').isalnum():
                return transcript_id

            logger.debug(f"Invalid transcript ID format: {transcript_id}")
            return None

        except Exception as e:
            logger.debug(f"Transcript path extraction failed: {e}")
            return None

    @staticmethod
    def detect_transcript_path() -> Optional[str]:
        """
        Auto-detect Claude Code transcript path from environment.

        Tries (in order):
        1. CLAUDE_TRANSCRIPT_PATH environment variable
        2. CLAUDE_SESSION_ID environment variable
        3. Current working directory check (if in .claude/transcripts/)

        Returns:
            Transcript path or None
        """
        # Try environment variable
        transcript_path = os.environ.get('CLAUDE_TRANSCRIPT_PATH')
        if transcript_path and Path(transcript_path).exists():
            return transcript_path

        # Try session ID environment variable
        session_id_env = os.environ.get('CLAUDE_SESSION_ID')
        if session_id_env:
            # Assume standard .claude/transcripts structure
            claude_home = Path.home() / '.claude' / 'transcripts' / session_id_env
            if claude_home.exists():
                return str(claude_home)

        # Try detecting from current working directory
        cwd = Path.cwd()
        if '.claude' in cwd.parts and 'transcripts' in cwd.parts:
            # Find the transcript session directory
            for i, part in enumerate(cwd.parts):
                if part == 'transcripts' and i + 1 < len(cwd.parts):
                    transcript_id = cwd.parts[i + 1]
                    transcript_dir = Path(*cwd.parts[:i+2])
                    if transcript_dir.exists():
                        return str(transcript_dir)

        logger.debug("Could not auto-detect transcript path")
        return None

    @staticmethod
    def generate_auto() -> str:
        """
        Generate session ID with automatic transcript detection.

        Convenience method that auto-detects transcript path.

        Returns:
            Unique session ID
        """
        transcript_path = SessionIDGenerator.detect_transcript_path()
        return SessionIDGenerator.generate(transcript_path)

    @staticmethod
    def parse_session_id(session_id: str) -> dict:
        """
        Parse session ID into components.

        Args:
            session_id: Session ID string

        Returns:
            {
                "prefix": "session",
                "identifier": "abc123" or uuid,
                "timestamp_ms": 1729367895123,
                "datetime": datetime object,
                "type": "transcript" or "uuid"
            }
        """
        try:
            parts = session_id.split('_')
            if len(parts) != 3 or parts[0] != 'session':
                logger.warning(f"Invalid session ID format: {session_id}")
                return {}

            identifier = parts[1]
            timestamp_ms = int(parts[2])
            timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000.0)

            # Determine type (transcript IDs are shorter, UUIDs are 12 chars)
            session_type = "transcript" if len(identifier) < 12 else "uuid"

            return {
                "prefix": "session",
                "identifier": identifier,
                "timestamp_ms": timestamp_ms,
                "datetime": timestamp_dt,
                "type": session_type
            }

        except Exception as e:
            logger.error(f"Failed to parse session ID {session_id}: {e}")
            return {}
