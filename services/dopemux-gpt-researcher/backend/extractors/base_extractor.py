"""
Base extractor class providing common functionality for all field extractors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import re
import spacy
from spacy.lang.en import English

@dataclass
class ExtractedField:
    """Represents a single extracted field with metadata."""

    field_type: str  # e.g., "decision", "feature", "research"
    content: str     # The extracted content
    confidence: float = 0.0  # 0.0 to 1.0
    context: str = ""  # Surrounding context
    source_chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    stakeholders: List[str] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Handle timestamp properly - could be datetime or string
        timestamp_str = None
        if self.timestamp:
            if isinstance(self.timestamp, str):
                timestamp_str = self.timestamp
            else:
                timestamp_str = self.timestamp.isoformat()

        return {
            'field_type': self.field_type,
            'content': self.content,
            'confidence': self.confidence,
            'context': self.context,
            'source_chunk_id': self.source_chunk_id,
            'metadata': self.metadata,
            'timestamp': timestamp_str,
            'stakeholders': self.stakeholders,
            'relationships': self.relationships
        }


class BaseExtractor(ABC):
    """
    Abstract base class for all field extractors.

    Provides common functionality including:
    - spaCy NLP processing
    - Pattern matching utilities
    - Confidence scoring
    - Context preservation
    """

    def __init__(self, nlp_model: str = "en_core_web_sm"):
        """Initialize the extractor with spaCy model."""
        try:
            self.nlp = spacy.load(nlp_model)
        except OSError:
            # Fallback to basic English model
            self.nlp = English()

        self.patterns = self._define_patterns()
        self.keywords = self._define_keywords()

    @abstractmethod
    def _define_patterns(self) -> List[str]:
        """Define regex patterns specific to this extractor."""
        pass

    @abstractmethod
    def _define_keywords(self) -> List[str]:
        """Define keywords that indicate relevant content."""
        pass

    @abstractmethod
    def extract_from_chunk(self, chunk: Dict[str, Any]) -> List[ExtractedField]:
        """Extract fields from a single conversation chunk."""
        pass

    def extract_from_chunks(self, chunks: List[Dict[str, Any]]) -> List[ExtractedField]:
        """Extract fields from multiple chunks."""
        all_fields = []
        for chunk in chunks:
            fields = self.extract_from_chunk(chunk)
            all_fields.extend(fields)
        return all_fields

    def _calculate_confidence(self, text: str, matches: List[str], context: str = "") -> float:
        """
        Calculate confidence score based on pattern matches and context.

        Args:
            text: The extracted text
            matches: List of patterns/keywords that matched
            context: Surrounding context

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not matches:
            return 0.0

        # Base confidence from number of matches
        base_confidence = min(len(matches) * 0.2, 0.8)

        # Boost for strong indicators
        strong_indicators = [
            r'\b(decided?|decision|conclude[ds]?)\b',
            r'\b(will|should|must|need to)\b',
            r'\b(requirement|spec|feature)\b',
            r'\b(risk|concern|issue)\b',
            r'\b(security|compliance|policy)\b'
        ]

        for pattern in strong_indicators:
            if re.search(pattern, text.lower()):
                base_confidence += 0.1

        # Text length adjustment (very short extracts are less reliable)
        if len(text.split()) < 3:
            base_confidence *= 0.7
        elif len(text.split()) > 20:
            base_confidence *= 1.1

        return min(base_confidence, 1.0)

    def _extract_context(self, full_text: str, match_start: int, match_end: int,
                        window_size: int = 100) -> str:
        """Extract surrounding context around a match."""
        start = max(0, match_start - window_size)
        end = min(len(full_text), match_end + window_size)
        return full_text[start:end].strip()

    def _extract_stakeholders(self, text: str) -> List[str]:
        """Extract stakeholder names from text using NLP."""
        doc = self.nlp(text)
        stakeholders = []

        # Extract person names
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG"]:
                stakeholders.append(ent.text)

        # Extract pronouns and role indicators
        role_patterns = [
            r'\b(team|developer|designer|manager|user|customer|client)\b',
            r'\b(we|us|they|them|he|she|him|her)\b',
            r'\b(@\w+)\b',  # mentions
        ]

        for pattern in role_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                stakeholders.append(match.group())

        return list(set(stakeholders))  # Remove duplicates

    def _find_pattern_matches(self, text: str) -> List[Dict[str, Any]]:
        """Find all pattern matches in text with positions."""
        matches = []

        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                matches.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'groups': match.groups()
                })

        return matches

    def _find_keyword_matches(self, text: str) -> List[str]:
        """Find keyword matches in text."""
        text_lower = text.lower()
        found_keywords = []

        for keyword in self.keywords:
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                found_keywords.append(keyword)

        return found_keywords

    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Fix common chat artifacts
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s*\[.*?\]\s*', ' ', text)  # Remove timestamps/metadata

        return text.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy."""
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 5]

    def get_extraction_summary(self, fields: List[ExtractedField]) -> Dict[str, Any]:
        """Generate summary statistics for extracted fields."""
        if not fields:
            return {
                'total_fields': 0,
                'avg_confidence': 0.0,
                'field_types': {},
                'stakeholder_count': 0
            }

        total_fields = len(fields)
        avg_confidence = sum(f.confidence for f in fields) / total_fields

        field_types = {}
        all_stakeholders = set()

        for field in fields:
            field_type = field.field_type
            field_types[field_type] = field_types.get(field_type, 0) + 1
            all_stakeholders.update(field.stakeholders)

        return {
            'total_fields': total_fields,
            'avg_confidence': round(avg_confidence, 3),
            'field_types': field_types,
            'stakeholder_count': len(all_stakeholders),
            'high_confidence_count': len([f for f in fields if f.confidence >= 0.7]),
            'medium_confidence_count': len([f for f in fields if 0.4 <= f.confidence < 0.7]),
            'low_confidence_count': len([f for f in fields if f.confidence < 0.4])
        }