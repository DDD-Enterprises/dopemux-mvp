# Independent audit report

```text
audited_content_head: 3cf129b127c07e2fbfb3571c8de6c42b22ed688c
base_sha:              e9945786efaaf2994bda32bf2419c391d23ce686  (origin/main)
original_pr_head:      16e8596410de9bbdef3db5993c5eaf3f60d8d4b6
PR:                    #1206  (DDD-Enterprises/dopemux-mvp, branch tp/DMX-SB-ARCH-AUTHORITY-PERSIST-001)
runner:                OpenCode CLI (separate tool/process/session from the repair producer)
model:                 openrouter/moonshotai/kimi-k3 (variant: max)
```

## Independence statement

This audit was run via the OpenCode CLI (`opencode run --dir <isolated worktree> -m
openrouter/moonshotai/kimi-k3 --variant max --auto`), a separate tool and process from the
Claude Code session that produced the repair commit. The auditor session had no access to the
repair producer's conversation history or reasoning — it was given only a self-contained prompt
describing the PR context and a checklist of claims to verify independently against the actual
repository bytes in the isolated worktree, and was instructed to run its own git/sha256/script
commands rather than trust the prompt's framing. After the run, the worktree was confirmed
unmodified (`git status` clean, HEAD unchanged at `3cf129b127c07e2fbfb3571c8de6c42b22ed688c`).

This is a genuine independent model/tool review. It is **not** the repository's own
`independent embedded audit` CI mechanism, which (absent a CI-provisioned model credential) only
turns green via a locally-signed operator attestation using the repo-registered `hue@local` SSH
key — a personal sign-off the repair producer explicitly did not fabricate on the operator's
behalf. See `HANDOFF.md` for that gate's status.

## Scope verified

1. Diff scope (origin/main...HEAD, 14 paths, all under the three authorized surfaces)
2. Byte-identity of the 3 immutable Markdown source records under
   `proof/.../source-authority/` against the original PR head's recorded hashes
3. Projection body-equivalence (stripping one frontmatter block reproduces the source exactly)
4. `RATIFICATION_BINDING.json`, `ARCHITECTURE_AUTHORITY_HEAD.json`,
   `OPERATOR_DECISION_LEDGER.yaml` untouched by the repair commit itself
5. Operator dispositions (32 ACCEPT / 0 DEFER / 0 REJECT)
6. Ratification binding hash consistency across all files
7. No code/ADR/runtime/CI-config paths in the diff
8. Live re-run of `validate_change_contract.py`, `docs_frontmatter_guard.py --fix`,
   `check_docs_filename_hygiene.py --check` against the actual worktree
9. Master-index link update scope
10. `readme.md` framing (generated metadata, not a fourth immutable-source claim)

## Findings (verbatim from the auditor's own report)

<!-- markdownlint-disable -->
All verification complete. Evidence summary per audit point:

**1. Scope** — `git diff --name-status origin/main...HEAD`: 14 files, all under `docs/00-MASTER-INDEX.md`, `docs/03-reference/architecture/second-brain/authority/`, `proof/TP-DMX-SECOND-BRAIN-ARCHITECTURE-AUTHORITY-PERSISTENCE-CI-REPAIR-001/source-authority/`. No code, ADR, `.github/`, `scripts/`, or config paths. Repair commit alone (`16e8596..HEAD`) shows R100 renames of the 3 immutable files into proof custody, README.md→readme.md swap, frontmatter projections added, metadata updates. In-scope.

**2. Byte identity (3/3)** — SHA-256 of proof-custody files vs original head's `SOURCE_SHA256SUMS.txt` and direct `git show 16e8596:...` hashing:
- `04_RATIFICATION_CORRECTIONS.md` = `135881e3…78d8` ✓
- `08_ARCHITECTURE_RATIFICATION_RECORD.md` = `880cc9fa…fe23` ✓
- `10_FINAL_RATIFICATION_VERDICT.md` = `1bdfef1a…f9c6` ✓

**3. Projection equivalence (3/3)** — script stripped first `---`→next `---` block from each of `architecture-ratification-record.md`, `ratification-corrections.md`, `final-ratification-verdict.md`; bodies byte-equal (`exact=True`, hashes match sources, no lstrip needed).

**4. Metadata unchanged** — `git diff 16e8596..HEAD` empty (0 lines) for `RATIFICATION_BINDING.json`, `ARCHITECTURE_AUTHORITY_HEAD.json`, `OPERATOR_DECISION_LEDGER.yaml`. Note: vs `origin/main` these are *new* files (added by original PR commit), so the main…HEAD diff is a full addition, not empty — expected, not a violation.

**5. Dispositions** — 32 `disposition: ACCEPT`, 0 DEFER, 0 REJECT in ledger YAML; binding JSON confirms `accepted_decision_count:32, deferred:0, rejected:0`. One extra `disposition: CORRECTED_BY_EXTERNAL_RATIFICATION_RECORD` exists under `carried_forward` item R2A-01 — not a SB-DEC decision disposition; consistent with binding JSON's `r2a01` field.

**6. Binding hash consistency** — `a23efdc6…07b34` verified as actual SHA-256 of `RATIFICATION_BINDING.json` itself (self-consistent), present in `PROOF_POINTERS.json`, `ARCHITECTURE_AUTHORITY_HEAD.json`, `PERSISTENCE_RECEIPT.json`, `readme.md`, `SOURCE_SHA256SUMS.txt`, and all 3 projection frontmatter blocks.

**7. Forbidden surfaces** — none in diff. Confirmed via name-status.

**8. Validators** —
- `validate_change_contract.py --base origin/main --head HEAD`: `status=PASS`, 14 paths, exit 0
- `docs_frontmatter_guard.py --fix …/authority/*.md`: "All docs have valid frontmatter", exit 0, `diff -r` vs backup confirmed zero modifications
- `check_docs_filename_hygiene.py --check --all-files`: `violations=0 OK`, exit 0

**9. Master index** — single-line change: link `README.md` → `readme.md` (lowercase); only change to that file.

**10. readme.md framing** — frontmatter `id: second-brain-architecture-authority`, presents itself as entry point; explicitly states "The projections are not a second architecture authority. The exact source bytes under `proof/` remain the evidentiary authority." Not listed as immutable member in SOURCE_SHA256SUMS.txt; no byte-identity claim.
<!-- markdownlint-enable -->

## Verdict

```text
verdict:                         PASS_WITH_NONBLOCKING_OBSERVATIONS
scope_violation:                 NO
byte_identity_source_records:    3/3 verified
projection_body_equivalence:     3/3 verified
ratification_binding_unchanged:  YES
operator_dispositions_unchanged: YES, 32 ACCEPT / 0 DEFER / 0 REJECT
architecture_semantics_changed:  NO
```

Non-blocking observations:

- The three machine metadata files (`RATIFICATION_BINDING.json`, `ARCHITECTURE_AUTHORITY_HEAD.json`,
  `OPERATOR_DECISION_LEDGER.yaml`) are new additions relative to `origin/main` (added by the
  original PR #1206 commit, not this repair); the repair commit itself leaves them byte-untouched.
  Not a defect — expected given the diff base chosen.
- `OPERATOR_DECISION_LEDGER.yaml` carries one additional `disposition:
  CORRECTED_BY_EXTERNAL_RATIFICATION_RECORD` entry under the R2A-01 carried-forward item, distinct
  from the 32 SB-DEC decision dispositions. Pre-existing from the original PR head, consistent with
  `RATIFICATION_BINDING.json`'s `r2a01` field, not introduced by this repair.
