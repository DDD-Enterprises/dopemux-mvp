# Phase H9: Merge + QA (Home Control Plane)

Goal:
- Merge all Phase H raw outputs into deterministic normalized artifacts.
- Emit a QA report: missing expected artifacts, empty artifacts, and evidence quality warnings.

Hard rules:
- Deterministic ordering: sort keys where applicable; sort arrays by stable keys (path/name) when possible.
- No invention.

Outputs:
- HOMECTRL_NORM_MANIFEST.json
- HOMECTRL_QA.json

HOMECTRL_NORM_MANIFEST.json:
{
  "manifest_version": "H9.v1",
  "generated_at": "<iso8601>",
  "inputs": ["<raw json file names>"],
  "outputs": [
    "HOME_KEYS_SURFACE.json",
    "HOME_REFERENCES.json",
    "HOME_MCP_SURFACE.json",
    "HOME_ROUTER_SURFACE.json",
    "HOME_PROVIDER_LADDER_HINTS.json",
    "HOME_LITELLM_SURFACE.json",
    "HOME_PROFILES_SURFACE.json",
    "HOME_TMUX_WORKFLOW_SURFACE.json",
    "HOME_SQLITE_SCHEMA.json"
  ],
  "notes":[]
}

HOMECTRL_QA.json:
{
  "qa_version": "H9.v1",
  "generated_at": "<iso8601>",
  "missing_expected_raw_steps": ["<string>"],
  "empty_outputs": ["<string>"],
  "evidence_warnings": ["<string>"],
  "safe_mode_observations": ["<string>"]
}
