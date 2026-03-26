from enum import Enum, auto
from typing import List, Literal, Optional

from .schema import PRState


class ConflictClass(Enum):
    MECHANICAL = auto()  # Simple import/version bumps
    GENERATED = auto()  # Lockfiles, generated code
    RERERE = auto()  # Previously resolved and recorded
    STRUCTURAL = auto()  # File moves, renames
    SEMANTIC = auto()  # Logic changes in same block
    HIGH_RISK = auto()  # Protected files, security logic


class ConflictAnalyzer:
    """Analyzes merge conflicts to determine automation safety."""

    def __init__(self):
        self.protected_paths = ["contracts/", "security/", "config/auth/"]

    def classify_conflict(
        self, pr_state: PRState, diff_context: Optional[str] = None
    ) -> ConflictClass:
        """Classify the conflict based on labels, paths, and diff (if available)."""
        if "conflict:semantic" in pr_state.labels:
            return ConflictClass.HIGH_RISK

        if "conflict:mechanical" in pr_state.labels:
            return ConflictClass.MECHANICAL

        return ConflictClass.HIGH_RISK

    def is_auto_resolvable(self, conflict_class: ConflictClass) -> bool:
        """Determine if a conflict class is safe for automated rerere path."""
        safe_classes = {
            ConflictClass.MECHANICAL,
            ConflictClass.GENERATED,
            ConflictClass.RERERE,
        }
        return conflict_class in safe_classes
