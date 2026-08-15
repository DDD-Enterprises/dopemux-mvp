# Signing Disclosure — PR #1232 (TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001)

```text
AUDITED_SUBSTANTIVE_TREE = 67f22b4829b0e3e98ba59fcb609f42c5af213ffc
AUDIT_EVIDENCE_HEAD      = 7acc0623440345bfc2915909413a26189d78f2ff
SIGNED_BRIDGE_HEAD       = <filled in after this commit is created>
```

## What this is

This is an **operator attestation** that allows the trusted `embedded-audit`
CI workflow to consume already-existing, already-completed independent audit
evidence, in a repo where the CI-native live auditor route (PAL clink /
`claude-audit`) is currently unable to execute because its underlying
provider (Anthropic, via the CI's Claude credential) returned "Credit
balance is too low" on run
[31868177387](https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/31868177387).

This bridge does **not** perform a new audit and does **not** re-judge the
work. It re-publishes, under a cryptographic operator signature, the exact
verdict already recorded at
`proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/PROOF.json` and
`proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/AUDITOR_REPORT.md`, which were
produced by an independently executed, genuinely non-Claude-family audit
(`grok-cli` / `grok-4.5`) before this bridge was ever proposed.

## Facts

- **Grok audit was independently executed before this bridge.** See
  `proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/COMMAND_LOG.md` (S7) for the
  full route-discovery trail (PAL codereview/chat with gemini-2.5-pro rate
  limited; gpt-5-pro produced a supporting review but is not
  schema-representable; PAL clink had no gemini/codex binaries in its
  sandboxed environment; a Docker rebuild attempt was superseded by the
  operator merging the repo's own already-reviewed `grok-cli`/`grok-4.5`
  schema admission, PR #1228; the direct host-level `~/.grok/bin/grok` CLI
  was then used, run by the operator, producing
  `proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/GROK_AUDIT_OUTPUT.json`).
- **Grok audit controls the L2 judgment.** Verdict: `PASS_WITH_RISKS`, 5
  explicit findings (R1-R5), all `ACCEPTED_RISK`, none reopening the three
  original RTE-W1-001/006/010 defects.
- **`7acc0623440345bfc2915909413a26189d78f2ff` is a proof/packet successor
  of the frozen substantive C1** (`67f22b4829b0e3e98ba59fcb609f42c5af213ffc`).
  `git diff --name-only 67f22b4829..7acc062344` (via the equivalent PR-diff
  scope, `origin/main...HEAD`) touches only proof-bundle files and the
  packet's own machine-companion JSON — confirmed at publication time.
- **No substantive source/test byte changed after C1.**
  `git diff --name-only 67f22b4829..HEAD -- services/repo-truth-extractor`
  is empty.
- **This bridge is an operator attestation allowing CI to consume
  already-existing audit evidence.** Per
  `scripts/audit/local_audit_acceptance.py`'s own documented trust model: "a
  valid signature proves that a holder of an allow-listed private key
  attested this exact code was audited. It is an operator attestation, not
  an independent third-party audit."
- **It is NOT a new audit or implementation repair.** No RTE source or test
  file is touched by this commit. No new model invocation was made to
  produce this bridge's verdict — the verdict is copied verbatim from the
  already-published `embedded_audit` object.
- **CI-native Claude audit failed from provider credit exhaustion, not from
  a finding, a schema defect, or a code defect.** The workflow's own
  preflight step found a valid, `AVAILABLE` `claude-audit` clink route
  (`pal-mcp-clink` / underlying `claude`) but that route requires operator
  approval and, when reached, the underlying provider call failed on
  insufficient credit balance — an infrastructure/billing condition
  unrelated to this packet's correctness.
- **`ANTHROPIC_API_KEY` and `EMBEDDED_AUDIT_TOKEN` were already available in
  the CI workflow; no credential repair was needed or performed by this
  bridge.** This bridge adds, rotates, or exposes no credential of any kind.

## Model identity note

`grok-4.5-build` is preserved here only as the **runtime/telemetry usage
label** that the Grok CLI's own `modelUsage` accounting reports for a
`--model grok-4.5` invocation (confirmed against this repo's own admitted-
route test fixtures, `tests/audit/test_embedded_audit_grok_route.py`, which
establish `grok-4.5-build` as the expected label when `grok-4.5` is the
requested, schema-admitted model id — `grok-4.5-build` itself is
deliberately **not** a requestable model id and is **not** used as the
`auditor_model` value in the signed `PROOF.json`). `auditor_tool=grok-cli` /
`auditor_model=grok-4.5` in the signed proof is the schema-admitted,
independently-proven pairing, not a relabeling.

## Scope of this bridge

Only these three files were created or modified by this operation:

```text
proof/pr_merge/embedded-audit/pr-1232/PROOF.json
proof/pr_merge/embedded-audit/pr-1232/PROOF.json.sig
proof/pr_merge/embedded-audit/pr-1232/SIGNING_DISCLOSURE.md
```

No RTE source or test file, no packet-proof file outside this directory,
and no file belonging to PR #1136 or PR #1183 was touched.
