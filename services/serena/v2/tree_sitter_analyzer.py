"""
Serena v2 Tree-sitter Code Analyzer

Enhanced code structure parsing with ADHD-optimized complexity analysis.
Complements LSP semantic understanding with detailed syntactic insights.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    from tree_sitter import Language, Parser, Node

    # Try to import language bindings with proper API
    try:
        import tree_sitter_python as tspython
        import tree_sitter_javascript as tsjavascript
        import tree_sitter_typescript as tstypescript
        import tree_sitter_rust as tsrust
        import tree_sitter_go as tsgo
        TREE_SITTER_AVAILABLE = True
    except (ImportError, AttributeError) as e:
        TREE_SITTER_AVAILABLE = False
        logging.warning(f"Tree-sitter language bindings not available: {e}")

except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("Tree-sitter not available - install tree_sitter and language bindings")

logger = logging.getLogger(__name__)


class CodeComplexity(str, Enum):
    """Code complexity levels for ADHD users."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class StructuralElement:
    """Represents a structural element in code."""
    name: str
    type: str  # function, class, variable, etc.
    start_line: int
    end_line: int
    complexity_score: float
    complexity_level: CodeComplexity
    children: List['StructuralElement'] = None
    metadata: Dict[str, Any] = None
    adhd_insights: List[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}
        if self.adhd_insights is None:
            self.adhd_insights = []


@dataclass
class CodeStructureAnalysis:
    """Complete code structure analysis results."""
    file_path: str
    language: str
    elements: List[StructuralElement]
    overall_complexity: float
    complexity_level: CodeComplexity
    lines_of_code: int
    analysis_duration_ms: float
    adhd_recommendations: List[str]
    timestamp: datetime


