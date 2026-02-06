"""
Critique Analyzer - Multi-dimensional prompt quality assessment

This module provides comprehensive analysis of prompt quality across multiple
dimensions including clarity, specificity, ADHD-friendliness, and overall effectiveness.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple

from .prompt_optimizer import PromptAnalysis


class CritiqueAnalyzer:
    """
    Advanced prompt critique and analysis system.

    Provides detailed quality assessment with scoring, suggestions,
    and improvement recommendations across multiple dimensions.
    """

    def __init__(self):
        # Quality thresholds
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.75,
            'fair': 0.6,
            'poor': 0.4
        }

        # Critique dimensions
        self.dimensions = {
            'clarity': self._analyze_clarity,
            'specificity': self._analyze_specificity,
            'adhd_friendliness': self._analyze_adhd_friendliness,
            'structure': self._analyze_structure,
            'context': self._analyze_context,
            'actionability': self._analyze_actionability
        }

    async def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """
        Perform comprehensive prompt analysis.

        Args:
            prompt: The prompt to analyze

        Returns:
            Detailed PromptAnalysis with scores and recommendations
        """
        scores = {}
        all_issues = []
        all_suggestions = []
        all_strengths = []

        # Analyze each dimension
        for dimension, analyzer in self.dimensions.items():
            score, issues, suggestions, strengths = await analyzer(prompt)
            scores[dimension] = score
            all_issues.extend(issues)
            all_suggestions.extend(suggestions)
            all_strengths.extend(strengths)

        # Calculate overall quality (weighted average)
        weights = {
            'clarity': 0.2,
            'specificity': 0.25,
            'adhd_friendliness': 0.2,
            'structure': 0.15,
            'context': 0.1,
            'actionability': 0.1
        }

        overall_quality = sum(scores[dim] * weights[dim] for dim in scores)

        # Convert to legacy format for compatibility
        return PromptAnalysis(
            clarity_score=scores.get('clarity', 0.5),
            specificity_score=scores.get('specificity', 0.5),
            adhd_friendliness=scores.get('adhd_friendliness', 0.5),
            overall_quality=overall_quality,
            issues=all_issues[:5],  # Limit to top 5
            suggestions=all_suggestions[:5],  # Limit to top 5
            strengths=all_strengths[:3]  # Limit to top 3
        )

    async def _analyze_clarity(self, prompt: str) -> Tuple[float, List[str], List[str], List[str]]:
        """Analyze prompt clarity."""
        score = 0.5
        issues = []
        suggestions = []
        strengths = []

        # Check for clear action verbs
        action_verbs = ['create', 'build', 'implement', 'design', 'analyze', 'optimize']
        has_actions = any(verb in prompt.lower() for verb in action_verbs)

        if has_actions:
            score += 0.2
            strengths.append("Contains clear action verbs")
        else:
            issues.append("Missing clear action verbs")
            suggestions.append("Add specific action words like 'create', 'implement', 'analyze'")

        # Check for ambiguous terms
        ambiguous_terms = ['good', 'nice', 'efficient', 'better', 'improve']
        ambiguous_count = sum(1 for term in ambiguous_terms if term in prompt.lower())

        if ambiguous_count > 2:
            score -= 0.2
            issues.append("Contains ambiguous subjective terms")
            suggestions.append("Replace vague terms with specific, measurable criteria")

        # Check sentence structure
        sentences = re.split(r'[.!?]+', prompt)
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)

        if avg_length > 25:
            score -= 0.1
            issues.append("Sentences are too long and complex")
            suggestions.append("Break long sentences into shorter, clearer statements")

        return max(0.0, min(1.0, score)), issues, suggestions, strengths

    async def _analyze_specificity(self, prompt: str) -> Tuple[float, List[str], List[str], List[str]]:
        """Analyze prompt specificity."""
        score = 0.5
        issues = []
        suggestions = []
        strengths = []

        # Check for specific requirements
        specific_indicators = ['must', 'should', 'required', 'exactly', 'specific']
        specificity_count = sum(1 for ind in specific_indicators if ind in prompt.lower())

        score += min(specificity_count * 0.1, 0.3)

        if specificity_count >= 2:
            strengths.append("Contains specific requirements")
        elif specificity_count == 0:
            issues.append("Lacks specific requirements or constraints")
            suggestions.append("Add specific requirements like 'must include', 'should use', 'required format'")

        # Check for measurable criteria
        measurable_terms = ['percentage', 'number', 'count', 'time', 'within', 'limit']
        measurable_count = sum(1 for term in measurable_terms if term in prompt.lower())

        if measurable_count > 0:
            score += 0.1
            strengths.append("Includes measurable criteria")

        # Check for examples
        if 'example' in prompt.lower() or 'for instance' in prompt.lower():
            score += 0.1
            strengths.append("Provides examples or concrete instances")

        return max(0.0, min(1.0, score)), issues, suggestions, strengths

    async def _analyze_adhd_friendliness(self, prompt: str) -> Tuple[float, List[str], List[str], List[str]]:
        """Analyze ADHD-friendliness."""
        score = 0.5
        issues = []
        suggestions = []
        strengths = []

        # Check for visual indicators
        visual_indicators = ['✅', '❌', '⚠️', '💡', '🎯', '•', '-']
        visual_count = sum(1 for ind in visual_indicators if ind in prompt)

        if visual_count > 3:
            score += 0.2
            strengths.append("Uses visual indicators for better scanning")
        elif visual_count == 0:
            issues.append("No visual indicators for easy scanning")
            suggestions.append("Add visual cues like ✅ ❌ ⚠️ 💡 🎯 or bullet points")

        # Check for step-by-step structure
        step_indicators = ['first', 'then', 'next', 'finally', 'step 1', 'step 2']
        step_count = sum(1 for ind in step_indicators if ind in prompt.lower())

        if step_count > 1:
            score += 0.15
            strengths.append("Provides step-by-step guidance")

        # Check cognitive load
        word_count = len(prompt.split())
        if word_count > 300:
            score -= 0.2
            issues.append("Prompt is too long and may be overwhelming")
            suggestions.append("Break into shorter sections or use progressive disclosure")
        elif word_count < 50:
            score -= 0.1
            issues.append("Prompt is too brief and lacks guidance")

        # Check for encouraging language
        encouraging_terms = ['easily', 'simply', 'clearly', 'straightforward']
        encouraging_count = sum(1 for term in encouraging_terms if term in prompt.lower())

        if encouraging_count > 0:
            score += 0.1
            strengths.append("Uses encouraging and approachable language")

        return max(0.0, min(1.0, score)), issues, suggestions, strengths

    async def _analyze_structure(self, prompt: str) -> Tuple[float, List[str], List[str], List[str]]:
        """Analyze prompt structure."""
        score = 0.5
        issues = []
        suggestions = []
        strengths = []

        # Check for sections/headers
        header_patterns = [r'^[A-Z][^.!?]*:$', r'^\*\*[^*]+\*\*$', r'^### .+$']
        has_headers = any(re.search(pattern, line.strip(), re.MULTILINE)
                         for pattern in header_patterns for line in prompt.split('\n'))

        if has_headers:
            score += 0.2
            strengths.append("Well-organized with clear sections")

        # Check for lists
        list_patterns = [r'^[-*•]', r'^\d+\.']
        has_lists = any(re.search(pattern, line.strip())
                       for pattern in list_patterns for line in prompt.split('\n'))

        if has_lists:
            score += 0.15
            strengths.append("Uses structured lists for better readability")

        # Check for logical flow
        if 'first' in prompt.lower() and ('then' in prompt.lower() or 'next' in prompt.lower()):
            score += 0.1
            strengths.append("Provides logical flow and sequence")

        if not has_headers and not has_lists and len(prompt.split()) > 100:
            issues.append("Long prompt lacks structure and organization")
            suggestions.append("Add section headers and bullet points to organize content")

        return max(0.0, min(1.0, score)), issues, suggestions, strengths

    async def _analyze_context(self, prompt: str) -> Tuple[float, List[str], List[str], List[str]]:
        """Analyze context richness."""
        score = 0.5
        issues = []
        suggestions = []
        strengths = []

        # Check for technical specifications
        tech_indicators = ['python', 'javascript', 'react', 'api', 'database', 'version']
        tech_count = sum(1 for ind in tech_indicators if ind in prompt.lower())

        if tech_count > 1:
            score += 0.15
            strengths.append("Includes technical specifications")

        # Check for constraints
        constraint_indicators = ['must', 'cannot', 'limit', 'maximum', 'minimum', 'within']
        constraint_count = sum(1 for ind in constraint_indicators if ind in prompt.lower())

        if constraint_count > 0:
            score += 0.1
            strengths.append("Specifies constraints and limitations")

        # Check for success criteria
        success_indicators = ['successful', 'complete', 'deliver', 'result', 'outcome']
        success_count = sum(1 for ind in success_indicators if ind in prompt.lower())

        if success_count > 0:
            score += 0.1
            strengths.append("Defines success criteria")

        if tech_count == 0 and constraint_count == 0:
            issues.append("Lacks technical context and constraints")
            suggestions.append("Add technical specifications, platform requirements, and constraints")

        return max(0.0, min(1.0, score)), issues, suggestions, strengths

    async def _analyze_actionability(self, prompt: str) -> Tuple[float, List[str], List[str], List[str]]:
        """Analyze actionability and executability."""
        score = 0.5
        issues = []
        suggestions = []
        strengths = []

        # Check for deliverables
        deliverable_indicators = ['create', 'build', 'implement', 'provide', 'return', 'output']
        deliverable_count = sum(1 for ind in deliverable_indicators if ind in prompt.lower())

        if deliverable_count > 0:
            score += 0.15
            strengths.append("Clearly defines deliverables and outputs")

        # Check for process guidance
        process_indicators = ['step', 'first', 'then', 'finally', 'approach', 'method']
        process_count = sum(1 for ind in process_indicators if ind in prompt.lower())

        if process_count > 1:
            score += 0.15
            strengths.append("Provides process guidance and methodology")

        # Check for validation criteria
        validation_indicators = ['test', 'verify', 'validate', 'check', 'ensure']
        validation_count = sum(1 for ind in validation_indicators if ind in prompt.lower())

        if validation_count > 0:
            score += 0.1
            strengths.append("Includes validation and testing requirements")

        if deliverable_count == 0:
            issues.append("Unclear what should be delivered or produced")
            suggestions.append("Specify expected outputs, deliverables, or results")

        return max(0.0, min(1.0, score)), issues, suggestions, strengths

    def get_quality_rating(self, analysis: PromptAnalysis) -> str:
        """Get quality rating based on overall score."""
        score = analysis.overall_quality

        if score >= self.quality_thresholds['excellent']:
            return 'excellent'
        elif score >= self.quality_thresholds['good']:
            return 'good'
        elif score >= self.quality_thresholds['fair']:
            return 'fair'
        else:
            return 'poor'

    def generate_improvement_plan(self, analysis: PromptAnalysis) -> List[str]:
        """Generate prioritized improvement plan."""
        plan = []

        # Address critical issues first
        if analysis.clarity_score < 0.5:
            plan.append("🔴 CRITICAL: Improve clarity - add clear action verbs and reduce ambiguity")

        if analysis.specificity_score < 0.5:
            plan.append("🔴 CRITICAL: Increase specificity - add concrete requirements and constraints")

        if analysis.adhd_friendliness < 0.5:
            plan.append("🟡 IMPORTANT: Enhance ADHD-friendliness - add visual indicators and structure")

        # Address secondary issues
        if analysis.clarity_score < 0.7:
            plan.append("🟢 OPTIONAL: Further improve clarity with examples and precision")

        if analysis.specificity_score < 0.7:
            plan.append("🟢 OPTIONAL: Add more detailed specifications and success metrics")

        if not plan:
            plan.append("✅ EXCELLENT: Prompt quality is already high - minor refinements possible")

        return plan
