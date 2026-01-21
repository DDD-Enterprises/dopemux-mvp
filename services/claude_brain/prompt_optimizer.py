"""
Prompt Optimizer - Advanced prompt optimization with meta-prompting

This module implements meta-prompting techniques for self-improving prompts,
including chain-of-thought reasoning, few-shot learning, and dynamic ADHD formatting.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from .brain_manager import ClaudeBrainManager, ClaudeBrainRequest, ClaudeBrainResponse

logger = logging.getLogger(__name__)


@dataclass
class PromptAnalysis:
    """Analysis results for a prompt."""
    clarity_score: float  # 0.0-1.0
    specificity_score: float  # 0.0-1.0
    adhd_friendliness: float  # 0.0-1.0
    overall_quality: float  # 0.0-1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class OptimizedPrompt:
    """Result of prompt optimization."""
    original_prompt: str
    optimized_prompt: str
    analysis: PromptAnalysis
    improvements_made: List[str]
    optimization_level: str  # basic, intermediate, advanced
    meta_prompt_used: str
    confidence_score: float  # 0.0-1.0


@dataclass
class FewShotExample:
    """Few-shot learning example."""
    input_prompt: str
    optimized_prompt: str
    improvement_type: str
    success_score: float  # 0.0-1.0
    context: str = ""


class PromptOptimizer:
    """
    Advanced prompt optimizer with meta-prompting capabilities.

    Implements the generate/critique/evolve cycle for self-improving prompts,
    with chain-of-thought reasoning, few-shot learning, and ADHD optimizations.
    """

    def __init__(self, brain_manager: ClaudeBrainManager):
        self.brain_manager = brain_manager

        # Few-shot learning database
        self.few_shot_examples = self._initialize_few_shot_examples()

        # Meta-prompt templates
        self.meta_prompts = self._initialize_meta_prompts()

        # Performance tracking
        self.optimization_count = 0
        self.avg_improvement = 0.0
        self.success_rate = 0.0

    def _initialize_few_shot_examples(self) -> List[FewShotExample]:
        """Initialize few-shot learning examples."""
        return [
            FewShotExample(
                input_prompt="Write code for a login form",
                optimized_prompt="Create a secure, accessible login form component with the following requirements:\n\n🎯 Core Requirements:\n- Email/password input fields with validation\n- Remember me checkbox\n- Login button with loading state\n- Error message display\n\n🛡️ Security Features:\n- Input sanitization\n- CSRF protection\n- Rate limiting consideration\n\n♿ Accessibility Features:\n- ARIA labels\n- Keyboard navigation\n- Screen reader support\n- High contrast support\n\n📱 Responsive Design:\n- Mobile-first approach\n- Touch-friendly inputs\n- Adaptive layouts\n\nProvide React/TypeScript implementation with proper error handling.",
                improvement_type="specificity_and_structure",
                success_score=0.9,
                context="UI component development"
            ),
            FewShotExample(
                input_prompt="Debug this error",
                optimized_prompt="Systematically debug this error using the following approach:\n\n🔍 Error Analysis:\n1. Error message and stack trace\n2. When does the error occur?\n3. What changed recently?\n4. Environment details\n\n🧪 Hypothesis Testing:\n1. Isolate the problematic code\n2. Create minimal reproduction case\n3. Test individual components\n4. Check dependencies and versions\n\n🔧 Debugging Steps:\n1. Add logging/debugging statements\n2. Use debugger tools\n3. Check network requests if applicable\n4. Verify data flow\n\n✅ Verification:\n1. Test the fix\n2. Ensure no regressions\n3. Document the solution\n\nProvide specific debugging steps and potential solutions.",
                improvement_type="structured_methodology",
                success_score=0.85,
                context="debugging and troubleshooting"
            ),
            FewShotExample(
                input_prompt="Optimize this database query",
                optimized_prompt="Optimize this database query using systematic performance analysis:\n\n📊 Current Query Analysis:\n- Execution plan review\n- Index usage assessment\n- Data volume impact\n- Query frequency analysis\n\n🎯 Optimization Strategies:\n1. **Index Optimization**\n   - Add missing indexes\n   - Composite index consideration\n   - Index selectivity analysis\n\n2. **Query Structure**\n   - JOIN optimization\n   - Subquery to JOIN conversion\n   - WHERE clause efficiency\n\n3. **Data Access Patterns**\n   - Pagination implementation\n   - Result limiting\n   - Selective column retrieval\n\n📈 Performance Monitoring:\n- Query execution time\n- Resource usage (CPU, memory, I/O)\n- Scalability assessment\n\nProvide optimized query with before/after performance comparison.",
                improvement_type="performance_optimization",
                success_score=0.88,
                context="database and performance"
            )
        ]

    def _initialize_meta_prompts(self) -> Dict[str, str]:
        """Initialize meta-prompt templates for different optimization levels."""
        return {
            "basic": """You are an expert prompt optimizer. Your task is to improve the given prompt to make it clearer, more specific, and more effective.

