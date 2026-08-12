# GROK_AUDIT_VALID_SCHEMA_REPRESENTATION_UNSUPPORTED

```text
classification: GROK_AUDIT_VALID_SCHEMA_REPRESENTATION_UNSUPPORTED
nature:         governance / tooling compatibility gap
NOT:            an audit failure, and NOT an invalidation of the Grok audit
authority:      operator AUDITOR ROUTE OVERRIDE — GROK IS CONTROLLING
```

## Two separate results, deliberately not conflated

| Lane | Result |
|---|---|
| **Substantive independent audit** (Grok 4.5, xAI, fresh read-only session, bound to content head `cc2f49ccad`) | **PASS** — 0 BLOCKER, 0 MUST_FIX, 2 nonblocking |
| **Repository-native embedded-audit lane** (`independent embedded audit` workflow) | **red / unsupported** — the trusted schema cannot encode this auditor |

The second does not overturn the first. A correctly executed, independently bound audit is not
invalidated because the repository's proof contract has no vocabulary for its runner.

## Why the native lane cannot represent it

The trusted embedded-audit contract is read from the **trusted ref (`main`)**, never from the PR
branch — the workflow checks out `trusted-source` and passes
`--schema schemas/proof/embedded_audit.schema.json` and
`--allowed-signers config/audit/embedded-audit-allowed-signers` from that checkout.

`schemas/proof/embedded_audit.schema.json` on `main`:

```text
auditor_tool  enum: agy | antigravity | claude-code-cli | copilot-cli | gemini-cli
                    | pal-mcp-clink | none
auditor_model enum: sonnet | claude-sonnet-4.6 | opus | gemini | unknown
additionalProperties: false
```

Occurrences of `grok` or `xai` in that schema: **0**.

And the conditional in `allOf[1]` forecloses the only otherwise-plausible escape:

```text
if status != "SKIPPED":
    auditor_tool  must NOT be "none"
    auditor_model must NOT be "unknown"
```

So a **passing** attestation must name a tool and model from those enums. There is no truthful
value for a Grok audit. `additionalProperties: false` also forbids adding a side-channel field.

Because the schema is read from `main`, adding Grok values on this PR branch would have **no
effect** — and modifying the schema here is explicitly out of scope for this narrowly scoped
AC#2 amendment.

## What was therefore NOT done

```text
did NOT write a passing embedded-audit proof claiming auditor_tool: claude-code-cli
did NOT write a passing embedded-audit proof claiming auditor_model: sonnet
did NOT normalise Grok into agy / antigravity / copilot-cli / gemini-cli / pal-mcp-clink
did NOT use auditor_model "unknown" with a passing status to smuggle the audit through
did NOT modify schemas/proof/embedded_audit.schema.json in this PR
did NOT sign any attestation naming a tool or model that did not perform the audit
```

The local signing key `~/.ssh/dopemux_audit_signing.pub` **is** allow-listed in
`config/audit/embedded-audit-allowed-signers` on `main` (principal `hue@local`), so the
local-attestation path is live and technically available. It was deliberately **not used**,
because the only signable payloads it would accept are ones that misstate the auditor identity.
A signature does not make a false statement true — it makes it attributable.

## Native lane recorded truthfully

The `independent embedded audit` check fails with
`Independent audit did not pass: NEEDS_SUPERVISOR`, and `PR Steward / final readiness` reports
`not READY … (audit=failure/failure steward=skipped)`.

Both are recorded as-is. Neither is in the `main` branch-protection required-check list:

```text
required: 🔒 Security Review · 📚 Documentation Check · identity-check · 🧪 Unit Tests
          Analyze (python) · Analyze (javascript-typescript) · Analyze (ruby)
          📊 CI Pipeline Summary
```

So the red native lane reflects a representation gap, not a substantive defect, and is left red
rather than papered over.

## A route-custody detail worth recording

The operator's override specifies `requested_model: grok-4.5-build`. That is **not requestable**
on this runner:

```text
$ grok -m grok-4.5-build -p "…"
Couldn't set model 'grok-4.5-build': Invalid params: "unknown model id".

$ grok models
Default model: grok-4.5
Available models:
  * grok-4.5 (default)
```

`grok-4.5-build` is a runner-internal usage/telemetry label, not an API model id. The truthful
record is therefore `requested_model: grok-4.5`, `observed usage key: grok-4.5-build`. This is
consistent with the operator's own earlier finding that `grok-4.5-build` is not a documented
xAI API alias, and it is why R-DELTA-06 was adjudicated as a **label variance** rather than a
model identity.

One useful consequence: because the runner exposes exactly one model, `fallback_enabled: false`
and `model_switching: false` are **structurally** guaranteed here, not merely asserted.

## Follow-up (separate packet, not this one)

Per operator instruction, first-class Grok support in the trusted embedded-audit contract is a
**separate governance packet**, to be created after the AC#2 authority work completes. Indicative
scope:

```text
schemas/proof/embedded_audit.schema.json   add grok-cli to auditor_tool
                                           add grok-4.5 to auditor_model
scripts/audit/run_embedded_audit.py        recognise the grok runner
scripts/audit/local_audit_acceptance.py    no change expected (tool-agnostic)
docs/…/evidence-economy.md                 record grok as an allowed L2/L3 audit family
```

That packet must land on `main` before any Grok audit can be represented in the native lane,
because the schema is read from the trusted ref.
