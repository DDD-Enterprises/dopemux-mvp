"""
Application Detector - OS-Specific Active App Detection

Detects which application is currently focused/frontmost.
Supports macOS (osascript) and Linux (wmctrl).
"""

import subprocess
import platform
import asyncio
from typing import Optional

import logging
logger = logging.getLogger(__name__)

IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


class AppDetector:
    """
    Detects currently active application across different operating systems.
    """

    def __init__(self):
        """Initialize app detector with OS-specific implementation"""
        self.os_type = platform.system()
        logger.info(f"App detector initialized for {self.os_type}")

    async def get_active_app_async(self) -> Optional[str]:
        """
        Async version of get_active_app.

        Uses thread pool execution to avoid blocking async event loops.
        """
        if IS_MACOS:
            return await self._get_active_app_macos_async()
        elif IS_LINUX:
            # Linux version is already async-compatible
            return self._get_active_app_linux()
        else:
            logger.warning(f"Unsupported OS: {self.os_type}")
            return None

    def get_active_app(self) -> Optional[str]:
        """
        Get the name of the currently active/frontmost application.
        """
        if IS_MACOS:
            return self._get_active_app_macos()
        elif IS_LINUX:
            return self._get_active_app_linux()
        else:
            logger.warning(f"Unsupported OS: {self.os_type}")
            return None

    async def _get_active_app_macos_async(self) -> Optional[str]:
        """
        Get active app on macOS using AppleScript (async version).
        """
        try:
            import asyncio

            # AppleScript to get frontmost application
            script = 'tell application "System Events" to get name of first process whose frontmost is true'

            # Run subprocess in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=1.0
                )
            )

            if result.returncode == 0:
                app_name = result.stdout.strip()
                return app_name if app_name else None
            else:
                logger.debug(f"osascript failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.warning("osascript timeout")
            return None
        except Exception as e:
            logger.error(f"macOS app detection error: {e}")
            return None

    def _get_active_app_macos(self) -> Optional[str]:
        """
        Get active app on macOS using AppleScript (sync version).
        """
        try:
            script = 'tell application "System Events" to get name of first process whose frontmost is true'

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=1.0
            )

            if result.returncode == 0:
                app_name = result.stdout.strip()
                return app_name if app_name else None
            else:
                logger.debug(f"osascript failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.warning("osascript timeout")
            return None
        except Exception as e:
            logger.error(f"macOS app detection error: {e}")
            return None

    def _get_active_app_linux(self) -> Optional[str]:
        """
        Get active app on Linux using wmctrl.
        """
        try:
            result = subprocess.run(
                ["wmctrl", "-m"],
                capture_output=True,
                text=True,
                timeout=1.0
            )

            if result.returncode == 0:
                # Parse wmctrl output to get active window
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Name:' in line:
                        app_name = line.split('Name:')[1].strip()
                        return app_name if app_name else None

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("wmctrl not available or timeout")
            return None
        except Exception as e:
            logger.error(f"Linux app detection error: {e}")
            return None