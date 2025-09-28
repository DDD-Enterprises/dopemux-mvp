"""Platform-specific chat data extractors."""

from chatx.extractors.base import BaseExtractor
from chatx.extractors.imessage import IMessageExtractor

__all__ = [
    "BaseExtractor",
    "IMessageExtractor",
]
