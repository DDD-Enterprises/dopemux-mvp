"""Core roast generation logic."""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence

from .models import RoastLine, RoastRequest, SpiceLevel
from .templates import CONSENT_PROMPTS, TEMPLATE_LIBRARY, TemplateBucket


class RoastEngine:
    """Composable roast generator aligned with the DØPEMÜX character bible."""

    def __init__(
        self,
        template_library: Optional[Dict[SpiceLevel, TemplateBucket]] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.template_library = template_library or TEMPLATE_LIBRARY
        self._rng = random.Random(seed)

    def generate_roasts(self, request: RoastRequest) -> List[RoastLine]:
        """Produce roast lines according to the provided request."""
        rng = random.Random(request.seed) if request.seed is not None else self._rng
        bucket = self._resolve_bucket(request.spice_level)

        user_handle = request.user_handle.strip() or "Operator"
        context = request.context.strip() if request.context else ""

        roasts: List[RoastLine] = []
        for _ in range(request.count):
            opener = rng.choice(bucket.openers).format(user=user_handle)
            user_burn = rng.choice(bucket.user_burns).format(user=user_handle)
            self_burn = rng.choice(bucket.self_burns)
            context_clause = self._context_clause(bucket, context, rng)
            closer = rng.choice(bucket.closers)
            status_chip = (
                rng.choice(bucket.status_chips) if request.include_status_chips else ""
            )
            consent_prompt = (
                rng.choice(CONSENT_PROMPTS) if request.include_consent_prompt else ""
            )
            register = self._choose_register(bucket.registers, request.registers, rng)

            fragments = [
                status_chip,
                opener,
                user_burn,
                context_clause,
                self_burn,
                closer,
                consent_prompt,
            ]

            text = " ".join(part.strip() for part in fragments if part.strip())

            roasts.append(
                RoastLine(
                    text=text,
                    spice_level=request.spice_level,
                    register=register,
                    status_chip=status_chip,
                    consent_prompt=consent_prompt,
                )
            )

        return roasts

    def _resolve_bucket(self, spice_level: SpiceLevel) -> TemplateBucket:
        if spice_level not in self.template_library:
            raise ValueError(f"Unsupported spice level: {spice_level}")
        return self.template_library[spice_level]

    def _context_clause(
        self, bucket: TemplateBucket, context: str, rng: random.Random
    ) -> str:
        if context:
            template = rng.choice(bucket.context_spins)
            return template.format(context=context)
        return rng.choice(bucket.context_fallbacks)

    @staticmethod
    def _choose_register(
        available: Sequence[str], requested: Sequence[str], rng: random.Random
    ) -> str:
        normalized = [reg.lower() for reg in requested]
        for option in available:
            if option.lower() in normalized:
                return option
        return rng.choice(available)
