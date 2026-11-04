# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 142, 143 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1486/r8/custody/cli-20261104_020753.log`, sha256 `47c7edb25dbd39a2264460b526e878ba9803ab07c4efc402698e8d823bb116c2`.
No other bundle file contained an email address (checked with the same pattern before bundling).
