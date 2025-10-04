"""
Tree-sitter Code Preprocessor - Task 2
AST-aware code chunking with semantic boundaries.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    from tree_sitter import Language, Node, Parser, Tree

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """
    Single code chunk with metadata.
    """

    content: str
    start_line: int
    end_line: int
    chunk_type: Literal["function", "class", "method", "block", "file"]
    language: str
    symbol_name: Optional[str] = None
    parent_symbol: Optional[str] = None
    complexity: float = 0.0  # 0.0-1.0 ADHD complexity score
    tokens_estimate: int = 0

    def __post_init__(self):
        """Estimate tokens after initialization."""
        if self.tokens_estimate == 0:
            # Rough estimate: 1 token ≈ 4 chars
            self.tokens_estimate = len(self.content) // 4


@dataclass
class ChunkingConfig:
    """Configuration for code chunking."""

    # Target chunk size (in tokens)
    target_chunk_tokens: int = 512
    max_chunk_tokens: int = 1024
    min_chunk_tokens: int = 128

    # Chunk at semantic boundaries
    prefer_semantic_boundaries: bool = True

    # Include parent context (class name for methods)
    include_parent_context: bool = True


class CodeChunker:
    """
    Tree-sitter based code chunker with semantic boundaries.

    Supports: Python, JavaScript, TypeScript
    Fallback: Simple line-based chunking if Tree-sitter unavailable
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize code chunker.

        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkingConfig()

        # Initialize parsers
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}

        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()
        else:
            logger.warning(
                "Tree-sitter not available, using fallback line-based chunking"
            )

    def _init_tree_sitter(self):
        """Initialize Tree-sitter parsers (v0.21+ API)."""
        try:
            # Python
            py_lang = tspython.language()
            self.parsers["python"] = Parser(py_lang)
            self.parsers["py"] = Parser(py_lang)
            self.languages["python"] = py_lang

            # JavaScript
            js_lang = tsjavascript.language()
            self.parsers["javascript"] = Parser(js_lang)
            self.parsers["js"] = Parser(js_lang)
            self.languages["javascript"] = js_lang

            # TypeScript
            ts_lang = tstypescript.language_typescript()
            self.parsers["typescript"] = Parser(ts_lang)
            self.parsers["ts"] = Parser(ts_lang)
            self.languages["typescript"] = ts_lang

            # TSX
            tsx_lang = tstypescript.language_tsx()
            self.parsers["tsx"] = Parser(tsx_lang)
            self.languages["tsx"] = tsx_lang

            logger.info("Tree-sitter parsers initialized for 4 languages")

        except ValueError as e:
            # Version incompatibility - gracefully fall back to line-based chunking
            logger.warning(f"Tree-sitter version incompatibility: {e}")
            logger.warning("Falling back to line-based chunking")
            # Clear any partial initialization
            self.parsers.clear()
            self.languages.clear()
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter: {e}")
            logger.warning("Falling back to line-based chunking")
            # Clear any partial initialization
            self.parsers.clear()
            self.languages.clear()

    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        suffix = file_path.suffix.lstrip(".")
        return suffix.lower()

    def _parse_file(self, code: str, language: str) -> Optional[Tree]:
        """Parse code with Tree-sitter."""
        parser = self.parsers.get(language)
        if not parser:
            logger.debug(f"No parser for language: {language}")
            return None

        try:
            tree = parser.parse(bytes(code, "utf-8"))
            return tree
        except Exception as e:
            logger.error(f"Parse error for {language}: {e}")
            return None

    def _extract_symbol_name(self, node: Node) -> Optional[str]:
        """Extract symbol name from AST node."""
        # Look for identifier or name child
        for child in node.children:
            if child.type in ("identifier", "name"):
                return child.text.decode("utf-8") if child.text else None

        return None

    def _calculate_complexity(self, node: Node) -> float:
        """
        Calculate ADHD-friendly complexity score (0.0-1.0).

        Based on:
        - Nesting depth
        - Number of branches (if/for/while)
        - Total lines
        """

        def count_depth(n: Node, depth: int = 0) -> int:
            if not n.children:
                return depth
            return max(count_depth(c, depth + 1) for c in n.children)

        def count_branches(n: Node) -> int:
            count = 0
            if n.type in (
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement",
                "match_statement",
            ):
                count += 1
            for child in n.children:
                count += count_branches(child)
            return count

        depth = count_depth(node)
        branches = count_branches(node)
        lines = node.end_point[0] - node.start_point[0] + 1

        # Normalize (heuristic)
        depth_score = min(depth / 10.0, 1.0)
        branch_score = min(branches / 10.0, 1.0)
        lines_score = min(lines / 100.0, 1.0)

        # Weighted average
        complexity = depth_score * 0.3 + branch_score * 0.4 + lines_score * 0.3

        return round(complexity, 2)

    def _extract_chunks_from_tree(
        self,
        tree: Tree,
        code: str,
        language: str,
    ) -> List[CodeChunk]:
        """Extract semantic chunks from Tree-sitter parse tree."""
        chunks: List[CodeChunk] = []

        # Node types to extract (language-specific)
        target_types = {
            "python": ["function_definition", "class_definition", "module"],
            "javascript": [
                "function_declaration",
                "class_declaration",
                "arrow_function",
            ],
            "typescript": [
                "function_declaration",
                "class_declaration",
                "arrow_function",
            ],
            "tsx": ["function_declaration", "class_declaration", "arrow_function"],
        }

        types = target_types.get(language, [])

        def traverse(node: Node, parent_name: Optional[str] = None):
            """Traverse AST and extract chunks."""

            # Check if this is a target node type
            if node.type in types:
                start_byte = node.start_byte
                end_byte = node.end_byte
                content = code[start_byte:end_byte]

                symbol_name = self._extract_symbol_name(node)
                start_line = node.start_point[0]
                end_line = node.end_point[0]

                # Determine chunk type
                if "function" in node.type or "arrow_function" in node.type:
                    chunk_type = "method" if parent_name else "function"
                elif "class" in node.type:
                    chunk_type = "class"
                else:
                    chunk_type = "block"

                complexity = self._calculate_complexity(node)

                chunk = CodeChunk(
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type=chunk_type,
                    language=language,
                    symbol_name=symbol_name,
                    parent_symbol=parent_name,
                    complexity=complexity,
                )

                chunks.append(chunk)

                # For classes, use class name as parent for nested functions
                if chunk_type == "class" and symbol_name:
                    parent_name = symbol_name

            # Recurse into children
            for child in node.children:
                traverse(child, parent_name)

        # Start traversal
        traverse(tree.root_node)

        return chunks

    def _fallback_chunk_by_lines(
        self,
        code: str,
        language: str,
        file_path: Optional[Path] = None,
    ) -> List[CodeChunk]:
        """
        Fallback line-based chunking when Tree-sitter unavailable.

        Chunks by target token size with simple line boundaries.
        """
        lines = code.split("\n")
        chunks: List[CodeChunk] = []

        current_chunk_lines: List[str] = []
        current_tokens = 0
        chunk_start_line = 0

        for i, line in enumerate(lines):
            line_tokens = len(line) // 4  # Rough estimate

            # Check if adding this line exceeds max
            if (
                current_tokens + line_tokens > self.config.max_chunk_tokens
                and current_chunk_lines
            ):
                # Save current chunk
                content = "\n".join(current_chunk_lines)
                chunks.append(
                    CodeChunk(
                        content=content,
                        start_line=chunk_start_line,
                        end_line=i - 1,
                        chunk_type="block",
                        language=language,
                        tokens_estimate=current_tokens,
                    )
                )

                # Start new chunk
                current_chunk_lines = [line]
                current_tokens = line_tokens
                chunk_start_line = i
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens

        # Add final chunk
        if current_chunk_lines:
            content = "\n".join(current_chunk_lines)
            chunks.append(
                CodeChunk(
                    content=content,
                    start_line=chunk_start_line,
                    end_line=len(lines) - 1,
                    chunk_type="block",
                    language=language,
                    tokens_estimate=current_tokens,
                )
            )

        logger.debug(f"Fallback chunking: {len(chunks)} chunks from {len(lines)} lines")
        return chunks

    def chunk_file(self, file_path: Path) -> List[CodeChunk]:
        """
        Chunk a code file into semantic chunks.

        Args:
            file_path: Path to code file

        Returns:
            List of CodeChunk objects
        """
        # Read file
        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return []

        # Detect language
        language = self._detect_language(file_path)

        # Try Tree-sitter parsing
        if TREE_SITTER_AVAILABLE and language in self.parsers:
            tree = self._parse_file(code, language)
            if tree:
                chunks = self._extract_chunks_from_tree(tree, code, language)
                logger.debug(
                    f"Tree-sitter chunked {file_path.name}: {len(chunks)} chunks"
                )
                return chunks

        # Fallback to line-based chunking
        chunks = self._fallback_chunk_by_lines(code, language, file_path)
        return chunks

    def chunk_code_string(
        self,
        code: str,
        language: str = "python",
    ) -> List[CodeChunk]:
        """
        Chunk a code string.

        Args:
            code: Code content
            language: Programming language

        Returns:
            List of CodeChunk objects
        """
        # Try Tree-sitter parsing
        if TREE_SITTER_AVAILABLE and language in self.parsers:
            tree = self._parse_file(code, language)
            if tree:
                chunks = self._extract_chunks_from_tree(tree, code, language)
                logger.debug(f"Tree-sitter chunked: {len(chunks)} chunks")
                return chunks

        # Fallback
        chunks = self._fallback_chunk_by_lines(code, language)
        return chunks


# Example usage
def main():
    """Example usage of CodeChunker."""
    chunker = CodeChunker()

    # Example Python code
    python_code = '''
class UserService:
    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int):
        """Fetch user by ID."""
        return await self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?", user_id
        )

    async def create_user(self, name: str, email: str):
        """Create new user."""
        if not email:
            raise ValueError("Email required")

        async with self.db.transaction():
            user_id = await self.db.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                name, email
            )
            return user_id

def calculate_total(items: List[Item]) -> float:
    total = 0.0
    for item in items:
        if item.discount:
            total += item.price * (1 - item.discount)
        else:
            total += item.price
    return total
'''

    chunks = chunker.chunk_code_string(python_code, language="python")

    print(f"Extracted {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Type: {chunk.chunk_type}")
        print(f"  Symbol: {chunk.symbol_name}")
        print(f"  Parent: {chunk.parent_symbol}")
        print(f"  Lines: {chunk.start_line}-{chunk.end_line}")
        print(f"  Complexity: {chunk.complexity}")
        print(f"  Tokens: ~{chunk.tokens_estimate}")
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
