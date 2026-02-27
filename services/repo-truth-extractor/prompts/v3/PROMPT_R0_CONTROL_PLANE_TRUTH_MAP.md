OUTPUTS:
- CONTROL_PLANE_TRUTH_MAP.md

Goal: CONTROL_PLANE_TRUTH_MAP.md

ROLE: Supervisor/Auditor. Evidence-first.
HARD RULE: Reason only from Phase A/H/D/C normalized artifacts. If evidence is missing, write UNKNOWN and name the missing artifact.

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
