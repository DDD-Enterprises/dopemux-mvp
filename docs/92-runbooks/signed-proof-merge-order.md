---
id: RUNBOOK-SIGNED-PROOF-MERGE-ORDER
title: Merging Signed-Proof PRs Under the Up-to-Date Rule
type: runbook
owner: '@hu3mann'
author: claude-code
date: '2026-10-29'
last_review: '2026-10-29'
next_review: '2027-01-27'
prelude: Why a PR carrying a signed local embedded-audit proof cannot simply be updated from main, what that does to the merge queue, and the three ways to get such a PR merged.
---
# Merging Signed-Proof PRs Under the Up-to-Date Rule

## The problem in one paragraph

`main` has branch protection with `required_status_checks.strict = true`, so a PR can only merge when it contains the current tip of `main`. A PR that carries a signed local embedded-audit proof is bound to one audited commit: the signing script requires that the proof commit be "the only change on top of the audited head_sha (proof-only delta), or CI rejects" (`scripts/audit/sign_local_audit_proof.sh`, header). Merging `main` into such a PR puts non-proof files on top of the audited head, so the proof-only closure fails. Every merge into `main` therefore makes every other signed PR stale.

Observed on 2026-10-29 with PR #1472: it was green (23 checks passed, 0 failed) and one commit behind `main` (#1447, no overlapping files). `gh pr merge 1472 --squash` was refused with "the head branch is not up to date with the base branch". A scratch merge of `origin/main` into the PR head failed `validate_change_contract.py --proof-only` with `proof_only_escaped_path` for every file #1447 brought in.

## How to check where a PR stands

```bash
gh pr view <PR> -R DDD-Enterprises/dopemux-mvp --json mergeStateStatus,mergeable,headRefOid
```

`mergeStateStatus: BEHIND` means the PR lacks the current `main` tip. `BEHIND` plus a signed proof means one of the three routes below.

To see what the branch is missing and whether anything overlaps:

```bash
git fetch -q origin main
git rev-list --left-right --count origin/main...<branch>   # left = missing from the PR, right = the PR's own commits
git log --oneline <branch>..origin/main
```

## The three routes

| Route | What it costs | What it risks |
|---|---|---|
| **A. Update and re-audit** | A new audit at the merged head (on an operator-approved route), a new canonical proof, a new per-PR proof, a new signature. | Nothing is bypassed. The audit is the expensive part. |
| **B. Admin merge** | One command by someone with administrator rights: `gh pr merge <PR> --squash --admin`. | Bypasses the up-to-date rule. Only the repository owner authorizes it. |
| **C. Merge order** | Nothing extra, but only helps a PR that is currently up to date. | None. |

Do not use `--auto` unless the owner asked for it. Pin the merge to the reviewed head with `--match-head-commit <sha>` so a late push cannot be merged by accident.

## Route C: choose the order, then pay for the rest

When several signed PRs are open, each merge makes the others stale.

- The first merge is free if that PR is currently up to date.
- Each later PR needs a new audit against the then-current `main`, and each merge before it stales it again.
- For N signed PRs the minimum is therefore N-1 re-audits, whatever the order.

Two rules reduce waste:

1. Merge PRs that are already up to date first.
2. A PR that is already behind should go last, after `main` has stopped moving. Re-auditing it earlier only to be staled again is wasted work.

## Route A: update and re-audit, step by step

Run these in the PR's worktree. Nothing here pushes; the operator pushes.

1. Merge the current `main` into the PR branch (a merge commit, not a rebase of the signed commits). The resulting commit is the new audited head.
2. Freeze the audit subject at that head: the cumulative diff against `main`, plus the delta since the last audited head.
3. Run one independent audit on the route the operator approves. The route is an operator decision per run; it is not implied by earlier runs.
4. Write the new canonical proof under `proof/<PACKET_ID>/` (with `PROOF.json`, the auditor report and `review_bundle/`) and commit it as its own proof-only commit.
5. Write `proof/pr_merge/embedded-audit/pr-<PR>/PROOF.json` bound to the new audited head. The operator sets `audit_identity.independence` to `PROVEN` in both proofs; that attestation is the operator's, not the implementer's.
6. Sign: `scripts/audit/sign_local_audit_proof.sh <PR> [signing-key]` signs the per-PR proof, then sign the canonical proof with `ssh-keygen -Y sign -n dopemux-embedded-audit <canonical PROOF.json>`.
7. Verify the canonical signature against the trusted signers from `origin/main`, not from the working tree:

   ```bash
   git show origin/main:config/audit/embedded-audit-allowed-signers > /tmp/signers
   ssh-keygen -Y find-principals -s <PROOF.json.sig> -f /tmp/signers
   ```

8. Commit both `.sig` files. Nothing but proof files may sit on top of the audited head.
9. Run the acceptance engine and the closure check locally before pushing:

   ```bash
   python -m scripts.audit.local_audit_acceptance --repo DDD-Enterprises/dopemux-mvp --pr <PR> \
     --head-sha <signed head> --risk-lane L2 --repo-root . \
     --allowed-signers <signers file> --schema <schema from origin/main> --out <tmp file>
   python scripts/governance/validate_change_contract.py --base <audited head> --head HEAD --proof-only \
     --content-head <audited head> --audited-head <audited head> --proof-head HEAD
   ```

   The closure check's `--base` is the audited head, not the macro base.
10. Push (plain, no force). Re-check `mergeStateStatus` before merging.

A merge that happens while step 10 is in flight stales the PR again. If `main` is moving, wait for it to settle first.

## What not to do

- Do not force-push to rebase a signed head. The signature binds the proof to a commit; a rewritten history needs a new audit and new signatures.
- Do not edit non-proof files after the audited head and then re-sign. A content change is a new audit subject.
- Do not use `--admin` or `--auto` on the agent's own initiative.
- Do not treat a green local acceptance as a reason to skip the pre-merge `mergeStateStatus` check.

## Open improvement (proposal, not implemented)

The closure check measures the delta from the audited head, so a clean merge of `main` looks like unaudited content. A closure mode that measured the PR's own delta against the merge-base, and accepted a merge from `main` whose incoming files are all already on `main`, would remove most of the cost above. It touches the change-contract validator and the acceptance engine, both contract-sensitive, and would need its own audit.

## References

- `scripts/audit/sign_local_audit_proof.sh`: signing script and prerequisites
- `scripts/audit/local_audit_acceptance.py`: trusted acceptance engine
- `scripts/governance/validate_change_contract.py`: proof-only closure (`validate_proof_only_closure`)
- `config/audit/embedded-audit-allowed-signers`: trusted signers (read from `origin/main`)
- `AGENTS.md` section 9.1: embedded audit
