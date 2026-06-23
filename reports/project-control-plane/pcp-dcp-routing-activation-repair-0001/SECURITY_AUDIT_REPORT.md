# Security / Live-Write Audit

**Verdict:** PASS_WITH_RISKS  
**Scope:** PCP bridge activation guards (not production activation)

## Controls verified

1. **Assertion authentication** — `NoTrustedIssuerVerifier` default; unsigned READY cannot reach writer when registry active.
2. **Authority binding** — SOURCE + `live_write_allowed=true` + writer/surface match required.
3. **Fail-closed ordering** — gate → binding → digest → execute → registry → auth → authority → dedup → writer.
4. **No default writer** — `writer_registry=None` default preserved.
5. **StrictBool HTTP boundary** — truthy non-booleans rejected at FastAPI layer.
6. **Bridge remains adapter** — `is_authority: false` on all results.

## Residual activation risks (documented, not blocking review)

- Production issuer/key material not configured (by design)
- In-process dedup only unless `RedisDedupStore` injected
- Schema validates field presence, not semantic truth of approval/audit/allowlist