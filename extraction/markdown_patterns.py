"""
Markdown-Aware Pattern Extraction for Dopemux Documentation

Designed specifically for documents in DOCS_TO_PROCESS that use:
- Bold key-value pairs: **Focus Duration**: 25 minutes
- Markdown headers as section identifiers
- Bullet point lists for features/requirements
- Code blocks and structured content
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class MarkdownEntity:
    """Extracted entity from markdown content."""
    type: str
    content: str
    value: Optional[str] = None
    section: Optional[str] = None
    line_number: int = 0
    confidence: float = 0.0


class MarkdownPatternExtractor:
    """Extract semantic entities from markdown documents."""

    def __init__(self):
        """Initialize extractor with markdown-specific patterns."""
        self._init_patterns()
        self.current_section = None

    def _init_patterns(self):
        """Initialize markdown-aware extraction patterns."""

        # Bold key-value pairs: **Key**: Value
        self.bold_kv_pattern = re.compile(
            r'\*\*([^*]+?)\*\*\s*:\s*([^\n]+)',
            re.MULTILINE
        )

        # Headers (section identifiers)
        self.header_pattern = re.compile(
            r'^(#{1,6})\s+(.+?)(?:\s*#*)?$',
            re.MULTILINE
        )

        # List items with optional bold keys
        self.list_item_pattern = re.compile(
            r'^[\s]*[-*+]\s+(?:\*\*([^*]+?)\*\*\s*:\s*)?(.+?)$',
            re.MULTILINE
        )

        # Code blocks (to exclude from text processing)
        self.code_block_pattern = re.compile(
            r'```[\s\S]*?```|`[^`]+`',
            re.MULTILINE
        )

        # ADHD-specific patterns
        self.adhd_patterns = {
            'focus_settings': re.compile(
                r'(?:focus|attention|concentration)[\s\w]*:\s*([^\n]+)',
                re.IGNORECASE | re.MULTILINE
            ),
            'break_intervals': re.compile(
                r'(?:break|interval|pause)[\s\w]*:\s*([^\n]+)',
                re.IGNORECASE | re.MULTILINE
            ),
            'accommodations': re.compile(
                r'(?:accommodation|adaptation|support)[\s\w]*:\s*([^\n]+)',
                re.IGNORECASE | re.MULTILINE
            ),
            'task_management': re.compile(
                r'(?:task|todo|chunking|decomposition)[\s\w]*:\s*([^\n]+)',
                re.IGNORECASE | re.MULTILINE
            )
        }

        # Development pattern categories
        self.dev_categories = {
            'principles': ['principle', 'guideline', 'rule'],
            'features': ['feature', 'capability', 'functionality'],
            'settings': ['setting', 'config', 'configuration'],
            'commands': ['command', 'cmd', 'cli'],
            'strategies': ['strategy', 'approach', 'method'],
            'standards': ['standard', 'convention', 'practice']
        }

    def extract_entities(self, content: str, filename: str = "") -> List[MarkdownEntity]:
        """Extract all entities from markdown content."""
        entities = []

        # Remove code blocks for cleaner text processing
        clean_content = self.code_block_pattern.sub('', content)
        lines = content.splitlines()

        # Extract headers and track sections
        entities.extend(self._extract_headers(lines))

        # Extract bold key-value pairs
        entities.extend(self._extract_bold_keyvalues(clean_content, lines))

        # Extract list items
        entities.extend(self._extract_list_items(lines))

        # Extract ADHD-specific patterns
        entities.extend(self._extract_adhd_patterns(clean_content, lines))

        # Calculate confidence scores
        for entity in entities:
            entity.confidence = self._calculate_confidence(entity, content, filename)

        return entities

    def _extract_headers(self, lines: List[str]) -> List[MarkdownEntity]:
        """Extract markdown headers as section identifiers."""
        entities = []

        for line_num, line in enumerate(lines, 1):
            match = self.header_pattern.match(line)
            if match:
                level = len(match.group(1))  # Number of # symbols
                header_text = match.group(2).strip()

                entity = MarkdownEntity(
                    type='section_header',
                    content=header_text,
                    section=header_text,
                    line_number=line_num,
                    confidence=0.9  # High confidence for headers
                )
                entities.append(entity)

                # Update current section for context
                if level <= 2:  # Only track main sections
                    self.current_section = header_text

        return entities

    def _extract_bold_keyvalues(self, content: str, lines: List[str]) -> List[MarkdownEntity]:
        """Extract bold key-value pairs like **Focus Duration**: 25 minutes."""
        entities = []

        for match in self.bold_kv_pattern.finditer(content):
            key = match.group(1).strip()
            value = match.group(2).strip()

            # Find line number
            line_num = content[:match.start()].count('\n') + 1

            # Categorize the key
            entity_type = self._categorize_key(key)

            entity = MarkdownEntity(
                type=entity_type,
                content=key,
                value=value,
                section=self.current_section,
                line_number=line_num
            )
            entities.append(entity)

        return entities

    def _extract_list_items(self, lines: List[str]) -> List[MarkdownEntity]:
        """Extract list items, especially those with bold keys."""
        entities = []

        for line_num, line in enumerate(lines, 1):
            match = self.list_item_pattern.match(line)
            if match:
                key = match.group(1)  # Bold key (may be None)
                content = match.group(2).strip()

                if key:  # Has bold key
                    entity_type = self._categorize_key(key)
                    entity = MarkdownEntity(
                        type=entity_type,
                        content=key,
                        value=content,
                        section=self.current_section,
                        line_number=line_num
                    )
                else:  # Simple list item
                    entity_type = self._categorize_content(content)
                    entity = MarkdownEntity(
                        type=entity_type,
                        content=content,
                        section=self.current_section,
                        line_number=line_num
                    )

                entities.append(entity)

        return entities

    def _extract_adhd_patterns(self, content: str, lines: List[str]) -> List[MarkdownEntity]:
        """Extract ADHD-specific patterns and accommodations."""
        entities = []

        for pattern_type, pattern in self.adhd_patterns.items():
            for match in pattern.finditer(content):
                value = match.group(1).strip()
                line_num = content[:match.start()].count('\n') + 1

                entity = MarkdownEntity(
                    type=f'adhd_{pattern_type}',
                    content=f'{pattern_type}: {value}',
                    value=value,
                    section=self.current_section,
                    line_number=line_num
                )
                entities.append(entity)

        return entities

    def _categorize_key(self, key: str) -> str:
        """Categorize a key based on its content."""
        key_lower = key.lower()

        # Check development categories
        for category, keywords in self.dev_categories.items():
            if any(keyword in key_lower for keyword in keywords):
                return category

        # ADHD-specific categorization
        adhd_keywords = {
            'adhd_accommodation': ['adhd', 'neurodivergent', 'accommodation', 'adaptation'],
            'focus_setting': ['focus', 'attention', 'concentration', 'duration'],
            'break_setting': ['break', 'interval', 'pause'],
            'notification_setting': ['notification', 'alert', 'reminder'],
            'task_setting': ['task', 'todo', 'chunking', 'decomposition']
        }

        for category, keywords in adhd_keywords.items():
            if any(keyword in key_lower for keyword in keywords):
                return category

        # Fallback categorization
        if any(word in key_lower for word in ['config', 'setting', 'option']):
            return 'configuration'
        if any(word in key_lower for word in ['command', 'cmd', 'cli']):
            return 'command'

        return 'general_property'

    def _categorize_content(self, content: str) -> str:
        """Categorize content without explicit keys."""
        content_lower = content.lower()

        if any(word in content_lower for word in ['use', 'prefer', 'follow', 'write']):
            return 'guideline'
        if any(word in content_lower for word in ['support', 'provide', 'enable']):
            return 'feature'
        if any(word in content_lower for word in ['must', 'should', 'require']):
            return 'requirement'

        return 'general_item'

    def _calculate_confidence(self, entity: MarkdownEntity, full_content: str, filename: str) -> float:
        """Calculate confidence score for extracted entity."""
        base_confidence = 0.7

        # Boost for ADHD/domain-specific content
        if 'adhd' in entity.type or any(word in entity.content.lower()
                                       for word in ['adhd', 'neurodivergent', 'focus', 'attention']):
            base_confidence += 0.2

        # Boost for structured formatting (bold keys)
        if entity.value is not None:  # Has key-value structure
            base_confidence += 0.1

        # Boost for specific sections
        if entity.section and any(word in entity.section.lower()
                                 for word in ['adhd', 'development', 'configuration']):
            base_confidence += 0.1

        # Boost for dopemux-related filename
        if 'dopemux' in filename.lower() or 'claude' in filename.lower():
            base_confidence += 0.05

        return max(0.1, min(1.0, base_confidence))

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
                'section': entity.section,
                'line_number': entity.line_number,
                'confidence': entity.confidence
            })

        return categorized


def extract_markdown_entities(content: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
    """Convenience function to extract entities from markdown content."""
    extractor = MarkdownPatternExtractor()
    return extractor.extract_to_dict(content, filename)


# Test function for validation
def test_with_sample_content():
    """Test the extractor with sample content from DOCS_TO_PROCESS."""
    sample_content = '''
# Python Project - Dopemux Configuration

## ADHD Accommodations Active
- **Focus Duration**: 25 minutes average
- **Break Intervals**: 5 minutes
- **Notification Style**: gentle
- **Visual Complexity**: minimal
- **Attention Adaptation**: Enabled

### Development Principles
- **Context Preservation**: Auto-save every 30 seconds
- **Gentle Guidance**: Use encouraging, supportive language
- **Progressive Disclosure**: Show essential info first, details on request
- **Task Chunking**: Break work into 25-minute segments

### Python Development Guidelines
- Use type hints for better ADHD developer experience
- Follow PEP 8 with Black formatting
- Prefer explicit over implicit (Zen of Python)
'''

    extractor = MarkdownPatternExtractor()
    entities = extractor.extract_entities(sample_content, "claude.md")

    print("Extracted entities:")
    for entity in entities:
        print(f"  {entity.type}: {entity.content}")
        if entity.value:
            print(f"    Value: {entity.value}")
        print(f"    Confidence: {entity.confidence:.2f}")
        print()

    return entities


if __name__ == "__main__":
    test_with_sample_content()