# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 80, 81 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1516/r1/custody/cli-20261116_163505.log`, sha256 `9a89e08ae5e137605ce4a209182aa0b5123af969a3dffb19d9b2d3a0e5ca9fc9`.
No other bundle file contained an email address (checked with the same pattern before bundling).
