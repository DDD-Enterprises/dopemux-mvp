"""iMessage extraction module.

This module provides functionality to extract iMessage conversations from macOS
chat.db files with full fidelity including replies, reactions, attachments, and
voice note transcription.

Safety & Privacy:
- Local-first operation only
- Attachments never uploaded to cloud
- Transcription only performed locally when opt-in
- Full Disk Access required for macOS Messages database access
"""

__version__ = "0.1.0"

from chatx.imessage.extract import extract_messages

__all__ = ["extract_messages"]