ORIGINAL PROMPT: {original_prompt}

IMPROVE this prompt by:
1. Making it more specific and actionable
2. Adding clear success criteria
3. Including relevant context or constraints
4. Using structured formatting when helpful

Provide only the improved prompt, no explanations.""",

            "intermediate": """You are an advanced prompt engineering specialist. Optimize this prompt using proven techniques.

ORIGINAL PROMPT: {original_prompt}

Apply these optimization techniques:
1. **Specificity Enhancement**: Replace vague terms with concrete requirements
2. **Context Addition**: Include relevant background, constraints, or examples
3. **Structure Improvement**: Use formatting, lists, or sections for clarity
4. **Success Criteria**: Define what constitutes a good response
5. **Cognitive Load Reduction**: Break complex requests into digestible parts

Few-shot examples for reference:
{examples}

Provide the optimized prompt with brief explanations of key improvements made.""",

            "advanced": """You are a master prompt engineer specializing in meta-prompting and self-improving AI systems.

ORIGINAL PROMPT: {original_prompt}

META-PROMPTING OPTIMIZATION:
Phase 1 - Analysis: Identify prompt weaknesses and improvement opportunities
Phase 2 - Generation: Create multiple optimized variants using different techniques
Phase 3 - Critique: Evaluate each variant for effectiveness and ADHD-friendliness
Phase 4 - Evolution: Select and refine the best approach

Optimization Techniques to Apply:
🎯 **Clarity & Precision**: Eliminate ambiguity, add specificity
🧩 **Structural Enhancement**: Use formatting, sections, visual indicators
🧠 **Cognitive Optimization**: Reduce mental load with progressive disclosure
📚 **Context Enrichment**: Add relevant examples, constraints, success criteria
🔄 **Chain-of-Thought**: Guide systematic reasoning and problem-solving

ADHD-Friendly Considerations:
- Use visual indicators (✅ ❌ ⚠️ 💡 🎯)
- Provide clear next steps
- Break complex ideas into manageable parts
- Lead with most important information

Few-shot examples:
{examples}

