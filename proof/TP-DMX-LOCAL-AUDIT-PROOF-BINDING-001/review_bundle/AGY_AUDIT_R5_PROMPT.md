You are an independent auditor. This working tree is a git worktree pinned at exact commit 5adc090065 (originally on branch feat/local-audit-proof-binding-001, draft PR #1236, base main). First run `git rev-parse HEAD` and confirm it starts with 5adc090065.

## Background

This is round 5 (R5) of TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001, a repair to `scripts/audit/local_audit_acceptance.py` (the fail-closed acceptance engine for signed local embedded-audit proofs) and `scripts/audit/sign_local_audit_proof.sh` (its local signer). Four prior rounds preceded this one (R1 `ab57983171`/`05c41b3e6b`, R2 `cdc83dda65`, R3 `a26474698c`, R4 `8e9b802729`, all independently audited PASS). After R4 was pushed, two more live review findings surfaced on PR #1236. This round's commit `5adc090065` (message: "fix(audit): R5 repair — reject symlinks as evidence, signer reuses _extract_packet_id") claims to fix them. Verify that claim independently — do not trust the commit message or my characterization below.

The 2 findings, verbatim:

1. **P2** (scripts/audit/local_audit_acceptance.py:187, chatgpt-codex-connector): "Reject symlink-only review bundles" — the R3 gitlink fix checked git object TYPE, requiring at least one entry with type "blob". But git reports a SYMLINK's mode as `120000` while its object type is STILL "blob" (a symlink's blob content is just the target path string, not real stored evidence). So a `review_bundle` containing only a symlink would pass the type-only check even though no actual audit evidence is stored in the repository.
2. **P2** (scripts/audit/sign_local_audit_proof.sh:80, chatgpt-codex-connector): "Apply reserved packet-ID rejection during signing" — after R4 added rejection of `packet_id="pr_merge"` inside `_extract_packet_id` (in `local_audit_acceptance.py`), the signer script still derived `packet_id` via its OWN separately re-implemented pattern-match-and-segment-split logic (not calling the actual function), so it never learned about the R4 reservation. If `proof/pr_merge/{PROOF.json,AUDITOR_REPORT.md,review_bundle/...}` existed, the signer would print "proof shape OK" and sign it, but the real `evaluate_local_audit()` would then reject it with `packet_id_undecidable` — the exact local-success/CI-failure divergence pattern the R3 signer-parity fix was supposed to eliminate.

## Scope — verify each independently, do not take my summary on faith

1. Run `git log --oneline -14` and `git show 5adc090065 --stat` for the R5 diff.
2. For finding #1: independently confirm a symlink's git mode/type by constructing one yourself in a scratch git repo (e.g. `mkdir -p /tmp/symtest && cd /tmp/symtest && git init -q && ln -s /etc/passwd link.txt && git add -A && git commit -q -m x && git ls-tree HEAD`) and report the exact mode/type git shows. Then read the fixed `_tree_has_entries` (and any new helper like `_is_regular_file`) in `scripts/audit/local_audit_acceptance.py` in THIS worktree and confirm it now checks the entry's MODE (e.g. requiring `100644`/`100755`), not merely its object type. Also check whether the SAME class of fix was applied to the report_path exact-file check (not just review_bundle) — was that necessary for full closure, or was report_path never vulnerable to this?
3. For finding #2: read the diff to `scripts/audit/sign_local_audit_proof.sh`. Does it now import and call the ACTUAL `_extract_packet_id` from `scripts.audit.local_audit_acceptance` instead of a separately re-implemented derivation? Confirm there is no leftover parallel/duplicate packet_id-deriving logic in the script.
4. Run and confirm these tests pass, and that they genuinely exercise the scenarios (not passing for the wrong reason): `python3 -m pytest tests/audit/test_local_audit_acceptance.py::test_review_bundle_symlink_only_is_rejected tests/audit/test_local_audit_acceptance.py::test_report_path_as_symlink_is_rejected tests/audit/test_local_audit_acceptance.py::test_signer_preflight_rejects_reserved_pr_merge_packet_id -v`
5. Think adversarially again: is there any OTHER git entry type/mode that could still slip past "review_bundle has >=1 real blob" or "report_path is a real file" after this fix? Consider: empty blobs, blobs with unusual modes, deeply nested trees, or any other mode string besides 100644/100755/120000/160000 that git supports. State explicitly whether you found anything, and if so describe it precisely.
6. Run `python3 -m pytest tests/audit -q` and report exact pass/fail/skip counts (count dots in the progress output directly if the final summary line doesn't render, e.g. via `python3 -m pytest tests/audit -q --color=no 2>&1 | grep -E '^[.sFE]+\s*\[' | tr -d ' []0-9%' | wc -c` gives total test count; count the 's' characters separately for skips).
7. Run `bash -n scripts/audit/sign_local_audit_proof.sh` to confirm valid syntax.
8. Anything ELSE wrong, fragile, incomplete, or newly introduced by this R5 diff — including any regression versus R1/R2/R3/R4 protections.

## Required output

Markdown with:
- Verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR
- For EACH of the 2 findings: RESOLVED / PARTIALLY RESOLVED (why) / STILL PRESENT (why), with the actual commands you ran and their real output.
- Your adversarial analysis from step 5, explicitly.
- The real pytest counts.
- Any newly-introduced risk or regression versus R1-R4.
- One-paragraph bottom line: is this R5 commit ready to be treated as the controlling audited head for a fresh canonical proof bundle?

Do not edit files. Read-only audit.
