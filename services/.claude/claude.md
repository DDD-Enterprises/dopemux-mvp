# Services Development Context

**Scope**: Service implementations, integrations, and microservice coordination
**Inherits**: Two-Plane Architecture from project root
**Focus**: Service excellence with ADHD-friendly development patterns and clear boundaries

## 🏗️ Service Architecture

### Service Design Principles
- **Single Responsibility**: Each service handles one specific domain
- **Clear Boundaries**: Well-defined interfaces and communication patterns
- **ADHD-Friendly**: Predictable behavior and clear error handling
- **Autonomous Operation**: Services can function independently when possible

### Service Categories
- **Core Services**: Essential business logic and data management
- **Integration Services**: External system communication and data transformation
- **Utility Services**: Shared functionality and cross-cutting concerns
- **MCP Services**: Model Context Protocol servers for AI coordination

## 🎯 Service Development Standards

### Service Structure Template
```python
# services/[service-name]/main.py
"""
Service: [Service Name]
Purpose: [Clear description of service responsibility]
Dependencies: [List of required external services]
Health: /health endpoint for monitoring
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    """Standard health check response."""
    status: str = "healthy"
    service: str
    version: str
    dependencies: dict[str, str]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle with proper startup/shutdown."""
    logger.info("🚀 Starting [Service Name] service")

    # Initialize service dependencies
    await initialize_dependencies()

    yield

    # Cleanup on shutdown
    logger.info("🛑 Shutting down [Service Name] service")
    await cleanup_dependencies()

# Create FastAPI application
app = FastAPI(
    title="[Service Name]",
    description="[Service description]",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check service dependencies
        dependency_status = await check_dependencies()

        return HealthResponse(
            service="[service-name]",
            version="1.0.0",
            dependencies=dependency_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

async def initialize_dependencies():
    """Initialize all service dependencies."""
    logger.info("📦 Initializing service dependencies")
    # Dependency setup logic here

async def cleanup_dependencies():
    """Clean up service dependencies."""
    logger.info("🧹 Cleaning up service dependencies")
    # Cleanup logic here

async def check_dependencies() -> dict[str, str]:
    """Check health of service dependencies."""
    return {
        "database": "healthy",
        "external_api": "healthy"
    }
```

### Service Communication Patterns
```python
# services/shared/communication.py
"""
Shared communication patterns for service-to-service interaction.
ADHD-Friendly: Clear error handling and timeout management.
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ServiceRequest(BaseModel):
    """Standard service request format."""
    operation: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    timeout: int = 30

class ServiceResponse(BaseModel):
    """Standard service response format."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    correlation_id: Optional[str] = None

class ServiceClient:
    """HTTP client for service-to-service communication."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def call_service(self, request: ServiceRequest) -> ServiceResponse:
        """Make service call with proper error handling."""
        try:
            logger.info(f"📡 Calling service: {request.operation}")

            async with self.session.post(
                f"{self.base_url}/api/{request.operation}",
                json=request.dict(),
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return ServiceResponse(success=True, data=data)
                else:
                    error_text = await response.text()
                    return ServiceResponse(
                        success=False,
                        error=f"Service error: {response.status} - {error_text}"
                    )

        except asyncio.TimeoutError:
            return ServiceResponse(
                success=False,
                error="Service call timeout"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Service call failed: {str(e)}"
            )
```

## 🚀 Agent Coordination

### Developer Agent (Primary)
**For Service Development**:
- Implement services following established patterns and standards
- Ensure proper error handling and logging throughout service code
- Create comprehensive tests for service functionality
- Integrate services with Two-Plane Architecture coordination

### Architect Agent (Consultation)
**For Service Design**:
- Design service boundaries and communication patterns
- Review service architecture for scalability and maintainability
- Guide integration patterns with external systems
- Ensure services align with overall system architecture

### Service Quality Standards
- **Reliability**: Services handle failures gracefully with proper recovery
- **Observability**: Comprehensive logging, metrics, and health checks
- **Performance**: Efficient resource usage and response times
- **Security**: Proper authentication, authorization, and data protection

## 🔧 Service-Specific Patterns

### MCP Service Template
```python
# services/mcp-[service-name]/server.py
"""
MCP Service: [Service Name]
Purpose: Model Context Protocol server for AI coordination
Integration: Works with Two-Plane Architecture
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

# Create MCP server instance
server = Server("mcp-[service-name]")

@server.list_tools()
async def list_tools():
    """List available tools for this MCP service."""
    return [
        Tool(
            name="[tool-name]",
            description="[Clear tool description]",
            inputSchema={
                "type": "object",
                "properties": {
                    "parameter": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["parameter"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls with proper error handling."""
    try:
        if name == "[tool-name]":
            result = await handle_tool_operation(arguments)
            return [TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def handle_tool_operation(arguments: dict) -> str:
    """Handle specific tool operation."""
    # Tool logic here
    return "Operation completed successfully"

async def main():
    """Start MCP server with proper lifecycle management."""
    logger.info("🚀 Starting MCP [service-name] server")

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("🛑 MCP server shutdown requested")
    except Exception as e:
        logger.error(f"❌ MCP server error: {e}")
    finally:
        logger.info("👋 MCP [service-name] server stopped")

if __name__ == "__main__":
    asyncio.run(main())
```

