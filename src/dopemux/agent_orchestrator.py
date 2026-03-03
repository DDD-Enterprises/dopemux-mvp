"""Agent orchestration system for Dopemux.

Centralized system for managing and coordinating AI agents with LiteLLM integration.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .litellm_manager import (
    LiteLLMProcessInfo,
    get_litellm_manager,
)

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class AgentType(Enum):
    """Type of agent."""
    TASK_DECOMPOSER = "task_decomposer"
    TOOL_ORCHESTRATOR = "tool_orchestrator"
    MEMORY_AGENT = "memory_agent"
    COGNITIVE_GUARDIAN = "cognitive_guardian"
    WORKFLOW_COORDINATOR = "workflow_coordinator"
    CUSTOM = "custom"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    litellm_instance: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    memory_enabled: bool = False
    max_retries: int = 3
    timeout: int = 300
    environment: Optional[Dict[str, str]] = None


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_id: str
    status: AgentStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = ""


@dataclass
class AgentTask:
    """Task to be executed by an agent."""
    task_id: str
    agent_id: str
    input_data: Any
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3


class AgentError(RuntimeError):
    """Raised when agent operations fail."""


class AgentManager:
    """Centralized manager for AI agents with LiteLLM integration."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._agents: Dict[str, AgentConfig] = {}
        self._active_tasks: Dict[str, AgentTask] = {}
        self._task_queue: List[AgentTask] = []
        self._litellm_manager = get_litellm_manager(self.project_root)
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
    def start(self) -> None:
        """Start the agent manager and its worker thread."""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._worker_thread = threading.Thread(
                target=self._process_tasks,
                daemon=True,
                name="AgentOrchestratorWorker"
            )
            self._worker_thread.start()
            
            # Start LiteLLM health monitoring
            self._litellm_manager.start()
            
            logger.info("🚀 Agent manager started")
    
    def stop(self) -> None:
        """Stop the agent manager and cleanup."""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # Stop LiteLLM monitoring
            self._litellm_manager.stop()
            
            # Wait for worker thread to finish
            if self._worker_thread:
                self._worker_thread.join(timeout=5.0)
            
            logger.info("⏹️  Agent manager stopped")
    
    def register_agent(self, config: AgentConfig) -> None:
        """Register a new agent with the manager."""
        with self._lock:
            if config.agent_id in self._agents:
                raise AgentError(f"Agent {config.agent_id} already registered")
            
            self._agents[config.agent_id] = config
            logger.info(f"🔧 Registered agent: {config.name} ({config.agent_id})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        with self._lock:
            if agent_id not in self._agents:
                raise AgentError(f"Agent {agent_id} not found")
            
            del self._agents[agent_id]
            logger.info(f"🗑️  Unregistered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration."""
        with self._lock:
            return self._agents.get(agent_id)
    
    def list_agents(self) -> List[AgentConfig]:
        """List all registered agents."""
        with self._lock:
            return list(self._agents.values())
    
    def submit_task(self, task: AgentTask) -> str:
        """Submit a task to be executed by an agent."""
        with self._lock:
            if task.agent_id not in self._agents:
                raise AgentError(f"Agent {task.agent_id} not found")
            
            task.task_id = str(uuid.uuid4())
            self._task_queue.append(task)
            self._active_tasks[task.task_id] = task
            
            logger.info(f"📥 Task submitted: {task.task_id} for agent {task.agent_id}")
            return task.task_id
    
    def get_task_status(self, task_id: str) -> Optional[AgentStatus]:
        """Get the status of a task."""
        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task:
                return None
            
            # Check if task is completed (no longer in active tasks)
            if task_id not in self._active_tasks:
                return AgentStatus.COMPLETED
            
            # For running tasks, return RUNNING status
            return AgentStatus.RUNNING
    
    def get_task_result(self, task_id: str) -> Optional[AgentResult]:
        """Get the result of a completed task."""
        # In a real implementation, this would retrieve from a results store
        # For now, return None as tasks are processed synchronously in the worker
        return None
    
    def _process_tasks(self) -> None:
        """Main task processing loop."""
        while self._running:
            try:
                self._process_next_task()
            except Exception as e:
                logger.error(f"Error processing task: {e}")
            
            # Small delay to prevent tight looping
            time.sleep(0.1)
    
    def _process_next_task(self) -> None:
        """Process the next task in the queue."""
        with self._lock:
            if not self._task_queue:
                return
            
            # Get the highest priority task
            task = min(self._task_queue, key=lambda t: t.priority)
            self._task_queue.remove(task)
        
        try:
            logger.info(f"🔄 Processing task: {task.task_id}")
            
            # Get agent configuration
            agent_config = self.get_agent(task.agent_id)
            if not agent_config:
                raise AgentError(f"Agent {task.agent_id} not found")
            
            # Execute the task
            result = self._execute_agent_task(agent_config, task)
            
            # Clean up active task
            with self._lock:
                if task.task_id in self._active_tasks:
                    del self._active_tasks[task.task_id]
            
            logger.info(f"✅ Task completed: {task.task_id} with status {result.status}")
            
        except Exception as e:
            logger.error(f"❌ Task failed: {task.task_id} - {e}")
            
            # Handle retries
            with self._lock:
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    self._task_queue.append(task)
                    logger.info(f"🔄 Retrying task: {task.task_id} (attempt {task.retry_count})")
                else:
                    if task.task_id in self._active_tasks:
                        del self._active_tasks[task.task_id]
                    logger.error(f"💥 Task failed permanently: {task.task_id}")
    
    def _execute_agent_task(self, agent_config: AgentConfig, task: AgentTask) -> AgentResult:
        """Execute a task using the specified agent."""
        start_time = time.time()
        
        try:
            # Ensure LiteLLM instance is available if needed
            if agent_config.litellm_instance:
                self._ensure_litellm_instance(agent_config.litellm_instance)
            
            # Execute the appropriate agent type
            if agent_config.agent_type == AgentType.TASK_DECOMPOSER:
                output = self._execute_task_decomposer(agent_config, task.input_data)
            elif agent_config.agent_type == AgentType.TOOL_ORCHESTRATOR:
                output = self._execute_tool_orchestrator(agent_config, task.input_data)
            elif agent_config.agent_type == AgentType.MEMORY_AGENT:
                output = self._execute_memory_agent(agent_config, task.input_data)
            elif agent_config.agent_type == AgentType.COGNITIVE_GUARDIAN:
                output = self._execute_cognitive_guardian(agent_config, task.input_data)
            elif agent_config.agent_type == AgentType.WORKFLOW_COORDINATOR:
                output = self._execute_workflow_coordinator(agent_config, task.input_data)
            elif agent_config.agent_type == AgentType.CUSTOM:
                output = self._execute_custom_agent(agent_config, task.input_data)
            else:
                raise AgentError(f"Unsupported agent type: {agent_config.agent_type}")
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_id=agent_config.agent_id,
                status=AgentStatus.COMPLETED,
                output=output,
                error=None,
                execution_time=execution_time,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_id=agent_config.agent_id,
                status=AgentStatus.ERROR,
                output=None,
                error=str(e),
                execution_time=execution_time,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
    
    def _ensure_litellm_instance(self, instance_id: str) -> LiteLLMProcessInfo:
        """Ensure a LiteLLM instance is running."""
        instance = self._litellm_manager.get_instance(instance_id)
        
        if instance:
            return instance
        
        # If not running, start a default instance
        # In a real implementation, this would use a proper configuration
        config_data = {
            "model_list": [
                {
                    "model_name": "default-model",
                    "litellm_params": {
                        "model": "gpt-4",
                        "api_key": "os.environ/OPENAI_API_KEY",
                    },
                }
            ],
            "litellm_settings": {
                "timeout": 90,
                "max_retries": 2,
            },
        }
        
        # Find an available port (simple approach for demo)
        port = 4000
        while self._litellm_manager._is_port_in_use(port):
            port += 1
        
        return self._litellm_manager.start_instance(
            instance_id=instance_id,
            port=port,
            config_data=config_data,
            db_enabled=False,
        )
    
    def _execute_task_decomposer(self, agent_config: AgentConfig, input_data: Any) -> Any:
        """Execute task decomposer agent."""
        logger.info(f"🧩 Executing task decomposer: {agent_config.name}")
        
        # In a real implementation, this would call the actual task decomposer
        # For now, return a mock response
        return {
            "original_task": input_data,
            "subtasks": [
                {"id": 1, "description": f"Subtask 1 for {input_data}"},
                {"id": 2, "description": f"Subtask 2 for {input_data}"},
            ],
            "agent": agent_config.name,
            "status": "decomposed"
        }
    
    def _execute_tool_orchestrator(self, agent_config: AgentConfig, input_data: Any) -> Any:
        """Execute tool orchestrator agent."""
        logger.info(f"🛠️  Executing tool orchestrator: {agent_config.name}")
        
        # Mock response
        return {
            "task": input_data,
            "tools_used": agent_config.tools or [],
            "result": f"Processed {input_data} with tools",
            "agent": agent_config.name,
            "status": "completed"
        }
    
    def _execute_memory_agent(self, agent_config: AgentConfig, input_data: Any) -> Any:
        """Execute memory agent."""
        logger.info(f"🧠 Executing memory agent: {agent_config.name}")
        
        # Mock response
        return {
            "input": input_data,
            "memory_updated": True,
            "context": f"Memory context for {input_data}",
            "agent": agent_config.name,
            "status": "memory_updated"
        }
    
    def _execute_cognitive_guardian(self, agent_config: AgentConfig, input_data: Any) -> Any:
        """Execute cognitive guardian agent."""
        logger.info(f"🛡️  Executing cognitive guardian: {agent_config.name}")
        
        # Mock response
        return {
            "input": input_data,
            "safety_check": "passed",
            "guardian_action": "approved",
            "agent": agent_config.name,
            "status": "guarded"
        }
    
    def _execute_workflow_coordinator(self, agent_config: AgentConfig, input_data: Any) -> Any:
        """Execute workflow coordinator agent."""
        logger.info(f"🔄 Executing workflow coordinator: {agent_config.name}")
        
        # Mock response
        return {
            "workflow": input_data,
            "steps": [
                {"step": 1, "action": "start", "status": "completed"},
                {"step": 2, "action": "process", "status": "completed"},
            ],
            "result": f"Workflow {input_data} coordinated",
            "agent": agent_config.name,
            "status": "coordinated"
        }
    
    def _execute_custom_agent(self, agent_config: AgentConfig, input_data: Any) -> Any:
        """Execute custom agent."""
        logger.info(f"🎛️  Executing custom agent: {agent_config.name}")
        
        # Mock response
        return {
            "input": input_data,
            "custom_processing": True,
            "result": f"Custom processing for {input_data}",
            "agent": agent_config.name,
            "status": "processed"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        with self._lock:
            return {
                "agents_registered": len(self._agents),
                "tasks_queued": len(self._task_queue),
                "tasks_active": len(self._active_tasks),
                "litellm_instances": len(self._litellm_manager.get_all_instances()),
                "system_healthy": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed system status."""
        status = self.get_system_status()
        
        # Add agent details
        agents_info = []
        for agent_id, config in self._agents.items():
            agents_info.append({
                "agent_id": agent_id,
                "name": config.name,
                "type": config.agent_type.value,
                "description": config.description,
                "status": "registered"
            })
        
        # Add LiteLLM status
        litellm_status = self._litellm_manager.get_health_status()
        
        return {
            **status,
            "agents": agents_info,
            "litellm_instances": litellm_status,
            "detailed": True
        }


class AgentWorkflow:
    """Workflow coordination for multi-agent tasks."""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.workflow_id = str(uuid.uuid4())
        self.steps: List[Dict[str, Any]] = []
        self.status = AgentStatus.IDLE
        
    def add_step(self, agent_id: str, input_data: Any, priority: int = 1) -> None:
        """Add a step to the workflow."""
        self.steps.append({
            "agent_id": agent_id,
            "input_data": input_data,
            "priority": priority,
            "status": AgentStatus.IDLE.value,
            "result": None,
            "error": None
        })
    
    def execute(self) -> Dict[str, Any]:
        """Execute the workflow."""
        self.status = AgentStatus.RUNNING
        results = []
        
        for i, step in enumerate(self.steps):
            try:
                # Create and submit task
                task = AgentTask(
                    task_id=str(uuid.uuid4()),
                    agent_id=step["agent_id"],
                    input_data=step["input_data"],
                    priority=step["priority"]
                )
                
                task_id = self.agent_manager.submit_task(task)
                
                # Wait for task completion (simplified for demo)
                time.sleep(1)  # Simulate processing time
                
                # Get result (in real implementation, this would be async)
                result = AgentResult(
                    agent_id=step["agent_id"],
                    status=AgentStatus.COMPLETED,
                    output=f"Processed step {i+1}: {step['input_data']}",
                    execution_time=0.5
                )
                
                step["status"] = AgentStatus.COMPLETED.value
                step["result"] = result.output
                results.append(result)
                
            except Exception as e:
                step["status"] = AgentStatus.ERROR.value
                step["error"] = str(e)
                self.status = AgentStatus.ERROR
                return {
                    "workflow_id": self.workflow_id,
                    "status": AgentStatus.ERROR.value,
                    "error": str(e),
                    "completed_steps": i,
                    "total_steps": len(self.steps)
                }
        
        self.status = AgentStatus.COMPLETED
        return {
            "workflow_id": self.workflow_id,
            "status": AgentStatus.COMPLETED.value,
            "results": results,
            "steps": self.steps
        }


# Global singleton instance
_agent_manager: Optional[AgentManager] = None


def get_agent_manager(project_root: Optional[Path] = None) -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    
    if _agent_manager is None:
        _agent_manager = AgentManager(project_root)
    
    return _agent_manager


class AgentCLI:
    """Command-line interface for agent management."""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
    
    def register_agent_from_config(self, config_path: Path) -> None:
        """Register an agent from a YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            agent_config = AgentConfig(
                agent_id=config_data['agent_id'],
                agent_type=AgentType(config_data['agent_type']),
                name=config_data['name'],
                description=config_data.get('description', ''),
                litellm_instance=config_data.get('litellm_instance'),
                model=config_data.get('model'),
                tools=config_data.get('tools'),
                memory_enabled=config_data.get('memory_enabled', False),
                max_retries=config_data.get('max_retries', 3),
                timeout=config_data.get('timeout', 300),
                environment=config_data.get('environment')
            )
            
            self.agent_manager.register_agent(agent_config)
            print(f"✅ Agent registered: {agent_config.name}")
            
        except Exception as e:
            print(f"❌ Error registering agent: {e}")
            raise
    
    def list_agents(self) -> None:
        """List all registered agents."""
        agents = self.agent_manager.list_agents()
        
        if not agents:
            print("No agents registered.")
            return
        
        print("Registered Agents:")
        print("-" * 50)
        for agent in agents:
            print(f"ID: {agent.agent_id}")
            print(f"Name: {agent.name}")
            print(f"Type: {agent.agent_type.value}")
            print(f"Description: {agent.description}")
            print(f"LiteLLM Instance: {agent.litellm_instance or 'None'}")
            print("-" * 50)
    
    def submit_task_interactive(self) -> None:
        """Interactively submit a task."""
        agents = self.agent_manager.list_agents()
        
        if not agents:
            print("No agents available. Register an agent first.")
            return
        
        print("Available Agents:")
        for i, agent in enumerate(agents):
            print(f"{i+1}. {agent.name} ({agent.agent_id}) - {agent.agent_type.value}")
        
        try:
            choice = int(input("Select agent number: ")) - 1
            if choice < 0 or choice >= len(agents):
                print("Invalid selection.")
                return
            
            selected_agent = agents[choice]
            input_data = input("Enter task input: ")
            priority = int(input("Priority (1-5, 1=highest): ") or "3")
            
            task = AgentTask(
                task_id="",  # Will be generated
                agent_id=selected_agent.agent_id,
                input_data=input_data,
                priority=priority
            )
            
            task_id = self.agent_manager.submit_task(task)
            print(f"✅ Task submitted: {task_id}")
            
        except Exception as e:
            print(f"❌ Error submitting task: {e}")
    
    def show_status(self) -> None:
        """Show system status."""
        status = self.agent_manager.get_detailed_status()
        
        print("Agent System Status:")
        print("=" * 50)
        print(f"Agents Registered: {status['agents_registered']}")
        print(f"Tasks Queued: {status['tasks_queued']}")
        print(f"Tasks Active: {status['tasks_active']}")
        print(f"LiteLLM Instances: {status['litellm_instances']}")
        print(f"System Healthy: {status['system_healthy']}")
        print(f"Timestamp: {status['timestamp']}")
        
        if status['agents']:
            print("\nRegistered Agents:")
            for agent in status['agents']:
                print(f"  - {agent['name']} ({agent['agent_id']}) [{agent['type']}]")
        
        if status['litellm_instances']:
            print("\nLiteLLM Instances:")
            for instance_id, instance_status in status['litellm_instances'].items():
                print(f"  - {instance_id}: port {instance_status['port']}, "
                      f"healthy={instance_status['healthy']}")


def create_sample_agent_configs() -> List[Dict[str, Any]]:
    """Create sample agent configurations for testing."""
    return [
        {
            "agent_id": "task-decomposer-001",
            "agent_type": "task_decomposer",
            "name": "Task Decomposer",
            "description": "Breaks down complex tasks into subtasks",
            "litellm_instance": "main",
            "model": "gpt-4",
            "max_retries": 3,
            "timeout": 300
        },
        {
            "agent_id": "tool-orchestrator-001",
            "agent_type": "tool_orchestrator",
            "name": "Tool Orchestrator",
            "description": "Coordinates tool usage for tasks",
            "litellm_instance": "main",
            "tools": ["search", "code_analysis", "documentation"],
            "max_retries": 2,
            "timeout": 240
        },
        {
            "agent_id": "memory-agent-001",
            "agent_type": "memory_agent",
            "name": "Memory Agent",
            "description": "Manages context and memory for tasks",
            "litellm_instance": "main",
            "memory_enabled": True,
            "max_retries": 2,
            "timeout": 180
        },
        {
            "agent_id": "cognitive-guardian-001",
            "agent_type": "cognitive_guardian",
            "name": "Cognitive Guardian",
            "description": "Ensures task safety and compliance",
            "litellm_instance": "main",
            "max_retries": 1,
            "timeout": 120
        },
        {
            "agent_id": "workflow-coordinator-001",
            "agent_type": "workflow_coordinator",
            "name": "Workflow Coordinator",
            "description": "Coordinates multi-agent workflows",
            "litellm_instance": "main",
            "max_retries": 2,
            "timeout": 600
        }
    ]


# Utility functions for common workflows

def setup_default_agents(agent_manager: AgentManager) -> None:
    """Set up default agents for common workflows."""
    configs = create_sample_agent_configs()
    
    for config_data in configs:
        try:
            agent_config = AgentConfig(
                agent_id=config_data['agent_id'],
                agent_type=AgentType(config_data['agent_type']),
                name=config_data['name'],
                description=config_data['description'],
                litellm_instance=config_data.get('litellm_instance'),
                model=config_data.get('model'),
                tools=config_data.get('tools'),
                memory_enabled=config_data.get('memory_enabled', False),
                max_retries=config_data.get('max_retries', 3),
                timeout=config_data.get('timeout', 300)
            )
            
            agent_manager.register_agent(agent_config)
            logger.info(f"🔧 Registered default agent: {agent_config.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to register agent {config_data['name']}: {e}")


def create_task_decomposition_workflow(agent_manager: AgentManager, task_input: str) -> AgentWorkflow:
    """Create a workflow for task decomposition."""
    workflow = AgentWorkflow(agent_manager)
    
    # Step 1: Cognitive Guardian - Safety check
    workflow.add_step("cognitive-guardian-001", {
        "task": task_input,
        "check_type": "safety"
    })
    
    # Step 2: Task Decomposer - Break down task
    workflow.add_step("task-decomposer-001", {
        "task": task_input,
        "context": "decomposition"
    })
    
    # Step 3: Memory Agent - Store context
    workflow.add_step("memory-agent-001", {
        "task": task_input,
        "action": "store",
        "context_type": "task_decomposition"
    })
    
    return workflow


def create_tool_execution_workflow(agent_manager: AgentManager, task_input: str, tools: List[str]) -> AgentWorkflow:
    """Create a workflow for tool execution."""
    workflow = AgentWorkflow(agent_manager)
    
    # Step 1: Tool Orchestrator - Execute tools
    workflow.add_step("tool-orchestrator-001", {
        "task": task_input,
        "tools": tools,
        "action": "execute"
    })
    
    # Step 2: Memory Agent - Store results
    workflow.add_step("memory-agent-001", {
        "task": task_input,
        "action": "store",
        "context_type": "tool_results",
        "tools_used": tools
    })
    
    return workflow


def create_comprehensive_workflow(agent_manager: AgentManager, task_input: str) -> AgentWorkflow:
    """Create a comprehensive multi-agent workflow."""
    workflow = AgentWorkflow(agent_manager)
    
    # Step 1: Cognitive Guardian - Initial safety check
    workflow.add_step("cognitive-guardian-001", {
        "task": task_input,
        "check_type": "initial_safety"
    }, priority=1)
    
    # Step 2: Task Decomposer - Break down complex task
    workflow.add_step("task-decomposer-001", {
        "task": task_input,
        "complexity": "high",
        "context": "full_decomposition"
    }, priority=1)
    
    # Step 3: Tool Orchestrator - Execute required tools
    workflow.add_step("tool-orchestrator-001", {
        "task": task_input,
        "tools": ["search", "code_analysis"],
        "action": "comprehensive_execution"
    }, priority=2)
    
    # Step 4: Memory Agent - Store comprehensive context
    workflow.add_step("memory-agent-001", {
        "task": task_input,
        "action": "comprehensive_store",
        "context_type": "full_workflow",
        "include_results": True
    }, priority=2)
    
    # Step 5: Workflow Coordinator - Final coordination
    workflow.add_step("workflow-coordinator-001", {
        "task": task_input,
        "workflow_type": "comprehensive",
        "final_check": True
    }, priority=1)
    
    # Step 6: Cognitive Guardian - Final safety check
    workflow.add_step("cognitive-guardian-001", {
        "task": task_input,
        "check_type": "final_safety",
        "include_results": True
    }, priority=1)
    
    return workflow
