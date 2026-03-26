import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    from tree_sitter import Language, Node, Parser, Tree
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Language = Node = Parser = Tree = Any

from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

class CodePrescan:
    def __init__(self, config: PrescanConfig):
        self.config = config
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        
        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()

    def _init_tree_sitter(self):
        try:
            # Python
            py_lang = Language(tspython.language())
            self.parsers["python"] = Parser(py_lang)
            self.parsers["py"] = self.parsers["python"]
            self.languages["python"] = py_lang

            # JavaScript
            js_lang = Language(tsjavascript.language())
            self.parsers["javascript"] = Parser(js_lang)
            self.parsers["js"] = self.parsers["javascript"]
            self.languages["javascript"] = js_lang

            # TypeScript
            ts_lang = Language(tstypescript.language_typescript())
            self.parsers["typescript"] = Parser(ts_lang)
            self.parsers["ts"] = self.parsers["typescript"]
            self.languages["typescript"] = ts_lang

            # TSX
            tsx_lang = Language(tstypescript.language_tsx())
            self.parsers["tsx"] = Parser(tsx_lang)
            self.languages["tsx"] = tsx_lang

            logger.info(f"Tree-sitter initialized for {len(self.languages)} languages")
        except Exception as e:
            logger.warning(f"Failed to initialize Tree-sitter: {e}")

    def analyze_file(self, entry: FileEntry, repo_root: Path) -> Dict[str, Any]:
        """Analyze a single code file and return intelligence dict."""
        if not entry.include or entry.is_ghost:
            return {}

        lang = entry.extension.lstrip(".")
        if lang not in self.parsers:
            return {}

        file_path = repo_root / entry.rel_path
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to read {entry.rel_path}: {e}")
            return {}

        parser = self.parsers[lang]
        try:
            tree = parser.parse(bytes(code, "utf-8"))
        except Exception as e:
            logger.error(f"Parse error for {entry.rel_path}: {e}")
            return {}

        # ── Intelligence Gathering ──
        symbols = self._extract_symbols(tree.root_node, code, lang)
        imports = self._extract_imports(tree.root_node, code, lang)
        api_surfaces = self._detect_api_surfaces(code, lang)
        
        # Update entry in-place for manifest
        entry.function_count = sum(1 for s in symbols if s["type"] in ("function", "method"))
        entry.class_count = sum(1 for s in symbols if s["type"] == "class")
        entry.import_count = len(imports)
        
        if symbols:
            entry.complexity_score = round(sum(s["complexity"] for s in symbols) / len(symbols), 2)
            entry.docstring_coverage = round(sum(1 for s in symbols if s.get("has_docstring")) / len(symbols), 2)

        return {
            "rel_path": entry.rel_path,
            "language": lang,
            "symbols": symbols,
            "imports": list(imports),
            "api_surfaces": api_surfaces,
        }

    def _extract_symbols(self, root_node: Node, code: str, lang: str) -> List[Dict[str, Any]]:
        symbols = []
        
        target_types = {
            "py": ["function_definition", "class_definition"],
            "js": ["function_declaration", "class_declaration", "arrow_function"],
            "ts": ["function_declaration", "class_declaration", "arrow_function"],
            "tsx": ["function_declaration", "class_declaration", "arrow_function"],
        }
        
        types = target_types.get(lang, [])

        def traverse(node: Node, parent_name: Optional[str] = None):
            if node.type in types:
                name = self._get_node_name(node)
                
                # Determine type
                stype = "block"
                if "function" in node.type or "arrow_function" in node.type:
                    stype = "method" if parent_name else "function"
                elif "class" in node.type:
                    stype = "class"
                
                comp = self._calculate_complexity(node)
                
                symbol = {
                    "name": name,
                    "type": stype,
                    "parent": parent_name,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                    "complexity": comp,
                    "has_docstring": self._has_docstring(node, lang)
                }
                symbols.append(symbol)
                
                if stype == "class" and name:
                    parent_name = name

            for child in node.children:
                traverse(child, parent_name)

        traverse(root_node)
        return symbols

    def _get_node_name(self, node: Node) -> Optional[str]:
        for child in node.children:
            if child.type in ("identifier", "name"):
                return child.text.decode("utf-8", errors="replace") if child.text else None
        return None

    def _has_docstring(self, node: Node, lang: str) -> bool:
        if lang == "py":
            # Check for expression_statement containing a string as first child of block
            for child in node.children:
                if child.type == "block":
                    if child.children and child.children[0].type == "expression_statement":
                        first = child.children[0].children[0]
                        if first.type == "string":
                            return True
        return False

    def _calculate_complexity(self, node: Node) -> float:
        def count_branches(n: Node) -> int:
            count = 0
            if n.type in ("if_statement", "for_statement", "while_statement", "try_statement", "match_statement", "conditional_expression"):
                count += 1
            for child in n.children:
                count += count_branches(child)
            return count

        branches = count_branches(node)
        lines = node.end_point[0] - node.start_point[0] + 1
        
        # Rough heuristic: 0.1 per branch, 0.01 per line
        score = (branches * 0.1) + (lines * 0.01)
        return round(min(score, 1.0), 2)

    def _extract_imports(self, root_node: Node, code: str, lang: str) -> Set[str]:
        imports = set()
        
        if lang == "py":
            # import_statement, import_from_statement
            def traverse(node: Node):
                if node.type == "import_statement":
                    for child in node.children:
                        if child.type == "dotted_name":
                            imports.add(child.text.decode("utf-8", errors="replace"))
                elif node.type == "import_from_statement":
                    for child in node.children:
                        if child.type == "dotted_name":
                            imports.add(child.text.decode("utf-8", errors="replace"))
                for child in node.children:
                    traverse(child)
            traverse(root_node)
        elif lang in ("js", "ts", "tsx"):
            # import_statement
            def traverse(node: Node):
                if node.type == "import_statement":
                    for child in node.children:
                        if child.type == "string":
                            val = child.text.decode("utf-8", errors="replace").strip("'\"")
                            imports.add(val)
                for child in node.children:
                    traverse(child)
            traverse(root_node)
            
        return imports

    def _detect_api_surfaces(self, code: str, lang: str) -> List[str]:
        surfaces = []
        if lang == "py":
            if "fastapi" in code: surfaces.append("fastapi")
            if "flask" in code: surfaces.append("flask")
            if "click" in code or "typer" in code: surfaces.append("cli")
            if "mcp" in code: surfaces.append("mcp")
        elif lang in ("js", "ts", "tsx"):
            if "express" in code: surfaces.append("express")
            if "next" in code: surfaces.append("nextjs")
            if "react" in code: surfaces.append("react")
        return surfaces

    # ── Extended methods (Part C) ──────────────────────────────────────────

    def extract_signatures(
        self, entry: FileEntry, repo_root: Path
    ) -> List[Dict[str, Any]]:
        """Aider-style signature extraction: headers without bodies.

        Returns compact structural map for partition context briefs.
        """
        if not entry.include or entry.is_ghost:
            return []

        lang = entry.extension.lstrip(".")
        if lang not in self.parsers:
            return []

        file_path = repo_root / entry.rel_path
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        parser = self.parsers[lang]
        try:
            tree = parser.parse(bytes(code, "utf-8"))
        except Exception:
            return []

        code_lines = code.splitlines()
        signatures: List[Dict[str, Any]] = []

        def visit(node: Node, parent_name: Optional[str] = None):
            target_types = {
                "py": ("function_definition", "class_definition"),
                "js": ("function_declaration", "class_declaration"),
                "ts": ("function_declaration", "class_declaration"),
                "tsx": ("function_declaration", "class_declaration"),
            }
            types = target_types.get(lang, ())

            if node.type in types:
                name = self._get_node_name(node)
                kind = "class" if "class" in node.type else "function"

                # Extract the first line (signature line)
                start_line = node.start_point[0]
                sig_line = code_lines[start_line] if start_line < len(code_lines) else ""

                # Extract decorators (lines before the node on same indent)
                decorators: List[str] = []
                for i in range(max(0, start_line - 5), start_line):
                    line = code_lines[i].strip() if i < len(code_lines) else ""
                    if line.startswith("@"):
                        decorators.append(line)

                # First line of docstring
                doc_summary = ""
                if self._has_docstring(node, lang):
                    for child in node.children:
                        if child.type == "block" and child.children:
                            first = child.children[0]
                            if first.type == "expression_statement" and first.children:
                                doc_text = first.children[0].text
                                if doc_text:
                                    doc_lines = doc_text.decode("utf-8", errors="replace").strip('"""\'').splitlines()
                                    doc_summary = doc_lines[0].strip() if doc_lines else ""
                            break

                signatures.append({
                    "name": name,
                    "kind": kind,
                    "signature": sig_line.strip(),
                    "decorators": decorators,
                    "doc_summary": doc_summary,
                    "start_line": start_line,
                    "end_line": node.end_point[0],
                    "parent": parent_name,
                })

                if kind == "class" and name:
                    parent_name = name

            for child in node.children:
                visit(child, parent_name)

        visit(tree.root_node)
        return signatures

    def calculate_cognitive_complexity(self, node: Node) -> float:
        """Cognitive complexity scoring with nesting increments.

        Nesting increments: each level of nesting adds +1 to branch cost.
        Structural: if/else/for/while/try/except/with each +1, +nesting bonus.
        Recursion: self-referencing calls +2.
        Boolean operators: and/or in conditions +1 each.
        """
        total = 0

        def walk(n: Node, nesting: int = 0):
            nonlocal total
            increment_nesting = False

            branching = (
                "if_statement", "for_statement", "while_statement",
                "try_statement", "except_clause", "with_statement",
                "match_statement",
            )

            if n.type in branching:
                total += 1 + nesting
                increment_nesting = True
            elif n.type in ("elif_clause",):
                total += 1  # no nesting increment for elif
            elif n.type == "conditional_expression":
                total += 1 + nesting
            elif n.type in ("boolean_operator",):
                # and/or in conditions
                total += 1

            child_nesting = nesting + 1 if increment_nesting else nesting
            for child in n.children:
                walk(child, child_nesting)

        walk(node)
        # Normalize: 0-1 scale, practical cap at ~40
        return round(min(total / 40.0, 1.0), 2)

    def extract_api_surfaces_detailed(
        self, entry: FileEntry, repo_root: Path
    ) -> List[Dict[str, Any]]:
        """AST-based API surface extraction with route/method info."""
        if not entry.include or entry.is_ghost:
            return []

        lang = entry.extension.lstrip(".")
        if lang not in self.parsers:
            return []

        file_path = repo_root / entry.rel_path
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        surfaces: List[Dict[str, Any]] = []
        code_lines = code.splitlines()

        # Pattern-based extraction (works across languages)
        decorator_patterns = [
            (r'@app\.(route|get|post|put|delete|patch)\s*\(', "http"),
            (r'@router\.(get|post|put|delete|patch)\s*\(', "http"),
            (r'@click\.(command|group)\s*\(', "cli"),
            (r'@(mcp_tool|tool)\s*\(', "mcp"),
            (r'@pytest\.fixture', "test_fixture"),
        ]

        for i, line in enumerate(code_lines):
            stripped = line.strip()
            for pattern, surface_type in decorator_patterns:
                match = re.search(pattern, stripped)
                if match:
                    # Find the next function definition
                    handler_name = ""
                    for j in range(i + 1, min(i + 5, len(code_lines))):
                        func_match = re.search(r'(?:def|async def)\s+(\w+)', code_lines[j])
                        if func_match:
                            handler_name = func_match.group(1)
                            break

                    surfaces.append({
                        "decorator": stripped,
                        "surface_type": surface_type,
                        "handler_name": handler_name,
                        "file": entry.rel_path,
                        "line": i + 1,
                    })

        # Check for __main__ guard
        if '__name__' in code and '__main__' in code:
            surfaces.append({
                "decorator": "__main__",
                "surface_type": "entry_point",
                "handler_name": "__main__",
                "file": entry.rel_path,
                "line": 0,
            })

        return surfaces