### Data Processing Service
```python
# services/data-processor/processor.py
"""
Data Processing Service
Purpose: Handle data transformation and validation
ADHD-Friendly: Clear progress feedback for long operations
"""

from typing import List, Dict, Any
import asyncio
from pydantic import BaseModel

class ProcessingJob(BaseModel):
    """Data processing job definition."""
    id: str
    data: List[Dict[str, Any]]
    operation: str
    progress: float = 0.0
    status: str = "pending"

class DataProcessor:
    """Process data with ADHD-friendly progress tracking."""

    def __init__(self):
        self.jobs: Dict[str, ProcessingJob] = {}

    async def submit_job(self, job: ProcessingJob) -> str:
        """Submit data processing job."""
        self.jobs[job.id] = job
        logger.info(f"📝 Submitted processing job: {job.id}")

        # Start processing in background
        asyncio.create_task(self.process_job(job.id))

        return job.id

    async def process_job(self, job_id: str) -> None:
        """Process job with progress updates."""
        job = self.jobs[job_id]
        job.status = "processing"

        try:
            total_items = len(job.data)
            processed = 0

            for item in job.data:
                # Process individual item
                await self.process_item(item, job.operation)

                # Update progress
                processed += 1
                job.progress = processed / total_items
                logger.info(f"📊 Job {job_id} progress: {job.progress:.1%}")

            job.status = "completed"
            logger.info(f"✅ Job {job_id} completed successfully")

        except Exception as e:
            job.status = "failed"
            logger.error(f"❌ Job {job_id} failed: {e}")

    async def get_job_status(self, job_id: str) -> ProcessingJob:
        """Get current job status."""
        return self.jobs.get(job_id)

    async def process_item(self, item: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """Process individual data item."""
        # Item processing logic here
        await asyncio.sleep(0.1)  # Simulate processing time
        return item
```

## 📁 Service Organization

### Directory Structure
```
services/
├── core/                 # Core business services
│   ├── user-management/  # User and authentication
│   ├── task-engine/      # Task processing and coordination
│   └── memory-system/    # ConPort and memory management
├── integration/          # External system integrations
│   ├── leantime-bridge/  # Leantime PM system integration
│   ├── github-sync/      # GitHub repository integration
│   └── notification/     # External notification services
├── mcp/                  # MCP server implementations
│   ├── mcp-conport/      # ConPort MCP server
│   ├── mcp-task-master/  # Task Master MCP server
│   └── mcp-serena/       # Serena LSP MCP server
├── utility/              # Shared utility services
│   ├── file-processor/   # File handling and processing
│   ├── scheduler/        # Background job scheduling
│   └── health-monitor/   # System health monitoring
└── shared/               # Shared libraries and utilities
    ├── communication/    # Service communication patterns
    ├── models/           # Shared data models
    └── middleware/       # Common middleware components
```

### Service Configuration
```yaml
# services/[service-name]/config.yml
service:
  name: "[service-name]"
  version: "1.0.0"
  port: 8080
  log_level: "INFO"

dependencies:
  database:
    url: "${DATABASE_URL}"
    pool_size: 10
  external_api:
    url: "${EXTERNAL_API_URL}"
    timeout: 30

health_check:
  interval: 30
  timeout: 10
  retries: 3

monitoring:
  metrics_enabled: true
  tracing_enabled: true
  log_structured: true
```

## 🎯 ADHD-Friendly Service Patterns

### Progress Tracking
```python
class ProgressTracker:
    """Track long-running operation progress."""

    def __init__(self, total_items: int):
        self.total_items = total_items
        self.completed_items = 0
        self.start_time = time.time()

    def update(self, items_completed: int = 1):
        """Update progress with visual feedback."""
        self.completed_items += items_completed
        progress = self.completed_items / self.total_items

        # Calculate ETA
        elapsed = time.time() - self.start_time
        eta = (elapsed / self.completed_items) * (self.total_items - self.completed_items)

        logger.info(
            f"📊 Progress: {progress:.1%} "
            f"({self.completed_items}/{self.total_items}) "
            f"ETA: {eta:.1f}s"
        )
```

### Error Recovery
```python
async def resilient_operation(operation, max_retries=3, backoff=1):
    """Execute operation with retry logic and clear feedback."""
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Attempt {attempt + 1}/{max_retries}")
            return await operation()

        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌ Operation failed after {max_retries} attempts: {e}")
                raise

            wait_time = backoff * (2 ** attempt)
            logger.warning(f"⚠️ Attempt failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

---

**Service Excellence**: Well-designed, reliable services with clear boundaries and responsibilities
**ADHD Integration**: Progress tracking, clear feedback, and predictable behavior patterns
**Architecture Alignment**: Services that support and enhance the Two-Plane Architecture coordination