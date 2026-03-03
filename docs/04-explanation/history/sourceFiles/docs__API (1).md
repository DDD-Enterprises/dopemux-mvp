# Dopemux API Documentation

Complete API reference for Dopemux Leantime and Task-Master AI integration.

## Overview

Dopemux provides three main API layers:

1. **MCP Bridges**: Protocol-based integration with Leantime and Task-Master
2. **Sync Manager**: Bidirectional synchronization between systems
3. **ADHD Optimizations**: Attention-aware workflow management

## Authentication

### API Keys
```python
# Environment variables
LEANTIME_API_KEY="leantime_api_key_here"
TASKMASTER_API_KEY="taskmaster_api_key_here"

# In code
from src.integrations.leantime_bridge import LeantimeMCPClient

client = LeantimeMCPClient(api_key=os.getenv("LEANTIME_API_KEY"))
```

### OAuth 2.0 (Future)
```python
# OAuth flow for production deployments
auth_config = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "http://localhost:8000/callback"
}
```

## Core APIs

### LeantimeMCPClient

#### Connection Management
```python
from src.integrations.leantime_bridge import LeantimeMCPClient

# Initialize client
client = LeantimeMCPClient(
    server_url="http://localhost:8080",
    api_key="your-api-key",
    timeout=30
)

# Connect to MCP server
await client.connect()

# Health check
health = await client.health_check()
# Returns: {"status": "healthy", "version": "1.0.0", "uptime": 3600}

# Disconnect
await client.disconnect()
```

#### Project Operations
```python
# Get all projects
projects = await client.get_projects()
# Returns: List[LeantimeProject]

# Get single project
project = await client.get_project(project_id="123")
# Returns: LeantimeProject

# Create project
project = await client.create_project(
    name="New Project",
    description="Project description",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adhd_optimized=True
)
# Returns: LeantimeProject

# Update project
updated = await client.update_project(
    project_id="123",
    name="Updated Name",
    description="New description"
)
# Returns: LeantimeProject
```

#### Task Operations
```python
# Get tasks for project
tasks = await client.get_tasks(project_id="123")
# Returns: List[LeantimeTask]

# Get single task
task = await client.get_task(task_id="456")
# Returns: LeantimeTask

# Create task
task = await client.create_task(
    project_id="123",
    title="Implement feature",
    description="Detailed description",
    priority="high",
    estimated_hours=8,
    tags=["feature", "backend"],
    adhd_metadata={
        "cognitive_load": 7,
        "focus_level": "high",
        "break_reminder": True
    }
)
# Returns: LeantimeTask

# Update task
updated = await client.update_task(
    task_id="456",
    status="in_progress",
    priority="medium"
)
# Returns: LeantimeTask

# Delete task
success = await client.delete_task(task_id="456")
# Returns: bool
```

#### ADHD-Optimized Methods
```python
# Get tasks by attention level
high_focus_tasks = await client.get_tasks_by_attention_level(
    project_id="123",
    attention_level="high"
)
# Returns: List[LeantimeTask]

# Get tasks by cognitive load
medium_load_tasks = await client.get_tasks_by_cognitive_load(
    project_id="123",
    max_load=5
)
# Returns: List[LeantimeTask]

# Get recommended next tasks
recommendations = await client.get_recommended_tasks(
    project_id="123",
    current_attention="medium",
    available_time=30
)
# Returns: List[TaskRecommendation]
```

### TaskMasterMCPClient

#### Initialization
```python
from src.integrations.taskmaster_bridge import TaskMasterMCPClient

# Initialize with subprocess management
client = TaskMasterMCPClient(
    port=3001,
    auto_start=True,
    timeout=60
)

# Connect
await client.connect()
```

#### PRD Processing
```python
# Parse PRD file
analysis = await client.parse_prd(
    prd_path="/path/to/prd.md",
    options={
        "complexity_analysis": True,
        "dependency_detection": True,
        "adhd_optimization": True
    }
)
# Returns: PRDAnalysis

# Get task breakdown
tasks = await client.get_task_breakdown(
    prd_content="# Feature Specification\n...",
    complexity_level="medium",
    max_tasks=20
)
# Returns: List[TaskMasterTask]

# Analyze complexity
complexity = await client.analyze_complexity(
    content="Detailed feature description...",
    context="web application"
)
# Returns: ComplexityAnalysis
```

