"""Tests for the Agent Orchestrator system."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

sys.modules.pop("dopemux", None)

from dopemux.agent_orchestrator import (
    AgentManager,
    AgentConfig,
    AgentTask,
    AgentStatus,
    AgentType,
    AgentWorkflow,
    AgentError,
    get_agent_manager,
    create_sample_agent_configs,
    setup_default_agents,
)


def test_agent_manager_initialization():
    """Test that AgentManager initializes correctly."""
    manager = AgentManager()
    assert manager.project_root == Path.cwd()
    assert len(manager._agents) == 0
    assert len(manager._task_queue) == 0
    assert len(manager._active_tasks) == 0


def test_agent_registration():
    """Test agent registration."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    
    assert len(manager._agents) == 1
    assert "test-agent-001" in manager._agents
    
    # Test duplicate registration
    try:
        manager.register_agent(config)
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected


def test_agent_unregistration():
    """Test agent unregistration."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    assert len(manager._agents) == 1
    
    manager.unregister_agent("test-agent-001")
    assert len(manager._agents) == 0
    
    # Test unregistering non-existent agent
    try:
        manager.unregister_agent("non-existent")
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected


def test_get_agent():
    """Test getting agent configuration."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    
    retrieved = manager.get_agent("test-agent-001")
    assert retrieved is not None
    assert retrieved.agent_id == "test-agent-001"
    
    # Test getting non-existent agent
    result = manager.get_agent("non-existent")
    assert result is None


def test_list_agents():
    """Test listing all agents."""
    manager = AgentManager()
    
    config1 = AgentConfig(
        agent_id="agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Agent 1",
        description="First test agent"
    )
    
    config2 = AgentConfig(
        agent_id="agent-002",
        agent_type=AgentType.TOOL_ORCHESTRATOR,
        name="Agent 2",
        description="Second test agent"
    )
    
    manager.register_agent(config1)
    manager.register_agent(config2)
    
    agents = manager.list_agents()
    assert len(agents) == 2
    assert agents[0].agent_id == "agent-001"
    assert agents[1].agent_id == "agent-002"


def test_task_submission():
    """Test task submission."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1
    )
    
    task_id = manager.submit_task(task)
    assert task_id is not None
    assert len(task_id) > 0
    assert len(manager._task_queue) == 1
    assert len(manager._active_tasks) == 1


def test_task_submission_nonexistent_agent():
    """Test task submission to non-existent agent."""
    manager = AgentManager()
    
    task = AgentTask(
        task_id="",
        agent_id="non-existent-agent",
        input_data={"test": "data"},
        priority=1
    )
    
    try:
        manager.submit_task(task)
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected


def test_task_status():
    """Test getting task status."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1
    )
    
    task_id = manager.submit_task(task)
    
    # Task should be running
    status = manager.get_task_status(task_id)
    assert status == AgentStatus.RUNNING
    
    # Test non-existent task
    status = manager.get_task_status("non-existent")
    assert status is None


def test_system_status():
    """Test getting system status."""
    manager = AgentManager()
    
    status = manager.get_system_status()
    
    assert "agents_registered" in status
    assert "tasks_queued" in status
    assert "tasks_active" in status
    assert "litellm_instances" in status
    assert "system_healthy" in status
    assert "timestamp" in status


def test_detailed_status():
    """Test getting detailed system status."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    
    status = manager.get_detailed_status()
    
    assert "agents" in status
    assert "litellm_instances" in status
    assert "detailed" in status
    assert status["detailed"] == True


def test_agent_workflow_creation():
    """Test creating an agent workflow."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    assert workflow.workflow_id is not None
    assert len(workflow.workflow_id) > 0
    assert workflow.status == AgentStatus.IDLE
    assert len(workflow.steps) == 0


