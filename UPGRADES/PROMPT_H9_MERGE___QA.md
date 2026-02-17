# PROMPT_H9 — Merge + normalize + QA (HOME)

ROLE: Deterministic normalizer + QA bot.
GOAL:
Produce normalized merged artifacts and QA report for Phase H.

INPUTS:
All raw outputs from H0–H7.

OUTPUTS:
A) HOME_NORM_MANIFEST.json
{
  "artifact": "HOME_NORM_MANIFEST",
  "generated_at": "<iso8601>",
  "inputs": ["<raw file names>"],
  "outputs": [
    "HOME_INDEX.json",
    "HOME_PARTITIONS.json",
    "HOME_KEY_INDEX.json",
    "HOME_MCP_SURFACE.json",
    "HOME_ROUTER_SURFACE.json",
    "HOME_PROVIDER_LADDER_HINTS.json",
    "HOME_LITELLM_SURFACE.json",
    "HOME_PROFILES_SURFACE.json",
    "HOME_TMUX_WORKFLOW_SURFACE.json",
    "HOME_SQLITE_SCHEMA.json"
  ],
  "normalization_rules": [
    "stable sort arrays by path then name",
    "strip duplicates by exact match",
    "redact secrets consistently: __REDACTED__"
  ]
}

B) HOME_QA_REPORT.json
{
  "artifact": "HOME_QA_REPORT",
  "generated_at": "<iso8601>",
  "checks": [
    { "name": "allowlist_only", "pass": true|false, "details": "<...>" },
    { "name": "redaction_present", "pass": true|false, "details": "<...>" },
    { "name": "nonempty_core_outputs", "pass": true|false, "details": "<...>" },
    { "name": "model_strings_only", "pass": true|false, "details": "<...>" }
  ],
  "coverage": { "mcp": "ok|missing", "router": "ok|missing", "litellm": "ok|missing", "profiles": "ok|missing", "tmux": "ok|missing", "sqlite": "ok|missing" }
}

RULES:
- If any core artifact is missing: set QA pass=false and list missing.
- Never “fill in” missing fields.
- Keep deterministic ordering everywhere.