#### Task Operations
```python
# Create task from PRD section
task = await client.create_task(
    title="Implement user auth",
    description="Add login/logout functionality",
    complexity_level="medium",
    estimated_hours=6
)
# Returns: TaskMasterTask

# Get task recommendations
recommendations = await client.get_task_recommendations(
    project_context="web app",
    current_tasks=existing_tasks,
    user_preferences={
        "adhd_optimized": True,
        "max_complexity": 7
    }
)
# Returns: List[TaskRecommendation]

# Decompose complex task
subtasks = await client.decompose_task(
    task_id="789",
    max_subtasks=5,
    target_duration=25  # minutes
)
# Returns: List[TaskMasterTask]
```

### Sync Manager

#### Initialization
```python
from src.integrations.sync_manager import LeantimeTaskMasterSyncManager

sync_manager = LeantimeTaskMasterSyncManager(
    leantime_client=leantime_client,
    taskmaster_client=taskmaster_client,
    sync_interval=300,  # seconds
    conflict_resolution="leantime_wins"
)
```

#### PRD-to-Tasks Workflow
```python
# Complete PRD processing workflow
result = await sync_manager.process_prd(
    prd_path="/path/to/prd.md",
    project_id="123",
    options={
        "create_tasks": True,
        "sync_immediately": True,
        "adhd_optimize": True
    }
)
# Returns: PRDProcessingResult

# Sync existing tasks
sync_result = await sync_manager.sync_tasks(
    project_id="123",
    direction="bidirectional"  # or "leantime_to_taskmaster", "taskmaster_to_leantime"
)
# Returns: SyncResult
```

#### Conflict Resolution
```python
# Handle sync conflicts
conflicts = await sync_manager.detect_conflicts(project_id="123")
# Returns: List[SyncConflict]

# Resolve conflicts
resolution_result = await sync_manager.resolve_conflicts(
    conflicts=conflicts,
    strategy="manual",  # or "auto", "leantime_wins", "taskmaster_wins"
    user_input=conflict_resolutions
)
# Returns: ConflictResolutionResult

# Get sync status
status = await sync_manager.get_sync_status(project_id="123")
# Returns: SyncStatus
```

### ADHD Optimizations

#### Task Optimizer
```python
from src.utils.adhd_optimizations import ADHDTaskOptimizer

optimizer = ADHDTaskOptimizer()

# Optimize task schedule
schedule = optimizer.optimize_schedule(
    tasks=task_list,
    current_attention="medium",
    available_time=120,  # minutes
    preferences={
        "focus_duration": 25,
        "break_duration": 5,
        "max_context_switches": 3
    }
)
# Returns: OptimizedSchedule

# Get attention recommendations
recommendations = optimizer.get_attention_recommendations(
    current_load="high",
    recent_performance=performance_metrics,
    time_of_day="morning"
)
# Returns: AttentionRecommendations

# Analyze cognitive load
load_analysis = optimizer.analyze_cognitive_load(
    tasks=current_tasks,
    duration=60,  # minutes
    user_profile=adhd_profile
)
# Returns: CognitiveLoadAnalysis
```

#### Context Management
```python
# Save context
context_id = await optimizer.save_context(
    task_id="456",
    mental_model="Working on user auth, completed login form",
    decisions=["Use JWT tokens", "Store in httpOnly cookies"],
    next_steps=["Implement logout", "Add password reset"]
)
# Returns: str (context_id)

# Restore context
context = await optimizer.restore_context(context_id)
# Returns: WorkContext

# Get context history
history = await optimizer.get_context_history(
    task_id="456",
    days_back=7
)
# Returns: List[WorkContext]
```

## Data Models

### Core Models

#### LeantimeProject
```python
@dataclass
class LeantimeProject:
    id: str
    name: str
    description: str
    status: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime
    adhd_settings: Optional[ADHDSettings] = None
```