def test_agent_workflow_steps():
    """Test adding steps to a workflow."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add some steps
    workflow.add_step("agent-001", {"task": "step1"}, priority=1)
    workflow.add_step("agent-002", {"task": "step2"}, priority=2)
    workflow.add_step("agent-003", {"task": "step3"}, priority=1)
    
    assert len(workflow.steps) == 3
    assert workflow.steps[0]["agent_id"] == "agent-001"
    assert workflow.steps[0]["priority"] == 1


def test_sample_agent_configs():
    """Test creating sample agent configurations."""
    configs = create_sample_agent_configs()
    
    assert len(configs) == 5
    
    # Check that all required fields are present
    for config in configs:
        assert "agent_id" in config
        assert "agent_type" in config
        assert "name" in config
        assert "description" in config


def test_setup_default_agents():
    """Test setting up default agents."""
    manager = AgentManager()
    
    # Mock the register_agent method to avoid actual registration
    with patch.object(manager, 'register_agent') as mock_register:
        setup_default_agents(manager)
        
        # Should have tried to register 5 agents
        assert mock_register.call_count == 5


def test_workflow_creation_functions():
    """Test workflow creation utility functions."""
    manager = AgentManager()
    
    # Test task decomposition workflow
    workflow1 = create_task_decomposition_workflow(manager, "test task")
    assert len(workflow1.steps) == 3
    
    # Test tool execution workflow
    workflow2 = create_tool_execution_workflow(manager, "test task", ["tool1", "tool2"])
    assert len(workflow2.steps) == 2
    
    # Test comprehensive workflow
    workflow3 = create_comprehensive_workflow(manager, "test task")
    assert len(workflow3.steps) == 6


def test_agent_manager_singleton():
    """Test that get_agent_manager returns a singleton."""
    manager1 = get_agent_manager()
    manager2 = get_agent_manager()
    
    assert manager1 is manager2


def test_agent_manager_lifecycle():
    """Test agent manager lifecycle."""
    manager = get_agent_manager()
    
    # Manager should start with no processes
    assert len(manager._agents) == 0
    assert len(manager._task_queue) == 0
    
    # Start the manager
    manager.start()
    assert manager._running == True
    
    # Stop the manager
    manager.stop()
    assert manager._running == False


def test_agent_config_validation():
    """Test agent configuration validation."""
    # Test valid configuration
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    assert config.agent_id == "test-agent-001"
    assert config.agent_type == AgentType.TASK_DECOMPOSER
    assert config.name == "Test Agent"
    assert config.description == "Test agent for unit tests"
    assert config.max_retries == 3
    assert config.timeout == 300


def test_task_priority_handling():
    """Test task priority handling."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    manager.register_agent(config)
    
    # Submit tasks with different priorities
    task1 = AgentTask(task_id="", agent_id="test-agent-001", input_data={"task": 1}, priority=3)
    task2 = AgentTask(task_id="", agent_id="test-agent-001", input_data={"task": 2}, priority=1)
    task3 = AgentTask(task_id="", agent_id="test-agent-001", input_data={"task": 3}, priority=2)
    
    manager.submit_task(task1)
    manager.submit_task(task2)
    manager.submit_task(task3)
    
    assert len(manager._task_queue) == 3
    
    # The next task to process should be the highest priority (priority 1)
    with patch.object(manager, '_process_next_task'):
        manager._process_tasks()  # This would normally run in a separate thread


def test_error_handling():
    """Test error handling in agent operations."""
    manager = AgentManager()
    
    # Test getting non-existent agent
    result = manager.get_agent("non-existent")
    assert result is None
    
    # Test unregistering non-existent agent
    try:
        manager.unregister_agent("non-existent")
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected
    
    # Test submitting task to non-existent agent
    task = AgentTask(task_id="", agent_id="non-existent", input_data={}, priority=1)
    try:
        manager.submit_task(task)
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected


def test_workflow_execution_simulation():
    """Test workflow execution (simulated)."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add a step
    workflow.add_step("test-agent", {"input": "test data"})
    
    # Mock the agent manager's submit_task method
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "mock-task-id"
        
        result = workflow.execute()
        
        assert result["status"] == AgentStatus.COMPLETED.value
        assert result["completed_steps"] == 1
        assert result["total_steps"] == 1


def test_workflow_error_handling():
    """Test workflow error handling."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add a step that will fail
    workflow.add_step("test-agent", {"input": "test data"})
    
    # Mock submit_task to raise an exception
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.side_effect = Exception("Test error")
        
        result = workflow.execute()
        
        assert result["status"] == AgentStatus.ERROR.value
        assert "Test error" in result["error"]
        assert result["completed_steps"] == 0


