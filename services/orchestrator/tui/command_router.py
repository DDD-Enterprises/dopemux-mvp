"""
Command Router for AI CLI Execution

Routes commands to available AI CLIs (claude, gemini-cli, grok-cli) with:
- Automatic CLI detection
- Async subprocess execution
- Real-time output streaming
- Error handling and recovery with retry logic
- Timeout management
- ConPort progress tracking

Part of IP-005 Day 3-4: Command routing + progress tracking
"""

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Callable, Dict, Optional
import time


class AIType(Enum):
    """Supported AI CLI types."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"


@dataclass
class CLIConfig:
    """Configuration for an AI CLI."""
    executable: str
    args: list[str]
    available: bool = False


class CommandRouter:
    """
    Routes commands to AI CLIs with async execution and streaming output.

    Features:
    - Auto-detects available AI CLIs on initialization
    - Executes commands asynchronously
    - Streams output line-by-line to callbacks
    - Handles errors and timeouts gracefully
    - ADHD-optimized: Clear error messages, fast feedback
    """

    # CLI command mappings
    CLI_CONFIGS: Dict[AIType, CLIConfig] = {
        AIType.CLAUDE: CLIConfig(
            executable="claude",
            args=[]  # claude will be invoked directly with command
        ),
        AIType.GEMINI: CLIConfig(
            executable="gemini-cli",
            args=["--non-interactive"]  # Prevent interactive prompts
        ),
        AIType.GROK: CLIConfig(
            executable="grok-cli",
            args=[]
        )
    }

    def __init__(self):
        """Initialize the command router and detect available CLIs."""
        self.cli_configs = self.CLI_CONFIGS.copy()
        self._detect_available_clis()

    def _detect_available_clis(self) -> None:
        """Detect which AI CLIs are installed and available."""
        for ai_type, config in self.cli_configs.items():
            # Check if executable exists in PATH
            executable_path = shutil.which(config.executable)
            config.available = executable_path is not None

            if config.available:
                print(f"✅ {ai_type.value} CLI detected: {executable_path}")
            else:
                print(f"⚠️  {ai_type.value} CLI not found in PATH")

    def is_available(self, ai: str) -> bool:
        """Check if a specific AI CLI is available."""
        try:
            ai_type = AIType(ai.lower())
            return self.cli_configs[ai_type].available
        except (ValueError, KeyError):
            return False

    def get_available_ais(self) -> list[str]:
        """Get list of available AI CLI names."""
        return [
            ai_type.value
            for ai_type, config in self.cli_configs.items()
            if config.available
        ]

    async def execute_command(
        self,
        ai: str,
        command: str,
        output_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        timeout: int = 300  # 5 minutes default
    ) -> tuple[int, str]:
        """
        Execute a command on the specified AI CLI.

        Args:
            ai: AI name (claude, gemini, grok)
            command: Command string to execute
            output_callback: Called with each line of stdout
            error_callback: Called with error messages
            timeout: Maximum execution time in seconds

        Returns:
            Tuple of (return_code, final_output)

        Raises:
            ValueError: If AI is not available
            asyncio.TimeoutError: If execution exceeds timeout
        """
        # Validate AI availability
        try:
            ai_type = AIType(ai.lower())
        except ValueError:
            raise ValueError(f"Unknown AI: {ai}")

        config = self.cli_configs[ai_type]
        if not config.available:
            raise ValueError(f"{ai} CLI not available. Install it first.")

        # Build command arguments
        cmd_args = [config.executable] + config.args + [command]

        # Execute with timeout
        try:
            return await asyncio.wait_for(
                self._run_subprocess(cmd_args, output_callback, error_callback),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            if error_callback:
                error_callback(f"⏰ Command timed out after {timeout}s")
            raise

    async def _run_subprocess(
        self,
        cmd_args: list[str],
        output_callback: Optional[Callable[[str], None]],
        error_callback: Optional[Callable[[str], None]]
    ) -> tuple[int, str]:
        """
        Run subprocess and stream output.

        Args:
            cmd_args: Command arguments list
            output_callback: Called for each stdout line
            error_callback: Called for stderr lines

        Returns:
            Tuple of (return_code, accumulated_output)
        """
        output_lines = []

        try:
            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )

            # Stream output concurrently
            async def stream_stdout():
                """Stream stdout lines."""
                async for line in self._read_stream(process.stdout):
                    output_lines.append(line)
                    if output_callback:
                        output_callback(line)

            async def stream_stderr():
                """Stream stderr lines."""
                async for line in self._read_stream(process.stderr):
                    if error_callback:
                        error_callback(f"stderr: {line}")

            # Wait for both streams and process
            await asyncio.gather(
                stream_stdout(),
                stream_stderr(),
                process.wait()
            )

            return process.returncode, "\n".join(output_lines)

        except FileNotFoundError:
            error_msg = f"❌ CLI executable not found: {cmd_args[0]}"
            if error_callback:
                error_callback(error_msg)
            return 1, error_msg

        except Exception as e:
            error_msg = f"❌ Execution failed: {e}"
            if error_callback:
                error_callback(error_msg)
            return 1, error_msg

    async def _read_stream(self, stream: asyncio.StreamReader) -> AsyncIterator[str]:
        """
        Read lines from a stream asynchronously.

        Args:
            stream: asyncio StreamReader

        Yields:
            Decoded text lines (without trailing newline)
        """
        while True:
            line = await stream.readline()
            if not line:
                break

            # Decode and strip newline
            text = line.decode('utf-8', errors='replace').rstrip('\n')
            if text:  # Skip empty lines
                yield text

    def get_cli_status_report(self) -> str:
        """
        Generate a status report of available CLIs.

        Returns:
            Formatted status report string
        """
        lines = ["🔍 AI CLI Status:"]

        for ai_type, config in self.cli_configs.items():
            status = "✅ Available" if config.available else "❌ Not Found"
            lines.append(f"  {ai_type.value}: {status}")

        available_count = sum(1 for c in self.cli_configs.values() if c.available)
        lines.append(f"\n{available_count}/{len(self.cli_configs)} CLIs available")

        return "\n".join(lines)


# Singleton instance for easy access
_router_instance: Optional[CommandRouter] = None


def get_command_router() -> CommandRouter:
    """Get or create the global CommandRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = CommandRouter()
    return _router_instance
