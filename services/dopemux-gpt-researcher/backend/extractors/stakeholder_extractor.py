"""
Stakeholder extractor for mapping stakeholders, roles, and responsibilities.
"""

import re
from typing import Dict, List, Any
from .base_extractor import BaseExtractor, ExtractedField


class StakeholderExtractor(BaseExtractor):
    """Extracts stakeholders, roles, and responsibility mappings from conversations."""

    def _define_patterns(self) -> List[str]:
        return [
            r'(@\w+)\s+(?:will|should|is responsible for)\s+([^.!?]+)',
            r'(?:role|responsibility)\s*:\s*([^.!?]+)',
            r'(?:stakeholder|owner|responsible)\s*:\s*([^.!?]+)',
            r'(\w+)\s+(?:team|department|group)\s+(?:will|should|handles?)\s+([^.!?]+)',
            r'(?:assigned to|delegated to|owned by)\s+([^.!?]+)',
            r'(?:contact|reach out to|ask)\s+([^.!?]+)\s+(?:about|for)',
        ]

    def _define_keywords(self) -> List[str]:
        return [
            'stakeholder', 'owner', 'responsible', 'accountable', 'role',
            'team', 'department', 'group', 'manager', 'lead', 'coordinator',
            'developer', 'designer', 'analyst', 'architect', 'engineer',
            'product', 'project', 'business', 'technical', 'user', 'customer',
            'client', 'vendor', 'partner', 'sponsor', 'executive', 'decision maker'
        ]

    def extract_from_chunk(self, chunk: Dict[str, Any]) -> List[ExtractedField]:
        content = chunk.get('content', '')
        if not content:
            return []

        content = self._preprocess_text(content)
        extracted_fields = []
        pattern_matches = self._find_pattern_matches(content)
        keyword_matches = self._find_keyword_matches(content)

        # Extract entities using spaCy
        doc = self.nlp(content)
        entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ['PERSON', 'ORG']]

        for match_info in pattern_matches:
            stakeholder_text = match_info['match']
            stakeholder_content = match_info.get('groups', [''])[0] if match_info.get('groups') else stakeholder_text

            context = self._extract_context(content, match_info['start'], match_info['end'])
            confidence = self._calculate_confidence(stakeholder_text, [match_info['pattern']] + keyword_matches, context)

            metadata = {
                'stakeholder_type': self._classify_stakeholder_type(stakeholder_text),
                'role': self._extract_role(context),
                'responsibilities': self._extract_responsibilities(context),
                'contact_info': self._extract_contact_info(context),
                'department': self._extract_department(context),
                'influence_level': self._assess_influence_level(context)
            }

            field = ExtractedField(
                field_type='stakeholder',
                content=stakeholder_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=[stakeholder_content.strip()]
            )
            extracted_fields.append(field)

        # Extract from named entities
        for entity_text, entity_type in entities:
            if entity_type == 'PERSON':
                sentences = [sent.text for sent in doc.sents if entity_text in sent.text]
                for sentence in sentences:
                    context = sentence
                    confidence = 0.7  # High confidence for named entities
                    
                    metadata = {
                        'stakeholder_type': 'person',
                        'role': self._extract_role(context),
                        'responsibilities': self._extract_responsibilities(context),
                        'contact_info': self._extract_contact_info(context),
                        'department': self._extract_department(context),
                        'influence_level': self._assess_influence_level(context)
                    }

                    field = ExtractedField(
                        field_type='stakeholder',
                        content=entity_text,
                        confidence=confidence,
                        context=context,
                        source_chunk_id=chunk.get('id'),
                        metadata=metadata,
                        timestamp=chunk.get('timestamp'),
                        stakeholders=[entity_text]
                    )
                    extracted_fields.append(field)

        return extracted_fields

    def _classify_stakeholder_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(term in text_lower for term in ['team', 'group', 'department']):
            return 'team'
        elif any(term in text_lower for term in ['customer', 'user', 'client']):
            return 'external'
        elif any(term in text_lower for term in ['manager', 'director', 'executive']):
            return 'management'
        elif any(term in text_lower for term in ['developer', 'engineer', 'designer']):
            return 'technical'
        else:
            return 'person'

    def _extract_role(self, context: str) -> str:
        role_patterns = [
            r'(?:role|title|position)\s*:\s*([^.!?]+)',
            r'(?:is|works as|serves as)\s+(?:a|an|the)?\s*([^.!?]+)',
        ]
        for pattern in role_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _extract_responsibilities(self, context: str) -> List[str]:
        responsibility_patterns = [
            r'(?:responsible for|handles?|manages?)\s+([^.!?]+)',
            r'(?:responsibility|duties?)\s*:\s*([^.!?]+)',
        ]
        responsibilities = []
        for pattern in responsibility_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            responsibilities.extend(matches)
        return [r.strip() for r in responsibilities if r.strip()]

    def _extract_contact_info(self, context: str) -> Dict[str, str]:
        contact = {}
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        phone_pattern = r'(\+?\d{1,3}[-.]?\d{3,4}[-.]?\d{3,4})'
        
        email_match = re.search(email_pattern, context)
        if email_match:
            contact['email'] = email_match.group(1)
            
        phone_match = re.search(phone_pattern, context)
        if phone_match:
            contact['phone'] = phone_match.group(1)
            
        return contact

    def _extract_department(self, context: str) -> str:
        dept_patterns = [
            r'(?:department|dept|division)\s*:\s*([^.!?]+)',
            r'(?:from|in)\s+(?:the)?\s*(\w+)\s+(?:team|department)',
        ]
        for pattern in dept_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ''

    def _assess_influence_level(self, context: str) -> str:
        text_lower = context.lower()
        if any(term in text_lower for term in ['executive', 'director', 'vp', 'ceo', 'cto']):
            return 'high'
        elif any(term in text_lower for term in ['manager', 'lead', 'senior']):
            return 'medium'
        else:
            return 'low'