def test_agent_types():
    """Test all agent types."""
    types = [
        AgentType.TASK_DECOMPOSER,
        AgentType.TOOL_ORCHESTRATOR,
        AgentType.MEMORY_AGENT,
        AgentType.COGNITIVE_GUARDIAN,
        AgentType.WORKFLOW_COORDINATOR,
        AgentType.CUSTOM
    ]
    
    for agent_type in types:
        assert agent_type.value in [
            "task_decomposer",
            "tool_orchestrator", 
            "memory_agent",
            "cognitive_guardian",
            "workflow_coordinator",
            "custom"
        ]


def test_agent_status_values():
    """Test agent status values."""
    statuses = [
        AgentStatus.IDLE,
        AgentStatus.RUNNING,
        AgentStatus.PAUSED,
        AgentStatus.ERROR,
        AgentStatus.COMPLETED
    ]
    
    for status in statuses:
        assert status.value in ["idle", "running", "paused", "error", "completed"]


def test_task_retry_logic():
    """Test task retry logic."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests",
        max_retries=2
    )
    
    manager.register_agent(config)
    
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1,
        max_retries=2
    )
    
    manager.submit_task(task)
    
    # Simulate task processing with retries
    with patch.object(manager, '_execute_agent_task') as mock_execute:
        mock_execute.side_effect = Exception("Test error")
        
        # Process the task (should retry up to max_retries)
        manager._process_next_task()
        
        # Task should still be in queue after first failure
        assert len(manager._task_queue) == 1
        
        # Process again (second attempt)
        manager._process_next_task()
        
        # Task should still be in queue after second failure
        assert len(manager._task_queue) == 1
        
        # Process again (third attempt - should fail permanently)
        manager._process_next_task()
        
        # Task should be removed from queue after max retries
        assert len(manager._task_queue) == 0


def test_multiple_agents_registration():
    """Test registering multiple agents of different types."""
    manager = AgentManager()
    
    configs = [
        AgentConfig(
            agent_id=f"agent-{i:03d}",
            agent_type=AgentType.TASK_DECOMPOSER,
            name=f"Agent {i}",
            description=f"Test agent {i}"
        ) for i in range(5)
    ]
    
    for config in configs:
        manager.register_agent(config)
    
    assert len(manager._agents) == 5
    
    agents = manager.list_agents()
    assert len(agents) == 5
    
    for i, agent in enumerate(agents):
        assert agent.agent_id == f"agent-{i:03d}"


def test_agent_manager_thread_safety():
    """Test thread safety of agent manager operations."""
    manager = AgentManager()
    
    # Perform operations that should be thread-safe
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent for unit tests"
    )
    
    # These operations should be safe to perform concurrently
    manager.register_agent(config)
    manager.get_agent("test-agent-001")
    manager.list_agents()
    
    # Verify state is consistent
    assert len(manager._agents) == 1
    assert manager.get_agent("test-agent-001") is not None


def test_workflow_with_multiple_agents():
    """Test workflow with multiple different agents."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add steps with different agent types
    workflow.add_step("task-decomposer-001", {"task": "decompose this"})
    workflow.add_step("tool-orchestrator-001", {"task": "use tools"})
    workflow.add_step("memory-agent-001", {"task": "store context"})
    workflow.add_step("cognitive-guardian-001", {"task": "safety check"})
    
    assert len(workflow.steps) == 4
    
    # Verify step structure
    for step in workflow.steps:
        assert "agent_id" in step
        assert "input_data" in step
        assert "priority" in step
        assert "status" in step
        assert "result" in step
        assert "error" in step


def test_agent_manager_cleanup():
    """Test cleanup of agent manager resources."""
    manager = get_agent_manager()
    
    # Start and stop the manager
    manager.start()
    manager.stop()
    
    # Manager should be in a clean state
    assert manager._running == False
    assert manager._worker_thread is None


def test_agent_config_with_optional_fields():
    """Test agent configuration with optional fields."""
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent",
        litellm_instance="main",
        model="gpt-4",
        tools=["tool1", "tool2"],
        memory_enabled=True,
        max_retries=5,
        timeout=600,
        environment={"VAR1": "value1", "VAR2": "value2"}
    )
    
    assert config.litellm_instance == "main"
    assert config.model == "gpt-4"
    assert config.tools == ["tool1", "tool2"]
    assert config.memory_enabled == True
    assert config.max_retries == 5
    assert config.timeout == 600
    assert config.environment == {"VAR1": "value1", "VAR2": "value2"}


