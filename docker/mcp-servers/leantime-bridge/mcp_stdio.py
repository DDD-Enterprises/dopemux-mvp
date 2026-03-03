import asyncio
from leantime_bridge.server import app
from mcp.server.stdio import stdio_server

async def run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(run())
