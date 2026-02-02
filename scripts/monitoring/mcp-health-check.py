#!/usr/bin/env python3
"""
MCP Services Health Check
Verifies all Dopemux MCP servers are running and accessible.
"""

import subprocess

import logging

logger = logging.getLogger(__name__)

import socket
import sys
import time
from typing import Dict, List, Tuple
import json

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_docker_container(name: str) -> Tuple[bool, str]:
    """Check if Docker container is running."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={name}', '--format', '{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        status = result.stdout.strip()
        if status:
            return True, status
        return False, "Not running"
    except Exception as e:
        return False, f"Error: {e}"

        logger.error(f"Error: {e}")
def check_port(port: int, timeout: float = 2.0) -> bool:
    """Check if port is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

        logger.error(f"Error: {e}")
def check_sse_endpoint(port: int, path: str = '/sse') -> Tuple[bool, str]:
    """Check SSE endpoint responds."""
    try:
        import urllib.request
        url = f'http://localhost:{port}{path}'
        req = urllib.request.Request(url, headers={'Accept': 'text/event-stream'})
        with urllib.request.urlopen(req, timeout=3) as response:
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as e:
        # SSE might respond with specific codes that are still "working"
        if e.code in [200, 202, 204]:
            return True, f"HTTP {e.code}"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)

        logger.error(f"Error: {e}")
def check_http_endpoint(port: int, path: str = '/health') -> Tuple[bool, str]:
    """Check HTTP endpoint responds."""
    try:
        import urllib.request
        url = f'http://localhost:{port}{path}'
        with urllib.request.urlopen(url, timeout=3) as response:
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True, "No /health (expected for some services)"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)

        logger.error(f"Error: {e}")
MCP_SERVICES = {
    'Serena v2 (Code Intelligence)': {
        'type': 'sse',
        'container': 'mcp-serena',
        'port': 3006,
        'endpoint': '/sse'
    },
    'ConPort (Knowledge Graph)': {
        'type': 'http',
        'container': 'mcp-conport',
        'port': 3004,
        'endpoint': '/health'
    },
    'Desktop Commander': {
        'type': 'http',
        'container': 'mcp-desktop-commander',
        'port': 3012,
        'endpoint': '/mcp',
        'health_endpoint': '/health'
    },
    'Zen (Multi-Model Reasoning)': {
        'type': 'stdio',
        'container': 'mcp-zen',
        'port': None,
        'endpoint': None
    },
    'Dope-Context (Semantic Search)': {
        'type': 'http',
        'container': 'mcp-dope-context',
        'port': 3010,
        'endpoint': '/health'
    },
    'Exa (Neural Search)': {
        'type': 'sse',
        'container': 'mcp-exa',
        'port': 3008,
        'endpoint': '/sse'
    },
    'GPT-Researcher': {
        'type': 'http',
        'container': 'mcp-gptr-mcp',
        'port': 3009,
        'endpoint': '/health'
    },
    'DDG-MCP (Decision Graph)': {
        'type': 'http',
        'container': 'mcp-ddg',
        'port': 3015,
        'endpoint': '/health'
    }
}

INFRASTRUCTURE = {
    'PostgreSQL (ConPort/AGE)': {
        'container': 'dopemux-postgres-age',
        'port': 5455
    },
    'PostgreSQL (DDG/ConPort-KG)': {
        'container': 'dope-decision-graph-postgres',
        'port': 5433
    },
    'Redis (Primary)': {
        'container': 'dopemux-redis-primary',
        'port': 6379
    },
    'Redis (Events)': {
        'container': 'dopemux-redis-events',
        'port': 6380
    },
    'Qdrant (Vector DB)': {
        'container': 'mcp-qdrant',
        'port': 6333
    }
}

def print_header(text: str):
    """Print section header."""
    logger.info(f"\n{BLUE}{'=' * 60}{RESET}")
    logger.info(f"{BLUE}{text:^60}{RESET}")
    logger.info(f"{BLUE}{'=' * 60}{RESET}\n")

def print_status(name: str, status: bool, details: str = ""):
    """Print service status line."""
    icon = "✅" if status else "❌"
    color = GREEN if status else RED

    # Format name to fixed width
    name_width = 35
    name_display = name[:name_width].ljust(name_width)

    logger.info(f"{icon} {color}{name_display}{RESET} {details}")

def main():
    print_header("Dopemux MCP Services Health Check")

    all_healthy = True

    # Check MCP Services
    logger.info(f"{YELLOW}MCP Services:{RESET}\n")

    for name, config in MCP_SERVICES.items():
        container_ok, container_status = check_docker_container(config['container'])

        if not container_ok:
            print_status(name, False, f"Container not running: {config['container']}")
            all_healthy = False
            continue

        # Check port if applicable
        port_ok = True
        endpoint_ok = True
        endpoint_msg = ""

        if config['port']:
            port_ok = check_port(config['port'])
            if not port_ok:
                print_status(name, False, f"Port {config['port']} not listening")
                all_healthy = False
                continue

            # Check endpoint based on type
            if config['type'] == 'sse':
                endpoint_ok, endpoint_msg = check_sse_endpoint(config['port'], config['endpoint'])
            elif config['type'] == 'http':
                # Use health_endpoint if specified, otherwise use main endpoint
                health_path = config.get('health_endpoint', config['endpoint'])
                endpoint_ok, endpoint_msg = check_http_endpoint(config['port'], health_path)

        if container_ok and port_ok:
            details = f"Port {config['port']}" if config['port'] else "stdio mode"
            if endpoint_msg:
                details += f" | {endpoint_msg}"
            print_status(name, endpoint_ok, details)
            if not endpoint_ok:
                all_healthy = False
        else:
            print_status(name, False, container_status)
            all_healthy = False

    # Check Infrastructure
    logger.info(f"\n{YELLOW}Infrastructure Services:{RESET}\n")

    for name, config in INFRASTRUCTURE.items():
        container_ok, container_status = check_docker_container(config['container'])

        if not container_ok:
            print_status(name, False, f"Container not running: {config['container']}")
            all_healthy = False
            continue

        port_ok = check_port(config['port'])

        if container_ok and port_ok:
            print_status(name, True, f"Port {config['port']}")
        else:
            print_status(name, False, f"Port {config['port']} not listening")
            all_healthy = False

    # Summary
    print_header("Summary")

    if all_healthy:
        logger.info(f"{GREEN}✅ All services are healthy and operational{RESET}\n")
        return 0
    else:
        logger.info(f"{RED}❌ Some services are unhealthy or not running{RESET}\n")
        logger.info(f"{YELLOW}💡 Troubleshooting tips:{RESET}")
        logger.info(f"   1. Start all services: docker-compose up -d")
        logger.info(f"   2. Check logs: docker logs <container-name>")
        logger.info(f"   3. Restart Claude Code to reconnect MCP servers")
        logger.info()
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info(f"\n{YELLOW}Health check interrupted{RESET}")
        sys.exit(130)
