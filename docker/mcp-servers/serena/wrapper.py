#!/usr/bin/env python3
"""
Serena MCP Server with proper Streamable HTTP transport via mcp-proxy
Uses metamcp proxy pattern following ConPort architecture with async subprocess handling
"""

import os
import asyncio
import sys
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerenaServer:
    def __init__(self):
        self.process = None
        self.port = int(os.getenv('MCP_SERVER_PORT', 3006))
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Start the Serena MCP server with async subprocess management"""
        logger.info(f"🔧 Starting Serena MCP Server with Streamable HTTP on port {self.port}")

        # Build command for mcp-proxy with Serena server
        cmd = [
            'uvx', 'mcp-proxy',
            '--transport', 'streamablehttp',
            '--port', str(self.port),
            '--host', '0.0.0.0',
            '--allow-origin', '*',
            '--',
            'uvx', '--from', 'git+https://github.com/oraios/serena', 'serena', 'start-mcp-server'
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

        try:
            # Create async subprocess - non-blocking
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            logger.info(f"Serena server started with PID {self.process.pid}")

            # Monitor process output
            asyncio.create_task(self._monitor_output())

            # Wait for shutdown or process completion
            await asyncio.wait([
                asyncio.create_task(self.shutdown_event.wait()),
                asyncio.create_task(self.process.wait())
            ], return_when=asyncio.FIRST_COMPLETED)

        except Exception as e:
            logger.error(f"Failed to start Serena server: {e}")
            sys.exit(1)

    async def _monitor_output(self):
        """Monitor subprocess output streams"""
        if not self.process:
            return

        async def read_stream(stream, prefix):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode().strip()
                    if decoded:
                        logger.info(f"[SERENA {prefix}] {decoded}")
            except Exception as e:
                logger.error(f"Error reading {prefix} stream: {e}")

        # Start output monitoring tasks
        if self.process.stdout:
            asyncio.create_task(read_stream(self.process.stdout, "OUT"))
        if self.process.stderr:
            asyncio.create_task(read_stream(self.process.stderr, "ERR"))

    async def stop(self):
        """Stop the server gracefully"""
        logger.info("🔧 Shutting down Serena MCP Server...")
        self.shutdown_event.set()

        if self.process and self.process.returncode is None:
            try:
                # Send SIGTERM to process group
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()

                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    # Force kill if needed
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                    await self.process.wait()

            except ProcessLookupError:
                pass  # Process already ended

async def main():
    server = SerenaServer()

    # Setup signal handlers
    def signal_handler():
        asyncio.create_task(server.stop())

    # Register signal handlers for graceful shutdown
    for sig in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(sig, lambda s, f: signal_handler())

    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        await server.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())