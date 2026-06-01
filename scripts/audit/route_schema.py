"""Audit route dataclass and constants for the auditor router."""
from __future__ import annotations

from dataclasses import dataclass, field

# CLI names that are never permitted as formal auditors.
# Codex is excluded because embedded_audit.schema.json auditor_tool enum
# does not include it, and the operator has not authorized schema changes.
FORBIDDEN_CLI_NAMES: frozenset[str] = frozenset({"codex", "codex-audit"})


@dataclass(frozen=True)
class AuditRoute:
    """A single auditor CLI route entry in the route registry.

    Attributes:
        cli_name:        Logical name matching the PAL clink config (e.g. "claude-audit").
        command:         Executable to probe for on PATH (e.g. "claude").
        priority:        Selection priority; lower value = higher preference.
        additional_args: Extra CLI arguments passed verbatim.
        env:             Extra environment variables for the invocation.
        role:            PAL clink role name to activate (default "codereviewer").
    """

    cli_name: str
    command: str
    priority: int = 0
    additional_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    role: str = "codereviewer"

    def __post_init__(self) -> None:
        if self.cli_name in FORBIDDEN_CLI_NAMES:
            raise ValueError(
                f"Forbidden auditor CLI: {self.cli_name!r}. "
                f"Not in embedded_audit.schema.json auditor_tool enum."
            )
        if not self.cli_name:
            raise ValueError("cli_name must be non-empty")
        if not self.command:
            raise ValueError("command must be non-empty")
        if self.priority < 0:
            raise ValueError("priority must be >= 0")
