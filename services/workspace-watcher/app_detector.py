"""
Application Detector - OS-Specific Active App Detection

Detects which application is currently focused/frontmost.
Supports macOS (osascript) and Linux (wmctrl).

ADHD Benefit: Automatic workspace switch detection without manual tracking.
"""

import subprocess
import platform
import logging
from typing import Optional

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

    def get_active_app(self) -> Optional[str]:
        """
        Get the name of the currently active/frontmost application.

        Returns:
            Application name (e.g., "Claude Code", "Visual Studio Code")
            or None if detection fails
        """
        if IS_MACOS:
            return self._get_active_app_macos()
        elif IS_LINUX:
            return self._get_active_app_linux()
        else:
            logger.warning(f"Unsupported OS: {self.os_type}")
            return None

    def _get_active_app_macos(self) -> Optional[str]:
        """
        Get active app on macOS using AppleScript.

        Uses System Events to query frontmost process name.
        """
        try:
            # AppleScript to get frontmost application
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

        Requires wmctrl to be installed: apt-get install wmctrl
        """
        try:
            # Get active window ID
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                timeout=1.0
            )

            if result.returncode != 0:
                logger.debug("xdotool failed, trying wmctrl")
                # Fallback to wmctrl
                result = subprocess.run(
                    ["wmctrl", "-a"],
                    capture_output=True,
                    text=True,
                    timeout=1.0
                )

            if result.returncode == 0:
                # Parse window title to extract application name
                window_id = result.stdout.strip()

                # Get window name
                name_result = subprocess.run(
                    ["xdotool", "getwindowname", window_id],
                    capture_output=True,
                    text=True,
                    timeout=1.0
                )

                if name_result.returncode == 0:
                    window_title = name_result.stdout.strip()
                    # Extract app name from window title
                    # Usually format: "Title - AppName"
                    if " - " in window_title:
                        app_name = window_title.split(" - ")[-1]
                        return app_name

                    return window_title

            return None

        except subprocess.TimeoutExpired:
            logger.warning("Linux app detection timeout")
            return None
        except FileNotFoundError:
            logger.error("xdotool/wmctrl not installed")
            return None
        except Exception as e:
            logger.error(f"Linux app detection error: {e}")
            return None
