"""
Deployment Orchestration Coordinator for Task Orchestrator
CI/CD Integration with ADHD-Optimized Deployment Workflows

Handles automated testing, deployment coordination, and release management
with neurodivergent-friendly monitoring and rollback capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import subprocess
import aiohttp

logger = logging.getLogger(__name__)


class DeploymentStage(str, Enum):
    """Stages in deployment pipeline."""
    PREPARATION = "preparation"           # Pre-deployment checks
    TESTING = "testing"                  # Automated testing
    STAGING = "staging"                  # Staging deployment
    PRODUCTION = "production"            # Production deployment
    VERIFICATION = "verification"        # Post-deployment checks
    ROLLBACK = "rollback"               # Rollback if needed


class DeploymentStatus(str, Enum):
    """Status of deployment operations."""
    PENDING = "pending"                  # Waiting to start
    RUNNING = "running"                  # Currently executing
    SUCCESS = "success"                  # Completed successfully
    FAILED = "failed"                   # Failed with errors
    CANCELLED = "cancelled"             # Manually cancelled
    ROLLING_BACK = "rolling_back"       # Rollback in progress


class TestType(str, Enum):
    """Types of automated tests."""
    UNIT = "unit"                       # Unit tests
    INTEGRATION = "integration"         # Integration tests
    E2E = "e2e"                        # End-to-end tests
    PERFORMANCE = "performance"         # Performance tests
    SECURITY = "security"              # Security tests
    ACCESSIBILITY = "accessibility"     # ADHD/accessibility tests


@dataclass
class DeploymentTask:
    """Individual deployment task with ADHD considerations."""
    task_id: str
    name: str
    stage: DeploymentStage
    test_types: List[TestType]
    command: str
    timeout_minutes: float
    retry_attempts: int

    # Dependencies
    depends_on: List[str]                # Other task IDs
    blocks: List[str]                    # Tasks blocked by this one

    # Status tracking
    status: DeploymentStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    output_log: List[str]

    # ADHD considerations
    cognitive_impact: float              # 0.0-1.0 mental overhead
    interruption_safe: bool             # Can be paused/resumed
    attention_required: bool             # Needs active monitoring
    visual_progress: bool                # Show progress indicators


@dataclass
class DeploymentPipeline:
    """Complete deployment pipeline with orchestration metadata."""
    pipeline_id: str
    name: str
    description: str
    git_branch: str
    target_environment: str

    # Pipeline configuration
    tasks: List[DeploymentTask]
    parallel_stages: List[List[str]]     # Tasks that can run in parallel
    critical_path: List[str]             # Critical path task IDs

    # ADHD optimizations
    gentle_notifications: bool           # Use gentle notifications
    batch_alerts: bool                  # Batch non-critical alerts
    visual_dashboard_url: Optional[str]  # URL to visual dashboard
    break_points: List[str]             # Natural stopping points

    # Metadata
    created_at: datetime
    estimated_duration: float           # Total estimated minutes
    success_rate: float                 # Historical success rate


class DeploymentOrchestrationCoordinator:
    """
    Intelligent deployment coordination with ADHD-optimized workflows.

    Features:
    - Automated CI/CD pipeline orchestration
    - ADHD-friendly deployment monitoring
    - Smart rollback decision making
    - Visual progress tracking
    - Cognitive load-aware alert batching
    - Break-friendly deployment scheduling
    """

    def __init__(self, conport_client=None, context7_client=None):
        self.conport = conport_client
        self.context7 = context7_client

        # Pipeline management
        self.pipelines: Dict[str, DeploymentPipeline] = {}
        self.active_deployments: Dict[str, DeploymentPipeline] = {}
        self.deployment_history: List[Dict[str, Any]] = []

        # Testing coordination
        self.test_runners: Dict[TestType, Dict[str, Any]] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}

        # ADHD optimizations
        self.notification_batching = True
        self.gentle_mode = True
        self.visual_feedback = True
        self.break_enforcement = True

        # Monitoring
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.alert_queue: List[Dict] = []

        # Statistics
        self.deployment_stats = {
            "deployments_orchestrated": 0,
            "successful_deployments": 0,
            "rollbacks_performed": 0,
            "adhd_optimizations_applied": 0,
            "cognitive_interruptions_prevented": 0,
            "break_points_utilized": 0
        }

    async def initialize(self) -> None:
        """Initialize the deployment orchestration coordinator."""
        try:
            await self._load_pipeline_definitions()
            await self._initialize_test_runners()
            await self._start_monitoring_services()
            logger.info("Deployment orchestration coordinator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize deployment coordinator: {e}")

    async def orchestrate_deployment(
        self,
        pipeline_id: str,
        git_branch: str = "main",
        adhd_mode: bool = True
    ) -> Optional[str]:
        """Orchestrate a complete deployment pipeline."""
        try:
            pipeline = self.pipelines.get(pipeline_id)
            if not pipeline:
                logger.error(f"Pipeline {pipeline_id} not found")
                return None

            # Create deployment instance
            deployment_instance_id = f"deploy_{uuid.uuid4().hex[:8]}"
            deployment_instance = self._create_deployment_instance(pipeline, git_branch)

            # Apply ADHD optimizations if requested
            if adhd_mode:
                deployment_instance = await self._apply_adhd_deployment_optimizations(deployment_instance)

            # Start deployment
            self.active_deployments[deployment_instance_id] = deployment_instance

            # Create monitoring task
            monitor_task = asyncio.create_task(
                self._monitor_deployment(deployment_instance_id, deployment_instance)
            )
            self.monitoring_tasks[deployment_instance_id] = monitor_task

            # Execute deployment pipeline
            success = await self._execute_deployment_pipeline(deployment_instance)

            self.deployment_stats["deployments_orchestrated"] += 1
            if success:
                self.deployment_stats["successful_deployments"] += 1

            logger.info(f"Deployment {deployment_instance_id} {'succeeded' if success else 'failed'}")
            return deployment_instance_id

        except Exception as e:
            logger.error(f"Deployment orchestration failed: {e}")
            return None

    async def run_automated_tests(
        self,
        test_types: List[TestType],
        target_branch: str = "main",
        adhd_friendly: bool = True
    ) -> Dict[TestType, Dict[str, Any]]:
        """Run automated tests with ADHD-optimized reporting."""
        try:
            test_results = {}

            for test_type in test_types:
                logger.info(f"🧪 Running {test_type.value} tests...")

                # Get test configuration
                test_config = self.test_runners.get(test_type, {})
                if not test_config:
                    logger.warning(f"No test runner configured for {test_type.value}")
                    continue

                # Execute tests
                result = await self._execute_test_suite(test_type, target_branch, test_config)

                # Apply ADHD-friendly formatting
                if adhd_friendly:
                    result = await self._format_test_results_adhd_friendly(result)

                test_results[test_type] = result

            return test_results

        except Exception as e:
            logger.error(f"Automated testing failed: {e}")
            return {}

    async def monitor_deployment_health(self, deployment_id: str) -> Dict[str, Any]:
        """Monitor health of active deployment."""
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                return {"error": "Deployment not found"}

            health_status = {
                "deployment_id": deployment_id,
                "pipeline_name": deployment.name,
                "current_stage": self._get_current_stage(deployment),
                "progress_percentage": self._calculate_progress(deployment),
                "estimated_completion": self._estimate_completion_time(deployment),
                "health_indicators": await self._get_health_indicators(deployment),
                "adhd_status": {
                    "cognitive_load": self._assess_deployment_cognitive_load(deployment),
                    "attention_required": self._check_attention_requirements(deployment),
                    "break_opportunity": self._identify_break_opportunities(deployment)
                }
            }

            return health_status

        except Exception as e:
            logger.error(f"Deployment health monitoring failed: {e}")
            return {"error": str(e)}

    async def suggest_deployment_improvements(self, deployment_id: str) -> List[str]:
        """Suggest improvements for deployment pipeline."""
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                return []

            suggestions = []

            # Analyze deployment performance
            performance_data = await self._analyze_deployment_performance(deployment)

            # Generate performance-based suggestions
            if performance_data.get("slow_stages"):
                suggestions.append("Parallelize slow deployment stages")

            if performance_data.get("high_failure_rate"):
                suggestions.append("Add more comprehensive pre-deployment checks")

            # Add ADHD-specific suggestions
            if deployment.gentle_notifications:
                suggestions.extend([
                    "Add visual progress indicators for better focus tracking",
                    "Create natural break points in long deployment stages",
                    "Implement gentle notification patterns for status updates"
                ])

            return suggestions

        except Exception as e:
            logger.error(f"Failed to suggest deployment improvements: {e}")
            return []

    # Private implementation methods

    async def _load_pipeline_definitions(self) -> None:
        """Load deployment pipeline definitions."""
        # Default dopemux pipeline
        dopemux_pipeline = DeploymentPipeline(
            pipeline_id="dopemux_mvp",
            name="Dopemux MVP Deployment",
            description="ADHD-optimized deployment pipeline for Dopemux",
            git_branch="main",
            target_environment="staging",
            tasks=[],  # Would be populated with actual tasks
            parallel_stages=[],
            critical_path=[],
            gentle_notifications=True,
            batch_alerts=True,
            visual_dashboard_url="http://localhost:3016/deployment-dashboard",
            break_points=["post_testing", "pre_production"],
            created_at=datetime.now(),
            estimated_duration=45.0,
            success_rate=0.85
        )

        self.pipelines["dopemux_mvp"] = dopemux_pipeline

    async def _initialize_test_runners(self) -> None:
        """Initialize test runners for different test types."""
        self.test_runners = {
            TestType.UNIT: {
                "command": "python -m pytest tests/unit/",
                "timeout": 10,
                "parallel": True
            },
            TestType.INTEGRATION: {
                "command": "python -m pytest tests/integration/",
                "timeout": 30,
                "parallel": False
            },
            TestType.E2E: {
                "command": "python -m pytest tests/e2e/",
                "timeout": 60,
                "parallel": False
            }
        }

    async def _start_monitoring_services(self) -> None:
        """Start background monitoring services."""
        # Start alert batching service
        asyncio.create_task(self._deployment_alert_batching_loop())

    def _create_deployment_instance(
        self, pipeline: DeploymentPipeline, git_branch: str
    ) -> DeploymentPipeline:
        """Create deployment instance from pipeline template."""
        # Deep copy pipeline with instance-specific data
        instance = DeploymentPipeline(
            pipeline_id=f"{pipeline.pipeline_id}_{uuid.uuid4().hex[:6]}",
            name=f"{pipeline.name} ({git_branch})",
            description=pipeline.description,
            git_branch=git_branch,
            target_environment=pipeline.target_environment,
            tasks=pipeline.tasks.copy(),
            parallel_stages=pipeline.parallel_stages.copy(),
            critical_path=pipeline.critical_path.copy(),
            gentle_notifications=pipeline.gentle_notifications,
            batch_alerts=pipeline.batch_alerts,
            visual_dashboard_url=pipeline.visual_dashboard_url,
            break_points=pipeline.break_points.copy(),
            created_at=datetime.now(),
            estimated_duration=pipeline.estimated_duration,
            success_rate=pipeline.success_rate
        )

        return instance

    async def _apply_adhd_deployment_optimizations(
        self, deployment: DeploymentPipeline
    ) -> DeploymentPipeline:
        """Apply ADHD-specific optimizations to deployment."""
        # Enable all ADHD features
        deployment.gentle_notifications = True
        deployment.batch_alerts = True

        # Add break points if long deployment
        if deployment.estimated_duration > 30:
            if "mid_deployment_break" not in deployment.break_points:
                deployment.break_points.append("mid_deployment_break")

        # Adjust task timeouts for ADHD considerations
        for task in deployment.tasks:
            if task.cognitive_impact > 0.7:
                task.timeout_minutes *= 1.5  # More time for high-cognitive tasks

        self.deployment_stats["adhd_optimizations_applied"] += 1
        return deployment

    async def _execute_deployment_pipeline(self, deployment: DeploymentPipeline) -> bool:
        """Execute the deployment pipeline with monitoring."""
        try:
            logger.info(f"🚀 Starting deployment: {deployment.name}")

            # Execute stages in order
            for task in deployment.tasks:
                success = await self._execute_deployment_task(task)
                if not success:
                    logger.error(f"❌ Deployment failed at task: {task.name}")
                    return False

                # Check for break points
                if task.task_id in deployment.break_points:
                    await self._handle_deployment_break_point(deployment, task)

            logger.info(f"✅ Deployment completed successfully: {deployment.name}")
            return True

        except Exception as e:
            logger.error(f"Deployment execution failed: {e}")
            return False

    async def _execute_deployment_task(self, task: DeploymentTask) -> bool:
        """Execute individual deployment task."""
        try:
            task.status = DeploymentStatus.RUNNING
            task.started_at = datetime.now()

            logger.info(f"⚡ Executing: {task.name}")

            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                task.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task.timeout_minutes * 60
                )

                if process.returncode == 0:
                    task.status = DeploymentStatus.SUCCESS
                    task.output_log.append(stdout.decode() if stdout else "")
                    return True
                else:
                    task.status = DeploymentStatus.FAILED
                    task.error_message = stderr.decode() if stderr else "Unknown error"
                    return False

            except asyncio.TimeoutError:
                process.kill()
                task.status = DeploymentStatus.FAILED
                task.error_message = f"Timeout after {task.timeout_minutes} minutes"
                return False

        except Exception as e:
            task.status = DeploymentStatus.FAILED
            task.error_message = str(e)
            return False

        finally:
            task.completed_at = datetime.now()

    async def _execute_test_suite(
        self, test_type: TestType, branch: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute specific test suite."""
        try:
            command = config["command"]
            timeout = config.get("timeout", 30)

            logger.info(f"🧪 Running {test_type.value} tests on {branch}")

            # Execute test command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout * 60
            )

            success = process.returncode == 0
            output = stdout.decode() if stdout else ""
            errors = stderr.decode() if stderr else ""

            return {
                "test_type": test_type.value,
                "success": success,
                "output": output,
                "errors": errors,
                "duration": timeout,  # Would track actual duration
                "timestamp": datetime.now().isoformat()
            }

        except asyncio.TimeoutError:
            return {
                "test_type": test_type.value,
                "success": False,
                "errors": f"Test suite timed out after {timeout} minutes",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "test_type": test_type.value,
                "success": False,
                "errors": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _format_test_results_adhd_friendly(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format test results in ADHD-friendly manner."""
        # Add visual indicators
        if result["success"]:
            result["visual_status"] = "✅ PASSED"
            result["cognitive_impact"] = "low"
        else:
            result["visual_status"] = "❌ FAILED"
            result["cognitive_impact"] = "high"

        # Simplify error messages
        if result.get("errors"):
            result["simple_error"] = await self._simplify_error_message(result["errors"])

        return result

    async def _simplify_error_message(self, error_text: str) -> str:
        """Simplify error messages for ADHD users."""
        # Extract key information from complex error messages
        lines = error_text.split('\n')

        # Look for common patterns
        for line in lines:
            if "FAILED" in line and "::" in line:
                return f"Test failed: {line.split('::')[-1].strip()}"
            elif "Error:" in line:
                return line.strip()
            elif "AssertionError" in line:
                return f"Assertion failed: {line.split('AssertionError:')[-1].strip()}"

        # Return first non-empty line if no patterns found
        for line in lines:
            if line.strip():
                return line.strip()[:100] + "..." if len(line) > 100 else line.strip()

        return "Unknown error occurred"

    def _get_current_stage(self, deployment: DeploymentPipeline) -> str:
        """Get current deployment stage."""
        # Find first non-completed task
        for task in deployment.tasks:
            if task.status in [DeploymentStatus.PENDING, DeploymentStatus.RUNNING]:
                return task.stage.value

        return "completed"

    def _calculate_progress(self, deployment: DeploymentPipeline) -> float:
        """Calculate deployment progress percentage."""
        if not deployment.tasks:
            return 0.0

        completed_tasks = sum(1 for task in deployment.tasks
                            if task.status == DeploymentStatus.SUCCESS)
        return (completed_tasks / len(deployment.tasks)) * 100

    def _estimate_completion_time(self, deployment: DeploymentPipeline) -> Optional[datetime]:
        """Estimate deployment completion time."""
        remaining_tasks = [task for task in deployment.tasks
                         if task.status not in [DeploymentStatus.SUCCESS, DeploymentStatus.FAILED]]

        if not remaining_tasks:
            return datetime.now()  # Already complete

        remaining_time = sum(task.timeout_minutes for task in remaining_tasks)
        return datetime.now() + timedelta(minutes=remaining_time)

    async def _get_health_indicators(self, deployment: DeploymentPipeline) -> List[str]:
        """Get deployment health indicators."""
        indicators = []

        # Check task success rate
        completed_tasks = [t for t in deployment.tasks if t.status != DeploymentStatus.PENDING]
        if completed_tasks:
            success_rate = sum(1 for t in completed_tasks if t.status == DeploymentStatus.SUCCESS) / len(completed_tasks)
            if success_rate > 0.8:
                indicators.append("✅ High success rate")
            elif success_rate < 0.5:
                indicators.append("⚠️ Low success rate")

        # Check timing
        current_time = datetime.now()
        if deployment.created_at:
            elapsed = (current_time - deployment.created_at).total_seconds() / 60
            if elapsed > deployment.estimated_duration * 1.5:
                indicators.append("⏰ Running over estimated time")

        return indicators

    def _assess_deployment_cognitive_load(self, deployment: DeploymentPipeline) -> float:
        """Assess cognitive load of current deployment state."""
        if not deployment.tasks:
            return 0.0

        running_tasks = [t for t in deployment.tasks if t.status == DeploymentStatus.RUNNING]
        high_cognitive_tasks = [t for t in running_tasks if t.cognitive_impact > 0.6]

        return min(1.0, len(high_cognitive_tasks) * 0.3)

    def _check_attention_requirements(self, deployment: DeploymentPipeline) -> bool:
        """Check if deployment currently requires active attention."""
        running_tasks = [t for t in deployment.tasks if t.status == DeploymentStatus.RUNNING]
        return any(t.attention_required for t in running_tasks)

    def _identify_break_opportunities(self, deployment: DeploymentPipeline) -> List[str]:
        """Identify current break opportunities."""
        current_stage = self._get_current_stage(deployment)

        opportunities = []
        if current_stage in deployment.break_points:
            opportunities.append(f"Natural break point available at {current_stage}")

        return opportunities

    async def _handle_deployment_break_point(
        self, deployment: DeploymentPipeline, completed_task: DeploymentTask
    ) -> None:
        """Handle reaching a deployment break point."""
        if self.break_enforcement and deployment.estimated_duration > 30:
            logger.info(f"🛑 Break point reached after {completed_task.name}")
            logger.info("💡 Consider taking a 5-10 minute break before continuing")

            self.deployment_stats["break_points_utilized"] += 1

            # Wait for user confirmation to continue (in real implementation)
            await asyncio.sleep(1)  # Placeholder

    async def _monitor_deployment(self, deployment_id: str, deployment: DeploymentPipeline) -> None:
        """Monitor deployment progress and health."""
        while deployment_id in self.active_deployments:
            try:
                health = await self.monitor_deployment_health(deployment_id)

                # Check for issues that need attention
                if health.get("adhd_status", {}).get("attention_required"):
                    await self._queue_attention_alert(deployment_id, health)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Deployment monitoring error: {e}")
                await asyncio.sleep(60)

    async def _queue_attention_alert(self, deployment_id: str, health: Dict[str, Any]) -> None:
        """Queue attention alert for deployment."""
        alert = {
            "type": "deployment_attention",
            "deployment_id": deployment_id,
            "urgency": "medium",
            "message": "Deployment needs attention",
            "timestamp": datetime.now()
        }

        self.alert_queue.append(alert)

    async def _deployment_alert_batching_loop(self) -> None:
        """Batch deployment alerts to reduce interruptions."""
        while True:
            try:
                if self.alert_queue:
                    await self._process_deployment_alerts()

                await asyncio.sleep(120)  # Check every 2 minutes

            except Exception as e:
                logger.error(f"Alert batching error: {e}")
                await asyncio.sleep(300)

    async def _process_deployment_alerts(self) -> None:
        """Process batched deployment alerts."""
        if not self.alert_queue:
            return

        # Group by urgency
        urgent = [a for a in self.alert_queue if a.get("urgency") == "high"]
        normal = [a for a in self.alert_queue if a.get("urgency") != "high"]

        if urgent:
            for alert in urgent:
                logger.warning(f"🚨 {alert['message']}")

        if normal and len(normal) > 1:
            logger.info(f"📊 {len(normal)} deployment updates available")
        elif normal:
            logger.info(f"📊 {normal[0]['message']}")

        self.alert_queue.clear()
        self.deployment_stats["cognitive_interruptions_prevented"] += len(normal)

    async def _analyze_deployment_performance(self, deployment: DeploymentPipeline) -> Dict[str, Any]:
        """Analyze deployment performance for improvement suggestions."""
        # Implementation would analyze performance metrics
        return {
            "slow_stages": [],
            "high_failure_rate": False,
            "optimization_opportunities": []
        }