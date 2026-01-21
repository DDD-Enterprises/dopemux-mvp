"""
Meta Prompt Generator - Self-improving prompt evolution system

This module implements the critique and evolution phases of meta-prompting,
enabling continuous improvement of prompt optimization strategies.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from .brain_manager import ClaudeBrainManager, ClaudeBrainRequest, ClaudeBrainResponse
from .prompt_optimizer import PromptAnalysis, OptimizedPrompt

logger = logging.getLogger(__name__)


@dataclass
class MetaPromptEvolution:
    """Result of meta-prompt evolution."""
    original_meta_prompt: str
    evolved_meta_prompt: str
    improvement_score: float  # 0.0-1.0
    critique_points: List[str]
    evolution_strategy: str
    confidence: float  # 0.0-1.0
    applied_improvements: List[str]


@dataclass
class PromptPerformanceData:
    """Performance data for prompt evaluation."""
    prompt_id: str
    prompt_text: str
    success_score: float  # 0.0-1.0
    user_feedback: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MetaPromptTemplate:
    """Template for meta-prompt generation."""
    name: str
    template: str
    optimization_focus: str  # clarity, specificity, adhd_friendly, structure
    success_patterns: List[str]
    failure_patterns: List[str]
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)


class MetaPromptGenerator:
    """
    Self-improving meta-prompt generator using critique and evolution cycles.

    This system analyzes prompt optimization performance and evolves meta-prompts
    to achieve better results over time through systematic improvement.
    """

    def __init__(self, brain_manager: ClaudeBrainManager):
        self.brain_manager = brain_manager

        # Performance database
        self.performance_data: List[PromptPerformanceData] = []

        # Meta-prompt templates
        self.templates = self._initialize_templates()

        # Evolution tracking
        self.evolution_history: List[MetaPromptEvolution] = []
        self.success_threshold = 0.7  # Minimum success score for "good" performance

    def _initialize_templates(self) -> Dict[str, MetaPromptTemplate]:
        """Initialize base meta-prompt templates."""
        return {
            "clarity_optimizer": MetaPromptTemplate(
                name="clarity_optimizer",
                template="""You are a prompt clarity specialist. Your task is to make prompts crystal clear and unambiguous.

ORIGINAL PROMPT: {original_prompt}

ANALYSIS REQUIREMENTS:
1. Identify ambiguous terms or vague language
2. Replace general concepts with specific requirements
3. Add concrete examples where helpful
4. Clarify success criteria and deliverables

OPTIMIZATION PRINCIPLES:
- Use precise, specific language
- Include measurable outcomes
- Remove subjective terms like "good", "nice", "efficient"
- Add context that eliminates assumptions

Provide the clarified prompt with specific improvements noted.""",
                optimization_focus="clarity",
                success_patterns=["specific requirements", "measurable outcomes", "clear deliverables"],
                failure_patterns=["vague language", "ambiguous terms", "subjective criteria"]
            ),

            "structure_enhancer": MetaPromptTemplate(
                name="structure_enhancer",
                template="""You are a prompt structure specialist. Transform prompts into well-organized, scannable formats.

ORIGINAL PROMPT: {original_prompt}

STRUCTURAL IMPROVEMENTS:
1. **Section Organization**: Break into logical sections with clear headers
2. **Visual Hierarchy**: Use bullet points, numbered lists, and formatting
3. **Progressive Disclosure**: Put essential info first, details second
4. **Actionable Steps**: Convert paragraphs into step-by-step instructions

ADHD-FRIENDLY FORMATTING:
- Use visual indicators: ✅ ❌ ⚠️ 💡 🎯
- Lead with most important information
- Break complex ideas into digestible chunks
- Provide clear next steps and success criteria

Transform the prompt into a structured, visually appealing format.""",
                optimization_focus="structure",
                success_patterns=["clear sections", "visual indicators", "numbered steps", "progressive disclosure"],
                failure_patterns=["wall of text", "no formatting", "mixed priorities", "unclear sequence"]
            ),

            "context_rich": MetaPromptTemplate(
                name="context_rich",
                template="""You are a context enrichment specialist. Add relevant background, constraints, and examples to prompts.

ORIGINAL PROMPT: {original_prompt}

CONTEXT ENHANCEMENT AREAS:
1. **Background Information**: Add relevant context about the problem domain
2. **Technical Constraints**: Include platform, framework, or system requirements
3. **Business Context**: Add user needs, success metrics, or use cases
4. **Examples**: Provide concrete examples of desired inputs/outputs

QUALITY IMPROVEMENTS:
- Include specific technologies, versions, or platforms
- Define success metrics and acceptance criteria
- Add edge cases and error handling requirements
- Specify performance, security, or usability constraints