Generate the optimized prompt and explain the meta-prompting process used."""
        }

    async def optimize_prompt(
        self,
        prompt: str,
        optimization_level: str = "intermediate",
        user_context: Optional[Dict[str, Any]] = None
    ) -> OptimizedPrompt:
        """
        Optimize a prompt using meta-prompting and few-shot learning.

        Args:
            prompt: The original prompt to optimize
            optimization_level: basic, intermediate, or advanced
            user_context: User-specific context for personalization

        Returns:
            OptimizedPrompt with analysis and improvements
        """
        self.optimization_count += 1

        try:
            # Analyze original prompt
            analysis = await self._analyze_prompt(prompt)

            # Select relevant few-shot examples
            examples = self._select_few_shot_examples(prompt, analysis)

            # Generate meta-prompt
            meta_prompt = self._generate_meta_prompt(prompt, optimization_level, examples)

            # Execute optimization using brain manager
            brain_request = ClaudeBrainRequest(
                operation="optimize_prompt",
                prompt=meta_prompt,
                context=user_context or {},
                cognitive_load=0.3,  # Lower load for optimization tasks
                attention_state="focused",
                max_tokens=1500
            )

            response = await self.brain_manager.process_request(brain_request)

            if not response.success:
                # Fallback to basic optimization
                optimized = self._basic_optimization(prompt, analysis)
                improvements = ["Fallback to basic optimization due to processing error"]
            else:
                optimized = self._extract_optimized_prompt(response.result)
                improvements = self._extract_improvements(prompt, optimized, analysis)

            # Calculate confidence
            confidence = self._calculate_optimization_confidence(analysis, improvements)

            # Update performance metrics
            improvement_score = len(improvements) / max(len(analysis.issues), 1)
            self.avg_improvement = (self.avg_improvement + improvement_score) / 2

            return OptimizedPrompt(
                original_prompt=prompt,
                optimized_prompt=optimized,
                analysis=analysis,
                improvements_made=improvements,
                optimization_level=optimization_level,
                meta_prompt_used=meta_prompt,
                confidence_score=confidence
            )

        except Exception as e:
            logger.error(f"Prompt optimization failed: {e}")
            # Return basic optimization as fallback
            analysis = PromptAnalysis(
                clarity_score=0.5,
                specificity_score=0.5,
                adhd_friendliness=0.5,
                overall_quality=0.5,
                issues=["Optimization failed due to error"],
                suggestions=["Try again or use basic optimization"]
            )
            return OptimizedPrompt(
                original_prompt=prompt,
                optimized_prompt=self._basic_optimization(prompt, analysis),
                analysis=analysis,
                improvements_made=["Error fallback optimization"],
                optimization_level="basic",
                meta_prompt_used="Error fallback",
                confidence_score=0.3
            )

    async def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """Analyze the quality and characteristics of a prompt."""
        # Basic heuristic analysis (could be enhanced with AI)
        clarity_score = self._calculate_clarity(prompt)
        specificity_score = self._calculate_specificity(prompt)
        adhd_score = self._calculate_adhd_friendliness(prompt)

        overall_quality = (clarity_score + specificity_score + adhd_score) / 3

        issues = []
        suggestions = []
        strengths = []

        # Identify issues and suggestions
        if clarity_score < 0.6:
            issues.append("Low clarity - prompt is ambiguous or unclear")
            suggestions.append("Add specific requirements and success criteria")

        if specificity_score < 0.6:
            issues.append("Low specificity - too vague or general")
            suggestions.append("Include concrete examples, constraints, and deliverables")

        if adhd_score < 0.6:
            issues.append("Low ADHD-friendliness - may be cognitively overwhelming")
            suggestions.append("Use visual indicators, break into steps, provide clear next actions")

        # Identify strengths
        if clarity_score > 0.8:
            strengths.append("Clear and understandable")
        if specificity_score > 0.8:
            strengths.append("Specific and actionable")
        if adhd_score > 0.8:
            strengths.append("ADHD-friendly structure")

        return PromptAnalysis(
            clarity_score=clarity_score,
            specificity_score=specificity_score,
            adhd_friendliness=adhd_score,
            overall_quality=overall_quality,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths
        )

    def _calculate_clarity(self, prompt: str) -> float:
        """Calculate clarity score based on linguistic analysis."""
        # Simple heuristics for clarity
        score = 0.5  # Base score

        # Positive indicators
        if any(word in prompt.lower() for word in ["clearly", "specifically", "exactly", "precisely"]):
            score += 0.1

        # Check for action verbs
        action_verbs = ["create", "build", "implement", "design", "analyze", "optimize", "debug"]
        if any(verb in prompt.lower() for verb in action_verbs):
            score += 0.1

        # Check for structure indicators
        if any(indicator in prompt for indicator in ["•", "-", "1.", "2.", "3."]):
            score += 0.1

        # Negative indicators
        if len(prompt.split()) < 5:
            score -= 0.2  # Too short
        if prompt.count("?") > 3:
            score -= 0.1  # Too many questions

        return max(0.0, min(1.0, score))

    def _calculate_specificity(self, prompt: str) -> float:
        """Calculate specificity score."""
        score = 0.5

        # Check for specific terms
        specific_indicators = [
            "implement", "create", "build", "design", "using", "with", "including",
            "requirements", "constraints", "deadline", "specific", "exactly"
        ]

        matches = sum(1 for indicator in specific_indicators if indicator in prompt.lower())
        score += min(matches * 0.05, 0.3)

        # Check for measurable criteria
        if any(term in prompt.lower() for term in ["must", "should", "required", "needs to"]):
            score += 0.1

        # Negative indicators
        vague_words = ["good", "nice", "better", "improve", "optimize", "efficient"]
        vague_count = sum(1 for word in vague_words if word in prompt.lower())
        score -= min(vague_count * 0.05, 0.2)

        return max(0.0, min(1.0, score))

    def _calculate_adhd_friendliness(self, prompt: str) -> float:
        """Calculate ADHD-friendliness score."""
        score = 0.5

        # Positive ADHD indicators
        adhd_friendly_elements = [
            "✅", "❌", "⚠️", "💡", "🎯", "step", "first", "then", "next",
            "clearly", "simple", "easy", "quick", "break down", "step by step"
        ]

        matches = sum(1 for element in adhd_friendly_elements if element in prompt.lower())
        score += min(matches * 0.03, 0.2)

        # Structure indicators
        if "•" in prompt or "-" in prompt:
            score += 0.1
        if re.search(r'\d+\.', prompt):  # Numbered lists
            score += 0.1

        # Length consideration (not too long)
        word_count = len(prompt.split())
        if word_count < 50:
            score += 0.1
        elif word_count > 200:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _select_few_shot_examples(self, prompt: str, analysis: PromptAnalysis) -> List[FewShotExample]:
        """Select relevant few-shot examples based on prompt content and issues."""
        # Simple keyword matching for now (could be enhanced with embeddings)
        relevant_examples = []

        prompt_lower = prompt.lower()

        for example in self.few_shot_examples:
            # Match by keywords or improvement type
            if any(keyword in prompt_lower for keyword in ["code", "implement", "create", "build"]):
                if "ui" in example.context or "component" in example.context:
                    relevant_examples.append(example)
            elif any(keyword in prompt_lower for keyword in ["debug", "error", "fix", "problem"]):
                if "debugging" in example.context:
                    relevant_examples.append(example)
            elif any(keyword in prompt_lower for keyword in ["optimize", "performance", "database", "query"]):
                if "database" in example.context or "performance" in example.context:
                    relevant_examples.append(example)

        # Return top 2 most relevant examples
        return relevant_examples[:2]

    def _generate_meta_prompt(self, original_prompt: str, level: str, examples: List[FewShotExample]) -> str:
        """Generate meta-prompt for optimization."""
        template = self.meta_prompts.get(level, self.meta_prompts["intermediate"])

        # Format examples
        examples_text = "\n".join([
            f"- Input: '{ex.input_prompt}'\n  Output: '{ex.optimized_prompt[:200]}...'\n  Type: {ex.improvement_type}"
            for ex in examples
        ])

        return template.format(
            original_prompt=original_prompt,
            examples=examples_text
        )

    def _extract_optimized_prompt(self, response: str) -> str:
        """Extract the optimized prompt from the AI response."""
        # Simple extraction - look for content after common markers
        markers = ["OPTIMIZED PROMPT:", "IMPROVED PROMPT:", "Here is the optimized prompt:", "```"]

        for marker in markers:
            if marker in response:
                parts = response.split(marker, 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                    # Remove markdown formatting if present
                    if content.startswith("```"):
                        content = content.split("```", 2)[1] if len(content.split("```")) > 2 else content
                    return content.strip()

        # Fallback: return the response as-is if no markers found
        return response.strip()

    def _extract_improvements(self, original: str, optimized: str, analysis: PromptAnalysis) -> List[str]:
        """Extract list of improvements made."""
        improvements = []

        # Compare lengths
        orig_len = len(original.split())
        opt_len = len(optimized.split())
        if opt_len > orig_len * 1.5:
            improvements.append("Added detailed requirements and context")
        elif opt_len < orig_len * 0.7:
            improvements.append("Condensed and clarified core requirements")

        # Check for structure additions
        if ("•" in optimized or "-" in optimized) and ("•" not in original and "-" not in original):
            improvements.append("Added structured formatting with bullet points")

        if re.search(r'\d+\.', optimized) and not re.search(r'\d+\.', original):
            improvements.append("Added numbered steps or requirements")

        # Check for ADHD-friendly elements
        adhd_elements = ["✅", "❌", "⚠️", "💡", "🎯", "🎯", "First", "Then", "Next"]
        added_adhd = any(elem in optimized and elem not in original for elem in adhd_elements)
        if added_adhd:
            improvements.append("Added ADHD-friendly visual indicators and structure")

        # Check for specificity improvements
        if analysis.specificity_score < 0.7 and "requirements" in optimized.lower():
            improvements.append("Added specific requirements and success criteria")

        # Default improvement if nothing specific detected
        if not improvements:
            improvements.append("Enhanced clarity and structure")

        return improvements

    def _basic_optimization(self, prompt: str, analysis: PromptAnalysis) -> str:
        """Basic optimization as fallback."""
        optimized = prompt

        # Add structure if missing
        if "•" not in optimized and len(optimized.split()) > 20:
            # Break into bullet points
            sentences = re.split(r'[.!?]+', optimized)
            optimized = "• " + "\n• ".join([s.strip() for s in sentences if s.strip()])

        # Add success criteria if missing
        if "should" not in optimized.lower() and "must" not in optimized.lower():
            optimized += "\n\nSuccess Criteria:\n• Deliver working, tested code\n• Include clear documentation\n• Follow best practices"

        return optimized

    def _calculate_optimization_confidence(self, analysis: PromptAnalysis, improvements: List[str]) -> float:
        """Calculate confidence score for the optimization."""
        base_confidence = 0.5

        # Higher confidence for more improvements
        base_confidence += min(len(improvements) * 0.1, 0.3)

        # Higher confidence for addressing major issues
        if analysis.overall_quality < 0.6 and len(improvements) > 2:
            base_confidence += 0.2

        # Lower confidence for basic optimizations
        if len(improvements) == 1 and "basic" in improvements[0].lower():
            base_confidence -= 0.2

        return max(0.1, min(1.0, base_confidence))

    async def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics and performance metrics."""
        return {
            "total_optimizations": self.optimization_count,
            "average_improvement_score": round(self.avg_improvement, 2),
            "few_shot_examples_count": len(self.few_shot_examples),
            "active_meta_prompts": len(self.meta_prompts),
            "performance_metrics": {
                "success_rate": round(self.success_rate, 2),
                "avg_improvement": round(self.avg_improvement, 2)
            }
        }