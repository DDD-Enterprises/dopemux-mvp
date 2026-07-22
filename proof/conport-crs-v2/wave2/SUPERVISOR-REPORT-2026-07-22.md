# Wave 2 (ConPort Dockerfile Pin/Freeze/Inventory) — Supervisor Report

**Date**: 2026-07-22
**Repo / branch**: `dopemux-mvp`, `.worktrees/CONPORT-W2-FREEZE-PIN-INVENTORY`, branch `feat/CONPORT-W2-FREEZE-PIN-INVENTORY`
**Commit**: `74817008c` (pushed to `origin/feat/CONPORT-W2-FREEZE-PIN-INVENTORY`)
**PR**: not yet opened — https://github.com/DDD-Enterprises/dopemux-mvp/pull/new/feat/CONPORT-W2-FREEZE-PIN-INVENTORY

## What shipped

The ConPort MCP server Dockerfile now pins the base image and `uv` binary by digest, installs apt packages from an immutable Debian snapshot mirror instead of the floating archive, and installs Python dependencies via `uv sync --frozen` against a committed `uv.lock` instead of an unpinned `uv pip install`. This closes the reproducibility/supply-chain gaps the Wave 2 packet was opened to fix.

Alongside the code change, the full Wave 2 governance proof trail is now committed to the repo for the first time (it had been sitting untracked): write-freeze receipt, apt snapshot pin + paired-build reproducibility comparison, redaction pipeline validation, the original tenant approval request/receipt/route-decision for `CONPORT-W2-TENANT-AUDIT-SBOM-APPROVAL-001`, and the local-runner amendment `...-002` that superseded it.

## What I did this session

1. **Preflight** against the candidate binding recorded in the tenant approval receipt — Dockerfile SHA-256, working-tree diff SHA-256, and HEAD SHA all matched exactly (`95264461d...`). Hostname matched the approved runner (`dddmbp.local`).
2. **Found a break in the freeze chain**: the four scoped writer containers named in `WAVE2-WRITE-FREEZE-RECEIPT.json` (`mcp-conport`, `mcp-conport-dnh-crm-8d6d`, `dopemux-dopemux-mvp-dcd6-conport`, `conport-dnh-crm-tgmirror0117`) don't exist on this host in *any* state — not running, not exited, gone. That receipt asserts `container_removal: false`; that's no longer true. Likely collateral damage from unrelated same-day MCP fleet work on another branch in this session, not a deliberate act. Assessed as benign for the audit (a nonexistent container can't write) but the receipt's documented rollback commands (`docker start ...`) no longer work.
3. **Rebuilt the candidate image** (`conport-w2-apt-proof-c:20260722T110706Z`) because the original proof images A/B referenced in the approval no longer existed on the host either. Dockerfile and working-tree diff are byte-identical to what was approved, so this is a same-input rebuild, not a different candidate.
4. **Acquired and checksum-verified official Syft v1.49.0** from the GitHub release (binary, `checksums.txt`, `.sig`, `.pem`). SHA-256 of the tarball matched the published checksum. **Cosign/Sigstore signature verification was NOT performed** — `cosign` isn't installed locally and installing it was judged out of the approved acquisition scope (which authorizes fetching Syft's own release assets only, not additional tooling). This is a real gap, not a rounding error — flag it if that matters for your risk tolerance.
5. **Ran the SBOM scan** locally via `docker:` source (no registry pull, zero network egress during the scan itself), producing CycloneDX (7,836 components) and SPDX (1,453 packages) documents. Full record: `proof/conport-crs-v2/wave2/WAVE2-INDEPENDENT-SBOM-C-RECORD.json`.
6. **Committed and pushed under your explicit override.** `WAVE2-TENANT-AUDIT-SBOM-APPROVAL-002` records `candidate_commit_or_push: FORBIDDEN` and `parent_wave2_readiness: BLOCKED_UNTIL_BOTH_CHILD_PACKETS_TERMINAL`. You instructed me directly to commit and push anyway. I did — but the independent embedded-audit packet (`TP-CONPORT-W2-INDEPENDENT-AUDIT-20260721`) is **still `NOT_RUN`**. That work is now on `origin` in an unaudited state.

## Open items for you

- **Independent audit still outstanding.** Nobody distinct from the implementer has reviewed this candidate. If that audit still matters to you, it needs to happen post-hoc now rather than pre-commit.
- **Syft signature verification skipped.** Only the checksum was verified, not the Sigstore signature. Decide if that's acceptable or if `cosign` should be installed and the verification redone.
- **Freeze-container discrepancy needs root-causing.** Confirm whether the missing conport containers were intentional cleanup or an accidental side effect of other MCP work today, and whether any ConPort data/state was lost.
- **No PR opened yet** — branch is 21 commits behind `origin/main` (intentionally left there to preserve candidate-binding integrity for the audit trail; a rebase would change the SHA the whole proof chain is keyed to). Someone will need to decide how to reconcile that before merge.

## Files touched

`docker/mcp-servers-source/conport/Dockerfile` (pin change) + full `proof/conport-crs-v2/wave2/` tree (48 files, proof bundle + new independent SBOM record and amendment-002 approval, landed into the repo for the first time this session).