class TreeSitterAnalyzer:
    """
    Tree-sitter based code analyzer with ADHD optimizations.

    Features:
    - Multi-language support (Python, JavaScript, TypeScript, Rust, Go)
    - Detailed structural analysis beyond LSP capabilities
    - ADHD-friendly complexity scoring and insights
    - Performance optimized parsing with caching
    - Integration with Serena's navigation system
    """

    def __init__(self):
        self.languages = {}
        self.parsers = {}
        self.initialized = False

        # ADHD-specific configuration
        self.complexity_thresholds = {
            CodeComplexity.SIMPLE: 0.3,
            CodeComplexity.MODERATE: 0.6,
            CodeComplexity.COMPLEX: 0.8,
            CodeComplexity.VERY_COMPLEX: 1.0
        }

        # Performance tracking
        self.analysis_stats = {
            "files_analyzed": 0,
            "total_analysis_time_ms": 0.0,
            "average_analysis_time_ms": 0.0,
            "cache_hits": 0,
            "parse_errors": 0
        }

    async def initialize(self) -> bool:
        """Initialize Tree-sitter languages and parsers with graceful fallback."""
        if not TREE_SITTER_AVAILABLE:
            logger.warning("Tree-sitter packages not available - LSP-only mode enabled")
            return False

        try:
            # Test Tree-sitter version compatibility first
            compatibility_test_passed = await self._test_tree_sitter_compatibility()

            if not compatibility_test_passed:
                logger.warning(
                    "🌳 Tree-sitter version compatibility issues detected. "
                    "Serena Layer 1 will run in LSP-only mode with full functionality."
                )
                return False

            # Initialize supported languages with proper API
            language_configs = {}

            # Try each language with different API patterns
            language_modules = {
                "python": tspython,
                "javascript": tsjavascript,
                "typescript": tstypescript,
                "rust": tsrust,
                "go": tsgo
            }

            for lang_name, module in language_modules.items():
                try:
                    # Get language capsule from module
                    if hasattr(module, 'language'):
                        language_capsule = module.language()
                    elif hasattr(module, 'LANGUAGE'):
                        language_capsule = module.LANGUAGE
                    else:
                        logger.debug(f"Unknown API for {lang_name} Tree-sitter module")
                        continue

                    # Create Language object from capsule
                    language = Language(language_capsule)
                    language_configs[lang_name] = language

                except Exception as e:
                    logger.debug(f"Failed to load {lang_name} language: {e}")
                    continue

            for lang_name, language in language_configs.items():
                try:
                    self.languages[lang_name] = language
                    parser = Parser()
                    parser.language = language
                    self.parsers[lang_name] = parser
                    logger.debug(f"🌳 Initialized Tree-sitter for {lang_name}")
                except Exception as e:
                    logger.debug(f"Failed to initialize {lang_name} parser: {e}")
                    continue

            self.initialized = len(self.parsers) > 0

            if self.initialized:
                logger.info(f"🌳 Tree-sitter analyzer ready with {len(self.parsers)} working parsers")
            else:
                logger.warning(
                    "🌳 Tree-sitter parsers unavailable due to version compatibility. "
                    "Layer 1 navigation intelligence fully functional with LSP-only mode."
                )

            return self.initialized

        except Exception as e:
            logger.warning(f"Tree-sitter initialization failed - LSP-only mode enabled: {e}")
            return False

    async def _test_tree_sitter_compatibility(self) -> bool:
        """Test Tree-sitter version compatibility before full initialization."""
        try:
            # Simple compatibility test
            test_language = tspython.language()
            test_lang_obj = Language(test_language)
            test_parser = Parser()
            test_parser.language = test_lang_obj

            # Try a simple parse
            test_tree = test_parser.parse(b'x = 1')
            return test_tree is not None and not test_tree.root_node.has_error

        except Exception as e:
            logger.debug(f"Tree-sitter compatibility test failed: {e}")
            return False

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        if not self.initialized:
            return None

        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go"
        }

        file_ext = Path(file_path).suffix.lower()
        return extension_map.get(file_ext)

    async def analyze_file(
        self,
        file_path: str,
        content: str = None,
        use_cache: bool = True
    ) -> Optional[CodeStructureAnalysis]:
        """
        Analyze code structure using Tree-sitter with ADHD optimizations.

        Args:
            file_path: Path to the file to analyze
            content: File content (if None, will read from file)
            use_cache: Whether to use cached results

        Returns:
            CodeStructureAnalysis with detailed structural insights
        """
        if not self.initialized:
            logger.warning("Tree-sitter analyzer not initialized")
            return None

        start_time = time.time()

        try:
            # Detect language
            language = self.detect_language(file_path)
            if not language or language not in self.parsers:
                logger.debug(f"Unsupported language for {file_path}")
                return None

            # Read file content if not provided
            if content is None:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
                    return None

            # Parse with Tree-sitter
            parser = self.parsers[language]
            tree = parser.parse(bytes(content, 'utf8'))

            if tree.root_node.has_error:
                logger.warning(f"Parse errors in {file_path}")
                self.analysis_stats["parse_errors"] += 1

            # Calculate analysis duration
            analysis_duration = (time.time() - start_time) * 1000

            # Analyze structure
            analysis = await self._analyze_syntax_tree(
                tree.root_node, file_path, language, content, len(content.split('\n')), analysis_duration
            )

            # Update statistics
            self.analysis_stats["files_analyzed"] += 1
            self.analysis_stats["total_analysis_time_ms"] += analysis_duration
            self.analysis_stats["average_analysis_time_ms"] = (
                self.analysis_stats["total_analysis_time_ms"] / self.analysis_stats["files_analyzed"]
            )

            logger.debug(f"🌳 Analyzed {Path(file_path).name}: {len(analysis.elements)} elements in {analysis_duration:.1f}ms")

            return analysis

        except Exception as e:
            logger.error(f"Tree-sitter analysis failed for {file_path}: {e}")
            return None

    async def _analyze_syntax_tree(
        self,
        root_node: Node,
        file_path: str,
        language: str,
        content: str,
        total_lines: int,
        analysis_duration_ms: float = 0.0
    ) -> CodeStructureAnalysis:
        """Analyze syntax tree and extract structural elements."""
        elements = []

        # Language-specific node type mappings
        important_node_types = {
            "python": {
                "function_definition": "function",
                "async_function_definition": "async_function",
                "class_definition": "class",
                "assignment": "variable",
                "import_statement": "import",
                "import_from_statement": "import"
            },
            "javascript": {
                "function_declaration": "function",
                "arrow_function": "function",
                "method_definition": "method",
                "class_declaration": "class",
                "variable_declaration": "variable"
            },
            "typescript": {
                "function_declaration": "function",
                "arrow_function": "function",
                "method_definition": "method",
                "class_declaration": "class",
                "interface_declaration": "interface",
                "type_alias_declaration": "type"
            },
            "rust": {
                "function_item": "function",
                "impl_item": "implementation",
                "struct_item": "struct",
                "enum_item": "enum",
                "trait_item": "trait"
            },
            "go": {
                "function_declaration": "function",
                "method_declaration": "method",
                "type_declaration": "type",
                "struct_type": "struct"
            }
        }

        node_mappings = important_node_types.get(language, {})

        # Traverse syntax tree
        def traverse_node(node: Node, depth: int = 0) -> List[StructuralElement]:
            node_elements = []

            # Check if this node represents a structural element
            if node.type in node_mappings:
                element = self._create_structural_element(
                    node, node_mappings[node.type], content, language, depth
                )
                if element:
                    node_elements.append(element)

            # Recursively process children (with depth limit for ADHD users)
            if depth < 5:  # Limit nesting depth for cognitive load management
                for child in node.children:
                    child_elements = traverse_node(child, depth + 1)
                    node_elements.extend(child_elements)

            return node_elements

        elements = traverse_node(root_node)

        # Calculate overall complexity
        overall_complexity = self._calculate_overall_complexity(elements, total_lines)
        complexity_level = self._determine_complexity_level(overall_complexity)

        # Generate ADHD recommendations
        adhd_recommendations = self._generate_adhd_recommendations(
            elements, overall_complexity, total_lines
        )

        return CodeStructureAnalysis(
            file_path=file_path,
            language=language,
            elements=elements,
            overall_complexity=overall_complexity,
            complexity_level=complexity_level,
            lines_of_code=total_lines,
            analysis_duration_ms=analysis_duration,
            adhd_recommendations=adhd_recommendations,
            timestamp=datetime.now(timezone.utc)
        )

    def _create_structural_element(
        self,
        node: Node,
        element_type: str,
        content: str,
        language: str,
        depth: int
    ) -> Optional[StructuralElement]:
        """Create a structural element from a Tree-sitter node."""
        try:
            # Extract name
            name = self._extract_node_name(node, content)
            if not name:
                return None

            # Calculate line numbers
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            # Calculate complexity
            complexity_score = self._calculate_node_complexity(node, element_type, depth)
            complexity_level = self._determine_complexity_level(complexity_score)

            # Generate ADHD insights
            adhd_insights = self._generate_element_insights(
                node, element_type, complexity_score, depth
            )

            # Extract metadata
            metadata = {
                "node_type": node.type,
                "depth": depth,
                "child_count": len(node.children),
                "line_span": end_line - start_line + 1,
                "language": language
            }

            return StructuralElement(
                name=name,
                type=element_type,
                start_line=start_line,
                end_line=end_line,
                complexity_score=complexity_score,
                complexity_level=complexity_level,
                metadata=metadata,
                adhd_insights=adhd_insights
            )

        except Exception as e:
            logger.error(f"Failed to create structural element: {e}")
            return None

    def _extract_node_name(self, node: Node, content: str) -> Optional[str]:
        """Extract the name of a structural element."""
        try:
            # Look for identifier child nodes
            for child in node.children:
                if child.type == "identifier":
                    return content[child.start_byte:child.end_byte]

            # Fallback: use the node's text up to first 50 chars
            node_text = content[node.start_byte:node.end_byte]
            return node_text.split('\n')[0][:50].strip()

        except Exception:
            return None

    def _calculate_node_complexity(self, node: Node, element_type: str, depth: int) -> float:
        """Calculate complexity score for a structural element."""
        base_complexity = 0.1

        # Type-based complexity
        type_complexity = {
            "function": 0.3,
            "async_function": 0.4,
            "class": 0.5,
            "method": 0.3,
            "variable": 0.1,
            "import": 0.05
        }

        complexity = base_complexity + type_complexity.get(element_type, 0.2)

        # Size-based complexity
        node_size = node.end_point[0] - node.start_point[0] + 1
        size_complexity = min(node_size / 50.0, 0.3)  # Max 0.3 for size
        complexity += size_complexity

        # Nesting complexity (ADHD users struggle with deep nesting)
        nesting_complexity = min(depth / 10.0, 0.2)  # Max 0.2 for nesting
        complexity += nesting_complexity

        # Child complexity (more children = more cognitive load)
        child_complexity = min(len(node.children) / 20.0, 0.2)  # Max 0.2 for children
        complexity += child_complexity

        return min(complexity, 1.0)

    def _determine_complexity_level(self, score: float) -> CodeComplexity:
        """Determine complexity level from score."""
        if score <= self.complexity_thresholds[CodeComplexity.SIMPLE]:
            return CodeComplexity.SIMPLE
        elif score <= self.complexity_thresholds[CodeComplexity.MODERATE]:
            return CodeComplexity.MODERATE
        elif score <= self.complexity_thresholds[CodeComplexity.COMPLEX]:
            return CodeComplexity.COMPLEX
        else:
            return CodeComplexity.VERY_COMPLEX

    def _calculate_overall_complexity(self, elements: List[StructuralElement], total_lines: int) -> float:
        """Calculate overall file complexity."""
        if not elements:
            return 0.1

        # Average element complexity
        avg_element_complexity = sum(e.complexity_score for e in elements) / len(elements)

        # File size factor
        size_factor = min(total_lines / 500.0, 0.3)

        # Element count factor
        count_factor = min(len(elements) / 30.0, 0.2)

        # Nesting depth factor
        max_depth = max((e.metadata.get("depth", 0) for e in elements), default=0)
        depth_factor = min(max_depth / 5.0, 0.2)

        overall = avg_element_complexity + size_factor + count_factor + depth_factor
        return min(overall, 1.0)

    def _generate_element_insights(
        self,
        node: Node,
        element_type: str,
        complexity_score: float,
        depth: int
    ) -> List[str]:
        """Generate ADHD-friendly insights for a structural element."""
        insights = []

        # Complexity insights
        if complexity_score > 0.8:
            insights.append("🔴 High complexity - consider breaking into smaller pieces")
        elif complexity_score > 0.6:
            insights.append("🟡 Moderate complexity - good candidate for focus mode")
        else:
            insights.append("🟢 Simple structure - easy to understand")

        # Depth insights
        if depth > 3:
            insights.append("🌀 Deeply nested - may be hard to follow")
        elif depth > 1:
            insights.append("📁 Nested structure - use breadcrumbs for navigation")

        # Type-specific insights
        if element_type == "function":
            line_count = node.end_point[0] - node.start_point[0] + 1
            if line_count > 50:
                insights.append("📏 Long function - consider splitting for readability")
            elif line_count < 5:
                insights.append("⚡ Concise function - quick to understand")

        elif element_type == "class":
            child_count = len(node.children)
            if child_count > 20:
                insights.append("🏗️ Large class - may benefit from decomposition")
            else:
                insights.append("🏠 Well-sized class - manageable scope")

        return insights

    def _generate_adhd_recommendations(
        self,
        elements: List[StructuralElement],
        overall_complexity: float,
        total_lines: int
    ) -> List[str]:
        """Generate ADHD-specific recommendations for the file."""
        recommendations = []

        # Overall complexity recommendations
        if overall_complexity > 0.8:
            recommendations.append("🎯 High complexity file - use focus mode when working here")
            recommendations.append("💡 Consider breaking into smaller modules")
        elif overall_complexity > 0.6:
            recommendations.append("🧠 Moderate complexity - good for focused work sessions")
        else:
            recommendations.append("✅ Simple structure - good for any energy level")

        # Size recommendations
        if total_lines > 500:
            recommendations.append("📄 Large file - use search and navigation aids")
        elif total_lines > 200:
            recommendations.append("📋 Medium file - use symbols outline for navigation")

        # Element distribution insights
        function_count = len([e for e in elements if e.type in ["function", "method"]])
        class_count = len([e for e in elements if e.type == "class"])

        if function_count > 20:
            recommendations.append("🔧 Many functions - consider grouping related ones")
        if class_count > 5:
            recommendations.append("🏗️ Multiple classes - each class might deserve its own file")

        # Complexity distribution
        complex_elements = [e for e in elements if e.complexity_score > 0.7]
        if len(complex_elements) > 3:
            recommendations.append("⚠️ Multiple complex elements - tackle one at a time")

        return recommendations[:5]  # Limit to 5 recommendations for ADHD users

    # Integration Methods

    def enhance_lsp_symbols(
        self,
        lsp_symbols: List[Dict[str, Any]],
        tree_analysis: CodeStructureAnalysis
    ) -> List[Dict[str, Any]]:
        """Enhance LSP symbols with Tree-sitter structural insights."""
        try:
            enhanced_symbols = []

            for lsp_symbol in lsp_symbols:
                enhanced_symbol = lsp_symbol.copy()

                # Find corresponding Tree-sitter element
                symbol_name = lsp_symbol.get("name", "")
                symbol_line = lsp_symbol.get("range", {}).get("start", {}).get("line", 0)

                matching_element = None
                for element in tree_analysis.elements:
                    if (element.name == symbol_name and
                        abs(element.start_line - symbol_line - 1) <= 2):  # Allow 2-line tolerance
                        matching_element = element
                        break

                if matching_element:
                    # Add Tree-sitter insights
                    enhanced_symbol["tree_sitter_analysis"] = {
                        "complexity_score": matching_element.complexity_score,
                        "complexity_level": matching_element.complexity_level.value,
                        "line_span": matching_element.end_line - matching_element.start_line + 1,
                        "adhd_insights": matching_element.adhd_insights,
                        "enhanced": True
                    }
                else:
                    enhanced_symbol["tree_sitter_analysis"] = {
                        "enhanced": False,
                        "reason": "No matching Tree-sitter element found"
                    }

                enhanced_symbols.append(enhanced_symbol)

            return enhanced_symbols

        except Exception as e:
            logger.error(f"Failed to enhance LSP symbols: {e}")
            return lsp_symbols

    # Health and Statistics

    async def get_analyzer_stats(self) -> Dict[str, Any]:
        """Get analyzer performance statistics."""
        return {
            "initialized": self.initialized,
            "supported_languages": list(self.languages.keys()),
            "analysis_stats": self.analysis_stats,
            "complexity_thresholds": {
                level.value: threshold
                for level, threshold in self.complexity_thresholds.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for Tree-sitter analyzer."""
        try:
            if not TREE_SITTER_AVAILABLE:
                return {
                    "status": "🔴 Tree-sitter Not Available",
                    "error": "Tree-sitter packages not installed"
                }

            if not self.initialized:
                return {
                    "status": "🔴 Not Initialized",
                    "error": "Analyzer not initialized"
                }

            # Test parsing with a simple example
            test_content = "def test_function():\n    return True"
            if "python" in self.parsers:
                start_time = time.time()
                tree = self.parsers["python"].parse(bytes(test_content, 'utf8'))
                parse_time = (time.time() - start_time) * 1000

                return {
                    "status": "🚀 Healthy",
                    "languages_available": len(self.languages),
                    "test_parse_time_ms": round(parse_time, 2),
                    "total_analyses": self.analysis_stats["files_analyzed"],
                    "average_analysis_time_ms": round(self.analysis_stats["average_analysis_time_ms"], 2),
                    "parse_error_rate": (
                        self.analysis_stats["parse_errors"] /
                        max(1, self.analysis_stats["files_analyzed"])
                    )
                }
            else:
                return {
                    "status": "⚠️ Limited",
                    "warning": "No parsers available for testing"
                }

        except Exception as e:
            logger.error(f"Tree-sitter health check failed: {e}")
            return {
                "status": "🔴 Error",
                "error": str(e)
            }