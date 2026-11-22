# Audit history of PR 1513

Four rounds on four frozen heads. Only round 4 is the audit this bundle attests; rounds 1-3 are spent and kept for the record (verdicts in `PRIOR_R*_*_VERDICT.json`, raw streams in the evidence folder outside the repo).

| Round | Audited head | Content head | Grok (governing) | AGY | Led to |
|---|---|---|---|---|---|
| r1 | `0dfc7220a` | `6212c8db4` | NEEDS_SUPERVISOR | not run | Amendment 02 |
| r2 | `ee43f9914` | `7a469cb21` | FAIL | FAIL | Amendment 08 (Amendments 03-07 came from Copilot reviews) |
| r3 | `e95187bb2` | `dc5aac697` | FAIL | FAIL | Amendment 11 (Amendments 09-10 came from Copilot reviews) |
| r4 | `3bc641e88` | `72aa9c902` | PASS_WITH_RISKS | PASS_WITH_RISKS | this bundle |

Each FAIL was reproduced before any change and answered by an amendment (`proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_01.md` to `AMENDMENT_11.md`, each with the operator's words). The operator's stop rule from the Amendment 11 ruling: another FAIL on a symlink shape would have meant no Amendment 12 and a descope choice instead. Round 4 did not FAIL.