Create a context-rich prompt that eliminates ambiguity and guides comprehensive solutions.""",
                optimization_focus="context",
                success_patterns=["specific technologies", "success metrics", "edge cases", "constraints"],
                failure_patterns=["missing requirements", "assumed knowledge", "no constraints", "unclear scope"]
            ),

            "adhd_optimizer": MetaPromptTemplate(
                name="adhd_optimizer",
                template="""You are an ADHD-friendly prompt optimization specialist. Transform prompts to reduce cognitive load and improve focus.

ORIGINAL PROMPT: {original_prompt}

ADHD OPTIMIZATION STRATEGIES:
1. **Cognitive Load Reduction**: Break complex tasks into smaller, manageable steps
2. **Attention Guidance**: Use clear visual indicators and structured navigation
3. **Progressive Disclosure**: Present essential information first, details on demand
4. **Success Path**: Provide clear next steps and decision points

FOCUS ENHANCEMENT TECHNIQUES:
- Use emojis and visual cues: ✅ ❌ ⚠️ 💡 🎯
- Start with "why" and "what" before "how"
- Limit choices and options to prevent decision paralysis
- Include time estimates and energy level guidance
- Provide gentle, encouraging language

Create a prompt optimized for ADHD-friendly execution and understanding.""",
                optimization_focus="adhd_friendly",
                success_patterns=["visual indicators", "step-by-step", "clear priorities", "encouraging tone"],
                failure_patterns=["overwhelming choices", "complex paragraphs", "unclear priorities", "harsh language"]
            )
        }

    async def generate_meta_prompt(
        self,
        optimization_focus: str,
        performance_history: Optional[List[PromptPerformanceData]] = None
    ) -> str:
        """
        Generate an optimized meta-prompt based on performance history and focus area.

        Args:
            optimization_focus: Area to optimize (clarity, structure, context, adhd_friendly)
            performance_history: Historical performance data for learning

        Returns:
            Optimized meta-prompt string
        """
        # Get base template
        template = self.templates.get(optimization_focus)
        if not template:
            # Fallback to clarity optimizer
            template = self.templates["clarity_optimizer"]

        # Analyze performance history for improvements
        if performance_history:
            improvements = await self._analyze_performance_patterns(performance_history, optimization_focus)
            evolved_template = await self._evolve_template(template, improvements)
        else:
            evolved_template = template.template

        return evolved_template

    async def evolve_meta_prompt(
        self,
        current_meta_prompt: str,
        performance_data: List[PromptPerformanceData],
        optimization_focus: str
    ) -> MetaPromptEvolution:
        """
        Evolve a meta-prompt based on performance analysis and critique.

        This implements the critique and evolution phases of meta-prompting.
        """
        try:
            # Phase 1: Analyze performance patterns
            critique_points = await self._analyze_performance_patterns(performance_data, optimization_focus)

            # Phase 2: Generate evolution strategy
            evolution_strategy = self._determine_evolution_strategy(critique_points, optimization_focus)

            # Phase 3: Create evolved prompt using AI
            evolved_prompt = await self._generate_evolved_prompt(
                current_meta_prompt,
                critique_points,
                evolution_strategy
            )

            # Phase 4: Calculate improvement score
            improvement_score = self._calculate_improvement_score(critique_points, evolved_prompt)

            # Phase 5: Validate evolution
            confidence = await self._validate_evolution(current_meta_prompt, evolved_prompt, performance_data)

            # Record evolution
            evolution = MetaPromptEvolution(
                original_meta_prompt=current_meta_prompt,
                evolved_meta_prompt=evolved_prompt,
                improvement_score=improvement_score,
                critique_points=critique_points,
                evolution_strategy=evolution_strategy,
                confidence=confidence,
                applied_improvements=self._extract_applied_improvements(critique_points, evolution_strategy)
            )

            self.evolution_history.append(evolution)
            return evolution

        except Exception as e:
            logger.error(f"Meta-prompt evolution failed: {e}")
            # Return minimal evolution as fallback
            return MetaPromptEvolution(
                original_meta_prompt=current_meta_prompt,
                evolved_meta_prompt=current_meta_prompt,
                improvement_score=0.0,
                critique_points=["Evolution failed due to error"],
                evolution_strategy="error_fallback",
                confidence=0.1,
                applied_improvements=[]
            )

    async def _analyze_performance_patterns(
        self,
        performance_data: List[PromptPerformanceData],
        focus: str
    ) -> List[str]:
        """Analyze performance patterns to identify improvement opportunities."""
        critique_points = []

        if not performance_data:
            return ["No performance data available for analysis"]

        # Calculate success metrics
        successful_prompts = [p for p in performance_data if p.success_score >= self.success_threshold]
        success_rate = len(successful_prompts) / len(performance_data)

        # Analyze common failure patterns
        failed_prompts = [p for p in performance_data if p.success_score < self.success_threshold]

        # Focus-specific analysis
        if focus == "clarity":
            # Check for ambiguity issues
            if any("ambiguous" in (p.user_feedback or "") for p in failed_prompts):
                critique_points.append("Prompts lack clarity - add specific requirements and examples")

        elif focus == "structure":
            # Check for organization issues
            if any("confusing" in (p.user_feedback or "") for p in failed_prompts):
                critique_points.append("Poor information structure - implement better visual hierarchy")

        elif focus == "context":
            # Check for context gaps
            if any("missing context" in (p.user_feedback or "") for p in failed_prompts):
                critique_points.append("Insufficient context - add domain knowledge and constraints")

        elif focus == "adhd_friendly":
            # Check for cognitive load issues
            if any("overwhelming" in (p.user_feedback or "") for p in failed_prompts):
                critique_points.append("High cognitive load - implement progressive disclosure")

        # General performance analysis
        if success_rate < 0.6:
            critique_points.append(f"Low success rate ({success_rate:.1%}) - fundamental approach needs revision")

        if len(performance_data) > 10:
            # Trend analysis
            recent_performance = performance_data[-5:]
            recent_avg = sum(p.success_score for p in recent_performance) / len(recent_performance)
            overall_avg = sum(p.success_score for p in performance_data) / len(performance_data)

            if recent_avg < overall_avg * 0.8:
                critique_points.append("Recent performance declining - adaptation needed")

        # Execution time analysis
        avg_time = sum(p.execution_time for p in performance_data if p.execution_time) / len([p for p in performance_data if p.execution_time])
        if avg_time and avg_time > 30:  # Too slow
            critique_points.append(f"High execution time ({avg_time:.1f}s) - optimize for speed")

        return critique_points if critique_points else ["Performance analysis shows strengths maintained - minor optimizations possible"]

    def _determine_evolution_strategy(self, critique_points: List[str], focus: str) -> str:
        """Determine the best evolution strategy based on critique points."""
        if not critique_points:
            return "maintain_current"

        # Analyze critique points for patterns
        if any("success rate" in point.lower() for point in critique_points):
            return "fundamental_restructure"

        if any("structure" in point.lower() or "organization" in point.lower() for point in critique_points):
            return "enhance_structure"

        if any("context" in point.lower() or "clarity" in point.lower() for point in critique_points):
            return "add_context_guidance"

        if any("cognitive" in point.lower() or "overwhelming" in point.lower() for point in critique_points):
            return "optimize_cognitive_load"

        if any("time" in point.lower() or "speed" in point.lower() for point in critique_points):
            return "streamline_process"

        return "iterative_improvement"

    async def _generate_evolved_prompt(
        self,
        current_prompt: str,
        critique_points: List[str],
        evolution_strategy: str
    ) -> str:
        """Generate evolved meta-prompt using AI assistance."""
        evolution_prompt = f"""You are a meta-prompt evolution specialist. Your task is to improve this meta-prompt based on the identified issues.

