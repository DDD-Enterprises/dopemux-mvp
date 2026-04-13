"""
Research extractor for identifying research findings, sources, and conclusions in conversations.
"""

import re
from typing import Dict, List, Any
from .base_extractor import BaseExtractor, ExtractedField


class ResearchExtractor(BaseExtractor):
    """Extracts research findings, sources, conclusions, and data from conversations."""

    def _define_patterns(self) -> List[str]:
        return [
            r'(?:research|study|analysis)\s+(?:shows?|indicates?|suggests?|found)\s+([^.!?]+)',
            r'(?:according to|based on)\s+([^.!?]+)',
            r'(?:source|reference|citation)\s*:\s*([^.!?]+)',
            r'(?:data|statistics|metrics)\s+(?:shows?|indicates?)\s+([^.!?]+)',
            r'(?:finding|conclusion|result)\s*:\s*([^.!?]+)',
            r'(?:evidence|proof|support)\s+(?:that|for)\s+([^.!?]+)',
        ]

    def _define_keywords(self) -> List[str]:
        return [
            'research', 'study', 'analysis', 'finding', 'conclusion', 'result',
            'data', 'statistics', 'metrics', 'evidence', 'proof', 'source',
            'reference', 'citation', 'survey', 'report', 'investigation',
            'benchmark', 'comparison', 'case study', 'experiment', 'test'
        ]

    def extract_from_chunk(self, chunk: Dict[str, Any]) -> List[ExtractedField]:
        content = chunk.get('content', '')
        if not content:
            return []

        content = self._preprocess_text(content)
        extracted_fields = []
        pattern_matches = self._find_pattern_matches(content)
        keyword_matches = self._find_keyword_matches(content)

        for match_info in pattern_matches:
            research_text = match_info['match']
            research_content = match_info.get('groups', [''])[0] if match_info.get('groups') else research_text

            context = self._extract_context(content, match_info['start'], match_info['end'])
            confidence = self._calculate_confidence(research_text, [match_info['pattern']] + keyword_matches, context)
            stakeholders = self._extract_stakeholders(context)

            metadata = {
                'research_type': self._classify_research_type(research_text),
                'source': self._extract_source(context),
                'methodology': self._extract_methodology(context),
                'sample_size': self._extract_sample_size(context),
                'confidence_level': self._extract_research_confidence(context),
                'limitations': self._extract_limitations(context)
            }

            field = ExtractedField(
                field_type='research',
                content=research_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=stakeholders
            )
            extracted_fields.append(field)

        return extracted_fields

    def _classify_research_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(term in text_lower for term in ['survey', 'poll', 'questionnaire']):
            return 'survey'
        elif any(term in text_lower for term in ['experiment', 'test', 'trial']):
            return 'experimental'
        elif any(term in text_lower for term in ['case study', 'analysis']):
            return 'case_study'
        elif any(term in text_lower for term in ['benchmark', 'comparison']):
            return 'comparative'
        else:
            return 'general'

    def _extract_source(self, context: str) -> str:
        source_patterns = [
            r'(?:source|from|according to)\s*:\s*([^.!?]+)',
            r'(?:published|reported)\s+(?:by|in)\s+([^.!?]+)',
        ]
        for pattern in source_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_methodology(self, context: str) -> str:
        method_patterns = [
            r'(?:methodology|method|approach)\s*:\s*([^.!?]+)',
            r'(?:using|via|through)\s+([^.!?]+)',
        ]
        for pattern in method_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_sample_size(self, context: str) -> str:
        size_pattern = r'(?:sample|n|participants?)\s*[=:]?\s*(\d+)'
        match = re.search(size_pattern, context, re.IGNORECASE)
        return match.group(1) if match else ''

    def _extract_research_confidence(self, context: str) -> str:
        confidence_patterns = [
            r'(\d+)%\s*confidence',
            r'confidence\s+(?:level|interval)\s*[=:]?\s*(\d+)%',
        ]
        for pattern in confidence_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1) + '%'
        return ''

    def _extract_limitations(self, context: str) -> List[str]:
        limitation_patterns = [
            r'limitation\s*:\s*([^.!?]+)',
            r'(?:however|but|limitation)\s+([^.!?]+)',
            r'(?:caveat|note|warning)\s*:\s*([^.!?]+)',
        ]
        limitations = []
        for pattern in limitation_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            limitations.extend(matches)
        return [l.strip() for l in limitations if l.strip()]