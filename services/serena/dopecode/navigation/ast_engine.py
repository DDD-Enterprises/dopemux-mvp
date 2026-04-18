from __future__ import annotations

"""
Serena v2 Tree-sitter Code Analyzer

Enhanced code structure parsing with ADHD-optimized complexity analysis.
Complements LSP semantic understanding with detailed syntactic insights.
"""

import asyncio
import ast
import json
import logging
import re
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
    Language = Parser = Node = object  # type: ignore[assignment]
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
            analysis_duration_ms=analysis_duration_ms,
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

        except Exception as e:
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


class ASTEngine:
    """Workspace-bounded navigation layer for dopeCode."""

    def __init__(
        self,
        workspace_root: Path,
        workspace_id: str,
        tree_sitter: Optional[Any] = None,
        lsp: Optional[Any] = None,
    ):
        from .symbol_manager import SymbolManager

        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = workspace_id
        self.tree_sitter = tree_sitter
        self.lsp = lsp
        self.symbol_manager = SymbolManager(self.workspace_root, workspace_id)
        self._javascript_parser: Optional[Any] = None

    def set_dependencies(self, tree_sitter: Optional[Any] = None, lsp: Optional[Any] = None) -> None:
        if tree_sitter is not None:
            self.tree_sitter = tree_sitter
        if lsp is not None:
            self.lsp = lsp

    def _resolve_file(self, relative_path: str) -> Path:
        return self.symbol_manager.resolve_path(relative_path)

    def _iter_workspace_files(self, suffixes: Optional[Set[str]] = None) -> List[Path]:
        files: List[Path] = []
        for path in self.workspace_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part.startswith(".") and part not in {".", ".."} for part in path.relative_to(self.workspace_root).parts):
                continue
            if suffixes and path.suffix.lower() not in suffixes:
                continue
            files.append(path)
        return sorted(files)

    def _relative(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.workspace_root))

    def _language_for_path(self, path: Path) -> Optional[str]:
        ext = path.suffix.lower()
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go",
        }.get(ext)

    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _javascript_parser_instance(self) -> Optional[Parser]:
        if not TREE_SITTER_AVAILABLE:
            return None
        if self._javascript_parser is not None:
            return self._javascript_parser

        try:
            language = Language(tsjavascript.language())
            parser = Parser()
            parser.language = language
            self._javascript_parser = parser
            return parser
        except Exception as exc:
            logger.debug(f"Failed to initialize JavaScript parser: {exc}")
            self._javascript_parser = None
            return None

    def _javascript_tree(self, content: str):
        parser = self._javascript_parser_instance()
        if not parser:
            return None
        return parser.parse(content.encode("utf-8"))

    def _node_text(self, content: str, node: Any) -> str:
        return content[node.start_byte:node.end_byte]

    def _javascript_string_value(self, content: str, node: Any) -> Optional[str]:
        text = self._node_text(content, node).strip()
        if len(text) < 2:
            return None
        quote = text[0]
        if quote not in {"'", '"', "`"} or text[-1] != quote:
            return None
        return text[1:-1]

    def _javascript_module_to_relative(self, source_path: Path, module_spec: str) -> Optional[str]:
        if not module_spec or not module_spec.startswith("."):
            return None

        candidate_text = module_spec.replace("\\", "/")
        candidate_base = (source_path.parent / candidate_text).resolve()
        candidates = []

        if candidate_base.suffix in {".js", ".jsx"}:
            candidates.append(candidate_base)
        else:
            candidates.extend(
                [
                    candidate_base.with_suffix(".js"),
                    candidate_base.with_suffix(".jsx"),
                    candidate_base / "index.js",
                    candidate_base / "index.jsx",
                ]
            )

        candidates.append(candidate_base)

        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                resolved.relative_to(self.workspace_root)
            except Exception:
                continue
            if resolved.exists():
                return self._relative(resolved)
        return None

    def _javascript_symbol_targets(self, content: str) -> List[Dict[str, Any]]:
        tree = self._javascript_tree(content)
        if tree is None:
            return []

        targets: List[Dict[str, Any]] = []

        def add_target(node: Any, name: str, kind: str, body_node: Optional[Any], exported: bool) -> None:
            if not name:
                return
            replaceable = body_node is not None and body_node.type in {"statement_block", "class_body"}
            targets.append(
                {
                    "node": node,
                    "body_node": body_node,
                    "name": name,
                    "kind": kind,
                    "line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "body_kind": getattr(body_node, "type", None),
                    "exported": exported,
                    "replaceable": replaceable,
                }
            )

        def visit(node: Any, exported: bool = False) -> None:
            if node.type == "export_statement":
                for child in node.named_children:
                    visit(child, exported=True)
                return

            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                body_node = node.child_by_field_name("body")
                if name_node is not None:
                    add_target(node, self._node_text(content, name_node), "function", body_node, exported)
                return

            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                body_node = node.child_by_field_name("body")
                if name_node is not None:
                    add_target(node, self._node_text(content, name_node), "class", body_node, exported)
                return

            if node.type == "lexical_declaration":
                for declarator in node.named_children:
                    if declarator.type != "variable_declarator":
                        continue
                    name_node = declarator.child_by_field_name("name")
                    value_node = declarator.child_by_field_name("value")
                    if name_node is None or value_node is None:
                        continue
                    if value_node.type not in {"arrow_function", "function_expression"}:
                        continue
                    body_node = value_node.child_by_field_name("body")
                    if body_node is None:
                        body_node = value_node
                    add_target(
                        declarator,
                        self._node_text(content, name_node),
                        "function",
                        body_node,
                        exported,
                    )

        for child in tree.root_node.named_children:
            visit(child)

        return sorted(targets, key=lambda item: (item["line"], item["name"]))

    def _javascript_import_aliases(self, content: str, source_path: Path) -> Dict[str, Dict[str, Any]]:
        aliases: Dict[str, Dict[str, Any]] = {}
        for entry in self._javascript_imports(content, source_path):
            module = entry.get("module")
            resolved_file = entry.get("resolved_path")
            kind = entry.get("kind")
            for alias in entry.get("aliases", []):
                aliases[alias] = {
                    "kind": kind,
                    "module": module,
                    "resolved_name": module,
                    "resolved_file": resolved_file,
                    "line": entry.get("line", 0),
                }
            for alias, resolved_name in entry.get("named_aliases", {}).items():
                aliases[alias] = {
                    "kind": "from_import",
                    "module": module,
                    "resolved_name": resolved_name,
                    "resolved_file": resolved_file,
                    "line": entry.get("line", 0),
                }
        return aliases

    def _javascript_imports(self, content: str, source_path: Path) -> List[Dict[str, Any]]:
        tree = self._javascript_tree(content)
        if tree is None:
            return []

        imports: List[Dict[str, Any]] = []

        for node in tree.root_node.named_children:
            if node.type != "import_statement":
                continue

            module_node = next((child for child in node.named_children if child.type == "string"), None)
            module_spec = self._javascript_string_value(content, module_node) if module_node else None
            clause = next((child for child in node.named_children if child.type != "string"), None)
            aliases: List[str] = []
            named_aliases: Dict[str, str] = {}

            if clause is not None:
                clause_text = self._node_text(content, clause).strip()
                if clause_text.startswith("{"):
                    spec_list = clause_text[1:-1].split(",")
                    for raw_spec in spec_list:
                        spec = raw_spec.strip()
                        if not spec:
                            continue
                        if " as " in spec:
                            imported_name, local_name = [part.strip() for part in spec.split(" as ", 1)]
                        else:
                            imported_name = local_name = spec
                        aliases.append(local_name)
                        named_aliases[local_name] = f"{module_spec}.{imported_name}" if module_spec else imported_name
                elif clause_text.startswith("*"):
                    namespace_alias = clause_text.split(" as ", 1)[1].strip() if " as " in clause_text else ""
                    if namespace_alias:
                        aliases.append(namespace_alias)
                else:
                    aliases.append(clause_text.split(",")[0].strip())

            imports.append(
                {
                    "module": module_spec or "",
                    "line": node.start_point[0] + 1,
                    "kind": "import",
                    "aliases": sorted({alias for alias in aliases if alias}),
                    "named_aliases": named_aliases,
                    "resolved_path": self._javascript_module_to_relative(source_path, module_spec or ""),
                }
            )

        return sorted(imports, key=lambda item: (item["line"], item["module"]))

    def _javascript_symbol_name_for_line(self, symbol_targets: List[Dict[str, Any]], symbol_name: str, line: Optional[int]) -> Optional[Dict[str, Any]]:
        candidates = [target for target in symbol_targets if target["name"] == symbol_name]
        if not candidates:
            return None
        if line is not None:
            for candidate in candidates:
                if candidate["line"] == line:
                    return candidate
        return candidates[0]

    def _javascript_callee_names(self, content: str, symbol_name: str, line: Optional[int], source_path: Path) -> List[Dict[str, Any]]:
        targets = self._javascript_symbol_targets(content)
        target = self._javascript_symbol_name_for_line(targets, symbol_name, line)
        if target is None or target["body_node"] is None:
            return []

        local_symbols = {
            item["name"]: item
            for item in targets
        }
        import_aliases = self._javascript_import_aliases(content, source_path)
        callees: Dict[Tuple[str, int, str], Dict[str, Any]] = {}

        def walk(node: Any) -> None:
            if node.type == "call_expression":
                func_node = node.child_by_field_name("function")
                callee_name: Optional[str] = None
                callee_kind = "unresolved"
                resolved_name: Optional[str] = None
                resolved_file: Optional[str] = None
                confidence = 0.4

                if func_node is not None and func_node.type == "identifier":
                    callee_name = self._node_text(content, func_node)
                    if callee_name in local_symbols:
                        callee_kind = "local_symbol"
                        resolved_name = callee_name
                        confidence = 1.0
                    elif callee_name in import_aliases:
                        alias = import_aliases[callee_name]
                        callee_kind = alias["kind"]
                        resolved_name = alias["resolved_name"]
                        resolved_file = alias["resolved_file"]
                        confidence = 0.95 if resolved_file else 0.8
                elif func_node is not None and func_node.type == "member_expression":
                    object_node = func_node.child_by_field_name("object")
                    property_node = func_node.child_by_field_name("property")
                    if property_node is not None:
                        callee_name = self._node_text(content, property_node)
                        if object_node is not None and object_node.type == "identifier":
                            object_name = self._node_text(content, object_node)
                            if object_name in import_aliases:
                                alias = import_aliases[object_name]
                                callee_kind = "qualified_import"
                                resolved_name = f"{alias['resolved_name']}.{callee_name}"
                                resolved_file = alias["resolved_file"]
                                confidence = 0.85 if resolved_file else 0.7
                            elif object_name in local_symbols:
                                callee_kind = "attribute_call"
                                confidence = 0.5

                if callee_name:
                    line_no = node.start_point[0] + 1
                    key = (callee_name, line_no, resolved_name or callee_kind)
                    if key not in callees:
                        callees[key] = {
                            "name": callee_name,
                            "line": line_no,
                            "kind": callee_kind,
                            "resolved_name": resolved_name,
                            "resolved_file": resolved_file,
                            "confidence": round(confidence, 2),
                        }

            for child in node.named_children:
                walk(child)

        walk(target["body_node"])
        return sorted(callees.values(), key=lambda item: (item["line"], item["name"], item["kind"]))

    def _symbol_to_dict(self, relative_path: str, element: StructuralElement) -> Dict[str, Any]:
        symbol_id = self.symbol_manager.create_id(relative_path, element.name, element.start_line)
        return {
            "symbol_id": symbol_id,
            "name": element.name,
            "kind": element.type,
            "file": relative_path,
            "line": element.start_line,
            "end_line": element.end_line,
            "complexity_score": element.complexity_score,
            "complexity_level": element.complexity_level.value,
            "adhd_insights": element.adhd_insights,
            "metadata": element.metadata,
        }

    async def _tree_sitter_symbols(self, relative_path: str) -> Optional[List[Dict[str, Any]]]:
        full_path = self._resolve_file(relative_path)
        language = self._language_for_path(full_path)

        if language == "javascript":
            content = self._read_text(full_path)
            symbols = []
            for target in self._javascript_symbol_targets(content):
                symbols.append(
                    {
                        "symbol_id": self.symbol_manager.create_id(relative_path, target["name"], target["line"]),
                        "name": target["name"],
                        "kind": target["kind"],
                        "file": relative_path,
                        "line": target["line"],
                        "end_line": target["end_line"],
                        "complexity_score": 0.0,
                        "complexity_level": CodeComplexity.SIMPLE.value,
                        "adhd_insights": [],
                        "metadata": {
                            "language": "javascript",
                            "node_type": target["node"].type,
                            "body_kind": target["body_kind"],
                            "exported": target["exported"],
                            "replaceable": target["replaceable"],
                        },
                    }
                )
            symbols.sort(key=lambda item: (item["line"], item["name"]))
            return symbols

        if self.tree_sitter and getattr(self.tree_sitter, "initialized", False):
            analysis = await self.tree_sitter.analyze_file(str(full_path))
            if analysis:
                symbols = [self._symbol_to_dict(relative_path, element) for element in analysis.elements]
                symbols.sort(key=lambda item: (item["line"], item["name"]))
                return symbols

        return None

    def _python_symbols(self, relative_path: str, content: str) -> List[Dict[str, Any]]:
        tree = ast.parse(content)
        symbols: List[Dict[str, Any]] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
                symbols.append({
                    "symbol_id": self.symbol_manager.create_id(relative_path, node.name, node.lineno),
                    "name": node.name,
                    "kind": kind,
                    "file": relative_path,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "complexity_score": 0.0,
                    "complexity_level": CodeComplexity.SIMPLE.value,
                    "adhd_insights": [],
                    "metadata": {"language": "python"},
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "symbol_id": self.symbol_manager.create_id(relative_path, node.name, node.lineno),
                    "name": node.name,
                    "kind": "class",
                    "file": relative_path,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "complexity_score": 0.0,
                    "complexity_level": CodeComplexity.SIMPLE.value,
                    "adhd_insights": [],
                    "metadata": {"language": "python"},
                })
        return sorted(symbols, key=lambda item: (item["line"], item["name"]))

    async def get_file_symbols(self, relative_path: str) -> Dict[str, Any]:
        full_path = self._resolve_file(relative_path)
        content = self._read_text(full_path)
        symbols = await self._tree_sitter_symbols(relative_path)
        if symbols is None:
            language = self._language_for_path(full_path)
            if language == "python":
                symbols = self._python_symbols(relative_path, content)
            else:
                symbols = []
        return {
            "file": relative_path,
            "language": self._language_for_path(full_path),
            "symbol_count": len(symbols),
            "symbols": symbols,
        }

    async def get_ast_outline(self, relative_path: str) -> Dict[str, Any]:
        payload = await self.get_file_symbols(relative_path)
        payload["outline"] = [
            {
                "name": symbol["name"],
                "kind": symbol["kind"],
                "line": symbol["line"],
                "end_line": symbol["end_line"],
            }
            for symbol in payload["symbols"]
        ]
        return payload

    def _symbol_position(self, file_path: Path, symbol_name: str, line_number: int) -> Tuple[int, int]:
        lines = self._read_text(file_path).splitlines()
        line_index = max(line_number - 1, 0)
        if line_index < len(lines):
            column = lines[line_index].find(symbol_name)
            if column >= 0:
                return line_index, column
        return line_index, 0

    def _location_to_reference(self, location: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        uri = location.get("uri") or location.get("targetUri")
        range_obj = location.get("range") or location.get("targetSelectionRange")
        if not uri or not range_obj or not uri.startswith("file://"):
            return None
        file_path = Path(uri[7:]).resolve()
        try:
            relative_path = self._relative(file_path)
        except ValueError:
            return None
        start = range_obj.get("start", {})
        end = range_obj.get("end", {})
        return {
            "file": relative_path,
            "line": start.get("line", 0) + 1,
            "column": start.get("character", 0) + 1,
            "end_line": end.get("line", 0) + 1,
            "end_column": end.get("character", 0) + 1,
        }

    def _grep_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        pattern = re.compile(rf"\b{re.escape(symbol_name)}\b")
        refs: List[Dict[str, Any]] = []
        for path in self._iter_workspace_files({".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"}):
            try:
                lines = self._read_text(path).splitlines()
            except UnicodeDecodeError:
                continue
            relative_path = self._relative(path)
            for line_no, line_text in enumerate(lines, start=1):
                for match in pattern.finditer(line_text):
                    refs.append({
                        "file": relative_path,
                        "line": line_no,
                        "column": match.start() + 1,
                        "end_line": line_no,
                        "end_column": match.end() + 1,
                    })
        refs.sort(key=lambda item: (item["file"], item["line"], item["column"]))
        return refs

    async def find_references(
        self,
        symbol_id_str: Optional[str] = None,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        include_declaration: bool = True,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        from .symbol_manager import SymbolID

        if symbol_id_str:
            symbol = SymbolID.parse(symbol_id_str)
            file_path = symbol.file_path
            line = symbol.line
            full_path = self._resolve_file(symbol.file_path)
            zero_line, zero_column = self._symbol_position(full_path, symbol.symbol_name, symbol.line)
            column = zero_column + 1
            symbol_name = symbol.symbol_name
        else:
            if file_path is None or line is None or column is None:
                raise ValueError("find_references requires either symbol_id_str or file_path, line, and column")
            full_path = self._resolve_file(file_path)
            lines = self._read_text(full_path).splitlines()
            symbol_name = ""
            if 0 <= line - 1 < len(lines):
                match = re.search(r"[A-Za-z_][A-Za-z0-9_]*", lines[line - 1][max(column - 1, 0):])
                if match:
                    symbol_name = match.group(0)
            zero_line, zero_column = line - 1, column - 1

        references: List[Dict[str, Any]] = []
        if self.lsp:
            try:
                locations = await self.lsp.find_references(
                    full_path.resolve().as_uri(),
                    zero_line,
                    zero_column,
                    include_declaration=include_declaration,
                )
                for location in locations:
                    ref = self._location_to_reference(location)
                    if ref:
                        references.append(ref)
            except Exception as exc:
                logger.warning(f"LSP reference lookup failed for {file_path}: {exc}")

        if not references and symbol_name:
            references = self._grep_references(symbol_name)
            if not include_declaration:
                references = [
                    ref for ref in references
                    if not (ref["file"] == file_path and ref["line"] == line)
                ]

        references.sort(key=lambda item: (item["file"], item["line"], item["column"]))
        if max_results is not None:
            references = references[:max_results]
        return references

    def _python_symbol_indexes(self, tree: ast.AST) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        local_symbols: Dict[str, Dict[str, Any]] = {}
        import_aliases: Dict[str, Dict[str, Any]] = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                local_symbols[getattr(node, "name", "")] = {
                    "kind": "local_symbol",
                    "line": getattr(node, "lineno", 0),
                    "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                }
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    key = alias.asname or alias.name.split(".")[0]
                    import_aliases[key] = {
                        "kind": "import",
                        "module": alias.name,
                        "name": alias.asname or alias.name,
                        "resolved_name": alias.name,
                        "line": getattr(node, "lineno", 0),
                        "resolved_file": self._module_to_relative(alias.name),
                    }
            elif isinstance(node, ast.ImportFrom):
                module = "." * node.level + (node.module or "")
                for alias in node.names:
                    key = alias.asname or alias.name
                    import_aliases[key] = {
                        "kind": "from_import",
                        "module": module,
                        "name": alias.asname or alias.name,
                        "imported_name": alias.name,
                        "resolved_name": f"{module}.{alias.name}" if module else alias.name,
                        "line": getattr(node, "lineno", 0),
                        "resolved_file": self._module_to_relative(module),
                    }

        return local_symbols, import_aliases

    def _python_callee_names(self, content: str, symbol_name: str) -> List[Dict[str, Any]]:
        tree = ast.parse(content)
        target: Optional[ast.AST] = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and getattr(node, "name", None) == symbol_name:
                target = node
                break
        if not target:
            return []

        local_symbols, import_aliases = self._python_symbol_indexes(tree)
        callees: Dict[Tuple[str, int, str], Dict[str, Any]] = {}

        for node in ast.walk(target):
            if not isinstance(node, ast.Call):
                continue

            callee_name: Optional[str] = None
            callee_kind = "unresolved"
            resolved_name: Optional[str] = None
            resolved_file: Optional[str] = None
            confidence = 0.4

            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
                if callee_name in local_symbols:
                    callee_kind = "local_symbol"
                    resolved_name = callee_name
                    confidence = 1.0
                elif callee_name in import_aliases:
                    alias = import_aliases[callee_name]
                    callee_kind = alias["kind"]
                    resolved_name = alias["resolved_name"]
                    resolved_file = alias["resolved_file"]
                    confidence = 0.95 if resolved_file else 0.8
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
                if isinstance(node.func.value, ast.Name) and node.func.value.id in import_aliases:
                    alias = import_aliases[node.func.value.id]
                    callee_kind = "qualified_import"
                    resolved_name = f"{alias['resolved_name']}.{node.func.attr}"
                    resolved_file = alias["resolved_file"]
                    confidence = 0.85 if resolved_file else 0.7
                elif isinstance(node.func.value, ast.Name) and node.func.value.id in local_symbols:
                    callee_kind = "attribute_call"
                    confidence = 0.5

            if not callee_name:
                continue

            line_no = getattr(node, "lineno", 0)
            key = (callee_name, line_no, resolved_name or callee_kind)
            if key in callees:
                continue
            callees[key] = {
                "name": callee_name,
                "line": line_no,
                "kind": callee_kind,
                "resolved_name": resolved_name,
                "resolved_file": resolved_file,
                "confidence": round(confidence, 2),
            }

        return sorted(callees.values(), key=lambda item: (item["line"], item["name"], item["kind"]))

    async def find_callees(self, symbol_id_str: str) -> Dict[str, Any]:
        from .symbol_manager import SymbolID

        symbol = SymbolID.parse(symbol_id_str)
        full_path = self._resolve_file(symbol.file_path)
        content = self._read_text(full_path)
        language = self._language_for_path(full_path)

        if language == "python":
            callees = self._python_callee_names(content, symbol.symbol_name)
        elif language == "javascript":
            callees = self._javascript_callee_names(content, symbol.symbol_name, symbol.line, full_path)
        else:
            callees = []

        return {
            "symbol_id": symbol_id_str,
            "file": symbol.file_path,
            "symbol": symbol.symbol_name,
            "callee_count": len(callees),
            "callees": callees,
            "resolution_mode": "python_ast" if language == "python" else ("javascript_ast" if language == "javascript" else "fail_closed"),
        }

    async def find_callers(self, symbol_id_str: str) -> Dict[str, Any]:
        from .symbol_manager import SymbolID

        symbol = SymbolID.parse(symbol_id_str)
        refs = await self.find_references(symbol_id_str=symbol_id_str, include_declaration=False)
        callers: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int, str]] = set()

        for ref in refs:
            file_symbols = await self.get_file_symbols(ref["file"])
            owner = next(
                (
                    item for item in file_symbols["symbols"]
                    if item["line"] <= ref["line"] <= item["end_line"] and item["kind"] in {"function", "async_function", "method", "class"}
                ),
                None,
            )
            caller_name = owner["name"] if owner else "<module>"
            key = (ref["file"], ref["line"], caller_name)
            if key in seen:
                continue
            seen.add(key)
            callers.append({
                "file": ref["file"],
                "line": ref["line"],
                "column": ref["column"],
                "caller": caller_name,
            })

        callers.sort(key=lambda item: (item["file"], item["line"], item["caller"]))
        return {
            "symbol_id": symbol_id_str,
            "file": symbol.file_path,
            "symbol": symbol.symbol_name,
            "caller_count": len(callers),
            "callers": callers,
        }

    def _extract_python_imports(self, content: str) -> List[Dict[str, Any]]:
        tree = ast.parse(content)
        imports: List[Dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "line": node.lineno,
                        "kind": "import",
                        "alias": alias.asname or alias.name,
                        "resolved_path": self._module_to_relative(alias.name),
                    })
            elif isinstance(node, ast.ImportFrom):
                module = "." * node.level + (node.module or "")
                names = [alias.name for alias in node.names]
                imports.append({
                    "module": module,
                    "names": names,
                    "line": node.lineno,
                    "kind": "from",
                    "aliases": [alias.asname or alias.name for alias in node.names],
                    "resolved_path": self._module_to_relative(module),
                })
        return sorted(imports, key=lambda item: (item["line"], item["module"]))

    def _extract_javascript_imports(self, content: str, source_path: Path) -> List[Dict[str, Any]]:
        return self._javascript_imports(content, source_path)

    def _module_to_relative(self, module: str) -> Optional[str]:
        if not module:
            return None
        normalized = module.lstrip(".")
        if not normalized:
            return None
        candidates = [
            self.workspace_root / f"{normalized.replace('.', '/')}.py",
            self.workspace_root / normalized.replace(".", "/") / "__init__.py",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    return self._relative(candidate)
                except ValueError:
                    continue
        return None

    async def get_import_graph(self, relative_path: Optional[str] = None) -> Dict[str, Any]:
        targets = [self._resolve_file(relative_path)] if relative_path else self._iter_workspace_files({".py", ".js", ".jsx"})
        graph: Dict[str, List[Dict[str, Any]]] = {}
        for path in targets:
            rel = self._relative(path)
            try:
                language = self._language_for_path(path)
                if language == "python":
                    graph[rel] = self._extract_python_imports(self._read_text(path))
                elif language == "javascript":
                    graph[rel] = self._extract_javascript_imports(self._read_text(path), path)
                else:
                    graph[rel] = []
            except SyntaxError as exc:
                graph[rel] = [{"error": str(exc)}]
        return {"file_count": len(graph), "imports": graph}

    async def search_pattern(
        self,
        pattern: str,
        relative_path: Optional[str] = None,
        use_regex: bool = False,
        max_results: int = 100,
    ) -> Dict[str, Any]:
        if max_results < 1:
            raise ValueError("max_results must be at least 1")

        targets = [self._resolve_file(relative_path)] if relative_path else self._iter_workspace_files()
        matcher = re.compile(pattern) if use_regex else None
        results: List[Dict[str, Any]] = []

        for path in targets:
            try:
                lines = self._read_text(path).splitlines()
            except UnicodeDecodeError:
                continue
            rel = self._relative(path)
            for line_no, line_text in enumerate(lines, start=1):
                matched = matcher.search(line_text) if matcher else (pattern in line_text)
                if not matched:
                    continue
                column = matched.start() + 1 if matcher else line_text.index(pattern) + 1
                results.append({
                    "file": rel,
                    "line": line_no,
                    "column": column,
                    "match": matched.group(0) if matcher else pattern,
                    "text": line_text.strip(),
                })
                if len(results) >= max_results:
                    return {"pattern": pattern, "use_regex": use_regex, "result_count": len(results), "results": results}

        results.sort(key=lambda item: (item["file"], item["line"], item["column"]))
        return {"pattern": pattern, "use_regex": use_regex, "result_count": len(results), "results": results}
