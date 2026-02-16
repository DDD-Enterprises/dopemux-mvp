# PROMPT_H5_PROFILES___SESSIONS
Goal: extract HOME profiles/sessions surfaces for dopemux/taskx/routers (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
From allowlisted home roots:
- ~/.dopemux/profiles/**
- ~/.dopemux/sessions/**
- ~/.dopemux/instances_cache.json (if present)
- ~/.config/dopemux/profiles/**
- ~/.config/dopemux/config.yaml (and dopemux.toml)
- ~/.config/taskx/** (only if profile/session concepts are present)

Extract:
1) Profile catalog: profile names/ids, declared purpose, file locations
2) Session catalog: session ids, layout hints, tools used, referenced worktrees, run_id ties
3) Any explicit "current profile" or "default profile" pointers
4) Any explicit safety modes, redaction settings, allowlists/denylists
5) Any coupling to tmux scripts, mcp configs, router ladders, compose targets

## Hard rules
- SAFE MODE: never dump full session transcripts or big blobs.
- Evidence required for each extracted entry.
- If files are large, extract only headers/keys and mark remaining UNKNOWN.

## Outputs (JSON only)
Produce:
1) HOME_PROFILES_SURFACE.json
2) HOME_SESSIONS_SURFACE.json
3) HOME_PROFILE_ROUTER_COUPLING.json

### 1) HOME_PROFILES_SURFACE.json
{
  "artifact": "HOME_PROFILES_SURFACE",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "profile_id": "<name_or_id>",
      "path": "<file_or_dir>",
      "format": "yaml|json|toml|unknown",
      "declared_purpose": "<safe_literal_or_UNKNOWN>",
      "defaults": [{"key":"<key_path>","value_literal_if_safe":"<literal_or_null>","evidence":["HOMECTRL:..."]}],
      "safety": [{"key":"<key_path>","value_literal_if_safe":"<literal_or_null>","evidence":["HOMECTRL:..."]}],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "default_profile_pointer": {
    "value_literal_if_safe": "<profile_id_or_UNKNOWN>",
    "evidence": ["HOMECTRL: ..."]
  }
}

### 2) HOME_SESSIONS_SURFACE.json
{
  "artifact": "HOME_SESSIONS_SURFACE",
  "generated_at": "<iso8601>",
  "sessions": [
    {
      "session_id": "<id_or_name>",
      "path": "<file_or_dir>",
      "mtime": "<iso8601>",
      "size": <int_bytes>,
      "layout_hint": "<tmux|worktree|pane|unknown>",
      "references": ["<paths_or_ids>"],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "notes": [
    "Session contents not emitted; SAFE MODE inventory only."
  ]
}

### 3) HOME_PROFILE_ROUTER_COUPLING.json
{
  "artifact": "HOME_PROFILE_ROUTER_COUPLING",
  "generated_at": "<iso8601>",
  "couplings": [
    {
      "profile_id": "<id>",
      "router_config": "<file_or_UNKNOWN>",
      "provider_ladder": "<ladder_id_or_UNKNOWN>",
      "mcp_servers": ["<names_or_UNKNOWN>"],
      "litellm_proxy": "<on|off|unknown>",
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "unknowns": [
    {"area": "mcp_servers", "reason": "No explicit coupling keys found in profile configs"}
  ]
}

## Determinism
- Sort profiles by profile_id.
- Sort sessions by mtime desc then session_id.
- Sort couplings by profile_id.

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
