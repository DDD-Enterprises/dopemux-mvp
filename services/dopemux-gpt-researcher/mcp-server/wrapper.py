#!/usr/bin/env python3
"""
GPT-Researcher MCP Server with Streamable HTTP transport via mcp-proxy
"""

import os
import asyncio
import sys
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GptResearcherServer:
    def __init__(self):
        self.process = None
        self.port = int(os.getenv('MCP_SERVER_PORT', 3009))
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Start the GPT-Researcher MCP server with async subprocess management"""
        logger.info(f"🔬 Starting GPT-Researcher MCP Server with Streamable HTTP on port {self.port}")

        # Build command for mcp-proxy with GPT-Researcher server
        cmd = [
            'uvx', 'mcp-proxy',
            '--transport', 'streamablehttp',
            '--port', str(self.port),
            '--host', '0.0.0.0',
            '--allow-origin', '*',
            '--',
            'python', '/app/server.py'
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

        try:
            # Create async subprocess
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            logger.info(f"GPT-Researcher server started with PID {self.process.pid}")

            # Monitor process output
            async def read_output(stream, prefix):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    logger.info(f"[GPTR {prefix}] {line.decode().strip()}")

            # Create tasks for stdout and stderr
            await asyncio.gather(
                read_output(self.process.stdout, "OUT"),
                read_output(self.process.stderr, "ERR"),
                self.wait_for_shutdown()
            )

        except Exception as e:
            logger.error(f"Failed to start GPT-Researcher server: {e}")
            raise

    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self.shutdown_event.wait()
        logger.info("Shutting down GPT-Researcher server...")

        if self.process:
            try:
                # Send SIGTERM to process group
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()

                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("GPT-Researcher server didn't stop gracefully, killing...")
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

    def handle_signal(self, sig):
        """Handle shutdown signals"""
        logger.info(f"Received signal {sig}, initiating shutdown...")
        self.shutdown_event.set()


async def main():
    server = GptResearcherServer()

    # Set up signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: server.handle_signal(s))

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
