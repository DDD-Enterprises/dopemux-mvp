"""
Feature extractor for identifying features, requirements, and specifications in conversations.
"""

import re
from typing import Dict, List, Any
from datetime import datetime
from .base_extractor import BaseExtractor, ExtractedField


class FeatureExtractor(BaseExtractor):
    """
    Extracts features, requirements, and specifications from conversation data.

    Identifies:
    - Feature requests and specifications
    - User requirements and acceptance criteria
    - User stories and use cases
    - Functional and non-functional requirements
    - Feature priorities and dependencies
    """

    def _define_patterns(self) -> List[str]:
        """Define regex patterns for feature identification."""
        return [
            # Feature requests
            r'(?:feature|functionality|capability)\s*:\s*([^.!?]+)',
            r'(?:we|i|users?)\s+(?:need|want|require)\s+(?:a|an|the)?\s*([^.!?]+)',
            r'(?:should|must|will)\s+(?:be able to|have|include|support)\s+([^.!?]+)',

            # Requirements
            r'requirement\s*:\s*([^.!?]+)',
            r'(?:functional|non-functional)\s+requirement\s*:\s*([^.!?]+)',
            r'(?:system|application)\s+(?:should|must|will)\s+([^.!?]+)',

            # User stories
            r'as a\s+([^,]+),\s*i\s+(?:want|need)\s+([^.!?]+)',
            r'user story\s*:\s*([^.!?]+)',
            r'use case\s*:\s*([^.!?]+)',

            # Acceptance criteria
            r'(?:acceptance criteria|given|when|then)\s*:\s*([^.!?]+)',
            r'(?:criteria|condition)\s*:\s*([^.!?]+)',
            r'(?:verify|ensure|check)\s+that\s+([^.!?]+)',

            # Feature descriptions
            r'(?:feature|component|module)\s+(?:will|should|must)\s+([^.!?]+)',
            r'(?:implement|build|create|add)\s+(?:a|an|the)?\s*([^.!?]+)',
            r'(?:new|additional)\s+(?:feature|functionality|capability)\s+([^.!?]+)',

            # Priority indicators
            r'(?:priority|p[0-9]|critical|important|nice to have)\s*:\s*([^.!?]+)',
            r'(?:must have|should have|could have|won\'t have)\s*:\s*([^.!?]+)',

            # Technical specifications
            r'(?:api|endpoint|interface)\s+(?:should|will|must)\s+([^.!?]+)',
            r'(?:database|storage|data)\s+(?:requirements?|specs?)\s*:\s*([^.!?]+)',
            r'(?:performance|security|scalability)\s+(?:requirements?|specs?)\s*:\s*([^.!?]+)',
        ]

    def _define_keywords(self) -> List[str]:
        """Define keywords that indicate feature-related content."""
        return [
            # Feature terms
            'feature', 'functionality', 'capability', 'function', 'component',
            'module', 'system', 'application', 'tool', 'service',

            # Requirement terms
            'requirement', 'spec', 'specification', 'criteria', 'condition',
            'rule', 'constraint', 'standard', 'guideline',

            # User story terms
            'user story', 'use case', 'scenario', 'persona', 'actor',
            'user', 'customer', 'stakeholder', 'end user',

            # Action terms
            'need', 'want', 'require', 'implement', 'build', 'create',
            'add', 'develop', 'design', 'integrate', 'support',

            # Modal verbs
            'should', 'must', 'will', 'shall', 'can', 'could', 'would',
            'may', 'might', 'have to', 'need to', 'able to',

            # Priority terms
            'priority', 'critical', 'important', 'urgent', 'nice to have',
            'must have', 'should have', 'could have', 'won\'t have',
            'p0', 'p1', 'p2', 'p3', 'high', 'medium', 'low',

            # Quality attributes
            'performance', 'security', 'scalability', 'usability',
            'reliability', 'maintainability', 'availability', 'accessibility',
        ]

    def extract_from_chunk(self, chunk: Dict[str, Any]) -> List[ExtractedField]:
        """Extract feature-related fields from a conversation chunk."""
        content = chunk.get('content', '')
        if not content:
            return []

        content = self._preprocess_text(content)
        extracted_fields = []

        # Find pattern matches
        pattern_matches = self._find_pattern_matches(content)
        keyword_matches = self._find_keyword_matches(content)

        # Extract features based on patterns
        for match_info in pattern_matches:
            feature_text = match_info['match']
            feature_content = match_info.get('groups', [''])[0] if match_info.get('groups') else feature_text

            # Extract context around the feature
            context = self._extract_context(
                content,
                match_info['start'],
                match_info['end'],
                window_size=200
            )

            # Calculate confidence based on patterns and keywords
            confidence = self._calculate_confidence(
                feature_text,
                [match_info['pattern']] + keyword_matches,
                context
            )

            # Extract stakeholders involved
            stakeholders = self._extract_stakeholders(context)

            # Determine feature type and extract metadata
            feature_metadata = self._analyze_feature_metadata(feature_text, context)

            field = ExtractedField(
                field_type='feature',
                content=feature_content.strip(),
                confidence=confidence,
                context=context,
                source_chunk_id=chunk.get('id'),
                metadata=feature_metadata,
                timestamp=chunk.get('timestamp'),
                stakeholders=stakeholders,
                relationships=self._extract_feature_relationships(content, feature_text)
            )

            extracted_fields.append(field)

        # Extract high-confidence keyword-based features
        if keyword_matches and not pattern_matches:
            sentences = self._split_sentences(content)
            for sentence in sentences:
                sentence_keywords = self._find_keyword_matches(sentence)
                if len(sentence_keywords) >= 2:  # Multiple feature indicators
                    confidence = self._calculate_confidence(sentence, sentence_keywords)
                    if confidence >= 0.6:  # Higher threshold for keyword matches
                        stakeholders = self._extract_stakeholders(sentence)
                        metadata = self._analyze_feature_metadata(sentence, content)

                        field = ExtractedField(
                            field_type='feature',
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

    def _analyze_feature_metadata(self, feature_text: str, context: str) -> Dict[str, Any]:
        """Analyze feature text to extract metadata."""
        metadata = {
            'feature_type': self._classify_feature_type(feature_text),
            'priority': self._extract_priority(feature_text + ' ' + context),
            'complexity': self._estimate_complexity(feature_text + ' ' + context),
            'user_story': self._extract_user_story(context),
            'acceptance_criteria': self._extract_acceptance_criteria(context),
            'dependencies': self._extract_feature_dependencies(context),
            'technical_requirements': self._extract_technical_requirements(context),
            'business_value': self._extract_business_value(context),
            'risks': self._extract_feature_risks(context)
        }
        return metadata

    def _classify_feature_type(self, text: str) -> str:
        """Classify the type of feature."""
        text_lower = text.lower()

        # UI/UX features
        if any(term in text_lower for term in ['ui', 'ux', 'interface', 'design', 'layout', 'visual', 'display']):
            return 'ui_ux'

        # API features
        if any(term in text_lower for term in ['api', 'endpoint', 'rest', 'graphql', 'webhook', 'integration']):
            return 'api'

        # Database features
        if any(term in text_lower for term in ['database', 'db', 'storage', 'query', 'schema', 'migration']):
            return 'database'

        # Authentication/Security features
        if any(term in text_lower for term in ['auth', 'login', 'security', 'permission', 'role', 'access']):
            return 'security'

        # Business logic features
        if any(term in text_lower for term in ['business', 'logic', 'rule', 'process', 'workflow', 'calculation']):
            return 'business_logic'

        # Performance features
        if any(term in text_lower for term in ['performance', 'optimization', 'cache', 'speed', 'latency']):
            return 'performance'

        # Integration features
        if any(term in text_lower for term in ['integration', 'connect', 'sync', 'import', 'export', 'third party']):
            return 'integration'

        # Reporting features
        if any(term in text_lower for term in ['report', 'analytics', 'dashboard', 'chart', 'graph', 'metrics']):
            return 'reporting'

        return 'general'

    def _extract_priority(self, text: str) -> str:
        """Extract priority level from feature context."""
        text_lower = text.lower()

        # Explicit priority indicators
        if any(term in text_lower for term in ['p0', 'critical', 'urgent', 'must have', 'blocker']):
            return 'critical'
        elif any(term in text_lower for term in ['p1', 'high priority', 'important', 'should have']):
            return 'high'
        elif any(term in text_lower for term in ['p2', 'medium priority', 'normal', 'could have']):
            return 'medium'
        elif any(term in text_lower for term in ['p3', 'low priority', 'nice to have', 'won\'t have']):
            return 'low'

        # Implicit priority indicators
        elif any(term in text_lower for term in ['asap', 'immediately', 'right away', 'first']):
            return 'high'
        elif any(term in text_lower for term in ['later', 'future', 'eventually', 'someday']):
            return 'low'
        else:
            return 'medium'

    def _estimate_complexity(self, text: str) -> str:
        """Estimate feature complexity based on description."""
        text_lower = text.lower()

        # High complexity indicators
        if any(term in text_lower for term in [
            'complex', 'complicated', 'sophisticated', 'advanced',
            'algorithm', 'machine learning', 'ai', 'real-time',
            'distributed', 'microservice', 'architecture'
        ]):
            return 'high'

        # Low complexity indicators
        elif any(term in text_lower for term in [
            'simple', 'basic', 'straightforward', 'easy',
            'quick', 'small', 'minor', 'trivial'
        ]):
            return 'low'

        # Count technical terms as complexity indicator
        technical_terms = ['api', 'database', 'integration', 'authentication',
                          'encryption', 'optimization', 'scalability']
        tech_count = sum(1 for term in technical_terms if term in text_lower)

        if tech_count >= 3:
            return 'high'
        elif tech_count >= 1:
            return 'medium'
        else:
            return 'low'

    def _extract_user_story(self, context: str) -> Dict[str, str]:
        """Extract user story components."""
        user_story = {'persona': '', 'goal': '', 'benefit': ''}

        # Standard user story format: "As a [persona], I want [goal] so that [benefit]"
        story_pattern = r'as a\s+([^,]+),\s*i\s+(?:want|need)\s+([^,]+)(?:,?\s*so that\s+([^.!?]+))?'
        match = re.search(story_pattern, context.lower())

        if match:
            user_story['persona'] = match.group(1).strip()
            user_story['goal'] = match.group(2).strip()
            if match.group(3):
                user_story['benefit'] = match.group(3).strip()

        return user_story

    def _extract_acceptance_criteria(self, context: str) -> List[str]:
        """Extract acceptance criteria."""
        criteria_patterns = [
            r'(?:acceptance criteria|given|when|then)\s*:\s*([^.!?]+)',
            r'(?:verify|ensure|check)\s+that\s+([^.!?]+)',
            r'(?:condition|criteria)\s*:\s*([^.!?]+)',
            r'should\s+(?:be able to|have|include|support)\s+([^.!?]+)',
        ]

        criteria = []
        for pattern in criteria_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            criteria.extend(matches)

        return [c.strip() for c in criteria if c.strip()]

    def _extract_feature_dependencies(self, context: str) -> List[str]:
        """Extract dependencies for the feature."""
        dependency_patterns = [
            r'depends on\s+([^.!?]+)',
            r'requires?\s+([^.!?]+)',
            r'needs?\s+([^.!?]+)',
            r'prerequisite\s*:\s*([^.!?]+)',
            r'after\s+([^.!?]+)',
            r'once\s+([^.!?]+)',
        ]

        dependencies = []
        for pattern in dependency_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            dependencies.extend(matches)

        return [d.strip() for d in dependencies if d.strip()]

    def _extract_technical_requirements(self, context: str) -> List[str]:
        """Extract technical requirements."""
        tech_patterns = [
            r'(?:api|endpoint|interface)\s+(?:should|will|must)\s+([^.!?]+)',
            r'(?:database|storage|data)\s+(?:requirements?|specs?)\s*:\s*([^.!?]+)',
            r'(?:performance|security|scalability)\s+(?:requirements?|specs?)\s*:\s*([^.!?]+)',
            r'(?:technology|tech|framework|library)\s*:\s*([^.!?]+)',
        ]

        requirements = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            requirements.extend(matches)

        return [r.strip() for r in requirements if r.strip()]

    def _extract_business_value(self, context: str) -> List[str]:
        """Extract business value statements."""
        value_patterns = [
            r'(?:benefit|value|impact)\s*:\s*([^.!?]+)',
            r'(?:so that|because|to)\s+([^.!?]+)',
            r'(?:improve|increase|reduce|save)\s+([^.!?]+)',
            r'(?:revenue|cost|efficiency|productivity)\s+([^.!?]+)',
        ]

        values = []
        for pattern in value_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            values.extend(matches)

        return [v.strip() for v in values if v.strip()]

    def _extract_feature_risks(self, context: str) -> List[str]:
        """Extract risks associated with the feature."""
        risk_patterns = [
            r'risk\s*:\s*([^.!?]+)',
            r'concern\s*:\s*([^.!?]+)',
            r'(?:might|could|may)\s+(?:cause|lead to|break)\s+([^.!?]+)',
            r'(?:challenge|issue|problem)\s*:\s*([^.!?]+)',
        ]

        risks = []
        for pattern in risk_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            risks.extend(matches)

        return [r.strip() for r in risks if r.strip()]

    def _extract_feature_relationships(self, content: str, feature_text: str) -> List[Dict[str, Any]]:
        """Extract relationships to other features or entities."""
        relationships = []

        # Look for references to other features
        reference_patterns = [
            r'(?:extends|builds on|enhances)\s+([^.!?]+)',
            r'(?:related to|similar to|like)\s+([^.!?]+)',
            r'(?:replaces|supersedes|deprecates)\s+([^.!?]+)',
            r'(?:integrates with|connects to|works with)\s+([^.!?]+)',
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