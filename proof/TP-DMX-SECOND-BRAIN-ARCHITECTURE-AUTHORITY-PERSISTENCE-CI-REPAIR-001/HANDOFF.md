# Handoff

```text
audited content head: 3cf129b127c07e2fbfb3571c8de6c42b22ed688c
proof-only head:       (this commit)
PR: #1206 (branch tp/DMX-SB-ARCH-AUTHORITY-PERSIST-001)
merge authorization: NOT_AUTHORIZED — operator decision only
```

## What changed

Repository representation only. `docs/03-reference/architecture/second-brain/authority/`'s three
ratification Markdown records and `README.md` moved from active, non-compliant uppercase files to:

- exact-byte immutable copies under
  `proof/TP-DMX-SECOND-BRAIN-ARCHITECTURE-AUTHORITY-PERSISTENCE-CI-REPAIR-001/source-authority/`
- repo-native, frontmatter-bearing, kebab-case projections in the active docs tree, each of which
  reproduces its source byte-for-byte after stripping one leading frontmatter block

No architecture semantics, ratification binding, or operator dispositions changed.

## What did NOT happen, and why

The repository has a real `independent embedded audit` CI job
(`.github/workflows/embedded-audit.yml`) and a downstream `PR Steward / final readiness` job. They
turn green only via:

1. A CI-provisioned `ANTHROPIC_API_KEY`/`CLAUDE_API_KEY` secret driving an automatic trusted-runner
   audit — outside this repair's visibility or control; it either fires on push or it doesn't.
2. A **locally-signed operator attestation**: `proof/pr_merge/embedded-audit/pr-1206/PROOF.json` +
   `PROOF.json.sig`, signed with the repo-registered `hue@local` SSH key
   (`ssh-keygen -Y sign -n dopemux-embedded-audit`), verified against
   `config/audit/embedded-audit-allowed-signers`. The repo's own
   `scripts/audit/local_audit_acceptance.py` documents this explicitly: *"a valid signature proves
   that a holder of an allow-listed private key attested this exact code was audited. It is an
   operator attestation, not an independent third-party audit."*

This repair deliberately did **not** produce or sign such a `PROOF.json` on the operator's behalf.
Doing so from an automated session, without the operator having actually reviewed the diff, would
fabricate a personal attestation the signature format exists specifically to guarantee is genuine.

Neither `independent embedded audit` nor `PR Steward / final readiness` is in `main`'s
GitHub branch-protection required status checks
(`Security Review`, `Documentation Check`, `identity-check`, `Unit Tests`,
`Analyze (python|javascript-typescript|ruby)`, `CI Pipeline Summary`) — so this gap does not block
GitHub's merge button, but it is a real governance signal the repo tracks for L2-classified changes.

Instead, a genuinely independent, fresh-session, different-vendor read-only review was obtained
(OpenCode CLI, `openrouter/moonshotai/kimi-k3`) and is recorded in `AUDITOR_REPORT.md`. It verified
the repair's scope, byte-identity, and projection-equivalence claims directly against repository
bytes. This satisfies this packet's own independent-auditor requirement (§6/§33-36) but does
**not** flip the repo's signed-attestation CI gate.

## If the operator wants those two checks green

```bash
# one-time setup (only if ~/.ssh/dopemux_audit_signing does not already exist):
ssh-keygen -t ed25519 -N '' -f ~/.ssh/dopemux_audit_signing -C "dopemux embedded-audit signing"
# (the corresponding public key is already registered in config/audit/embedded-audit-allowed-signers
#  as hue@local, so no repo change should be needed if that key already exists)

# after personally reviewing the diff at the audited content head:
mkdir -p proof/pr_merge/embedded-audit/pr-1206
cat > proof/pr_merge/embedded-audit/pr-1206/PROOF.json <<'JSON'
{
  "repo": "DDD-Enterprises/dopemux-mvp",
  "pr_number": 1206,
  "head_sha": "<the PR head SHA AFTER this repair is pushed>",
  "embedded_audit": {
    "required": true,
    "status": "PASS",
    "auditor_tool": "<value from schemas/proof/embedded_audit.schema.json auditor_tool enum>",
    "auditor_model": "<value from schemas/proof/embedded_audit.schema.json auditor_model enum>",
    "invocation": null,
    "exit_code": 0,
    "report_path": "proof/pr_merge/embedded-audit/pr-1206/PROOF.json",
    "findings": [],
    "fixes_applied": [],
    "remaining_risks": []
  }
}
JSON
ssh-keygen -Y sign -n dopemux-embedded-audit -f ~/.ssh/dopemux_audit_signing \
  proof/pr_merge/embedded-audit/pr-1206/PROOF.json
mv proof/pr_merge/embedded-audit/pr-1206/PROOF.json.sig proof/pr_merge/embedded-audit/pr-1206/PROOF.json.sig
git add proof/pr_merge/embedded-audit/pr-1206/
git commit -m "proof(pr-1206): local operator-signed embedded-audit attestation"
git push
```

This step is intentionally left for the operator to perform (or decline) at their discretion.

## Remaining empirical states (unchanged by this repair)

```text
runtime conformance:       NOT_RUN
retrieval benchmarks:      NOT_RUN
purge completeness:        NOT_RUN
multi-project isolation:   NOT_RUN
split-brain proof:         NOT_RUN
encryption implementation: ABSENT
```

## FO-01 (unchanged)

```text
architecture ratification blocker: NO
ADR acceptance blocker:            YES
required resolution:               REPAIR_AND_REVERIFY_TRACEABILITY_BEFORE_ANY_ADR_ACCEPTANCE
```
