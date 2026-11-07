# Filler size probes

Operator-approved, one per auditor, before any audit. Filler of 879,525 bytes with no repo content (`r1/grok-probe/PROBE.txt`,
sha256 dcbf51a788918750c1bf51a2ebde01b5ad86dc692bc1ec77f23c975fd3766147, same size as the full prompt; kept off-repo because it is meaningless).

| Auditor | Input tokens | Result |
|---|---|---|
| Grok grok-4.5 | 247,559 | Whole prompt arrived. `init.tools == []`. |
| AGY gemini-4-argon-high | 74,939 | SUCCESS, but 687,943 bytes were silently dropped: see `AGY_MESSAGE_CAP.md`. |

The AGY result is why Grok governs: operator ruling in `AUDIT_ROUTE_AUTHORIZATION.md`.
