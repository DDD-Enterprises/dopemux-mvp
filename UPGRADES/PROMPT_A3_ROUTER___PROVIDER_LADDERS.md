Goal: REPO_ROUTER_SURFACE.json

Prompt:
- Scan repo for:
  - "router", "provider ladder", "fallback", "model routing", "litellm" configs, .dopemux/** configs in repo.
- Extract:
  - provider ordering, selection criteria, environment toggles, default models, refusal/guardrail hints.
- Output JSON, no "best" judgments.