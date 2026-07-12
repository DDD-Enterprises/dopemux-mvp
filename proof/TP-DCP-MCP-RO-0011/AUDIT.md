# TP-DCP-MCP-RO-0011 Audit

Verdict: `PASS_WITH_RISKS`

The implementation is a pure, facade-local join. It accepts already-loaded
catalog/runtime mappings, uses explicit service-family translation, requires
exact project/worktree identity for the two conditionally readable families,
blocks ambiguity, and serializes no operational infrastructure fields.
Any non-mapping member in the runtime instance list invalidates the complete
operational input rather than being silently discarded.

The external Gemini codereview completed its inspection phase with zero reported
issues. Its final provider call was unavailable because the configured Gemini
quota returned HTTP 429 / `RESOURCE_EXHAUSTED`. Follow-up GitHub review found a
mutable internal `callable` constructor input and a public-contract wording
mismatch; both were corrected and covered by focused tests. The local review
also corrected the proof rollback instruction and duplicate risk wording.

Accepted risks and unknowns:

- No live protocol, ownership, mount/data scope, freshness, or backend evidence
  is evaluated; these are later gates.
- `to_mcp_wrapper` and `to_compose_rest` remain blocked.
- Existing v1 facade tools still use `project_id` and are intentionally not
  rewired by this packet.
- The schema change aligns two fields already present in the restored canonical
  catalog; it does not change catalog values or runtime behavior.
