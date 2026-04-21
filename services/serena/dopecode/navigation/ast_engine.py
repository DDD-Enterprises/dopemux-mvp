from __future__ import annotations

"""Workspace-bounded dopeCode AST navigation layer."""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...tree_sitter_analyzer import CodeComplexity, StructuralElement

logger = logging.getLogger(__name__)


class ASTEngine:
    """Workspace-bounded navigation layer for dopeCode."""
    SEARCHABLE_SUFFIXES: Set[str] = {
        ".py",
        ".pyi",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".c",
        ".cc",
        ".cpp",
        ".h",
        ".hpp",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".sh",
    }
    MAX_SEARCH_FILE_SIZE_BYTES = 1_000_000

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
        if not self.tree_sitter or not getattr(self.tree_sitter, "initialized", False):
            return None

        full_path = self._resolve_file(relative_path)
        analysis = await self.tree_sitter.analyze_file(str(full_path))
        if not analysis:
            return None

        symbols = [self._symbol_to_dict(relative_path, element) for element in analysis.elements]
        symbols.sort(key=lambda item: (item["line"], item["name"]))
        return symbols

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

    def _python_callee_names(self, content: str, symbol_name: str) -> List[Dict[str, Any]]:
        tree = ast.parse(content)
        callees: Set[Tuple[str, int]] = set()
        target: Optional[ast.AST] = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and getattr(node, "name", None) == symbol_name:
                target = node
                break
        if not target:
            return []
        for node in ast.walk(target):
            if isinstance(node, ast.Call):
                callee = None
                if isinstance(node.func, ast.Name):
                    callee = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee = node.func.attr
                if callee:
                    callees.add((callee, getattr(node, "lineno", 0)))
        return [
            {"name": name, "line": line_no}
            for name, line_no in sorted(callees, key=lambda item: (item[0], item[1]))
        ]

    async def find_callees(self, symbol_id_str: str) -> Dict[str, Any]:
        from .symbol_manager import SymbolID

        symbol = SymbolID.parse(symbol_id_str)
        full_path = self._resolve_file(symbol.file_path)
        content = self._read_text(full_path)
        language = self._language_for_path(full_path)

        if language == "python":
            callees = self._python_callee_names(content, symbol.symbol_name)
        else:
            callees = []

        return {
            "symbol_id": symbol_id_str,
            "file": symbol.file_path,
            "symbol": symbol.symbol_name,
            "callee_count": len(callees),
            "callees": callees,
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
                    imports.append({"module": alias.name, "line": node.lineno, "kind": "import"})
            elif isinstance(node, ast.ImportFrom):
                module = "." * node.level + (node.module or "")
                names = [alias.name for alias in node.names]
                imports.append({"module": module, "names": names, "line": node.lineno, "kind": "from"})
        return sorted(imports, key=lambda item: (item["line"], item["module"]))

    async def get_import_graph(self, relative_path: Optional[str] = None) -> Dict[str, Any]:
        targets = [self._resolve_file(relative_path)] if relative_path else self._iter_workspace_files({".py"})
        graph: Dict[str, List[Dict[str, Any]]] = {}
        for path in targets:
            rel = self._relative(path)
            try:
                language = self._language_for_path(path)
                if language == "python":
                    graph[rel] = self._extract_python_imports(self._read_text(path))
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
        if not pattern or not pattern.strip():
            raise ValueError("pattern must be a non-empty, non-whitespace string")

        targets = [self._resolve_file(relative_path)] if relative_path else self._iter_workspace_files(self.SEARCHABLE_SUFFIXES)
        if use_regex:
            try:
                matcher = re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"Invalid regex pattern: {exc}") from exc
        else:
            matcher = None
        results: List[Dict[str, Any]] = []

        for path in targets:
            try:
                if path.stat().st_size > self.MAX_SEARCH_FILE_SIZE_BYTES:
                    continue
                lines = self._read_text(path).splitlines()
            except (OSError, UnicodeDecodeError):
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

