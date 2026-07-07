# Backlog Packet Authoring Contract (for authoring agents)

Author schema-valid dopeTask JSON packets. Schema: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (draft-07, `additionalProperties:false` everywhere). Full reference: `task-packets/generated/DMX-CONPORT-OPTIMAL/_AUTHORING_KIT.md`. Frozen inputs: `claudedocs/backlog/decisions-ledger.md`. Your packet list + targets + deps: `claudedocs/backlog/README.md` (your series' table).

## Placement & naming
- One file per packet at `task-packets/generated/<SERIES>/<id>.json` where `<SERIES>` is the series dir (e.g. `DMX-FLEET-P0`) and `<id>` is the packet id.
- `id` field MUST equal the filename stem exactly (e.g. file `DMX-FLEET-P0-001-real-healthchecks.json` → `"id": "DMX-FLEET-P0-001-real-healthchecks"`).

## Required root fields (exactly these keys allowed; no `status`/`notes`/`tags`/`author`/`date`)
`id, project, target, repo_binding, series, commit, pr, steps` (required) + optional `invariants, depends_on, execution, pal_chain`.

### Reusable scaffolds — copy verbatim, adjust only where noted
```json
"project": "dopemux-mvp",
"repo_binding": { "project_id": "dopemux-mvp", "repo_marker": ".dopetaskroot", "origin_hint": "DDD-Enterprises/dopemux-mvp", "require_identity_match": true },
"series": { "id": "<series-slug-kebab>", "base_branch": "origin/main", "parent_tp_id": <null-or-prior-id-in-series>, "final_packet": <true only for the last packet in the series> },
"execution": { "agent": "codex", "branch": "codex/<series>-<nnn>-<slug>", "base_branch": "origin/main" }
```
- `series.id` = kebab of the series (e.g. `dmx-fleet-p0`). `parent_tp_id`: `null` for the first packet in the series, else the previous packet's id (chain them in numeric order). `final_packet`: `true` only on the highest-numbered packet of the series.
- `commit`: `{ "message": "<conventional commit>", "allowlist": [<every file the packet may touch>, "task-packets/generated/<SERIES>/<id>.json", "task-packets/INDEX.md", "proof/<id>/**"], "verify": ["python -m json.tool task-packets/generated/<SERIES>/<id>.json >/dev/null", "python -m jsonschema -i task-packets/generated/<SERIES>/<id>.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json", "git diff --check"] }`
- `pr`: `{ "title": "<short>", "body": "<1-3 sentence description referencing the source finding>", "base": "main" }` (all three required — `body` is NOT optional).
- `depends_on`: array of packet ids from the README (may reference other series, e.g. an ADR id). Use `[]` if none.

## PAL chain
- Tier B implementation packets touching runtime/schema/contract surfaces: include `"pal_chain": {"enabled": false, "steps": ["analyze","planner","codereview","precommit"]}` (Codex minimum).
- Architecture-risky packets (schema migrations, MCP surface changes, catalog/codegen, lane-engine, Serena promotion, event-source wiring): use the risky chain `["analyze","thinkdeep","challenge","planner","challenge","implement","codereview","precommit","challenge"]` with `"enabled": false` (Codex).
- Tier A (ADR) / Tier C (spec-only) packets: `pal_chain` optional; if included use the minimum chain.

## Steps by tier (each step: `id`, `task`, non-empty `validation`; optional `requirements`, `commands`, `expected_files`, `context_files`)
- **Tier B (implementation)** — mechanical: S1 preflight (fresh worktree, repo marker, clean baseline recorded in proof); S2 write failing test(s) before code where code is testable; S3 minimal implementation; S4 materialize packet + update INDEX + proof + validate + commit + PR + move orchestrator item to review. Reference the source build plan / audit section in `context_files`. Name concrete files in `expected_files` where known from the README/source.
- **Tier C (planning/spec)** — deliverable is a spec doc, not code: S1 read the named source docs + inspect the current runtime paths (read-only); S2 produce the spec at `claudedocs/specs/<id>.md` (or `docs/03-reference/...`) covering scope/invariants/interfaces/acceptance/phasing; S3 self-review vs the source + validate the packet + commit. Validation asserts the spec file exists and covers the required sections. **No runtime code.**
- **Tier A (ADR)** — deliverable is an ADR: S1 author `docs/90-adr/adr-<slug>.md` with status `accepted`, the decision, rationale, and consequences (copy the decision + rationale verbatim from `decisions-ledger.md`); S2 validate + commit. Validation asserts `grep -q 'status: accepted'` (or the repo's ADR frontmatter convention — check an existing file in `docs/90-adr/`).

## Invariants (add where relevant)
- Every packet: "This packet must run from a fresh dedicated worktree based on origin/main." and "This packet must only touch files in its commit.allowlist."
- Planning/ADR packets: "This packet must not change runtime code." Implementation packets touching contract surfaces (schemas, MCP manifests, event payloads, allowlists): "This packet must preserve the canonical writer and add a contract test."

## Validate every packet you write (from the repository root)
```bash
mise exec -- python -m jsonschema -i task-packets/generated/<SERIES>/<id>.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json && echo "PASS <id>"
```
Fix any packet that does not exit 0. Do NOT commit (the parent session commits). Return: the list of files you wrote + PASS/FAIL per packet.
