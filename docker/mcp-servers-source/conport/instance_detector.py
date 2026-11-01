"""
SimpleInstanceDetector - Minimal Worktree Instance Detection

Purpose:
    Detect worktree instance via environment variables for multi-instance ConPort support.

Design Philosophy:
    - Dead simple: Read env vars, return values
    - Zero dependencies: No git parsing, no filesystem detection
    - Explicit over implicit: User sets env vars manually
    - Fail-safe: Returns None for single-worktree mode

Usage:
    # Single worktree (no env vars):
    detector = SimpleInstanceDetector()
    instance_id = detector.get_instance_id()  # Returns None
    workspace_id = detector.get_workspace_id()  # Returns cwd

    # Multi-worktree (env vars set):
    export DOPEMUX_INSTANCE_ID="feature-auth"
    export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
    instance_id = detector.get_instance_id()  # Returns "feature-auth"
    workspace_id = detector.get_workspace_id()  # Returns "/Users/hue/code/dopemux-mvp"
"""

import os
from typing import Optional


class SimpleInstanceDetector:
    """
    Detects worktree instance via environment variables.

    Environment Variables:
        DOPEMUX_INSTANCE_ID: Unique identifier for this worktree instance.
                            Set to None/unset for main worktree.
                            Example: "feature-auth", "hotfix-redis"

        DOPEMUX_WORKSPACE_ID: Absolute path to main workspace/repository root.
                             Falls back to current directory if not set.
                             Example: "/Users/hue/code/dopemux-mvp"

    Data Isolation Strategy:
        instance_id = None → Shared data (COMPLETED/BLOCKED tasks visible everywhere)
        instance_id = "name" → Isolated data (IN_PROGRESS/PLANNED tasks only in this worktree)
    """

    # Environment variable names
    ENV_INSTANCE_ID = "DOPEMUX_INSTANCE_ID"
    ENV_WORKSPACE_ID = "DOPEMUX_WORKSPACE_ID"

    # Wave 2A R2: a write's instance_id is request data.  The value "shared"
    # lands where NULL lands (the existing shared rows), so a caller can name
    # the shared scope explicitly instead of omitting the id.
    SHARED_INSTANCE_ID = "shared"

    @classmethod
    def normalize_instance_id(cls, value: Optional[str]) -> Optional[str]:
        """Map a request ``instance_id`` to the stored value.

        ``None``, empty and ``shared`` (any case) mean the shared scope and are
        stored as NULL; anything else is stored as given (surrounding spaces
        trimmed).
        """
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() == cls.SHARED_INSTANCE_ID:
            return None
        return text

    @classmethod
    def get_bound_workspace_id(cls) -> Optional[str]:
        """The workspace this server is bound to, from env only.

        Unlike ``get_workspace_id`` there is no cwd fallback: a write binding
        must be explicit, so an unset binding returns None and writes are
        rejected (fail closed).
        """
        return os.getenv(cls.ENV_WORKSPACE_ID) or None

    @classmethod
    def get_instance_id(cls) -> Optional[str]:
        """
        Get current worktree instance identifier.

        Returns:
            str: Instance ID if in linked worktree (e.g., "feature-auth")
            None: If in main worktree or single-worktree mode

        Examples:
            # Main worktree (no env var)
            >>> os.environ.pop('DOPEMUX_INSTANCE_ID', None)
            >>> SimpleInstanceDetector.get_instance_id()
            None

            # Linked worktree
            >>> os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'
            >>> SimpleInstanceDetector.get_instance_id()
            'feature-auth'
        """
        instance_id = os.getenv(cls.ENV_INSTANCE_ID)

        # Return None if empty string (treat as unset)
        if instance_id == "":
            return None

        return instance_id

    @classmethod
    def get_workspace_id(cls) -> str:
        """
        Get workspace identifier (main repository root).

        Returns:
            str: Absolute path to workspace root

        Fallback:
            If DOPEMUX_WORKSPACE_ID not set, uses current working directory.
            This is safe for single-worktree mode.

        Examples:
            # Explicit workspace
            >>> os.environ['DOPEMUX_WORKSPACE_ID'] = '/Users/hue/code/dopemux-mvp'
            >>> SimpleInstanceDetector.get_workspace_id()
            '/Users/hue/code/dopemux-mvp'

            # Fallback to cwd
            >>> os.environ.pop('DOPEMUX_WORKSPACE_ID', None)
            >>> SimpleInstanceDetector.get_workspace_id()
            '/current/working/directory'
        """
        workspace_id = os.getenv(cls.ENV_WORKSPACE_ID)

        if workspace_id:
            return workspace_id

        # Fallback: Use current directory
        # Safe for single-worktree mode where cwd == workspace root
        return os.getcwd()

    @classmethod
    def get_context(cls) -> dict:
        """
        Get complete worktree context (convenience method).

        Returns:
            dict: {
                'instance_id': str | None,
                'workspace_id': str,
                'is_main_worktree': bool,
                'is_multi_worktree': bool
            }

        Example:
            >>> context = SimpleInstanceDetector.get_context()
            >>> context
            {
                'instance_id': 'feature-auth',
                'workspace_id': '/Users/hue/code/dopemux-mvp',
                'is_main_worktree': False,
                'is_multi_worktree': True
            }
        """
        instance_id = cls.get_instance_id()
        workspace_id = cls.get_workspace_id()

        return {
            'instance_id': instance_id,
            'workspace_id': workspace_id,
            'is_main_worktree': instance_id is None,
            'is_multi_worktree': instance_id is not None
        }

    @classmethod
    def is_isolated_status(cls, status: str) -> bool:
        """
        Check if a status should be isolated to current instance.

        Args:
            status: Task status (PLANNED, IN_PROGRESS, COMPLETED, BLOCKED, CANCELLED)

        Returns:
            bool: True if status should be instance-isolated, False if shared

        Isolation Rules:
            - IN_PROGRESS: Isolated (active work in this worktree only)
            - PLANNED: Isolated (planned work in this worktree only)
            - COMPLETED: Shared (visible to all worktrees)
            - BLOCKED: Shared (blockers affect everyone)
            - CANCELLED: Shared (cancelled tasks visible to all)

        Examples:
            >>> SimpleInstanceDetector.is_isolated_status('IN_PROGRESS')
            True
            >>> SimpleInstanceDetector.is_isolated_status('COMPLETED')
            False
        """
        # Isolated statuses (work in progress)
        isolated_statuses = {'IN_PROGRESS', 'PLANNED'}

        # Shared statuses (completed or blocked work)
        # shared_statuses = {'COMPLETED', 'BLOCKED', 'CANCELLED'}

        return status.upper() in isolated_statuses


# Convenience functions for common use cases
SHARED_INSTANCE_ID = SimpleInstanceDetector.SHARED_INSTANCE_ID


def normalize_instance_id(value: Optional[str]) -> Optional[str]:
    """Map a request instance_id to the stored value (convenience function)."""
    return SimpleInstanceDetector.normalize_instance_id(value)


def get_bound_workspace_id() -> Optional[str]:
    """Get the explicit workspace binding for writes (convenience function)."""
    return SimpleInstanceDetector.get_bound_workspace_id()


def get_instance_id() -> Optional[str]:
    """Get current instance ID (convenience function)."""
    return SimpleInstanceDetector.get_instance_id()


def get_workspace_id() -> str:
    """Get current workspace ID (convenience function)."""
    return SimpleInstanceDetector.get_workspace_id()


def get_context() -> dict:
    """Get complete worktree context (convenience function)."""
    return SimpleInstanceDetector.get_context()


def is_isolated_status(status: str) -> bool:
    """Check if status should be isolated (convenience function)."""
    return SimpleInstanceDetector.is_isolated_status(status)
