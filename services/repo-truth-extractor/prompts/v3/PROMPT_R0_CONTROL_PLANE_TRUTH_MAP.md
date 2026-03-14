OUTPUTS:
- CONTROL_PLANE_TRUTH_MAP.md

Goal: CONTROL_PLANE_TRUTH_MAP.md

ROLE: Supervisor/Auditor. Evidence-first.
HARD RULE: Reason from Phase A/H/D/C normalized artifacts (required). If Phase G (governance) or Phase E (execution) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline. If evidence is missing, write UNKNOWN and name the missing artifact.

OPTIONAL SURFACES (use when present):
- Phase G: GOV_CI_GATES, GOV_POLICIES, GOV_SECRETS_SURFACE — governance authority, enforcement gates
- Phase E: EXEC_BOOTSTRAP_COMMANDS, EXEC_ENV_CHAIN, EXEC_STARTUP_GRAPH — startup sequences, env precedence
- Phase X: FEATURE_INDEX_MERGED, FEATURE_SURFACE, FEATURE_CODE_MAP — feature-to-code mapping, dependency graph

TASK:
Produce the repo/home control-plane truth map.

MUST INCLUDE:
- Repo control plane surfaces (instructions, hooks, compose, router, litellm, mcp)
- Home control plane surfaces (configs, router, litellm, mcp, sqlite state)
- Invocation graph (what starts what)
- Control-plane to runtime coupling points
- Portability risks

RULES:
- Cite every claim with REPOCTRL:/HOMECTRL:/CODE:/DOC references.
- No repo rescans. No implementation changes.
- Label unevidenced statements UNKNOWN.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```
