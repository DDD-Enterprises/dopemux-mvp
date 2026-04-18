import difflib
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..policy.mutation_policy import MutationPolicy

logger = logging.getLogger(__name__)


@dataclass
class _UnifiedDiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]


class WriteLayer:
    """Controlled code transformation layer. Strictly enforces workspace bounds."""

    def __init__(self, workspace_root: Path, workspace_id: str, policy: Optional[MutationPolicy] = None):
        self.workspace_root = workspace_root.resolve()
        self.workspace_id = workspace_id
        self.policy = policy or MutationPolicy(self.workspace_root, workspace_id)

    def _validate_boundary(self, relative_path: str) -> Path:
        """Resolve a workspace-relative path and reject any escape from the root."""
        if not relative_path:
            raise ValueError("Path must be provided")

        candidate = (self.workspace_root / relative_path).resolve()
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ValueError(
                f"Security: path '{relative_path}' resolves outside workspace root '{self.workspace_root}'"
            ) from exc
        return candidate

    def _normalize_patch_path(self, path_text: str) -> Optional[str]:
        path_text = path_text.strip()
        if path_text in {"/dev/null", "dev/null"}:
            return None
        if path_text.startswith("a/") or path_text.startswith("b/"):
            path_text = path_text[2:]
        return path_text

    def _log_mutation(self, operation: str, files: List[str], details: Dict[str, Any]) -> None:
        """Required audit logging for all mutations."""
        log_entry = {
            "type": "dopecode_write",
            "workspace_id": self.workspace_id,
            "operation": operation,
            "files": files,
            "details": details,
            "ts": time.time(),
        }
        logger.info(json.dumps(log_entry, sort_keys=True))

    def _parse_unified_diff(self, diff_text: str, relative_path: str) -> List[_UnifiedDiffHunk]:
        lines = diff_text.splitlines(keepends=True)
        if not lines:
            raise ValueError("Unified diff is empty")

        expected_path = relative_path.replace("\\", "/")
        old_path: Optional[str] = None
        new_path: Optional[str] = None
        hunks: List[_UnifiedDiffHunk] = []
        index = 0
        seen_hunk = False

        hunk_header = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

        while index < len(lines):
            stripped = lines[index].rstrip("\n")
            if stripped.startswith("diff --git "):
                if seen_hunk:
                    raise ValueError("Multiple file patches are not supported")
                index += 1
                continue
            if stripped.startswith("--- "):
                if seen_hunk:
                    raise ValueError("Multiple file patches are not supported")
                old_path = self._normalize_patch_path(stripped[4:])
                index += 1
                continue
            if stripped.startswith("+++ "):
                if seen_hunk:
                    raise ValueError("Multiple file patches are not supported")
                new_path = self._normalize_patch_path(stripped[4:])
                index += 1
                continue
            if stripped.startswith("@@ "):
                match = hunk_header.match(stripped)
                if not match:
                    raise ValueError(f"Malformed hunk header: {stripped}")
                seen_hunk = True
                old_start = int(match.group(1))
                old_count = int(match.group(2) or "1")
                new_start = int(match.group(3))
                new_count = int(match.group(4) or "1")
                index += 1
                hunk_lines: List[str] = []
                while index < len(lines):
                    current = lines[index]
                    current_stripped = current.rstrip("\n")
                    if current_stripped.startswith("@@ "):
                        break
                    if current_stripped.startswith("diff --git ") or current_stripped.startswith("--- ") or current_stripped.startswith("+++ "):
                        break
                    if current_stripped.startswith("\\ No newline at end of file"):
                        index += 1
                        continue
                    if not current or current[0] not in {" ", "+", "-"}:
                        raise ValueError(f"Unsupported unified diff line: {current_stripped}")
                    hunk_lines.append(current)
                    index += 1
                hunks.append(
                    _UnifiedDiffHunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        lines=hunk_lines,
                    )
                )
                continue
            index += 1

        if not hunks:
            raise ValueError("Unified diff contains no hunks")

        if old_path and old_path != expected_path:
            raise ValueError(f"Unified diff targets '{old_path}', not '{relative_path}'")
        if new_path and new_path != expected_path:
            raise ValueError(f"Unified diff targets '{new_path}', not '{relative_path}'")

        return hunks

    def _apply_hunks(self, source_lines: List[str], hunks: List[_UnifiedDiffHunk]) -> List[str]:
        result: List[str] = []
        cursor = 0

        for hunk in hunks:
            hunk_start = max(hunk.old_start - 1, 0)
            if hunk_start < cursor:
                raise ValueError("Unified diff hunks overlap or are out of order")

            result.extend(source_lines[cursor:hunk_start])
            source_index = hunk_start
            old_consumed = 0
            new_consumed = 0

            for line in hunk.lines:
                prefix = line[0]
                payload = line[1:]
                if prefix == " ":
                    if source_index >= len(source_lines) or source_lines[source_index] != payload:
                        raise ValueError("Context line mismatch while applying unified diff")
                    result.append(source_lines[source_index])
                    source_index += 1
                    old_consumed += 1
                    new_consumed += 1
                elif prefix == "-":
                    if source_index >= len(source_lines) or source_lines[source_index] != payload:
                        raise ValueError("Deletion line mismatch while applying unified diff")
                    source_index += 1
                    old_consumed += 1
                elif prefix == "+":
                    result.append(payload)
                    new_consumed += 1
                else:
                    raise ValueError(f"Unsupported unified diff marker: {prefix!r}")

            if old_consumed != hunk.old_count:
                raise ValueError(
                    f"Unified diff hunk expected {hunk.old_count} source lines, consumed {old_consumed}"
                )
            if new_consumed != hunk.new_count:
                raise ValueError(
                    f"Unified diff hunk expected {hunk.new_count} target lines, produced {new_consumed}"
                )

            cursor = source_index

        result.extend(source_lines[cursor:])
        return result

    def write_file(self, relative_path: str, content: str) -> str:
        """Full overwrite of an existing file."""
        target = self._validate_boundary(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}. Use create_file instead.")

        try:
            old_content = target.read_text(encoding="utf-8")
            target.write_text(content, encoding="utf-8")

            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}",
            )
            diff_text = "".join(diff)

            self._log_mutation(
                "write_file",
                [relative_path],
                {"action": "overwrite", "diff_length": len(diff_text)},
            )
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
            target.write_text(content, encoding="utf-8")
            self._log_mutation("create_file", [relative_path], {"action": "create"})
            return f"Successfully created {relative_path}"
        except Exception as e:
            logger.error(f"Failed to create file {relative_path}: {e}")
            raise

    def apply_patch(self, relative_path: str, diff_text: str) -> Dict[str, Any]:
        """Apply a supported unified diff patch to a single workspace file."""
        target = self._validate_boundary(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found for patching: {relative_path}")

        hunks = self._parse_unified_diff(diff_text, relative_path)
        source_lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
        patched_lines = self._apply_hunks(source_lines, hunks)
        policy = self.policy.single_file_patch(relative_path, preview=False)

        if patched_lines == source_lines:
            self._log_mutation(
                "apply_patch",
                [relative_path],
                {"action": "noop", "hunk_count": len(hunks), "changed": False, "policy": policy.as_dict()},
            )
            return {
                "status": "noop",
                "operation": "apply_patch",
                "file": relative_path,
                "changed": False,
                "hunk_count": len(hunks),
                "policy": policy.as_dict(),
                "approval_receipt": policy.approval_receipt(),
                "message": "Patch produced no content changes.",
            }

        target.write_text("".join(patched_lines), encoding="utf-8")

        added_lines = sum(1 for hunk in hunks for line in hunk.lines if line.startswith("+"))
        removed_lines = sum(1 for hunk in hunks for line in hunk.lines if line.startswith("-"))
        self._log_mutation(
            "apply_patch",
            [relative_path],
            {
                "action": "patch",
                "hunk_count": len(hunks),
                "added_lines": added_lines,
                "removed_lines": removed_lines,
                "changed": True,
                "policy": policy.as_dict(),
            },
        )
        return {
            "status": "applied",
            "operation": "apply_patch",
            "file": relative_path,
            "changed": True,
            "hunk_count": len(hunks),
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "policy": policy.as_dict(),
            "approval_receipt": policy.approval_receipt(),
            "message": f"Successfully applied patch to {relative_path}",
        }

    def batch_apply_patch(self, operations: List[Dict[str, str]], preview: bool = True) -> Dict[str, Any]:
        """Apply a deterministic batch of unified diff operations."""
        ordered = sorted(
            enumerate(operations),
            key=lambda item: ((item[1].get("path") or ""), item[0]),
        )
        ordered_files = [op.get("path") for _, op in ordered if op.get("path")]
        unique_files = sorted({path for path in ordered_files if path})
        policy = self.policy.batch_patch(operations, preview=preview)

        if preview:
            receipts = []
            for original_index, op in ordered:
                path = op.get("path")
                diff = op.get("diff")
                receipt = {
                    "index": original_index,
                    "file": path,
                    "status": "preview",
                    "operation": "apply_patch",
                    "supported": bool(path and diff),
                }
                if not path:
                    receipt["status"] = "invalid"
                    receipt["error"] = "Missing path"
                elif not diff:
                    receipt["status"] = "invalid"
                    receipt["error"] = "Missing diff"
                receipts.append(receipt)

            return {
                "status": "preview",
                "operation": "batch_apply_patch",
                "preview": True,
                "total_operations": len(operations),
                "ordered_files": unique_files,
                "receipts": receipts,
                "policy": policy.as_dict(),
                "approval_receipt": policy.approval_receipt(),
                "message": "Preview mode: no files were mutated.",
            }

        receipts = []
        applied_count = 0
        failed_count = 0

        for original_index, op in ordered:
            path = op.get("path")
            diff = op.get("diff")
            if not path:
                failed_count += 1
                receipts.append(
                    {
                        "index": original_index,
                        "file": None,
                        "status": "failed",
                        "operation": "apply_patch",
                        "error": "Missing path",
                    }
                )
                continue
            if not diff:
                failed_count += 1
                receipts.append(
                    {
                        "index": original_index,
                        "file": path,
                        "status": "failed",
                        "operation": "apply_patch",
                        "error": "Missing diff",
                    }
                )
                continue

            try:
                result = self.apply_patch(path, diff)
                applied_count += 1
                receipts.append(
                    {
                        "index": original_index,
                        "file": path,
                        "status": result["status"],
                        "operation": "apply_patch",
                        "result": result,
                    }
                )
            except Exception as exc:
                failed_count += 1
                logger.error(f"Batch patch failed for {path}: {exc}")
                receipts.append(
                    {
                        "index": original_index,
                        "file": path,
                        "status": "failed",
                        "operation": "apply_patch",
                        "error": str(exc),
                    }
                )

        batch_status = "success" if failed_count == 0 else ("partial_failure" if applied_count else "failed")
        self._log_mutation(
            "batch_apply_patch",
            unique_files,
                {
                    "preview": False,
                    "operation_count": len(operations),
                    "applied_count": applied_count,
                    "failed_count": failed_count,
                    "status": batch_status,
                    "policy": policy.as_dict(),
                },
        )
        return {
            "status": batch_status,
            "operation": "batch_apply_patch",
            "preview": False,
            "total_operations": len(operations),
            "applied_count": applied_count,
            "failed_count": failed_count,
            "ordered_files": unique_files,
            "receipts": receipts,
            "policy": policy.as_dict(),
            "approval_receipt": policy.approval_receipt(),
        }