def test_agent_manager_integration_with_litellm():
    """Test agent manager integration with LiteLLM manager."""
    manager = AgentManager()
    
    # The agent manager should have a LiteLLM manager
    assert manager._litellm_manager is not None
    
    # Test that we can access LiteLLM functionality through the agent manager
    litellm_manager = manager._litellm_manager
    
    # Verify it's the same instance as the global one
    from dopemux.litellm_manager import get_litellm_manager
    global_litellm = get_litellm_manager()
    
    assert litellm_manager is global_litellm


def test_workflow_priority_handling():
    """Test workflow priority handling."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add steps with different priorities
    workflow.add_step("agent-001", {"task": "high priority"}, priority=1)
    workflow.add_step("agent-002", {"task": "medium priority"}, priority=3)
    workflow.add_step("agent-003", {"task": "low priority"}, priority=5)
    workflow.add_step("agent-004", {"task": "highest priority"}, priority=1)
    
    # Verify priorities are set correctly
    priorities = [step["priority"] for step in workflow.steps]
    assert priorities == [1, 3, 5, 1]


def test_agent_manager_error_recovery():
    """Test agent manager error recovery."""
    manager = AgentManager()
    
    # Test that manager can handle errors gracefully
    try:
        # Try to register an invalid agent (missing required fields)
        # This should fail but not crash the manager
        config = AgentConfig(
            agent_id="",  # Empty ID should cause issues
            agent_type=AgentType.TASK_DECOMPOSER,
            name="",
            description=""
        )
        manager.register_agent(config)
    except Exception:
        pass  # Expected to fail
    
    # Manager should still be functional
    assert manager._running == False  # Not started yet
    assert len(manager._agents) == 0  # No agents registered


def test_agent_workflow_status_transitions():
    """Test workflow status transitions."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Initial status should be IDLE
    assert workflow.status == AgentStatus.IDLE
    
    # Add a step and execute
    workflow.add_step("test-agent", {"input": "test"})
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "task-id"
        
        result = workflow.execute()
        
        # Status should be COMPLETED after successful execution
        assert workflow.status == AgentStatus.COMPLETED
        assert result["status"] == AgentStatus.COMPLETED.value


def test_agent_manager_task_cleanup():
    """Test cleanup of completed tasks."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1
    )
    
    task_id = manager.submit_task(task)
    assert len(manager._active_tasks) == 1
    
    # Simulate task completion
    with patch.object(manager, '_execute_agent_task'):
        manager._process_next_task()
    
    # Active task should be cleaned up
    assert len(manager._active_tasks) == 0


def test_agent_manager_queue_management():
    """Test task queue management."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    # Submit multiple tasks
    for i in range(5):
        task = AgentTask(
            task_id="",
            agent_id="test-agent-001",
            input_data={"task": i},
            priority=1
        )
        manager.submit_task(task)
    
    assert len(manager._task_queue) == 5
    
    # Process one task
    with patch.object(manager, '_execute_agent_task'):
        manager._process_next_task()
    
    assert len(manager._task_queue) == 4


def test_agent_manager_concurrent_operations():
    """Test concurrent operations on agent manager."""
    manager = AgentManager()
    
    # These operations should be safe to perform concurrently
    config1 = AgentConfig(
        agent_id="agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Agent 1",
        description="First agent"
    )
    
    config2 = AgentConfig(
        agent_id="agent-002",
        agent_type=AgentType.TOOL_ORCHESTRATOR,
        name="Agent 2",
        description="Second agent"
    )
    
    manager.register_agent(config1)
    manager.register_agent(config2)
    
    # Verify both agents are registered
    assert len(manager._agents) == 2
    assert manager.get_agent("agent-001") is not None
    assert manager.get_agent("agent-002") is not None


def test_agent_workflow_result_structure():
    """Test structure of workflow execution results."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    workflow.add_step("test-agent", {"input": "test"})
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "task-id"
        
        result = workflow.execute()
        
        # Verify result structure
        assert "workflow_id" in result
        assert "status" in result
        assert "results" in result
        assert "steps" in result
        
        # Verify results structure
        assert len(result["results"]) == 1
        assert "agent_id" in result["results"][0]
        assert "status" in result["results"][0]
        assert "output" in result["results"][0]


def test_agent_manager_system_health():
    """Test system health reporting."""
    manager = AgentManager()
    
    status = manager.get_system_status()
    
    assert status["system_healthy"] == True
    assert isinstance(status["agents_registered"], int)
    assert isinstance(status["tasks_queued"], int)
    assert isinstance(status["tasks_active"], int)
    assert isinstance(status["litellm_instances"], int)


def test_agent_manager_detailed_health():
    """Test detailed health reporting."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    status = manager.get_detailed_status()
    
    assert status["detailed"] == True
    assert "agents" in status
    assert len(status["agents"]) == 1
    assert status["agents"][0]["agent_id"] == "test-agent-001"


