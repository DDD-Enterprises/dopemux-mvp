import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .symbol_manager import SymbolID, SymbolManager

logger = logging.getLogger(__name__)


class ASTEngine:
    """Fast AST and symbol navigation layer for dopeCode."""

    def __init__(
        self,
        workspace_root: Path,
        workspace_id: str,
        tree_sitter: Any = None,
        lsp_client: Any = None,
    ):
        self.symbol_manager = SymbolManager(workspace_root, workspace_id)
        self.workspace_root = workspace_root.resolve()
        self.tree_sitter = tree_sitter
        self.lsp_client = lsp_client

    def set_dependencies(
        self, tree_sitter: Any = None, lsp: Any = None, lsp_client: Any = None
    ) -> None:
        """Hydrate lazy runtime dependencies from the server."""
        if tree_sitter is not None:
            self.tree_sitter = tree_sitter
        if lsp_client is not None:
            self.lsp_client = lsp_client
        elif lsp is not None:
            self.lsp_client = lsp

    def _read_source(self, abs_path: Path) -> str:
        return abs_path.read_text(encoding="utf-8")

    def _walk_python_files(self, search_root: Path) -> List[Path]:
        if search_root.is_file():
            return [search_root]
        return sorted(p for p in search_root.rglob("*.py") if p.is_file())

    def _relative(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.workspace_root))

    def _parse_python_symbols(
        self, relative_path: str, source: str
    ) -> List[Dict[str, Any]]:
        tree = ast.parse(source)
        symbols: List[Dict[str, Any]] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbol_name = getattr(node, "name", "")
                start_line = getattr(node, "lineno", 1)
                end_line = getattr(node, "end_lineno", start_line)
                symbol_type = "class" if isinstance(node, ast.ClassDef) else "function"
                symbols.append(
                    {
                        "symbol_id": self.symbol_manager.create_id(
                            relative_path, symbol_name, start_line
                        ),
                        "name": symbol_name,
                        "type": symbol_type,
                        "start_line": start_line,
                        "end_line": end_line,
                        "complexity_level": "low",
                        "complexity_score": 0.0,
                        "adhd_insights": [],
                    }
                )
        symbols.sort(key=lambda item: (item["start_line"], item["name"]))
        return symbols

    def _parse_imports(self, source: str) -> List[Dict[str, Any]]:
        tree = ast.parse(source)
        imports: List[Dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"module": alias.name, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                prefix = "." * (node.level or 0)
                imports.append(
                    {
                        "module": f"{prefix}{module}" if module else prefix,
                        "line": node.lineno,
                    }
                )
        imports.sort(key=lambda item: (item["line"], item["module"]))
        return imports

    async def get_file_symbols(self, relative_path: str) -> Dict[str, Any]:
        """Returns all structural elements in a file."""
        abs_path = self.symbol_manager.resolve_path(relative_path)
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")

        symbols: List[Dict[str, Any]] = []
        analysis = None
        if self.tree_sitter is not None:
            try:
                analysis = await self.tree_sitter.analyze_file(str(abs_path))
            except Exception:
                logger.debug(
                    "Tree-sitter analysis failed for %s; falling back to Python AST",
                    relative_path,
                    exc_info=True,
                )

        if analysis and getattr(analysis, "elements", None):
            for element in analysis.elements:
                start_line = getattr(element, "start_line", 1)
                end_line = getattr(element, "end_line", start_line)
                complexity_level = getattr(
                    getattr(element, "complexity_level", None), "value", "unknown"
                )
                symbols.append(
                    {
                        "symbol_id": self.symbol_manager.create_id(
                            relative_path, element.name, start_line
                        ),
                        "name": element.name,
                        "type": element.type,
                        "start_line": start_line,
                        "end_line": end_line,
                        "complexity_level": complexity_level,
                        "complexity_score": getattr(element, "complexity_score", 0.0),
                        "adhd_insights": getattr(element, "adhd_insights", []),
                    }
                )
        else:
            if abs_path.suffix == ".py":
                symbols = self._parse_python_symbols(
                    relative_path, self._read_source(abs_path)
                )

        return {
            "file": relative_path,
            "symbols": symbols,
            "symbol_count": len(symbols),
        }

    async def get_ast_outline(self, relative_path: str) -> Dict[str, Any]:
        """Returns a simplified hierarchical view of the file structure."""
        symbols_payload = await self.get_file_symbols(relative_path)
        elements = [
            {
                "name": symbol["name"],
                "type": symbol["type"],
                "start": symbol["start_line"],
                "end": symbol["end_line"],
                "complexity": symbol.get("complexity_level", "unknown"),
            }
            for symbol in symbols_payload["symbols"]
        ]
        return {
            "file": relative_path,
            "overall_complexity": "unknown",
            "lines_of_code": None,
            "adhd_recommendations": [],
            "elements": elements,
        }

    async def find_symbol(self, name: str) -> List[Dict[str, Any]]:
        """Find symbol by name across workspace."""
        results: List[Dict[str, Any]] = []

        if self.lsp_client:
            symbols = await self.lsp_client.workspace_symbols(name)
            for sym in symbols:
                uri = sym.get("location", {}).get("uri", "")
                if not uri.startswith("file://"):
                    continue
                abs_path = Path(uri.replace("file://", "")).resolve()
                try:
                    rel_path = str(abs_path.relative_to(self.workspace_root))
                except ValueError:
                    continue
                line = (
                    sym.get("location", {})
                    .get("range", {})
                    .get("start", {})
                    .get("line", 0)
                    + 1
                )
                results.append(
                    {
                        "symbol_id": self.symbol_manager.create_id(
                            rel_path, sym.get("name", name), line
                        ),
                        "name": sym.get("name"),
                        "kind": sym.get("kind"),
                        "file": rel_path,
                        "line": line,
                    }
                )
            results.sort(
                key=lambda item: (item["file"], item["line"], item["name"] or "")
            )
            return results

        pattern = re.compile(rf"\b{re.escape(name)}\b")
        for py_file in self._walk_python_files(self.workspace_root):
            source = self._read_source(py_file)
            for line_num, line in enumerate(source.splitlines(), 1):
                if pattern.search(line):
                    rel = self._relative(py_file)
                    results.append(
                        {
                            "symbol_id": self.symbol_manager.create_id(
                                rel, name, line_num
                            ),
                            "name": name,
                            "kind": "unknown",
                            "file": rel,
                            "line": line_num,
                        }
                    )
        results.sort(key=lambda item: (item["file"], item["line"]))
        return results

    async def get_symbol_body(self, symbol_id_str: str) -> str:
        """Returns the text body of a symbol."""
        sym_id = SymbolID.parse(symbol_id_str)
        abs_path = self.symbol_manager.resolve_path(sym_id.file_path)
        source = self._read_source(abs_path)

        if abs_path.suffix == ".py":
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if (
                    isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    )
                    and getattr(node, "name", None) == sym_id.symbol_name
                ):
                    if abs(getattr(node, "lineno", 0) - sym_id.line) <= 2:
                        lines = source.splitlines()
                        return "\n".join(
                            lines[
                                node.lineno
                                - 1 : getattr(node, "end_lineno", node.lineno)
                            ]
                        )

        raise ValueError(f"Symbol {sym_id.symbol_name} not found at line {sym_id.line}")

    async def find_references(
        self, symbol_id_str: str, include_declaration: bool = False
    ) -> List[Dict[str, Any]]:
        sym_id = SymbolID.parse(symbol_id_str)
        pattern = re.compile(rf"\b{re.escape(sym_id.symbol_name)}\b")
        results: List[Dict[str, Any]] = []

        if self.lsp_client:
            abs_path = self.symbol_manager.resolve_path(sym_id.file_path)
            file_uri = f"file://{abs_path}"
            refs = await self.lsp_client.find_references(file_uri, sym_id.line - 1, 0)
            for r in refs:
                uri = r.get("uri", "")
                if not uri.startswith("file://"):
                    continue
                p = Path(uri.replace("file://", "")).resolve()
                try:
                    rel = str(p.relative_to(self.workspace_root))
                except ValueError:
                    continue
                line = r.get("range", {}).get("start", {}).get("line", 0) + 1
                column = r.get("range", {}).get("start", {}).get("character", 0) + 1
                if (
                    not include_declaration
                    and rel == sym_id.file_path
                    and line == sym_id.line
                ):
                    continue
                results.append({"file": rel, "line": line, "column": column})
        else:
            for py_file in self._walk_python_files(self.workspace_root):
                rel = self._relative(py_file)
                source = self._read_source(py_file)
                for line_num, line in enumerate(source.splitlines(), 1):
                    if pattern.search(line):
                        if (
                            not include_declaration
                            and rel == sym_id.file_path
                            and line_num == sym_id.line
                        ):
                            continue
                        results.append({"file": rel, "line": line_num, "column": 1})

        results.sort(
            key=lambda item: (item["file"], item["line"], item.get("column", 0))
        )
        return results

    async def find_callers(self, symbol_id_str: str) -> Dict[str, Any]:
        sym_id = SymbolID.parse(symbol_id_str)
        callers: List[Dict[str, Any]] = []

        for py_file in self._walk_python_files(self.workspace_root):
            rel = self._relative(py_file)
            source = self._read_source(py_file)
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call):
                        fn = inner.func
                        called = None
                        if isinstance(fn, ast.Name):
                            called = fn.id
                        elif isinstance(fn, ast.Attribute):
                            called = fn.attr
                        if called == sym_id.symbol_name:
                            callers.append(
                                {
                                    "caller": node.name,
                                    "file": rel,
                                    "line": node.lineno,
                                    "symbol_id": self.symbol_manager.create_id(
                                        rel, node.name, node.lineno
                                    ),
                                }
                            )
                            break

        callers.sort(key=lambda item: (item["file"], item["line"], item["caller"]))
        return {
            "symbol_id": symbol_id_str,
            "callers": callers,
            "caller_count": len(callers),
        }

    async def find_callees(self, symbol_id_str: str) -> Dict[str, Any]:
        sym_id = SymbolID.parse(symbol_id_str)
        abs_path = self.symbol_manager.resolve_path(sym_id.file_path)
        source = self._read_source(abs_path)
        tree = ast.parse(source)

        target: Optional[ast.AST] = None
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == sym_id.symbol_name
            ):
                if abs(getattr(node, "lineno", 0) - sym_id.line) <= 2:
                    target = node
                    break

        if target is None:
            return {"symbol_id": symbol_id_str, "callees": [], "callee_count": 0}

        callees: List[Dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        for inner in ast.walk(target):
            if not isinstance(inner, ast.Call):
                continue
            fn = inner.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if not name:
                continue
            key = (name, getattr(inner, "lineno", 0))
            if key in seen:
                continue
            seen.add(key)
            callees.append({"name": name, "line": getattr(inner, "lineno", 0)})

        callees.sort(key=lambda item: (item["line"], item["name"]))
        return {
            "symbol_id": symbol_id_str,
            "callees": callees,
            "callee_count": len(callees),
        }

    async def get_import_graph(
        self, relative_path: Optional[str] = None
    ) -> Dict[str, Any]:
        imports_by_file: Dict[str, List[Dict[str, Any]]] = {}

        if relative_path:
            search_root = self.symbol_manager.resolve_path(relative_path)
        else:
            search_root = self.workspace_root

        for py_file in self._walk_python_files(search_root):
            rel = self._relative(py_file)
            imports = self._parse_imports(self._read_source(py_file))
            if imports:
                imports_by_file[rel] = imports

        import_count = sum(len(items) for items in imports_by_file.values())
        return {
            "imports": imports_by_file,
            "file_count": len(imports_by_file),
            "import_count": import_count,
        }

    async def search_pattern(
        self,
        pattern: Optional[str] = None,
        relative_path: Optional[str] = None,
        use_regex: bool = False,
        max_results: int = 100,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        search_pattern = pattern if pattern is not None else query
        if not search_pattern:
            raise ValueError("pattern is required")

        compiled = re.compile(
            search_pattern if use_regex else re.escape(search_pattern)
        )
        search_root = (
            self.workspace_root
            if not relative_path
            else self.symbol_manager.resolve_path(relative_path)
        )

        results: List[Dict[str, Any]] = []
        for py_file in self._walk_python_files(search_root):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            rel = self._relative(py_file)
            for line_num, line in enumerate(self._read_source(py_file).splitlines(), 1):
                if compiled.search(line):
                    results.append(
                        {"file": rel, "line": line_num, "text": line.strip()}
                    )
                    if len(results) >= max_results:
                        results.sort(
                            key=lambda item: (item["file"], item["line"], item["text"])
                        )
                        return {
                            "pattern": search_pattern,
                            "results": results,
                            "total_matches": len(results),
                            "truncated": True,
                        }

        results.sort(key=lambda item: (item["file"], item["line"], item["text"]))
        return {
            "pattern": search_pattern,
            "results": results,
            "total_matches": len(results),
            "truncated": False,
        }
