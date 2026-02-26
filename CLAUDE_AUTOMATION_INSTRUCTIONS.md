# Claude Automation Instructions

Operator runbook for the v4 prompt rewrite batch harness.

## What This Does

Enriches v4 prompt files by replacing their Extraction Procedure section with domain-specific discovery steps and appending failure mode bullets. Uses Claude Opus in patch-only mode to produce minimal unified diffs, validated and applied one file at a time.

## Prerequisites

- Python 3.11+
- `pyperclip` installed (`pip install pyperclip`)
- Clean git working tree (`git status --porcelain` should be empty before starting)
- Files present:
  - `tools/prompt_rewrite_v4/config.json` (batch configuration)
  - `tools/prompt_rewrite_v4/state.json` (cursor and audit trail)
  - `tools/prompt_rewrite_v4/OPUS_SYSTEM_PROMPT.txt` (system prompt for Claude)
  - `tools/prompt_rewrite_v4/HEURISTICS_LIBRARY_v1.md` (domain knowledge reference)

## Step-by-Step Batch Cycle

Each prompt file goes through three phases. Repeat until cursor reaches end of file list.

### Phase 1: Render

```bash
python tools/prompt_rewrite_v4/run_batch.py --render
```

What happens:
1. Reads cursor from `state.json`, loads prompt file at that index
2. Pre-validates that both `Extraction Procedure` and `Failure Modes` section headings exist
3. Computes SHA256 of original file
4. Writes `out/request_N.txt` with heuristics + prompt content
5. Prints next-step instructions to stdout

Output example:
```
WROTE: /Users/hue/code/dopemux-mvp/out/request_6.txt
SHA256: d39af49c18e888fbf87abff2a36932105e5038e1794fe9c6fe112c860c75d86c
NEXT: run Opus in Claude Code using .../OPUS_SYSTEM_PROMPT.txt + .../out/request_6.txt
SAVE PATCH AS: .../out/response_6.patch
```

### Phase 2: Run Claude (Manual)

1. Set model to Opus: `/model opus`
2. Paste the full contents of `OPUS_SYSTEM_PROMPT.txt` followed by `out/request_N.txt` as your message to Claude
3. Claude outputs a unified diff (no prose, no markdown fences)
4. Select and copy the entire diff output
5. Run the patch capture script:

```bash
./patchit
```

This reads your clipboard, auto-repairs common formatting issues (missing git headers, trailing whitespace), and writes `out/response_N.patch`.

If `patchit` reports a validation warning, inspect the patch file before proceeding.

### Phase 3: Apply

```bash
python tools/prompt_rewrite_v4/run_batch.py --apply
```

What happens:
1. Validates patch:
   - Is valid unified diff (has `--- a/`, `+++ b/`, `@@ -` markers)
   - Line count <= 350
   - Paths match expected prompt file
   - In-memory simulation: all deleted lines within Extraction Procedure or Failure Modes (original bounds), all added lines within those sections (patched bounds)
2. Runs `git apply --whitespace=nowarn`
3. Runs lint gate: `python scripts/repo_truth_extractor_promptset_audit_v4.py --strict`
4. Computes SHA256 after patch
5. Moves entry from `in_progress` to `completed`, advances cursor

Output on success:
```
APPLIED + LINT PASS: services/repo-truth-extractor/.../PROMPT_A6_COMPOSE_SERVICE_GRAPH.md
SHA256: <new_hash>
ADVANCED CURSOR -> 7
```

### Repeat

Go back to Phase 1. When `--render` prints `DONE: cursor at end of file list`, all files are processed.

## Error Handling Procedures

### Error Reference

| Error Message | Cause | Recovery |
|---------------|-------|----------|
| `patch with only garbage at line N` | Copy-paste corruption; extra whitespace, markdown fences, or prose mixed into diff | Re-copy diff from Claude (raw text only, no fences), re-run `./patchit`, then `--apply` |
| `Not a unified diff` | Claude output prose instead of a diff | Re-prompt Claude; ensure system prompt is loaded |
| `Added line N outside allowed sections` | Patch edits sections beyond Extraction Procedure / Failure Modes | Re-prompt Claude or manually trim the patch to only touch allowed sections |
| `Deleted line N outside allowed sections` | Same as above but for deletions | Same recovery |
| `patch does not apply` | Source file changed since render, or hunk line numbers are stale | Re-run `--render` to regenerate the request, then redo the full cycle |
| `Patch exceeds max_patch_lines=350` | Diff too large | Re-prompt Claude to produce a more concise diff, or increase `max_patch_lines` in `config.json` |
| `Model reported OUTPUT_LIMIT_REACHED` | Claude detected its diff would exceed 350 lines | Same as above |
| `Diff targets do not match expected path` | Patch modifies a different file than expected | Re-prompt Claude; verify request file references correct prompt |
| `Missing required sections` (pre-render) | Prompt file lacks `Extraction Procedure` or `Failure Modes` heading | Add stub section headings to the prompt file, then re-run `--render` |
| `Patch apply failed in-memory: overlapping hunks` | Malformed hunk ranges in diff | Re-prompt Claude for a clean diff |
| Lint gate failure (non-zero exit) | Patch broke prompt structure rules | Inspect `git diff`, fix manually or `git checkout -- <file>` and retry |
| `Missing patch file: out/response_N.patch` | Phase 2 not completed | Run Claude + `./patchit` first |

