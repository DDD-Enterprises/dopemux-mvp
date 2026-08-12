# Independent audit — TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001

You are an independent auditor. You did not produce this work and you have none of
the producer's conversation history. Your job is to try to break it.

**Read-only.** Do not edit, create, stage, commit or push anything in the repository.
Run mutations only under `/tmp`, on copies. You are in a throwaway detached worktree;
even so, changing tracked files would invalidate the audit.

## What you are auditing

```text
repository    DDD-Enterprises/dopemux-mvp
branch        tp/DMX-EMBEDDED-AUDIT-GROK-ROUTE-001
frozen head   2c1d15afbb12fcb3a20e79231dc14d505590aaf3
base          6626aa9a58dd82e62226cfca63498cc3f711bb75   (trusted main)
```

Confirm first that `git rev-parse HEAD` is `2c1d15afbb12fcb3a20e79231dc14d505590aaf3`.
If it is not, stop and report that instead of auditing whatever is there.

## What this packet claims to do

The trusted embedded-audit contract, `schemas/proof/embedded_audit.schema.json`,
could not name the Grok runner. Its `auditor_tool` and `auditor_model` enums had zero
grok entries, `additionalProperties` is false, and `allOf[1]` forbids
`auditor_tool: "none"` or `auditor_model: "unknown"` for any non-`SKIPPED` status. So
a completed, passing Grok audit had exactly two representable encodings, both false:
claim `SKIPPED` (asserts no audit happened), or name a runner from the enum
(fabricates an auditor identity).

This packet admits exactly one pair — `grok-cli` / `grok-4.5` — bound in both
directions, and claims to change nothing else.

**This packet is a contract change only. It accepts nothing, audits nothing else, and
implements no runtime behaviour.**

## Attack these seven areas

Do not merely confirm the producer's description of any of them.

### 1. Backward compatibility — did anything previously valid become invalid?

This is the highest-value attack. The change adds enum members and two `allOf`
conditionals. A new conditional applies to *every* document, so a mistake here
silently invalidates historical proofs.

```bash
git show origin/main:schemas/proof/embedded_audit.schema.json > /tmp/old.json
python3 scripts/audit/validate_audit_proof.py --all proof
python3 scripts/audit/validate_audit_proof.py --schema /tmp/old.json --all proof
```

Both must agree on all 74 bundles. Then go further than the producer did: construct
proof objects the existing corpus does not contain and check old-vs-new verdicts
yourself. Find any input whose verdict changed and is not a Grok input.

### 2. Is the bidirectional binding actually bidirectional, and non-vacuous?

```text
auditor_model == grok-4.5  =>  auditor_tool  == grok-cli
auditor_tool  == grok-cli  =>  auditor_model == grok-4.5
```

JSON Schema `properties` is vacuous for an absent key. Check that each conditional
carries its own `then.required`, and prove it: delete `auditor_tool` from an object
claiming `grok-4.5` and confirm it fails. Then try to construct **any** object that
names one half of the pair without the other and still validates. Try missing keys,
null values, wrong types, and `SKIPPED` status.

### 3. Can `SKIPPED` be used to smuggle a Grok claim, or vice versa?

`SKIPPED` must still force `none`/`unknown`/null invocation/null exit code. Confirm
the new conditionals did not weaken `allOf[0]`. Confirm `SKIPPED` + `grok-cli` fails.

### 4. Is the excluded vocabulary genuinely excluded?

`grok-4.5-build` and `grok-4.6` must both be rejected. The producer claims
`grok-4.5-build` is a runner-internal usage/telemetry label rather than a requestable
model id, and that `grok-4.6` is outside the authorization. Check the schema rejects
both. The live evidence is in `review_bundle/GROK_MODEL_SELECTOR_PROBE_20260812.txt`
and `GROK_MODELS_20260812.txt` — is the recorded evidence consistent with the claim?

### 5. Is the scope boundary honest?

`proof/TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001/CONSUMER_INVENTORY.json` claims a
deterministic inventory of every consumer of these enums, and justifies each
non-change. Attack it:

- Is `scripts/audit/run_embedded_audit.py` really free of an auditor recognition
  table? Read it. If it has one, the inventory is wrong and the packet under-reached.
- Can `tools/auditor_router/pal_clink.py` ever emit `auditor_model: grok-4.5`? If it
  can, the new conditional breaks a working lane, because that file hardcodes
  `auditor_tool: "pal-mcp-clink"`.
