# Redactions in this review bundle

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 80, 81 | operator account email address | `<REDACTED:operator-account-email>` |

Nothing else in the log changed. The original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1524/r1/custody/cli-20261126_215629.log`, sha256 `20b62821b5b59ae027e4ee35e4618f5dcc21c298071cc85a8755c2f9015d11d9`.
No other bundle file contained an email address. That check needs the local part to start with a letter or digit, so the
Python decorators on added diff lines (`+@app.get`, `+@pytest.mark.parametrize`) are not read as addresses.