### General Recovery Pattern

1. Check `state.json` -> `failed[]` for the failure reason
2. The cursor does NOT advance on failure, so the same file will be retried
3. Fix the issue:
   - **Bad patch**: re-copy from Claude, re-run `./patchit`
   - **Stale render**: re-run `--render` (overwrites `request_N.txt`)
   - **Structural issue**: edit the prompt file or patch manually
4. Re-run `--apply`

### Manual Patch Repair

If `./patchit` produces a patch that fails validation:

```bash
# Inspect the patch
cat out/response_N.patch

# Validate manually
python tools/prompt_rewrite_v4/validate_patch.py \
  --diff out/response_N.patch \
  --expected-relpath "services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_AN_NAME.md" \
  --original "services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_AN_NAME.md"

# Test apply without modifying files
git apply --check out/response_N.patch
```

### Reverting a Bad Apply

If `git apply` succeeded but the lint gate failed:

```bash
# The file is already modified on disk. Revert it:
git checkout -- services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_AN_NAME.md

# Fix the patch or re-prompt, then retry --apply
```

## Monitoring Guidelines

### Progress Tracking

```bash
# Quick status
python -c "
import json, glob as g
s = json.load(open('tools/prompt_rewrite_v4/state.json'))
total = len(g.glob('services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_*.md'))
print(f'Progress: {s[\"cursor\"]}/{total}')
print(f'Done: {len(s.get(\"done\", []))}')
print(f'Failed: {len(s.get(\"failed\", []))}')
print(f'In-progress: {len(s.get(\"in_progress\", []))}')
"
```

### Health Checks

| Check | Command | Expected |
|-------|---------|----------|
| Clean working tree | `git status --porcelain` | Only modified prompt files (if mid-cycle) |
| No stale in-progress | Check `state.json` `in_progress[]` | Empty between cycles |
| Failure trend | Check `state.json` `failed[]` length | Not growing rapidly |
| Lint compliance | `python scripts/repo_truth_extractor_promptset_audit_v4.py --strict` | Exit 0 |

### Audit Trail

Each entry in `state.json` `completed[]` contains:
- `sha256_before`: hash of original file before patch
- `sha256_after`: hash after successful patch + lint
- `started_at` / `completed_at`: timestamps
- `request_path` / `response_path`: preserved in `out/` for review

### Inspecting Failures

```bash
# List all failure reasons
python -c "
import json
s = json.load(open('tools/prompt_rewrite_v4/state.json'))
for f in s.get('failed', []):
    print(f'Cursor {f[\"cursor\"]}: {f[\"reason\"]}')
"
```

### State File Location

`tools/prompt_rewrite_v4/state.json` - do not delete. This is the resume mechanism.

To reset and reprocess a file, manually set `cursor` back to the desired index.

## Quick Reference

```bash
# Full cycle for one prompt file:
python tools/prompt_rewrite_v4/run_batch.py --render
# ... run Claude Opus, copy diff output ...
./patchit
python tools/prompt_rewrite_v4/run_batch.py --apply

# Check batch progress:
python -c "import json; s=json.load(open('tools/prompt_rewrite_v4/state.json')); print(f'Cursor: {s[\"cursor\"]}, Done: {len(s.get(\"done\",[]))}, Failed: {len(s.get(\"failed\",[]))}')"

# Re-render after failure (safe, overwrites request file):
python tools/prompt_rewrite_v4/run_batch.py --render

# Validate a patch without applying:
python tools/prompt_rewrite_v4/validate_patch.py --diff out/response_N.patch --expected-relpath <path> --original <path>

# Test patch application without modifying files:
git apply --check out/response_N.patch
```

## File Reference

| File | Purpose |
|------|---------|
| `tools/prompt_rewrite_v4/run_batch.py` | Main orchestrator (--render / --apply) |
| `tools/prompt_rewrite_v4/config.json` | Glob pattern, paths, limits, lint command |
| `tools/prompt_rewrite_v4/state.json` | Cursor, done/failed/completed/in_progress tracking |
| `tools/prompt_rewrite_v4/validate_patch.py` | Section-aware patch validation |
| `tools/prompt_rewrite_v4/render_request.py` | Request text composition |
| `tools/prompt_rewrite_v4/clipboard_to_patch.py` | Clipboard-to-patch bridge (`./patchit`) |
| `tools/prompt_rewrite_v4/OPUS_SYSTEM_PROMPT.txt` | Hard rules for Claude Opus patch mode |
| `tools/prompt_rewrite_v4/HEURISTICS_LIBRARY_v1.md` | Domain knowledge for extraction step generation |
| `scripts/repo_truth_extractor_promptset_audit_v4.py` | Lint gate (--strict mode) |
