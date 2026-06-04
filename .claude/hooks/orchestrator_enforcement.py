"""
Orchestrator PreToolUse / PostToolUse enforcement helpers.

Dopemux-adapted port of two upstream claude-plugins/task-orchestrator hooks
(jpicklyk/task-orchestrator @ main):
  - hooks/enforce-actor-attribution.mjs  -> actor_attribution_block(...)
  - hooks/skill-enforcement.mjs          -> skill_enforcement_warnings(...)
plus the plan-mode guidance texts from hooks/pre-plan.mjs + hooks/post-plan.mjs.

Public functions used by native_hooks.py:
  find_orchestrator_config(start)            -> str | None
  actor_authentication_enabled(config_text)  -> bool
  actor_attribution_violation(tool, input)   -> bool
  actor_attribution_block(tool, input, cfg)  -> str | None   (block reason)
  note_skill_map(config_text)                -> dict[str, str]
  skill_enforcement_warnings(tool, input, cfg) -> list[str]

Design notes:
  - Tool-name matching uses substring checks, so it is prefix-agnostic and works
    for both `mcp__task-orchestrator__*` (Dopemux) and the upstream
    `mcp__mcp-task-orchestrator__*` prefix.
  - Config parsing uses PyYAML (yaml.safe_load); absence/parse errors fail safe
    (disabled / empty map). A missing `actor_authentication` block means the
    actor check is dormant — enabling it is a separate, ADR-gated config edit.
  - All functions are pure and never raise; hook failures must not block work.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover - PyYAML is a project dependency
    yaml = None  # type: ignore[assignment]

_CONFIG_RELPATH = (".taskorchestrator", "config.yaml")

# A note body shorter than this (and matching no real content) is treated as
# non-substantive — i.e., the skill framework was likely not followed.
MIN_SUBSTANTIVE_LENGTH = 200

# Patterns that indicate a placeholder note body (skill framework NOT followed).
# Ported from the upstream skill-enforcement.mjs PLACEHOLDER_PATTERNS.
_PLACEHOLDER_PATTERNS = [
    re.compile(r"^n/?a$", re.IGNORECASE),
    re.compile(r"^looks?\s+(fine|good|ok)", re.IGNORECASE),
    re.compile(r"^no\s+issues?\s*(found)?", re.IGNORECASE),
    re.compile(r"^todo$", re.IGNORECASE),
    re.compile(r"^placeholder$", re.IGNORECASE),
    re.compile(r"^tbd$", re.IGNORECASE),
    re.compile(r"^pending$", re.IGNORECASE),
    re.compile(r"^will\s+fill\s+(later|soon)", re.IGNORECASE),
]

PRE_PLAN_GUIDANCE = """\
## PREREQUISITE — task-orchestrator plan-mode entry

Before exploring the codebase or drafting a plan, run the `/dx:plan-enter` command to
establish the orchestrator work-item context (active items, gates, what this plan must
materialize). Do this now — do not begin exploring or writing the plan until it completes.
"""

POST_PLAN_GUIDANCE = """\
## NEXT STEP — task-orchestrator plan-mode exit

