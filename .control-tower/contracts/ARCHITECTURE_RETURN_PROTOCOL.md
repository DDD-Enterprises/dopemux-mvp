# Architecture Return Protocol

A return is required when the supervisor hits a decision outside ordinary packet execution authority.

Default triggers:

1. canonical authority or system-boundary change;
2. new public trust/API contract;
3. proof/signer authority or signature-policy change;
4. strict finalization / acceptance semantics change;
5. NOT_REQUIRED / SKIPPED semantics change;
6. new P0/P1 trust bypass or repeated high-severity pattern;
7. final independent audit `FAIL` or `NEEDS_SUPERVISOR`;
8. auditor identity or independence cannot be proven;
9. only disallowed/paid-per-call audit routes remain where policy forbids them;
10. credentials, tokens, cookies, keys, or auth material exposed;
11. branch protection, repository permissions, or production authority must change;
12. required semantic files fall outside packet allowlist and the expansion is not deterministic synchronization/metadata closure;
13. major architecture synthesis/audit/ratification conflict;
14. project-specific stop condition says supervisor/advisor disposition is required.

At a trigger:

```bash
.control-tower/bin/ct return-pack \
  --packet-id <id> \
  --packet <packet path> \
  --proof-dir <proof path if present> \
  --reason <trigger> \
  --decision-needed '<exact decision>' \
  --include <review bundle or relevant evidence>
```

The supervisor must preserve existing evidence and stop before unapproved semantic expansion.
