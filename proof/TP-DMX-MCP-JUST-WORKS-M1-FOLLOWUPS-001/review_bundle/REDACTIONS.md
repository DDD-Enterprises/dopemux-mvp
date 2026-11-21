# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 82, 83 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1521/r1/custody/cli-20261119_200940.log`, sha256 `6998bbf054f00708153f122cc1af24fb6b46fc0f4e444d6c66c34b5ca2b36c32`.

Not redacted: the operator's home directory path, which appears in `AGY_OUTPUT_RAW.txt` (1 line) and
`AGY_CLI_LOG.txt` (5 lines), as in earlier bundles.
