# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 83, 84 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1518/r1/custody/cli-20261119_210803.log`, sha256 `6f550cd7d922a3ee8cdd67e765e16169434838264a04a044eeb00b2c142c99cb`.
No other bundle file contained an email address. That check needs the local part to start with a letter or digit, so the
Python decorators on added diff lines (`+@app.get`, `+@pytest.mark.parametrize`) are not read as addresses.