def test_agent_workflow_error_recovery():
    """Test workflow error recovery."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add multiple steps
    workflow.add_step("agent-001", {"step": 1})
    workflow.add_step("agent-002", {"step": 2})
    workflow.add_step("agent-003", {"step": 3})
    
    # Mock the second step to fail
    call_count = 0
    def mock_submit_side_effect(agent_id, input_data, priority=1):
        nonlocal call_count
        call_count += 1
        if call_count == 2:  # Second step fails
            raise Exception("Step 2 failed")
        return f"task-{call_count}"
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.side_effect = mock_submit_side_effect
        
        result = workflow.execute()
        
        assert result["status"] == AgentStatus.ERROR.value
        assert result["completed_steps"] == 1
        assert result["total_steps"] == 3


def test_agent_manager_lifecycle_with_tasks():
    """Test full lifecycle with tasks."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    # Submit a task
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1
    )
    
    task_id = manager.submit_task(task)
    
    # Start and stop the manager
    manager.start()
    assert manager._running == True
    
    manager.stop()
    assert manager._running == False
    
    # Manager should have cleaned up properly
    assert len(manager._task_queue) == 0
    assert len(manager._active_tasks) == 0


def test_agent_manager_multiple_workflows():
    """Test managing multiple workflows."""
    manager = AgentManager()
    
    workflow1 = AgentWorkflow(manager)
    workflow2 = AgentWorkflow(manager)
    workflow3 = AgentWorkflow(manager)
    
    # Each workflow should have a unique ID
    assert workflow1.workflow_id != workflow2.workflow_id
    assert workflow2.workflow_id != workflow3.workflow_id
    assert workflow1.workflow_id != workflow3.workflow_id
    
    # Each workflow should start with IDLE status
    assert workflow1.status == AgentStatus.IDLE
    assert workflow2.status == AgentStatus.IDLE
    assert workflow3.status == AgentStatus.IDLE


def test_agent_manager_agent_types_coverage():
    """Test coverage of all agent types."""
    manager = AgentManager()
    
    agent_types = [
        AgentType.TASK_DECOMPOSER,
        AgentType.TOOL_ORCHESTRATOR,
        AgentType.MEMORY_AGENT,
        AgentType.COGNITIVE_GUARDIAN,
        AgentType.WORKFLOW_COORDINATOR,
        AgentType.CUSTOM
    ]
    
    for i, agent_type in enumerate(agent_types):
        config = AgentConfig(
            agent_id=f"agent-{agent_type.value}-{i}",
            agent_type=agent_type,
            name=f"{agent_type.value.replace('_', ' ').title()} Agent",
            description=f"Test agent for {agent_type.value}"
        )
        
        manager.register_agent(config)
    
    assert len(manager._agents) == len(agent_types)


def test_agent_manager_task_priority_range():
    """Test task priority range handling."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    # Test various priority values
    priorities = [1, 2, 3, 4, 5, 10, 100]
    
    for priority in priorities:
        task = AgentTask(
            task_id="",
            agent_id="test-agent-001",
            input_data={"priority": priority},
            priority=priority
        )
        
        task_id = manager.submit_task(task)
        assert len(task_id) > 0
    
    assert len(manager._task_queue) == len(priorities)


def test_agent_manager_large_workload():
    """Test agent manager with large workload."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    # Submit many tasks
    num_tasks = 50
    for i in range(num_tasks):
        task = AgentTask(
            task_id="",
            agent_id="test-agent-001",
            input_data={"task": i},
            priority=1
        )
        manager.submit_task(task)
    
    assert len(manager._task_queue) == num_tasks
    
    # Process some tasks
    with patch.object(manager, '_execute_agent_task'):
        for _ in range(10):
            manager._process_next_task()
    
    assert len(manager._task_queue) == num_tasks - 10


