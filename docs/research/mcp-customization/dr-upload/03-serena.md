# DR Pack 03: Serena

Access date: 2026-04-28

## Objective

Research current `oraios/serena` and map it to a Dopemux optional code-intelligence and technical-context support surface.

## Source Seeds

- https://github.com/oraios/serena
- https://oraios.github.io/serena/
- `docs/research/mcp-customization/data/upstream-source-manifest.json`
- Dopemux deployment seed: `docker/mcp-servers-source/serena/Dockerfile`
- Dopemux in-repo seed: `services/serena/mcp_server.py`
- Dopemux truth seed: `docs/03-reference/truth/truth-canonicals.md`

Observed source status:

- GitHub: archived=false, pushed_at=2026-04-28T07:19:47Z.
- Latest release: v1.2.0 published 2026-04-27T11:37:14Z.
- Dopemux Docker wrapper pins external Serena at `f561204840eb4a96c6956d5cd98712f8ed52d0cb`.

## Required Extraction Fields

- tools/resources/prompts
- modes and profiles
- project configuration
- memory surfaces
- transports
- shell/file/edit/refactor capabilities
- symbol/IDE capabilities
- indexing/search behavior
- auth/security model
- package/release status
- client integration surfaces

## Dopemux Boundary Constraints

- Serena is support/code-intelligence unless runtime authority is proven.
- It must not replace dope-context code/docs retrieval.
- It must not replace ConPort memory authority.
- It must not replace task-orchestrator workflow authority.
- Shell/write/refactor tools must be hidden by default unless a worktree/task packet authorizes them.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Which tools mutate files, run shell commands, or refactor code?
- Which tools duplicate host file/search tools?
- Which tools duplicate dope-context retrieval?
- Which memory features duplicate ConPort or dope-memory?
- Does Dopemux deploy external Serena wrapper or in-repo `services/serena` as canonical runtime?

## Output Contract

Return exactly:

- `items`: Top-3 actionable findings.
- `more_count`
- `next_token`
- evidence matrix
- fact vs inference separation
- UNKNOWN list
- blocker list
- responsibility collision matrix
- implementation slices with validation

## UNKNOWN / Blocker Handling

Dopemux Serena canonical runtime is UNKNOWN. Preserve the split between external Docker wrapper and in-repo implementation unless runtime evidence resolves it.

## Adopt / Adapt / Reject / Hide / Defer Table Requirements

Include rows for:

- symbol lookup
- definition/reference lookup
- file reading
- shell execution
- write/refactor tools
- memory/project context
- onboarding/project activation
- code search
- IDE/LSP integration

## Validation Requirements

- Verify current upstream Serena release/tool surface.
- Produce default read-only allowlist.
- Produce hidden write/shell list.
- Require worktree guard validation for any edit/refactor exposure.
