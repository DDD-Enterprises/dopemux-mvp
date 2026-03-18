"""Dopemux Voice Engine — programmatic brand copy for all surfaces.

Usage:
    from dopemux.ui.voice import VoiceMode, CopyLibrary, validate_output

    copy = CopyLibrary()
    console.print(copy.banner("extract"))
    console.print(copy.random_aftercare())
    violations = validate_output("maybe this works")
"""

from __future__ import annotations

import csv
import enum
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import yaml


class VoiceMode(enum.Enum):
    """Brand voice modes from BRAND_VOICE_BIBLE.md."""
    FILTH_DAEMON = "FilthDaemon"
    CLINICAL_FORENSICS = "ClinicalForensics"
    UX_SCOLD = "UXScold"
    UI_STRICT = "UIStrict"
    BANNER_ONE_LINER = "BannerOneLiner"
    KINK_ACCENT = "KinkAccent"


@dataclass
class VoiceViolation:
    """A voice gate violation found in output text."""
    gate_type: str          # "hard_avoid" | "soft_avoid" | "missing_closer"
    matched_text: str       # The offending text or missing element
    severity: str           # "error" | "warning"
    suggestion: str         # What to do instead


class CopyLibrary:
    """Brand copy sourced from enriched specimen ledger."""

    def __init__(self, ledger_path: Path | None = None) -> None:
        # Default: look for enriched CSV relative to repo root
        if ledger_path is None:
            ledger_path = Path(__file__).resolve().parents[3] / (
                "dopemux_voice_branding_bundle/SPECIMEN_LEDGER_ENRICHED.csv"
            )
        self._ledger_path = ledger_path
        self._specimens: dict[str, list[str]] = {}  # usable_as -> [excerpts]
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._ledger_path.exists():
            return
        with open(self._ledger_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = row.get("usable_as", "").strip()
                excerpt = row.get("excerpt", "").strip()
                if category and excerpt:
                    self._specimens.setdefault(category, []).append(excerpt)

    def random_roast(self) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("roast", [])
        return random.choice(pool) if pool else "[UXScold] You're still here? Ship something."

    def random_aftercare(self) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("aftercare", [])
        if pool:
            return random.choice(pool)
        return random.choice([
            "💧 Hydrate. You earned it.",
            "💊 Session logged. Go touch grass.",
            "🧠 Context saved. Take a break.",
            "💧 Water check. Posture check. You shipped.",
        ])

    def banner(self, command: str) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("banner", [])
        if pool:
            return random.choice(pool)
        return f"━━━◆ Ø ◆━━━  dopemux {command}"

    def error_copy(self, error_type: str) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("error", [])
        return random.choice(pool) if pool else f"[BLOCKER] {error_type}"

    def success_copy(self, action: str) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("success", [])
        return random.choice(pool) if pool else f"[LOGGED] {action}"


def _load_voice_gates() -> dict:
    """Load VOICE_GATES.yaml from the branding bundle."""
    gates_path = Path(__file__).resolve().parents[3] / (
        "dopemux_voice_branding_bundle/VOICE_GATES.yaml"
    )
    if not gates_path.exists():
        return {"lexical_gates": {}, "structure_gates": {}}
    with open(gates_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_output(text: str) -> list[VoiceViolation]:
    """Check text against VOICE_GATES.yaml. Returns list of violations."""
    gates = _load_voice_gates()
    violations: list[VoiceViolation] = []
    text_lower = text.lower()

    # Hard avoids
    for phrase in gates.get("lexical_gates", {}).get("hard_avoid_phrases", []):
        if phrase.lower() in text_lower:
            violations.append(VoiceViolation(
                gate_type="hard_avoid",
                matched_text=phrase,
                severity="error",
                suggestion=f"Remove '{phrase}'. Use direct language instead.",
            ))

    # Soft avoids
    for phrase in gates.get("lexical_gates", {}).get("soft_avoid_phrases", []):
        if phrase.lower() in text_lower:
            violations.append(VoiceViolation(
                gate_type="soft_avoid",
                matched_text=phrase,
                severity="warning",
                suggestion=f"Consider removing '{phrase}'. Too soft for dopemux voice.",
            ))

    return violations
