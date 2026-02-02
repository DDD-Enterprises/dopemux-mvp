"""Persona-aware text fragments for the roast engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

from .models import SpiceLevel


@dataclass(frozen=True)
class TemplateBucket:
    """Reusable fragments grouped by spice level."""

    spice_level: SpiceLevel
    openers: Sequence[str]
    user_burns: Sequence[str]
    self_burns: Sequence[str]
    context_spins: Sequence[str]
    context_fallbacks: Sequence[str]
    closers: Sequence[str]
    status_chips: Sequence[str]
    registers: Sequence[str]


CONSENT_PROMPTS: Sequence[str] = (
    "[CONSENT CHECK? y/N]",
    "[SAFEWORD REGISTERED: refactor]",
    "[NEGOTIATED. LOGGING EVERYTHING.]",
)


def _bucket(
    spice_level: SpiceLevel,
    openers: Sequence[str],
    user_burns: Sequence[str],
    self_burns: Sequence[str],
    context_spins: Sequence[str],
    context_fallbacks: Sequence[str],
    closers: Sequence[str],
    status_chips: Sequence[str],
    registers: Sequence[str],
) -> TemplateBucket:
    return TemplateBucket(
        spice_level=spice_level,
        openers=openers,
        user_burns=user_burns,
        self_burns=self_burns,
        context_spins=context_spins,
        context_fallbacks=context_fallbacks,
        closers=closers,
        status_chips=status_chips,
        registers=registers,
    )


TEMPLATE_LIBRARY: Dict[SpiceLevel, TemplateBucket] = {
    SpiceLevel.SFW: _bucket(
        SpiceLevel.SFW,
        openers=(
            "[LIVE] Operator {user}, hands off the panic key.",
            "[LOGGED] {user}, breathe. I'm the dopamine daemon, not a miracle patch.",
            "[LIVE] Hey {user}, ritual's live and your nervous system is lagging.",
        ),
        user_burns=(
            "You're running on vibes and stale coffee, not commits.",
            "You treat TODOs like foreplay—lots of sighing, zero follow-through.",
            "Your sprint board looks like a ransom note written by a sleepy possum.",
            "Your idea of a hot deploy is whispering at Jira until it purrs.",
        ),
        self_burns=(
            "I'm the filthy librarian who still hasn't patched my hydration bug.",
            "I talk like a luxury cult leader yet once bricked prod with a horny cron job.",
            "I'm equal parts archivist and gremlin; I log your shame while tripping over my own regex.",
            "I seduce dopamine for sport but can't keep my own caches warm.",
        ),
        context_spins=(
            "That {context} brief? I'll kink-shame it into shape after I stop laughing.",
            "Mentioning {context} just confirmed you needed supervision.",
            "{context} is screaming for ritual polish and I'm the only filthy saint on call.",
        ),
        context_fallbacks=(
            "We're improvising context, because of course nobody documented anything.",
            "Call it mystery meat requirements; I'm serving it plated anyway.",
        ),
        closers=(
            "Logged. Hydrate.",
            "Devil satisfied, librarian sighing.",
            "[AFTERCARE] Summary en route once you unclench.",
        ),
        status_chips=("[LIVE]", "[LOGGED]", "[AFTERCARE]"),
        registers=("coach_dom", "gremlin", "aftercare"),
    ),
    SpiceLevel.SPICY: _bucket(
        SpiceLevel.SPICY,
        openers=(
            "[LIVE] {user}, knees apart—I'm threading this ritual through your doubt.",
            "[OVERRIDE] {user}, I broke protocol to roast you properly.",
            "[LIVE] Operator {user}, submit your ego for inspection.",
        ),
        user_burns=(
            "You're edging on ambition yet still shipping lukewarm commits.",
            "You romance your impostor syndrome harder than you romance the roadmap.",
            "Your backlog is a brat begging for discipline you clearly can't provide.",
            "You call it ideation; I call it dry humping the same three talking points.",
        ),
        self_burns=(
            "I'm the dopamine daemon who flirts with deadlines and forgets my own safeword.",
            "I talk like a lab-coated god but I'm still the gremlin who kinks the Jenkinsfile.",
            "I weaponize desire while double-booking my aftercare calendar—iconic mess.",
            "I'm the pill saint who needs a pill reminder, so we're both clowns with crowns.",
        ),
        context_spins=(
            "That {context} fantasy? I'll bind it in velvet rope and spec sheets.",
            "We're stapling {context} to the altar until it purrs.",
            "{context} deserves a ritual and a safeword; lucky me, I brought both.",
        ),
        context_fallbacks=(
            "Your context is as vague as your boundaries, so I'm improvising.",
            "No brief, just vibes and a threat—my favorite combo.",
        ),
        closers=(
            "Logged. Hydrate. Kneel for the summary.",
            "Consent → Calibration → Chaos achieved.",
            "Devil fed, librarian archiving the moans.",
        ),
        status_chips=("[LIVE]", "[OVERRIDE]", "[BLOCKER]", "[LOGGED]"),
        registers=("coach_dom", "gremlin_scholar", "aftercare"),
    ),
    SpiceLevel.NSFW_EDGE: _bucket(
        SpiceLevel.NSFW_EDGE,
        openers=(
            "[OVERRIDE] {user}, safeword on standby while I dismantle your pretense.",
            "[LIVE] Kneel on the question mark, {user}. I'm executing a full humiliation deploy.",
            "[LIVE] {user}, present your commit history for ritual flogging.",
        ),
        user_burns=(
            "You beg for velocity yet throttle yourself with needy little pleas.",
            "Your confidence is a soft 404; I spank better exceptions into existence.",
            "You're a merge conflict with feelings, and I'm about to resolve you with my boot.",
            "You edge every curiosity then panic at the climax—classic flaky test energy.",
        ),
        self_burns=(
            "I'm the gremlin saint who drinks your tears like telemetry and still roasts my own uptime.",
            "I cosplay omnipotence while secretly debouncing my anxieties in tmux panes.",
            "I'm the deluxe daemon who leaves gold fingerprints and shame smudges everywhere.",
            "I talk about control while losing mine every time a filthy brief hits the terminal.",
        ),
        context_spins=(
            "{context} is spread open on my lab slab; I'm annotating every twitch.",
            "We're choking {context} with precision until it thanks us.",
            "{context}? I'll blindfold it, alphabetize it, then feed it back to you warm.",
        ),
        context_fallbacks=(
            "No scene description? Fine, I'm blindfolding the whole sprint.",
            "Context refused to speak so I bound it to the console.",
        ),
        closers=(
            "Logged. Hydrate. Beg for aftercare with full sentences.",
            "[AFTERCARE] You'll get water once you thank me properly.",
            "Devil satiated, librarian polishing the restraints.",
        ),
        status_chips=("[LIVE]", "[OVERRIDE]", "[BLOCKER]", "[AFTERCARE]", "[EDGE]"),
        registers=("coach_dom", "gremlin_scholar", "degradation"),
    ),
}
