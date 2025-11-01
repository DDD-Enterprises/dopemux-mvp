"""
File Activity Checker - Detects Recent File Modifications

Checks for recent file activity in workspace directories.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import logging
logger = logging.getLogger(__name__)


class FileActivityChecker:
    """
    Checks for recent file activity in workspace directories.

    Detects recently modified files to provide context about workspace activity.
    """

    def __init__(self, recency_threshold: int = 30):
        """
        Initialize file activity checker.

        Args:
            recency_threshold: Seconds threshold for "recent" activity
        """
        self.recency_threshold = recency_threshold

    def check_recent_activity(self, workspace_path: str) -> Dict:
        """
        Check for recent file activity in workspace.

        Args:
            workspace_path: Path to workspace directory

        Returns:
            Dict with activity information
        """
        try:
            workspace = Path(workspace_path)
            if not workspace.exists() or not workspace.is_dir():
                return {
                    "has_recent_activity": False,
                    "files_modified": 0,
                    "seconds_since_last_save": None,
                    "error": "Workspace path does not exist or is not a directory"
                }

            # Find recently modified files
            recent_files = []
            current_time = time.time()

            # Common file extensions to check
            extensions = ['.py', '.js', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.md', '.txt', '.json', '.yaml', '.yml']

            for ext in extensions:
                for file_path in workspace.rglob(f"*{ext}"):
                    if file_path.is_file():
                        try:
                            stat = file_path.stat()
                            if current_time - stat.st_mtime <= self.recency_threshold:
                                recent_files.append({
                                    "path": str(file_path.relative_to(workspace)),
                                    "modified_time": stat.st_mtime,
                                    "seconds_ago": current_time - stat.st_mtime
                                })
                        except (OSError, PermissionError):
                            # Skip files we can't access
                            continue

            # Sort by modification time (most recent first)
            recent_files.sort(key=lambda x: x["modified_time"], reverse=True)

            has_activity = len(recent_files) > 0
            last_save_seconds = recent_files[0]["seconds_ago"] if recent_files else None

            return {
                "has_recent_activity": has_activity,
                "files_modified": len(recent_files),
                "seconds_since_last_save": last_save_seconds,
                "recent_files": recent_files[:5]  # Top 5 most recent
            }

        except Exception as e:
            logger.error(f"Error checking file activity in {workspace_path}: {e}")
            return {
                "has_recent_activity": False,
                "files_modified": 0,
                "seconds_since_last_save": None,
                "error": str(e)
            }