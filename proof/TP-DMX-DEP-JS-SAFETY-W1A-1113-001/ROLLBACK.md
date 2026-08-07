# Rollback Guide: TP-DMX-DEP-JS-SAFETY-W1A-1113-001

## 1. Pre-Push Local Restoration
To abandon local worktree changes and reset to the pre-packet remote PR head:
```bash
git reset --hard origin/dependabot/npm_and_yarn/next-15.5.21
```

## 2. Post-Merge Reversion
If merged into `main`, revert the dependency bump commit cleanly without force-push or history rewrite:
```bash
git revert -m 1 <COMMIT_SHA> -m "revert(deps): rollback Next.js 15.5.21 security patch refresh"
git push origin main
```
