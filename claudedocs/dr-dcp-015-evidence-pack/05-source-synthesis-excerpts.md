# Source Excerpts — DCP 5.5 Synthesis Pack

Verbatim excerpts from [`docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md`](../../docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md) (on the current branch). These are the authoritative ingested constraints that the reconciliation and contract audit rest on. Quoted, not paraphrased.

## §8.3 Tooling-Layer subsection (TOOLING-0001)

> ### 8.3 Tooling-Layer subsection (TOOLING-0001)
>
> **Deterministic infra exists at scale** (see §2.5): 10 hooks, 12 pre-commit guards, 80 personas, 20 skills, 27 commands, 60+ validators. The synthesis question is not "does tooling exist" but "which surfaces should DCP standardize as deterministic hooks vs leave to LLM instruction."
>
> **Three decisions requested (TOOLING-0001 §9):** (1) which surfaces → deterministic hooks vs LLM instruction; (2) centralized skill/agent/command registry vs distributed discovery; (3) enforce MCP config schema + deprecation tracking?

## DR-015 ingested summary (synthesis line ~410)

> - **DR-015 (Tooling layer)**: core directive **`BUILD_AFTER_CORE_CONTRACTS`** (lock first: red-lane taxonomy / receipt schema / mutation classes / approval artifact / project path+resource maps); control split "LLMs reason → hooks enforce → CLI standardizes → proof records → supervisor decides"; deterministic (hooks/CLI: forbidden-path, schema, receipts, red-lines, hard blocks in UserPromptExpansion+PreToolUse+pre-commit+CI) vs LLM (skills/subagents: teach/synthesize/author, advisory); "probabilistic guard = vibe plane, not a red-lane gate"; plugin V1 `defaultEnabled:false`, no monitors/channels/default-agent-override, side-effectful skills `disable-model-invocation:true`; cross-project packaging `dcp-core` + `dcp-profile-dopemux` + `dcp-profile-dnh-crm` + repo-local (extend via rules/schemas/path-maps, not forked prompts; repo-local must not weaken core denies); NEVER build channels/default-agent-override/auto-approve-merge-resolve/CRM-client-send-from-skills/broad-live-writer-plugin; client-side Git hooks bypassable (`--no-verify`) → duplicate in CI.

## O-7. Tooling layer — build after contracts

> ### O-7. Tooling layer — build after contracts
> - DR-015 `BUILD_AFTER_CORE_CONTRACTS`: lock red-lane taxonomy / receipt schema / mutation classes / approval artifact / project path+resource maps FIRST. Then split: which surfaces → DCP Claude plugin vs skills vs deterministic hooks vs `dopemux dcp` CLI; advisory vs blocking hooks; how dNh red-lane hooks differ from Dopemux (file-path-anchored vs governance-level). Plugin v1 `defaultEnabled:false`. Existing infra at scale (10 hooks, 12 guards, 80 personas, etc.) with UNKNOWN integration.

## D15 — Tooling boundaries (decision register row)

> | **D15** | **Tooling boundaries** — what belongs in a DCP Claude plugin vs skills vs deterministic hooks vs `dopemux dcp` CLI; advisory vs blocking hooks; how dNh red-lane hooks differ from Dopemux | checklist #7 | DR-015 BUILD_AFTER_CORE_CONTRACTS; block>ask>warn>allow; client hooks bypassable→CI; dNh file-path vs Dopemux governance-level; O-7 |
