"""
Serena v2 ADHD Code Navigation Features

ADHD-optimized code exploration with progressive disclosure, complexity awareness,
and cognitive load management for neurodivergent developers.
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class CodeComplexityAnalyzer:
    """Analyzes code complexity for ADHD-friendly presentation."""

    # Complexity weight factors
    COMPLEXITY_WEIGHTS = {
        "line_count": 0.1,
        "nesting_depth": 0.3,
        "cyclomatic_complexity": 0.4,
        "cognitive_complexity": 0.2
    }

    @staticmethod
    def calculate_function_complexity(symbol: Dict[str, Any]) -> float:
        """Calculate complexity score for a function symbol (0.0 - 1.0)."""
        try:
            # Extract range information
            symbol_range = symbol.get("range", {})
            start_line = symbol_range.get("start", {}).get("line", 0)
            end_line = symbol_range.get("end", {}).get("line", 0)
            line_count = max(1, end_line - start_line)

            # Basic complexity factors
            line_complexity = min(line_count / 50.0, 1.0)  # 50+ lines = high complexity

            # Estimate nesting from symbol kind and detail
            kind = symbol.get("kind", 0)
            detail = symbol.get("detail", "")

            # Function kinds that suggest complexity
            complex_kinds = {6, 12}  # Method, Function
            nesting_complexity = 0.3 if kind in complex_kinds else 0.1

            # Look for complexity indicators in detail/name
            name = symbol.get("name", "").lower()
            complexity_indicators = ["async", "generator", "decorator", "property"]
            detail_complexity = 0.2 if any(indicator in name or indicator in detail.lower() for indicator in complexity_indicators) else 0.0

            total_complexity = min(
                line_complexity * CodeComplexityAnalyzer.COMPLEXITY_WEIGHTS["line_count"] +
                nesting_complexity * CodeComplexityAnalyzer.COMPLEXITY_WEIGHTS["nesting_depth"] +
                detail_complexity * CodeComplexityAnalyzer.COMPLEXITY_WEIGHTS["cognitive_complexity"],
                1.0
            )

            return total_complexity

        except Exception as e:
            logger.error(f"Complexity calculation failed: {e}")
            return 0.5  # Default moderate complexity

    @staticmethod
    def categorize_complexity(score: float) -> Tuple[str, str]:
        """Categorize complexity score into ADHD-friendly labels."""
        if score <= 0.3:
            return ("🟢 Simple", "Easy to understand and modify")
        elif score <= 0.6:
            return ("🟡 Moderate", "Requires some focus but manageable")
        elif score <= 0.8:
            return ("🟠 Complex", "Consider breaking into smaller pieces")
        else:
            return ("🔴 Very Complex", "High cognitive load - tackle during peak focus")


class ADHDCodeNavigator:
    """
    ADHD-optimized code navigation with progressive disclosure and complexity awareness.

    NOW INTEGRATED WITH ADHD ENGINE for dynamic, personalized accommodations!

    Features:
    - Progressive disclosure of complex code structures
    - Complexity-based filtering and warnings (DYNAMIC per user state)
    - Context preservation during navigation
    - Gentle guidance for overwhelming code sections
    - Smart result limiting based on real-time attention state
    """

    def __init__(self, user_id: str = "default"):
        """
        Initialize ADHD Code Navigator.

        Args:
            user_id: User identifier for personalized ADHD accommodations
        """
        self.user_id = user_id
        self.navigation_context = {}

        # Legacy hardcoded values (fallback when ADHD Engine unavailable or feature flag OFF)
        self._default_max_initial_results = 10
        self._default_complexity_threshold = 0.7
        self._default_focus_mode_limit = 5
        self._default_max_context_depth = 3

        # ADHD-friendly configuration (static)
        self.show_complexity_indicators = True
        self.enable_progressive_disclosure = True
        self.enable_gentle_warnings = True

        # ADHD Engine integration (initialized in initialize())
        self.adhd_config = None
        self.feature_flags = None

    async def initialize(self, workspace_path: Path) -> None:
        """
        Initialize ADHD navigator for workspace.

        Connects to ADHD Engine for dynamic accommodations if available.
        """
        self.workspace_path = workspace_path

        # Connect to ADHD Engine (if available)
        try:
            # Import here to avoid circular dependencies
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "adhd_engine"))

            from adhd_config_service import get_adhd_config_service
            from feature_flags import ADHDFeatureFlags, FEATURE_ADHD_ENGINE_SERENA

            self.adhd_config = await get_adhd_config_service()
            self.feature_flags = ADHDFeatureFlags(self.adhd_config.redis_client)

            logger.info("✅ ADHD Code Navigator connected to ADHD Engine")

        except Exception as e:
            logger.warning(f"⚠️ ADHD Engine unavailable, using defaults: {e}")
            self.adhd_config = None
            self.feature_flags = None

        logger.info("🧠 ADHD Code Navigator initialized")

    async def get_max_initial_results(self) -> int:
        """
        Get max initial results dynamically from ADHD Engine.

        Returns dynamic value based on attention state or fallback to default.
        """
        # Check feature flag
        if self.feature_flags and self.adhd_config:
            try:
                from feature_flags import FEATURE_ADHD_ENGINE_SERENA

                if await self.feature_flags.is_enabled(
                    FEATURE_ADHD_ENGINE_SERENA,
                    "serena",
                    self.user_id
                ):
                    return await self.adhd_config.get_max_results(self.user_id)
            except Exception as e:
                logger.error(f"ADHD Engine query failed: {e}")

        # Fallback to hardcoded default
        return self._default_max_initial_results

    async def get_complexity_threshold(self) -> float:
        """Get complexity threshold dynamically from ADHD Engine."""
        if self.feature_flags and self.adhd_config:
            try:
                from feature_flags import FEATURE_ADHD_ENGINE_SERENA

                if await self.feature_flags.is_enabled(
                    FEATURE_ADHD_ENGINE_SERENA,
                    "serena",
                    self.user_id
                ):
                    return await self.adhd_config.get_complexity_threshold(self.user_id)
            except Exception as e:
                logger.error(f"ADHD Engine query failed: {e}")

        return self._default_complexity_threshold

    async def get_focus_mode_limit(self) -> int:
        """Get focus mode limit dynamically from ADHD Engine."""
        if self.feature_flags and self.adhd_config:
            try:
                from feature_flags import FEATURE_ADHD_ENGINE_SERENA

                if await self.feature_flags.is_enabled(
                    FEATURE_ADHD_ENGINE_SERENA,
                    "serena",
                    self.user_id
                ):
                    return await self.adhd_config.get_focus_mode_limit(self.user_id)
            except Exception as e:
                logger.error(f"ADHD Engine query failed: {e}")

        return self._default_focus_mode_limit

    async def get_max_context_depth(self) -> int:
        """Get max context depth dynamically from ADHD Engine."""
        if self.feature_flags and self.adhd_config:
            try:
                from feature_flags import FEATURE_ADHD_ENGINE_SERENA

                if await self.feature_flags.is_enabled(
                    FEATURE_ADHD_ENGINE_SERENA,
                    "serena",
                    self.user_id
                ):
                    return await self.adhd_config.get_context_depth(self.user_id)
            except Exception as e:
                logger.error(f"ADHD Engine query failed: {e}")

        return self._default_max_context_depth

    async def filter_symbols_for_focus(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter symbols for focus mode - show only essential items."""
        if not symbols:
            return symbols

        # In focus mode, prioritize:
        # 1. Public functions/methods (kind 6, 12)
        # 2. Classes (kind 5)
        # 3. Important variables/constants (kind 13, 14)

        essential_kinds = {5, 6, 12, 13, 14}  # Class, Function, Method, Variable, Constant
        filtered_symbols = []

        for symbol in symbols:
            kind = symbol.get("kind", 0)
            name = symbol.get("name", "")

            # Include if essential kind
            if kind in essential_kinds:
                # Add complexity indicator for ADHD users
                if self.show_complexity_indicators:
                    complexity = CodeComplexityAnalyzer.calculate_function_complexity(symbol)
                    complexity_label, complexity_desc = CodeComplexityAnalyzer.categorize_complexity(complexity)

                    symbol["_adhd_metadata"] = {
                        "complexity_score": complexity,
                        "complexity_label": complexity_label,
                        "complexity_description": complexity_desc,
                        "focus_mode_filtered": True
                    }

                filtered_symbols.append(symbol)

        # Sort by complexity (simple first) for ADHD users
        filtered_symbols.sort(key=lambda s: s.get("_adhd_metadata", {}).get("complexity_score", 0.5))

        # Limit results in focus mode (NOW DYNAMIC!)
        focus_limit = await self.get_focus_mode_limit()
        if len(filtered_symbols) > focus_limit:
            truncated = filtered_symbols[:focus_limit]
            logger.debug(f"🎯 Focus mode: showing {len(truncated)}/{len(filtered_symbols)} symbols")
            return truncated

        return filtered_symbols

    async def apply_progressive_disclosure(
        self,
        results: List[Dict[str, Any]],
        max_initial_items: int = None
    ) -> List[Dict[str, Any]]:
        """Apply progressive disclosure to large result sets (NOW DYNAMIC!)."""
        # Get dynamic max from ADHD Engine
        if max_initial_items is None:
            max_initial_items = await self.get_max_initial_results()

        max_items = max_initial_items

        if len(results) <= max_items:
            return results

        # Sort by relevance/importance for ADHD users
        sorted_results = self._sort_by_importance(results)

        # Take initial set
        initial_results = sorted_results[:max_items]

        # Add metadata about remaining items
        remaining_count = len(results) - max_items
        disclosure_metadata = {
            "_progressive_disclosure": {
                "initial_count": len(initial_results),
                "total_count": len(results),
                "remaining_count": remaining_count,
                "expansion_available": True,
                "adhd_friendly_message": f"Showing {len(initial_results)} most relevant results. {remaining_count} more available - use 'show more' to expand."
            }
        }

        # Add metadata to first result for UI consumption
        if initial_results:
            initial_results[0]["_disclosure_info"] = disclosure_metadata

        logger.debug(f"📋 Progressive disclosure: {len(initial_results)}/{len(results)} results shown initially")
        return initial_results

    def _sort_by_importance(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort results by importance for ADHD users."""
        def importance_score(item):
            score = 0.5  # Base score

            # Boost based on item type/kind
            kind = item.get("kind", 0)
            name = item.get("name", "").lower()

            # Functions and classes are typically more important
            if kind in {5, 6, 12}:  # Class, Function, Method
                score += 0.3

    async def filter_symbols_for_focus(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter symbols for focus mode - show only essential items."""
        if not symbols:
            return symbols

        # In focus mode, prioritize:
        # 1. Public functions/methods (kind 6, 12)
        # 2. Classes (kind 5)
        # 3. Important variables/constants (kind 13, 14)

        essential_kinds = {5, 6, 12, 13, 14}  # Class, Function, Method, Variable, Constant
        filtered_symbols = []

        for symbol in symbols:
            kind = symbol.get("kind", 0)
            name = symbol.get("name", "")

            # Include if essential kind
            if kind in essential_kinds:
                # Add complexity indicator for ADHD users
                if self.show_complexity_indicators:
                    complexity = CodeComplexityAnalyzer.calculate_function_complexity(symbol)
                    complexity_label, complexity_desc = CodeComplexityAnalyzer.categorize_complexity(complexity)

                    symbol["_adhd_metadata"] = {
                        "complexity_score": complexity,
                        "complexity_label": complexity_label,
                        "complexity_description": complexity_desc,
                        "focus_mode_filtered": True
                    }

                filtered_symbols.append(symbol)

        # Sort by complexity (simple first) for ADHD users
        filtered_symbols.sort(key=lambda s: s.get("_adhd_metadata", {}).get("complexity_score", 0.5))

        # Limit results in focus mode
        if len(filtered_symbols) > self.focus_mode_limit:
            truncated = filtered_symbols[:self.focus_mode_limit]
            logger.debug(f"🎯 Focus mode: showing {len(truncated)}/{len(filtered_symbols)} symbols")
            return truncated

        return filtered_symbols

    async def apply_progressive_disclosure(
        self,
        results: List[Dict[str, Any]],
        max_initial_items: int = None
    ) -> List[Dict[str, Any]]:
        """Apply progressive disclosure to large result sets."""
        max_items = max_initial_items or self.max_initial_results

        if len(results) <= max_items:
            return results

        # Sort by relevance/importance for ADHD users
        sorted_results = self._sort_by_importance(results)

        # Take initial set
        initial_results = sorted_results[:max_items]

        # Add metadata about remaining items
        remaining_count = len(results) - max_items
        disclosure_metadata = {
            "_progressive_disclosure": {
                "initial_count": len(initial_results),
                "total_count": len(results),
                "remaining_count": remaining_count,
                "expansion_available": True,
                "adhd_friendly_message": f"Showing {len(initial_results)} most relevant results. {remaining_count} more available - use 'show more' to expand."
            }
        }

        # Add metadata to first result for UI consumption
        if initial_results:
            initial_results[0]["_disclosure_info"] = disclosure_metadata

        logger.debug(f"📋 Progressive disclosure: {len(initial_results)}/{len(results)} results shown initially")
        return initial_results

    def _sort_by_importance(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort results by importance for ADHD users."""
        def importance_score(item):
            score = 0.5  # Base score

            # Boost based on item type/kind
            kind = item.get("kind", 0)
            name = item.get("name", "").lower()

            # Functions and classes are typically more important
            if kind in {5, 6, 12}:  # Class, Function, Method
                score += 0.3

            # Public items (no underscore prefix) are more important
            if name and not name.startswith("_"):
                score += 0.2

            # Items with clear, descriptive names
            if len(name) > 3 and not name.startswith("temp") and not name.startswith("tmp"):
                score += 0.1

            # Penalize very long names (often auto-generated)
            if len(name) > 30:
                score -= 0.2

            return min(score, 1.0)

        return sorted(results, key=importance_score, reverse=True)

    async def filter_for_focus_mode(self, lsp_response) -> Any:
        """Filter LSP response for focus mode."""
        if not hasattr(lsp_response, 'result'):
            return lsp_response

        # Apply complexity filtering
        if isinstance(lsp_response.result, list):
            # Filter out overly complex items in focus mode
            filtered_result = []

            for item in lsp_response.result:
                complexity = CodeComplexityAnalyzer.calculate_function_complexity(item)

                if complexity <= self.complexity_threshold:
                    # Add ADHD metadata
                    item["_adhd_metadata"] = {
                        "complexity_score": complexity,
                        "focus_mode_approved": True,
                        "cognitive_load": "low" if complexity <= 0.4 else "medium"
                    }
                    filtered_result.append(item)

            logger.debug(f"🎯 Focus filter: {len(filtered_result)}/{len(lsp_response.result)} items passed complexity filter")
            lsp_response.result = filtered_result

        return lsp_response

    # Context and Guidance Generation

    async def generate_navigation_guidance(
        self,
        current_file: str,
        current_function: str = None,
        navigation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate ADHD-friendly navigation guidance."""
        guidance = {
            "current_context": f"📍 You are in: {Path(current_file).name}",
            "suggestions": [],
            "complexity_warning": None,
            "focus_recommendations": []
        }

        try:
            # Add function context if available
            if current_function:
                guidance["current_context"] += f" → {current_function}()"

            # Analyze recent navigation for patterns
            if navigation_history:
                recent_files = [entry.get("file_path") for entry in navigation_history[-5:]]
                unique_files = len(set(recent_files))

                if unique_files > 3:
                    guidance["complexity_warning"] = "⚠️ You've been jumping between multiple files. Consider focusing on one area at a time."

                # Suggest returning to frequently visited files
                file_counts = {}
                for file_path in recent_files:
                    if file_path:
                        file_counts[file_path] = file_counts.get(file_path, 0) + 1

                frequent_file = max(file_counts.items(), key=lambda x: x[1], default=(None, 0))
                if frequent_file[1] > 1 and frequent_file[0] != current_file:
                    guidance["suggestions"].append(
                        f"💡 Return to {Path(frequent_file[0]).name} (visited {frequent_file[1]} times recently)"
                    )

            # General ADHD recommendations
            guidance["focus_recommendations"] = [
                "🎯 Use focus mode to reduce distractions",
                "🍞 Check breadcrumbs to see your path",
                "📊 Watch complexity indicators for cognitive load"
            ]

            return guidance

        except Exception as e:
            logger.error(f"Failed to generate navigation guidance: {e}")
            return {"error": str(e)}

    async def create_code_summary(
        self,
        file_path: str,
        symbols: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create ADHD-friendly code summary for file."""
        try:
            if not symbols:
                return {
                    "summary": f"📄 {Path(file_path).name}",
                    "details": "No symbols detected",
                    "complexity": "unknown"
                }

            # Categorize symbols
            categories = {
                "classes": [s for s in symbols if s.get("kind") == 5],
                "functions": [s for s in symbols if s.get("kind") in {6, 12}],  # Function, Method
                "variables": [s for s in symbols if s.get("kind") in {13, 14}],  # Variable, Constant
                "other": [s for s in symbols if s.get("kind") not in {5, 6, 12, 13, 14}]
            }

            # Calculate overall file complexity
            complexities = [
                CodeComplexityAnalyzer.calculate_function_complexity(symbol)
                for symbol in symbols
            ]
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0

            # Generate ADHD-friendly summary
            summary_parts = []
            if categories["classes"]:
                summary_parts.append(f"{len(categories['classes'])} classes")
            if categories["functions"]:
                summary_parts.append(f"{len(categories['functions'])} functions")
            if categories["variables"]:
                summary_parts.append(f"{len(categories['variables'])} variables")

            summary_text = f"📄 {Path(file_path).name}: " + ", ".join(summary_parts)

            # Complexity assessment
            complexity_label, complexity_desc = CodeComplexityAnalyzer.categorize_complexity(avg_complexity)

            return {
                "summary": summary_text,
                "details": {
                    "categories": {k: len(v) for k, v in categories.items()},
                    "total_symbols": len(symbols),
                    "complexity_score": avg_complexity,
                    "complexity_label": complexity_label,
                    "complexity_description": complexity_desc
                },
                "complexity": complexity_label,
                "cognitive_load_estimate": "low" if avg_complexity <= 0.4 else "medium" if avg_complexity <= 0.7 else "high"
            }

        except Exception as e:
            logger.error(f"Failed to create code summary: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for ADHD features."""
        # Get current dynamic values
        max_results = await self.get_max_initial_results()
        complexity_threshold = await self.get_complexity_threshold()
        focus_limit = await self.get_focus_mode_limit()

        return {
            "status": "🚀 Active",
            "adhd_engine_connected": self.adhd_config is not None,
            "features_enabled": {
                "complexity_indicators": self.show_complexity_indicators,
                "progressive_disclosure": self.enable_progressive_disclosure,
                "gentle_warnings": self.enable_gentle_warnings
            },
            "configuration": {
                "max_initial_results": max_results,
                "complexity_threshold": complexity_threshold,
                "focus_mode_limit": focus_limit,
                "source": "adhd_engine" if self.adhd_config else "default"
            }
        }

    async def close(self) -> None:
        """Close ADHD navigator."""
        logger.debug("🧠 ADHD Code Navigator closed")


class ProgressiveDisclosure:
    """Manages progressive disclosure of complex code information."""

    def __init__(self, max_initial_items: int = 10, expand_threshold: int = 5):
        self.max_initial_items = max_initial_items
        self.expand_threshold = expand_threshold

    async def apply_to_results(
        self,
        results: List[Dict[str, Any]],
        result_type: str = "general"
    ) -> Dict[str, Any]:
        """Apply progressive disclosure to results."""
        if len(results) <= self.max_initial_items:
            return {
                "items": results,
                "disclosure_applied": False,
                "total_count": len(results)
            }

        # Sort by importance/relevance
        sorted_results = self._prioritize_results(results, result_type)

        initial_items = sorted_results[:self.max_initial_items]
        remaining_items = sorted_results[self.max_initial_items:]

        # Add disclosure metadata
        for item in initial_items:
            item["_disclosed"] = True

        return {
            "items": initial_items,
            "disclosure_applied": True,
            "total_count": len(results),
            "remaining_count": len(remaining_items),
            "expansion_message": f"💡 Showing {len(initial_items)} most relevant items. {len(remaining_items)} more available.",
            "remaining_items": remaining_items  # Available for expansion
        }

    def _prioritize_results(self, results: List[Dict[str, Any]], result_type: str) -> List[Dict[str, Any]]:
        """Prioritize results based on type and ADHD-friendly criteria."""
        def priority_score(item):
            score = 0.5  # Base score

            # Type-specific prioritization
            if result_type == "symbols":
                kind = item.get("kind", 0)
                # Prioritize functions and classes
                if kind in {5, 6, 12}:  # Class, Function, Method
                    score += 0.3

                # Public symbols are often more important
                name = item.get("name", "")
                if name and not name.startswith("_"):
                    score += 0.2

            elif result_type == "references":
                # Prioritize references in the same file or nearby files
                uri = item.get("uri", "")
                if uri:
                    # Local references are often more relevant
                    score += 0.2

            elif result_type == "definitions":
                # Prioritize based on accessibility and clarity
                name = item.get("name", "")
                if name and len(name) > 3:  # Descriptive names
                    score += 0.1

            return min(score, 1.0)

        return sorted(results, key=priority_score, reverse=True)


class CognitiveLoadManager:
    """
    Manages cognitive load during code navigation.

    NOW INTEGRATED WITH ADHD ENGINE for personalized thresholds!
    """

    def __init__(self, user_id: str = "default"):
        """
        Initialize Cognitive Load Manager.

        Args:
            user_id: User identifier for personalized load thresholds
        """
        self.user_id = user_id
        self.current_load = 0.0
        self.load_history = []

        # Legacy defaults (fallback)
        self._default_max_load_threshold = 0.8
        self._default_break_suggestion_threshold = 0.9

        # ADHD Engine integration
        self.adhd_config = None
        self.feature_flags = None

    async def initialize(self) -> None:
        """Connect to ADHD Engine."""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "adhd_engine"))

            from adhd_config_service import get_adhd_config_service
            from feature_flags import ADHDFeatureFlags

            self.adhd_config = await get_adhd_config_service()
            self.feature_flags = ADHDFeatureFlags(self.adhd_config.redis_client)

            logger.info("✅ Cognitive Load Manager connected to ADHD Engine")

        except Exception as e:
            logger.warning(f"⚠️ ADHD Engine unavailable: {e}")

    async def get_max_load_threshold(self) -> float:
        """Get max load threshold dynamically from ADHD Engine."""
        if self.feature_flags and self.adhd_config:
            try:
                from feature_flags import FEATURE_ADHD_ENGINE_SERENA

                if await self.feature_flags.is_enabled(
                    FEATURE_ADHD_ENGINE_SERENA,
                    "serena",
                    self.user_id
                ):
                    return await self.adhd_config.get_cognitive_load_threshold(self.user_id)
            except Exception as e:
                logger.error(f"ADHD Engine query failed: {e}")

        return self._default_max_load_threshold

    async def get_break_suggestion_threshold(self) -> float:
        """Get break suggestion threshold dynamically from ADHD Engine."""
        if self.feature_flags and self.adhd_config:
            try:
                from feature_flags import FEATURE_ADHD_ENGINE_SERENA

                if await self.feature_flags.is_enabled(
                    FEATURE_ADHD_ENGINE_SERENA,
                    "serena",
                    self.user_id
                ):
                    return await self.adhd_config.get_break_suggestion_threshold(self.user_id)
            except Exception as e:
                logger.error(f"ADHD Engine query failed: {e}")

        return self._default_break_suggestion_threshold

    async def assess_navigation_load(
        self,
        action: str,
        result_complexity: float,
        result_count: int,
        file_path: str = None
    ) -> Dict[str, Any]:
        """Assess cognitive load for navigation action (NOW WITH DYNAMIC THRESHOLDS!)."""
        try:
            # Calculate load contribution
            action_loads = {
                "find_definition": 0.2,
                "find_references": 0.4,
                "document_symbols": 0.3,
                "workspace_symbols": 0.6,
                "hover": 0.1
            }

            base_load = action_loads.get(action, 0.3)

            # Adjust for result complexity
            complexity_load = result_complexity * 0.3

            # Adjust for result count (too many results = cognitive overload)
            count_load = min(result_count / 20.0, 0.4)

            total_load = min(base_load + complexity_load + count_load, 1.0)

            # Update current load (with decay over time)
            self._update_cognitive_load(total_load)

            # Get DYNAMIC thresholds from ADHD Engine
            max_threshold = await self.get_max_load_threshold()
            break_threshold = await self.get_break_suggestion_threshold()

            # Check if break recommended from ADHD Engine
            should_break = False
            break_reason = ""
            if self.adhd_config:
                should_break, break_reason = await self.adhd_config.should_suggest_break(self.user_id)

            # Generate recommendations
            recommendations = []
            if should_break:
                recommendations.append(f"☕ {break_reason}")
            elif self.current_load > break_threshold:
                recommendations.append("☕ Consider taking a break - cognitive load is high")
            elif self.current_load > max_threshold:
                recommendations.append("🎯 Focus mode recommended to reduce information overload")

            # File-specific recommendations
            if file_path and result_complexity > 0.7:
                recommendations.append(f"⚠️ {Path(file_path).name} is complex - consider breaking into smaller functions")

            return {
                "current_load": self.current_load,
                "load_contribution": total_load,
                "load_level": self._categorize_load(self.current_load),
                "recommendations": recommendations,
                "break_suggested": should_break or self.current_load > break_threshold,
                "adhd_engine_active": self.adhd_config is not None
            }

        except Exception as e:
            logger.error(f"Cognitive load assessment failed: {e}")
            return {"error": str(e)}

    def _update_cognitive_load(self, new_load: float):
        """Update current cognitive load with time-based decay."""
        current_time = datetime.now(timezone.utc)

        # Apply time decay (load decreases over time)
        if self.load_history:
            last_time = self.load_history[-1]["timestamp"]
            time_diff = (current_time - last_time).total_seconds() / 60  # minutes
            decay_factor = max(0.1, 1.0 - (time_diff / 30.0))  # 30-minute full decay
            self.current_load *= decay_factor

        # Add new load
        self.current_load = min(self.current_load + new_load, 1.0)

        # Track history
        self.load_history.append({
            "timestamp": current_time,
            "load": new_load,
            "cumulative_load": self.current_load
        })

        # Keep history manageable
        if len(self.load_history) > 50:
            self.load_history = self.load_history[-25:]

    def _categorize_load(self, load: float) -> str:
        """Categorize cognitive load for ADHD-friendly display."""
        if load <= 0.3:
            return "🟢 Low - comfortable pace"
        elif load <= 0.6:
            return "🟡 Moderate - manageable focus"
        elif load <= 0.8:
            return "🟠 High - consider focusing"
        else:
            return "🔴 Overload - break recommended"


class ContextPreserver:
    """Preserves navigation context for ADHD context switching support."""

    def __init__(self):
        self.context_stack = []
        self.max_context_depth = 10
        self.current_focus_area = None

    async def push_context(
        self,
        file_path: str,
        location: Dict[str, Any],
        purpose: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Push new context onto stack."""
        context_id = f"ctx_{datetime.now().timestamp()}"

        context_entry = {
            "id": context_id,
            "file_path": file_path,
            "location": location,
            "purpose": purpose,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_name": Path(file_path).name
        }

        self.context_stack.append(context_entry)

        # Maintain manageable stack size for ADHD users
        if len(self.context_stack) > self.max_context_depth:
            removed_context = self.context_stack.pop(0)
            logger.debug(f"🗑️ Removed old context: {removed_context['purpose']}")

        logger.debug(f"📌 Context pushed: {purpose} in {Path(file_path).name}")
        return context_id

    async def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from stack (go back)."""
        if self.context_stack:
            context = self.context_stack.pop()
            logger.debug(f"⬅️ Context popped: {context['purpose']}")
            return context
        return None

    async def get_context_breadcrumbs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent context breadcrumbs for ADHD orientation."""
        recent_contexts = self.context_stack[-limit:] if self.context_stack else []

        # Add ADHD-friendly descriptions
        for context in recent_contexts:
            context["breadcrumb_text"] = f"{context['file_name']} → {context['purpose']}"

        return recent_contexts

    async def suggest_return_points(self) -> List[Dict[str, Any]]:
        """Suggest good return points for ADHD context recovery."""
        if not self.context_stack:
            return []

        # Find contexts that were significant work areas
        work_contexts = []
        for context in self.context_stack:
            purpose = context.get("purpose", "").lower()
            if any(keyword in purpose for keyword in ["edit", "implement", "debug", "refactor"]):
                work_contexts.append({
                    **context,
                    "return_reason": "🔧 Active work area",
                    "return_priority": "high"
                })

        return work_contexts[-3:]  # Last 3 work contexts