#### LeantimeTask
```python
@dataclass
class LeantimeTask:
    id: str
    project_id: str
    title: str
    description: str
    status: str
    priority: str
    estimated_hours: float
    actual_hours: float
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    adhd_metadata: Optional[ADHDMetadata] = None
```

#### TaskMasterTask
```python
@dataclass
class TaskMasterTask:
    id: str
    title: str
    description: str
    complexity_score: int
    estimated_duration: int  # minutes
    dependencies: List[str]
    tags: List[str]
    prd_section: Optional[str] = None
    adhd_optimized: bool = False
```

#### ADHDMetadata
```python
@dataclass
class ADHDMetadata:
    cognitive_load: int  # 1-10 scale
    focus_level: str  # "low", "medium", "high"
    break_reminder: bool
    context_switch_cost: int  # 1-5 scale
    optimal_time_of_day: List[str]  # ["morning", "afternoon", "evening"]
    estimated_focus_duration: int  # minutes
```

### Sync Models

#### SyncResult
```python
@dataclass
class SyncResult:
    success: bool
    synced_tasks: int
    conflicts_detected: int
    conflicts_resolved: int
    errors: List[str]
    sync_duration: float  # seconds
    timestamp: datetime
```

#### SyncConflict
```python
@dataclass
class SyncConflict:
    task_id: str
    field: str
    leantime_value: Any
    taskmaster_value: Any
    conflict_type: str  # "update", "delete", "create"
    timestamp: datetime
    auto_resolvable: bool
```

## Error Handling

### Exception Types
```python
from src.integrations.exceptions import (
    LeantimeConnectionError,
    TaskMasterConnectionError,
    SyncConflictError,
    ADHDOptimizationError
)

# Handle connection errors
try:
    await client.connect()
except LeantimeConnectionError as e:
    logger.error(f"Leantime connection failed: {e}")
    # Implement retry logic

# Handle sync conflicts
try:
    sync_result = await sync_manager.sync_tasks(project_id)
except SyncConflictError as e:
    conflicts = e.conflicts
    # Handle conflicts with user input
```

### Error Responses
```python
# Standard error response format
{
    "error": {
        "code": "LEANTIME_CONNECTION_FAILED",
        "message": "Unable to connect to Leantime server",
        "details": {
            "server_url": "http://localhost:8080",
            "timeout": 30,
            "last_attempt": "2024-01-15T10:30:00Z"
        },
        "suggestions": [
            "Check if Leantime server is running",
            "Verify API key is correct",
            "Ensure network connectivity"
        ]
    }
}
```

## Rate Limiting

### Request Limits
- Leantime API: 100 requests/minute per API key
- Task-Master MCP: No built-in limits (subprocess-based)
- Sync operations: Max 1 full sync per minute per project

### Handling Rate Limits
```python
from src.integrations.rate_limiter import RateLimiter

limiter = RateLimiter(requests_per_minute=100)

async with limiter:
    result = await client.get_projects()
```

## WebSocket Support (Future)

### Real-time Updates
```python
# WebSocket connection for real-time sync
from src.integrations.websocket_client import DopemuxWebSocket

ws = DopemuxWebSocket("ws://localhost:8080/ws")

@ws.on("task_updated")
async def handle_task_update(event):
    task_id = event["task_id"]
    changes = event["changes"]
    # Handle real-time task updates

await ws.connect()
```

## Testing APIs

### Mock Clients
```python
from tests.mocks import MockLeantimeMCPClient, MockTaskMasterMCPClient

# Use in tests
mock_client = MockLeantimeMCPClient()
mock_client.set_response("get_projects", [project1, project2])

projects = await mock_client.get_projects()
assert len(projects) == 2
```

### Integration Testing
```python
# Test complete workflow
from tests.integration.helpers import IntegrationTestHelper

helper = IntegrationTestHelper()
await helper.setup_test_environment()

# Test PRD-to-tasks workflow
result = await helper.test_prd_workflow(
    prd_content="test PRD content",
    expected_tasks=5
)
assert result.success
```

---

**API Version**: 1.0.0
**Last Updated**: 2024-01-15
**Compatibility**: Python 3.8+, Docker 20.10+