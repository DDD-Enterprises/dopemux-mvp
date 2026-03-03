import asyncio
from task_orchestrator.app import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
