# ConPort Wave 0 Git Custody Verification

Bundle contains baseline, reviewed ADR commit, and original Wave 0 proof head. It requires baseline parent `9d7878092e31d021eceaf829355e73bec33b36eb`, available from repository history.

From a clone containing baseline history:

```bash
git bundle verify git-custody/CONPORT-W0-ADR-CUSTODY.bundle
git fetch git-custody/CONPORT-W0-ADR-CUSTODY.bundle \
  refs/heads/docs/conport-crs-v2-adr-wave0:refs/remotes/custody/conport-wave0

git show -s --format='%H %P %T' a5b9006aa3f5a95f81e4bab324931ade71ee8b31
git merge-base 5a9f8f7b5d4a03be323723a92baf3c4e162d5b65 \
  a5b9006aa3f5a95f81e4bab324931ade71ee8b31
git rev-list --count \
  5a9f8f7b5d4a03be323723a92baf3c4e162d5b65..a5b9006aa3f5a95f81e4bab324931ade71ee8b31

git diff --binary --unified=0 \
  5a9f8f7b5d4a03be323723a92baf3c4e162d5b65 \
  a5b9006aa3f5a95f81e4bab324931ade71ee8b31 \
  -- docs/90-adr > /tmp/recomputed-wave0.patch
cmp /tmp/recomputed-wave0.patch wave0-proof/WAVE0-DIFF.patch
```

Expected commit receipt:

```text
a5b9006aa3f5a95f81e4bab324931ade71ee8b31 5a9f8f7b5d4a03be323723a92baf3c4e162d5b65 73fe54ea841369b3c3126562d8bd1ba22384200d
```

Expected merge base: `5a9f8f7b5d4a03be323723a92baf3c4e162d5b65`.

Expected baseline-to-reviewed commit count: `1`.

For each row in `wave0-proof/WAVE0-GIT-CUSTODY-FILES.json`, compare:

```bash
git show a5b9006aa3f5a95f81e4bab324931ade71ee8b31:<path> > /tmp/reviewed-file
cmp /tmp/reviewed-file changed-adrs/<path>
shasum -a 256 /tmp/reviewed-file changed-adrs/<path>
```

All 22 rows must report `equal: true`. Any mismatch invalidates custody and requires a new package.
