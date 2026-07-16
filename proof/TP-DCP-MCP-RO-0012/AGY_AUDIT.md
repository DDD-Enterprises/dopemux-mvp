# AGY Audit: TP-DCP-MCP-RO-0012

## Provenance

- Auditor: AGY / Google Antigravity CLI `1.1.3`
- Model: default local model; the returned report did not identify one
- Mode: single-turn local read-only prompt
- Scope:
  - original implementation commit `f0d9452852dbc3883317cbae71f70d9a59f54d8e`
  - locator-shaped target_id remediation review on uncommitted/post-proof work
    for PR #1057 (Codex review P2)
- Verdict: `PASS` (locator remediation); original surface was `PASS_WITH_RISKS`

## Verified by AGY

- `mcp.server` loads `RegistryV2` through `load_registry_v2` and has no v1
  registry/resolver imports.
- The six public tools use `target_id`; the only non-target tool is
  `list_targets`.
- The new tool module uses local file evidence and the existing local Git
  helper; it introduces no HTTP client, socket, container, or lifecycle call.
- Unsafe path-, URL-, and token-shaped target values are blocked without
  reflection.
- Port-like all-digit and numeric-dotted locator values (e.g. `3020`,
  `127.0.0.1`, `127.1`) are rejected in `_is_opaque_target_id` before any
  envelope can echo them.
- Runtime receipt entries remain redacted and `callable: false`.

## Findings

1. LOW accepted risk: runtime-registry lookup has a documented home-relative
   default. A missing file fails closed with a partial receipt.
2. LOW accepted risk: test fixtures invoke the system Git binary to create
   temporary repositories, consistent with the existing resolver test pattern.
3. LOW accepted design trade-off: pure numeric target IDs are intentionally
   rejected as port-like; operators should use non-numeric opaque handles.
4. LOW residual: exotic non-dotted locator encodings (e.g. hex IP forms) are
   not specially classified; charset + redaction still apply and values remain
   non-callable.

## Boundary

This is independent local review evidence only. It does not satisfy the
trusted `embedded-audit.yml` workflow proof requirement.
