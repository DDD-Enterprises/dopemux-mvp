# Rollback Plan: TP-DMX-PYASN1-SECURITY-W1-001

## Single-Commit Rollback
If a issue is detected post-merge, revert the commit:
```bash
git revert <COMMIT_SHA> -m "revert: pyasn1 0.6.4 update"
```

## Manual Lock Restoration
To restore locks to `pyasn1 0.6.3`:
```bash
git checkout origin/main -- uv.lock docker/mcp-servers-source/pal/pal-mcp-server/uv.lock
uv sync --frozen
cd docker/mcp-servers-source/pal/pal-mcp-server && uv sync --frozen
```