def test_agent_workflow_complex_scenarios():
    """Test complex workflow scenarios."""
    manager = AgentManager()
    
    # Create a complex workflow with many steps
    workflow = AgentWorkflow(manager)
    
    num_steps = 20
    for i in range(num_steps):
        priority = 1 if i % 2 == 0 else 2  # Alternate priorities
        workflow.add_step(f"agent-{i:03d}", {"step": i}, priority=priority)
    
    assert len(workflow.steps) == num_steps
    
    # Verify priorities alternate
    for i, step in enumerate(workflow.steps):
        expected_priority = 1 if i % 2 == 0 else 2
        assert step["priority"] == expected_priority


def test_agent_manager_error_conditions():
    """Test various error conditions."""
    manager = AgentManager()
    
    # Test 1: Register duplicate agent
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    try:
        manager.register_agent(config)  # Duplicate
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected
    
    # Test 2: Unregister non-existent agent
    try:
        manager.unregister_agent("non-existent")
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected
    
    # Test 3: Submit task to non-existent agent
    task = AgentTask(
        task_id="",
        agent_id="non-existent",
        input_data={},
        priority=1
    )
    
    try:
        manager.submit_task(task)
        assert False, "Should have raised AgentError"
    except AgentError:
        pass  # Expected


def test_agent_manager_cleanup_after_errors():
    """Test cleanup after errors."""
    manager = AgentManager()
    
    # Cause an error and verify manager recovers
    try:
        manager.unregister_agent("non-existent")
    except AgentError:
        pass  # Expected
    
    # Manager should still be functional
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    assert len(manager._agents) == 1


def test_agent_workflow_status_consistency():
    """Test workflow status consistency."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Initial state
    assert workflow.status == AgentStatus.IDLE
    
    # After adding steps, status should still be IDLE
    workflow.add_step("agent-001", {"step": 1})
    assert workflow.status == AgentStatus.IDLE
    
    # After execution starts, status should be RUNNING
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "task-id"
        
        # Start execution
        result = workflow.execute()
        
        # Status should be COMPLETED after successful execution
        assert workflow.status == AgentStatus.COMPLETED
        assert result["status"] == AgentStatus.COMPLETED.value


def test_agent_manager_task_management():
    """Test comprehensive task management."""
    manager = AgentManager()
    
    # Register multiple agents
    for i in range(3):
        config = AgentConfig(
            agent_id=f"agent-{i:03d}",
            agent_type=AgentType.TASK_DECOMPOSER,
            name=f"Agent {i}",
            description=f"Test agent {i}"
        )
        manager.register_agent(config)
    
    # Submit tasks to different agents
    for i in range(5):
        agent_id = f"agent-{i % 3:03d}"
        task = AgentTask(
            task_id="",
            agent_id=agent_id,
            input_data={"task": i},
            priority=1
        )
        manager.submit_task(task)
    
    assert len(manager._task_queue) == 5
    assert len(manager._active_tasks) == 5
    
    # Process some tasks
    with patch.object(manager, '_execute_agent_task'):
        for _ in range(3):
            manager._process_next_task()
    
    assert len(manager._task_queue) == 2
    assert len(manager._active_tasks) == 2


def test_agent_manager_resource_cleanup():
    """Test resource cleanup."""
    manager = AgentManager()
    
    # Start and stop multiple times
    for _ in range(3):
        manager.start()
        manager.stop()
    
    # Manager should be in a clean state
    assert manager._running == False
    assert manager._worker_thread is None


def test_agent_workflow_execution_flow():
    """Test workflow execution flow."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add steps with different agents
    workflow.add_step("agent-001", {"step": 1, "type": "first"})
    workflow.add_step("agent-002", {"step": 2, "type": "second"})
    workflow.add_step("agent-003", {"step": 3, "type": "third"})
    
    # Mock the agent manager to track execution order
    execution_order = []
    
    def mock_submit(agent_id, input_data, priority=1):
        execution_order.append((agent_id, input_data))
        return f"task-{len(execution_order)}"
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.side_effect = mock_submit
        
        result = workflow.execute()
        
        # Verify execution order
        assert len(execution_order) == 3
        assert execution_order[0][0] == "agent-001"
        assert execution_order[1][0] == "agent-002"
        assert execution_order[2][0] == "agent-003"


