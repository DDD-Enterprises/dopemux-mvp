"""ChatX - Privacy-focused, local-first CLI tool for forensic chat analysis.

This package provides tools to:
- Extract chat data from multiple platforms (iMessage, Instagram, WhatsApp, TXT files)
- Transform messages into canonical JSON formats
- Redact sensitive information using Policy Shield
- Enrich messages with LLM-generated metadata
- Index conversations in local vector databases
- Analyze chat patterns with privacy-by-default principles
"""

__version__ = "0.1.0"
__author__ = "Dopemux-ChatRipperXX Contributors"
__email__ = ""
__license__ = "MIT"

from chatx.schemas.enrichment import EnrichmentMessage
from chatx.schemas.message import CanonicalMessage

__all__ = ["CanonicalMessage", "EnrichmentMessage"]
