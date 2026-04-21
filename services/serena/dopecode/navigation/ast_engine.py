import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .symbol_manager import SymbolManager, SymbolID

logger = logging.getLogger(__name__)

class ASTEngine:
    """Fast AST and symbol navigation layer for dopeCode."""
    
    def __init__(self, workspace_root: Path, workspace_id: str, tree_sitter, lsp_client=None):
        self.symbol_manager = SymbolManager(workspace_root, workspace_id)
        self.tree_sitter = tree_sitter
        self.lsp_client = lsp_client
        self.workspace_root = workspace_root

    async def get_file_symbols(self, relative_path: str) -> List[Dict[str, Any]]:
        """Returns all structural elements in a file."""
        abs_path = self.symbol_manager.resolve_path(relative_path)
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        analysis = await self.tree_sitter.analyze_file(str(abs_path))
        if not analysis:
            return []
            
        results = []
        for element in analysis.elements:
            sym_id = self.symbol_manager.create_id(relative_path, element.name, element.start_line)
            results.append({
                "symbol_id": sym_id,
                "name": element.name,
                "type": element.type,
                "start_line": element.start_line,
                "end_line": element.end_line,
                "complexity_level": element.complexity_level.value,
                "complexity_score": element.complexity_score,
                "adhd_insights": element.adhd_insights
            })
        return results

    async def get_ast_outline(self, relative_path: str) -> Dict[str, Any]:
        """Returns a simplified hierarchical view of the file structure."""
        abs_path = self.symbol_manager.resolve_path(relative_path)
        analysis = await self.tree_sitter.analyze_file(str(abs_path))
        if not analysis:
            return {"error": "AST analysis failed or unsupported language"}
            
        return {
            "file": relative_path,
            "overall_complexity": analysis.complexity_level.value,
            "lines_of_code": analysis.lines_of_code,
            "adhd_recommendations": analysis.adhd_recommendations,
            "elements": [
                {
                    "name": e.name, 
                    "type": e.type, 
                    "start": e.start_line, 
                    "end": e.end_line,
                    "complexity": e.complexity_level.value
                } for e in analysis.elements
            ]
        }

    async def find_symbol(self, name: str) -> List[Dict[str, Any]]:
        """Find symbol by name across workspace using LSP + AST overlay."""
        if not self.lsp_client:
            return []
            
        symbols = await self.lsp_client.workspace_symbols(name)
        results = []
        for sym in symbols:
            uri = sym.get("location", {}).get("uri", "")
            if not uri.startswith("file://"): continue
            
            abs_path = Path(uri.replace("file://", ""))
            if self.workspace_root not in abs_path.parents: continue
                
            rel_path = str(abs_path.relative_to(self.workspace_root))
            line = sym.get("location", {}).get("range", {}).get("start", {}).get("line", 0) + 1
            
            sym_id = self.symbol_manager.create_id(rel_path, sym.get("name", name), line)
            
            results.append({
                "symbol_id": sym_id,
                "name": sym.get("name"),
                "kind": sym.get("kind"),
                "file": rel_path,
                "line": line
            })
        return results

    async def get_symbol_body(self, symbol_id_str: str) -> str:
        """Returns the text body of a symbol."""
        sym_id = SymbolID.parse(symbol_id_str)
        abs_path = self.symbol_manager.resolve_path(sym_id.file_path)
        
        analysis = await self.tree_sitter.analyze_file(str(abs_path))
        if not analysis:
            raise ValueError("Failed to analyze file for AST.")
            
        target = None
        for element in analysis.elements:
        content = abs_path.read_text(encoding='utf-8').splitlines()
        body = content[target.start_line-1:target.end_line]
        return "\n".join(body)
                target = element
                break
                
        if not target:
            raise ValueError(f"Symbol {sym_id.symbol_name} not found at line {sym_id.line}")
            
        content = abs_path.read_text(encoding='utf-8').splitlines()
        body = content[target.start_line-1:target.end_line]
        return "\\n".join(body)

    async def find_references(self, symbol_id_str: str) -> List[Dict[str, Any]]:
        sym_id = SymbolID.parse(symbol_id_str)
        if not self.lsp_client:
            return [{"error": "LSP required for cross-file references"}]
            
        abs_path = self.symbol_manager.resolve_path(sym_id.file_path)
        file_uri = f"file://{abs_path}"
        refs = await self.lsp_client.find_references(file_uri, sym_id.line - 1, 0)
        
        results = []
        for r in refs:
            uri = r.get("uri", "")
            if not uri.startswith("file://"): continue
            p = Path(uri.replace("file://", ""))
            if self.workspace_root not in p.parents: continue
            rel = str(p.relative_to(self.workspace_root))
            line = r.get("range", {}).get("start", {}).get("line", 0) + 1
            results.append({
                "file": rel,
                "line": line
            })
        return results

    async def find_callers(self, symbol_id_str: str) -> List[Dict[str, Any]]:
        return await self.find_references(symbol_id_str)

    async def find_callees(self, symbol_id_str: str) -> List[Dict[str, Any]]:
        return [{"error": "Not natively supported by pylsp without extended plugins. Requires AST data flow."}]

    async def get_import_graph(self, relative_path: str) -> List[str]:
        abs_path = self.symbol_manager.resolve_path(relative_path)
        analysis = await self.tree_sitter.analyze_file(str(abs_path))
        if not analysis: return []
        return [e.name for e in analysis.elements if e.type == "import"]

    async def search_pattern(self, query: str) -> List[Dict[str, Any]]:
        import re
        results = []
        pattern = re.compile(query)
        for py_file in self.workspace_root.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(encoding='utf-8')
            for line_num, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    results.append({
                        "file": str(py_file.relative_to(self.workspace_root)),
                        "line": line_num,
                        "text": line.strip()
                    })
        return results
