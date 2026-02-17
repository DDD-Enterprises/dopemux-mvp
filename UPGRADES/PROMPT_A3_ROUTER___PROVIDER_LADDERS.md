# PHASE A3 — ROUTER + PROVIDER LADDERS (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_ROUTER_SURFACE.json + REPO_PROVIDER_LADDER_HINTS.json

Hard rules:
- Extract literal routing logic/config only.
- If routing is procedural (code), only record that it exists and where, do not interpret in Phase A.
- Evidence required for each rule.

Inputs:
- Partitions containing: litellm.config*, router configs, dopemux.toml, .claude.json, docs mentioning routing.

Task:
1) REPO_ROUTER_SURFACE.json:
   - router_sources[] (path, kind: config/doc/code_pointer)
   - selection_rules[]:
     - rule_id
     - trigger (literal: env var, flag, profile, tool name, “cc_mode”, etc.)
     - outcome (model/provider)
     - evidence {path, anchor_excerpt}
   - fallback_ladders[] (ordered lists if present literally)
   - refusal/guardrail hints (literal phrases)

2) REPO_PROVIDER_LADDER_HINTS.json:
   - providers_seen[]
   - models_seen[]
   - env_switches[] (names + what they toggle, if stated)
   - “unknown/implicit routing” pointers (where routing is referenced but not defined in scanned config)

Output files:
- REPO_ROUTER_SURFACE.json
- REPO_PROVIDER_LADDER_HINTS.json
