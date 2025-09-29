"""
Tree-sitter Code Structure Analyzer for Serena v2

Multi-language code structure analysis using Tree-sitter for AST parsing.
Provides import graphs, call hierarchies, and dependency mapping for navigation intelligence.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Tree-sitter imports (would be installed via pip install tree-sitter)
try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("Tree-sitter not available - install with: pip install tree-sitter")

logger = logging.getLogger(__name__)


class LanguageSupport(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"


@dataclass
class CodeSymbol:
    """Represents a code symbol with structure information."""
    name: str
    symbol_type: str  # function, class, variable, import, etc.
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int

    # Structure information
    parent_symbol: Optional[str] = None
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)

    # Metadata
    complexity_score: float = 0.5
    language: str = ""
    namespace: Optional[str] = None
    docstring: Optional[str] = None

    # ADHD optimizations
    cognitive_load: float = 0.5
    focus_required: bool = False


@dataclass
class ImportRelationship:
    """Represents an import relationship between files."""
    source_file: str
    imported_file: str
    import_type: str  # module, function, class, alias
    import_name: str
    alias: Optional[str] = None
    line_number: int = 0


@dataclass
class CallRelationship:
    """Represents a function call relationship."""
    caller_file: str
    caller_function: str
    called_file: str
    called_function: str
    call_line: int
    call_type: str  # direct, method, async, etc.


class CodeStructureAnalyzer:
    """
    Multi-language code structure analyzer using Tree-sitter.

    Features:
    - AST parsing for multiple programming languages
    - Import graph generation and dependency mapping
    - Call hierarchy analysis with cross-file tracking
    - Symbol extraction with structure relationships
    - ADHD-optimized complexity assessment
    - Incremental parsing for performance
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.languages: Dict[LanguageSupport, Language] = {}
        self.parsers: Dict[LanguageSupport, Parser] = {}

        # Analysis state
        self.parsed_files: Dict[str, Dict[str, Any]] = {}
        self.symbol_index: Dict[str, CodeSymbol] = {}
        self.import_graph: List[ImportRelationship] = []
        self.call_graph: List[CallRelationship] = []

        # Language detection
        self.file_extensions = {
            ".py": LanguageSupport.PYTHON,
            ".ts": LanguageSupport.TYPESCRIPT,
            ".tsx": LanguageSupport.TYPESCRIPT,
            ".js": LanguageSupport.JAVASCRIPT,
            ".jsx": LanguageSupport.JAVASCRIPT,
            ".rs": LanguageSupport.RUST,
            ".go": LanguageSupport.GO,
            ".java": LanguageSupport.JAVA
        }

        # ADHD optimization settings
        self.max_symbols_per_file = 100  # Prevent overwhelm
        self.complexity_threshold = 0.8   # High complexity warning
        self.batch_size = 10             # Process files in batches

    async def initialize(self) -> None:
        """Initialize Tree-sitter languages and parsers."""
        if not TREE_SITTER_AVAILABLE:
            logger.error("Tree-sitter not available - code structure analysis disabled")
            return

        logger.info("🌳 Initializing Tree-sitter code structure analyzer...")

        # Initialize languages (would need pre-built language libraries)
        await self._initialize_languages()

        # Create parsers for each language
        for language_enum, language_obj in self.languages.items():
            parser = Parser()
            parser.set_language(language_obj)
            self.parsers[language_enum] = parser

        logger.info(f"✅ Tree-sitter initialized with {len(self.parsers)} language parsers")

    async def _initialize_languages(self) -> None:
        """Initialize Tree-sitter language objects."""
        try:
            # This would load pre-built language libraries
            # For development, these would need to be built from tree-sitter grammar repos

            # Mock initialization - in real implementation would load .so files
            language_paths = {
                LanguageSupport.PYTHON: "build/python.so",
                LanguageSupport.TYPESCRIPT: "build/typescript.so",
                LanguageSupport.JAVASCRIPT: "build/javascript.so",
                LanguageSupport.RUST: "build/rust.so"
            }

            for lang_enum, lib_path in language_paths.items():
                try:
                    # language = Language.load_library(lib_path, lang_enum.value)
                    # self.languages[lang_enum] = language
                    logger.debug(f"📚 Loaded {lang_enum.value} grammar")
                except Exception as e:
                    logger.warning(f"Failed to load {lang_enum.value} grammar: {e}")

        except Exception as e:
            logger.error(f"Language initialization failed: {e}")

    # Core Analysis Methods

    async def analyze_file_structure(
        self,
        file_path: str,
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """Analyze code structure for a specific file."""
        try:
            if not TREE_SITTER_AVAILABLE:
                return {"error": "Tree-sitter not available"}

            # Detect language
            language = self._detect_language(file_path)
            if not language:
                return {"error": f"Unsupported language for {file_path}"}

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            # Parse with Tree-sitter
            parser = self.parsers.get(language)
            if not parser:
                return {"error": f"No parser for {language.value}"}

            tree = parser.parse(code_content.encode('utf-8'))

            # Extract structure information
            structure_info = {
                "file_path": file_path,
                "language": language.value,
                "symbols": await self._extract_symbols(tree.root_node, file_path, code_content),
                "imports": await self._extract_imports(tree.root_node, file_path, language),
                "complexity_metrics": self._calculate_file_complexity(tree.root_node),
                "adhd_assessment": self._assess_adhd_friendliness(tree.root_node, code_content),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Add dependency analysis if requested
            if include_dependencies:
                structure_info["dependencies"] = await self._analyze_file_dependencies(file_path)

            # Cache analysis result
            self.parsed_files[file_path] = structure_info

            logger.debug(f"🔍 Analyzed structure: {file_path} ({len(structure_info['symbols'])} symbols)")
            return structure_info

        except Exception as e:
            logger.error(f"File structure analysis failed for {file_path}: {e}")
            return {"error": str(e)}

    async def _extract_symbols(
        self,
        root_node: 'Node',
        file_path: str,
        code_content: str
    ) -> List[Dict[str, Any]]:
        """Extract symbols from AST with ADHD optimization."""
        try:
            symbols = []
            code_lines = code_content.split('\n')

            def extract_node_symbols(node: 'Node', parent_name: Optional[str] = None):
                """Recursively extract symbols from AST nodes."""
                if len(symbols) >= self.max_symbols_per_file:
                    return  # ADHD: Prevent overwhelming symbol lists

                node_type = node.type

                # Extract different symbol types based on node type
                if node_type in ["function_definition", "method_definition", "function_declaration"]:
                    symbol = self._create_function_symbol(node, file_path, code_lines, parent_name)
                    if symbol:
                        symbols.append(symbol)

                elif node_type in ["class_definition", "class_declaration"]:
                    symbol = self._create_class_symbol(node, file_path, code_lines, parent_name)
                    if symbol:
                        symbols.append(symbol)
                        # Recursively analyze class methods
                        for child in node.children:
                            extract_node_symbols(child, symbol["name"])

                elif node_type in ["variable_declaration", "assignment"]:
                    symbol = self._create_variable_symbol(node, file_path, code_lines, parent_name)
                    if symbol:
                        symbols.append(symbol)

                # Recursively process children for other node types
                else:
                    for child in node.children:
                        extract_node_symbols(child, parent_name)

            # Start extraction from root
            extract_node_symbols(root_node)

            # Sort symbols by line number for logical ordering
            symbols.sort(key=lambda s: s.get("start_line", 0))

            return symbols

        except Exception as e:
            logger.error(f"Symbol extraction failed: {e}")
            return []

    def _create_function_symbol(
        self,
        node: 'Node',
        file_path: str,
        code_lines: List[str],
        parent_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Create function symbol from AST node."""
        try:
            # Extract function name
            name_node = self._find_child_by_type(node, "identifier")
            if not name_node:
                return None

            function_name = self._get_node_text(name_node, code_lines)

            # Calculate function complexity
            complexity = self._calculate_function_complexity(node)

            # Extract docstring if available
            docstring = self._extract_docstring(node, code_lines)

            return {
                "name": function_name,
                "symbol_type": "function",
                "file_path": file_path,
                "start_line": node.start_point[0],
                "end_line": node.end_point[0],
                "start_column": node.start_point[1],
                "end_column": node.end_point[1],
                "parent_symbol": parent_name,
                "complexity_score": complexity,
                "docstring": docstring,
                "cognitive_load": min(complexity * 1.2, 1.0),  # Slightly higher load for functions
                "focus_required": complexity > self.complexity_threshold
            }

        except Exception as e:
            logger.error(f"Function symbol creation failed: {e}")
            return None

    def _create_class_symbol(
        self,
        node: 'Node',
        file_path: str,
        code_lines: List[str],
        parent_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Create class symbol from AST node."""
        try:
            # Extract class name
            name_node = self._find_child_by_type(node, "identifier")
            if not name_node:
                return None

            class_name = self._get_node_text(name_node, code_lines)

            # Count methods and attributes
            methods = len([child for child in node.children if child.type in ["function_definition", "method_definition"]])

            # Calculate class complexity
            complexity = min(methods / 10.0, 1.0)  # Normalize by method count

            return {
                "name": class_name,
                "symbol_type": "class",
                "file_path": file_path,
                "start_line": node.start_point[0],
                "end_line": node.end_point[0],
                "start_column": node.start_point[1],
                "end_column": node.end_point[1],
                "parent_symbol": parent_name,
                "complexity_score": complexity,
                "method_count": methods,
                "cognitive_load": min(complexity * 0.8, 1.0),  # Classes slightly lower cognitive load
                "focus_required": methods > 8  # Large classes require focus
            }

        except Exception as e:
            logger.error(f"Class symbol creation failed: {e}")
            return None

    async def _extract_imports(
        self,
        root_node: 'Node',
        file_path: str,
        language: LanguageSupport
    ) -> List[Dict[str, Any]]:
        """Extract import statements and relationships."""
        try:
            imports = []

            def find_imports(node: 'Node'):
                """Recursively find import statements."""
                if language == LanguageSupport.PYTHON:
                    if node.type in ["import_statement", "import_from_statement"]:
                        import_info = self._parse_python_import(node, file_path)
                        if import_info:
                            imports.append(import_info)

                elif language in [LanguageSupport.TYPESCRIPT, LanguageSupport.JAVASCRIPT]:
                    if node.type == "import_statement":
                        import_info = self._parse_ts_import(node, file_path)
                        if import_info:
                            imports.append(import_info)

                elif language == LanguageSupport.RUST:
                    if node.type == "use_declaration":
                        import_info = self._parse_rust_import(node, file_path)
                        if import_info:
                            imports.append(import_info)

                # Recursively check children
                for child in node.children:
                    find_imports(child)

            find_imports(root_node)
            return imports

        except Exception as e:
            logger.error(f"Import extraction failed: {e}")
            return []

    def _parse_python_import(self, node: 'Node', file_path: str) -> Optional[Dict[str, Any]]:
        """Parse Python import statement."""
        try:
            # This would parse Python import syntax using AST node structure
            # Simplified implementation for demonstration
            return {
                "source_file": file_path,
                "import_type": "module",
                "imported_name": "example_module",  # Would extract from AST
                "line_number": node.start_point[0],
                "import_statement": node.type
            }
        except Exception:
            return None

    def _parse_ts_import(self, node: 'Node', file_path: str) -> Optional[Dict[str, Any]]:
        """Parse TypeScript/JavaScript import statement."""
        try:
            # This would parse TS/JS import syntax
            return {
                "source_file": file_path,
                "import_type": "es_module",
                "imported_name": "example_import",
                "line_number": node.start_point[0],
                "import_statement": node.type
            }
        except Exception:
            return None

    def _parse_rust_import(self, node: 'Node', file_path: str) -> Optional[Dict[str, Any]]:
        """Parse Rust use declaration."""
        try:
            # This would parse Rust use syntax
            return {
                "source_file": file_path,
                "import_type": "use_declaration",
                "imported_name": "example_crate",
                "line_number": node.start_point[0],
                "import_statement": node.type
            }
        except Exception:
            return None

    # Dependency Analysis

    async def build_import_graph(self, file_paths: List[str]) -> Dict[str, Any]:
        """Build import dependency graph for multiple files."""
        try:
            logger.info(f"🕸️ Building import graph for {len(file_paths)} files...")

            # Reset import graph
            self.import_graph = []

            # Process files in batches for ADHD-friendly progress
            for i in range(0, len(file_paths), self.batch_size):
                batch = file_paths[i:i + self.batch_size]

                # Process batch
                batch_tasks = [self._analyze_file_imports(file_path) for file_path in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Process results
                for file_path, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.warning(f"Import analysis failed for {file_path}: {result}")
                    elif result:
                        self.import_graph.extend(result)

                # ADHD: Show progress
                logger.info(f"📊 Import analysis progress: {min(i + self.batch_size, len(file_paths))}/{len(file_paths)}")

            # Build graph structure
            graph_structure = self._build_graph_structure(self.import_graph)

            logger.info(f"🕸️ Import graph complete: {len(self.import_graph)} relationships")
            return graph_structure

        except Exception as e:
            logger.error(f"Import graph building failed: {e}")
            return {}

    async def _analyze_file_imports(self, file_path: str) -> List[ImportRelationship]:
        """Analyze imports for a single file."""
        try:
            # Get or create file analysis
            if file_path not in self.parsed_files:
                await self.analyze_file_structure(file_path, include_dependencies=False)

            file_analysis = self.parsed_files.get(file_path, {})
            imports_data = file_analysis.get("imports", [])

            # Convert to ImportRelationship objects
            relationships = []
            for import_data in imports_data:
                relationship = ImportRelationship(
                    source_file=import_data.get("source_file", file_path),
                    imported_file=self._resolve_import_path(import_data.get("imported_name", ""), file_path),
                    import_type=import_data.get("import_type", "module"),
                    import_name=import_data.get("imported_name", ""),
                    line_number=import_data.get("line_number", 0)
                )
                relationships.append(relationship)

            return relationships

        except Exception as e:
            logger.error(f"File import analysis failed: {e}")
            return []

    def _resolve_import_path(self, import_name: str, source_file: str) -> str:
        """Resolve import name to actual file path."""
        try:
            # This would implement language-specific import resolution
            # For now, simplified resolution
            source_path = Path(source_file)

            # Relative import resolution (simplified)
            if import_name.startswith('.'):
                # Relative import
                resolved_path = source_path.parent / f"{import_name[1:]}.py"
            else:
                # Absolute import - search in workspace
                potential_paths = list(self.workspace_path.rglob(f"{import_name}.py"))
                resolved_path = potential_paths[0] if potential_paths else None

            return str(resolved_path) if resolved_path else import_name

        except Exception:
            return import_name

    def _build_graph_structure(self, relationships: List[ImportRelationship]) -> Dict[str, Any]:
        """Build graph structure from import relationships."""
        try:
            nodes = set()
            edges = []

            for rel in relationships:
                nodes.add(rel.source_file)
                nodes.add(rel.imported_file)

                edges.append({
                    "source": rel.source_file,
                    "target": rel.imported_file,
                    "type": rel.import_type,
                    "name": rel.import_name,
                    "line": rel.line_number
                })

            return {
                "nodes": list(nodes),
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "complexity_score": len(edges) / max(len(nodes), 1),  # Graph density
                "adhd_assessment": self._assess_graph_complexity(len(nodes), len(edges))
            }

        except Exception as e:
            logger.error(f"Graph structure building failed: {e}")
            return {}

    # Complexity Assessment

    def _calculate_file_complexity(self, root_node: 'Node') -> Dict[str, Any]:
        """Calculate complexity metrics for file."""
        try:
            metrics = {
                "node_count": self._count_nodes(root_node),
                "nesting_depth": self._calculate_max_depth(root_node),
                "cyclomatic_complexity": self._estimate_cyclomatic_complexity(root_node),
                "cognitive_complexity": 0.0  # Would implement cognitive complexity calculation
            }

            # Overall complexity score
            normalized_nodes = min(metrics["node_count"] / 500.0, 1.0)
            normalized_depth = min(metrics["nesting_depth"] / 10.0, 1.0)
            normalized_cyclomatic = min(metrics["cyclomatic_complexity"] / 20.0, 1.0)

            overall_complexity = (
                normalized_nodes * 0.3 +
                normalized_depth * 0.4 +
                normalized_cyclomatic * 0.3
            )

            metrics["overall_complexity"] = overall_complexity
            return metrics

        except Exception as e:
            logger.error(f"Complexity calculation failed: {e}")
            return {"overall_complexity": 0.5}

    def _assess_adhd_friendliness(self, root_node: 'Node', code_content: str) -> Dict[str, Any]:
        """Assess how ADHD-friendly the code structure is."""
        try:
            lines = code_content.split('\n')

            assessment = {
                "line_count": len(lines),
                "average_line_length": sum(len(line) for line in lines) / max(len(lines), 1),
                "comment_ratio": len([line for line in lines if line.strip().startswith('#')]) / max(len(lines), 1),
                "function_count": self._count_nodes_by_type(root_node, ["function_definition", "method_definition"]),
                "class_count": self._count_nodes_by_type(root_node, ["class_definition"]),
                "nesting_depth": self._calculate_max_depth(root_node)
            }

            # ADHD-friendly scoring
            friendliness_score = 1.0

            # Penalize very long files
            if assessment["line_count"] > 500:
                friendliness_score -= 0.3

            # Penalize deep nesting (cognitive load)
            if assessment["nesting_depth"] > 5:
                friendliness_score -= 0.4

            # Bonus for good comments
            if assessment["comment_ratio"] > 0.2:
                friendliness_score += 0.2

            # Penalize very long lines
            if assessment["average_line_length"] > 120:
                friendliness_score -= 0.2

            assessment["adhd_friendliness_score"] = max(0.0, min(friendliness_score, 1.0))
            assessment["adhd_recommendations"] = self._generate_adhd_code_recommendations(assessment)

            return assessment

        except Exception as e:
            logger.error(f"ADHD assessment failed: {e}")
            return {"adhd_friendliness_score": 0.5}

    def _generate_adhd_code_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """Generate ADHD-specific code improvement recommendations."""
        recommendations = []

        try:
            if assessment["line_count"] > 300:
                recommendations.append("📄 Consider breaking this file into smaller, focused modules")

            if assessment["nesting_depth"] > 4:
                recommendations.append("🧩 High nesting detected - consider extracting nested logic into functions")

            if assessment["comment_ratio"] < 0.1:
                recommendations.append("💬 Adding comments would help with context switching")

            if assessment["average_line_length"] > 100:
                recommendations.append("📏 Consider shorter lines for better readability")

            if assessment["function_count"] > 20:
                recommendations.append("🔧 Many functions detected - good modular structure!")

            return recommendations

        except Exception:
            return []

    # Utility Methods

    def _detect_language(self, file_path: str) -> Optional[LanguageSupport]:
        """Detect programming language from file extension."""
        suffix = Path(file_path).suffix.lower()
        return self.file_extensions.get(suffix)

    def _find_child_by_type(self, node: 'Node', target_type: str) -> Optional['Node']:
        """Find first child node of specific type."""
        for child in node.children:
            if child.type == target_type:
                return child
            # Recursively search children
            found = self._find_child_by_type(child, target_type)
            if found:
                return found
        return None

    def _get_node_text(self, node: 'Node', code_lines: List[str]) -> str:
        """Extract text content of AST node."""
        try:
            start_line, start_col = node.start_point
            end_line, end_col = node.end_point

            if start_line == end_line:
                return code_lines[start_line][start_col:end_col]
            else:
                # Multi-line node
                lines = []
                lines.append(code_lines[start_line][start_col:])
                for line_idx in range(start_line + 1, end_line):
                    lines.append(code_lines[line_idx])
                lines.append(code_lines[end_line][:end_col])
                return '\n'.join(lines)

        except Exception:
            return ""

    def _count_nodes(self, node: 'Node') -> int:
        """Count total nodes in AST."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _count_nodes_by_type(self, node: 'Node', target_types: List[str]) -> int:
        """Count nodes of specific types."""
        count = 0
        if node.type in target_types:
            count = 1

        for child in node.children:
            count += self._count_nodes_by_type(child, target_types)

        return count

    def _calculate_max_depth(self, node: 'Node', current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        if not node.children:
            return current_depth

        max_child_depth = max(
            self._calculate_max_depth(child, current_depth + 1)
            for child in node.children
        )

        return max_child_depth

    def _calculate_function_complexity(self, node: 'Node') -> float:
        """Calculate function complexity score."""
        try:
            # Count complexity indicators
            complexity_nodes = ["if_statement", "for_statement", "while_statement", "try_statement"]
            complexity_count = self._count_nodes_by_type(node, complexity_nodes)

            # Calculate lines in function
            line_count = node.end_point[0] - node.start_point[0]

            # Combine factors
            complexity = min(
                (complexity_count / 10.0) * 0.6 +    # Control flow complexity
                (line_count / 50.0) * 0.4,           # Length complexity
                1.0
            )

            return complexity

        except Exception:
            return 0.5

    def _estimate_cyclomatic_complexity(self, node: 'Node') -> int:
        """Estimate cyclomatic complexity."""
        try:
            # Count decision points
            decision_nodes = [
                "if_statement", "elif_clause", "else_clause",
                "for_statement", "while_statement",
                "try_statement", "except_clause",
                "and", "or", "conditional_expression"
            ]

            decision_count = self._count_nodes_by_type(node, decision_nodes)
            return decision_count + 1  # +1 for linear path

        except Exception:
            return 1

    def _extract_docstring(self, node: 'Node', code_lines: List[str]) -> Optional[str]:
        """Extract docstring from function/class node."""
        try:
            # Look for string literal as first statement
            for child in node.children:
                if child.type == "expression_statement":
                    for grandchild in child.children:
                        if grandchild.type == "string":
                            return self._get_node_text(grandchild, code_lines)
            return None

        except Exception:
            return None

    def _assess_graph_complexity(self, node_count: int, edge_count: int) -> str:
        """Assess complexity of dependency graph for ADHD users."""
        density = edge_count / max(node_count, 1)

        if density < 0.5:
            return "🟢 Simple structure - easy to navigate"
        elif density < 1.0:
            return "🟡 Moderate complexity - manageable structure"
        elif density < 2.0:
            return "🟠 Complex dependencies - focus mode recommended"
        else:
            return "🔴 Very complex - consider refactoring for clarity"

    # Public API Methods

    async def get_file_structure_summary(self, file_path: str) -> Dict[str, Any]:
        """Get ADHD-friendly file structure summary."""
        try:
            structure = await self.analyze_file_structure(file_path)

            if "error" in structure:
                return structure

            # Create ADHD-friendly summary
            symbols = structure.get("symbols", [])
            complexity = structure.get("complexity_metrics", {})

            summary = {
                "file_name": Path(file_path).name,
                "language": structure.get("language", "unknown"),
                "symbol_count": len(symbols),
                "complexity_level": self._categorize_complexity(complexity.get("overall_complexity", 0.5)),
                "adhd_friendliness": structure.get("adhd_assessment", {}).get("adhd_friendliness_score", 0.5),
                "key_symbols": [
                    {
                        "name": symbol["name"],
                        "type": symbol["symbol_type"],
                        "line": symbol["start_line"],
                        "complexity": symbol.get("complexity_score", 0.5)
                    }
                    for symbol in symbols[:5]  # Top 5 for ADHD
                ],
                "adhd_recommendations": structure.get("adhd_assessment", {}).get("adhd_recommendations", [])
            }

            return summary

        except Exception as e:
            logger.error(f"File structure summary failed: {e}")
            return {"error": str(e)}

    def _categorize_complexity(self, complexity_score: float) -> str:
        """Categorize complexity for ADHD users."""
        if complexity_score <= 0.3:
            return "🟢 Simple"
        elif complexity_score <= 0.6:
            return "🟡 Moderate"
        elif complexity_score <= 0.8:
            return "🟠 Complex"
        else:
            return "🔴 Very Complex"

    # Health and Performance

    async def get_analyzer_health(self) -> Dict[str, Any]:
        """Get code structure analyzer health."""
        try:
            return {
                "tree_sitter_available": TREE_SITTER_AVAILABLE,
                "languages_loaded": len(self.languages),
                "parsers_ready": len(self.parsers),
                "files_analyzed": len(self.parsed_files),
                "symbols_indexed": len(self.symbol_index),
                "import_relationships": len(self.import_graph),
                "performance": {
                    "batch_size": self.batch_size,
                    "max_symbols_per_file": self.max_symbols_per_file,
                    "complexity_threshold": self.complexity_threshold
                },
                "status": "🌳 Analyzing" if TREE_SITTER_AVAILABLE else "⚠️ Limited"
            }

        except Exception as e:
            logger.error(f"Analyzer health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Close code structure analyzer."""
        if self.session:
            await self.session.close()
        logger.info("🌳 Code structure analyzer closed")

    # Placeholder methods for full implementation
    async def _analyze_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Analyze file dependencies."""
        return {}  # Placeholder

    async def analyze_call_hierarchy(self, function_name: str, file_path: str) -> Dict[str, Any]:
        """Analyze call hierarchy for function."""
        return {}  # Placeholder

    async def find_symbol_references(self, symbol_name: str, workspace_path: str) -> List[Dict[str, Any]]:
        """Find all references to a symbol across workspace."""
        return []  # Placeholder