TP-DMX-PR-QUEUE-BLOCKERS-001 blocker note for PR #659:

Current posture: BLOCKED / CONFLICTING pending refreshed proof and scope correction.

Observed live evidence:
- PR is OPEN, targets main, and has mergeStateStatus=BEHIND.
- Changed files include .claude/claude.md, .claude/modules/shared/governance-principles.md, and AGENTS.md.
- Changed-file list does not include a schema-valid task packet or proof artifact for this PR scope.
- Two unresolved review threads remain, including attestation/path contradiction findings.

Required before merge consideration:
- Reconcile PR body claims against the actual changed-file list.
- Resolve proof/attestation contradictions, including the .claude/path mismatch evidence if still present.
- Provide or validate a schema-valid Dopemux Task Packet and proof trail covering the actual PR scope.
- Preserve UNKNOWN / CONFLICTING / STALE labels until live evidence resolves them.

This note does not authorize merge, approval, rebase, close, branch rewrite, or source/config/test changes.