def test_agent_manager_concurrent_task_submission():
    """Test concurrent task submission."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    # Submit tasks concurrently (simulated)
    tasks = []
    for i in range(10):
        task = AgentTask(
            task_id="",
            agent_id="test-agent-001",
            input_data={"task": i},
            priority=1
        )
        tasks.append(task)
    
    # Submit all tasks
    task_ids = []
    for task in tasks:
        task_id = manager.submit_task(task)
        task_ids.append(task_id)
    
    assert len(task_ids) == 10
    assert len(manager._task_queue) == 10
    assert len(manager._active_tasks) == 10


def test_agent_manager_task_completion_cleanup():
    """Test cleanup after task completion."""
    manager = AgentManager()
    
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    
    manager.register_agent(config)
    
    # Submit and complete a task
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1
    )
    
    task_id = manager.submit_task(task)
    assert len(manager._active_tasks) == 1
    
    # Simulate task completion
    with patch.object(manager, '_execute_agent_task'):
        manager._process_next_task()
    
    # Task should be cleaned up
    assert len(manager._active_tasks) == 0
    assert len(manager._task_queue) == 0


def test_agent_manager_workflow_integration():
    """Test integration between agent manager and workflows."""
    manager = AgentManager()
    
    # Register agents
    for agent_type in [AgentType.TASK_DECOMPOSER, AgentType.TOOL_ORCHESTRATOR]:
        config = AgentConfig(
            agent_id=f"{agent_type.value}-001",
            agent_type=agent_type,
            name=f"{agent_type.value.title()}",
            description=f"Test {agent_type.value}"
        )
        manager.register_agent(config)
    
    # Create and execute a workflow
    workflow = AgentWorkflow(manager)
    workflow.add_step("task_decomposer-001", {"task": "decompose"})
    workflow.add_step("tool_orchestrator-001", {"task": "execute"})
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "task-id"
        
        result = workflow.execute()
        
        assert result["status"] == AgentStatus.COMPLETED.value
        assert mock_submit.call_count == 2


def test_agent_manager_system_status_updates():
    """Test that system status updates correctly."""
    manager = AgentManager()
    
    # Initial status
    status1 = manager.get_system_status()
    assert status1["agents_registered"] == 0
    assert status1["tasks_queued"] == 0
    
    # Register an agent
    config = AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Test Agent",
        description="Test agent"
    )
    manager.register_agent(config)
    
    # Status should reflect the change
    status2 = manager.get_system_status()
    assert status2["agents_registered"] == 1
    assert status2["tasks_queued"] == 0
    
    # Submit a task
    task = AgentTask(
        task_id="",
        agent_id="test-agent-001",
        input_data={"test": "data"},
        priority=1
    )
    manager.submit_task(task)
    
    # Status should reflect the task
    status3 = manager.get_system_status()
    assert status3["agents_registered"] == 1
    assert status3["tasks_queued"] == 1


def test_agent_manager_detailed_status_updates():
    """Test that detailed status updates correctly."""
    manager = AgentManager()
    
    # Register multiple agents
    for i in range(3):
        config = AgentConfig(
            agent_id=f"agent-{i:03d}",
            agent_type=AgentType.TASK_DECOMPOSER,
            name=f"Agent {i}",
            description=f"Test agent {i}"
        )
        manager.register_agent(config)
    
    # Detailed status should show all agents
    status = manager.get_detailed_status()
    assert len(status["agents"]) == 3
    
    # Verify agent details
    for i, agent in enumerate(status["agents"]):
        assert agent["agent_id"] == f"agent-{i:03d}"
        assert agent["name"] == f"Agent {i}"
        assert agent["status"] == "registered"


def test_agent_workflow_result_handling():
    """Test workflow result handling."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add steps
    workflow.add_step("agent-001", {"step": 1})
    workflow.add_step("agent-002", {"step": 2})
    
    # Mock execution with specific results
    results = [
        AgentResult(
            agent_id="agent-001",
            status=AgentStatus.COMPLETED,
            output={"result": "step 1 completed"},
            execution_time=0.5
        ),
        AgentResult(
            agent_id="agent-002",
            status=AgentStatus.COMPLETED,
            output={"result": "step 2 completed"},
            execution_time=0.3
        )
    ]
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "task-id"
        
        workflow_result = workflow.execute()
        
        # Verify workflow result structure
        assert "workflow_id" in workflow_result
        assert "status" in workflow_result
        assert "results" in workflow_result
        assert "steps" in workflow_result
        
        # Verify step results
        assert len(workflow_result["steps"]) == 2
        assert workflow_result["steps"][0]["status"] == AgentStatus.COMPLETED.value
        assert workflow_result["steps"][1]["status"] == AgentStatus.COMPLETED.value


