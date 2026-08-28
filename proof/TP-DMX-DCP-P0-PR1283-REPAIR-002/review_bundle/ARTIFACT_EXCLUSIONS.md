# Review-bundle artifact exclusions

## Raw AGY diagnostic log and transcript

- Retained: **NO**.
- Raw-log path used by invocation:
  `/private/tmp/dopemux-pr-repair-r2-briefs/pr1283-agy-controlling.log`.
- Disposition: deleted before proof materialization.
- Reason: diagnostic output contained unrelated user-local sensitive
  configuration. Secret-bearing bytes must not enter repository proof.
- Recovery/read attempt during proof materialization: **NOT_RUN**.

Canonical bundle retains only sanitized evidence:

- exact frozen subject and comparison range;
- explicit AGY selector and exact invocation;
- exit code, `SUCCESS` status, and conversation ID;
- verdict, findings, validation results, review results, and remaining risks;
- explicit statement that no additional hidden fallback state is inferred.

No tokens, credentials, private keys, environment values, raw auth headers, or
local permission-configuration contents are included.
