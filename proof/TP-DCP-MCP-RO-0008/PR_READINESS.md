# TP-DCP-MCP-RO-0008 — PR Readiness

Final packet of the DCP-MCP-RO read-only evidence facade series (8 of 8).

## Series completion

| Packet | Scope | Status |
| --- | --- | --- |
| 0002 | Architecture + multi-project contract | merged |
| 0003 | dopemux init / registry inspection | merged |
| 0004 | Facade scaffold + resolver + proof tools | merged |
| 0005 | ConPort + dope-memory read adapters | merged |
| 0006 | dope-context (fail-closed) + task-orchestrator adapters | merged |
| 0007 | Secure MCP Tunnel integration docs | merged (#853) |
| 0008 | Hardening: isolation, injection, redaction, no-write, PR readiness | **this PR** |

## What this PR adds

- **`untrusted` envelope field** (fail-closed default `true`; `false` only for the
  two facade-authored tools). Closes the SECURITY_MODEL §5 prompt-injection
  control that prior packets documented but deferred.
- **Hardening regression suite** (`test_packet_0008.py`, 22 tests): untrusted
  marking, prompt-injection wrapping, cross-project isolation (both directions +
  symlink escape), secret/path redaction on backend payloads, stale-proof +
  dirty-worktree warnings, and a static no-write / no-shell / no-mutating-verb
  gate over the whole facade source tree.
- Doc updates: `RESPONSE_ENVELOPE_SCHEMA.md` §6 + `ARCHITECTURE.md` §7.

## Readiness checklist

- [x] Full facade suite: 130 passed, 1 skipped (exit 0)
- [x] `compileall` exit 0
- [x] No-write / hazard scan classified (all benign — `NO_WRITE_REVIEW.md`)
- [x] Secret scan: no real secrets
- [x] Diff allowlist-only (5 files + proof bundle)
- [x] Embedded audit PASS_WITH_RISKS (2 LOW + 1 INFO, all accepted, non-blocking)
- [x] No STOP-IF triggered
- [ ] CI green on PR (pending push)
- [ ] Backend integration exercised live (NOT_RUN by design — suite mocks HTTP;
  opt-in `DCP_FACADE_LIVE_TESTS=1`; live tunnel/connector per 0007 manual checklist)

## Residual risk

`untrusted` is an advisory marker plus structural confinement of retrieved
content to `data`; the client must honor the marker. dope-context tools remain
Phase-1 BLOCKED (MCP transport bridge is Phase 2). See `AUDITOR_REPORT.md` §5.
