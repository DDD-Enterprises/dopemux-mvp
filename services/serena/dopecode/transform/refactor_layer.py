import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..policy.mutation_policy import MutationPolicy
from .write_layer import WriteLayer
from ..navigation.ast_engine import ASTEngine
from ..navigation.symbol_manager import SymbolID

logger = logging.getLogger(__name__)


def _sorted_unique(values: Iterable[str]) -> List[str]:
    return sorted({value for value in values if value})


class RefactorLayer:
    """Symbol refactoring and batch operations."""

    def __init__(self, write_layer: WriteLayer, ast_engine: ASTEngine, policy: Optional[MutationPolicy] = None):
        self.write_layer = write_layer
        self.ast_engine = ast_engine
        self.policy = policy or getattr(write_layer, "policy", None) or MutationPolicy(write_layer.workspace_root, write_layer.workspace_id)

    def _symbol_pattern(self, symbol_name: str) -> re.Pattern[str]:
        return re.compile(rf"\b{re.escape(symbol_name)}\b")

    def _read_file_text(self, relative_path: str) -> str:
        target = self.write_layer._validate_boundary(relative_path)
        return target.read_text(encoding="utf-8")

    def _rename_preview_receipts(self, symbol_name: str, files: List[str], new_name: str) -> List[Dict[str, Any]]:
        pattern = self._symbol_pattern(symbol_name)
        receipts = []
        for relative_path in files:
            content = self._read_file_text(relative_path)
            match_count = len(pattern.findall(content))
            receipts.append(
                {
                    "file": relative_path,
                    "match_count": match_count,
                    "replacement_count": match_count,
                    "preview": True,
                    "new_name": new_name,
                }
            )
        receipts.sort(key=lambda item: item["file"])
        return receipts

    def _replace_occurrences(self, content: str, symbol_name: str, new_name: str) -> Tuple[str, int]:
        pattern = self._symbol_pattern(symbol_name)
        return pattern.subn(new_name, content)

    def _python_symbol_node(self, content: str, symbol_name: str, line: int) -> Optional[ast.AST]:
        tree = ast.parse(content)
        fallback = None
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if getattr(node, "name", None) != symbol_name:
                continue
            if getattr(node, "lineno", None) == line:
                return node
            if fallback is None and getattr(node, "lineno", 0) <= line <= getattr(node, "end_lineno", getattr(node, "lineno", 0)):
                fallback = node
        return fallback

    def _javascript_symbol_target(self, content: str, symbol_name: str, line: int) -> Optional[Dict[str, Any]]:
        targets = self.ast_engine._javascript_symbol_targets(content)
        exact = [target for target in targets if target["name"] == symbol_name and target["line"] == line]
        if exact:
            return exact[0]
        matches = [target for target in targets if target["name"] == symbol_name]
        return matches[0] if matches else None

    def _indent_block(self, body_text: str, indent: str) -> str:
        body_text = body_text.rstrip("\n")
        if not body_text.strip():
            body_text = "pass"
        lines = body_text.splitlines()
        indented_lines = [f"{indent}{line}" if line.strip() else indent.rstrip() for line in lines]
        return "\n".join(indented_lines) + "\n"

    async def rename_symbol(self, symbol_id_str: str, new_name: str, preview: bool = True) -> Dict[str, Any]:
        """Find all references and rename the symbol in a workspace-bounded way."""
        symbol = SymbolID.parse(symbol_id_str)
        if not new_name or not new_name.isidentifier():
            raise ValueError(f"Invalid replacement symbol name: {new_name!r}")

        refs = await self.ast_engine.find_references(symbol_id_str=symbol_id_str, include_declaration=True)
        files = _sorted_unique([symbol.file_path, *(ref.get("file") for ref in refs)])
        receipts = self._rename_preview_receipts(symbol.symbol_name, files, new_name)
        total_replacements = sum(item["replacement_count"] for item in receipts)
        policy = self.policy.refactor("rename_symbol", symbol_id_str, files, preview=preview)

        if preview:
            return {
                "status": "preview",
                "action": "rename_symbol",
                "symbol_id": symbol_id_str,
                "old_name": symbol.symbol_name,
                "new_name": new_name,
                "files_affected": files,
                "file_receipts": receipts,
                "reference_count": len(refs),
                "replacement_count": total_replacements,
                "policy": policy.as_dict(),
                "message": "Preview mode. Pass preview=False to apply the refactor.",
            }

        if total_replacements == 0:
            return {
                "status": "noop",
                "action": "rename_symbol",
                "symbol_id": symbol_id_str,
                "old_name": symbol.symbol_name,
                "new_name": new_name,
                "files_affected": files,
                "replacement_count": 0,
                "policy": policy.as_dict(),
                "message": "No occurrences found to rename.",
            }

        applied_receipts: List[Dict[str, Any]] = []
        modified_files: List[str] = []
        for relative_path in files:
            content = self._read_file_text(relative_path)
            updated, replacements = self._replace_occurrences(content, symbol.symbol_name, new_name)
            if replacements == 0:
                applied_receipts.append(
                    {
                        "file": relative_path,
                        "status": "noop",
                        "replacement_count": 0,
                    }
                )
                continue
            self.write_layer.write_file(relative_path, updated)
            modified_files.append(relative_path)
            applied_receipts.append(
                {
                    "file": relative_path,
                    "status": "applied",
                    "replacement_count": replacements,
                }
            )

        self.write_layer._log_mutation(
            "rename_symbol",
            modified_files,
            {
                "symbol_id": symbol_id_str,
                "old_name": symbol.symbol_name,
                "new_name": new_name,
                "modified_file_count": len(modified_files),
                "replacement_count": total_replacements,
                "policy": policy.as_dict(),
            },
        )
        return {
            "status": "applied",
            "action": "rename_symbol",
            "symbol_id": symbol_id_str,
            "old_name": symbol.symbol_name,
            "new_name": new_name,
            "files_affected": files,
            "file_receipts": applied_receipts,
            "modified_files": modified_files,
            "replacement_count": total_replacements,
            "policy": policy.as_dict(),
        }

    async def replace_symbol_body(self, symbol_id_str: str, new_body: str, preview: bool = True) -> Dict[str, Any]:
        """Replace the body of a Python symbol with bounded workspace writes."""
        symbol = SymbolID.parse(symbol_id_str)
        target_path = self.write_layer._validate_boundary(symbol.file_path)
        content = target_path.read_text(encoding="utf-8")
        language = self.ast_engine._language_for_path(target_path)

        body_start_index: int
        body_end_index: int
        body_start_line: int
        body_end_line: int
        body_indent = ""

        if target_path.suffix == ".py" or language == "python":
            symbol_node = self._python_symbol_node(content, symbol.symbol_name, symbol.line)
            if symbol_node is None:
                raise ValueError(f"Symbol '{symbol.symbol_name}' not found in {symbol.file_path}")
            if not hasattr(symbol_node, "body") or not symbol_node.body:
                raise ValueError(f"Symbol '{symbol.symbol_name}' does not expose a replaceable body")

            body_start_line = symbol_node.body[0].lineno
            body_end_line = getattr(symbol_node, "end_lineno", body_start_line)
            lines = content.splitlines(keepends=True)
            body_start_index = max(body_start_line - 1, 0)
            body_end_index = max(body_end_line, body_start_line) - 1
            body_indent = re.match(r"^\s*", lines[body_start_index]).group(0) if body_start_index < len(lines) else ""
            rendered_body = self._indent_block(new_body, body_indent)
        elif language == "javascript":
            symbol_target = self._javascript_symbol_target(content, symbol.symbol_name, symbol.line)
            if symbol_target is None:
                raise ValueError(f"Symbol '{symbol.symbol_name}' not found in {symbol.file_path}")
            if not symbol_target.get("replaceable"):
                raise NotImplementedError(
                    "replace_symbol_body currently supports block-bodied JavaScript functions and classes only"
                )

            body_node = symbol_target["body_node"]
            if body_node.type not in {"statement_block", "class_body"}:
                raise NotImplementedError(
                    "replace_symbol_body currently supports block-bodied JavaScript functions and classes only"
                )

            lines = content.splitlines(keepends=True)
            body_start_line = body_node.start_point[0] + 2
            body_end_line = body_node.end_point[0] + 1
            body_start_index = body_start_line - 1
            body_end_index = body_end_line - 1
            if body_start_index >= len(lines) or body_end_index < body_start_index:
                raise NotImplementedError(
                    "replace_symbol_body currently supports multi-line JavaScript block bodies only"
                )
            if body_node.start_point[0] == body_node.end_point[0]:
                raise NotImplementedError(
                    "replace_symbol_body currently supports multi-line JavaScript block bodies only"
                )
            body_indent = re.match(r"^\s*", lines[body_start_index]).group(0)
            rendered_body = self._indent_block(new_body, body_indent)
        else:
            raise NotImplementedError("replace_symbol_body currently supports Python and JavaScript symbols only")

        policy = self.policy.refactor("replace_symbol_body", symbol_id_str, [symbol.file_path], preview=preview)

        preview_payload = {
            "status": "preview",
            "action": "replace_symbol_body",
            "symbol_id": symbol_id_str,
            "target_file": symbol.file_path,
            "symbol": symbol.symbol_name,
            "line_span": {
                "definition_start_line": symbol.line,
                "definition_end_line": body_end_line,
                "body_start_line": body_start_line,
                "body_end_line": body_end_line,
            },
            "policy": policy.as_dict(),
            "message": "Preview mode. Pass preview=False to apply the refactor.",
        }

        if preview:
            return preview_payload

        if language == "javascript":
            updated_lines = lines[:body_start_index] + rendered_body.splitlines(keepends=True) + lines[body_end_index:]
        else:
            updated_lines = lines[:body_start_index] + rendered_body.splitlines(keepends=True) + lines[body_end_index + 1 :]
        updated_content = "".join(updated_lines)
        if updated_content == content:
            return {
                "status": "noop",
                "action": "replace_symbol_body",
                "symbol_id": symbol_id_str,
                "target_file": symbol.file_path,
                "symbol": symbol.symbol_name,
                "policy": policy.as_dict(),
                "message": "Replacement produced no content changes.",
            }

        self.write_layer.write_file(symbol.file_path, updated_content)
        self.write_layer._log_mutation(
            "replace_symbol_body",
            [symbol.file_path],
            {
                "symbol_id": symbol_id_str,
                "symbol": symbol.symbol_name,
                "definition_start_line": symbol.line,
                "definition_end_line": body_end_line,
                "body_start_line": body_start_line,
                "body_end_line": body_end_line,
                "policy": policy.as_dict(),
            },
        )
        return {
            "status": "applied",
            "action": "replace_symbol_body",
            "symbol_id": symbol_id_str,
            "target_file": symbol.file_path,
            "symbol": symbol.symbol_name,
            "line_span": preview_payload["line_span"],
            "policy": policy.as_dict(),
            "message": "Successfully replaced symbol body.",
        }
