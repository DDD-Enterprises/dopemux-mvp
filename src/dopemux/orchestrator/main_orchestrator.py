"""
Main Dopemux Orchestrator with ADHD UX Integration

This orchestrator ties together all Dopemux components with ADHD-optimized UX.
Integrates parallel MCP operations, hook systems, and ADHD workflow management.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from .adhd_orchestrator import ADHDOrchestrator
from ..hooks.hook_manager import HookManager
from ..mcp.parallel_executor import MCPParallelExecutor
from ..tools.conport_client import ConPortClient


class BatchFileOps:
    """Simple async batch file operations used by main orchestrator."""

    async def batch_read_files(self, paths: List[str]) -> List[Dict[str, Any]]:
        async def _read(path_str: str) -> Dict[str, Any]:
            path = Path(path_str)
            try:
                content = await asyncio.to_thread(path.read_text, encoding="utf-8")
                return {"path": str(path), "success": True, "content": content}
            except Exception as exc:
                return {"path": str(path), "success": False, "error": str(exc)}

        return await asyncio.gather(*[_read(path) for path in paths])

    async def batch_write_files(self, writes: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        async def _write(item: Dict[str, str]) -> Dict[str, Any]:
            path = Path(item.get("path", ""))
            content = item.get("content", "")
            if not path:
                return {"path": "", "success": False, "error": "Missing path"}
            try:
                await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
                await asyncio.to_thread(path.write_text, content, encoding="utf-8")
                return {"path": str(path), "success": True}
            except Exception as exc:
                return {"path": str(path), "success": False, "error": str(exc)}

        return await asyncio.gather(*[_write(item) for item in writes])

class MainDopemuxOrchestrator:
    """
    Main orchestrator integrating all Dopemux enhancements.

    Provides ADHD-optimized workflow with parallel operations, seamless hooks,
    and cognitive load management.
    """

    def __init__(self):
        self.adhd_orchestrator = ADHDOrchestrator()
        self.hook_manager = HookManager()
        self.conport_client = ConPortClient()
        self.parallel_executor = MCPParallelExecutor()
        self.batch_file_ops = BatchFileOps()

        # Start hook monitoring
        self.hook_manager.start_monitoring()

    async def execute_task(
        self,
        task_type: str,
        task_params: Dict[str, Any],
        use_adhd_ux: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task with full Dopemux enhancements.

        Args:
            task_type: Type of task (mcp_call, file_op, workflow_step, etc.)
            task_params: Parameters for the task
            use_adhd_ux: Whether to use ADHD optimizations

        Returns:
            Task result with ADHD metadata
        """
        if use_adhd_ux:
            # Start ADHD session
            self.adhd_orchestrator.start_session(task_description=task_type)

        try:
            # Execute based on task type
            result = await self._dispatch_task(task_type, task_params)

            # Update cognitive load
            self.adhd_orchestrator.workflow_manager.update_cognitive_load(
                load_level=0.6,  # Simulated
                context=f"Completed {task_type}"
            )

            # Check for break
            break_needed = self.adhd_orchestrator.workflow_manager.check_break_needed()
            if break_needed[0]:
                self.adhd_orchestrator.workflow_manager.take_break()

            return {
                "result": result,
                "adhd_status": self.adhd_orchestrator.get_status_snapshot(),
                "break_recommended": break_needed[0]
            }

        finally:
            if use_adhd_ux:
                # End session
                self.adhd_orchestrator.end_session()

    async def _dispatch_task(self, task_type: str, params: Dict[str, Any]) -> Any:
        """Dispatch task to appropriate handler."""
        if task_type == "mcp_call":
            return await self._execute_mcp_call(params)
        elif task_type == "file_op":
            return await self._execute_file_op(params)
        elif task_type == "workflow_step":
            return await self._execute_workflow_step(params)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _execute_mcp_call(self, params: Dict[str, Any]) -> Any:
        """Execute MCP call with parallel processing."""
        method = params.get("method")
        kwargs = params.get("kwargs", {})
        if not method or not hasattr(self.conport_client, method):
            raise ValueError(f"Unknown ConPort client method: {method}")

        # Use parallel executor for batch operations
        if isinstance(kwargs.get("data"), list):
            calls = [{"method": method, "kwargs": item} for item in kwargs.pop("data")]
            results = await self.parallel_executor.execute_batch(
                self.conport_client,
                calls
            )
            return {"batch_results": results}
        else:
            # Single call
            return await getattr(self.conport_client, method)(**kwargs)

    async def _execute_file_op(self, params: Dict[str, Any]) -> Any:
        """Execute file operation with batch handling."""
        op_type = params.get("op_type")
        paths = params.get("paths", [])

        if op_type == "read":
            return await self.batch_file_ops.batch_read_files(paths)
        elif op_type == "write":
            return await self.batch_file_ops.batch_write_files(params["writes"])
        else:
            raise ValueError(f"Unknown file op: {op_type}")

    async def _execute_workflow_step(self, params: Dict[str, Any]) -> Any:
        """Execute workflow step with hook integration."""
        # Trigger hook if applicable
        if params.get("trigger_hook"):
            await self.hook_manager.trigger_hook(
                params["hook_type"],
                params.get("hook_context", {})
            )

        # Execute step
        step_result = await self.adhd_orchestrator.execute_with_adhd_optimization(
            lambda: self._simple_step(params),
            **params
        )

        return step_result

    async def _simple_step(self, params: Dict[str, Any]) -> Any:
        """Simple workflow step for testing."""
        await asyncio.sleep(0.1)  # Simulate work
        return {"step_completed": True, "params": params}

    def get_adhd_status(self) -> Dict[str, Any]:
        """Get current ADHD status."""
        return self.adhd_orchestrator.get_status_snapshot()

    def start_hooks(self):
        """Start hook monitoring."""
        self.hook_manager.start_monitoring()

    def stop_hooks(self):
        """Stop hook monitoring."""
        self.hook_manager.stop_monitoring()


# Global instance
main_orchestrator = MainDopemuxOrchestrator()
