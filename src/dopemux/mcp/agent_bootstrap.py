"""Agent bootstrap doc generation for worktree MCP setup.

Writes/updates ``.claude/WORKTREE_MCP_SETUP.md`` using marked sections only.
Never mutates ``~/.claude.json`` or starts containers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BEGIN_MARKER = "<!-- BEGIN DOPEMUX MCP SETUP -->"
END_MARKER = "<!-- END DOPEMUX MCP SETUP -->"
DEFAULT_RELATIVE_PATH = ".claude/WORKTREE_MCP_SETUP.md"


def default_agent_doc_path(repo: Path | str) -> Path:
    return Path(repo).expanduser().resolve() / DEFAULT_RELATIVE_PATH


def bootstrap_section_body() -> str:
    """Canonical marked-section body (without markers)."""
    return """# Worktree MCP Setup

## Purpose

Safe, reversible MCP config and lifecycle for this worktree. Dopemux coordinates
MCP startup and local config; it is not ConPort, dope-memory, task-orchestrator,
bridge, PM, or chronicle authority.

## Session Start

```bash
source .envrc.dopemux-mcp
dopemux mcp doctor
```

If services are not running:

```bash
dopemux mcp start
dopemux mcp doctor
```

## Healthy Sequence

```bash
dopemux mcp init                 # once per worktree (scaffolds config)
dopemux mcp repair-config --dry-run
dopemux mcp repair-config --apply
dopemux mcp start
source .envrc.dopemux-mcp
dopemux mcp doctor
```

## Doctor / Start / Stop

```bash
dopemux mcp doctor --repo .
dopemux mcp start --repo .
dopemux mcp status --repo .
dopemux mcp stop --repo .
```

## Do Not Run

Do not start this repo's MCP services by cd'ing into `dopemux-mvp` and injecting
this repo's env into `docker compose up`.

Do not replace global ConPort with local ConPort.

Do not treat a listening port as healthy unless `dopemux mcp doctor` proves ownership.

Do not run `dopemux mcp sync-globals` unless you intentionally want to change
`~/.claude.json` singletons. `repair-config` never mutates globals.

## Authority

| Surface | Authority |
|---------|-----------|
| Dopemux | MCP lifecycle / local config coordination only |
| ConPort | Structured context (decisions, progress, KG) |
| dope-memory | Chronicle / historical receipts |
| task-orchestrator | Workflow views and transitions |
| dopecon-bridge | Proxy / adapter only — not canonical writer |

## Limitations (honest)

* Port allocation uses hash `% 100` — collision risk across many worktrees
  (`PORT_HASH_BUCKET_COLLISION_RISK`). Live free-port rebind is not implemented.
* `task-orchestrator` uses fixed port `7890` (wrapper-singleton).
* Unlabeled existing containers are not adopted automatically.
* Cross-worktree port lease registry is a future packet (RUNTIME-004).

## Evidence Capture

When debugging MCP setup, capture:

1. `dopemux mcp doctor --json` (or `--repo <path> --json`)
2. `dopemux mcp repair-config --dry-run --json`
3. `dopemux mcp status --json`
4. Exit codes and paths only — never paste secrets or `.env` tokens
"""


def wrap_marked_section(body: str | None = None) -> str:
    content = (body if body is not None else bootstrap_section_body()).rstrip() + "\n"
    return f"{BEGIN_MARKER}\n{content}{END_MARKER}\n"


@dataclass
class AgentBootstrapPlan:
    path: Path
    kind: str  # create | update | append | noop
    reason: str
    before_exists: bool
    content: str
    safe: bool = True

    def to_change_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "kind": self.kind if self.kind != "noop" else "noop",
            "reason": self.reason,
            "service": None,
            "before": {"exists": self.before_exists},
            "after": {"kind": self.kind},
            "safe": self.safe,
        }


def plan_agent_bootstrap(repo: Path | str, *, doc_path: Optional[Path] = None) -> AgentBootstrapPlan:
    """Plan idempotent update of the agent bootstrap doc."""
    path = Path(doc_path) if doc_path is not None else default_agent_doc_path(repo)
    desired = wrap_marked_section()

    if not path.exists():
        return AgentBootstrapPlan(
            path=path,
            kind="create",
            reason="AGENT_BOOTSTRAP_CREATED",
            before_exists=False,
            content=desired,
        )

    text = path.read_text(encoding="utf-8")
    if BEGIN_MARKER in text and END_MARKER in text:
        begin = text.index(BEGIN_MARKER)
        end = text.index(END_MARKER) + len(END_MARKER)
        # Preserve trailing newline after end marker if present
        after_end = end
        if after_end < len(text) and text[after_end] == "\n":
            after_end += 1
        new_text = text[:begin] + desired
        if after_end < len(text):
            # Ensure separation if remaining content
            if not new_text.endswith("\n"):
                new_text += "\n"
            new_text += text[after_end:].lstrip("\n")
            if text[after_end:] and not new_text.endswith("\n"):
                new_text += "\n"
        if new_text == text:
            return AgentBootstrapPlan(
                path=path,
                kind="noop",
                reason="AGENT_BOOTSTRAP_NOOP",
                before_exists=True,
                content=text,
            )
        return AgentBootstrapPlan(
            path=path,
            kind="update",
            reason="AGENT_BOOTSTRAP_UPDATED",
            before_exists=True,
            content=new_text if new_text.endswith("\n") else new_text + "\n",
        )

    # File exists without markers — append bounded section
    prefix = text if text.endswith("\n") else text + "\n"
    return AgentBootstrapPlan(
        path=path,
        kind="append",
        reason="AGENT_BOOTSTRAP_UPDATED",
        before_exists=True,
        content=prefix + "\n" + desired,
    )


def apply_agent_bootstrap(plan: AgentBootstrapPlan) -> None:
    """Write the planned agent bootstrap doc. No-op when kind is noop."""
    if plan.kind == "noop":
        return
    plan.path.parent.mkdir(parents=True, exist_ok=True)
    tmp = plan.path.with_suffix(plan.path.suffix + ".tmp")
    tmp.write_text(plan.content, encoding="utf-8")
    tmp.replace(plan.path)


def verify_bootstrap_content(text: str) -> List[str]:
    """Return list of missing required phrases (empty = ok)."""
    required = [
        "dopemux mcp start",
        "dopemux mcp doctor",
        "dopemux mcp stop",
        "Do not start this repo's MCP services by cd'ing into `dopemux-mvp`",
        "Authority",
        "ConPort",
        "dope-memory",
        "task-orchestrator",
    ]
    missing = [r for r in required if r not in text]
    return missing
