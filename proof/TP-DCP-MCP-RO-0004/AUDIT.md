# Audit — TP-DCP-MCP-RO-0004 (Facade Scaffold)

Auditor focus per packet `embedded_audit`. Verdict: **PASS_WITH_RISKS** (non-blocking residual risks tracked; HIGH-risk security review completed).

## 1. Can any tool read outside a registered root?

No (within the threat model). Every project-scoped tool resolves through `resolver.resolve()` first (fail-closed): unknown/disabled → `BLOCKED`; `workspace_path` is `realpath`-canonicalized and must be contained in a registry `approved_root`; must contain `.dopemux/` and pass `validate_workspace()`; `.repo_id` `project` (and `owner` iff declared) must match the registry `identity`. Proof reads (`proofs.fetch_bundle`) are confined to `<workspace>/proof/`: the `bundle_id` is a single validated segment, the target is `resolve()`d and re-checked with `relative_to(proof_root)`, and **each file is opened by its resolved path** after a second containment check (closes a check/use TOCTOU window flagged by PAL codereview). Tests cover unknown/disabled, approved-root escape, symlink-workspace escape, symlink-proof escape, cross-project, and `..`/separator bundle ids.

## 2. Can a caller supply a raw path or shell?

No. No tool accepts a filesystem path, URL, port, route, or shell. Callers supply only `project_id`, an optional `packet_id_filter` (a **literal substring**, ≤128 chars — **not** a regex, eliminating the ReDoS surface PAL flagged), and a `bundle_id` (single-segment). `gitstate` runs ONLY a hardcoded argv allowlist (`rev-parse HEAD`, `rev-parse --abbrev-ref HEAD`, `status --porcelain`), `shell=False`, `cwd` = the resolver-chosen workspace, with no caller interpolation. `rg` confirms `src/` has no `write_*`/`open('w')`/`mkdir`/`rmtree`/`shell=True`/`os.system`; the only `subprocess` use is the fixed git allowlist.

## 3. Are outputs redacted and enveloped?

Yes. Every tool returns the canonical envelope (full key set, `OK|PARTIAL|BLOCKED`, never guessed data). All `data` passes `redaction.redact_value`, which recursively masks (a) registry/workspace roots, (b) a broadened set of generic absolute roots (`/Users//home//root//private//mnt//var//opt//srv//usr//etc//tmp/...`) plus any deep (≥3-segment) absolute path, and (c) secret patterns (`sk-`, `gh*_`, `AKIA`, `Bearer`, `API_KEY|TOKEN|PASSWORD|SECRET`=VALUE). Per PAL codereview, **dict keys are also redacted** (proof JSON could carry secrets/paths in keys). Tests assert paths + secrets (including in keys) are stripped and the `redactions` categories are reported.

## 4. Is proof staleness detected?

Yes. `fetch_proof_bundle` reads the current repo head via `gitstate` and compares it to the bundle's `PROOF.json` `head_sha`/`commit_sha`; a mismatch emits a `stale proof bundle` warning and sets `data.stale=true`. Dirty-worktree warnings are emitted by `get_repo_state_snapshot`. Both are tested.

## PAL codereview (gpt-5.2, HIGH-risk gate)

Ran `pal/codereview` (security, external) on resolver/proofs/redaction/gitstate/tools. Findings and dispositions:

- 🔴 **Unbounded file read before cap** → FIXED: bounded `open('rb').read(cap+1)` of the resolved path.
- 🔴 **ReDoS via caller `packet_id_regex`** → FIXED: replaced with a length-capped literal substring `packet_id_filter`; TOOL_CONTRACT §1a updated; no caller regex remains.
- 🟠 **TOCTOU (validate `f.resolve()` but read `f`)** → FIXED: read the resolved path.
- 🟠 **Redaction misses non-home absolute roots + dict keys** → FIXED: broadened roots + deep-path token; dict keys redacted.
- 🟡 **iterdir DoS on huge proof/** → FIXED: scan bounded to `MAX_BUNDLES*5` before sort.
- 🟡 **broad `except Exception`** → FIXED: narrowed to `OSError`/`RuntimeError`/`ValueError`.
- 🟡 **`.repo_id` case-sensitivity** / 🟢 **gitstate error-swallow** → left as-is: exact match is the safer (fail-closed) behavior; swallowing git errors yields `None`/`PARTIAL`, never fabricated data. Noted as accepted.

## Deviations / residual risks (non-blocking)

- **`services/registry.yaml` NOT updated**: the services CLAUDE.md asks new services to register there, but the packet's `forbidden_files` lists `services/registry.yaml`, and this is a stdio MCP server (no HTTP `/health` port). Packet authority wins; not registered. Flagged for operator.
- **`packet_id_filter` supersedes the inventory's "packet_id regex"**: a deliberate security-driven contract change (documented in TOOL_CONTRACT §1a).
- **fastmcp optional**: not installed in this env; `src/mcp/server.py` falls back to a no-op stub for import/compile safety. Tests target the pure `dcp_facade` package (no MCP dep). Live MCP endpoint requires `fastmcp` (root `[services]` extra).
- **Redaction is heuristic** (defence-in-depth), not a proof of zero-leak; deep-path scrub may over-redact (acceptable: "when unsure, redact"). Hardening/adversarial coverage continues in TP-DCP-MCP-RO-0008.
- Reachability of `service_profiles` is not probed here (configured-only); live binding is 0005/0006.
