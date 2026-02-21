# PROMPT_H9_COVERAGE_QA___DRIFT___SAFETY_CHECKS
Goal: produce Phase H QA + coverage + safe-mode audit reports (NO RESCAN)
Model: Gemini Flash (preferred)

## Inputs
You will be given:
- Phase H normalized outputs from H8 (HOME_*.json)
- (optional) Phase A normalized outputs (REPO_*.json) for cross-checking
You must NOT rescan the filesystem.

## Mission
Produce QA artifacts that answer:
1) Did Phase H capture the expected home control plane surfaces?
2) Are there obvious gaps that will block Phase R?
3) Are there safety leaks (secrets) that must be remediated before archival?
4) What home-vs-repo couplings exist (paths/env/mcp/router drift)?

## Hard rules
- Only reason from provided inputs.
- Cite evidence using:
  HOMENORM: <file>#<json_pointer_or_section>
  REPONORM: <file>#<json_pointer_or_section> (if provided)
- Never include secret values.
- Provide concrete remediation suggestions as "actions" but do NOT claim execution.

## Outputs (JSON + MD)
Produce:
1) HOME_COVERAGE_QA.json
2) HOME_SAFETY_REDACTION_AUDIT.json
3) HOME_HOME_VS_REPO_DRIFT_REPORT.md
4) HOME_PHASE_R_READINESS.json

### 1) HOME_COVERAGE_QA.json
{
  "artifact": "HOME_COVERAGE_QA",
  "generated_at": "<iso8601>",
  "expected_outputs": [
    {"name":"HOME_MCP_SURFACE.json","present":true,"count":0,"evidence":["HOMENORM: ..."]},
    {"name":"HOME_ROUTER_SURFACE.json","present":true,"count":0,"evidence":["HOMENORM: ..."]},
    {"name":"HOME_PROVIDER_LADDER_HINTS.json","present":true,"count":0,"evidence":["HOMENORM: ..."]},
    {"name":"HOME_LITELLM_SURFACE.json","present":true,"count":0,"evidence":["HOMENORM: ..."]},
    {"name":"HOME_PROFILES_SURFACE.json","present":true,"count":0,"evidence":["HOMENORM: ..."]},
    {"name":"HOME_TMUX_WORKFLOW_SURFACE.json","present":true,"count":0,"evidence":["HOMENORM: ..."]},
    {"name":"HOME_SQLITE_SCHEMA.json","present":true,"count":0,"evidence":["HOMENORM: ..."]}
  ],
  "blocking_gaps": [
    {"gap":"HOME_MCP_SURFACE empty","why_blocking":"Phase R requires HOME_MCP_SURFACE","action":"Re-run H2 with expanded allowlist targets","evidence":["HOMENORM: ..."]}
  ],
  "nonblocking_gaps": [],
  "notes": []
}

### 2) HOME_SAFETY_REDACTION_AUDIT.json
{
  "artifact": "HOME_SAFETY_REDACTION_AUDIT",
  "generated_at": "<iso8601>",
  "mode": "safe",
  "findings": [
    {
      "severity": "HIGH|MED|LOW",
      "pattern": "api_key|bearer|secret|token|private_key|ssh|password|cookie|session",
      "location": "HOMENORM: <file>#<pointer>",
      "action": "REDACTED|NEEDS_REDACTION|OK",
      "recommended_fix": "<literal>",
      "evidence": ["HOMENORM: ..."]
    }
  ],
  "summary": {"high":0,"med":0,"low":0}
}

### 3) HOME_HOME_VS_REPO_DRIFT_REPORT.md
Format:
# HOME vs REPO Drift Report (Phase H)
## Coupling Points
- Env vars required only at home
- Absolute path dependencies
- MCP server name mismatches
- Router/provider ladder mismatches
- LiteLLM proxy mismatch
Each bullet must cite HOMENORM (and REPONORM if present).

## Risk
- Portability impacts
- CI/devcontainer impacts
- New-machine bootstrap impacts
Each with citations.

## Recommended bounded actions
- Small, mechanical steps to reduce drift (e.g., move a path into repo config, document required env var)
No refactors.

### 4) HOME_PHASE_R_READINESS.json
{
  "artifact": "HOME_PHASE_R_READINESS",
  "generated_at": "<iso8601>",
  "phase_r_required": [
    {"name":"HOME_MCP_SURFACE.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]},
    {"name":"HOME_ROUTER_SURFACE.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]},
    {"name":"HOME_PROVIDER_LADDER_HINTS.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]},
    {"name":"HOME_LITELLM_SURFACE.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]},
    {"name":"HOME_PROFILES_SURFACE.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]},
    {"name":"HOME_TMUX_WORKFLOW_SURFACE.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]},
    {"name":"HOME_SQLITE_SCHEMA.json","status":"OK|MISSING|EMPTY","evidence":["HOMENORM: ..."]}
  ],
  "gate": {"ready": false, "why": ["<literal>"], "next_action": ["<literal>"]}
}

## Determinism
- Stable section order as specified.
- Sort findings by severity (HIGH->LOW), then by location.
- Sort coupling points by type.

## Finish
Emit outputs in this order:
===FILE: HOME_COVERAGE_QA.json===
===FILE: HOME_SAFETY_REDACTION_AUDIT.json===
===FILE: HOME_HOME_VS_REPO_DRIFT_REPORT.md===
===FILE: HOME_PHASE_R_READINESS.json===
No markdown fences around JSON.
