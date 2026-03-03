#!/usr/bin/env python3
"""
Conflict Resolution Helper - Guides through manual merge conflict resolution
"""

import subprocess
import json
import sys
from typing import List, Dict, Tuple

def run_command(cmd: str) -> Tuple[str, str, int]:
    """Run a shell command and return (stdout, stderr, returncode)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def get_open_prs_with_conflicts() -> List[Dict]:
    """Get list of open PRs that have merge conflicts"""
    stdout, stderr, returncode = run_command(
        'gh pr list --state open --json number,title,headRefName,mergeable,mergeStateStatus'
    )
    if returncode != 0:
        print(f"Error getting PRs: {stderr}")
        return []
    
    try:
        prs = json.loads(stdout)
        # Filter for PRs that likely have conflicts
        return [pr for pr in prs 
                if pr.get('mergeable') in ['CONFLICTING', 'UNKNOWN'] 
                or pr.get('mergeStateStatus') in ['DIRTY', 'UNKNOWN']]
    except json.JSONDecodeError:
        print(f"Failed to parse PR list")
        return []

def show_conflict_resolution_guide():
    """Show step-by-step guide for resolving merge conflicts"""
    print("""
🚀 MERGE CONFLICT RESOLUTION GUIDE
==================================

STEP 1: Check out the PR branch
-------------------------------
git checkout <branch-name>
Example: git checkout fix/desktop-commander-security-exposure-339845444623396959

STEP 2: Attempt merge with base branch
--------------------------------------
git merge origin/main

STEP 3: Identify conflicted files
---------------------------------
git status
# Look for "both modified" files

STEP 4: Resolve conflicts in each file
--------------------------------------
# Open each conflicted file in your editor
# Look for conflict markers: <<<<<<< HEAD ... ======= ... >>>>>>>>
# Edit the file to keep the correct changes
# Remove all conflict markers

STEP 5: Mark conflicts as resolved
----------------------------------
git add <file1> <file2> ...
# Or add all resolved files:
git add .

STEP 6: Commit the resolution
-----------------------------
git commit -m "Resolve merge conflicts"

STEP 7: Push the changes
------------------------
git push origin <branch-name> --force-with-lease

STEP 8: Approve the PR
---------------------
gh pr review <PR_NUMBER> --approve

💡 TIPS FOR CONFLICT RESOLUTION:
=============================
1. Use a visual diff tool: git mergetool
2. Check PR description for context
3. Look at recent commits in the PR
4. When in doubt, favor the PR changes (they're newer)
5. Test the resolution before pushing

🔧 COMMON GIT COMMANDS:
=====================
git merge --abort      # Abort merge and start over
git reset --hard       # Reset to clean state
git status            # Check current status
git diff              # See uncommitted changes
git log --oneline     # See recent commits
""")

def provide_pr_specific_help(pr: Dict):
    """Provide specific help for a PR"""
    pr_number = pr['number']
    branch_name = pr['headRefName']
    title = pr['title']
    
    print(f"""
📋 PR #{pr_number}: {title}
==================================
Branch: {branch_name}

STEP-BY-STEP RESOLUTION:
-----------------------

1. Check out the branch:
   git checkout {branch_name}

2. Attempt merge:
   git merge origin/main

3. If conflicts occur, resolve them:
   - Open conflicted files in your editor
   - Look for <<<<<<< HEAD ... ======= ... >>>>>>>>> markers
   - Edit to keep the correct code
   - Remove all conflict markers

4. Add resolved files:
   git add .

5. Commit:
   git commit -m "Resolve merge conflicts for PR #{pr_number}"

6. Push:
   git push origin {branch_name} --force-with-lease

7. Approve:
   gh pr review {pr_number} --approve

🔍 PR DETAILS:
=============
""")
    
    # Get PR details
    stdout, stderr, returncode = run_command(f"gh pr view {pr_number} --json files")
    if returncode == 0:
        try:
            details = json.loads(stdout)
            files = details.get('files', [])
            if files:
                print("Files in this PR:")
                for file in files[:10]:  # Show first 10 files
                    print(f"  - {file.get('path', 'Unknown')}")
                if len(files) > 10:
                    print(f"  ... and {len(files) - 10} more files")
        except json.JSONDecodeError:
            pass
    
    print("\n🎯 After resolving conflicts, this PR will be ready for auto-merge!")

def main():
    """Main function"""
    print("🚀 MERGE CONFLICT RESOLUTION HELPER")
    print("=" * 60)
    
    # Get PRs with conflicts
    prs = get_open_prs_with_conflicts()
    
    if not prs:
        print("🎉 No PRs with conflicts found!")
        return
    
    print(f"📋 Found {len(prs)} PRs that need conflict resolution")
    print("=" * 60)
    
    # Show general guide first
    show_conflict_resolution_guide()
    
    # Provide specific help for each PR
    for i, pr in enumerate(prs, 1):
        print(f"\n{'='*60}")
        print(f"PR {i}/{len(prs)}: #{pr['number']} - {pr['title']}")
        print(f"{'='*60}")
        provide_pr_specific_help(pr)
    
    print(f"\n{'='*60}")
    print("🎯 SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Conflict resolution guide provided")
    print(f"✅ Specific instructions for {len(prs)} PRs")
    print(f"✅ Ready to resolve conflicts and merge PRs!")
    print("\n💡 Start with the first PR and work through them one by one.")
    print("   The automation system will handle the rest once conflicts are resolved!")

if __name__ == "__main__":
    main()
