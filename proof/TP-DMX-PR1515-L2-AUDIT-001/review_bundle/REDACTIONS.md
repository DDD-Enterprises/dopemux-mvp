# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 78, 79 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1515/r1/custody/cli-20261115_105934.log`, sha256 `2c8c82c7f8d0a7358863d74c4e1731ab24bbfc23019d343e4d1cdf725d509c07`.
No other bundle file contained an email address (checked with the same pattern before bundling).
