> **ADDENDUM (post-audit fix + independent re-verification)**: this report's
> findings (Finding A, B1, B2, B3) were fixed by a supervisor in a follow-up
> commit and each fix was independently re-verified by a separate subagent
> (not this auditor, not the implementer) via targeted adversarial tests —
> see `AUDIT_VERDICT.json`'s `fixes_applied_from_audit` array for the exact
> evidence per finding. `AUDIT_VERDICT.json.auditor_verdict` now reads
> `PASS_WITH_RISKS` to reflect that final state. The body below is left
> unedited as the original NEEDS_SUPERVISOR findings record.

# Independent Embedded Audit — R1 Repair Re-Audit

**This report SUPERSEDES the prior AUDITOR_REPORT.md/AUDIT_VERDICT.json** (which
audited the pre-repair state, verdict `PASS_WITH_RISKS`, at head `12d990a994`).
That report is now stale — it did not evaluate the R1 repair commit at all.

- **PR**: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1152
- **Head audited**: `94c1dcb1bc1f8ddcab2f166e7f702b751533e2c2` ("R1 repair — CI-red
  root causes, stale ledger, validator gaps")
- **Auditor**: Claude Code CLI (Sonnet), separate Agent-tool subagent, no
  implementer context, re-auditing the repair described in
  `PROOF.json`'s `supervisor_repair_r1` section
- **Method**: independent re-execution of every claimed fix (CI checks, schema
  validation, ZIP rebuild, validator corruption test, ledger conservation,
  GitHub PR-thread inspection), not a re-read of the implementer's narrative.

## Summary

The R1 repair genuinely fixes all 5 originally-flagged validator/assembler
gaps and the CI-red root causes — every one independently re-verified below,
several by actively breaking the artifact and confirming the fix catches it.
However, this audit surfaced **material new information not reflected in
`PROOF.json`'s own residual-risk disclosure**: three fresh, currently
unresolved GitHub review threads from `chatgpt-codex-connector`, posted
*after* the R1 repair commit landed (i.e., reviewing `94c1dcb1bc` itself, not
a stale prior head), plus one crash bug found independently by this audit.
One of the four is a confirmed, reproducible defect in the shipped
deliverable, not a hypothetical risk. Verdict: **NEEDS_SUPERVISOR** — not
because the claimed repairs are false, but because there is new, real,
undisclosed information a human should weigh before treating this head as
merge-ready (independent of the two intentionally-pending gates).

## Verified fixes (all independently re-executed, not just re-read)

1. **CI**: `gh pr checks 1152` shows every job green except the two expected
   pending gates ("independent embedded audit", "PR Steward / final
   readiness" — both fail only because a signed local attestation hasn't been
   produced yet, exactly as briefed; not treated as a defect).
2. **pre-commit**: `pre-commit run --files task-packets/TP-DMX-FDOS-004-...md
   proof/TP-DMX-FDOS-004-.../PROOF.json` — all hooks Passed, including
   "Validate proof bundle embedded_audit schema".
3. **Embedded-audit schema**: `scripts/audit/validate_audit_proof.py` reports
   `PASS 1/1`. Direct `jsonschema.validate()` of `PROOF.json["embedded_audit"]`
   against `schemas/proof/embedded_audit.schema.json` also passes cleanly
   (ran this myself, not trusting the validator script alone).
4. **ZIP sidecar path**: `cat .../TP-DMX-FDOS-004-....zip.sha256` shows a
   repo-relative path (`out/chatgpt-project-upload-set/....zip`), and
   `shasum -a 256 -c` on it from the repo root reports `OK`.
5. **ZIP generation is really in the committed assembler**:
   `scripts/project_sources/build_chatgpt_project_sources.py` has a real
   `build_zip_archive()` function (deterministic member order, fixed
   timestamps) called from `main()` at line 488. Independently rebuilt the
   package from scratch (in-repo scratch dirs, since an out-of-repo `--output-dir`
   crashes — see Finding A below) and confirmed a `.zip` + `.zip.sha256` are
   produced with no manual step, and `shasum -a 256 -c` on the fresh sidecar
   succeeds. Rebuilding twice with identical args into two different parent
   locations (same output-dir basename) produced a **byte-identical ZIP**
   (`cmp` exit 0). Rebuilding with the exact `generated_at` used in the
   committed `out/` package also produced a byte-identical ZIP to the
   committed one (only difference: the committed copy's package directory
   also contains `PACKAGE_VALIDATION.json`, written by a later, separate
   validator run — see Finding B1).
6. **Manifest-disk coverage gate**: `validate_chatgpt_project_sources.py`
   line 70-78 does real set-equality (`disk_names == manifest_names`), not a
   count check.
7. **Hash-gate no longer skips generated slots 38/40**: line 88
   (`if entry.get("sha256"):`) checks every manifest entry carrying a
   non-null hash, not just `artifact_type == "copied_source"`. Verified by
   copying the built package, flipping one byte in
   `38_SOURCE_FRESHNESS_POLICY.md`, and re-running the validator against the
   corrupted copy: `hash` gate reported `pass: false`, `all_gates_pass: false`,
   process exit code 1.
8. **Open-PR ledger conservation**: captured (`OPEN_PRS_INITIAL.json`) = 29
   PR numbers, classified (`pr_classifications.json`) = 29, set-equal (no
   missing, no extra). Live `gh pr list --state open` currently shows 28 open
   PRs (includes #1152 itself, which is correctly absent from the captured
   set — expected churn: 2 PRs from the capture, #1126/#1160, have since
   closed/merged; this is disclosed churn, not a ledger defect).
9. **PR #1159 classification spot-check**: ledger classifies it
   `SOURCE_CONTENT_REFRESH_IF_MERGED` touching slot 25. Independently
   confirmed via `gh pr view 1159 --json files`: it touches exactly
   `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` and
   `docs/03-reference/governance/codex-macro-packet-blueprint.md`, title
   matches ("add 'claude' to execution.agent enum") — the classification is
   accurate, not fabricated.
10. **Self-PR exclusion**: `grep -rn "1152"` across the ledger/manifest/
    classifications finds only the disclosed `self_exclusion_note` field —
    #1152 is never a classified/ledgered entry. The build script also has a
    `FATAL` guard (`load_captured_prs`) that aborts if the self-PR ever
    appears in captured evidence.
11. **HANDOFF.json vs PROOF.json**: consistent — both describe the same
    blocker set (`HARVEST_INCOMPLETE`, `REVIEW_ITEM_MUST_FIX`,
    `UNRESOLVED_REVIEW_THREAD` fixed at the root cause;
    `EMBEDDED_AUDIT_NEEDS_SUPERVISOR` still open pending this very audit +
    signed attestation). No contradiction found.
12. **Local-attestation path is genuinely live** (not just claimed):
    `config/audit/embedded-audit-allowed-signers` has `hue@local`'s ed25519
    key registered, **and this entry already exists on `origin/main`**
    (`git diff origin/main -- config/audit/embedded-audit-allowed-signers`
    is empty — it wasn't only added on this PR branch). The corresponding
    private key exists at `~/.ssh/dopemux_audit_signing` on this machine and
    its public half matches the registered entry byte-for-byte.

## New findings (not covered by the original 5 gaps, not in PROOF.json's residual-risk list)

**Finding A — `build_zip_archive()` crashes for any `--output-dir` outside the repo root.**
`scripts/project_sources/build_chatgpt_project_sources.py:529` calls
`zip_path.relative_to(repo_root)`, which raises `ValueError` (uncaught,
`main()` exits 1 after the ZIP is already partially written but before the
sidecar exists) whenever the output directory isn't a subpath of
`--repo-root`. Reproduced directly: `--output-dir /tmp/audit-rebuild` crashes;
the identical command with an in-repo output dir succeeds. This doesn't
affect the packet's own documented workflow (`out/chatgpt-project-upload-set/`
is in-repo), but it means the natural "rebuild into a scratch tmp dir to
verify" pattern — exactly what an auditor or CI job would do — fails.

**Finding B — three fresh, currently-unresolved review threads on PR #1152, posted *after* `94c1dcb1bc`.**
Via `gh api graphql` on `reviewThreads`, 10 threads are open; 7 predate the
repair commit (posted against the two earlier heads, addressed by the repair —
consistent with PROOF.json). But **3 threads from `chatgpt-codex-connector`
are timestamped ~2026-07-29T00:55:01Z, roughly 4 minutes after `94c1dcb1bc`
landed (committed 2026-07-28T17:51:24-0700 = 2026-07-29T00:51:24Z)** — i.e.,
they review the repair commit itself, not a stale head. None appear in
PROOF.json's `not_yet_resolved_in_this_commit` list.

- **B1 (confirmed real defect)**: "Build archive after validation output
  exists" (build script line 488). `build_zip_archive()` runs inside
  `main()` before `validate_chatgpt_project_sources.py` ever executes as a
  separate script to write `PACKAGE_VALIDATION.json` into the package
  directory. Independently confirmed: `unzip -l
  out/chatgpt-project-upload-set/TP-DMX-FDOS-004-....zip | grep -i
  PACKAGE_VALIDATION` returns nothing — the shipped ZIP does not contain
  `PACKAGE_VALIDATION.json`, even though the package's own
  `README.md` line 11 explicitly advertises it as a deliverable
  ("`PACKAGE_VALIDATION.json` -- validation gate results for this build").
  No committed script rebuilds the ZIP after validation runs, so this isn't
  a one-off — it reproduces every time the two scripts are run in their
  documented order. Note this does not affect the 40 `UPLOAD_FILES/`
  themselves (those are what actually gets uploaded to the ChatGPT Project
  per the README's own top-line instruction) — only the supporting audit
  trail bundled into the archive is incomplete relative to its own docs.

- **B2 (structural gap, no live failure in current data)**: "Derive capture
  completeness from captured file count" (build script line 191-192):
  `capture_complete = bool(pr.get("capture_complete", len(files) ==
  pr.get("changedFiles", -1)))` trusts a self-reported `capture_complete`
  flag rather than always recomputing it from `len(files) == changedFiles`.
  Checked every currently-committed `open-pr-*.json`: only PR #1123 is
  incomplete, and it correctly discloses `capture_complete: false` — so
  there's no live mismatch today. But if a future capture run sets
  `capture_complete: true` incorrectly (e.g. a paginator bug), this
  fail-closed guard would be silently bypassed.

- **B3 (structural gap, no live failure in current data)**: "Reject unknown
  PR classification values" (build script lines 231, 387): the material-PR
  filter is `if e["classification"] in ("SOURCE_SET_CHANGES_IF_MERGED",
  "SOURCE_CONTENT_REFRESH_IF_MERGED")` with no enum/allow-list validation
  anywhere in the script. A typo'd or unrecognized classification value in
  `pr_classifications.json` would silently fall into "non-material" rather
  than raising a fail-closed error (unlike a *missing* classification entry,
  which correctly does `raise SystemExit(... FATAL ...)`). Checked all 29
  current classification values — all are valid enum members, so no live
  occurrence exists today.

## Why NEEDS_SUPERVISOR rather than PASS

The 5 originally-flagged gaps and the CI-red root causes are genuinely fixed
— I verified each one adversarially (corruption tests, byte-diffing rebuilds,
live `gh` queries), not by trusting the implementer's narrative. But this
audit surfaced a confirmed live defect (B1: shipped ZIP missing a
README-advertised file) and a crash bug (Finding A) that nobody — implementer
or prior reviewer — had disclosed as of this commit, plus two structural
robustness gaps (B2, B3) an independent bot reviewer flagged against this
exact head within minutes of it landing. None of this blocks the two
already-pending gates (embedded audit, PR Steward) from remaining exactly
where they are, but a supervisor should decide whether B1/Finding A need a
follow-up fix before this package is actually handed to an operator for
upload, since the archive's own documentation currently overstates its
contents.

## Commands run (for reproducibility)

```
gh pr checks 1152 --repo DDD-Enterprises/dopemux-mvp
pre-commit run --files task-packets/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.md proof/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH/PROOF.json
python3 scripts/audit/validate_audit_proof.py proof/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH/PROOF.json
python3 -c "import json,jsonschema; ..."  # direct embedded_audit schema check
shasum -a 256 -c out/chatgpt-project-upload-set/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.zip.sha256
python3 scripts/project_sources/build_chatgpt_project_sources.py --repo-root . --execution-base-sha 5f862d36f5417801b9fe148fccbb439731627234 --open-pr-dir proof/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH --output-dir <scratch> --generated-at <ts>
python3 scripts/project_sources/validate_chatgpt_project_sources.py --repo-root . --execution-base-sha 5f862d36f5417801b9fe148fccbb439731627234 --package-dir <corrupted-copy> --open-pr-dir proof/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH
gh pr list --repo DDD-Enterprises/dopemux-mvp --state open --limit 200 --json number
gh pr view 1159 --json files --repo DDD-Enterprises/dopemux-mvp
gh api graphql -f query='{ repository(...) { pullRequest(number: 1152) { reviewThreads(first: 50) { nodes { isResolved isOutdated path line comments(first:1){nodes{body createdAt author{login}}} } } } } }'
unzip -l out/chatgpt-project-upload-set/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.zip
```

All scratch directories created during this audit (`_audit_scratch/`,
`/tmp/audit-rebuild*`) were deleted before finishing. No repo files were
modified except this report and `AUDIT_VERDICT.json`; nothing was committed.
