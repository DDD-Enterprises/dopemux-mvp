# TP-DCP-MCP-RO-0007 — Embedded Audit

**Verdict: PASS_WITH_RISKS** (non-blocking). Docs-only packet; self-audit by the
implementing agent challenging doc safety and secret leakage per S3.

## 1. Scope conformance

- Deliverables present: `TUNNEL_INTEGRATION.md`, `MANUAL_VALIDATION.md`,
  `FAILURE_RUNBOOK.md`, proof bundle (`PROOF.json`, `COMMAND_LOG.md`, `AUDIT.md`).
- Only allowlisted paths changed (`docs/03-reference/dcp/chatgpt-mcp-readonly/**`,
  `proof/TP-DCP-MCP-RO-0007/**`). No `services/**`, `src/**`, `.env*`,
  `.dopemux/**`, `compose*.yml`. README under `services/dcp-readonly-facade/` was
  **not** touched (was permitted only "if strictly needed" — not needed).

## 2. Secret-leakage challenge (the critical risk)

The commit.verify regex matches in the repo. I inspected **every** hit:

| Hit class | Example | Real secret? |
| --- | --- | --- |
| Documented scan command | `FAILURE_RUNBOOK.md:108` | No — the pattern is the runbook's own grep command, no value. |
| `sk-` in "ta**sk-**orchestrator" | `MANUAL_VALIDATION.md`, `TUNNEL_INTEGRATION.md` | No — substring of a service name. |
| `tunnel_s` in `chatgpt_tunnel_suitability` | `READ_ONLY_SURFACE_INVENTORY.json` (pre-existing) | No — inventory field name. |
| Redaction regex literals | `redaction.py`, `test_redaction.py` (pre-existing) | No — the redaction code/fixtures. |

**Conclusion:** zero real credentials. All tunnel ids, hostnames, ports, and
tokens in the new docs are `<PLACEHOLDER>` tokens. No registry, tunnel config, or
credentials file is committed.

**Residual risk (LOW, accepted):** the runbook intentionally inlines the secret-scan
pattern so operators can copy it. This will always self-trigger the scan. Chose
operator usefulness over a clean scan; the `|| true` in commit.verify makes it
non-blocking and the criterion is "no real secrets", which holds.

## 3. Doc-safety challenge

- **Loopback claim is honest.** Docs state plainly that the scaffold defaults to
  stdio and does **not** pin host/port (`server.py:102-104`), so loopback is an
  operator-enforced manual control with a mandatory bind-verification gate. They do
  **not** claim automatic loopback. This avoids a false-safety assertion.
- **Tunnel→facade-only invariant** is stated in all three docs, with a backend-port
  denylist and a catch-all `404` ingress default.
- **Dev-mode read/write warning** present (TUNNEL_INTEGRATION §4, MANUAL_VALIDATION
  §5.1, FAILURE_RUNBOOK §3): the facade denylist — not tunnel trust — is the
  boundary.
- **Vendor specifics labelled `PROPOSED`/placeholder** with explicit "verify
  against current official docs" and STOP-IF reconciliation, satisfying the
  "official tunnel behavior contradicts docs" STOP-IF without asserting unverified
  vendor behavior as fact.
- **Provenance discipline:** runtime facts labelled `OBSERVED` with file:line;
  procedure labelled `PROPOSED`; version-dependent transport/host env names flagged
  `UNKNOWN`/verify.

## 4. Findings

| ID | Severity | Status | Note |
| --- | --- | --- | --- |
| F-0007-LOW-1 | LOW | ACCEPTED_RISK | Runbook self-triggers the secret scan by inlining the grep pattern (§2). Operator-usefulness tradeoff; non-blocking. |
| F-0007-LOW-2 | LOW | ACCEPTED_RISK | Exact `DCP_FACADE_TRANSPORT` transport string and FastMCP host/port env names are runtime-version dependent; docs flag them `UNKNOWN`/verify rather than assert. Verified at integration time, not in CI. |

No HIGH/CRITICAL findings. No mutating surface introduced (docs only).

## 5. Validation buckets

- **PASS:** facade test suite (108 passed, 1 skipped, exit 0); diff-scope check
  (allowlist only); secret scan (no real secrets).
- **NOT_RUN:** live tunnel-client connection, ChatGPT connector creation, MCP
  inspector session — **out of scope by packet invariant** (no tunnel/connector in
  CI). These are the manual steps the new `MANUAL_VALIDATION.md` exists to drive;
  residual risk is that vendor-specific UI/transport names drift before an operator
  runs them.
- **FAIL:** none.
