# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 137, 138 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1486/r6/custody/cli-20261031_202247.log`, sha256 `304bc39bd28f71baa8e42c4f393c4bf2c7693d869aa0965660e25957059eb619`.
No other bundle file contained an email address (checked with the same pattern before bundling).
