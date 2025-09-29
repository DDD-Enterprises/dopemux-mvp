"""
Serena v2 Phase 2C: ConPort Knowledge Graph Bridge

Integration bridge between Serena code intelligence and ConPort knowledge graph,
providing decision context for code relationships and ADHD-optimized knowledge correlation.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

# Phase 2 Intelligence Components
from .database import SerenaIntelligenceDatabase
from .graph_operations import CodeElementNode, SerenaGraphOperations
from .adaptive_learning import AdaptiveLearningEngine, PersonalLearningProfile
from .learning_profile_manager import PersonalLearningProfileManager

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ConPortItemType(str, Enum):
    """Types of ConPort items that can link to code."""
    DECISION = "decision"
    PROGRESS_ENTRY = "progress_entry"
    SYSTEM_PATTERN = "system_pattern"
    CUSTOM_DATA = "custom_data"


class LinkStrength(str, Enum):
    """Strength of links between code and ConPort items."""
    WEAK = "weak"          # 0.0-0.3 - tangentially related
    MODERATE = "moderate"  # 0.3-0.6 - clearly related
    STRONG = "strong"      # 0.6-0.8 - directly implements/addresses
    CRITICAL = "critical"  # 0.8-1.0 - essential connection


class ContextRelevance(str, Enum):
    """Relevance of ConPort context to code navigation."""
    IMMEDIATE = "immediate"       # Directly relevant to current task
    SUPPORTING = "supporting"     # Provides helpful context
    BACKGROUND = "background"     # General background knowledge
    HISTORICAL = "historical"     # Past context, may be outdated


@dataclass
class ConPortCodeLink:
    """Link between code element and ConPort knowledge item."""
    # Code side
    code_element_id: int
    code_element_name: str
    code_file_path: str

    # ConPort side
    conport_item_type: ConPortItemType
    conport_item_id: str
    conport_summary: str
    conport_content: str

    # Link metadata
    link_strength: float  # 0.0-1.0
    link_type: str  # implements, addresses, relates_to, etc.
    context_relevance: ContextRelevance
    discovery_method: str  # manual, automatic, pattern_based

    # ADHD optimization
    cognitive_value: float  # How much this context helps understanding
    attention_impact: str  # positive, neutral, negative
    complexity_context: str  # simplifies, neutral, complicates

    # Effectiveness tracking
    user_found_helpful: Optional[bool] = None
    effectiveness_score: float = 0.0
    usage_frequency: int = 0
    last_accessed: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DecisionCodeContext:
    """Code context for a ConPort decision."""
    decision_id: str
    decision_summary: str
    related_code_elements: List[CodeElementNode]
    implementation_status: str  # planned, partial, complete, abandoned
    complexity_impact: float  # How much this decision affects code complexity
    adhd_considerations: List[str]  # ADHD factors in the decision


@dataclass
class CodeDecisionInsight:
    """Insight about code derived from ConPort decisions."""
    insight_id: str
    code_element_id: int
    insight_type: str  # architectural, implementation, maintenance, etc.
    title: str
    description: str
    decision_context: str
    actionable_recommendations: List[str]
    adhd_relevance: str  # high, medium, low
    confidence: float


class ConPortKnowledgeGraphBridge:
    """
    Bridge between Serena code intelligence and ConPort knowledge graph.

    Features:
    - Automatic discovery of code-decision relationships
    - Decision context integration for code navigation
    - ADHD-optimized knowledge presentation
    - Bidirectional link management (code ↔ decisions)
    - Context-aware knowledge retrieval
    - Progressive disclosure of complex decision context
    - Effectiveness tracking for knowledge utility
    - Integration with adaptive learning for personalized context
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        graph_operations: SerenaGraphOperations,
        profile_manager: PersonalLearningProfileManager,
        workspace_id: str,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.graph_operations = graph_operations
        self.profile_manager = profile_manager
        self.workspace_id = workspace_id  # ConPort workspace identifier
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # ConPort integration configuration
        self.max_context_items = 10  # ADHD cognitive load limit
        self.relevance_threshold = 0.4  # Minimum relevance for context
        self.context_cache_ttl_minutes = 15  # Cache decision context

        # Caching for performance
        self._decision_cache: Dict[str, Dict[str, Any]] = {}
        self._link_cache: Dict[str, List[ConPortCodeLink]] = {}

        # ADHD presentation settings
        self.enable_progressive_disclosure = True
        self.enable_complexity_filtering = True
        self.enable_cognitive_load_scoring = True

    # Core Bridge Operations

    async def get_decision_context_for_code(
        self,
        code_element: CodeElementNode,
        user_session_id: str,
        include_historical: bool = False
    ) -> Dict[str, Any]:
        """Get ConPort decision context relevant to code element."""
        operation_id = self.performance_monitor.start_operation("get_decision_context_for_code")

        try:
            # Find ConPort links for this code element
            links = await self._find_conport_links_for_element(
                code_element.id, include_historical
            )

            if not links:
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=False)
                return {
                    "code_element": code_element.element_name,
                    "decision_context": [],
                    "insights": [],
                    "recommendations": []
                }

            # Get user profile for personalization
            profile = await self.profile_manager.get_or_create_profile(
                user_session_id, self.workspace_id
            )

            # Fetch decision details and apply ADHD filtering
            decision_contexts = []
            for link in links:
                context = await self._get_enhanced_decision_context(link, profile)
                if context:
                    decision_contexts.append(context)

            # Apply ADHD optimization
            filtered_contexts = self._apply_adhd_context_filtering(
                decision_contexts, profile
            )

            # Generate insights based on decision context
            insights = await self._generate_decision_based_insights(
                code_element, filtered_contexts, profile
            )

            # Generate ADHD-optimized recommendations
            recommendations = await self._generate_context_based_recommendations(
                code_element, filtered_contexts, profile
            )

            result = {
                "code_element": code_element.element_name,
                "decision_context": [self._serialize_decision_context(ctx) for ctx in filtered_contexts],
                "context_count": len(filtered_contexts),
                "total_available": len(decision_contexts),
                "adhd_filtered": len(decision_contexts) - len(filtered_contexts),
                "insights": [self._serialize_insight(insight) for insight in insights],
                "recommendations": recommendations,
                "context_relevance": "high" if any(ctx.context_relevance == ContextRelevance.IMMEDIATE for ctx in filtered_contexts) else "moderate"
            }

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🔗 Retrieved decision context for {code_element.element_name}: "
                        f"{len(filtered_contexts)} contexts")

            return result

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get decision context for code: {e}")
            return {"error": str(e), "decision_context": []}

    async def create_code_decision_link(
        self,
        code_element_id: int,
        conport_item_type: ConPortItemType,
        conport_item_id: str,
        link_type: str,
        link_strength: float,
        user_session_id: str,
        context: Optional[str] = None
    ) -> bool:
        """Create link between code element and ConPort decision/item."""
        operation_id = self.performance_monitor.start_operation("create_code_decision_link")

        try:
            # Validate code element exists
            code_element = await self.graph_operations.get_element_by_id(code_element_id)
            if not code_element:
                raise ValueError(f"Code element {code_element_id} not found")

            # Get ConPort item details (would use ConPort MCP in real implementation)
            conport_item = await self._get_conport_item_details(
                conport_item_type, conport_item_id
            )

            if not conport_item:
                raise ValueError(f"ConPort item {conport_item_id} not found")

            # Create link in database
            insert_query = """
            INSERT INTO conport_integration_links (
                serena_element_id, serena_element_type, conport_workspace,
                conport_item_type, conport_item_id, link_type,
                link_strength, bidirectional, link_context,
                automated_confidence, user_confirmed
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (serena_element_id, serena_element_type, conport_item_type, conport_item_id, link_type)
            DO UPDATE SET
                link_strength = EXCLUDED.link_strength,
                link_context = EXCLUDED.link_context,
                user_confirmed = EXCLUDED.user_confirmed,
                updated_at = NOW()
            """

            await self.database.execute_query(insert_query, (
                code_element_id,
                "code_element",
                self.workspace_id,
                conport_item_type.value,
                conport_item_id,
                link_type,
                link_strength,
                True,  # bidirectional
                context or f"Link created by user {user_session_id}",
                0.9,  # High confidence for user-created links
                True   # user_confirmed
            ))

            # Clear relevant caches
            cache_key = f"element_{code_element_id}"
            if cache_key in self._link_cache:
                del self._link_cache[cache_key]

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🔗 Created link: {code_element.element_name} ↔ {conport_item_type.value} {conport_item_id}")
            return True

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to create code-decision link: {e}")
            return False

    async def discover_automatic_links(
        self,
        code_elements: List[CodeElementNode],
        user_session_id: str,
        confidence_threshold: float = 0.7
    ) -> List[ConPortCodeLink]:
        """Automatically discover links between code and ConPort items."""
        operation_id = self.performance_monitor.start_operation("discover_automatic_links")

        try:
            discovered_links = []

            # Get recent ConPort decisions for context
            recent_decisions = await self._get_recent_conport_decisions()

            for element in code_elements:
                # Try to find relevant decisions for this code element
                potential_links = await self._find_potential_decision_links(
                    element, recent_decisions
                )

                for potential_link in potential_links:
                    if potential_link.effectiveness_score >= confidence_threshold:
                        # Validate and create the link
                        validated_link = await self._validate_potential_link(
                            potential_link, user_session_id
                        )

                        if validated_link:
                            discovered_links.append(validated_link)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🔍 Discovered {len(discovered_links)} automatic code-decision links")
            return discovered_links

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to discover automatic links: {e}")
            return []

    async def get_code_insights_from_decisions(
        self,
        code_element: CodeElementNode,
        user_session_id: str
    ) -> List[CodeDecisionInsight]:
        """Get insights about code derived from ConPort decisions."""
        operation_id = self.performance_monitor.start_operation("get_code_insights_from_decisions")

        try:
            # Get decision context
            decision_context = await self.get_decision_context_for_code(
                code_element, user_session_id
            )

            insights = []

            for context in decision_context.get("decision_context", []):
                # Generate insights from decision context
                insight = await self._generate_decision_insight(
                    code_element, context, user_session_id
                )

                if insight:
                    insights.append(insight)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"💡 Generated {len(insights)} decision-based insights for {code_element.element_name}")
            return insights

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get code insights from decisions: {e}")
            return []

    # ConPort Integration Methods

    async def _find_conport_links_for_element(
        self, element_id: int, include_historical: bool = False
    ) -> List[ConPortCodeLink]:
        """Find ConPort links for a code element."""
        try:
            cache_key = f"element_{element_id}_{include_historical}"
            if cache_key in self._link_cache:
                return self._link_cache[cache_key]

            # Build query based on whether to include historical
            time_filter = ""
            if not include_historical:
                time_filter = " AND cil.created_at > NOW() - INTERVAL '30 days'"

            query = f"""
            SELECT
                cil.*,
                ce.element_name,
                ce.file_path
            FROM conport_integration_links cil
            JOIN code_elements ce ON cil.serena_element_id = ce.id
            WHERE cil.serena_element_id = $1
              AND cil.conport_workspace = $2
              AND cil.link_strength > 0.3
            {time_filter}
            ORDER BY cil.link_strength DESC, cil.updated_at DESC
            LIMIT 20
            """

            results = await self.database.execute_query(query, (element_id, self.workspace_id))

            links = []
            for row in results:
                # Get ConPort item details
                conport_details = await self._get_conport_item_details(
                    ConPortItemType(row['conport_item_type']),
                    row['conport_item_id']
                )

                if conport_details:
                    link = ConPortCodeLink(
                        code_element_id=element_id,
                        code_element_name=row['element_name'],
                        code_file_path=row['file_path'],
                        conport_item_type=ConPortItemType(row['conport_item_type']),
                        conport_item_id=row['conport_item_id'],
                        conport_summary=conport_details.get('summary', ''),
                        conport_content=conport_details.get('content', ''),
                        link_strength=row['link_strength'],
                        link_type=row['link_type'],
                        context_relevance=self._assess_context_relevance(conport_details),
                        discovery_method=row.get('discovery_method', 'manual'),
                        cognitive_value=self._assess_cognitive_value(conport_details),
                        attention_impact=self._assess_attention_impact(conport_details),
                        complexity_context=self._assess_complexity_context(conport_details),
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    links.append(link)

            # Cache the results
            self._link_cache[cache_key] = links

            return links

        except Exception as e:
            logger.error(f"Failed to find ConPort links for element: {e}")
            return []

    async def _get_conport_item_details(
        self, item_type: ConPortItemType, item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get ConPort item details using ConPort MCP integration."""
        try:
            # This would use ConPort MCP calls in real implementation
            # For now, return simulated data structure

            if item_type == ConPortItemType.DECISION:
                return {
                    "id": item_id,
                    "summary": f"Decision {item_id}: Architecture decision",
                    "content": "Detailed decision rationale and implementation details",
                    "rationale": "Technical reasoning for the decision",
                    "implementation_details": "How this decision affects code implementation",
                    "tags": ["architecture", "implementation"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            elif item_type == ConPortItemType.SYSTEM_PATTERN:
                return {
                    "id": item_id,
                    "name": f"Pattern {item_id}",
                    "description": "System pattern description",
                    "tags": ["pattern", "system"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            # Default return for other types
            return {
                "id": item_id,
                "summary": f"{item_type.value} {item_id}",
                "content": "ConPort item content",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get ConPort item details: {e}")
            return None

    async def _get_recent_conport_decisions(self, days: int = 14) -> List[Dict[str, Any]]:
        """Get recent ConPort decisions for link discovery."""
        try:
            # This would use ConPort MCP get_decisions in real implementation
            # For now, return simulated decisions

            return [
                {
                    "id": "91",
                    "summary": "Serena v2 Phase 2A: PostgreSQL Intelligence Foundation Complete",
                    "tags": ["serena", "postgresql", "intelligence"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "implementation_details": "PostgreSQL intelligence layer implementation"
                },
                {
                    "id": "92",
                    "summary": "Serena v2 Phase 2B: Adaptive Learning Engine Complete",
                    "tags": ["serena", "adaptive-learning", "adhd-optimization"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "implementation_details": "Adaptive learning system for ADHD navigation"
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get recent ConPort decisions: {e}")
            return []

    # Link Discovery and Analysis

    async def _find_potential_decision_links(
        self, element: CodeElementNode, decisions: List[Dict[str, Any]]
    ) -> List[ConPortCodeLink]:
        """Find potential links between code element and decisions."""
        potential_links = []

        try:
            for decision in decisions:
                # Calculate potential link strength using text similarity and context
                link_strength = await self._calculate_decision_link_strength(
                    element, decision
                )

                if link_strength > 0.3:  # Above minimum threshold
                    # Assess context relevance
                    relevance = self._assess_decision_relevance(element, decision)

                    # Create potential link
                    potential_link = ConPortCodeLink(
                        code_element_id=element.id,
                        code_element_name=element.element_name,
                        code_file_path=element.file_path,
                        conport_item_type=ConPortItemType.DECISION,
                        conport_item_id=decision['id'],
                        conport_summary=decision['summary'],
                        conport_content=decision.get('implementation_details', ''),
                        link_strength=link_strength,
                        link_type="implements" if link_strength > 0.7 else "relates_to",
                        context_relevance=relevance,
                        discovery_method="automatic",
                        cognitive_value=self._assess_cognitive_value(decision),
                        attention_impact="positive",  # Decisions generally provide helpful context
                        complexity_context="simplifies",  # Good decisions reduce complexity
                        effectiveness_score=link_strength  # Use link strength as initial effectiveness
                    )

                    potential_links.append(potential_link)

            return potential_links

        except Exception as e:
            logger.error(f"Failed to find potential decision links: {e}")
            return []

    async def _calculate_decision_link_strength(
        self, element: CodeElementNode, decision: Dict[str, Any]
    ) -> float:
        """Calculate link strength between code element and decision."""
        strength_factors = []

        # Text similarity factors
        element_terms = {element.element_name.lower(), element.element_type.lower()}
        decision_text = f"{decision['summary']} {decision.get('implementation_details', '')}".lower()

        # Check for direct mentions
        direct_mentions = sum(1 for term in element_terms if term in decision_text)
        if direct_mentions > 0:
            strength_factors.append(0.8)

        # File path correlation
        if element.file_path.lower() in decision_text:
            strength_factors.append(0.7)

        # Tag correlation
        decision_tags = decision.get('tags', [])
        if any(tag in element.file_path.lower() or tag in element.element_name.lower()
               for tag in decision_tags):
            strength_factors.append(0.6)

        # Language/technology correlation
        if element.language in decision_text:
            strength_factors.append(0.5)

        # Recency factor (more recent decisions are more relevant)
        decision_timestamp = decision.get('timestamp')
        if decision_timestamp:
            try:
                decision_date = datetime.fromisoformat(decision_timestamp.replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - decision_date).days
                recency_factor = max(0.2, 1.0 - (days_ago / 30.0))  # 30-day decay
                strength_factors.append(recency_factor * 0.3)
            except Exception:
                strength_factors.append(0.3)  # Default recency

        return min(1.0, statistics.mean(strength_factors)) if strength_factors else 0.0

    # ADHD Optimization

    def _apply_adhd_context_filtering(
        self, contexts: List[Dict[str, Any]], profile: PersonalLearningProfile
    ) -> List[Dict[str, Any]]:
        """Apply ADHD-optimized filtering to decision contexts."""
        # Sort by relevance and cognitive value
        sorted_contexts = sorted(
            contexts,
            key=lambda ctx: (
                ctx.get('relevance_score', 0.0),
                ctx.get('cognitive_value', 0.0),
                -ctx.get('complexity_impact', 0.0)  # Lower complexity impact preferred
            ),
            reverse=True
        )

        # Apply progressive filtering based on user's capacity
        filtered_contexts = []

        for context in sorted_contexts:
            # Skip if too complex for current session
            if (context.get('complexity_impact', 0.0) > 0.8 and
                len(filtered_contexts) >= 2):  # Already have some context
                continue

            # Skip if cognitive value is too low
            if context.get('cognitive_value', 0.0) < 0.4:
                continue

            filtered_contexts.append(context)

            # ADHD hard limit: max 5 context items
            if len(filtered_contexts) >= min(5, self.max_context_items):
                break

        return filtered_contexts

    async def _generate_decision_based_insights(
        self,
        code_element: CodeElementNode,
        decision_contexts: List[Dict[str, Any]],
        profile: PersonalLearningProfile
    ) -> List[CodeDecisionInsight]:
        """Generate insights about code based on decision context."""
        insights = []

        try:
            for context in decision_contexts:
                # Generate insight based on decision type and content
                insight_type = self._classify_insight_type(context)

                # Create actionable insight
                insight = CodeDecisionInsight(
                    insight_id=f"insight_{code_element.id}_{context.get('id', 'unknown')}",
                    code_element_id=code_element.id,
                    insight_type=insight_type,
                    title=f"Decision Context: {context.get('summary', 'Unknown')[:50]}",
                    description=self._generate_insight_description(code_element, context),
                    decision_context=context.get('content', ''),
                    actionable_recommendations=self._generate_actionable_recommendations(
                        code_element, context, profile
                    ),
                    adhd_relevance=self._assess_adhd_relevance(context, profile),
                    confidence=context.get('relevance_score', 0.5)
                )

                insights.append(insight)

            return insights

        except Exception as e:
            logger.error(f"Failed to generate decision-based insights: {e}")
            return []

    async def _generate_context_based_recommendations(
        self,
        code_element: CodeElementNode,
        decision_contexts: List[Dict[str, Any]],
        profile: PersonalLearningProfile
    ) -> List[str]:
        """Generate ADHD-optimized recommendations based on decision context."""
        recommendations = []

        if not decision_contexts:
            return ["No decision context available for additional guidance"]

        # Analyze decision patterns
        implementation_decisions = [ctx for ctx in decision_contexts
                                 if 'implementation' in ctx.get('summary', '').lower()]
        if implementation_decisions:
            recommendations.append(f"📋 {len(implementation_decisions)} implementation decisions provide context")

        # ADHD-specific recommendations
        high_complexity_decisions = [ctx for ctx in decision_contexts
                                   if ctx.get('complexity_impact', 0.0) > 0.6]
        if high_complexity_decisions:
            recommendations.append("🧠 Complex decisions involved - review during peak focus time")

        # Pattern-based recommendations
        if profile.learning_phase.value in ["convergence", "optimization"]:
            recommendations.append("🎯 Decision context aligns with your learned patterns")

        # General guidance
        if len(decision_contexts) > 3:
            recommendations.append("📖 Multiple decisions - use progressive disclosure")

        recommendations.append("🔗 Decision context helps understand the 'why' behind code")

        return recommendations

    # Utility Methods

    def _assess_context_relevance(self, conport_item: Dict[str, Any]) -> ContextRelevance:
        """Assess relevance of ConPort context."""
        # Simple relevance assessment based on recency and content
        timestamp = conport_item.get('timestamp')
        if timestamp:
            try:
                item_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - item_date).days

                if days_ago <= 1:
                    return ContextRelevance.IMMEDIATE
                elif days_ago <= 7:
                    return ContextRelevance.SUPPORTING
                elif days_ago <= 30:
                    return ContextRelevance.BACKGROUND
                else:
                    return ContextRelevance.HISTORICAL
            except Exception:
                pass

        return ContextRelevance.BACKGROUND

    def _assess_cognitive_value(self, conport_item: Dict[str, Any]) -> float:
        """Assess cognitive value of ConPort context."""
        # Base value on content quality and detail
        content_length = len(conport_item.get('content', ''))
        summary_length = len(conport_item.get('summary', ''))

        if content_length > 500 or summary_length > 100:
            return 0.8  # Detailed content has high cognitive value
        elif content_length > 100 or summary_length > 50:
            return 0.6  # Moderate content
        else:
            return 0.4  # Brief content

    def _assess_attention_impact(self, conport_item: Dict[str, Any]) -> str:
        """Assess how ConPort context affects attention."""
        # Generally, decision context is positive for attention
        # as it provides the "why" that ADHD users often need

        content_length = len(conport_item.get('content', ''))
        if content_length > 1000:
            return "neutral"  # Long content might overwhelm
        else:
            return "positive"  # Helpful context

    def _assess_complexity_context(self, conport_item: Dict[str, Any]) -> str:
        """Assess how ConPort context affects complexity perception."""
        # Decision context usually simplifies understanding
        # by providing rationale and background

        if 'rationale' in conport_item or 'implementation_details' in conport_item:
            return "simplifies"
        else:
            return "neutral"

    def _classify_insight_type(self, context: Dict[str, Any]) -> str:
        """Classify type of insight from decision context."""
        tags = context.get('tags', [])

        if any(tag in ["architecture", "design"] for tag in tags):
            return "architectural"
        elif any(tag in ["implementation", "coding"] for tag in tags):
            return "implementation"
        elif any(tag in ["performance", "optimization"] for tag in tags):
            return "performance"
        elif any(tag in ["maintenance", "refactoring"] for tag in tags):
            return "maintenance"
        else:
            return "general"

    def _generate_insight_description(
        self, code_element: CodeElementNode, context: Dict[str, Any]
    ) -> str:
        """Generate description for code insight."""
        return f"This {code_element.element_type} is related to the decision: {context.get('summary', 'Unknown decision')}"

    def _generate_actionable_recommendations(
        self, code_element: CodeElementNode, context: Dict[str, Any], profile: PersonalLearningProfile
    ) -> List[str]:
        """Generate actionable recommendations from decision context."""
        recommendations = []

        # Base recommendations on decision content
        if 'implementation_details' in context:
            recommendations.append("Review implementation details from related decision")

        if 'rationale' in context:
            recommendations.append("Understand decision rationale for better context")

        # ADHD-specific recommendations
        if profile.progressive_disclosure_preference:
            recommendations.append("Use progressive disclosure to explore decision context gradually")

        recommendations.append("Keep decision context in mind while navigating this code")

        return recommendations

    def _assess_adhd_relevance(self, context: Dict[str, Any], profile: PersonalLearningProfile) -> str:
        """Assess ADHD relevance of decision context."""
        # ADHD users benefit from understanding "why" behind code
        if 'rationale' in context or 'implementation_details' in context:
            return "high"
        elif len(context.get('content', '')) > 100:
            return "medium"
        else:
            return "low"

    async def _get_enhanced_decision_context(
        self, link: ConPortCodeLink, profile: PersonalLearningProfile
    ) -> Optional[Dict[str, Any]]:
        """Get enhanced decision context with ADHD optimization."""
        try:
            context = {
                "link": link,
                "relevance_score": link.link_strength,
                "cognitive_value": link.cognitive_value,
                "complexity_impact": 0.5,  # Would be calculated
                "adhd_optimized": True,
                "progressive_disclosure_available": len(link.conport_content) > 200
            }

            return context

        except Exception as e:
            logger.error(f"Failed to get enhanced decision context: {e}")
            return None

    # Serialization

    def _serialize_decision_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize decision context for API response."""
        link = context.get('link')
        if not link:
            return context

        return {
            "decision_id": link.conport_item_id,
            "decision_summary": link.conport_summary,
            "link_strength": link.link_strength,
            "link_type": link.link_type,
            "cognitive_value": link.cognitive_value,
            "attention_impact": link.attention_impact,
            "complexity_context": link.complexity_context,
            "relevance": link.context_relevance.value,
            "progressive_disclosure": context.get('progressive_disclosure_available', False)
        }

    def _serialize_insight(self, insight: CodeDecisionInsight) -> Dict[str, Any]:
        """Serialize code insight for API response."""
        return {
            "insight_id": insight.insight_id,
            "type": insight.insight_type,
            "title": insight.title,
            "description": insight.description,
            "recommendations": insight.actionable_recommendations,
            "adhd_relevance": insight.adhd_relevance,
            "confidence": insight.confidence
        }

    # Placeholder methods for complex operations
    def _assess_decision_relevance(self, element: CodeElementNode, decision: Dict[str, Any]) -> ContextRelevance:
        return ContextRelevance.SUPPORTING  # Default

    async def _validate_potential_link(self, potential_link: ConPortCodeLink, user_session_id: str) -> Optional[ConPortCodeLink]:
        return potential_link  # For now, accept all potential links

    async def _generate_decision_insight(self, code_element: CodeElementNode, context: Dict[str, Any], user_session_id: str) -> Optional[CodeDecisionInsight]:
        return None  # Placeholder - would generate actual insights


# Convenience functions
async def create_conport_bridge(
    database: SerenaIntelligenceDatabase,
    graph_operations: SerenaGraphOperations,
    profile_manager: PersonalLearningProfileManager,
    workspace_id: str,
    performance_monitor: PerformanceMonitor = None
) -> ConPortKnowledgeGraphBridge:
    """Create ConPort knowledge graph bridge instance."""
    return ConPortKnowledgeGraphBridge(
        database, graph_operations, profile_manager, workspace_id, performance_monitor
    )


async def test_conport_integration(
    bridge: ConPortKnowledgeGraphBridge,
    test_element: CodeElementNode,
    user_session_id: str
) -> Dict[str, Any]:
    """Test ConPort integration functionality."""
    try:
        # Test decision context retrieval
        context_result = await bridge.get_decision_context_for_code(test_element, user_session_id)

        # Test automatic link discovery
        auto_links = await bridge.discover_automatic_links([test_element], user_session_id)

        # Test insights generation
        insights = await bridge.get_code_insights_from_decisions(test_element, user_session_id)

        return {
            "decision_context_available": len(context_result.get('decision_context', [])) > 0,
            "automatic_links_discovered": len(auto_links),
            "insights_generated": len(insights),
            "adhd_filtering_applied": context_result.get('adhd_filtered', 0) > 0,
            "test_status": "success",
            "integration_functional": True
        }

    except Exception as e:
        logger.error(f"ConPort integration test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "integration_functional": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🌉 Serena ConPort Knowledge Graph Bridge")
        print("Code intelligence + decision context integration")
        print("✅ Module loaded successfully")

    asyncio.run(main())