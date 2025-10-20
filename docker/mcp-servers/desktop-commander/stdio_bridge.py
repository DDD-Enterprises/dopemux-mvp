#!/usr/bin/env python3
"""
Desktop-Commander MCP Stdio Bridge

Bridges Claude Code's stdio MCP protocol to Desktop-Commander's HTTP server.
Reads JSON-RPC from stdin, forwards to HTTP endpoint, returns response to stdout.
"""

import sys
import json
import asyncio
import aiohttp
import logging

# Configure logging to stderr (stdout is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Desktop-Commander HTTP server endpoint
DESKTOP_COMMANDER_URL = "http://localhost:3012/mcp"

async def handle_request(request: dict) -> dict:
    """Forward MCP request to Desktop-Commander HTTP server"""
    try:
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        logger.debug(f"Forwarding request: {method}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                DESKTOP_COMMANDER_URL,
                json={'method': method, 'params': params},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status}: {error_text}")
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {
                            'code': -32603,
                            'message': f"HTTP {response.status}: {error_text}"
                        }
                    }

                result_data = await response.json()

                # Desktop-Commander returns {result: ..., error: ...}
                # Convert to JSON-RPC format
                if result_data.get('error'):
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {
                            'code': -32603,
                            'message': result_data['error']
                        }
                    }
                else:
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': result_data['result']
                    }

    except asyncio.TimeoutError:
        logger.error("Request timeout")
        return {
            'jsonrpc': '2.0',
            'id': request.get('id'),
            'error': {'code': -32603, 'message': 'Request timeout'}
        }
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return {
            'jsonrpc': '2.0',
            'id': request.get('id'),
            'error': {'code': -32603, 'message': str(e)}
        }

async def main():
    """Main stdio loop"""
    logger.info("Desktop-Commander Stdio Bridge started")
    logger.info(f"Forwarding to: {DESKTOP_COMMANDER_URL}")

    # Ensure stdin is available and properly configured for asyncio
    import os
    import fcntl

    try:
        # Verify stdin is a valid file descriptor
        stdin_fd = sys.stdin.fileno()

        # Set stdin to blocking mode for asyncio compatibility
        flags = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
        if flags & os.O_NONBLOCK:
            fcntl.fcntl(stdin_fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
            logger.debug("Set stdin to blocking mode")

    except (AttributeError, OSError, ValueError) as e:
        logger.error(f"stdin is not available or not a valid file descriptor: {e}")
        logger.error("This script must be run with stdin connected (not in background)")
        return

    # Read from stdin and write to stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    try:
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    except Exception as e:
        logger.error(f"Failed to connect stdin to asyncio: {e}")
        logger.error("Make sure stdin is available and the script is run interactively")
        return

    while True:
        try:
            # Read line from stdin
            line = await reader.readline()
            if not line:
                logger.info("EOF received, exiting")
                break

            # Parse JSON-RPC request
            try:
                request = json.loads(line.decode())
                logger.debug(f"Received request: {request}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                continue

            # Handle the request
            response = await handle_request(request)

            # Send response to stdout
            response_str = json.dumps(response) + '\n'
            sys.stdout.write(response_str)
            sys.stdout.flush()
            logger.debug(f"Sent response for request {request.get('id')}")

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            continue

def run():
    """Entry point for uvx/uv tool"""
    asyncio.run(main())

if __name__ == '__main__':
    run()
