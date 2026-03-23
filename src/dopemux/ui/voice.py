"""
Dopemux Brand System — Voice and Tone Engine.
Phase 1: Thematic Persona Engine (Merged Opus + Specialist).
"""

import csv
import os
import random
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from .theme import StatusChip, Glyphs

class VoiceMode(Enum):
    """Thematic voice modes from the Brand System spec."""
    FILTH_DAEMON = "FilthDaemon"  # Drift, untagged, consequence + imperative
    CLINICAL_FORENSICS = "ClinicalForensics"  # MUST/thresholds + UNKNOWN+TODO
    UX_SCOLD = "UXScold"  # Roast + one step + evidence request
    UI_STRICT = "UIStrict"  # Form fields, labels - no threats
    BANNER_ONE_LINER = "BannerOneLiner"  # Punch lines then utility
    KINK_ACCENT = "KinkAccent"  # Optional spice layer


# Voice Gates from Resource Pack
HARD_AVOID = [
    r"as an ai",
    r"probably",
    r"maybe",
    r"generally speaking",
]

SOFT_AVOID = [
    r"no worries",
    r"it's okay",
    r"don't worry",
    r"hope you're doing well",
]

REQUIRED_CLOSERS = ["NEXT:", "Next:", "Receipt:", "PROGRESS"]


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

    def get_roast(self) -> str:
        """Get a random self-aware or user-facing roast."""
        roasts = [s for s in self.specimens if 'roast' in s.tags or 'UXScold' in s.tags]
        if not roasts:
            return "You're still here? Ship something."
        return random.choice(roasts).excerpt

    def get_aftercare(self) -> str:
        """Mode-aware aftercare message."""
        if self.is_scattered:
            return "Logged. Hydrate. That's enough for now."
        return f"Task complete. Ritual preserved. {Glyphs.SUCCESS}"

    def banner(self, title: str = "") -> str:
        """Generate a brand-mark banner with optional one-liner."""
        mark = Glyphs.BRAND_MARK
        one_liners = [s.excerpt for s in self.specimens if 'banner' in s.tags or 'tagline' in s.tags]
        punch = random.choice(one_liners) if one_liners else "All memory. No mercy."
        
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
    """Check text for brand violations and voice gate compliance."""
    violations = []
    text_lower = text.lower()

    # Hard Avoid Check
    for pattern in HARD_AVOID:
        if re.search(pattern, text_lower):
            violations.append(f"HARD_AVOID: Detected forbidden hedge/robot-speak ('{pattern}')")

    # Soft Avoid Check
    for pattern in SOFT_AVOID:
        if re.search(pattern, text_lower):
            violations.append(f"SOFT_AVOID: Detected corporate/filler fluff ('{pattern}')")

    return violations


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
