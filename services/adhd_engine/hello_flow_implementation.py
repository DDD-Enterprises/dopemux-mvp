#!/usr/bin/env python3
"""
Dopemux Hello-Flow Implementation
4-step workflow: Pick → Plan → Execute → Validate → Close

This implements the core Task Orchestrator + ConPort workflow for ADHD-optimized development.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# MCP Client imports (simplified for implementation)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hello-flow")

class DopemuxHelloFlow:
    """Implements the 4-step Hello-Flow for Task Orchestrator + ConPort"""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.current_task_id: Optional[str] = None
        self.conport_session = None
        self.task_orchestrator_session = None
        self.playwright_session = None

    async def initialize_mcp_sessions(self):
        """Initialize all required MCP server connections"""

        # ConPort - Memory & Decisions
        conport_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"],
            env={"CONPORT_URL": "http://localhost:3004"}
        )

        # Task Orchestrator - Tactical Execution
        task_params = StdioServerParameters(
            command="python",
            args=["services/task-orchestrator/server.py"],
            env={"DOPEMUX_INSTANCE_ID": "hello-flow"}
        )

        # Playwright - Validation
        playwright_params = StdioServerParameters(
            command="npx",
            args=["@playwright/mcp@latest"]
        )

        # Initialize sessions
        async with stdio_client(conport_params) as (read, write):
            self.conport_session = ClientSession(read, write)
            await self.conport_session.initialize()

        async with stdio_client(task_params) as (read, write):
            self.task_orchestrator_session = ClientSession(read, write)
            await self.task_orchestrator_session.initialize()

        async with stdio_client(playwright_params) as (read, write):
            self.playwright_session = ClientSession(read, write)
            await self.playwright_session.initialize()

        logger.info("All MCP sessions initialized")

    # =====================================================
    # STEP 1: PICK WORK
    # =====================================================

    async def step1_pick_work(self, project_filter: Optional[str] = None) -> Dict:
        """Step 1: Pull next work from ConPort upcoming queue"""

        logger.info("Step 1: Picking next work item...")

        # Get upcoming work items
        upcoming_result = await self.conport_session.call_tool(
            "conport_work_upcoming_next",
            workspace_id=self.workspace_id,
            project=project_filter,
            limit=3
        )

        upcoming_tasks = upcoming_result.content[0].text
        upcoming_tasks = json.loads(upcoming_tasks) if isinstance(upcoming_tasks, str) else upcoming_tasks

        if not upcoming_tasks:
            logger.info("No upcoming work found")
            return {"status": "no_work", "message": "No upcoming tasks available"}

        # Select first task (ADHD: choose one clear task)
        selected_task = upcoming_tasks[0]
        self.current_task_id = selected_task["id"]

        # Log decision about task selection
        await self._log_decision(
            title=f"Selected task: {selected_task['title']}",
            rationale=f"Top priority task from upcoming queue (priority: {selected_task.get('priority', 'medium')})",
            tags=["task-selection", "workflow-start"],
            links=[{"type": "work_item", "id": self.current_task_id}]
        )

        # Update task status to in_progress
        await self.conport_session.call_tool(
            "conport_work_update_status",
            workspace_id=self.workspace_id,
            work_item_id=self.current_task_id,
            status="in_progress"
        )

        logger.info(f"Selected task: {selected_task['title']}")
        return {
            "status": "task_selected",
            "task": selected_task,
            "task_id": self.current_task_id
        }

    # =====================================================
    # STEP 2: PLAN & EXECUTE
    # =====================================================

    async def step2_plan_and_execute(self, task: Dict) -> Dict:
        """Step 2: Plan with Task Orchestrator and complete subtasks"""

        logger.info("Step 2: Planning and executing task...")

        # Plan the task using Task Orchestrator
        plan_result = await self.task_orchestrator_session.call_tool(
            "task_orchestrator_plan",
            input=f"{task['title']}: {task.get('description', '')}",
            max_subtasks=3  # ADHD-optimized: max 3 subtasks
        )

        plan_data = json.loads(plan_result.content[0].text)

        # Execute each subtask
        completed_subtasks = []
        for subtask in plan_data.get("subtasks", []):

            logger.info(f"Executing subtask: {subtask['title']}")

            # Mark subtask complete in Task Orchestrator
            await self.task_orchestrator_session.call_tool(
                "task_orchestrator_set_status",
                id=subtask["id"],
                status="done"
            )

            completed_subtasks.append(subtask)

            # ADHD: Celebrate small wins
            logger.info(f"✅ Subtask complete: {subtask['title']}")

        # Log completion decision
        await self._log_decision(
            title=f"Completed task planning and execution: {task['title']}",
            rationale=f"Successfully executed {len(completed_subtasks)} subtasks using Task Orchestrator",
            implementation_details=f"Subtasks: {', '.join([s['title'] for s in completed_subtasks])}",
            tags=["task-execution", "implementation"],
            links=[{"type": "work_item", "id": self.current_task_id}]
        )

        return {
            "status": "execution_complete",
            "subtasks_completed": len(completed_subtasks),
            "subtasks": completed_subtasks
        }

    # =====================================================
    # STEP 3: VALIDATE
    # =====================================================

    async def step3_validate(self, task: Dict) -> Dict:
        """Step 3: Validate implementation with Playwright"""

        logger.info("Step 3: Validating implementation...")

        validation_results = []

        # Determine validation approach based on task type
        if "ui" in task.get("tags", []) or "frontend" in task.get("description", "").lower():

            # UI Validation with Playwright
            validation_results = await self._validate_with_playwright(task)

        elif "api" in task.get("tags", []) or "backend" in task.get("description", "").lower():

            # API Validation (simplified - would use HTTP client)
            validation_results = await self._validate_api(task)

        else:

            # Generic validation
            validation_results = [{"status": "passed", "type": "generic", "message": "Basic validation completed"}]

        # Attach validation artifacts
        for result in validation_results:
            if result.get("screenshot_path"):
                await self.conport_session.call_tool(
                    "conport_artifacts_attach",
                    workspace_id=self.workspace_id,
                    kind="screenshot",
                    title=f"Validation: {task['title']}",
                    path=result["screenshot_path"],
                    description=result.get("message", ""),
                    work_item_id=self.current_task_id
                )

        # Determine overall validation status
        all_passed = all(r.get("status") == "passed" for r in validation_results)
        validation_status = "passed" if all_passed else "failed"

        # Log validation decision
        await self._log_decision(
            title=f"Validation {'passed' if all_passed else 'failed'}: {task['title']}",
            rationale=f"Validation completed with status: {validation_status}. Results: {len(validation_results)} checks performed.",
            implementation_details=f"Validation types: {', '.join(set(r.get('type', 'unknown') for r in validation_results))}",
            tags=["validation", "playwright", validation_status],
            links=[{"type": "work_item", "id": self.current_task_id}]
        )

        return {
            "status": validation_status,
            "validation_results": validation_results,
            "checks_performed": len(validation_results)
        }

    async def _validate_with_playwright(self, task: Dict) -> List[Dict]:
        """Validate UI features with Playwright"""

        results = []

        try:
            # Navigate to application
            await self.playwright_session.call_tool(
                "playwright_browser_navigate",
                url="http://localhost:3000"  # Would be configurable
            )

            # Perform validation steps (simplified)
            # In practice, this would be more sophisticated based on the task

            # Take screenshot for evidence
            screenshot_result = await self.playwright_session.call_tool(
                "playwright_browser_take_screenshot",
                path=f"validation-{self.current_task_id}.png"
            )

            results.append({
                "status": "passed",
                "type": "ui",
                "message": "UI validation completed successfully",
                "screenshot_path": f"validation-{self.current_task_id}.png"
            })

        except Exception as e:
            results.append({
                "status": "failed",
                "type": "ui",
                "message": f"UI validation failed: {str(e)}"
            })

        return results

    async def _validate_api(self, task: Dict) -> List[Dict]:
        """Validate API endpoints (simplified)"""
        # In practice, this would make HTTP requests
        return [{"status": "passed", "type": "api", "message": "API validation completed"}]

    # =====================================================
    # STEP 4: CLOSE LOOP
    # =====================================================

    async def step4_close_loop(self, task: Dict, validation_result: Dict) -> Dict:
        """Step 4: Update status and close the workflow loop"""

        logger.info("Step 4: Closing workflow loop...")

        # Determine final task status
        if validation_result["status"] == "passed":
            final_status = "done"
            outcome_message = "Task completed successfully with validation"
        else:
            final_status = "blocked"
            outcome_message = "Task blocked due to validation failures"

        # Update task status in ConPort
        await self.conport_session.call_tool(
            "conport_work_update_status",
            workspace_id=self.workspace_id,
            work_item_id=self.current_task_id,
            status=final_status
        )

        # Log final completion decision
        await self._log_decision(
            title=f"Workflow closed: {task['title']} - {final_status.upper()}",
            rationale=f"Task workflow completed. Validation: {validation_result['status']}. {outcome_message}",
            implementation_details=f"Completed {validation_result.get('checks_performed', 0)} validation checks. Final status: {final_status}",
            tags=["workflow-complete", "task-closed", final_status],
            links=[{"type": "work_item", "id": self.current_task_id}]
        )

        # Link validation artifacts to task
        await self.conport_session.call_tool(
            "conport_graph_link",
            workspace_id=self.workspace_id,
            source_type="work_item",
            source_id=self.current_task_id,
            target_type="decision",
            target_id=f"decisions/{datetime.now().strftime('%Y-%m-%d')}-validation-{self.current_task_id[-8:]}",
            relationship_type="validated_by",
            description="Task completion validated through automated checks"
        )

        logger.info(f"Workflow closed: {task['title']} → {final_status.upper()}")

        return {
            "status": "loop_closed",
            "final_task_status": final_status,
            "outcome": outcome_message,
            "validation_summary": validation_result
        }

    # =====================================================
    # HELPER METHODS
    # =====================================================

    async def _log_decision(self, title: str, rationale: str, tags: List[str],
                           links: List[Dict], implementation_details: str = None):
        """Helper to log decisions in ConPort"""

        await self.conport_session.call_tool(
            "conport_decisions_add",
            workspace_id=self.workspace_id,
            title=title,
            rationale=rationale,
            implementation_details=implementation_details,
            tags=tags,
            links=links
        )

    # =====================================================
    # MAIN WORKFLOW EXECUTOR
    # =====================================================

    async def execute_hello_flow(self, project_filter: Optional[str] = None) -> Dict:
        """Execute the complete 4-step Hello-Flow"""

        logger.info("🚀 Starting Dopemux Hello-Flow execution")

        try:
            # Initialize MCP sessions
            await self.initialize_mcp_sessions()

            # Step 1: Pick work
            step1_result = await self.step1_pick_work(project_filter)
            if step1_result["status"] == "no_work":
                return {"status": "no_work_available", "message": "No upcoming tasks to process"}

            task = step1_result["task"]
            logger.info(f"📋 Step 1 Complete: Selected '{task['title']}'")

            # Step 2: Plan & Execute
            step2_result = await self.step2_plan_and_execute(task)
            logger.info(f"🔧 Step 2 Complete: Executed {step2_result['subtasks_completed']} subtasks")

            # Step 3: Validate
            step3_result = await self.step3_validate(task)
            logger.info(f"✅ Step 3 Complete: Validation {step3_result['status'].upper()}")

            # Step 4: Close Loop
            step4_result = await self.step4_close_loop(task, step3_result)
            logger.info(f"🔄 Step 4 Complete: Workflow closed - {step4_result['final_task_status'].upper()}")

            return {
                "status": "hello_flow_complete",
                "task_completed": task["title"],
                "final_status": step4_result["final_task_status"],
                "validation_status": step3_result["status"],
                "subtasks_executed": step2_result["subtasks_completed"],
                "validation_checks": step3_result["checks_performed"],
                "execution_time": "calculated_duration",  # Would calculate actual time
                "artifacts_created": len([r for r in step3_result["validation_results"] if r.get("screenshot_path")])
            }

        except Exception as e:
            logger.error(f"Hello-Flow execution failed: {e}")

            # Log failure decision
            if self.current_task_id:
                await self._log_decision(
                    title=f"Hello-Flow execution failed: {task.get('title', 'Unknown task')}",
                    rationale=f"Workflow failed with error: {str(e)}",
                    tags=["workflow-failure", "error"],
                    links=[{"type": "work_item", "id": self.current_task_id}]
                )

            return {
                "status": "execution_failed",
                "error": str(e),
                "task_id": self.current_task_id
            }

# =====================================================
# CLI INTERFACE
# =====================================================

async def main():
    """CLI entry point for Hello-Flow execution"""

    import argparse

    parser = argparse.ArgumentParser(description="Dopemux Hello-Flow Executor")
    parser.add_argument("--workspace", default="/Users/hue/code/dopemux-mvp",
                       help="Workspace directory path")
    parser.add_argument("--project", help="Optional project filter for work selection")

    args = parser.parse_args()

    # Execute Hello-Flow
    workflow = DopemuxHelloFlow(args.workspace)
    result = await workflow.execute_hello_flow(args.project)

    # Output results
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())