The plan is approved. Run `/dx:plan-exit` NOW to materialize the orchestrator work-items
(create_work_tree) and dispatch implementation before writing any code.
"""

ACTOR_ATTRIBUTION_BLOCK_REASON = (
    'Actor authentication is enabled — actor attribution required. Include an "actor" object '
    'with "id" (string) and "kind" (orchestrator|subagent|user|external) on every '
    'transition/note element. For subagents, include "parent" with the dispatching agent\'s id.'
)


def find_orchestrator_config(start: Path) -> Optional[str]:
    """Locate and read `.taskorchestrator/config.yaml`.

    Checks the AGENT_CONFIG_DIR env first, then walks up from `start` to the
    filesystem root. Worktree-safe: handles a cwd nested under
    `.claude/worktrees/<name>/` whose config lives at the repo root.
    Returns the file text, or None if not found / unreadable.
    """
    candidates: List[Path] = []
    env_dir = os.environ.get("AGENT_CONFIG_DIR")
    if env_dir:
        candidates.append(Path(env_dir).joinpath(*_CONFIG_RELPATH))

    try:
        current = Path(start).resolve()
    except Exception:
        return None
    for directory in [current, *current.parents]:
        candidates.append(directory.joinpath(*_CONFIG_RELPATH))

    for candidate in candidates:
        try:
            return candidate.read_text(encoding="utf-8")
        except (OSError, ValueError):
            continue
    return None


def _safe_load(config_text: Optional[str]) -> Any:
    if not config_text or yaml is None:
        return None
    try:
        return yaml.safe_load(config_text)
    except Exception:
        return None


def actor_authentication_enabled(config_text: Optional[str]) -> bool:
    """True only when `actor_authentication.enabled` is explicitly true."""
    data = _safe_load(config_text)
    if not isinstance(data, dict):
        return False
    section = data.get("actor_authentication")
    if not isinstance(section, dict):
        return False
    return section.get("enabled") is True


def actor_attribution_violation(tool_name: str, tool_input: Dict[str, Any]) -> bool:
    """True when an advance_item / manage_notes(upsert) call omits `actor`.

    advance_item: any element of `transitions` missing a truthy `actor`.
    manage_notes upsert: any element of `notes` missing a truthy `actor`.
    Other tools never violate.
    """
    tool_name = tool_name or ""
    tool_input = tool_input or {}

    is_advance = "advance_item" in tool_name
    is_note_upsert = "manage_notes" in tool_name and tool_input.get("operation") == "upsert"
    if not is_advance and not is_note_upsert:
        return False

    if is_advance:
        elements = tool_input.get("transitions") or []
    else:
        elements = tool_input.get("notes") or []
    if not isinstance(elements, list):
        return False
    return any(not (isinstance(el, dict) and el.get("actor")) for el in elements)


def actor_attribution_block(
    tool_name: str, tool_input: Dict[str, Any], config_text: Optional[str]
) -> Optional[str]:
    """Return a block reason when actor auth is enabled AND attribution is missing.

    Returns None (allow) when actor auth is disabled/absent or attribution is present.
    """
    if not actor_authentication_enabled(config_text):
        return None
    if actor_attribution_violation(tool_name, tool_input):
        return ACTOR_ATTRIBUTION_BLOCK_REASON
    return None


def _collect_skill_map(node: Any, out: Dict[str, str]) -> None:
    """Recursively collect {note-key: skill} from any dict carrying both fields."""
    if isinstance(node, dict):
        key = node.get("key")
        skill = node.get("skill")
        if isinstance(key, str) and isinstance(skill, str) and skill.strip():
            out[key] = skill  # last-writer-wins, matching upstream semantics
        for value in node.values():
            _collect_skill_map(value, out)
    elif isinstance(node, list):
        for item in node:
            _collect_skill_map(item, out)


def note_skill_map(config_text: Optional[str]) -> Dict[str, str]:
    """Map note key -> required skill, from any schema/trait note carrying `skill:`."""
    data = _safe_load(config_text)
    out: Dict[str, str] = {}
    _collect_skill_map(data, out)
    return out


def _is_placeholder(body: str) -> bool:
    return any(p.match(body) for p in _PLACEHOLDER_PATTERNS)


def skill_enforcement_warnings(
    tool_name: str, tool_input: Dict[str, Any], config_text: Optional[str]
) -> List[str]:
    """Warn when a manage_notes(upsert) fills a skill-gated note with a thin body.

    Non-blocking: the upstream hook injects context (exit 0), it does not deny.
    A warning fires when the note's key carries a `skill:` pointer AND the body
    is empty, shorter than MIN_SUBSTANTIVE_LENGTH, or a placeholder phrase.
    """
    tool_name = tool_name or ""
    tool_input = tool_input or {}
    if "manage_notes" not in tool_name or tool_input.get("operation") != "upsert":
        return []
    notes = tool_input.get("notes")
    if not isinstance(notes, list) or not notes:
        return []

    skill_map = note_skill_map(config_text)
    if not skill_map:
        return []

    warnings: List[str] = []
    for note in notes:
        if not isinstance(note, dict):
            continue
        key = note.get("key")
        if not key or key not in skill_map:
            continue
        body = (note.get("body") or "").strip()
        too_short = len(body) < MIN_SUBSTANTIVE_LENGTH
        placeholder = too_short and _is_placeholder(body)
        if not body or too_short or placeholder:
            skill = skill_map[key]
            warnings.append(
                f"⊘ SKILL REQUIRED — the note \"{key}\" requires the /{skill} skill framework.\n"
                f"Before filling it, invoke the Skill tool with skill=\"{skill}\" and follow its "
                f"structured evaluation. A note produced without the skill framework will not meet "
                f"the quality bar. Abort this call, invoke the skill, then retry with substantive findings."
            )
    return warnings