- Is `scripts/audit/local_audit_acceptance.py` really tool-agnostic?
- Find a consumer the inventory missed. `grep` for the enum members yourself.

### 6. Do the tests actually test, and does the suite still pass?

```bash
python3 -m pytest tests/audit/ -q
```

Then read `tests/audit/test_embedded_audit_grok_route.py`. Specifically:

- Does `test_new_schema_matches_pre_change_schema_on_all_old_pairs` actually execute,
  or does it `pytest.skip` and take credit for passing? Run it with `-rs`.
- Does the operator-mandated matrix assert failure for the right reason, or would an
  unrelated schema error satisfy the assertion?
- `tests/audit/test_local_audit_acceptance.py` pins the `allOf` count at 5 and requires
  a violating parity fixture per conditional. Is that count honest, and do the four
  new fixtures actually violate the conditionals they claim to?

Try deleting one new conditional from a **copy** of the schema and confirm the suite
goes red. A test suite that passes against a schema with the feature removed is not
testing the feature.

### 7a. Review-response delta

This head is a **fourth** content head. The previous audit returned FAIL on
`29a6fb54d0` with one blocker: the vendored fixture
`tests/audit/fixtures/embedded_audit.schema.pre_grok.json` was committed without being
covered by the packet's declared commit allowlist. The allowlist now includes it.
**Re-check that yourself**: compare `git diff --name-only 6626aa9a58..HEAD` against the
allowlist in the task packet and confirm every changed path is covered.

This head is also a third-generation content head. `8290d7bd8e` was the first; `d95b48a52a`
responded to three Copilot review findings; this head responds to a prior independent
audit that returned FAIL on `d95b48a52a` with one blocker — that `CONSUMER_INVENTORY.json`
claimed a deterministic inventory while documenting a bounded directory search, and so
missed a `grok-4.5` string under `docker/`.

Judge the response yourself rather than accepting it. The producer re-ran the search
repository-wide and dispositioned the `docker/` hit as a string coincidence
(`pal-mcp-server/providers/xai.py` selects a PAL *reasoning* model; the strings
`auditor_tool`/`auditor_model`/`embedded_audit` are claimed to have zero occurrences
under `docker/`). **Verify that zero-occurrence claim yourself.** If the disposition is
wrong, or if the repository-wide search still misses a consumer, say so. Also check the
delta with `git diff 8290d7bd8e..HEAD` and judge whether it strengthens or weakens the
guarantees. Specifically: the backward-compatibility differential no longer reads the
pre-change schema from git and no longer skips — it reads a vendored, hash-pinned
fixture. Is that hash pin real? Try editing the fixture and confirm the suite fails.
Is the vendored copy actually the pre-change contract, or was it produced from the
wrong ref?

### 7. Bootstrap integrity

This packet adds the Grok route. Its own controlling audit must therefore **not** be
performed by Grok, or the route would bootstrap its own admission. Check
`PROOF.json`: is the recorded auditor representable under the **pre-change** schema
(`/tmp/old.json`)? If the producer used Grok to approve Grok, that is a BLOCKING
finding.

## Also worth attacking

- The producer claims the PR #1227 round-2 audit was served by `grok-4.5`, evidenced
  by runner session metadata in `review_bundle/pr1227_r2_session_model_evidence/`.
  Is that evidence what it claims to be, or is it inference dressed as fact? Note the
  README explicitly disclaims provider-side attestation — is the disclaimer adequate?
- Does anything in this packet edit PR #1227, another packet's proof bundle, or any
  runtime code? `git diff --stat 6626aa9a58..HEAD` should show only the allowlisted
  paths.
- Is the commit allowlist in the task packet consistent with what was actually
  committed?

## What must be true for a PASS

```text
VERDICT=PASS
BLOCKERS=0
MUST_FIX=0
```

Anything less is a FAIL and the packet does not progress. Do not soften a finding to
reach PASS, and do not manufacture a finding to look rigorous. If the evidence holds,
say so and say what you actually did to try to break it.

An audit that only restates the producer's own claims is worthless. Every conclusion
you report must come from bytes you read or a command you ran.

## Report format

Return a Markdown report with exactly these sections:

```markdown
# VERDICT
PASS | FAIL

BLOCKERS: <n>
MUST_FIX: <n>

# WHAT I VERIFIED
<what you actually executed and read, with the results>

# FINDINGS
<id, severity (BLOCKING | HIGH | MEDIUM | LOW), title, body — or "none">

# WHAT I COULD NOT VERIFY
<anything you could not check from these bytes, stated plainly>
```
