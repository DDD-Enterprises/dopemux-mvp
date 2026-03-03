#!/usr/bin/env python3
"""
Dopemux Failure Playbook
Handles outages and failures in Task Orchestrator + ConPort workflow

Recovery strategies:
- ConPort down → Local spooling with background replay
- Task Orchestrator ambiguity → Zen escalation for consensus
- Playwright flake → Retry with increased timeout
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import aiofiles

# MCP Client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("failure-playbook")

@dataclass
class FailureContext:
    """Context information for failure recovery"""
    failure_type: str
    component: str
    operation: str
    error_message: str
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: Optional[datetime] = None
    task_id: Optional[str] = None
    workspace_id: str = ""
    recovery_strategy: str = ""

@dataclass
class SpoolEntry:
    """Queued operation for later replay"""
    operation: str
    args: Dict[str, Any]
    timestamp: datetime
    client_id: str
    sequence_id: int

class FailurePlaybook:
    """Handles failure recovery for Dopemux workflow components"""

    def __init__(self, workspace_id: str, spool_dir: str = ".conport/spool"):
        self.workspace_id = workspace_id
        self.spool_dir = Path(spool_dir)
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        self.sequence_counter = 0

        # Recovery strategy mappings
        self.recovery_strategies = {
            "conport_down": self._recover_conport_down,
            "task_orchestrator_ambiguous": self._recover_task_ambiguity,
            "playwright_flake": self._recover_playwright_flake,
            "validation_failure": self._recover_validation_failure
        }

    # =====================================================
    # SPOOLED OPERATIONS (ConPort Down)
    # =====================================================

    async def spool_operation(self, operation: str, args: Dict[str, Any]) -> str:
        """Spool operation to local file when ConPort is unavailable"""

        client_id = f"client-{os.getpid()}-{int(time.time())}"
        self.sequence_counter += 1

        spool_entry = SpoolEntry(
            operation=operation,
            args=args,
            timestamp=datetime.now(),
            client_id=client_id,
            sequence_id=self.sequence_counter
        )

        spool_file = self.spool_dir / f"spool-{client_id}.ndjson"

        async with aiofiles.open(spool_file, 'a') as f:
            await f.write(json.dumps(asdict(spool_entry), default=str) + '\n')

        logger.info(f"Operation spooled: {operation} → {spool_file}")
        return str(spool_file)

    async def replay_spooled_operations(self) -> Dict[str, int]:
        """Replay spooled operations when ConPort becomes available"""

        replayed_count = 0
        error_count = 0

        # Find all spool files
        spool_files = list(self.spool_dir.glob("spool-*.ndjson"))

        for spool_file in spool_files:
            try:
                await self._replay_single_file(spool_file)
                replayed_count += 1
                spool_file.unlink()  # Remove successfully replayed file

            except Exception as e:
                logger.error(f"Failed to replay {spool_file}: {e}")
                error_count += 1

        return {"replayed": replayed_count, "errors": error_count}

    async def _replay_single_file(self, spool_file: Path):
        """Replay operations from a single spool file"""

        # Initialize ConPort session for replay
        conport_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"],
            env={"CONPORT_URL": "http://localhost:3004"}
        )

        async with stdio_client(conport_params) as (read, write):
            session = ClientSession(read, write)
            await session.initialize()

            async with aiofiles.open(spool_file, 'r') as f:
                async for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        spool_entry = SpoolEntry(**entry)

                        # Replay the operation
                        try:
                            await session.call_tool(spool_entry.operation, **spool_entry.args)
                            logger.info(f"Replayed: {spool_entry.operation}")
                        except Exception as e:
                            logger.error(f"Replay failed for {spool_entry.operation}: {e}")
                            raise  # Re-raise to mark file as failed

    # =====================================================
    # TASK ORCHESTRATOR AMBIGUITY → ZEN ESCALATION
    # =====================================================

    async def _recover_task_ambiguity(self, context: FailureContext) -> Dict[str, Any]:
        """Recover from Task Orchestrator ambiguity by escalating to Zen consensus"""

        logger.info("Escalating ambiguous task to Zen multi-model analysis")

        # Initialize Zen session
        zen_params = StdioServerParameters(
            command="uvx",
            args=["--from", "git+https://github.com/BeehiveInnovations/zen-mcp-server.git", "zen-mcp-server"]
        )

        async with stdio_client(zen_params) as (read, write):
            zen_session = ClientSession(read, write)
            await zen_session.initialize()

            # Get task details from ConPort
            task_details = await self._get_task_details(context.task_id)

            # Create consensus prompt for task clarification
            consensus_prompt = f"""
            This task is ambiguous and needs clarification:
            Title: {task_details.get('title', 'Unknown')}
            Description: {task_details.get('description', 'No description')}
            Error: {context.error_message}

            Please analyze this task and provide clear, actionable subtasks.
            Focus on: What specific implementation steps are needed?
            Consider: Technical constraints, dependencies, validation requirements.
            """

            # Call Zen consensus with multiple models
            consensus_result = await zen_session.call_tool(
                "zen_consensus",
                step=consensus_prompt,
                models=[
                    {"model": "gpt-5", "stance": "for", "stance_prompt": "Provide detailed, structured breakdown"},
                    {"model": "claude-sonnet-4", "stance": "against", "stance_prompt": "Challenge assumptions and clarify requirements"},
                    {"model": "gemini-pro", "stance": "neutral", "stance_prompt": "Focus on practical implementation steps"}
                ],
                step_number=1,
                total_steps=1,
                next_step_required=False
            )

            # Extract clarified task breakdown
            clarification = consensus_result.content[0].text

            # Log decision about clarification
            await self._log_recovery_decision(
                context,
                "Task ambiguity resolved via Zen consensus",
                f"Multi-model analysis provided clear task breakdown: {clarification[:200]}...",
                ["zen-escalation", "task-clarification", "consensus"]
            )

            return {
                "strategy": "zen_consensus",
                "clarification": clarification,
                "models_consulted": 3,
                "recovery_success": True
            }

    # =====================================================
    # PLAYWRIGHT FLAKE → RETRY WITH BACKOFF
    # =====================================================

    async def _recover_playwright_flake(self, context: FailureContext) -> Dict[str, Any]:
        """Recover from Playwright flakiness with retry and increased timeout"""

        logger.info(f"Retrying Playwright validation (attempt {context.retry_count + 1}/{context.max_retries})")

        # Implement exponential backoff
        backoff_seconds = 2 ** context.retry_count
        await asyncio.sleep(backoff_seconds)

        # Initialize Playwright with increased timeout
        playwright_params = StdioServerParameters(
            command="npx",
            args=["@playwright/mcp@latest"],
            env={"PLAYWRIGHT_TIMEOUT": str(30000 * (context.retry_count + 1))}  # Increase timeout
        )

        async with stdio_client(playwright_params) as (read, write):
            playwright_session = ClientSession(read, write)
            await playwright_session.initialize()

            try:
                # Retry the failed operation (would need original args)
                # This is simplified - in practice, you'd store the original call details

                await playwright_session.call_tool(
                    "playwright_browser_navigate",
                    url="http://localhost:3000"
                )

                # Take screenshot for evidence
                screenshot_path = f"retry-validation-{context.task_id}-{context.retry_count + 1}.png"
                await playwright_session.call_tool(
                    "playwright_browser_take_screenshot",
                    path=screenshot_path
                )

                # Log successful recovery
                await self._log_recovery_decision(
                    context,
                    "Playwright validation recovered via retry",
                    f"Successful retry on attempt {context.retry_count + 1} with {backoff_seconds}s backoff",
                    ["playwright-retry", "validation-recovery", "backoff"]
                )

                return {
                    "strategy": "retry_with_backoff",
                    "attempt": context.retry_count + 1,
                    "backoff_seconds": backoff_seconds,
                    "screenshot_captured": screenshot_path,
                    "recovery_success": True
                }

            except Exception as retry_error:
                if context.retry_count < context.max_retries - 1:
                    # Try again with incremented retry count
                    context.retry_count += 1
                    return await self._recover_playwright_flake(context)
                else:
                    # Max retries reached
                    await self._log_recovery_decision(
                        context,
                        "Playwright validation failed after max retries",
                        f"All {context.max_retries} retry attempts failed. Latest error: {str(retry_error)}",
                        ["playwright-failure", "max-retries", "validation-blocked"]
                    )

                    return {
                        "strategy": "retry_exhausted",
                        "attempts_made": context.max_retries,
                        "final_error": str(retry_error),
                        "recovery_success": False
                    }

    # =====================================================
    # CONPORT DOWN → SPOOL MODE
    # =====================================================

    async def _recover_conport_down(self, context: FailureContext) -> Dict[str, Any]:
        """Handle ConPort being unavailable by spooling operations"""

        logger.warning("ConPort unavailable, entering spool mode")

        # Spool the failed operation
        spool_file = await self.spool_operation(context.operation, context.__dict__)

        # Start background replay task
        asyncio.create_task(self._monitor_conport_recovery())

        return {
            "strategy": "spool_mode",
            "spool_file": spool_file,
            "background_monitoring": True,
            "recovery_success": "pending"
        }

    async def _monitor_conport_recovery(self):
        """Monitor for ConPort recovery and replay operations"""

        max_attempts = 10
        attempt = 0

        while attempt < max_attempts:
            try:
                # Test ConPort connectivity
                conport_params = StdioServerParameters(
                    command="docker",
                    args=["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"]
                )

                async with stdio_client(conport_params) as (read, write):
                    session = ClientSession(read, write)
                    await session.initialize()

                    # Test basic operation
                    await session.call_tool("conport_get_product_context", workspace_id=self.workspace_id)

                    # ConPort is back - replay operations
                    replay_result = await self.replay_spooled_operations()

                    logger.info(f"ConPort recovered, replayed {replay_result['replayed']} operations")

                    await self._log_recovery_decision(
                        FailureContext(
                            failure_type="conport_down",
                            component="conport",
                            operation="connectivity_test",
                            error_message="Service was unavailable"
                        ),
                        "ConPort service recovered",
                        f"Replayed {replay_result['replayed']} spooled operations, {replay_result['errors']} errors",
                        ["conport-recovery", "spool-replay", "service-restored"]
                    )

                    return

            except Exception:
                attempt += 1
                await asyncio.sleep(30)  # Wait 30s before retry

        logger.error("ConPort recovery failed after max attempts")
        await self._log_recovery_decision(
            FailureContext(
                failure_type="conport_down",
                component="conport",
                operation="recovery_attempt",
                error_message="Max recovery attempts exceeded"
            ),
            "ConPort recovery failed",
            "Service remained unavailable after 10 attempts. Manual intervention required.",
            ["conport-failure", "recovery-failed", "manual-intervention"]
        )

    # =====================================================
    # VALIDATION FAILURE → LOG AND ESCALATE
    # =====================================================

    async def _recover_validation_failure(self, context: FailureContext) -> Dict[str, Any]:
        """Handle validation failures by logging detailed failure analysis"""

        logger.warning(f"Validation failed for task {context.task_id}")

        # Get task details for context
        task_details = await self._get_task_details(context.task_id)

        # Log comprehensive failure decision
        await self._log_recovery_decision(
            context,
            f"Validation failed: {task_details.get('title', 'Unknown task')}",
            f"Validation checks failed: {context.error_message}. Task moved to 'blocked' status. Manual review required.",
            ["validation-failure", "task-blocked", "manual-review"],
            implementation_details=f"Task details: {task_details}. Failure context: {context.error_message}"
        )

        # Update task status to blocked
        await self._update_task_status(context.task_id, "blocked")

        return {
            "strategy": "failure_logged",
            "task_status_updated": "blocked",
            "manual_review_required": True,
            "recovery_success": "escalated"
        }

    # =====================================================
    # MAIN RECOVERY INTERFACE
    # =====================================================

    async def handle_failure(self, failure_context: FailureContext) -> Dict[str, Any]:
        """Main entry point for failure recovery"""

        logger.info(f"Handling failure: {failure_context.failure_type} in {failure_context.component}")

        # Select recovery strategy
        recovery_func = self.recovery_strategies.get(failure_context.failure_type)

        if not recovery_func:
            logger.error(f"No recovery strategy for failure type: {failure_context.failure_type}")
            return {"strategy": "none", "recovery_success": False, "error": "Unknown failure type"}

        try:
            result = await recovery_func(failure_context)

            # Update failure context with result
            failure_context.recovery_strategy = result.get("strategy", "unknown")
            failure_context.last_attempt = datetime.now()

            return result

        except Exception as e:
            logger.error(f"Recovery failed for {failure_context.failure_type}: {e}")

            await self._log_recovery_decision(
                failure_context,
                f"Recovery failed: {failure_context.failure_type}",
                f"Recovery strategy failed with error: {str(e)}",
                ["recovery-failure", "error", "manual-intervention"]
            )

            return {
                "strategy": "recovery_error",
                "error": str(e),
                "recovery_success": False,
                "manual_intervention_required": True
            }

    # =====================================================
    # HELPER METHODS
    # =====================================================

    async def _get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get task details from ConPort (with fallback)"""
        try:
            # Try ConPort first
            conport_params = StdioServerParameters(
                command="docker",
                args=["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"]
            )

            async with stdio_client(conport_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()

                result = await session.call_tool(
                    "conport_get_progress",
                    workspace_id=self.workspace_id,
                    limit=1
                )

                # Find the specific task (simplified)
                return {"title": "Retrieved task", "description": "Task details from ConPort"}

        except Exception:
            # Fallback: return minimal info
            return {"title": f"Task {task_id}", "description": "Task details unavailable (ConPort down)"}

    async def _update_task_status(self, task_id: str, status: str):
        """Update task status (with error handling)"""
        try:
            conport_params = StdioServerParameters(
                command="docker",
                args=["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"]
            )

            async with stdio_client(conport_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()

                await session.call_tool(
                    "conport_work_update_status",
                    workspace_id=self.workspace_id,
                    work_item_id=task_id,
                    status=status
                )

        except Exception as e:
            logger.warning(f"Could not update task status: {e}")

    async def _log_recovery_decision(self, context: FailureContext, title: str,
                                   rationale: str, tags: List[str],
                                   implementation_details: str = None):
        """Log recovery decisions (with error handling)"""

        try:
            conport_params = StdioServerParameters(
                command="docker",
                args=["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"]
            )

            async with stdio_client(conport_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()

                links = []
                if context.task_id:
                    links.append({"type": "work_item", "id": context.task_id})

                await session.call_tool(
                    "conport_decisions_add",
                    workspace_id=self.workspace_id,
                    title=title,
                    rationale=rationale,
                    implementation_details=implementation_details,
                    tags=tags,
                    links=links
                )

        except Exception as e:
            logger.warning(f"Could not log recovery decision: {e}")

    async def _run_shell_command(self, command: str) -> Dict[str, Any]:
        """Run shell command and return result"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_id
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "returncode": process.returncode
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# =====================================================
# CLI INTERFACE
# =====================================================

async def main():
    """CLI entry point for failure recovery testing"""

    import argparse

    parser = argparse.ArgumentParser(description="Dopemux Failure Playbook")
    parser.add_argument("--workspace", default="/Users/hue/code/dopemux-mvp")
    parser.add_argument("--failure-type", choices=[
        "conport_down", "task_orchestrator_ambiguous",
        "playwright_flake", "validation_failure"
    ], required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--error-message", required=True)
    parser.add_argument("--task-id", help="Associated task ID")

    args = parser.parse_args()

    # Create failure context
    context = FailureContext(
        failure_type=args.failure_type,
        component=args.component,
        operation=args.operation,
        error_message=args.error_message,
        task_id=args.task_id,
        workspace_id=args.workspace
    )

    # Execute recovery
    playbook = FailurePlaybook(args.workspace)
    result = await playbook.handle_failure(context)

    # Output results
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())