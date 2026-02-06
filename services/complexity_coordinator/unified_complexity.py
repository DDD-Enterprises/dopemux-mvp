"""
F-NEW-3: Unified Complexity Intelligence

Combines complexity scores from multiple sources for enhanced accuracy:
- Dope-Context: AST-based Tree-sitter complexity (structural analysis)
- Serena: LSP-based complexity (usage patterns, references, relationships)
- ADHD Engine: User-specific complexity adjustments (personal thresholds)

Benefits:
- More accurate complexity (AST + LSP + usage patterns + personal factors)
- Reduced computation (calculate once, share everywhere)
- Better ADHD accommodations (personalized cognitive load assessment)

ADHD Optimization:
- 0.0-1.0 scale maintained for consistency
- Complexity > 0.6 triggers gentle warnings
- Personalized thresholds based on user patterns
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ComplexityBreakdown:
    """
    Detailed breakdown of unified complexity score.

    Attributes:
        ast_score: Tree-sitter structural complexity (0.0-1.0)
        lsp_score: LSP usage pattern complexity (0.0-1.0)
        usage_score: Reference count & call frequency score (0.0-1.0)
        adhd_multiplier: User-specific adjustment factor (0.5-1.5)
        unified_score: Final combined score (0.0-1.0)
        confidence: Confidence in score (0.0-1.0, based on data availability)
    """
    ast_score: float
    lsp_score: float
    usage_score: float
    adhd_multiplier: float
    unified_score: float
    confidence: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "ast_score": round(self.ast_score, 3),
            "lsp_score": round(self.lsp_score, 3),
            "usage_score": round(self.usage_score, 3),
            "adhd_multiplier": round(self.adhd_multiplier, 3),
            "unified_score": round(self.unified_score, 3),
            "confidence": round(self.confidence, 3),
            "interpretation": self._interpret_score()
        }

    def _interpret_score(self) -> str:
        """Human-readable interpretation of unified score."""
        if self.unified_score < 0.3:
            return "Low complexity - safe to read anytime"
        elif self.unified_score < 0.6:
            return "Medium complexity - needs focus"
        else:
            return "High complexity - schedule dedicated time"


class ComplexityCoordinator:
    """
    Coordinates complexity analysis across multiple systems.

    Combines AST analysis, LSP metadata, and user-specific ADHD adjustments
    for a unified, more accurate complexity score.
    """

    def __init__(self):
        """Initialize complexity coordinator."""
        self._dope_context_client = None
        self._serena_client = None
        self._adhd_config = None
        self._initialized = False

        # Weighting factors (can be tuned based on validation)
        self.ast_weight = 0.4  # Structural complexity is foundational
        self.lsp_weight = 0.3  # Usage patterns add context
        self.usage_weight = 0.3  # Reference counts indicate real-world complexity

    async def _ensure_clients(self):
        """Lazy-load client connections."""
        if self._initialized:
            return

        try:
            # Import dope-context
            import sys
            dope_path = Path(__file__).parent.parent / "dope-context" / "src"
            if str(dope_path) not in sys.path:
                sys.path.insert(0, str(dope_path))

            # Import ADHD Engine
            adhd_path = Path(__file__).parent.parent / "adhd_engine"
            if str(adhd_path) not in sys.path:
                sys.path.insert(0, str(adhd_path))

            from adhd_config_service import get_adhd_config_service

            self._adhd_config = await get_adhd_config_service()
            self._initialized = True

            logger.info("✅ ComplexityCoordinator initialized with ADHD Engine")

        except Exception as e:
            logger.warning(f"⚠️  Partial initialization: {e}")
            self._initialized = True  # Continue with degraded mode

    async def get_ast_complexity(
        self,
        file_path: str,
        symbol: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Get AST-based complexity from dope-context.

        Args:
            file_path: File path
            symbol: Optional function/class name

        Returns:
            (complexity_score, confidence) tuple
        """
        try:
            # Try importing dope-context chunking module
            from chunking.structure_aware import get_file_chunks

            # Get chunks for file
            chunks = get_file_chunks(file_path)

            if symbol:
                # Find specific symbol's chunk
                matching_chunks = [c for c in chunks if symbol in c.get('function_name', '')]
                if matching_chunks:
                    complexity = matching_chunks[0].get('complexity', 0.5)
                    logger.debug(f"AST complexity for {file_path}:{symbol} = {complexity:.3f}")
                    return (complexity, 0.9)  # High confidence (Tree-sitter data)
                else:
                    logger.debug(f"Symbol {symbol} not found in {file_path}")
                    return (0.5, 0.2)  # Symbol not found
            else:
                # Return average complexity for entire file
                complexities = [c.get('complexity', 0.5) for c in chunks]
                avg_complexity = sum(complexities) / len(complexities) if complexities else 0.5
                logger.debug(f"AST complexity for {file_path} (avg) = {avg_complexity:.3f}")
                return (avg_complexity, 0.8)  # Good confidence (Tree-sitter data)

        except Exception as e:
            logger.debug(f"AST complexity failed, using fallback: {e}")
            return (0.5, 0.3)  # Medium complexity, low confidence (no data)

    async def get_lsp_complexity(
        self,
        file_path: str,
        symbol: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Get LSP-based complexity from Serena.

        Args:
            file_path: File path
            symbol: Optional function/class name

        Returns:
            (complexity_score, confidence) tuple
        """
        try:
            # Try importing Serena's ADHD features for complexity analysis
            serena_path = Path(__file__).parent.parent / "serena" / "v2"
            if str(serena_path) not in sys.path:
                sys.path.insert(0, str(serena_path))

            from adhd_features import CodeComplexityAnalyzer

            analyzer = CodeComplexityAnalyzer()

            # Analyze complexity using Serena's LSP-based analyzer
            result = analyzer.analyze_complexity(file_path, symbol)

            complexity_score = result.get('complexity_score', 0.5)
            confidence = result.get('confidence', 0.7)

            logger.debug(f"LSP complexity for {file_path}:{symbol} = {complexity_score:.3f}")
            return (complexity_score, confidence)

        except Exception as e:
            logger.debug(f"LSP complexity failed, using fallback: {e}")
            return (0.5, 0.3)  # Medium complexity, low confidence (no data)

    async def get_usage_complexity(
        self,
        file_path: str,
        symbol: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculate usage-based complexity from reference counts.

        Higher reference count = higher complexity (more impact if changed)

        Args:
            file_path: File path
            symbol: Optional function/class name

        Returns:
            (complexity_score, confidence) tuple
        """
        if not symbol:
            # Can't calculate usage for entire file
            return (0.5, 0.2)

        try:
            # Try using Serena's database for reference counting
            serena_db_path = Path(__file__).parent.parent / "serena" / "v2" / "intelligence"
            if str(serena_db_path) not in sys.path:
                sys.path.insert(0, str(serena_db_path))

            from database import SerenaDatabase

            db = SerenaDatabase()
            await db.initialize()

            # Query reference count for symbol
            # This uses the code_relationships table from Serena
            async with db.connection_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as ref_count
                    FROM code_relationships
                    WHERE target_symbol = $1 AND target_file = $2
                    """,
                    symbol,
                    file_path
                )

                ref_count = result['ref_count'] if result else 0

            # Convert ref_count to 0.0-1.0 complexity score
            # Logarithmic scale: 1-5 refs = low, 6-20 = medium, 21+ = high
            if ref_count == 0:
                complexity = 0.2  # Unused code = low complexity risk
            elif ref_count <= 5:
                complexity = 0.4  # Few refs = medium-low
            elif ref_count <= 20:
                complexity = 0.6  # Moderate refs = medium-high
            else:
                complexity = 0.8 + min(0.2, (ref_count - 20) / 100)  # Many refs = high

            logger.debug(f"Usage complexity for {file_path}:{symbol} = {complexity:.3f} ({ref_count} refs)")
            return (complexity, 0.85)  # High confidence (database query)

        except Exception as e:
            logger.debug(f"Usage complexity failed, using fallback: {e}")
            return (0.5, 0.3)  # Medium complexity, low confidence (no data)

    async def get_adhd_multiplier(
        self,
        user_id: str = "default"
    ) -> float:
        """
        Get user-specific complexity multiplier from ADHD Engine.

        Adjusts complexity based on:
        - User's historical success with different complexity levels
        - Current energy level
        - Current attention state
        - Personal thresholds

        Args:
            user_id: User identifier

        Returns:
            Multiplier (0.5-1.5) where:
            - 0.5 = user handles complexity well, reduce perceived difficulty
            - 1.0 = standard (no adjustment)
            - 1.5 = user struggles with complexity, increase perceived difficulty
        """
        await self._ensure_clients()

        if not self._adhd_config:
            return 1.0  # No adjustment

        try:
            # Query ADHD Engine for user's complexity multiplier
            # Based on energy level and attention state
            state = await self._adhd_config.get_state(user_id)

            energy = state.get('energy_level', 'medium')
            attention = state.get('attention_state', 'focused')

            # Calculate multiplier based on current state
            multiplier = 1.0

            # Energy adjustment
            if energy == 'low':
                multiplier *= 1.3  # Low energy = perceive higher complexity
            elif energy == 'high':
                multiplier *= 0.8  # High energy = handle complexity better

            # Attention adjustment
            if attention == 'scattered':
                multiplier *= 1.4  # Scattered = everything feels harder
            elif attention == 'hyperfocused':
                multiplier *= 0.7  # Hyperfocus = complexity less intimidating

            # Clamp to reasonable range
            multiplier = max(0.5, min(1.5, multiplier))

            logger.debug(f"ADHD multiplier for {user_id}: {multiplier:.2f}x (energy:{energy}, attention:{attention})")
            return multiplier

        except Exception as e:
            logger.debug(f"ADHD multiplier failed, using baseline: {e}")
            return 1.0

    async def get_unified_complexity(
        self,
        file_path: str,
        symbol: Optional[str] = None,
        user_id: str = "default"
    ) -> ComplexityBreakdown:
        """
        Get unified complexity score combining all sources.

        Calculation:
            base_score = (ast * 0.4) + (lsp * 0.3) + (usage * 0.3)
            unified = base_score * adhd_multiplier
            unified = clamp(unified, 0.0, 1.0)

        Args:
            file_path: File path
            symbol: Optional function/class name
            user_id: User identifier for ADHD adjustments

        Returns:
            ComplexityBreakdown with scores and interpretation
        """
        await self._ensure_clients()

        # Get complexity from all sources
        ast_score, ast_conf = await self.get_ast_complexity(file_path, symbol)
        lsp_score, lsp_conf = await self.get_lsp_complexity(file_path, symbol)
        usage_score, usage_conf = await self.get_usage_complexity(file_path, symbol)
        adhd_mult = await self.get_adhd_multiplier(user_id)

        # Calculate base unified score (weighted average)
        base_score = (
            ast_score * self.ast_weight +
            lsp_score * self.lsp_weight +
            usage_score * self.usage_weight
        )

        # Apply ADHD multiplier
        unified = base_score * adhd_mult

        # Clamp to 0.0-1.0
        unified = max(0.0, min(1.0, unified))

        # Calculate confidence (average of component confidences)
        confidence = (ast_conf + lsp_conf + usage_conf) / 3.0

        breakdown = ComplexityBreakdown(
            ast_score=ast_score,
            lsp_score=lsp_score,
            usage_score=usage_score,
            adhd_multiplier=adhd_mult,
            unified_score=unified,
            confidence=confidence
        )

        logger.info(
            f"Unified complexity for {file_path}:{symbol} = {unified:.3f} "
            f"(AST:{ast_score:.2f} LSP:{lsp_score:.2f} Usage:{usage_score:.2f} "
            f"ADHD:{adhd_mult:.2f}x) confidence:{confidence:.2f}"
        )

        return breakdown


# Global singleton
_complexity_coordinator = None


async def get_complexity_coordinator() -> ComplexityCoordinator:
    """
    Get or create complexity coordinator singleton.

    Returns:
        ComplexityCoordinator instance
    """
    global _complexity_coordinator

    if _complexity_coordinator is None:
        _complexity_coordinator = ComplexityCoordinator()

    return _complexity_coordinator


async def get_unified_complexity(
    file_path: str,
    symbol: Optional[str] = None,
    user_id: str = "default"
) -> Dict:
    """
    Convenience function for getting unified complexity.

    Args:
        file_path: File path
        symbol: Optional function/class name
        user_id: User identifier

    Returns:
        Dictionary with complexity breakdown

    Example:
        >>> complexity = await get_unified_complexity("auth.py", "login")
        >>> logger.info(f"Complexity: {complexity['unified_score']:.2f}")
        >>> logger.info(f"Interpretation: {complexity['interpretation']}")
    """
    coordinator = await get_complexity_coordinator()
    breakdown = await coordinator.get_unified_complexity(file_path, symbol, user_id)
    return breakdown.to_dict()
