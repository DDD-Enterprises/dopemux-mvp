# AGY Audit: TP-DCP-MCP-RO-0013

## Provenance

- Auditor: AGY / Google Antigravity CLI `1.1.3`
- Mode: single-turn local read-only prompt
- Scope: `connector_policy.py`, `auth_context.py`
- Verdict: `PASS_WITH_RISKS` (pre-hardening notes), remediations applied locally

## Verified by AGY

- Raw secrets are not retained on sealed `ConnectorAuthContext`.
- Auth failures remain generic for public reasons.
- Untrusted connector headers are stripped/denied.
- Target/tool authorization is deny-by-default.
- No public listener, socket, or tunnel code is present.

## Findings And Local Response

1. **Rotation via dual connector_id** — AGY noted duplicate `connector_id` drops
   both records. **Accepted design:** connector identity remains unique;
   rotation updates the secret behind the same non-secret reference (covered by
   rotation tests). Dual live tokens under one id are intentionally not supported.
2. **Short secret in reference** — hardened locator requirements (`env:VAR` and
   kind-specific prefixes) and broader secret-like detection; regression test added.
3. **Seal delimiter ambiguity** — seal material now uses structured JSON encoding.
4. **Linear scan without connector hint** — accepted residual DoS risk for large
   stores; ingress rate limits deferred to TP-0014.

## Boundary

Local AGY evidence is advisory only. It does **not** satisfy
`embedded-audit.yml` or PR Steward readiness.
