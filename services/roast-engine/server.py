"""FastAPI surface for the DØPEMÜX Roast Engine."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from roast_engine import (
    RoastEngine,
    RoastPreset,
    RoastRequest,
    RoastResponse,
    SpiceLevel,
)
from roast_engine.models import PresetResponse
from roast_engine.templates import TEMPLATE_LIBRARY

PERSONA_NAME = "DØPEMÜX Ritual Daemon"

app = FastAPI(
    title="DØPEMÜX Roast Engine",
    description="Terminal-native roast microservice for filthy dopamine rituals.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RoastEngine()

PRESET_DESCRIPTIONS = {
    SpiceLevel.SFW: "Innuendo-forward, ritual nerd snark. Office-safe (ish).",
    SpiceLevel.SPICY: "Full Dom energy, kink-coded insults, explicit consent chips.",
    SpiceLevel.NSFW_EDGE: "Humiliation kink, obedience drills, zero chill, still no explicit body parts.",
}


@app.get("/health")
def healthcheck() -> dict:
    """Lightweight heartbeat for orchestrators."""
    return {
        "status": "ok",
        "persona": PERSONA_NAME,
        "presets": list(level.value for level in TEMPLATE_LIBRARY.keys()),
    }


@app.get("/presets", response_model=PresetResponse)
def list_presets() -> PresetResponse:
    """Describe available spice levels/register combos."""
    presets = []
    for level, bucket in TEMPLATE_LIBRARY.items():
        presets.append(
            RoastPreset(
                spice_level=level,
                registers=list(bucket.registers),
                description=PRESET_DESCRIPTIONS[level],
            )
        )
    return PresetResponse(persona=PERSONA_NAME, presets=presets)


@app.post("/roast", response_model=RoastResponse)
def generate_roast(request: RoastRequest) -> RoastResponse:
    """Generate dopamine-compliant roasts."""
    try:
        roasts = engine.generate_roasts(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RoastResponse(persona=PERSONA_NAME, count=len(roasts), roasts=roasts)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8077)
