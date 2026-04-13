"""
Template selector for intelligently choosing document templates based on extracted field analysis.
"""

from typing import Dict, List, Any, Set
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class TemplateSelector:
    """
    Analyzes extracted fields to determine which document templates should be generated.

    Uses field analysis, content patterns, and business rules to make intelligent
    decisions about document generation.
    """

    def __init__(self):
        """Initialize the template selector with template criteria."""
        self.template_criteria = self._define_template_criteria()
        self.document_priorities = self._define_document_priorities()

    def _define_template_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Define criteria for each document template."""
        return {
            'prd': {
                'required_fields': ['feature'],
                'boosting_fields': ['stakeholder', 'research'],
                'min_confidence': 0.5,
                'min_field_count': 3,
                'keywords': ['requirement', 'feature', 'user story', 'acceptance criteria']
            },
            'adr': {
                'required_fields': ['decision'],
                'boosting_fields': ['constraint', 'risk'],
                'min_confidence': 0.6,
                'min_field_count': 2,
                'keywords': ['decision', 'architecture', 'technical', 'rationale']
            },
            'design_spec': {
                'required_fields': ['feature', 'decision'],
                'boosting_fields': ['constraint', 'security'],
                'min_confidence': 0.5,
                'min_field_count': 4,
                'keywords': ['design', 'architecture', 'system', 'component']
            },
            'business_plan': {
                'required_fields': ['feature', 'stakeholder'],
                'boosting_fields': ['research', 'risk'],
                'min_confidence': 0.4,
                'min_field_count': 5,
                'keywords': ['business', 'market', 'revenue', 'strategy', 'value']
            },
            'implementation_plan': {
                'required_fields': ['feature', 'decision'],
                'boosting_fields': ['constraint', 'risk'],
                'min_confidence': 0.5,
                'min_field_count': 3,
                'keywords': ['implementation', 'development', 'timeline', 'milestone']
            },
            'architecture_doc': {
                'required_fields': ['decision', 'constraint'],
                'boosting_fields': ['security', 'feature'],
                'min_confidence': 0.6,
                'min_field_count': 4,
                'keywords': ['architecture', 'system', 'component', 'infrastructure']
            },
            'security_assessment': {
                'required_fields': ['security'],
                'boosting_fields': ['risk', 'constraint'],
                'min_confidence': 0.7,
                'min_field_count': 2,
                'keywords': ['security', 'threat', 'vulnerability', 'compliance']
            },
            'risk_register': {
                'required_fields': ['risk'],
                'boosting_fields': ['constraint', 'security'],
                'min_confidence': 0.6,
                'min_field_count': 2,
                'keywords': ['risk', 'mitigation', 'threat', 'impact']
            },
            'stakeholder_map': {
                'required_fields': ['stakeholder'],
                'boosting_fields': ['decision', 'feature'],
                'min_confidence': 0.5,
                'min_field_count': 3,
                'keywords': ['stakeholder', 'role', 'responsibility', 'owner']
            },
            'research_summary': {
                'required_fields': ['research'],
                'boosting_fields': ['feature', 'decision'],
                'min_confidence': 0.5,
                'min_field_count': 2,
                'keywords': ['research', 'analysis', 'finding', 'data', 'study']
            }
        }

    def _define_document_priorities(self) -> Dict[str, int]:
        """Define priority scores for document types (higher = more important)."""
        return {
            'prd': 100,           # Always generate if criteria met
            'adr': 90,            # High priority for decision tracking
            'design_spec': 80,    # Important for technical implementation
            'security_assessment': 85,  # High priority for security
            'risk_register': 75,  # Important for risk management
            'implementation_plan': 70,  # Useful for project management
            'architecture_doc': 60,     # Good for system understanding
            'business_plan': 50,  # Lower priority, more optional
            'stakeholder_map': 40,      # Useful but not critical
            'research_summary': 30      # Lowest priority
        }

    def select_templates(self, extracted_fields: List[Dict[str, Any]],
                        max_documents: int = 6) -> List[str]:
        """
        Select appropriate document templates based on extracted fields.

        Args:
            extracted_fields: List of extracted field dictionaries
            max_documents: Maximum number of documents to generate

        Returns:
            List of template names to generate
        """
        logger.info(f"Analyzing {len(extracted_fields)} extracted fields for template selection")

        # Analyze field composition
        field_analysis = self._analyze_field_composition(extracted_fields)

        # Score each template
        template_scores = self._score_templates(field_analysis, extracted_fields)

        # Select templates based on scores and priorities
        selected_templates = self._select_top_templates(
            template_scores,
            max_documents
        )

        logger.info(f"Selected templates: {selected_templates}")
        return selected_templates

    def _analyze_field_composition(self, extracted_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the composition and patterns of extracted fields."""
        analysis = {
            'field_counts': Counter(),
            'confidence_by_type': {},
            'total_fields': len(extracted_fields),
            'content_keywords': Counter()
        }

        for field_dict in extracted_fields:
            field_type = field_dict.get('field_type', 'unknown')
            confidence = field_dict.get('confidence', 0.0)
            content = field_dict.get('content', '').lower()

            # Count field types
            analysis['field_counts'][field_type] += 1

            # Track confidence by type
            if field_type not in analysis['confidence_by_type']:
                analysis['confidence_by_type'][field_type] = []
            analysis['confidence_by_type'][field_type].append(confidence)

            # Extract keywords from content
            words = content.split()
            for word in words:
                if len(word) > 3:  # Filter short words
                    analysis['content_keywords'][word] += 1

        # Calculate average confidence by type
        for field_type, confidences in analysis['confidence_by_type'].items():
            analysis['confidence_by_type'][field_type] = sum(confidences) / len(confidences)

        return analysis

    def _score_templates(self, field_analysis: Dict[str, Any],
                        extracted_fields: List[Dict[str, Any]]) -> Dict[str, float]:
        """Score each template based on field analysis."""
        template_scores = {}

        for template_name, criteria in self.template_criteria.items():
            score = self._calculate_template_score(
                template_name,
                criteria,
                field_analysis,
                extracted_fields
            )
            template_scores[template_name] = score

        return template_scores

    def _calculate_template_score(self, template_name: str, criteria: Dict[str, Any],
                                 field_analysis: Dict[str, Any],
                                 extracted_fields: List[Dict[str, Any]]) -> float:
        """Calculate score for a specific template."""
        score = 0.0

        # Check required fields
        required_score = self._check_required_fields(criteria, field_analysis)
        if required_score == 0:
            return 0.0  # Cannot generate without required fields

        score += required_score * 40  # 40% weight for required fields

        # Check boosting fields
        boosting_score = self._check_boosting_fields(criteria, field_analysis)
        score += boosting_score * 20  # 20% weight for boosting fields

        # Check confidence levels
        confidence_score = self._check_confidence_levels(criteria, field_analysis)
        score += confidence_score * 15  # 15% weight for confidence

        # Check field count
        count_score = self._check_field_count(criteria, field_analysis)
        score += count_score * 10  # 10% weight for field count

        # Check keyword presence
        keyword_score = self._check_keyword_presence(criteria, field_analysis)
        score += keyword_score * 10  # 10% weight for keywords

        # Add priority bonus
        priority = self.document_priorities.get(template_name, 0)
        score += (priority / 100) * 5  # 5% weight for priority

        logger.debug(f"Template {template_name} scored: {score:.2f}")
        return score

    def _check_required_fields(self, criteria: Dict[str, Any],
                             field_analysis: Dict[str, Any]) -> float:
        """Check if required fields are present."""
        required_fields = criteria.get('required_fields', [])
        field_counts = field_analysis['field_counts']

        present_count = sum(1 for field in required_fields if field_counts.get(field, 0) > 0)
        return present_count / len(required_fields) if required_fields else 1.0

    def _check_boosting_fields(self, criteria: Dict[str, Any],
                             field_analysis: Dict[str, Any]) -> float:
        """Check for presence of boosting fields."""
        boosting_fields = criteria.get('boosting_fields', [])
        if not boosting_fields:
            return 0.5  # Neutral score if no boosting fields defined

        field_counts = field_analysis['field_counts']
        present_count = sum(1 for field in boosting_fields if field_counts.get(field, 0) > 0)
        return present_count / len(boosting_fields)

    def _check_confidence_levels(self, criteria: Dict[str, Any],
                               field_analysis: Dict[str, Any]) -> float:
        """Check if confidence levels meet criteria."""
        min_confidence = criteria.get('min_confidence', 0.5)
        confidence_by_type = field_analysis['confidence_by_type']

        if not confidence_by_type:
            return 0.0

        avg_confidence = sum(confidence_by_type.values()) / len(confidence_by_type)
        return min(avg_confidence / min_confidence, 1.0)

    def _check_field_count(self, criteria: Dict[str, Any],
                         field_analysis: Dict[str, Any]) -> float:
        """Check if field count meets minimum requirements."""
        min_field_count = criteria.get('min_field_count', 1)
        total_fields = field_analysis['total_fields']

        return min(total_fields / min_field_count, 1.0)

    def _check_keyword_presence(self, criteria: Dict[str, Any],
                              field_analysis: Dict[str, Any]) -> float:
        """Check for presence of relevant keywords in content."""
        keywords = criteria.get('keywords', [])
        if not keywords:
            return 0.5  # Neutral score if no keywords defined

        content_keywords = field_analysis['content_keywords']

        keyword_matches = sum(1 for keyword in keywords
                            if any(keyword in content_word
                                 for content_word in content_keywords))

        return min(keyword_matches / len(keywords), 1.0)

    def _select_top_templates(self, template_scores: Dict[str, float],
                            max_documents: int) -> List[str]:
        """Select top-scoring templates up to max_documents limit."""
        # Filter out templates with zero scores
        valid_templates = {name: score for name, score in template_scores.items()
                         if score > 0}

        if not valid_templates:
            # Fallback to basic templates if nothing qualifies
            logger.warning("No templates met criteria, falling back to basics")
            return ['prd', 'adr']

        # Sort by score descending
        sorted_templates = sorted(valid_templates.items(),
                                key=lambda x: x[1], reverse=True)

        # Select top templates
        selected = [name for name, score in sorted_templates[:max_documents]]

        # Ensure we have at least PRD and ADR if they're available
        if 'prd' not in selected and 'prd' in valid_templates:
            selected = ['prd'] + selected
        if 'adr' not in selected and 'adr' in valid_templates:
            selected = ['adr'] + selected

        return selected[:max_documents]

    def get_template_recommendations(self, extracted_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed template recommendations with explanations."""
        field_analysis = self._analyze_field_composition(extracted_fields)
        template_scores = self._score_templates(field_analysis, extracted_fields)

        recommendations = {
            'field_summary': field_analysis,
            'template_scores': template_scores,
            'recommended_templates': self.select_templates(extracted_fields),
            'explanations': {}
        }

        # Add explanations for each template
        for template_name, score in template_scores.items():
            if score > 0:
                recommendations['explanations'][template_name] = \
                    self._generate_template_explanation(template_name, score, field_analysis)

        return recommendations

    def _generate_template_explanation(self, template_name: str, score: float,
                                     field_analysis: Dict[str, Any]) -> str:
        """Generate explanation for why a template was recommended or not."""
        criteria = self.template_criteria[template_name]
        required_fields = criteria['required_fields']
        field_counts = field_analysis['field_counts']

        explanation = f"Score: {score:.2f}/100. "

        # Check required fields
        missing_required = [field for field in required_fields
                          if field_counts.get(field, 0) == 0]

        if missing_required:
            explanation += f"Missing required fields: {', '.join(missing_required)}. "
        else:
            explanation += f"All required fields present: {', '.join(required_fields)}. "

        # Add field count info
        total_fields = field_analysis['total_fields']
        min_fields = criteria.get('min_field_count', 1)
        explanation += f"Field count: {total_fields} (min: {min_fields}). "

        return explanation