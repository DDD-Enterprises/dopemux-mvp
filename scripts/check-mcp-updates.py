#!/usr/bin/env python3
"""
MCP Update Checker - Check all MCP servers for available updates
Usage: python3 scripts/check-mcp-updates.py
"""

import json

import logging

logger = logging.getLogger(__name__)

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class MCPServerStatus:
    name: str
    current_version: str
    latest_version: str
    update_available: bool
    upstream_url: str
    container_name: Optional[str] = None


def get_zen_version() -> Optional[MCPServerStatus]:
    """Check Zen MCP server version"""
    try:
        # Get current version from Docker container
        result = subprocess.run(
            ["docker", "exec", "mcp-zen", "python", "-c", "from config import __version__; logger.info(__version__)"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            logger.error(f"⚠️  Failed to get Zen MCP version from Docker: {result.stderr}")
            return None

        current = result.stdout.strip()

        # Get latest version from GitHub
        import urllib.request
        with urllib.request.urlopen("https://raw.githubusercontent.com/BeehiveInnovations/zen-mcp-server/main/config.py", timeout=10) as response:
            content = response.read().decode("utf-8")
            import re
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            latest = match.group(1) if match else "Unknown"

        return MCPServerStatus(
            name="zen",
            current_version=current,
            latest_version=latest,
            update_available=current != latest,
            upstream_url="https://github.com/BeehiveInnovations/zen-mcp-server",
            container_name="mcp-zen"
        )
    except Exception as e:
        logger.error(f"⚠️  Error checking Zen MCP: {e}")
        return None


def get_conport_version() -> Optional[MCPServerStatus]:
    """Check ConPort MCP server version"""
    try:
        # ConPort is running locally via venv
        conport_path = Path("/Users/hue/code/dopemux-mvp/services/conport")

        if not conport_path.exists():
            return None

        # Get current version from pyproject.toml
        pyproject_file = conport_path / "pyproject.toml"
        if not pyproject_file.exists():
            return None

        import re
        with open(pyproject_file) as f:
            content = f.read()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            current = match.group(1) if match else "Unknown"

        return MCPServerStatus(
            name="conport",
            current_version=current,
            latest_version=current,  # Local service, no upstream
            update_available=False,
            upstream_url="Local service (no upstream)",
            container_name=None
        )
    except Exception as e:
        logger.error(f"⚠️  Error checking ConPort: {e}")
        return None


def get_serena_version() -> Optional[MCPServerStatus]:
    """Check Serena MCP server version"""
    try:
        # Serena is running in Docker
        result = subprocess.run(
            ["docker", "exec", "dopemux-mcp-serena", "python", "-c", "import sys; sys.path.append('/app'); from config import VERSION; logger.info(VERSION)"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            logger.error(f"⚠️  Failed to get Serena version from Docker: {result.stderr}")
            return None

        current = result.stdout.strip()

        return MCPServerStatus(
            name="serena",
            current_version=current,
            latest_version=current,  # Local service, no upstream
            update_available=False,
            upstream_url="Local service (no upstream)",
            container_name="dopemux-mcp-serena"
        )
    except Exception as e:
        logger.error(f"⚠️  Error checking Serena: {e}")
        return None


def check_all_mcp_servers() -> list[MCPServerStatus]:
    """Check all MCP servers for updates"""
    logger.info("🔍 Checking MCP server versions...\n")

    results = []

    # Check Zen MCP
    zen_status = get_zen_version()
    if zen_status:
        results.append(zen_status)

    # Check ConPort
    conport_status = get_conport_version()
    if conport_status:
        results.append(conport_status)

    # Check Serena
    serena_status = get_serena_version()
    if serena_status:
        results.append(serena_status)

    return results


def print_results(results: list[MCPServerStatus]):
    """Print formatted results"""
    logger.info("=" * 80)
    logger.info("MCP SERVER UPDATE STATUS")
    logger.info("=" * 80)
    logger.info()

    update_available_count = 0

    for server in results:
        status_icon = "🚀" if server.update_available else "✅"
        status_text = "UPDATE AVAILABLE" if server.update_available else "Up to date"

        logger.info(f"{status_icon} {server.name.upper()}")
        logger.info(f"   Current:  {server.current_version}")
        logger.info(f"   Latest:   {server.latest_version}")
        logger.info(f"   Status:   {status_text}")
        logger.info(f"   Upstream: {server.upstream_url}")

        if server.container_name:
            logger.info(f"   Container: {server.container_name}")

        logger.info()

        if server.update_available:
            update_available_count += 1

    logger.info("=" * 80)

    if update_available_count > 0:
        logger.info(f"\n✨ {update_available_count} update(s) available!")
        logger.info("Run './scripts/update-mcp.sh <server-name>' to update")
        logger.info("Example: ./scripts/update-mcp.sh zen")
    else:
        logger.info("\n✨ All MCP servers are up to date!")

    logger.info()


def main():
    """Main entry point"""
    results = check_all_mcp_servers()

    if not results:
        logger.error("❌ No MCP servers found or all checks failed")
        sys.exit(1)

    print_results(results)

    # Exit with non-zero if updates available
    updates_available = any(r.update_available for r in results)
    sys.exit(1 if updates_available else 0)


if __name__ == "__main__":
    main()
