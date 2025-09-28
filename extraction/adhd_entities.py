"""
ADHD-Specific Entity Extractor for Dopemux Documentation

Specialized extractor focused on ADHD accommodations, neurodivergent
features, and cognitive load optimization patterns in documentation.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ADHDEntity:
    """Extracted ADHD-specific entity."""
    type: str
    content: str
    value: Optional[str] = None
    category: str = "general"
    accommodation_type: Optional[str] = None
    confidence: float = 0.0
    source_context: Optional[str] = None


class ADHDEntityExtractor:
    """Extract ADHD and neurodivergent-specific entities from documentation."""

    def __init__(self):
        """Initialize ADHD extractor with specialized patterns."""
        self._init_adhd_patterns()
        self._init_accommodation_mappings()

    def _init_adhd_patterns(self):
        """Initialize ADHD-specific extraction patterns."""

        # Core ADHD accommodation patterns
        self.core_patterns = {
            'focus_settings': {
                'pattern': re.compile(
                    r'(?:\*\*)?(?:focus|attention|concentration)[\s\w]*(?:\*\*)?\s*:?\s*([^\n]+)',
                    re.IGNORECASE | re.MULTILINE
                ),
                'category': 'attention_management'
            },
            'break_settings': {
                'pattern': re.compile(
                    r'(?:\*\*)?(?:break|interval|pause|rest)[\s\w]*(?:\*\*)?\s*:?\s*([^\n]+)',
                    re.IGNORECASE | re.MULTILINE
                ),
                'category': 'energy_management'
            },
            'task_management': {
                'pattern': re.compile(
                    r'(?:\*\*)?(?:task|chunking|decomposition|breakdown)[\s\w]*(?:\*\*)?\s*:?\s*([^\n]+)',
                    re.IGNORECASE | re.MULTILINE
                ),
                'category': 'executive_function'
            },
            'cognitive_load': {
                'pattern': re.compile(
                    r'(?:\*\*)?(?:cognitive|mental|visual)?\s*(?:load|complexity|burden|overhead)(?:\*\*)?\s*:?\s*([^\n]+)',
                    re.IGNORECASE | re.MULTILINE
                ),
                'category': 'cognitive_optimization'
            },
            'notifications': {
                'pattern': re.compile(
                    r'(?:\*\*)?(?:notification|alert|reminder|gentle)[\s\w]*(?:\*\*)?\s*:?\s*([^\n]+)',
                    re.IGNORECASE | re.MULTILINE
                ),
                'category': 'sensory_management'
            }
        }

        # ADHD feature detection patterns
        self.feature_patterns = {
            'context_preservation': re.compile(
                r'(?:context|session|state)\s+(?:preservation|persistence|saving|restoration)',
                re.IGNORECASE | re.MULTILINE
            ),
            'attention_monitoring': re.compile(
                r'(?:attention|focus)\s+(?:monitoring|tracking|awareness)',
                re.IGNORECASE | re.MULTILINE
            ),
            'progressive_disclosure': re.compile(
                r'progressive\s+disclosure|show\s+essential\s+first|details\s+on\s+request',
                re.IGNORECASE | re.MULTILINE
            ),
            'gentle_guidance': re.compile(
                r'gentle|encouraging|supportive|non-judgmental',
                re.IGNORECASE | re.MULTILINE
            ),
            'decision_reduction': re.compile(
                r'(?:reduce|limit|minimize)\s+(?:decisions|choices|options)|maximum\s+\d+\s+options',
                re.IGNORECASE | re.MULTILINE
            )
        }

        # Neurodivergent terminology patterns
        self.terminology_patterns = {
            'adhd_terms': re.compile(
                r'\b(?:ADHD|ADD|attention\s+deficit|hyperactivity|neurodivergent|neurodiverse)\b',
                re.IGNORECASE | re.MULTILINE
            ),
            'executive_function': re.compile(
                r'executive\s+function|working\s+memory|cognitive\s+flexibility|inhibitory\s+control',
                re.IGNORECASE | re.MULTILINE
            ),
            'hyperfocus': re.compile(
                r'hyperfocus|deep\s+focus|flow\s+state|intense\s+concentration',
                re.IGNORECASE | re.MULTILINE
            ),
            'time_blindness': re.compile(
                r'time\s+blindness|time\s+awareness|temporal\s+processing',
                re.IGNORECASE | re.MULTILINE
            )
        }

    def _init_accommodation_mappings(self):
        """Initialize accommodation type mappings."""
        self.accommodation_types = {
            'attention_management': [
                'focus duration', 'attention span', 'concentration',
                'distraction filtering', 'attention monitoring'
            ],
            'energy_management': [
                'break intervals', 'rest periods', 'energy conservation',
                'hyperfocus prevention', 'sustainable pacing'
            ],
            'executive_function': [
                'task decomposition', 'decision reduction', 'working memory support',
                'planning assistance', 'cognitive scaffolding'
            ],
            'cognitive_optimization': [
                'cognitive load reduction', 'visual complexity', 'information hierarchy',
                'progressive disclosure', 'mental model preservation'
            ],
            'sensory_management': [
                'gentle notifications', 'sensory filtering', 'distraction management',
                'environmental accommodations'
            ],
            'emotional_regulation': [
                'gentle guidance', 'encouraging feedback', 'anxiety reduction',
                'stress management', 'emotional safety'
            ]
        }

        # Time-related patterns
        self.time_patterns = {
            'duration': re.compile(r'(\d+)\s*(?:minute|min|hour|hr|second|sec)s?', re.IGNORECASE),
            'frequency': re.compile(r'every\s+(\d+)\s*(?:minute|min|hour|hr|second|sec)s?', re.IGNORECASE),
            'range': re.compile(r'(\d+)[-–](\d+)\s*(?:minute|min|hour|hr)s?', re.IGNORECASE)
        }

    def extract_entities(self, content: str, filename: str = "") -> List[ADHDEntity]:
        """Extract ADHD-specific entities from content."""
        entities = []

        # Extract core ADHD patterns
        entities.extend(self._extract_core_patterns(content))

        # Extract ADHD features
        entities.extend(self._extract_features(content))

        # Extract terminology
        entities.extend(self._extract_terminology(content))

        # Extract time-related accommodations
        entities.extend(self._extract_time_patterns(content))

        # Calculate confidence scores
        for entity in entities:
            entity.confidence = self._calculate_confidence(entity, content, filename)

        # Remove duplicates and merge similar entities
        entities = self._deduplicate_entities(entities)

        return entities

    def _extract_core_patterns(self, content: str) -> List[ADHDEntity]:
        """Extract core ADHD accommodation patterns."""
        entities = []

        for pattern_name, pattern_info in self.core_patterns.items():
            pattern = pattern_info['pattern']
            category = pattern_info['category']

            for match in pattern.finditer(content):
                if match.groups():
                    value = match.group(1).strip()
                    key_text = match.group(0)[:match.start(1)].strip()
                else:
                    value = None
                    key_text = match.group(0).strip()

                entity = ADHDEntity(
                    type=pattern_name,
                    content=key_text,
                    value=value,
                    category=category,
                    accommodation_type=self._classify_accommodation(key_text, value),
                    source_context=self._get_context(content, match.start(), match.end())
                )
                entities.append(entity)

        return entities

    def _extract_features(self, content: str) -> List[ADHDEntity]:
        """Extract ADHD feature implementations."""
        entities = []

        for feature_name, pattern in self.feature_patterns.items():
            for match in pattern.finditer(content):
                entity = ADHDEntity(
                    type='adhd_feature',
                    content=match.group(0),
                    category='feature_implementation',
                    accommodation_type=feature_name,
                    source_context=self._get_context(content, match.start(), match.end())
                )
                entities.append(entity)

        return entities

    def _extract_terminology(self, content: str) -> List[ADHDEntity]:
        """Extract neurodivergent terminology and concepts."""
        entities = []

        for term_type, pattern in self.terminology_patterns.items():
            for match in pattern.finditer(content):
                entity = ADHDEntity(
                    type='neurodivergent_terminology',
                    content=match.group(0),
                    category='terminology',
                    accommodation_type=term_type,
                    source_context=self._get_context(content, match.start(), match.end())
                )
                entities.append(entity)

        return entities

    def _extract_time_patterns(self, content: str) -> List[ADHDEntity]:
        """Extract time-related ADHD accommodations."""
        entities = []

        for time_type, pattern in self.time_patterns.items():
            for match in pattern.finditer(content):
                entity = ADHDEntity(
                    type='time_accommodation',
                    content=match.group(0),
                    value=match.group(1) if match.groups() else None,
                    category='temporal_support',
                    accommodation_type=time_type,
                    source_context=self._get_context(content, match.start(), match.end())
                )
                entities.append(entity)

        return entities

    def _classify_accommodation(self, key_text: str, value: Optional[str]) -> str:
        """Classify the type of accommodation based on content."""
        combined_text = f"{key_text} {value or ''}".lower()

        for acc_type, keywords in self.accommodation_types.items():
            if any(keyword in combined_text for keyword in keywords):
                return acc_type

        return 'general_accommodation'

    def _get_context(self, content: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for an entity."""
        context_start = max(0, start - window)
        context_end = min(len(content), end + window)
        return content[context_start:context_end].strip()

    def _calculate_confidence(self, entity: ADHDEntity, content: str, filename: str) -> float:
        """Calculate confidence score for ADHD entity."""
        base_confidence = 0.8  # Higher base for specialized extractor

        # Boost for specific ADHD terminology
        adhd_indicators = ['adhd', 'neurodivergent', 'executive', 'cognitive', 'attention']
        if any(indicator in entity.content.lower() for indicator in adhd_indicators):
            base_confidence += 0.15

        # Boost for structured patterns (bold, lists)
        if entity.value is not None:
            base_confidence += 0.1

        # Boost for accommodation-specific content
        if entity.accommodation_type and entity.accommodation_type != 'general_accommodation':
            base_confidence += 0.1

        # Boost for dopemux/ADHD-related files
        if any(term in filename.lower() for term in ['adhd', 'dopemux', 'claude', 'config']):
            base_confidence += 0.05

        # Boost for time-specific accommodations (very reliable)
        if entity.type == 'time_accommodation':
            base_confidence += 0.1

        return max(0.1, min(1.0, base_confidence))

    def _deduplicate_entities(self, entities: List[ADHDEntity]) -> List[ADHDEntity]:
        """Remove duplicate entities and merge similar ones."""
        unique_entities = []
        seen_content = set()

        for entity in entities:
            # Create a normalized key for deduplication
            content_key = entity.content.lower().strip()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_entities.append(entity)

        return unique_entities

    def extract_adhd_profile(self, content: str) -> Dict[str, Any]:
        """Extract a comprehensive ADHD accommodation profile."""
        entities = self.extract_entities(content)

        profile = {
            'accommodation_categories': {},
            'time_settings': {},
            'features': [],
            'terminology_found': [],
            'confidence_summary': {}
        }

        # Group entities by category
        for entity in entities:
            category = entity.category

            if category not in profile['accommodation_categories']:
                profile['accommodation_categories'][category] = []

            profile['accommodation_categories'][category].append({
                'type': entity.type,
                'content': entity.content,
                'value': entity.value,
                'accommodation_type': entity.accommodation_type,
                'confidence': entity.confidence
            })

            # Collect time settings separately
            if entity.type == 'time_accommodation':
                if entity.accommodation_type not in profile['time_settings']:
                    profile['time_settings'][entity.accommodation_type] = []
                profile['time_settings'][entity.accommodation_type].append(entity.value)

            # Collect features
            if entity.type == 'adhd_feature':
                profile['features'].append(entity.accommodation_type)

            # Collect terminology
            if entity.type == 'neurodivergent_terminology':
                profile['terminology_found'].append(entity.content)

        # Calculate confidence summary
        confidences = [e.confidence for e in entities if e.confidence > 0]
        if confidences:
            profile['confidence_summary'] = {
                'average': sum(confidences) / len(confidences),
                'max': max(confidences),
                'min': min(confidences),
                'total_entities': len(entities)
            }

        return profile

    def extract_to_dict(self, content: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities and return as categorized dictionary."""
        entities = self.extract_entities(content, filename)

        # Group by type
        categorized = {}
        for entity in entities:
            if entity.type not in categorized:
                categorized[entity.type] = []

            categorized[entity.type].append({
                'content': entity.content,
                'value': entity.value,
                'category': entity.category,
                'accommodation_type': entity.accommodation_type,
                'confidence': entity.confidence,
                'source_context': entity.source_context
            })

        return categorized


def extract_adhd_entities(content: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
    """Convenience function to extract ADHD entities from content."""
    extractor = ADHDEntityExtractor()
    return extractor.extract_to_dict(content, filename)


# Test function
def test_adhd_extractor():
    """Test the ADHD extractor with sample content."""
    sample_content = '''
# ADHD Accommodations Active

- **Focus Duration**: 25 minutes average
- **Break Intervals**: 5 minutes
- **Attention Adaptation**: Enabled
- **Task Chunking**: Break work into 25-minute segments

### ADHD Features
- Context preservation for neurodivergent developers
- Progressive disclosure to reduce cognitive load
- Gentle notifications for executive function support

The system provides ADHD-friendly task decomposition and helps with time blindness
through automatic break reminders every 30 minutes.
'''

    extractor = ADHDEntityExtractor()
    entities = extractor.extract_entities(sample_content, "adhd_config.md")

    print("ADHD-specific entities extracted:")
    for entity in entities:
        print(f"  {entity.type}: {entity.content}")
        if entity.value:
            print(f"    Value: {entity.value}")
        print(f"    Category: {entity.category}")
        print(f"    Accommodation: {entity.accommodation_type}")
        print(f"    Confidence: {entity.confidence:.2f}")
        print()

    # Test profile extraction
    print("ADHD Profile:")
    profile = extractor.extract_adhd_profile(sample_content)
    for category, items in profile['accommodation_categories'].items():
        print(f"  {category}: {len(items)} items")

    return entities


if __name__ == "__main__":
    test_adhd_extractor()