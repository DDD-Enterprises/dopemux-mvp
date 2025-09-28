"""PII detection patterns and validators."""

import hashlib
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """Represents a detected PII entity."""
    type: str
    text: str
    start: int
    end: int
    confidence: float = 1.0


class PIIPatterns:
    """Collection of PII detection patterns and validators."""
    
    # Core regex patterns for structured PII
    PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
        'phone_us': re.compile(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'),
        'phone_intl': re.compile(r'\+\d{1,3}[-.\s]?\d{1,14}'),
        'ssn': re.compile(r'\b(?!000|666|9\d{2})([0-8]\d{2}|7([0-6]\d))([-]?|\s{1})(?!00)\d{2}\2(?!0000)\d{4}\b'),
        'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        'url': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?', re.IGNORECASE),
        'address': re.compile(r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Boulevard|Blvd)', re.IGNORECASE),
        'zip_code': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
        'coordinates': re.compile(r'[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)'),
    }
    
    # Name patterns (common first/last names)
    COMMON_NAMES = {
        'first_names': {
            'male': {'john', 'michael', 'william', 'james', 'david', 'robert', 'christopher', 'joseph', 'thomas', 'charles'},
            'female': {'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica', 'sarah', 'karen'},
        },
        'last_names': {'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez', 'martinez'},
    }
    
    # Chat-specific patterns
    CHAT_PATTERNS = {
        'mention_me': re.compile(r'\b(?:call me|text me|reach me at|my (?:phone|number) is)\s+([^\s]+)', re.IGNORECASE),
        'address_context': re.compile(r'\b(?:i live (?:at|on)|my address is|home is at|work is at)\s+([^.!?]+)', re.IGNORECASE),
        'name_context': re.compile(r'\b(?:my name is|i\'m|im)\s+([A-Za-z]+)', re.IGNORECASE),
        'birthday': re.compile(r'\b(?:birthday|born on|birth date)\s*:?\s*(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)', re.IGNORECASE),
    }
    
    @classmethod
    def luhn_checksum(cls, card_num: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        def digits_of(n: str) -> List[int]:
            return [int(d) for d in n]
        
        digits = digits_of(card_num.replace(' ', '').replace('-', ''))
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(str(d*2)))
        return checksum % 10 == 0
    
    @classmethod
    def detect_pii(cls, text: str, include_names: bool = True) -> List[PIIMatch]:
        """Detect PII entities in text.
        
        Args:
            text: Text to scan
            include_names: Whether to detect common names
            
        Returns:
            List of detected PII matches
        """
        matches = []
        
        # Detect structured PII
        for pii_type, pattern in cls.PATTERNS.items():
            for match in pattern.finditer(text):
                confidence = 1.0
                
                # Validate credit cards with Luhn
                if pii_type == 'credit_card':
                    if not cls.luhn_checksum(match.group()):
                        continue
                
                # Validate IP addresses (basic range check)
                if pii_type == 'ip_address':
                    parts = match.group().split('.')
                    if not all(0 <= int(part) <= 255 for part in parts):
                        continue
                
                matches.append(PIIMatch(
                    type=pii_type,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                ))
        
        # Detect chat-specific patterns
        for pattern_name, pattern in cls.CHAT_PATTERNS.items():
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    type=pattern_name,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8,
                ))
        
        # Detect common names (if enabled)
        if include_names:
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            for word in words:
                word_lower = word.lower()
                if (word_lower in cls.COMMON_NAMES['first_names']['male'] or
                    word_lower in cls.COMMON_NAMES['first_names']['female'] or
                    word_lower in cls.COMMON_NAMES['last_names']):
                    
                    # Find position in text
                    start_pos = text.find(word)
                    if start_pos != -1:
                        matches.append(PIIMatch(
                            type='common_name',
                            text=word,
                            start=start_pos,
                            end=start_pos + len(word),
                            confidence=0.7,
                        ))
        
        # Sort matches by position and remove overlaps
        matches.sort(key=lambda x: x.start)
        return cls._remove_overlapping_matches(matches)
    
    @classmethod
    def _remove_overlapping_matches(cls, matches: List[PIIMatch]) -> List[PIIMatch]:
        """Remove overlapping matches, keeping higher confidence ones."""
        if not matches:
            return matches
        
        filtered = [matches[0]]
        for match in matches[1:]:
            # Check if this match overlaps with the last filtered match
            last_match = filtered[-1]
            if match.start < last_match.end:
                # Overlapping - keep the higher confidence one
                if match.confidence > last_match.confidence:
                    filtered[-1] = match
            else:
                filtered.append(match)
        
        return filtered


class HardFailDetector:
    """Detector for content that should never be processed."""
    
    # Simplified patterns for demo - in production would use specialized classifiers
    HARD_FAIL_PATTERNS = {
        'explicit_violence': [
            r'\b(?:kill|murder|hurt|harm)\s+(?:someone|people|kids|children)',
            r'\b(?:bomb|explosive|weapon)\s+(?:making|building|creating)',
        ],
        'illegal_drugs': [
            r'\b(?:selling|buying|dealing)\s+(?:cocaine|heroin|meth|drugs)',
            r'\b(?:drug deal|trafficking|smuggling)',
        ],
        'csam_indicators': [
            r'\b(?:child|kid|minor)\s+(?:inappropriate|sexual|explicit)',
            r'\b(?:underage|illegal)\s+(?:content|material|images)',
        ],
    }
    
    @classmethod
    def detect_hard_fail_classes(cls, text: str) -> List[str]:
        """Detect hard-fail content classes.
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected hard-fail classes
        """
        detected_classes = []
        text_lower = text.lower()
        
        for class_name, patterns in cls.HARD_FAIL_PATTERNS.items():
            for pattern_str in patterns:
                if re.search(pattern_str, text_lower, re.IGNORECASE):
                    detected_classes.append(class_name)
                    break  # One match per class is enough
        
        return detected_classes


class ConsistentTokenizer:
    """Consistent tokenization for pseudonymization."""
    
    def __init__(self, salt: Optional[str] = None):
        """Initialize tokenizer.
        
        Args:
            salt: Salt for hashing, generates random if None
        """
        self.salt = salt or self._generate_salt()
        self.mapping: Dict[str, str] = {}
    
    def _generate_salt(self) -> str:
        """Generate a random salt."""
        import secrets
        return secrets.token_hex(16)
    
    def tokenize_pii(self, text: str, pii_type: str) -> str:
        """Tokenize PII consistently.
        
        Args:
            text: Original PII text
            pii_type: Type of PII
            
        Returns:
            Consistent token
        """
        # Create cache key
        cache_key = f"{pii_type}:{text}"
        
        if cache_key not in self.mapping:
            # Generate consistent hash
            hash_input = f"{text}:{pii_type}:{self.salt}"
            hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
            self.mapping[cache_key] = f"⟦TKN:{pii_type.upper()}:{hash_value}⟧"
        
        return self.mapping[cache_key]
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """Get tokenization statistics."""
        type_counts = {}
        for key in self.mapping:
            pii_type = key.split(':')[0]
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1
        
        return {
            'total_tokens': len(self.mapping),
            'types': type_counts,
            'salt_hash': hashlib.sha256(self.salt.encode()).hexdigest()[:12],
        }