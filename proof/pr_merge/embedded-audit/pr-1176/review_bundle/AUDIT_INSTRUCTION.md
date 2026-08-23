# Formal independent audit — CCAR-002R R1 (Supervisor Amendment A1)

## Role
You are a **read-only** independent code auditor (Claude Code / sonnet).
You have **no implementation authority**. Do not modify files, run shell that mutates state, or call MCP tools.
Base your verdict **only** on the materials in this bundle and the fixed SHAs below.

## Fixed identity (must bind verdict to exact SHA)
- Repository: `DDD-Enterprises/dopemux-mvp`
- PR: `#1176`
- Pinned start: `a22699fc9834c77017ac88e482a6c94fdd319bda`
- **Audit target R1**: `41bc62071ce4e152a3b2040e408eda0c830fb215`
- PR base: `899082ae74155b2412a2ce862376438c1d33d13e`
- Packet: `CCAR-002R` + Supervisor Amendment A1 (Claude audit route)

## Required questions (answer all)
1. Does R1 descend **directly** from pinned start `a22699fc…`?
2. Does R1 stay within the CCAR-002R allowlist (packet, builder, tests, catalog, proof/CCAR-002/**)?
3. Is `meta.source_manifest` repository-relative (`proof/CCAR-002/SOURCE_MANIFEST.json`)?
4. Is repository-root discovery validated/explicit rather than dependent **only** on fixed parent depth?
5. Do dual-worktree tests prove byte-identical catalog generation (with fixed timestamp)?
6. Are all active agent/persona **source** surfaces unchanged by R1?
7. Are exactly **nine** base agents and **43** persona records represented?
8. Are normalized outputs free of exact model IDs and unauthorized authority?
9. Are personas advisory and unable to change tools, models, or write authority?
10. Was no CommandCode agent, routing activation, skill, hook, MCP, DCP, or runtime surface added?
11. Is `proof/CCAR-002/**` truthful and current to R1 (implementation evidence; audit SKIPPED for canonical CI path is OK)?
12. Will proposed R1→R2 proof-only topology (`proof/pr_merge/embedded-audit/pr-1176/**` only; `head_sha=R1`) satisfy trusted local acceptance shape?
13. Are there any **blocking** findings?

## Allowed verdicts
`PASS` | `PASS_WITH_RISKS` | `FAIL` | `NEEDS_SUPERVISOR`

Only PASS or non-blocking PASS_WITH_RISKS authorizes R2.

## Output format
Return **ONLY** one JSON object (no markdown fences, no prose before/after):

```json
{
  "verdict": "PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR",
  "audited_sha": "41bc62071ce4e152a3b2040e408eda0c830fb215",
  "pinned_start_ok": true,
  "allowlist_ok": true,
  "source_manifest_repo_relative": true,
  "repo_root_discovery_validated": true,
  "dual_worktree_byte_identical": true,
  "source_surfaces_unchanged": true,
  "base_agent_count": 9,
  "persona_count": 43,
  "model_free_ok": true,
  "authority_prohibitions_ok": true,
  "no_runtime_activation": true,
  "proof_ccar002_truthful": true,
  "r2_topology_acceptable": true,
  "blocking_findings": false,
  "summary": "string",
  "findings": [
    {"severity": "info|low|medium|high", "area": "string", "description": "string", "status": "resolved|open|accepted_risk"}
  ],
  "remaining_risks": ["string"],
  "answers": {
    "q1": "string", "q2": "string", "q3": "string", "q4": "string", "q5": "string",
    "q6": "string", "q7": "string", "q8": "string", "q9": "string", "q10": "string",
    "q11": "string", "q12": "string", "q13": "string"
  }
}
```

Materials: IDENTITY.txt, LINEAGE.txt, R1_CHANGED_FILES.txt, R1_UNIFIED_DIFF.patch, builder, tests, catalog meta, packet, proof/CCAR-002 PROOF, schema, COUNTS.txt, SOURCE_SURFACE_CHECK.txt.
