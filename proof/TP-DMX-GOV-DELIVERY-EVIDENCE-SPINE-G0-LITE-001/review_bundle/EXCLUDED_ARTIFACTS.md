# Excluded and custody-limited artifacts

No PAL/clink wrapper, subprocess, prompt builder, result, or verdict was used for this audit.

Included in review bundle:

- exact direct-Claude prompt;
- exact structured-output schema;
- exact normalized structured verdict returned by Claude Code CLI;
- exact candidate changed-path inventory and unified diff;
- route/model custody and deterministic validation ledger.

Raw Claude CLI JSON envelope was captured in operator tool transcript but was not
written as a loose file before the no-session-persistence process exited. Review
bundle therefore preserves normalized structured output plus disclosed usage/model
custody, not byte-for-byte raw stdout. No finding, risk, model disclosure, exit code,
or exact-head binding was omitted from canonical evidence.

Instruction-like scanner is `NOT_RUN_DIRECT_CLAUDE_ROUTE`; no clink-named scanner
module was invoked. Auditor independently treated candidate content as untrusted and
recorded its observation as F3.