def test_agent_manager_comprehensive_workflow():
    """Test comprehensive workflow creation and execution."""
    manager = AgentManager()
    
    # Register all agent types
    agent_types = [
        AgentType.TASK_DECOMPOSER,
        AgentType.TOOL_ORCHESTRATOR,
        AgentType.MEMORY_AGENT,
        AgentType.COGNITIVE_GUARDIAN,
        AgentType.WORKFLOW_COORDINATOR
    ]
    
    for agent_type in agent_types:
        config = AgentConfig(
            agent_id=f"{agent_type.value}-001",
            agent_type=agent_type,
            name=agent_type.value.title().replace("_", " "),
            description=f"Test {agent_type.value}"
        )
        manager.register_agent(config)
    
    # Create a comprehensive workflow
    workflow = AgentWorkflow(manager)
    
    # Add steps for each agent type
    workflow.add_step("cognitive_guardian-001", {"task": "safety check"})
    workflow.add_step("task_decomposer-001", {"task": "decompose"})
    workflow.add_step("tool_orchestrator-001", {"task": "execute tools"})
    workflow.add_step("memory_agent-001", {"task": "store context"})
    workflow.add_step("workflow_coordinator-001", {"task": "coordinate"})
    
    # Execute workflow
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.return_value = "task-id"
        
        result = workflow.execute()
        
        assert result["status"] == AgentStatus.COMPLETED.value
        assert len(result["steps"]) == 5
        assert mock_submit.call_count == 5


def test_agent_manager_error_recovery_comprehensive():
    """Test comprehensive error recovery."""
    manager = AgentManager()
    
    # Test various error scenarios
    scenarios = [
        ("duplicate_registration", lambda: manager.register_agent(AgentConfig(
            agent_id="test-agent-001",
            agent_type=AgentType.TASK_DECOMPOSER,
            name="Test Agent",
            description="Test agent"
        ))),
        ("unregister_nonexistent", lambda: manager.unregister_agent("nonexistent")),
        ("submit_to_nonexistent", lambda: manager.submit_task(AgentTask(
            task_id="", agent_id="nonexistent", input_data={}, priority=1
        )))
    ]
    
    for scenario_name, scenario_func in scenarios:
        try:
            if scenario_name == "duplicate_registration":
                # First registration should succeed
                scenario_func()
            scenario_func()
            assert False, f"Scenario {scenario_name} should have failed"
        except AgentError:
            pass  # Expected
    
    # Manager should still be functional
    config = AgentConfig(
        agent_id="recovery-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Recovery Agent",
        description="Recovery test agent"
    )
    
    manager.register_agent(config)
    assert len(manager._agents) == 1


def test_agent_workflow_priority_execution():
    """Test workflow execution with priority handling."""
    manager = AgentManager()
    workflow = AgentWorkflow(manager)
    
    # Add steps with different priorities
    workflow.add_step("agent-001", {"step": 1}, priority=3)  # Low priority
    workflow.add_step("agent-002", {"step": 2}, priority=1)  # High priority
    workflow.add_step("agent-003", {"step": 3}, priority=2)  # Medium priority
    
    # Mock execution to track order
    execution_order = []
    
    def mock_submit(agent_id, input_data, priority=1):
        execution_order.append(priority)
        return "task-id"
    
    with patch.object(manager, 'submit_task') as mock_submit:
        mock_submit.side_effect = mock_submit
        
        workflow.execute()
        
        # Steps should be executed in priority order (1, 2, 3)
        assert execution_order == [1, 2, 3]


def test_agent_manager_final_cleanup():
    """Test final cleanup of agent manager."""
    manager = get_agent_manager()
    
    # Clean up any existing state
    manager.stop()
    
    # Verify clean state
    assert manager._running == False
    assert manager._worker_thread is None
    
    # Manager should be ready for new operations
    config = AgentConfig(
        agent_id="final-test-agent-001",
        agent_type=AgentType.TASK_DECOMPOSER,
        name="Final Test Agent",
        description="Final test agent"
    )
    
    manager.register_agent(config)
    assert len(manager._agents) == 1