CURRENT META-PROMPT:
{current_prompt}

CRITIQUE POINTS:
{chr(10).join(f"- {point}" for point in critique_points)}

EVOLUTION STRATEGY: {evolution_strategy}

IMPROVEMENT REQUIREMENTS:
1. Address each critique point directly
2. Apply the evolution strategy consistently
3. Maintain the core functionality while improving effectiveness
4. Ensure ADHD-friendly structure and clarity
5. Preserve successful elements from the original

Focus on concrete, actionable improvements that will increase prompt optimization success rates.

Provide the evolved meta-prompt with clear improvements noted."""

        brain_request = ClaudeBrainRequest(
            operation="generate_meta_prompt",
            prompt=evolution_prompt,
            context={"evolution_strategy": evolution_strategy, "critique_points": critique_points},
            cognitive_load=0.4,
            attention_state="focused",
            max_tokens=1200
        )

        response = await self.brain_manager.process_request(brain_request)

        if response.success:
            return self._extract_evolved_prompt(response.result)
        else:
            # Fallback: apply basic improvements
            return self._apply_basic_improvements(current_prompt, critique_points)

    def _extract_evolved_prompt(self, response: str) -> str:
        """Extract the evolved prompt from AI response."""
        # Look for common markers
        markers = ["EVOLVED META-PROMPT:", "IMPROVED META-PROMPT:", "Here is the evolved prompt:"]

        for marker in markers:
            if marker in response:
                parts = response.split(marker, 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                    # Remove markdown if present
                    if "```" in content:
                        content = content.split("```")[1] if len(content.split("```")) > 1 else content
                    return content.strip()

        # Fallback: return response with some cleaning
        return response.replace("EVOLVED META-PROMPT:", "").replace("IMPROVED META-PROMPT:", "").strip()

    def _apply_basic_improvements(self, prompt: str, critique_points: List[str]) -> str:
        """Apply basic improvements as fallback."""
        improved = prompt

        # Add ADHD-friendly elements if needed
        if any("cognitive" in point.lower() for point in critique_points):
            if "✅" not in improved:
                improved += "\n\nADHD OPTIMIZATION:\n- Use visual indicators (✅ ❌ ⚠️ 💡 🎯)\n- Break complex tasks into steps\n- Lead with essential information"

        # Add structure if needed
        if any("structure" in point.lower() for point in critique_points):
            if "STRUCTURAL" not in improved:
                improved = "STRUCTURAL IMPROVEMENTS:\n- Use clear sections and headers\n- Implement bullet points and numbered lists\n- Apply progressive disclosure\n\n" + improved

        return improved

    def _calculate_improvement_score(self, critique_points: List[str], evolved_prompt: str) -> float:
        """Calculate improvement score based on critique point addressing."""
        if not critique_points:
            return 0.5  # Neutral score

        addressed_points = 0

        for point in critique_points:
            point_lower = point.lower()

            # Check if the evolved prompt addresses this point
            if "cognitive" in point_lower and ("ADHD" in evolved_prompt or "visual" in evolved_prompt.lower()):
                addressed_points += 1
            elif "structure" in point_lower and ("section" in evolved_prompt.lower() or "•" in evolved_prompt):
                addressed_points += 1
            elif "context" in point_lower and ("requirements" in evolved_prompt.lower() or "constraints" in evolved_prompt.lower()):
                addressed_points += 1
            elif "clarity" in point_lower and ("specific" in evolved_prompt.lower() or "clear" in evolved_prompt.lower()):
                addressed_points += 1
            elif "success" in point_lower and ("rate" in point_lower):
                # Harder to check automatically - assume partial addressing
                addressed_points += 0.5

        return min(addressed_points / len(critique_points), 1.0)

    async def _validate_evolution(
        self,
        original: str,
        evolved: str,
        performance_data: List[PromptPerformanceData]
    ) -> float:
        """Validate the evolution by testing against recent performance."""
        # Simple validation: check if evolved prompt is more comprehensive
        orig_length = len(original.split())
        evolved_length = len(evolved.split())

        # Length increase often indicates better guidance
        length_ratio = evolved_length / max(orig_length, 1)

        # Check for improvement indicators
        improvement_indicators = ["ADHD", "visual", "structure", "clarity", "specific", "requirements"]
        indicator_count = sum(1 for indicator in improvement_indicators if indicator in evolved)

        # Calculate confidence based on improvements
        confidence = min(0.3 + (indicator_count * 0.1) + (length_ratio - 1) * 0.2, 0.9)

        return max(0.1, confidence)

    def _extract_applied_improvements(self, critique_points: List[str], strategy: str) -> List[str]:
        """Extract list of applied improvements."""
        improvements = []

        if strategy == "enhance_structure":
            improvements.extend([
                "Added structured sections and headers",
                "Implemented visual hierarchy with formatting",
                "Applied progressive disclosure principles"
            ])
        elif strategy == "add_context_guidance":
            improvements.extend([
                "Enhanced context requirements",
                "Added specific constraints and examples",
                "Included success criteria and deliverables"
            ])
        elif strategy == "optimize_cognitive_load":
            improvements.extend([
                "Implemented ADHD-friendly formatting",
                "Added visual indicators and step-by-step guidance",
                "Applied cognitive load reduction techniques"
            ])
        elif strategy == "fundamental_restructure":
            improvements.extend([
                "Complete meta-prompt restructuring",
                "Fundamental approach revision",
                "Comprehensive improvement implementation"
            ])

        # Add strategy-specific improvements
        improvements.append(f"Applied evolution strategy: {strategy}")

        return improvements

    def record_performance(self, prompt_data: PromptPerformanceData) -> None:
        """Record prompt performance data for learning."""
        self.performance_data.append(prompt_data)

        # Keep only recent data (last 100 entries)
        if len(self.performance_data) > 100:
            self.performance_data = self.performance_data[-100:]

        # Update success rate
        if self.performance_data:
            successful = sum(1 for p in self.performance_data if p.success_score >= self.success_threshold)
            self.success_rate = successful / len(self.performance_data)

    async def get_stats(self) -> Dict[str, Any]:
        """Get meta-prompt generator statistics."""
        return {
            "total_evolutions": len(self.evolution_history),
            "active_templates": len(self.templates),
            "performance_data_points": len(self.performance_data),
            "current_success_rate": round(self.success_rate, 2),
            "latest_evolution_score": self.evolution_history[-1].improvement_score if self.evolution_history else 0.0,
            "evolution_history_length": len(self.evolution_history)
        }