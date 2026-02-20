# Phase H5: Home Profiles + Sessions Surface

Goal:
- Extract any operator profiles, session presets, persona configs, or “profile selection” hints from home control-plane.

Outputs:
- HOME_PROFILES_SURFACE.json

HOME_PROFILES_SURFACE.json:
{
  "surface_version": "H5.v1",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "name": "<string>",
      "path": "<path>",
      "fields": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes":[]
}
