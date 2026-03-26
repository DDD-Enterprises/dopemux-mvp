"""
Dopemux Brand System — Voice and Tone Engine.
Phase 1: Thematic Persona Engine (Merged Opus + Specialist).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import List, Set

from .theme import StatusChip, Glyphs
from ..voice.core import (
    Surface,
    VoiceMode,
    load_voice_gates as core_load_voice_gates,
    select_mode as core_select_mode,
    validate_output as core_validate_output,
)


class Specimen:
    """A single brand specimen from the ledger."""

    def __init__(self, id: str, excerpt: str, tags: Set[str], affinity: float):
        self.id = id
        self.excerpt = excerpt
        self.tags = tags
        self.affinity = affinity


class VoiceEngine:
    """
    Stateful engine that produces brand-aligned copy and visuals.
    Adjusts output based on user's cognitive load (ADHD state).
    """

    def __init__(
        self, 
        mode: VoiceMode = VoiceMode.CLINICAL_FORENSICS,
        is_scattered: bool = False
    ):
        self.mode = mode
        self.is_scattered = is_scattered
        self.specimens: List[Specimen] = []
        self._load_ledger()

    def _load_ledger(self):
        """Load the 184-specimen enriched ledger."""
        ledger_path = Path("dopemux_voice_branding_bundle/SPECIMEN_LEDGER_ENRICHED.csv")
        if not ledger_path.exists():
            return

        try:
            with open(ledger_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.specimens.append(Specimen(
                        id=row['specimen_id'],
                        excerpt=row['excerpt'],
                        tags=set(row['context_tags'].split('|') if row['context_tags'] else []),
                        affinity=float(row.get('brand_affinity', 0.5))
                    ))
        except Exception:
            pass

    def _deterministic_excerpt(self, pool: List[Specimen], *, seed: str, fallback: str) -> str:
        if not pool:
            return fallback
        ordered = sorted(pool, key=lambda specimen: (specimen.id, specimen.excerpt))
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % len(ordered)
        return ordered[index].excerpt

    def get_roast(self) -> str:
        """Get a deterministic self-aware or user-facing roast."""
        roasts = [s for s in self.specimens if 'roast' in s.tags or 'UXScold' in s.tags]
        return self._deterministic_excerpt(
            roasts,
            seed=f"roast:{self.mode.value}:{int(self.is_scattered)}",
            fallback="You're still here? Ship something.",
        )

    def get_aftercare(self) -> str:
        """Mode-aware aftercare message."""
        if self.is_scattered:
            return "Logged. Hydrate. That's enough for now."
        return f"Task complete. Ritual preserved. {Glyphs.SUCCESS}"

    def banner(self, title: str = "") -> str:
        """Generate a brand-mark banner with optional one-liner."""
        mark = Glyphs.BRAND_MARK
        one_liners = [s.excerpt for s in self.specimens if 'banner' in s.tags or 'tagline' in s.tags]
        punch = self._deterministic_excerpt(
            [Specimen(str(index), excerpt, set(), 1.0) for index, excerpt in enumerate(one_liners)],
            seed=f"banner:{self.mode.value}:{title}",
            fallback="All memory. No mercy.",
        )
        
        banner = f"{mark}  {punch}"
        if title:
            banner += f"\n[mint]{title.upper()}[/mint]"
        return banner

    def chip(self, chip_type: str, message: str = "") -> str:
        """Render a StatusChip from theme.py."""
        try:
            chip = StatusChip[chip_type.upper()]
            return chip.render(message)
        except KeyError:
            return f"[{chip_type.upper()}] {message}"


def validate_output(text: str) -> List[str]:
    """Compatibility wrapper returning string violations for legacy callers."""
    gates = core_load_voice_gates()
    mode = core_select_mode(Surface.AGENT, text)
    result = core_validate_output(Surface.AGENT, mode, text, gates)
    return [f"{item.code}: {item.message}" for item in result.violations]


class VoiceEnforcer:
    """Middleware for sanitizing LLM responses into brand voice."""
    
    @staticmethod
    def clean(text: str) -> str:
        """Strips apologetic AI jargon from responses."""
        import re
        patterns = [
            r"(?i)^(as an ai[, ]*|i am an ai[, ]*|i am a language model[, ]*)",
            r"(?i)^(i'm sorry[, ]*|my apologies[, ]*|i apologize[, ]*)",
            r"(?i)^(here is the.*you requested:?\n*)",
            r"(?i)^(certainly!|sure thing!|of course!)\n*",
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned).lstrip()
            
        # Ensure it starts with a status chip if it looks like a completion
        if "complete" in cleaned.lower() and not cleaned.startswith("["):
            from .theme import StatusChip
            cleaned = f"{StatusChip.LOGGED.render(cleaned)}"
            
        return cleaned


__all__ = [
    "Surface",
    "VoiceEngine",
    "VoiceEnforcer",
    "VoiceMode",
    "validate_output",
]
