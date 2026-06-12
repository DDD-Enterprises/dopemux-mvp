# Validation Report

- status: ValidationStatus.FAILED
- passed: False
- attempts: 1
- remediation_applied: False

## Steps
### pre-commit
- command: `pre-commit run`
- status: failed
- exit_code: 3

```text
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to /Users/hue/.cache/pre-commit/patch1777619099-96375.
Validate YAML frontmatter in docs......................................(no files to check)Skipped
Validate documentation against knowledge graph schema..................(no files to check)Skipped
Block prohibited documentation patterns (NOTES, TODO, TEMP, etc.)......(no files to check)Skipped
Validate prelude ≤100 tokens for efficient embeddings..................(no files to check)Skipped
Enforce markdown file locations for changed files......................(no files to check)Skipped
Enforce docs placement hygiene (changed files).........................(no files to check)Skipped
Enforce docs filename hygiene (kebab-case).............................(no files to check)Skipped
Audit docs filename hygiene (kebab-case, full-tree legacy debt)............................Passed
Reject executable/config code under UPGRADES (docs-only legacy tree)...(no files to check)Skipped
Enforce repository root hygiene (no random root files).................(no files to check)Skipped
markdownlint...........................................................(no files to check)Skipped
trim trailing whitespace...............................................(no files to check)Skipped
fix end of files.......................................................(no files to check)Skipped
check yaml.............................................................(no files to check)Skipped
[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
An unexpected error has occurred: CalledProcessError: command: ('/opt/homebrew/bin/git', '-c', 'core.autocrlf=false', 'apply', '--whitespace=nowarn', '/Users/hue/.cache/pre-commit/patch1777619099-96375')
return code: 1
stdout: (none)
stderr:
    error: patch failed: docs/03-reference/Dopemux Cockpit TUI Design System/ACCEPTANCE.md:22
    error: docs/03-reference/Dopemux Cockpit TUI Design System/ACCEPTANCE.md: patch does not apply
    error: patch failed: docs/03-reference/Dopemux Cockpit TUI Design System/SKILL.md:12
    error: docs/03-reference/Dopemux Cockpit TUI Design System/SKILL.md: patch does not apply
Check the log at /Users/hue/.cache/pre-commit/pre-commit.log
```

## Fingerprint
- input_fingerprint: `78bf57a3e003c536bf201d80ca51b453c746f465af76d8d9bfc6c3bcab2ed8b4`
- valid_for_sha: `910ce7f03b18f8ff2156ac3e63e6e2920432730d`
- created_from_state: `applied`
