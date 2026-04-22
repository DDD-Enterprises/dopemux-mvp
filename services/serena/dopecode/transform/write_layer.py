import difflib
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..execution_receipts import DopeCodeExecutionReceiptStore, DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH, sha256_hex
from ..policy.mutation_policy import MutationPolicy
from .orchestration import (
    build_execution_plan,
    describe_next_action,
    execute_plan,
    extract_latest_orchestration_state,
    is_terminal_plan,
    resume_requires_explicit_opt_in,
    summarize_state_for_payload,
)

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

    def __init__(
        self,
        workspace_root: Path,
        workspace_id: str,
        policy: Optional[MutationPolicy] = None,
        receipt_store: Optional[DopeCodeExecutionReceiptStore] = None,
    ):
        self.workspace_root = workspace_root.resolve()
        self.workspace_id = workspace_id
        self.policy = policy or MutationPolicy(self.workspace_root, workspace_id)
        self.receipt_store = receipt_store or DopeCodeExecutionReceiptStore(self.workspace_root, workspace_id)

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

    def _event_type_for_status(self, status: str) -> str:
        mapping = {
            "preview": "dopecode.mutation.previewed",
            "applied": "dopecode.mutation.applied",
            "success": "dopecode.mutation.applied",
            "noop": "dopecode.mutation.noop",
            "partial_failure": "dopecode.mutation.partial_failure",
            "failed": "dopecode.mutation.failed",
        }
        return mapping.get(status, "dopecode.mutation.failed")

    def _attach_execution_receipt(
        self,
        result: Dict[str, Any],
        *,
        operation: str,
        operation_class: str,
        mutation_context: Dict[str, Any],
        execution_receipt: Dict[str, Any],
        lifecycle_stage: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        event = self.receipt_store.build_event(
            event_type=self._event_type_for_status(str(result.get("status", "failed"))),
            lifecycle_stage=lifecycle_stage,
            operation=operation,
            operation_class=operation_class,
            execution_mode=str(execution_receipt["execution_mode"]),
            execution_status=str(execution_receipt["execution_status"]),
            mutation_context=mutation_context,
            payload=payload,
        )
        stored_event, persistence_status = self.receipt_store.append_event(event)
        response = dict(result)
        response["execution_receipt"] = {
            "event": stored_event,
            "persistence": {
                "status": persistence_status,
                "path": str(DOPECODE_EXECUTION_RECEIPT_RELATIVE_PATH),
            },
        }
        return response

    def _read_file_text(self, relative_path: str) -> str:
        target = self._validate_boundary(relative_path)
        return target.read_text(encoding="utf-8")

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

    def write_file(self, relative_path: str, content: str, emit_receipt: bool = True) -> str:
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
            if emit_receipt:
                self.receipt_store.append_event(
                    self.receipt_store.build_event(
                        event_type="dopecode.mutation.applied",
                        lifecycle_stage="apply",
                        operation="write_file",
                        operation_class="file_overwrite",
                        execution_mode="direct",
                        execution_status="ready",
                        mutation_context={
                            "path": relative_path,
                            "content_sha256": sha256_hex(content),
                        },
                        payload={
                            "status": "applied",
                            "summary": f"Successfully overwrote {relative_path}",
                            "files": [relative_path],
                        },
                    )
                )
            return f"Successfully overwrote {relative_path}"
        except Exception as e:
            logger.error(f"Failed to write file {relative_path}: {e}")
            raise

    def create_file(self, relative_path: str, content: str, emit_receipt: bool = True) -> str:
        """Create a new file within the workspace."""
        target = self._validate_boundary(relative_path)
        if target.exists():
            raise FileExistsError(f"File already exists: {relative_path}. Use write_file instead.")

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            self._log_mutation("create_file", [relative_path], {"action": "create"})
            if emit_receipt:
                self.receipt_store.append_event(
                    self.receipt_store.build_event(
                        event_type="dopecode.mutation.applied",
                        lifecycle_stage="apply",
                        operation="create_file",
                        operation_class="file_create",
                        execution_mode="direct",
                        execution_status="ready",
                        mutation_context={
                            "path": relative_path,
                            "content_sha256": sha256_hex(content),
                        },
                        payload={
                            "status": "applied",
                            "summary": f"Successfully created {relative_path}",
                            "files": [relative_path],
                        },
                    )
                )
            return f"Successfully created {relative_path}"
        except Exception as e:
            logger.error(f"Failed to create file {relative_path}: {e}")
            raise

    def apply_patch(self, relative_path: str, diff_text: str, emit_receipt: bool = True) -> Dict[str, Any]:
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
            result = {
                "status": "noop",
                "operation": "apply_patch",
                "file": relative_path,
                "changed": False,
                "hunk_count": len(hunks),
                "policy": policy.as_dict(),
                "approval_receipt": policy.approval_receipt(),
                "message": "Patch produced no content changes.",
            }
            if not emit_receipt:
                return result
            return self._attach_execution_receipt(
                result,
                operation="apply_patch",
                operation_class=policy.operation_class,
                mutation_context={
                    "path": relative_path,
                    "diff_sha256": sha256_hex(diff_text),
                },
                execution_receipt=policy.approval_receipt(),
                lifecycle_stage="apply",
                payload={
                    "status": "noop",
                    "summary": "Patch produced no content changes.",
                    "files": [relative_path],
                    "changed": False,
                    "hunk_count": len(hunks),
                },
            )

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
        result = {
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
        if not emit_receipt:
            return result
        return self._attach_execution_receipt(
            result,
            operation="apply_patch",
            operation_class=policy.operation_class,
            mutation_context={
                "path": relative_path,
                "diff_sha256": sha256_hex(diff_text),
            },
            execution_receipt=policy.approval_receipt(),
            lifecycle_stage="apply",
            payload={
                "status": "applied",
                "summary": f"Successfully applied patch to {relative_path}",
                "files": [relative_path],
                "changed": True,
                "hunk_count": len(hunks),
                "added_lines": added_lines,
                "removed_lines": removed_lines,
            },
        )

    def _orchestration_lifecycle_stage(self, plan_status: str, preview: bool) -> str:
        if preview:
            return "preview"
        if plan_status in {"blocked", "partial_failure"}:
            return "resume"
        return "apply"

    def _orchestration_event_status(self, plan_status: str, preview: bool) -> str:
        if preview:
            return "preview"
        if plan_status in {"verified", "completed"}:
            return "applied"
        if plan_status == "failed":
            return "failed"
        return "partial_failure"

    def _build_patch_execution_plan(
        self,
        *,
        operation: str,
        operation_class: str,
        mutation_context: Dict[str, Any],
        operations: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        mutation_id = self.receipt_store.mutation_id_for(
            operation=operation,
            operation_class=operation_class,
            mutation_context=mutation_context,
        )
        ordered = sorted(
            enumerate(operations),
            key=lambda item: ((item[1].get("path") or ""), item[0]),
        )
        steps: List[Dict[str, Any]] = []
        for _, op in ordered:
            path = op.get("path")
            diff = op.get("diff")
            if not path or not diff:
                raise ValueError("Batch patch orchestration requires every operation to include path and diff")
            before_content = self._read_file_text(path)
            hunks = self._parse_unified_diff(diff, path)
            after_content = "".join(self._apply_hunks(before_content.splitlines(keepends=True), hunks))
            steps.append(
                {
                    "step_type": "apply_patch",
                    "title": f"Patch {path}",
                    "file": path,
                    "operation": {
                        "path": path,
                        "diff_text": diff,
                        "before_sha256": sha256_hex(before_content),
                        "after_sha256": sha256_hex(after_content),
                    },
                }
            )
            steps.append(
                {
                    "step_type": "verify_file_sha",
                    "title": f"Verify patched state for {path}",
                    "file": path,
                    "operation": {
                        "path": path,
                        "expected_sha256": sha256_hex(after_content),
                    },
                }
            )
        return build_execution_plan(
            mutation_id=mutation_id,
            operation=operation,
            operation_class=operation_class,
            summary="Deterministic bounded batch patch execution.",
            steps=steps,
        )

    def _unsupported_execution_plan(
        self,
        *,
        operation: str,
        operation_class: str,
        mutation_context: Dict[str, Any],
        files: List[str],
        reason: str,
    ) -> Dict[str, Any]:
        mutation_id = self.receipt_store.mutation_id_for(
            operation=operation,
            operation_class=operation_class,
            mutation_context=mutation_context,
        )
        return {
            "schema_version": "dopecode.orchestration_state.v1",
            "plan_id": None,
            "mutation_id": mutation_id,
            "operation": operation,
            "operation_class": operation_class,
            "plan_status": "blocked",
            "summary": "Orchestration unavailable for the current bounded batch request.",
            "resume_supported": False,
            "deterministic": True,
            "replay_safe": True,
            "current_step_id": None,
            "blocked_reason": reason,
            "next_action": "inspect_request",
            "affected_files": files,
            "steps": [],
            "status_counts": {},
            "completed_step_count": 0,
            "step_count": 0,
        }

    def batch_apply_patch(self, operations: List[Dict[str, str]], preview: bool = True, resume: bool = False) -> Dict[str, Any]:
        """Apply a deterministic batch of unified diff operations."""
        ordered = sorted(
            enumerate(operations),
            key=lambda item: ((item[1].get("path") or ""), item[0]),
        )
        ordered_files = [op.get("path") for _, op in ordered if op.get("path")]
        unique_files = sorted({path for path in ordered_files if path})
        policy = self.policy.batch_patch(operations, preview=preview)

        mutation_context = {
            "operations": [
                {
                    "path": op.get("path"),
                    "diff_sha256": sha256_hex(op.get("diff", "")) if op.get("diff") else None,
                }
                for _, op in ordered
            ]
        }
        execution_plan_error: Optional[str] = None
        try:
            execution_plan = self._build_patch_execution_plan(
                operation="batch_apply_patch",
                operation_class=policy.operation_class,
                mutation_context=mutation_context,
                operations=operations,
            )
        except Exception as exc:
            execution_plan_error = str(exc)
            execution_plan = self._unsupported_execution_plan(
                operation="batch_apply_patch",
                operation_class=policy.operation_class,
                mutation_context=mutation_context,
                files=unique_files,
                reason=execution_plan_error,
            )
        prior_state = extract_latest_orchestration_state(
            self.receipt_store.load_events(),
            mutation_id=str(execution_plan["mutation_id"]),
            operation="batch_apply_patch",
        )

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

            return self._attach_execution_receipt(
                {
                "status": "preview",
                "operation": "batch_apply_patch",
                "preview": True,
                "total_operations": len(operations),
                "ordered_files": unique_files,
                "receipts": receipts,
                "execution_plan": execution_plan,
                "policy": policy.as_dict(),
                "approval_receipt": policy.approval_receipt(),
                "message": "Preview mode: no files were mutated.",
                },
                operation="batch_apply_patch",
                operation_class=policy.operation_class,
                mutation_context={
                    "operations": [
                        {
                            "path": op.get("path"),
                            "diff_sha256": sha256_hex(op.get("diff", "")) if op.get("diff") else None,
                        }
                        for _, op in ordered
                    ]
                },
                execution_receipt=policy.approval_receipt(),
                lifecycle_stage="preview",
                payload={
                    "status": "preview",
                    "summary": "Preview mode: no files were mutated.",
                    "files": unique_files,
                    "preview": True,
                    "total_operations": len(operations),
                    "invalid_operations": sum(1 for item in receipts if item["status"] == "invalid"),
                    "orchestration": summarize_state_for_payload(execution_plan),
                },
            )

        if execution_plan_error is not None:
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
            return self._attach_execution_receipt(
                {
                "status": batch_status,
                "operation": "batch_apply_patch",
                "preview": False,
                "total_operations": len(operations),
                "applied_count": applied_count,
                "failed_count": failed_count,
                "ordered_files": unique_files,
                "receipts": receipts,
                "execution_plan": execution_plan,
                "policy": policy.as_dict(),
                "approval_receipt": policy.approval_receipt(),
                "message": execution_plan_error,
                },
                operation="batch_apply_patch",
                operation_class=policy.operation_class,
                mutation_context=mutation_context,
                execution_receipt=policy.approval_receipt(),
                lifecycle_stage="apply",
                payload={
                    "status": batch_status,
                    "summary": execution_plan_error,
                    "files": unique_files,
                    "preview": False,
                    "total_operations": len(operations),
                    "applied_count": applied_count,
                    "failed_count": failed_count,
                    "orchestration": summarize_state_for_payload(execution_plan),
                },
            )

        if prior_state is not None and resume_requires_explicit_opt_in(prior_state) and not resume:
            state = prior_state
        elif prior_state is not None and (resume or is_terminal_plan(prior_state)):
            state = execute_plan(
                prior_state,
                read_file=self._read_file_text,
                apply_patch=lambda path, diff: self.apply_patch(path, diff, emit_receipt=False),
                resume=resume,
            )
        else:
            state = execute_plan(
                execution_plan,
                read_file=self._read_file_text,
                apply_patch=lambda path, diff: self.apply_patch(path, diff, emit_receipt=False),
                resume=resume,
            )

        applied_count = sum(1 for step in state["steps"] if step["status"] == "applied")
        failed_count = sum(1 for step in state["steps"] if step["status"] in {"failed", "blocked"})
        batch_status = (
            "success"
            if state["plan_status"] in {"verified", "completed"}
            else ("partial_failure" if failed_count or state["plan_status"] == "partial_failure" else "failed")
        )
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
        return self._attach_execution_receipt(
            {
            "status": batch_status,
            "operation": "batch_apply_patch",
            "preview": False,
            "total_operations": len(operations),
            "applied_count": applied_count,
            "failed_count": failed_count,
            "ordered_files": unique_files,
            "execution_plan": state,
            "policy": policy.as_dict(),
            "approval_receipt": policy.approval_receipt(),
            "message": describe_next_action(state),
            },
            operation="batch_apply_patch",
            operation_class=policy.operation_class,
            mutation_context=mutation_context,
            execution_receipt=policy.approval_receipt(),
            lifecycle_stage=self._orchestration_lifecycle_stage(state["plan_status"], preview=False),
            payload={
                "status": self._orchestration_event_status(state["plan_status"], preview=False),
                "summary": describe_next_action(state),
                "files": unique_files,
                "preview": False,
                "total_operations": len(operations),
                "applied_count": applied_count,
                "failed_count": failed_count,
                "orchestration": summarize_state_for_payload(state),
            },
        )
