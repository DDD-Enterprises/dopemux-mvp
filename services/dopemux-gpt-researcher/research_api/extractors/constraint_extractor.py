"""
Constraint extractor for identifying technical, business, and regulatory constraints.
"""

import re
from typing import Dict, List, Any
from .base_extractor import BaseExtractor, ExtractedField


class ConstraintExtractor(BaseExtractor):
    """Extracts constraints, limitations, and restrictions from conversations."""

    def _define_patterns(self) -> List[str]:
        return [
            r'(?:constraint|limitation|restriction)\s*:\s*([^.!?]+)',
            r'(?:cannot|can\'t|unable to|must not)\s+([^.!?]+)',
            r'(?:budget|cost|time)\s+(?:constraint|limit)\s*:\s*([^.!?]+)',
            r'(?:regulation|compliance|policy)\s+(?:requires?|mandates?)\s+([^.!?]+)',
            r'(?:blocked by|prevented by|limited by)\s+([^.!?]+)',
            r'(?:deadline|timeline|schedule)\s+(?:constraint|requirement)\s*:\s*([^.!?]+)',
        ]

    def _define_keywords(self) -> List[str]:
        return [
            'constraint', 'limitation', 'restriction', 'requirement', 'mandate',
            'regulation', 'compliance', 'policy', 'rule', 'standard',
            'budget', 'cost', 'time', 'deadline', 'schedule', 'resource',
            'cannot', 'forbidden', 'prohibited', 'blocked', 'prevented',
            'legal', 'regulatory', 'security', 'privacy', 'gdpr', 'hipaa'
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
            constraint_text = match_info['match']
            constraint_content = match_info.get('groups', [''])[0] if match_info.get('groups') else constraint_text

            context = self._extract_context(content, match_info['start'], match_info['end'])
            confidence = self._calculate_confidence(constraint_text, [match_info['pattern']] + keyword_matches, context)
            stakeholders = self._extract_stakeholders(context)

            metadata = {
                'constraint_type': self._classify_constraint_type(constraint_text),
                'severity': self._extract_severity(context),
                'source': self._extract_constraint_source(context),
                'impact': self._extract_impact(context),
                'workaround': self._extract_workaround(context)
            }

            field = ExtractedField(
                field_type='constraint',
                content=constraint_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=stakeholders
            )
            extracted_fields.append(field)

        return extracted_fields

    def _classify_constraint_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(term in text_lower for term in ['budget', 'cost', 'money', 'financial']):
            return 'financial'
        elif any(term in text_lower for term in ['time', 'deadline', 'schedule']):
            return 'temporal'
        elif any(term in text_lower for term in ['resource', 'staff', 'team', 'capacity']):
            return 'resource'
        elif any(term in text_lower for term in ['technical', 'technology', 'system', 'platform']):
            return 'technical'
        elif any(term in text_lower for term in ['legal', 'regulation', 'compliance', 'policy']):
            return 'regulatory'
        elif any(term in text_lower for term in ['business', 'organizational', 'process']):
            return 'business'
        else:
            return 'general'

    def _extract_severity(self, context: str) -> str:
        text_lower = context.lower()
        if any(term in text_lower for term in ['critical', 'blocker', 'must', 'mandatory']):
            return 'critical'
        elif any(term in text_lower for term in ['important', 'should', 'significant']):
            return 'high'
        elif any(term in text_lower for term in ['minor', 'small', 'could']):
            return 'low'
        else:
            return 'medium'

    def _extract_constraint_source(self, context: str) -> str:
        source_patterns = [
            r'(?:according to|mandated by|required by)\s+([^.!?]+)',
            r'(?:regulation|policy|law)\s*:\s*([^.!?]+)',
        ]
        for pattern in source_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_impact(self, context: str) -> str:
        impact_patterns = [
            r'(?:impact|effect|consequence)\s*:\s*([^.!?]+)',
            r'(?:will|would|could)\s+(?:cause|lead to|result in)\s+([^.!?]+)',
        ]
        for pattern in impact_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_workaround(self, context: str) -> str:
        workaround_patterns = [
            r'(?:workaround|alternative|instead)\s*:\s*([^.!?]+)',
            r'(?:could|can|might)\s+(?:work around|bypass|avoid)\s+([^.!?]+)',
        ]
        for pattern in workaround_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''
