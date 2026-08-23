# TP-DCP-MCP-RO-0009 Command Log

Commands are summarized with observed outcomes. Full terminal output remains in the Codex session.

## Preflight

```text
pwd
[LOCAL_PATH_REDACTED]

git rev-parse --show-toplevel
[LOCAL_PATH_REDACTED]

git remote -v
mvp/origin -> https://github.com/DDD-Enterprises/dopemux-mvp.git

git branch --show-current
codex/dcp-mcp-ro-0009-exposure-target-contract
```

## Live PR Check

```text
gh pr view 1031 --repo DDD-Enterprises/dopemux-mvp --json number,state,mergedAt,headRefName,baseRefName,mergeCommit,url,title
state: MERGED
mergedAt: 2026-07-10T05:06:09Z
mergeCommit: d170fa756c7708a0da98d51fe1aa0991ecfde9d2
url: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1031
```

## Base-Branch Ancestry Check

```text
git merge-base --is-ancestor d170fa756c7708a0da98d51fe1aa0991ecfde9d2 origin/main
exit: 1

git merge-base --is-ancestor b911e916c208109ecc862c8afa7365ad306d6cba origin/main
exit: 1
```

Interpretation: PR #1031 is merged according to GitHub, but the current `origin/main` ref used for this docs branch does not contain the PR #1031 merge commit or PR branch head by ancestry.

## Validation

```text
python -m json.tool task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0009.json >/tmp/tp-dcp-mcp-ro-0009.valid.json
exit: 0

Draft7Validator against docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
schema: PASS
exit: 0

rg secret-pattern scan over changed markdown docs/proof files
exit: 1
interpretation: PASS, no matches

git diff --check
exit: 0

pre-commit run --files <changed files>
exit: 0
hooks: frontmatter, knowledge graph docs schema, prohibited docs patterns, prelude length, docs hygiene, proof embedded_audit schema, markdownlint, whitespace, EOF
```
