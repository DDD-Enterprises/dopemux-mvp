# Advanced PR Merger Solution

## Overview

This solution provides a comprehensive approach to automatically manage GitHub Pull Requests by:

1. **Resolving review comments and threads** using GitHub GraphQL API
2. **Updating PR branches** with the latest changes from their base branch
3. **Intelligently resolving merge conflicts** (simple ones automatically, complex ones flagged for LLM assistance)
4. **Enabling auto-merge** for PRs that are ready
5. **Providing detailed reporting** on what was accomplished and what needs manual attention

## Files Created

### 1. `advanced_pr_merger.py` (Main Solution)

**Key Features:**
- **Comment Resolution**: Automatically resolves all review threads and comments on PRs
- **Conflict Detection**: Identifies and classifies merge conflicts by type and complexity
- **Automatic Resolution**: Handles simple conflicts automatically using intelligent strategies
- **LLM Assistance Framework**: Flags complex conflicts for LLM-assisted resolution
- **Auto-Merge Enablement**: Enables auto-merge with squash for ready PRs
- **Comprehensive Reporting**: Provides detailed summary of processing results

### 2. Supporting Scripts

- `batch_merger.py` - Initial basic version
- `batch_merger_v2.py` - Improved error handling
- `batch_merger_v3.py` - Added force push support
- `batch_merger_final.py` - Comprehensive conflict resolution
- `test_single_pr.py` - Testing harness

## How It Works

### 1. PR Discovery
```bash
gh pr list --state open --json number,headRefName,baseRefName,title,reviewDecision,isDraft
```

### 2. Comment Resolution
Uses GitHub GraphQL API to:
- Query all unresolved review threads
- Automatically resolve each thread
- Handle comments from different authors

### 3. Branch Update Process
1. **Ensure clean working directory** (stash changes, abort merges)
2. **Checkout PR branch**
3. **Fetch latest base branch** (usually main)
4. **Attempt merge or rebase**
5. **Handle conflicts** if they occur

### 4. Conflict Resolution Strategy

#### Conflict Types Handled:
- **both_modified**: Both branches modified the same file
- **modified_deleted**: One modified, other deleted
- **deleted_modified**: One deleted, other modified  
- **both_deleted**: Both branches deleted the file
- **both_added**: Both branches added the same file

#### Resolution Strategies:
- **Simple Conflicts**: Automatically resolved using preference rules
- **Moderate Conflicts**: Automatically resolved with smart merging
- **Complex Conflicts**: Flagged for LLM assistance, saved as JSON requests

### 5. Auto-Merge Enablement
```bash
gh pr merge <PR_NUMBER> --auto --squash
```

## Usage

### Basic Usage
```bash
python3 advanced_pr_merger.py
```

### Expected Output
```
🚀 Starting Advanced PR Merger...
📋 Found 20 open PRs to process

============================================================
📝 Processing PR 1/20 - #102: chore: cleanup secrets and add features
============================================================
💬 Resolving comments and threads for PR #102...
   Found 0 unresolved threads
🔍 Processing PR #102: chore: cleanup secrets and add features
   Branch: cleanup-secrets-and-add-features, Base: main
   ✅ Clean working directory ensured
   ✅ Checked out cleanup-secrets-and-add-features
   ✅ Fetched main
   🔄 Attempting merge...
   🔧 Resolving merge conflicts for PR #102...
   📁 Conflict in .pre-commit-config.yaml - Type: both_modified, Complexity: simple
   🔧 Attempting automatic resolution for .pre-commit-config.yaml (both_modified)...
   ✅ Automatically resolved .pre-commit-config.yaml
   ✅ Committed merge resolution
   ✅ Pushed branch successfully
   ✅ Enabled auto-merge for PR #102
   ✅ Successfully processed PR #102

📊 Processing Summary:
   ✅ Successfully processed: 15
   🤖 Requires LLM assistance: 3
   ⚠️  Not ready for merge: 2
   📋 Total PRs: 20

🎯 Next Steps:
   1. Review LLM conflict resolution requests (llm_conflict_*.json files)
   2. Process complex conflicts with LLM assistance
   3. Manually review 2 PRs that aren't ready for merge
   4. Monitor auto-merge progress for 15 processed PRs
```

## Conflict Resolution Examples

### Simple Conflict (Automatic)
```
<<<<<<< HEAD
# Main branch version
feature_enabled = False
=======
# PR branch version  
feature_enabled = True
>>>>>>> branch
```
**Resolution**: Keeps PR branch version (prefers "current" changes)

### Complex Conflict (LLM Assistance)
```
<<<<<<< HEAD
# Main branch - complex logic
def calculate_total():
    return sum(items) + tax - discount
=======
# PR branch - different complex logic  
def calculate_total():
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate) - discount_amount
>>>>>>> branch
```
**Resolution**: Flagged for LLM assistance, saved as structured JSON request

## Requirements

- GitHub CLI (`gh`) installed and authenticated
- Python 3.7+
- Git 2.20+
- GitHub API permissions (read/write for PRs)

## Installation

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Make script executable
chmod +x advanced_pr_merger.py
```

## Error Handling

The script handles various edge cases:
- **Non-fast-forward pushes**: Uses `--force-with-lease` when needed
- **Merge/rebase failures**: Automatically aborts and cleans up
- **Git index issues**: Resets and cleans working directory
- **Rate limiting**: Includes delays between PR processing
- **Authentication errors**: Provides clear error messages

## Limitations

1. **Complex Conflicts**: Requires LLM assistance or manual resolution
2. **PR Approvals**: Doesn't automatically approve PRs (requires human review)
3. **CI Checks**: Doesn't wait for CI to pass before enabling auto-merge
4. **Large Files**: May struggle with very large conflicted files

## Future Enhancements

1. **LLM Integration**: Direct API calls to resolve complex conflicts
2. **CI Monitoring**: Wait for and monitor CI check results
3. **Batch Processing**: Process PRs in parallel where possible
4. **Webhook Integration**: Trigger on PR events
5. **Slack Notifications**: Send progress updates to team channels

## Safety Features

- **Force-with-lease**: Safer than regular force push
- **Conflict Backup**: Creates JSON backups of complex conflicts
- **Dry Run Mode**: (Planned) Test without making changes
- **Progress Tracking**: Detailed logging of all operations

## Monitoring Auto-Merge Progress

After running the script, monitor progress with:

```bash
# Check auto-merge status
gh pr view <PR_NUMBER> --json autoMergeRequest

# List PRs with auto-merge enabled  
gh pr list --search "is:open is:mergeable auto-merge:enabled"

# Check CI status
gh pr checks <PR_NUMBER>
```

## Troubleshooting

### Git Index Issues
```bash
rm -f .git/index.lock
git reset --hard HEAD
```

### Authentication Problems
```bash
gh auth status
gh auth login
```

### Rate Limiting
```bash
# Check rate limits
gh api rate_limit

# Wait and retry
sleep 60 && python3 advanced_pr_merger.py
```

## Conclusion

This solution provides a robust framework for automating PR management while intelligently handling the complexities of real-world Git workflows. It balances automation with safety, handling what it can automatically while clearly flagging what needs human or LLM assistance.