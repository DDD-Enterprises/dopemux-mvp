import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import difflib
import json

logger = logging.getLogger(__name__)

class WriteLayer:
    """Controlled code transformation layer. Strictly enforces workspace bounds."""
    
    def __init__(self, workspace_root: Path, workspace_id: str):
        self.workspace_root = workspace_root.resolve()
        self.workspace_id = workspace_id

    def _validate_boundary(self, relative_path: str) -> Path:
        """Enforce root-scoped path resolution and resolve symlinks."""
        target_path = (self.workspace_root / relative_path)
        
        # Resolve symlinks and normalize the path
        full_path = target_path.resolve()

        # Security: Ensure the resolved path is strictly within the workspace root
        try:
            full_path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(f"❌ Security: Path traversal attempt detected. Resolved path '{full_path}' is outside workspace root '{self.workspace_root}'. Original relative path: '{relative_path}'")
        
        return full_path

    def _log_mutation(self, operation: str, files: List[str], details: Dict[str, Any]):
        """Required audit logging for all mutations."""
        log_entry = {
            "type": "dopecode_write",
            "workspace_id": self.workspace_id,
            "operation": operation,
            "files": files,
            "details": details,
            "ts": time.time() # Use timestamp for logging
        }
        logger.info(json.dumps(log_entry))

    def write_file(self, relative_path: str, content: str) -> str:
        """Full overwrite of an existing file."""
        target = self._validate_boundary(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}. Use create_file instead.")
        
        try:
            # Read old content to log diff later if needed (or for future revert)
            old_content = target.read_text(encoding='utf-8')
            target.write_text(content, encoding='utf-8')
            
            # Generate a simple diff for logging purposes
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}"
            )
            diff_text = "".join(diff)

            self._log_mutation("write_file", [relative_path], {"action": "overwrite", "diff_length": len(diff_text)})
            return f"Successfully overwrote {relative_path}"
        except Exception as e:
            logger.error(f"Failed to write file {relative_path}: {e}")
            raise

    def create_file(self, relative_path: str, content: str) -> str:
        """Create a new file within the workspace."""
        target = self._validate_boundary(relative_path)
        if target.exists():
            raise FileExistsError(f"File already exists: {relative_path}. Use write_file instead.")
        
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            self._log_mutation("create_file", [relative_path], {"action": "create"})
            return f"Successfully created {relative_path}"
        except Exception as e:
            logger.error(f"Failed to create file {relative_path}: {e}")
            raise

    def apply_patch(self, relative_path: str, diff_text: str) -> str:
        """
        Apply a unified diff patch to the file.
        This is a simplified patch applier. For robust patching, external libraries like `patch` might be needed.
        For MVP, this function logs the intent and requires manual application or a more sophisticated diff tool.
        """
        target = self._validate_boundary(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found for patching: {relative_path}")
            
        # Log the intent to apply patch. Actual application is deferred.
        self._log_mutation("apply_patch", [relative_path], {"diff_length": len(diff_text), "action": "patch_intent"})
        
        # Raise NotImplementedError as per previous plan for MVP.
        # A robust diff application is complex and requires external libraries or system commands,
        # which should be avoided for controlled Python execution.
        raise NotImplementedError("apply_patch requires a robust unified diff applier, which is deferred to Phase 2. Use write_file for manual edits.")

    def batch_apply_patch(self, operations: List[Dict[str, str]], preview: bool = True) -> Dict[str, Any]:
        """
        Multi-file deterministic batch patch application.
        Requires operations to be ordered deterministically.
        """
        if preview:
            # Simulate operations and return a preview of affected files
            affected_files = set()
            for op in operations:
                path = op.get('path')
                if path:
                    affected_files.add(path)
            return {
                "status": "preview",
                "operation": "batch_apply_patch",
                "total_operations": len(operations),
                "files_affected_preview": sorted(list(affected_files)),
                "message": "Preview mode: Would apply patches to the listed files."
            }
        
        results = []
        all_files_in_batch = []
        
        # Ensure operations are ordered to maintain determinism
        # For now, we process them in the order received, assuming caller handles order.
        # In a real system, a sort based on file path might be needed.
        for op in operations:
            path = op.get('path')
            diff = op.get('diff')
            if not path or not diff:
                results.append({"file": path or "unknown", "status": "FAILED", "error": "Missing path or diff"})
                continue
                
            all_files_in_batch.append(path)
            try:
                res = self.apply_patch(path, diff)
                results.append({"file": path, "status": "SUCCESS", "message": res})
            except Exception as e:
                logger.error(f"Batch patch failed for {path}: {e}")
                results.append({"file": path, "status": "FAILED", "error": str(e)})
        
        self._log_mutation("batch_apply_patch", all_files_in_batch, {"preview": False, "operation_count": len(operations)})
        return {"batch_results": results}
