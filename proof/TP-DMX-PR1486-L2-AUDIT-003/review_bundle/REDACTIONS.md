# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 137, 138 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1486/r7/custody/cli-20261031_234720.log`, sha256 `378a90b7b8ba5952d041e0c96eebc78a680be69d3b5084f2cab336cbbe6069ab`.
No other bundle file contained an email address (checked with the same pattern before bundling).
