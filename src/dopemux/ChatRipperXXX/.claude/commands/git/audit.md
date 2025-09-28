# git/audit
Use **git_local** MCP to inspect the repo and draft a plan.

**Args**: *(optional)* `$ARGUMENTS` = `<PATH>` (default = current repo)

**Steps**
1) Run git_status and summarize staged/unstaged/untracked; then show a focused list of hot files (top 10 by churn).
2) Run git_diff for unstaged changes; produce a bullet plan of fixes/refactors/tests to write.
3) Offer to generate **commit messages per scope** and a top-level conventional commit.

**Tools**: git_local only. Do NOT run actual `git commit`—just prepare messages unless I confirm.
