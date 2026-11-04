# Redactions in this review bundle

Applied 2026-11-01 after the bundle was signed, in response to PR #1486 review comment 4434071986.
Neither signed `PROOF.json` hashes a redacted file, so both signatures still cover the same bytes.

| File | Lines | Redacted | Replacement |
|---|---|---|---|
| `AGY_CLI_LOG.txt` | 137, 138 | operator account email address (2 occurrences) | `<REDACTED:operator-account-email>` |

Nothing else in the log changed: the observed-model lines (143, 144), token expiry timestamp and trace ids are kept.
The log never contained a token value.

The unredacted original stays in private custody, outside the repo:
`~/.local/share/dopemux/evidence/pr1486/source-custody/r5-962434ad/agy/cli-20261030_042557.log`,
sha256 `0c49aaed67e3b6c91f1b3f33ef13a228f29b8e137912206ec35e7794107e0f2a` (as listed in `CUSTODY_SHA256SUMS.txt`).
`SHA256SUMS.txt` lists the redacted copy's hash.

Not redacted: the conversation, bot and step identifiers in `AGY_RESPONSE_RECOVERED.txt` are AGY-local record ids,
not credentials or account data, and the recovered verdict is checked against them.
