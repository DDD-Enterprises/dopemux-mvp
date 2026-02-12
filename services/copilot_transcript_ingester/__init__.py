"""
Copilot CLI Transcript Ingester

Parses JSONL event logs from ~/.copilot/session-state/{SESSION_ID}/events.jsonl
and ingests them into Dope-Memory Chronicle (raw_activity_events table).

Strategy A: Transcript Ingestion (no hooks, stable JSONL format)
"""

__version__ = "0.1.0"
__author__ = "Dopemux"

from .parser import JSONLParser
from .mapper import EventTypeMapper
from .ingester import ChronicleIngester

__all__ = ["JSONLParser", "EventTypeMapper", "ChronicleIngester"]
