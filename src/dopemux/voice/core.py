"""Deterministic Dopemux voice gates and mode selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any
import re

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


class Surface(str, Enum):
    """Supported voice validation surfaces."""

    CLI = "cli"
    AGENT = "agent"
    UI = "ui"


class VoiceMode(str, Enum):
    """Deterministic voice modes derived from the brand artifacts."""

    FILTH_DAEMON = "FilthDaemon"
    CLINICAL_FORENSICS = "ClinicalForensics"
    CYBERPUNK_MEDIC = "CyberpunkMedic"
    UX_SCOLD = "UXScold"
    BANNER = "BannerOneLiner"
    BANNER_ONE_LINER = "BannerOneLiner"
    UI_STRICT = "UIStrict"
    KINK_ACCENT = "KinkAccent"


@dataclass(frozen=True)
class GateViolation:
    """Single gate failure."""

    code: str
    message: str


@dataclass(frozen=True)
class GateResult:
    """Structured validation result."""

    ok: bool
    violations: list[GateViolation]


DEFAULT_GATES: dict[str, Any] = {
    "lexical_gates": {
        "hard_avoid_phrases": [
            "as an ai",
            "probably",
            "maybe",
            "generally speaking",
        ],
        "soft_avoid_phrases": [
            "no worries",
            "it's okay",
            "don't worry",
            "hope you're doing well",
        ],
        "required_closers": ["NEXT:", "Next:", "Receipt:", "PROGRESS"],
    },
    "structure_gates": {
        "require_fact_inference_split_for_nontrivial_claims": True,
        "require_unknown_todo_instead_of_guessing": True,
    },
}

MODE_RULES = [
    (
        VoiceMode.CLINICAL_FORENSICS,
        re.compile(
            r"\b(privacy|security|redact|redaction|residency|provenance|shield|coverage|hardfail|threshold)\b",
            re.IGNORECASE,
        ),
    ),
    (
        VoiceMode.FILTH_DAEMON,
        re.compile(r"\b(drift|untagged|missing field|schema mismatch|hallucination)\b", re.IGNORECASE),
    ),
    (
        VoiceMode.UX_SCOLD,
        re.compile(
            r"\b(best practices|stuck|vague|open tabs|stale context|neglect|procrastination)\b",
            re.IGNORECASE,
        ),
    ),
]

_HEDGE_RE = re.compile(r"\b(probably|maybe|generally speaking|it seems)\b", re.IGNORECASE)
_AI_DISCLAIMER_RE = re.compile(r"\bas an ai\b", re.IGNORECASE)
_UI_TONE_RE = re.compile(r"\b(public shame|roast escalation|shame you)\b", re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_gates_path() -> Path:
    return _repo_root() / "dopemux_voice_branding_bundle" / "VOICE_GATES.yaml"


def _merge_gates(data: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "lexical_gates": dict(DEFAULT_GATES["lexical_gates"]),
        "structure_gates": dict(DEFAULT_GATES["structure_gates"]),
    }
    for section, payload in data.items():
        if isinstance(payload, dict) and isinstance(merged.get(section), dict):
            merged[section].update(payload)
        else:
            merged[section] = payload
    return merged


@lru_cache(maxsize=8)
def _load_voice_gates_cached(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    if not path.exists() or yaml is None:
        return _merge_gates({})
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return _merge_gates({})
    return _merge_gates(data)


def load_voice_gates(gates_path: Path | None = None) -> dict[str, Any]:
    """Load gates from the canonical artifact path with fail-closed defaults."""
    path = (gates_path or _default_gates_path()).resolve()
    return _load_voice_gates_cached(str(path))


def select_mode(surface: Surface, intent_text: str) -> VoiceMode:
    """Choose a deterministic mode from surface and intent."""
    if surface is Surface.UI:
        return VoiceMode.UI_STRICT

    stripped = intent_text.strip()
    for mode, pattern in MODE_RULES:
        if pattern.search(intent_text):
            return mode

    if stripped and len(stripped) <= 40:
        return VoiceMode.BANNER

    return VoiceMode.FILTH_DAEMON


def _contains_any(text: str, phrases: list[str]) -> str | None:
    lowered = text.lower()
    for phrase in phrases:
        if phrase.lower() in lowered:
            return phrase
    return None


def _has_required_closer(text: str, required: list[str]) -> bool:
    stripped = text.strip()
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    markdown_lines = [line.lstrip("#").strip() for line in lines]
    for token in required:
        if stripped.endswith(token):
            return True
        if any(line.startswith(token) for line in lines):
            return True
        base = token.rstrip(":")
        if any(line == base for line in markdown_lines):
            return True
        if any(line.startswith(f"{base}:") for line in markdown_lines):
            return True
    return False


def validate_output(
    surface: Surface,
    mode: VoiceMode,
    text: str,
    gates: dict[str, Any] | None = None,
) -> GateResult:
    """Validate output against lexical and structural voice gates."""
    del mode
    config = gates or load_voice_gates()
    violations: list[GateViolation] = []
    lexical = config.get("lexical_gates", {})
    hard = lexical.get("hard_avoid_phrases", [])
    soft = lexical.get("soft_avoid_phrases", [])
    closers = lexical.get("required_closers", [])

    hit = _contains_any(text, hard)
    if hit:
        violations.append(
            GateViolation("LEX_HARD_AVOID", f'Contains hard-avoid phrase: "{hit}"')
        )

    hit = _contains_any(text, soft)
    if hit:
        violations.append(
            GateViolation("LEX_SOFT_AVOID", f'Contains soft-avoid phrase: "{hit}"')
        )

    if surface in (Surface.CLI, Surface.AGENT) and not _has_required_closer(text, closers):
        violations.append(
            GateViolation(
                "MISSING_CLOSER",
                "CLI and agent surfaces must include NEXT:/Receipt:/PROGRESS.",
            )
        )

    if surface is Surface.UI:
        if not all(field in text for field in ("label:", "message:", "action:")):
            violations.append(
                GateViolation(
                    "UI_SHAPE",
                    "UI output must include label:/message:/action: fields.",
                )
            )
        if _UI_TONE_RE.search(text):
            violations.append(
                GateViolation(
                    "UI_TONE",
                    "UI output must not use public shame or roast-escalation language.",
                )
            )

    if _AI_DISCLAIMER_RE.search(text) or _HEDGE_RE.search(text):
        violations.append(
            GateViolation(
                "HEDGE",
                "Hedging or AI disclaimer detected; use UNKNOWN+TODO instead.",
            )
        )

    return GateResult(ok=not violations, violations=violations)


def build_rewrite_instruction(violations: list[GateViolation]) -> str:
    """Build a single deterministic rewrite instruction from gate failures."""
    details = "\n".join(f"- {item.code}: {item.message}" for item in violations)
    return (
        "DRIFT ALERT: voice gates failed.\n"
        "Fix violations and rewrite once. Do not add fluff.\n"
        "Violations:\n"
        f"{details}\n"
    )


__all__ = [
    "DEFAULT_GATES",
    "GateResult",
    "GateViolation",
    "Surface",
    "VoiceMode",
    "build_rewrite_instruction",
    "load_voice_gates",
    "select_mode",
    "validate_output",
]
