#!/usr/bin/env python3
"""
ConPort MCP Server with proper Streamable HTTP transport via mcp-proxy
Uses proper MCP patterns following MetaMCP architecture with async subprocess handling
"""

import os
import asyncio
import sys
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConPortServer:
    def __init__(self):
        self.process = None
        self.port = int(os.getenv('MCP_SERVER_PORT', 3004))
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Start the ConPort MCP server with async subprocess management"""
        logger.info(f"🧠 Starting ConPort MCP Server with Streamable HTTP on port {self.port}")

        # Build command for mcp-proxy with ConPort server
        cmd = [
            'uvx', 'mcp-proxy',
            '--transport', 'streamablehttp',
            '--port', str(self.port),
            '--host', '0.0.0.0',
            '--allow-origin', '*',
            '--',
            'uvx', '--from', 'context-portal-mcp', 'conport-mcp', '--mode', 'stdio'
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

            logger.info(f"ConPort server started with PID {self.process.pid}")

            # Wait for either process completion or shutdown signal
            done, pending = await asyncio.wait([
                asyncio.create_task(self.process.wait()),
                asyncio.create_task(self.shutdown_event.wait())
            ], return_when=asyncio.FIRST_COMPLETED)

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            if self.process.returncode is not None:
                if self.process.returncode == 0:
                    logger.info("ConPort server completed successfully")
                else:
                    logger.error(f"ConPort server failed with exit code {self.process.returncode}")
                    # Read error output for debugging
                    if self.process.stderr:
                        stderr = await self.process.stderr.read()
                        if stderr:
                            logger.error(f"Error output: {stderr.decode()}")
                    return self.process.returncode
            else:
                logger.info("Shutdown requested, terminating ConPort server")
                await self.cleanup()

            return 0

        except Exception as e:
            logger.error(f"Failed to start ConPort server: {e}")
            await self.cleanup()
            raise

    async def cleanup(self):
        """Clean shutdown of the subprocess"""
        if self.process and self.process.returncode is None:
            logger.info("Terminating ConPort server process")
            try:
                # Try graceful shutdown first
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful shutdown fails
                    logger.warning("Graceful shutdown timed out, force killing")
                    self.process.kill()
                    await self.process.wait()
                logger.info("ConPort server stopped")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        """Signal shutdown and cleanup"""
        self.shutdown_event.set()

async def main():
    server = ConPortServer()

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, server.signal_handler, sig, None)

    try:
        exit_code = await server.start()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down")
        await server.cleanup()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await server.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

