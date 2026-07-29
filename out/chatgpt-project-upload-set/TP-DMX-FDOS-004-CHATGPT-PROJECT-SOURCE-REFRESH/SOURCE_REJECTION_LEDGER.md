# SOURCE_REJECTION_LEDGER

Every rejected candidate for a selected slot, classified.

- `RULES.md` (candidate for slot 02 / 02_RULES.md) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e <sha>:RULES.md fails; not present in tree
- `docs/04-explanation/architecture/dopemux-architecture.md` (candidate for slot 04 / 04_ARCHITECTURE.md) -- **REDUNDANT_WITH_HIGHER_AUTHORITY**: Packet slot 04 explicitly names root ARCHITECTURE.md; this is a separate 'explanation' typed doc (frontmatter type: explanation, dated 2026-05-19), not the named source.
- `SYSTEM_BOUNDARIES.md` (candidate for slot 05 / 05_SYSTEM_BOUNDARIES.md) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent
- `PM_PLANE.md` (candidate for slot 06 / 06_PM_PLANE.md) -- **REDUNDANT_WITH_HIGHER_AUTHORITY**: Not itself named in doc-trust-map.md's LOW-trust source-path list; rejected on independent content comparison instead -- it lacks the dated frontmatter and explicit truth/runtime-path authority chain that docs/03-reference/planes/pm/pm-plane.md carries.
- `TRUTH_CANONICALS.md` (candidate for slot 12 / 12_TRUTH_CANONICALS.md) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent
- `TRUTH_INTERFACES.md` (candidate for slot 13 / 13_TRUTH_INTERFACES.md) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent
- `TRUTH_GAPS.md` (candidate for slot 14 / 14_TRUTH_GAPS.md) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent
- `PAL_EXECUTION_RULES.md` (candidate for slot 24 / 24_PAL_EXECUTION_RULES.md) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent
- `dopetask-canonical-spec.json` (candidate for slot 25 / 25_TASK_PACKET_SCHEMA.json) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent
- `dopetask-cannonical-spec.json` (candidate for slot 25 / 25_TASK_PACKET_SCHEMA.json) -- **BLOCKED_SOURCE_MISSING**: git cat-file -e confirms absent (also a known misspelling variant)
- `src/dopemux/templates/init/docs/task-packets/TEMPLATE_TASK_PACKET.md` (candidate for slot 26 / 26_TASK_PACKET_TEMPLATE.md) -- **TOOL_SPECIFIC_OUT_OF_SCOPE**: Installer scaffolding copy shipped to newly-initialized repos, not this repo's own authoring template.
- `src/dopemux/templates/init/task-packets/TEMPLATE_TASK_PACKET.md` (candidate for slot 26 / 26_TASK_PACKET_TEMPLATE.md) -- **DUPLICATE**: Second installer scaffolding copy, duplicate of the above.
- `docs/03-reference/fast-dev-os/task-packet-template.json` (candidate for slot 26 / 26_TASK_PACKET_TEMPLATE.md) -- **WRONG_IDENTITY**: JSON structural template distinct in scope/format from the canonical authoring template requested by slot 26.
- `docs/integrations/dopetask/adapter-contract.md` (candidate for slot 35 / 35_DOPETASK_ADAPTER_CONTRACT.md) -- **DUPLICATE**: Identical blob SHA to the selected docs/02-how-to path; doc-trust-map.md does not cite this path.
- `docs/integrations/dopetask/adapter-schema.md` (candidate for slot 36 / 36_DOPETASK_ADAPTER_SCHEMA.md) -- **DUPLICATE**: Identical blob SHA to the selected docs/02-how-to path; doc-trust-map.md cites only the docs/02-how-to path.

## Explicitly Adjudicated Exclusions (packet section 18)

- `Package Verification Process.txt` -- **HISTORICAL_CASE_ARTIFACT**: Case-specific historical acceptance verdict for a prior package; not present in the current tracked tree and explicitly excluded by packet invariant 8.
- `Multi-Model Routing Policy.txt` -- **WRONG_IDENTITY**: Prior oversized/wrong-identity multi-model routing artifact; not present in the current tracked tree and explicitly excluded by packet invariant 9. The correctly-scoped current source is slot 34 (config/ai/model-routing.policy.yaml).
- `REPO_STRUCTURE.md` -- **GENERATED_NAVIGATION_NOISE**: Not present in current tracked tree; historical navigation dump from a prior upload pass.
- `TOP40_SELECTION_RATIONALE.md` -- **HISTORICAL_CASE_ARTIFACT**: Not present in current tracked tree; rationale doc for a prior (FDOS-003) selection, superseded by this packet's own SOURCE_RESOLUTION_REPORT.md.
- `DRIFT_AND_GAPS_SUMMARY.md` -- **HISTORICAL_CASE_ARTIFACT**: Not present in current tracked tree as a top-level file; superseded by 40_OPEN_PR_IMPACT_LEDGER.md and this packet's own reports.
- `CHATGPT_PROJECT_UPLOAD_SET.md` -- **GENERATED_NAVIGATION_NOISE**: Prior generated navigation/meta doc referenced by doc-trust-map.md as advisory-only navigation index, not source authority.
- `INDEX.md` -- **GENERATED_NAVIGATION_NOISE**: task-packets/INDEX.md is a generated navigation index, explicitly excluded by packet section 9.
- `agents.instructions.md` -- **TOOL_SPECIFIC_OUT_OF_SCOPE**: config/instructions/agents.instructions.md is broad Copilot custom-agent authoring instruction, explicitly excluded by packet section 9; distinct from and not a substitute for AGENTS.md (slot 01).
- `PAL_CHAINING_DOCTRINE.md` -- **REDUNDANT_WITH_HIGHER_AUTHORITY**: Remains a valid repo reference per packet section 18, but the compressed operational rules (slot 24) plus live AGENTS.md (slot 01) adequately preserve the execution contract for this upload set; not present at a root path in the current tracked tree in any case.
- `PAL_PACKET_TEMPLATE.md` -- **GENERATED_NAVIGATION_NOISE**: No such file exists in the current tracked tree; only task-packets/TEMPLATE_TASK_PACKET.md (selected, slot 26) is present.
- `TEMPLATE_TASK_PACKET.md (installer scaffolding copies)` -- **TOOL_SPECIFIC_OUT_OF_SCOPE**: src/dopemux/templates/init/**/TEMPLATE_TASK_PACKET.md are installer scaffolding copies for newly-initialized repos, not this repo's own authoring template (slot 26 uses task-packets/TEMPLATE_TASK_PACKET.md directly).

