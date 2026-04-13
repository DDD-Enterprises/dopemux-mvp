"""
Decision extractor for identifying decisions, conclusions, and consensus points in conversations.
"""

import re
from typing import Dict, List, Any
from datetime import datetime
from .base_extractor import BaseExtractor, ExtractedField


class DecisionExtractor(BaseExtractor):
    """
    Extracts decisions, conclusions, and consensus points from conversation data.

    Identifies:
    - Explicit decisions and conclusions
    - Consensus points and agreements
    - Action items and next steps
    - Decision rationale and context
    - Stakeholders involved in decisions
    """

    def _define_patterns(self) -> List[str]:
        """Define regex patterns for decision identification."""
        return [
            # Explicit decision statements
            r'(?:we|i|team|let\'s)\s+(?:decided?|chose|conclude[ds]?|determine[ds]?|settle[ds]?)\s+(?:to|that|on)\s+([^.!?]+)',
            r'(?:decision|conclusion)\s*:\s*([^.!?]+)',
            r'(?:it\'s|we\'re)\s+(?:decided|agreed|settled)\s+(?:that|to)\s+([^.!?]+)',

            # Agreement and consensus
            r'(?:agreed|consensus|unanimous|all agreed)\s+(?:that|to|on)\s+([^.!?]+)',
            r'(?:everyone|all|we all)\s+(?:agrees?|agreed)\s+(?:that|to|on)\s+([^.!?]+)',
            r'(?:final|final decision|final call)\s*:\s*([^.!?]+)',

            # Action decisions
            r'(?:we|i|team)\s+(?:will|should|must|need to|have to)\s+([^.!?]+)',
            r'(?:going forward|moving forward|from now on),?\s+([^.!?]+)',
            r'(?:next steps?|action items?)\s*:\s*([^.!?]+)',

            # Approval and authorization
            r'(?:approved|authorized|signed off on|greenlit)\s+([^.!?]+)',
            r'(?:go ahead|proceed|move forward)\s+with\s+([^.!?]+)',
            r'(?:recommendation|propose[ds]?)\s*:\s*([^.!?]+)',

            # Resolution and finalization
            r'(?:resolved|closed|finalized?|settled)\s+(?:that|to|on)\s+([^.!?]+)',
            r'(?:outcome|result|resolution)\s*:\s*([^.!?]+)',
            r'(?:ruling|verdict|judgment)\s*:\s*([^.!?]+)',

            # Rejection decisions
            r'(?:rejected|declined|turned down|said no to)\s+([^.!?]+)',
            r'(?:not going|won\'t|will not)\s+(?:with|forward with)\s+([^.!?]+)',
        ]

    def _define_keywords(self) -> List[str]:
        """Define keywords that indicate decision-related content."""
        return [
            # Decision verbs
            'decide', 'decided', 'decision', 'choose', 'chose', 'choice',
            'conclude', 'concluded', 'conclusion', 'determine', 'determined',
            'settle', 'settled', 'resolve', 'resolved', 'finalize', 'finalized',

            # Agreement terms
            'agree', 'agreed', 'agreement', 'consensus', 'unanimous',
            'approve', 'approved', 'approval', 'authorize', 'authorized',
            'confirm', 'confirmed', 'confirmation', 'accept', 'accepted',

            # Action terms
            'will', 'should', 'must', 'need to', 'have to', 'going to',
            'next steps', 'action items', 'moving forward', 'going forward',

            # Resolution terms
            'outcome', 'result', 'resolution', 'ruling', 'verdict',
            'final', 'finalized', 'closed', 'complete', 'done',

            # Rejection terms
            'reject', 'rejected', 'decline', 'declined', 'refuse', 'refused',
            'no', 'not going', 'won\'t', 'cancel', 'cancelled',
        ]

    def extract_from_chunk(self, chunk: Dict[str, Any]) -> List[ExtractedField]:
        """Extract decision-related fields from a conversation chunk."""
        content = chunk.get('content', '')
        if not content:
            return []

        content = self._preprocess_text(content)
        extracted_fields = []

        # Find pattern matches
        pattern_matches = self._find_pattern_matches(content)
        keyword_matches = self._find_keyword_matches(content)

        # Extract decisions based on patterns
        for match_info in pattern_matches:
            decision_text = match_info['match']
            decision_content = match_info.get('groups', [''])[0] if match_info.get('groups') else decision_text

            # Extract context around the decision
            context = self._extract_context(
                content,
                match_info['start'],
                match_info['end'],
                window_size=150
            )

            # Calculate confidence based on patterns and keywords
            confidence = self._calculate_confidence(
                decision_text,
                [match_info['pattern']] + keyword_matches,
                context
            )

            # Extract stakeholders involved
            stakeholders = self._extract_stakeholders(context)

            # Determine decision type and extract metadata
            decision_metadata = self._analyze_decision_metadata(decision_text, context)

            field = ExtractedField(
                field_type='decision',
                content=decision_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=decision_metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=stakeholders,
                relationships=self._extract_decision_relationships(content, decision_text)
            )

            extracted_fields.append(field)

        # Extract high-confidence keyword-based decisions
        if keyword_matches and not pattern_matches:
            sentences = self._split_sentences(content)
            for sentence in sentences:
                sentence_keywords = self._find_keyword_matches(sentence)
                if len(sentence_keywords) >= 2:  # Multiple decision indicators
                    confidence = self._calculate_confidence(sentence, sentence_keywords)
                    if confidence >= 0.5:  # Only high-confidence keyword matches
                        stakeholders = self._extract_stakeholders(sentence)
                        metadata = self._analyze_decision_metadata(sentence, content)

                        field = ExtractedField(
                            field_type='decision',
                            content=sentence.strip(),
                            confidence=confidence,
                            context=content[:200] + '...' if len(content) > 200 else content,
                            source_chunk_id=chunk.get('id'),
                            metadata=metadata,
                            timestamp=chunk.get('timestamp'),
                            stakeholders=stakeholders,
                            relationships=[]
                        )
                        extracted_fields.append(field)

        return extracted_fields

    def _analyze_decision_metadata(self, decision_text: str, context: str) -> Dict[str, Any]:
        """Analyze decision text to extract metadata."""
        metadata = {
            'decision_type': self._classify_decision_type(decision_text),
            'urgency': self._extract_urgency(decision_text + ' ' + context),
            'scope': self._extract_scope(decision_text + ' ' + context),
            'rationale': self._extract_rationale(context),
            'alternatives': self._extract_alternatives(context),
            'risks': self._extract_decision_risks(context),
            'dependencies': self._extract_dependencies(context)
        }
        return metadata

    def _classify_decision_type(self, text: str) -> str:
        """Classify the type of decision."""
        text_lower = text.lower()

        # Technical decisions
        if any(term in text_lower for term in ['api', 'database', 'architecture', 'framework', 'library', 'tech']):
            return 'technical'

        # Business decisions
        if any(term in text_lower for term in ['business', 'strategy', 'market', 'customer', 'revenue', 'budget']):
            return 'business'

        # Process decisions
        if any(term in text_lower for term in ['process', 'workflow', 'procedure', 'method', 'approach']):
            return 'process'

        # Resource decisions
        if any(term in text_lower for term in ['hire', 'budget', 'resource', 'team', 'staff', 'allocation']):
            return 'resource'

        # Timeline decisions
        if any(term in text_lower for term in ['deadline', 'timeline', 'schedule', 'milestone', 'release']):
            return 'timeline'

        return 'general'

    def _extract_urgency(self, text: str) -> str:
        """Extract urgency level from decision context."""
        text_lower = text.lower()

        if any(term in text_lower for term in ['urgent', 'asap', 'immediately', 'critical', 'emergency']):
            return 'high'
        elif any(term in text_lower for term in ['soon', 'quickly', 'priority', 'important']):
            return 'medium'
        elif any(term in text_lower for term in ['eventually', 'future', 'later', 'when possible']):
            return 'low'
        else:
            return 'normal'

    def _extract_scope(self, text: str) -> str:
        """Extract the scope/impact of the decision."""
        text_lower = text.lower()

        if any(term in text_lower for term in ['entire', 'all', 'company', 'organization', 'global']):
            return 'organization'
        elif any(term in text_lower for term in ['team', 'department', 'group', 'project']):
            return 'team'
        elif any(term in text_lower for term in ['individual', 'personal', 'my', 'i will']):
            return 'individual'
        else:
            return 'project'

    def _extract_rationale(self, context: str) -> List[str]:
        """Extract reasoning behind the decision."""
        rationale_patterns = [
            r'because\s+([^.!?]+)',
            r'due to\s+([^.!?]+)',
            r'since\s+([^.!?]+)',
            r'given that\s+([^.!?]+)',
            r'rationale\s*:\s*([^.!?]+)',
            r'reasoning\s*:\s*([^.!?]+)',
        ]

        rationales = []
        for pattern in rationale_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            rationales.extend(matches)

        return [r.strip() for r in rationales if r.strip()]

    def _extract_alternatives(self, context: str) -> List[str]:
        """Extract alternative options that were considered."""
        alternative_patterns = [
            r'(?:alternative|option|choice)\s*:\s*([^.!?]+)',
            r'(?:could also|alternatively|instead)\s+([^.!?]+)',
            r'(?:other options?|alternatives?)\s+(?:include|are)\s+([^.!?]+)',
        ]

        alternatives = []
        for pattern in alternative_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            alternatives.extend(matches)

        return [a.strip() for a in alternatives if a.strip()]

    def _extract_decision_risks(self, context: str) -> List[str]:
        """Extract risks associated with the decision."""
        risk_patterns = [
            r'risk\s*:\s*([^.!?]+)',
            r'concern\s*:\s*([^.!?]+)',
            r'downside\s*:\s*([^.!?]+)',
            r'(?:might|could|may)\s+(?:cause|lead to|result in)\s+([^.!?]+)',
        ]

        risks = []
        for pattern in risk_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            risks.extend(matches)

        return [r.strip() for r in risks if r.strip()]

    def _extract_dependencies(self, context: str) -> List[str]:
        """Extract dependencies for the decision implementation."""
        dependency_patterns = [
            r'depends on\s+([^.!?]+)',
            r'requires?\s+([^.!?]+)',
            r'needs?\s+([^.!?]+)',
            r'prerequisite\s*:\s*([^.!?]+)',
            r'first we need\s+([^.!?]+)',
        ]

        dependencies = []
        for pattern in dependency_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            dependencies.extend(matches)

        return [d.strip() for d in dependencies if d.strip()]

    def _extract_decision_relationships(self, content: str, decision_text: str) -> List[Dict[str, Any]]:
        """Extract relationships to other decisions or entities."""
        relationships = []

        # Look for references to other decisions
        reference_patterns = [
            r'(?:related to|builds on|follows from)\s+([^.!?]+)',
            r'(?:reverses|overrides|replaces)\s+([^.!?]+)',
            r'(?:similar to|like)\s+([^.!?]+)',
        ]

        for pattern in reference_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                relationships.append({
                    'type': 'references',
                    'target': match.strip(),
                    'relationship': pattern.split(r'\s+')[0].strip('(?:')
                })

        return relationships