# Off-repo custody

Read-only originals kept outside the public repo under `~/.local/share/dopemux/evidence/pr1513/`:

| File | sha256 |
|---|---|
| `r4/custody/agy-a9308992.db` | `2d15dce0a9986ffe000aaebe26ad9da35f933a81c7cdb498294f089d44e3c301` |
| `r4/AUDIT_PROMPT.txt` | `8ee369de1c329643813d4f1c1bf4a1495c216fbbca2847b4b85bd03390841a47` |

The sealed dirs `r4/grok/` and `r4/agy/` held only `AUDIT_PROMPT.txt` (same sha256 as the copy in this bundle).
Rounds 1-3 are in `r1/`, `r2/`, `r3/` of the same folder, with their raw streams.
No AGY CLI log was captured this round; the conversation database above is the AGY record.
