"""
Promotion Engine - Redaction and event promotion for Dope-Memory.

Implements:
- Dual redaction pass (ingest + promotion)
- Denylist path hashing
- Regex secret scrubbing
- Deterministic promotion rules
"""

__all__ = ["Redactor", "PromotionEngine"]

from .redactor import Redactor
from .promotion import PromotionEngine
