# Command log (representative, not exhaustive)

## Admission gates

```text
gh auth status                                          # confirmed logged in as hu3mann
gh pr view 1206 --repo DDD-Enterprises/dopemux-mvp \
  --json number,title,state,baseRefName,headRefName,headRefOid,body,mergeable,url
  -> headRefOid=16e8596410de9bbdef3db5993c5eaf3f60d8d4b6 (matches expected starting head)
gh pr checks 1206 --repo DDD-Enterprises/dopemux-mvp
  -> confirmed real failing checks: "checks", "independent embedded audit",
     "PR Steward / final readiness", "Code Quality & Linting"
gh api repos/DDD-Enterprises/dopemux-mvp/branches/main/protection --jq '.required_status_checks.contexts'
  -> confirmed independent embedded audit / PR Steward are NOT in the required-status-check set
git ls-remote git@github.com:DDD-Enterprises/dopemux-mvp.git main
  -> e9945786efaaf2994bda32bf2419c391d23ce686
```

## Isolation

```text
git clone git@github.com:DDD-Enterprises/dopemux-mvp.git repo   # into fresh RUN_ROOT/work
git worktree add ../pr1206 tp/DMX-SB-ARCH-AUTHORITY-PERSIST-001
```

## MA-08 fresh drift recheck

```text
git cat-file -t 33d6c353023ecc3aa6331ab39f4f076ae3ca1fda        # commit, exists
git merge-base --is-ancestor 33d6c353... origin/main             -> YES_ANCESTOR
git rev-list --count 33d6c353...origin/main                      -> 1
git diff --stat 33d6c353...origin/main -- docs/ proof/           -> unrelated proof path only
  (proof/TP-DMX-PYASN1-SECURITY-W1-001/**, proof/pr_merge/embedded-audit/** receipts)
  disposition: NEW_DRIFT_CONTAINED
```

## Source authority custody

Ratification package/candidate zip files were not present on the local filesystem; the exact-byte
verification instead used the already-committed copies in PR #1206 (whose own description claims
prior SHA-256+cmp verification against the source package), cross-checked for internal consistency
against `SOURCE_SHA256SUMS.txt` and `PROOF_POINTERS.json` recorded at the original PR head
(all 9/9 recorded hashes matched actual file bytes).

## Repair (in `work/pr1206`)

```text
mkdir -p proof/TP-DMX-.../source-authority
cp docs/.../ARCHITECTURE_RATIFICATION_RECORD.md proof/.../08_ARCHITECTURE_RATIFICATION_RECORD.md
cp docs/.../FINAL_RATIFICATION_VERDICT.md       proof/.../10_FINAL_RATIFICATION_VERDICT.md
cp docs/.../RATIFICATION_CORRECTIONS.md          proof/.../04_RATIFICATION_CORRECTIONS.md
cmp (x3) -> byte-identical
cat <frontmatter> <original> > <projection>.md   (x3, plus readme.md new content)
awk '<strip first --- block>' <projection> | cmp <source>   -> 3/3 PASS
git rm --cached README.md ; git mv README.md -> .tmp -> readme.md   # case-insensitive FS workaround
git rm ARCHITECTURE_RATIFICATION_RECORD.md FINAL_RATIFICATION_VERDICT.md RATIFICATION_CORRECTIONS.md
git add (new projections, proof custody, updated PROOF_POINTERS.json/SOURCE_SHA256SUMS.txt/
         PERSISTENCE_RECEIPT.json, docs/00-MASTER-INDEX.md link fix)
git commit -> 3cf129b127c07e2fbfb3571c8de6c42b22ed688c
```

## Local validation

```text
python3 scripts/docs_frontmatter_guard.py --fix docs/.../authority/*.md    -> 0 changed, PASS
python3 scripts/check_docs_filename_hygiene.py --check --all-files        -> violations=0, OK
python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text
  -> status=PASS, max_lane=L2, model_audit_required=True, 14 paths
pre-commit run --from-ref origin/main --to-ref HEAD                       -> all hooks PASS/Skipped
git status --porcelain=v1                                                 -> clean after all of the above
```

## Independent audit

```text
opencode auth list                                       -> OpenRouter credentials present
opencode models | grep kimi                              -> openrouter/moonshotai/kimi-k3 available
git rev-parse HEAD > pre_audit_head.txt                   # integrity baseline before audit run
opencode run --dir <isolated worktree> -m openrouter/moonshotai/kimi-k3 --variant max --auto \
  "<self-contained audit prompt, checklist per packet §34>"
  -> verdict: PASS_WITH_NONBLOCKING_OBSERVATIONS (see AUDITOR_REPORT.md)
git status --porcelain=v1 ; git rev-parse HEAD             # confirmed worktree untouched by audit run
```
