# AUDITOR REPORT — PR #1465 L3 embedded audit (TP-DMX-PR1465-L3-AUDIT-001)

- **Auditor**: grok 1.0.67 (2fe064390d07) [stable], `grok-4.5` (`--effort high`), operator-approved fallback route; empty tool list, replaced system prompt, sealed cwd holding only the prompt; prompt built by `scripts/audit/pal_clink_runner.py --build-prompt` (proof/** excluded)
- **Implementer**: Claude Code (Anthropic Claude); runner and model family differ from the auditor's.
- **Audited head**: `8e9fe0607c3840685892bd4b530e6d55ddf5f50d` · **Base**: `93050d135ffc2592000c1d0edef82b2912935525` (main)
- **Verdict**: **PASS_WITH_RISKS**
- **Observed identity**: grok session `01a1635c-3c25-7521-8021-747964ca6ab5`, `current_model_id=grok-4.5`, `reasoning_effort=high`
- **Containment**: init tools `[]`; tool_use blocks `[]`; system prompt replaced: True; sealed dir before/after `['AUDIT_PROMPT.txt']` / `['AUDIT_PROMPT.txt']`
- **Instruction-like scan**: detected=False, matches=0
- **Superseded attempts**: 1 (AGY 429, no verdict)

## Route approval

Operator chose the Grok route in Claude Code desktop session f10afffd-f9c0-4a2e-86ad-17f8109a3a3a on 2026-10-22 after the operator-approved AGY gemini-4-argon-high route returned HTTP 429 RESOURCE_EXHAUSTED with no verdict. grok-4.5 is the embedded_audit schema's exact Grok value; precedents PR #1420 and #1459.

Residual: Grok still injects home-level instruction files and the skill-name list as context (no secret values); changing that requires editing ~/.grok/config.toml, which was not authorized. MCP servers start but are unreachable because use_tool/search_tool are disallowed.

## Auditor return (verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "findings": [],
  "risks": [
    "Profile-plane startable outputs are scanned via existing `_json_mcp_server_names`, while opencode/copilot now record shape/parse errors through `_mapping_server_names`; unparseable profile JSON may fail open (empty name set) rather than appending a parse/shape error, which is weaker than the hardened non-profile paths.",
    "Quarantine CLI wiring is shown only on the profile generate path in this diff; equivalence of non-profile generate callers is assumed from the pre-existing validator and was not re-verified against full `mcp_commands.py` outside the hunk.",
    "Static diff-only audit: unit/CLI tests were not executed in this embedded auditor session."
  ],
  "rationale": "PR 1465 at head 8e9fe0607c3840685892bd4b530e6d55ddf5f50d extends decision-required quarantine (ADR/AGENTS \u00a712.5) to profile-plane startable outputs (`profiles/<name>/mcpServers.json` and `profiles/<name>/.mcp.json`), hardens opencode/copilot mapping extraction to record shape/YAML errors instead of raising, and fails closed in `mcp_generate_cmd` before any write when quarantine errors exist. New pure-function and CliRunner tests cover positive quarantine hits, clean outputs, copilot/opencode shape failures, and apply-path non-write. No instruction-like candidate content was reported by the deterministic scanner. Residual risks are parse-path asymmetry for profile JSON and lack of executed validation evidence.",
  "inspected_paths": [
    "src/dopemux/commands/mcp_commands.py",
    "src/dopemux/mcp/fleet_catalog.py",
    "tests/unit/test_mcp_fleet_catalog_profile_quarantine.py"
  ],
  "evidence_refs": [
    "trusted_audit_authority:repo=DDD-Enterprises/dopemux-mvp;pr=1465;head=8e9fe0607c3840685892bd4b530e6d55ddf5f50d;base=93050d135ffc2592000c1d0edef82b2912935525",
    "candidate_diff:mcp_commands.py:quarantine gate before write on profile generate",
    "candidate_diff:fleet_catalog.py:_PROFILE_STARTABLE_OUTPUT_RE+_mapping_server_names+profile startable scan+YAMLError handling",
    "candidate_diff:tests/unit/test_mcp_fleet_catalog_profile_quarantine.py:164 lines covering profile quarantine, shape errors, CLI fail-closed",
    "instruction_like_scan_summary:detected=false;match_count=0"
  ],
  "validation_status": "NOT_RUN"
}
```

## Normalization notes

- Findings keep the auditor's id, severity and summary; path/lines go into `body`. `status: OPEN` is set by the proof author: no risk acceptance is claimed (that is the owner's decision).
