"""
Security extractor for identifying security requirements, threats, and compliance needs.
"""

import re
from typing import Dict, List, Any
from .base_extractor import BaseExtractor, ExtractedField


class SecurityExtractor(BaseExtractor):
    """Extracts security requirements, threats, and compliance information from conversations."""

    def _define_patterns(self) -> List[str]:
        return [
            r'(?:security|auth|authentication|authorization)\s+(?:requirement|spec)\s*:\s*([^.!?]+)',
            r'(?:threat|attack|vulnerability)\s*:\s*([^.!?]+)',
            r'(?:compliance|regulation|standard)\s*:\s*([^.!?]+)',
            r'(?:encrypt|hash|secure|protect)\s+([^.!?]+)',
            r'(?:permission|role|access)\s+(?:control|management)\s*:\s*([^.!?]+)',
            r'(?:gdpr|hipaa|sox|pci|iso 27001)\s+([^.!?]+)',
        ]

    def _define_keywords(self) -> List[str]:
        return [
            'security', 'authentication', 'authorization', 'encryption', 'hashing',
            'ssl', 'tls', 'https', 'oauth', 'jwt', 'saml', 'sso',
            'firewall', 'vpn', 'access control', 'permission', 'role',
            'threat', 'attack', 'vulnerability', 'exploit', 'breach',
            'compliance', 'gdpr', 'hipaa', 'sox', 'pci', 'iso', 'nist',
            'audit', 'logging', 'monitoring', 'incident', 'response',
            'privacy', 'data protection', 'personal data', 'sensitive',
            'secure', 'protect', 'defend', 'prevent', 'mitigate'
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
            security_text = match_info['match']
            security_content = match_info.get('groups', [''])[0] if match_info.get('groups') else security_text

            context = self._extract_context(content, match_info['start'], match_info['end'])
            confidence = self._calculate_confidence(security_text, [match_info['pattern']] + keyword_matches, context)
            stakeholders = self._extract_stakeholders(context)

            metadata = {
                'security_type': self._classify_security_type(security_text),
                'threat_level': self._extract_threat_level(context),
                'compliance_framework': self._extract_compliance_framework(context),
                'implementation': self._extract_implementation_details(context),
                'data_classification': self._extract_data_classification(context),
                'access_level': self._extract_access_level(context)
            }

            field = ExtractedField(
                field_type='security',
                content=security_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=stakeholders
            )
            extracted_fields.append(field)

        return extracted_fields

    def _classify_security_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(term in text_lower for term in ['auth', 'login', 'password', 'credential']):
            return 'authentication'
        elif any(term in text_lower for term in ['permission', 'role', 'access', 'authorization']):
            return 'authorization'
        elif any(term in text_lower for term in ['encrypt', 'decrypt', 'hash', 'crypto']):
            return 'encryption'
        elif any(term in text_lower for term in ['network', 'firewall', 'vpn', 'ssl', 'tls']):
            return 'network_security'
        elif any(term in text_lower for term in ['data', 'privacy', 'gdpr', 'hipaa']):
            return 'data_protection'
        elif any(term in text_lower for term in ['audit', 'log', 'monitor', 'compliance']):
            return 'compliance'
        elif any(term in text_lower for term in ['threat', 'attack', 'vulnerability']):
            return 'threat_management'
        else:
            return 'general'

    def _extract_threat_level(self, context: str) -> str:
        text_lower = context.lower()
        if any(term in text_lower for term in ['critical', 'severe', 'high risk', 'urgent']):
            return 'critical'
        elif any(term in text_lower for term in ['high', 'important', 'significant']):
            return 'high'
        elif any(term in text_lower for term in ['medium', 'moderate', 'normal']):
            return 'medium'
        elif any(term in text_lower for term in ['low', 'minor', 'informational']):
            return 'low'
        else:
            return 'medium'

    def _extract_compliance_framework(self, context: str) -> List[str]:
        frameworks = []
        framework_patterns = [
            r'\b(gdpr|ccpa|hipaa|sox|pci[-\s]?dss|iso[-\s]?27001|nist|fisma|fedramp)\b',
        ]
        for pattern in framework_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            frameworks.extend([m.upper().replace('-', ' ').replace(' ', '') for m in matches])
        return list(set(frameworks))

    def _extract_implementation_details(self, context: str) -> Dict[str, str]:
        details = {}
        
        # Extract encryption algorithms
        crypto_pattern = r'\b(aes|rsa|sha|md5|bcrypt|scrypt|pbkdf2)[-\s]?(\d+)?\b'
        crypto_match = re.search(crypto_pattern, context, re.IGNORECASE)
        if crypto_match:
            details['encryption'] = crypto_match.group(0)
        
        # Extract protocols
        protocol_pattern = r'\b(https?|ssl|tls|oauth|jwt|saml|ldap)\b'
        protocol_match = re.search(protocol_pattern, context, re.IGNORECASE)
        if protocol_match:
            details['protocol'] = protocol_match.group(0).upper()
        
        return details

    def _extract_data_classification(self, context: str) -> str:
        text_lower = context.lower()
        if any(term in text_lower for term in ['top secret', 'classified', 'confidential']):
            return 'confidential'
        elif any(term in text_lower for term in ['sensitive', 'restricted', 'personal']):
            return 'sensitive'
        elif any(term in text_lower for term in ['internal', 'private']):
            return 'internal'
        elif any(term in text_lower for term in ['public', 'open']):
            return 'public'
        else:
            return 'unclassified'

    def _extract_access_level(self, context: str) -> str:
        text_lower = context.lower()
        if any(term in text_lower for term in ['admin', 'administrator', 'root', 'superuser']):
            return 'admin'
        elif any(term in text_lower for term in ['manager', 'supervisor', 'lead']):
            return 'manager'
        elif any(term in text_lower for term in ['user', 'employee', 'staff']):
            return 'user'
        elif any(term in text_lower for term in ['guest', 'visitor', 'readonly', 'read-only']):
            return 'guest'
        else:
            return 'user'
