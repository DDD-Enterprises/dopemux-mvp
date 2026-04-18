import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import difflib

logger = logging.getLogger(__name__)

class WriteLayer:
    """Controlled code transformation layer. Strictly enforces workspace bounds."""

    def __init__(self, workspace_root: Path, workspace_id: str):
        self.workspace_root = workspace_root.resolve()
        self.workspace_id = workspace_id

    def _validate_boundary(self, relative_path: str) -> Path:
        """Enforce root-scoped path resolution."""
        full_path = (self.workspace_root / relative_path).resolve()
        if not str(full_path).startswith(str(self.workspace_root)):
            raise ValueError(f"❌ Security: Path '{relative_path}' escapes workspace root {self.workspace_root}")
        return full_path

    def _log_mutation(self, operation: str, files: List[str], details: Any):
        """Required audit logging for all mutations."""
        logger.info(str({
            "type": "dopecode_write",
            "workspace_id": self.workspace_id,
            "operation": operation,
            "files": files,
            "details": details,
            "ts": str(time.time())
        }))

    def write_file(self, relative_path: str, content: str) -> str:
        """Full overwrite of an existing file."""
        target = self._validate_boundary(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}. Use create_file instead.")
        
        target.write_text(content, encoding='utf-8')
        self._log_mutation("write_file", [relative_path], {"action": "overwrite"})
        return f"Successfully overwrote {relative_path}"

    def create_file(self, relative_path: str, content: str) -> str:
        """Create a new file within the workspace."""
        target = self._validate_boundary(relative_path)
        if target.exists():
            raise FileExistsError(f"File already exists: {relative_path}. Use write_file instead.")
        
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        self._log_mutation("create_file", [relative_path], {"action": "create"})
        return f"Successfully created {relative_path}"

    def apply_patch(self, relative_path: str, diff_text: str) -> str:
        """
        Apply a unified diff patch to the file.
        This is a simplified patch applier. For robust patching, external libraries like `patch` might be needed,
        but for standard MCP tool replacement, we try to apply chunks or fallback to standard python patch if available.
        For MVP, we will assume diff_text is standard unified diff, but we can also use a string replacement logic if diff fails.
        """
        # Note: Implementing a full patch applier in pure python without external dependencies can be brittle.
        # Often LLMs output replace operations rather than strict unified diffs.
        target = self._validate_boundary(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
            
        # As an MVP controlled transform: we will log the diff intent and use a basic line replacement or ask user for full file write.
        # Since 'apply_patch' is requested, we'll log it.
        self._log_mutation("apply_patch", [relative_path], {"diff_length": len(diff_text)})
        
        # We need a unified diff applier. We will use a naive implementation or simply fail safe.
        raise NotImplementedError("apply_patch requires a robust unified diff applier which is deferred to Phase 2. Use write_file for now.")

    def batch_apply_patch(self, operations: List[Dict[str, str]], preview: bool = True) -> str:
        """Multi-file deterministic batch patch application."""
        if preview:
            return f"Preview mode: Would modify {len(operations)} files."
        
        results = []
        for op in operations:
            path = op.get('path')
            diff = op.get('diff')
            try:
                res = self.apply_patch(path, diff)
                results.append(f"SUCCESS: {path}")
            except Exception as e:
                results.append(f"FAILED {path}: {str(e)}")
        
        self._log_mutation("batch_apply_patch", [op.get('path') for op in operations], {"preview": False})
        return "\\n".join(results)
