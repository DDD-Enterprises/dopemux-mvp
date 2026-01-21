"""
File Activity Checker - Detect Active Coding

Checks if code files have been recently modified to determine if user is
actively coding vs idle/reading in IDE.

ADHD Benefit: Differentiate active coding from passive IDE time for better
complexity estimation.
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class FileActivityChecker:
    """
    Checks for recent file modifications in workspace.

    Detects if user is actively coding based on file modification times.
    """

    def __init__(
        self,
        recency_threshold: int = 30,
        file_patterns: List[str] = None
    ):
        """
        Initialize file activity checker.

        Args:
            recency_threshold: Seconds since modification to consider "recent" (default: 30)
            file_patterns: File extensions to check (default: code files)
        """
        self.recency_threshold = recency_threshold
        self.file_patterns = file_patterns or [
            ".py", ".js", ".ts", ".tsx", ".jsx",
            ".go", ".rs", ".java", ".c", ".cpp",
            ".sh", ".bash", ".md", ".json", ".yaml"
        ]

    def check_recent_activity(self, workspace_path: str) -> dict:
        """
        Check if code files were recently modified in workspace.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            Dict with:
            - has_recent_activity: bool
            - files_modified: int
            - most_recent_file: str
            - seconds_since_last_save: int
        """
        if not workspace_path or workspace_path == "unknown":
            return {
                "has_recent_activity": False,
                "files_modified": 0,
                "most_recent_file": None,
                "seconds_since_last_save": None
            }

        try:
            workspace = Path(workspace_path)

            if not workspace.exists() or not workspace.is_dir():
                return {
                    "has_recent_activity": False,
                    "files_modified": 0,
                    "most_recent_file": None,
                    "seconds_since_last_save": None
                }

            current_time = time.time()
            recent_files = []

            # Check code files in workspace (non-recursive for speed)
            for pattern in self.file_patterns:
                for file in workspace.glob(f"**/*{pattern}"):
                    if file.is_file():
                        try:
                            mtime = file.stat().st_mtime
                            age = current_time - mtime

                            if age <= self.recency_threshold:
                                recent_files.append((file, age))

                        except Exception as e:
                            continue  # Skip files we can't stat

                            logger.error(f"Error: {e}")
            # Sort by age (most recent first)
            recent_files.sort(key=lambda x: x[1])

            has_activity = len(recent_files) > 0

            if has_activity:
                most_recent = recent_files[0]
                return {
                    "has_recent_activity": True,
                    "files_modified": len(recent_files),
                    "most_recent_file": str(most_recent[0].name),
                    "seconds_since_last_save": int(most_recent[1])
                }
            else:
                return {
                    "has_recent_activity": False,
                    "files_modified": 0,
                    "most_recent_file": None,
                    "seconds_since_last_save": None
                }

        except Exception as e:
            logger.debug(f"File activity check failed: {e}")
            return {
                "has_recent_activity": False,
                "files_modified": 0,
                "most_recent_file": None,
                "seconds_since_last_save": None
            }
