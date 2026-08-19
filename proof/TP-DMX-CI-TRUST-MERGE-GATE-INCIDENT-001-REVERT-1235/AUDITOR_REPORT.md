# Auditor Report — PR #1235 revert of accidental canary merge (refreshed)

**Audited commit**: `bbcd474a0fb81a160e68537eb56c5b195133072b`
**Auditor**: `agy` / `gemini-3.1-pro-high`, `--mode plan`, read-only git worktree audit

## Why this report was replaced

The original evidence at this path (`AUDITOR_REPORT.md`, `AGY_AUDIT_RAW.json`) came from
an AGY invocation that returned `status: "ERROR"` (a cascade code-action charset-decoding
failure), not `status: "SUCCESS"`. Despite that, its response body contained plausible-looking
PASS content, and that content was mistakenly promoted into a signed PROOF.json's
`embedded_audit.status: "PASS"` — an ERROR-status run must never be promoted to a controlling
verdict regardless of how plausible its content reads. This is a genuine, clean re-run against
the exact same commit, using the same audit prompt, that returned a real `status: "SUCCESS"`.
The substance is unchanged (a trivial, single-file, byte-identical revert), because the
underlying facts were always simple and independently reverifiable — but the verdict is now
actually backed by a completed audit run, not an errored one.

## Verdict: PASS

**Blocking findings**: None. This is a clean, single-file revert that accurately restores the
repository to its exact pre-incident state.

**Non-blocking risks**: None. The only file touched (`CANARY_MERGE_GATE_PROBE.txt`) is a
throwaway root-level text file. No governance, schemas, CI workflows, or proof machinery are
impacted by this merge.

**Files reviewed / commands run**:
- `git show bbcd474a0fb81a160e68537eb56c5b195133072b --stat`
- `git show bbcd474a0fb81a160e68537eb56c5b195133072b`
- `git diff 75b4cfc581786a53445e412bfc8e25a6e0fdb978 bbcd474a0fb81a160e68537eb56c5b195133072b`
- `git log --oneline -5 bbcd474a0fb81a160e68537eb56c5b195133072b`

**Validation evidence reviewed**:
1. **Scope of change**: `git show --stat` and `git show` confirmed exactly 1 file touched
   (`CANARY_MERGE_GATE_PROBE.txt`), 1 line deleted. No other file modified, added, or deleted.
2. **Parent chain**: `git log` confirmed the exact claimed lineage:
   `bbcd474a0f` -> `e84d62caee` -> `75b4cfc581` — a genuine revert of the actual accidental
   canary commit, not a fabricated diff.
3. **Net-zero-content-change (explicitly confirmed)**: `git diff 75b4cfc581..bbcd474a0f`
   returned completely empty output (blank stdout, exit code 0). The tree at the audited
   commit is byte-identical to the pre-incident `main` tip.

## Response to live review finding: audit topology (head_sha vs. audited commit)

A live review comment (`chatgpt-codex-connector`, PR #1235) correctly observed that the
signed PR-scoped proof's `head_sha` field does not equal the literal commit AGY examined
(`bbcd474a0fb81a160e68537eb56c5b195133072b`) — it instead points at a later successor commit
that adds this packet-directory evidence on top of the audited commit. This is the same
AUDIT_EVIDENCE_HEAD / AUDITED_TREE distinction already established, named, and disclosed
throughout the related TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 and TP-DMX-PR-PREP-SPECIALIST-V2-001
packets: `head_sha` in the signed proof is the evidence-head (the commit that exists once this
proof-only successor is added), never conflated with the substantively-audited commit, which is
independently named here.

The distinction matters only if the delta between the audited commit and the evidence-head
could smuggle in unaudited substantive changes. It cannot here: `git diff --stat
bbcd474a0fb81a160e68537eb56c5b195133072b..<evidence-head>` is confined entirely to
`proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/` (this packet's own directory) —
verifiable directly, not merely asserted. No code, schema, or governance file is touched by
that delta. This mirrors the identical, already-accepted pattern used for PR #1224's R7 proof
(evidence-head verified confined to that packet's own directory) and PR #1236's own packet
proof bundle.

**Residual, already-documented limitation** (not new to this packet): the mechanical
acceptance check trusts the signer's claim about which commit was examined
(`ATTESTED_AUDITED_SHA`), bounded only by structural enforcement (ancestor check + diff-scope
allowlist), not by independent cryptographic proof of auditor execution. This is the same
documented limitation carried in every proof in this packet family.
