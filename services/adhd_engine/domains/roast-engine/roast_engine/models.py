"""Pydantic models and enums for the roast engine."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SpiceLevel(str, Enum):
    """Preset horniness/filth levels that map to the Character Bible."""

    SFW = "sfw"
    SPICY = "spicy"
    NSFW_EDGE = "nsfw_edge"


class RoastRequest(BaseModel):
    """API payload for requesting roast lines."""

    user_handle: str = Field(
        default="Operator",
        min_length=1,
        max_length=48,
        description="Name or codename for the poor soul getting roasted.",
    )
    context: Optional[str] = Field(
        default=None,
        max_length=160,
        description="Optional scene or task to fold into the roast.",
    )
    count: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of roast lines to generate.",
    )
    spice_level: SpiceLevel = Field(
        default=SpiceLevel.SPICY,
        description="How filthy the daemon should get.",
    )
    registers: List[str] = Field(
        default_factory=list,
        description="Optional registers to bias toward (coach_dom, gremlin, aftercare).",
    )
    include_status_chips: bool = Field(
        default=True,
        description="If false, omit status chips like [LIVE] or [OVERRIDE].",
    )
    include_consent_prompt: bool = Field(
        default=True,
        description="If false, skip consent prompts in the rendered line.",
    )
    seed: Optional[int] = Field(
        default=None,
        ge=0,
        le=2**31 - 1,
        description="Optional RNG seed for deterministic output.",
    )


class RoastLine(BaseModel):
    """Single roast output."""

    text: str
    spice_level: SpiceLevel
    register: str
    status_chip: str
    consent_prompt: str
    aftercare_required: bool = Field(
        default=True,
        description="Reminder flag for downstream UX to deliver aftercare.",
    )


class RoastResponse(BaseModel):
    """API response payload."""

    persona: str
    count: int
    roasts: List[RoastLine]


class RoastPreset(BaseModel):
    """Metadata describing available spice/register combos."""

    spice_level: SpiceLevel
    registers: List[str]
    description: str


class PresetResponse(BaseModel):
    """Response model for /presets."""

    persona: str
    presets: List[RoastPreset]
