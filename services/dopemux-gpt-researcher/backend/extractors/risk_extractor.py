"""
Risk extractor for identifying risks, mitigations, and impact assessments.
"""

import re
from typing import Dict, List, Any
from .base_extractor import BaseExtractor, ExtractedField


class RiskExtractor(BaseExtractor):
    """Extracts risks, mitigations, and impact assessments from conversations."""

    def _define_patterns(self) -> List[str]:
        return [
            r'(?:risk|concern|issue|problem)\s*:\s*([^.!?]+)',
            r'(?:might|could|may)\s+(?:cause|lead to|result in)\s+([^.!?]+)',
            r'(?:vulnerable to|susceptible to|at risk of)\s+([^.!?]+)',
            r'(?:mitigation|solution|fix)\s*:\s*([^.!?]+)',
            r'(?:impact|consequence|effect)\s*:\s*([^.!?]+)',
            r'(?:worst case|if this fails|potential failure)\s+([^.!?]+)',
        ]

    def _define_keywords(self) -> List[str]:
        return [
            'risk', 'concern', 'issue', 'problem', 'threat', 'vulnerability',
            'danger', 'hazard', 'challenge', 'obstacle', 'blocker',
            'mitigation', 'solution', 'fix', 'workaround', 'contingency',
            'impact', 'consequence', 'effect', 'damage', 'loss',
            'failure', 'breakdown', 'outage', 'breach', 'attack',
            'security', 'safety', 'compliance', 'legal', 'financial'
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
            risk_text = match_info['match']
            risk_content = match_info.get('groups', [''])[0] if match_info.get('groups') else risk_text

            context = self._extract_context(content, match_info['start'], match_info['end'])
            confidence = self._calculate_confidence(risk_text, [match_info['pattern']] + keyword_matches, context)
            stakeholders = self._extract_stakeholders(context)

            metadata = {
                'risk_type': self._classify_risk_type(risk_text),
                'probability': self._extract_probability(context),
                'impact_level': self._extract_impact_level(context),
                'severity': self._calculate_risk_severity(context),
                'mitigation': self._extract_mitigation(context),
                'owner': self._extract_risk_owner(context),
                'timeline': self._extract_risk_timeline(context)
            }

            field = ExtractedField(
                field_type='risk',
                content=risk_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=stakeholders
            )
            extracted_fields.append(field)

        return extracted_fields

    def _classify_risk_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(term in text_lower for term in ['security', 'breach', 'attack', 'hack']):
            return 'security'
        elif any(term in text_lower for term in ['technical', 'system', 'failure', 'outage']):
            return 'technical'
        elif any(term in text_lower for term in ['business', 'market', 'competitive']):
            return 'business'
        elif any(term in text_lower for term in ['financial', 'budget', 'cost']):
            return 'financial'
        elif any(term in text_lower for term in ['operational', 'process', 'workflow']):
            return 'operational'
        elif any(term in text_lower for term in ['legal', 'compliance', 'regulatory']):
            return 'regulatory'
        elif any(term in text_lower for term in ['reputation', 'brand', 'image']):
            return 'reputational'
        else:
            return 'general'

    def _extract_probability(self, context: str) -> str:
        prob_patterns = [
            r'(?:probability|likelihood|chance)\s*:\s*([^.!?]+)',
            r'(\d+)%\s*(?:chance|probability)',
            r'(?:likely|unlikely|probable|improbable)',
        ]
        for pattern in prob_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        # Implicit probability
        text_lower = context.lower()
        if any(term in text_lower for term in ['very likely', 'almost certain', 'probable']):
            return 'high'
        elif any(term in text_lower for term in ['possible', 'might', 'could']):
            return 'medium'
        elif any(term in text_lower for term in ['unlikely', 'remote', 'rare']):
            return 'low'
        else:
            return 'unknown'

    def _extract_impact_level(self, context: str) -> str:
        impact_patterns = [
            r'(?:impact|consequence|damage)\s*:\s*([^.!?]+)',
            r'(?:would|could)\s+(?:cause|result in|lead to)\s+([^.!?]+)',
        ]
        for pattern in impact_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                impact_text = match.group(1).lower()
                if any(term in impact_text for term in ['critical', 'severe', 'catastrophic']):
                    return 'high'
                elif any(term in impact_text for term in ['significant', 'major', 'serious']):
                    return 'medium'
                elif any(term in impact_text for term in ['minor', 'small', 'limited']):
                    return 'low'
        return 'medium'

    def _calculate_risk_severity(self, context: str) -> str:
        probability = self._extract_probability(context)
        impact = self._extract_impact_level(context)
        
        # Simple risk matrix calculation
        prob_score = {'high': 3, 'medium': 2, 'low': 1, 'unknown': 2}.get(probability, 2)
        impact_score = {'high': 3, 'medium': 2, 'low': 1}.get(impact, 2)
        total_score = prob_score * impact_score
        
        if total_score >= 6:
            return 'critical'
        elif total_score >= 4:
            return 'high'
        elif total_score >= 2:
            return 'medium'
        else:
            return 'low'

    def _extract_mitigation(self, context: str) -> List[str]:
        mitigation_patterns = [
            r'(?:mitigation|solution|fix|workaround)\s*:\s*([^.!?]+)',
            r'(?:to|can)\s+(?:mitigate|address|solve|fix)\s+([^.!?]+)',
            r'(?:prevention|preventive)\s+(?:measure|action)\s*:\s*([^.!?]+)',
        ]
        mitigations = []
        for pattern in mitigation_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            mitigations.extend(matches)
        return [m.strip() for m in mitigations if m.strip()]

    def _extract_risk_owner(self, context: str) -> str:
        owner_patterns = [
            r'(?:owner|responsible|assigned to)\s*:\s*([^.!?]+)',
            r'(@\w+)\s+(?:will|should)\s+(?:handle|manage|address)',
        ]
        for pattern in owner_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_risk_timeline(self, context: str) -> str:
        timeline_patterns = [
            r'(?:by|within|before)\s+(\w+\s+\d+|\d+\s+\w+)',
            r'(?:timeline|deadline)\s*:\s*([^.!?]+)',
        ]
        for pattern in timeline_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''
