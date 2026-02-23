#!/usr/bin/env python3
"""
Comprehensive PR Processor - Handles comment resolution, branch updates, and auto-merge
"""

import subprocess
import json
import time
import sys
from typing import List, Dict, Tuple

def run_command(cmd: str) -> Tuple[str, str, int]:
    """Run a shell command and return (stdout, stderr, returncode)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def get_open_prs() -> List[Dict]:
    """Get list of open PRs using gh CLI"""
    stdout, stderr, returncode = run_command(
        'gh pr list --state open --json number,title,headRefName,baseRefName,reviewDecision,mergeable,mergeStateStatus'
    )
    if returncode != 0:
        print(f"Error getting PRs: {stderr}")
        return []
    
    try:
        prs = json.loads(stdout)
        return sorted(prs, key=lambda x: x['number'])
    except json.JSONDecodeError:
        print(f"Failed to parse PR list")
        return []

def get_pr_details(pr_number: int) -> Dict:
    """Get detailed information about a specific PR"""
    stdout, stderr, returncode = run_command(
        f"gh pr view {pr_number} --json number,title,headRefName,baseRefName,reviewDecision,mergeable,mergeStateStatus"
    )
    if returncode != 0:
        print(f"Failed to get PR details for #{pr_number}: {stderr}")
        return {}
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse PR details for #{pr_number}")
        return {}

def resolve_pr_comments(pr_number: int) -> bool:
    """Resolve all comments and review threads on a PR"""
    print(f"  💬 Resolving comments for PR #{pr_number}...")
    
    # Get review threads
    query = f'''
    query {{
      repository(owner:"DDD-Enterprises", name:"dopemux-mvp") {{
        pullRequest(number: {pr_number}) {{
          reviewThreads(first: 100) {{
            nodes {{
              id
              isResolved
            }}
          }}
        }}
      }}
    }}
    '''
    
    stdout, stderr, returncode = run_command(f'gh api graphql -f query=\'{query}\'')
    if returncode != 0:
        print(f"    ❌ Failed to get review threads: {stderr}")
        return False
    
    try:
        data = json.loads(stdout)
        threads = data.get('data', {}).get('repository', {}).get('pullRequest', {}).get('reviewThreads', {}).get('nodes', [])
        
        unresolved = [t for t in threads if not t.get('isResolved', True)]
        print(f"    Found {len(unresolved)} unresolved threads")
        
        for thread in unresolved:
            thread_id = thread['id']
            mutation = '''
            mutation($id: ID!) {
              resolveReviewThread(input: {threadId: $id}) {
                thread { isResolved }
              }
            }
            '''
            resolve_result = run_command(f'gh api graphql -f query=\'{mutation}\' -f id={thread_id}')
            if resolve_result[2] != 0:
                print(f"      ❌ Failed to resolve thread {thread_id}")
            else:
                print(f"      ✅ Resolved thread {thread_id}")
        
        return True
        
    except json.JSONDecodeError:
        print(f"    ❌ Failed to parse review threads response")
        return False

def update_pr_branch(pr: Dict) -> bool:
    """Update a PR branch with latest from base branch"""
    pr_number = pr['number']
    branch_name = pr['headRefName']
    base_branch = pr['baseRefName']
    
    print(f"  🔄 Updating branch for PR #{pr_number}...")
    
    # Store current branch
    current_branch_stdout, _, _ = run_command("git branch --show-current")
    current_branch = current_branch_stdout.strip()
    
    try:
        # Checkout PR branch
        stdout, stderr, returncode = run_command(f"git checkout {branch_name}")
        if returncode != 0:
            print(f"    ❌ Failed to checkout branch: {stderr}")
            return False
        
        # Fetch latest base
        stdout, stderr, returncode = run_command(f"git fetch origin {base_branch}")
        if returncode != 0:
            print(f"    ❌ Failed to fetch base: {stderr}")
            return False
        
        # Try merge first
        stdout, stderr, returncode = run_command(f"git merge origin/{base_branch}")
        if returncode == 0:
            print(f"    ✅ Merge successful")
        else:
            # Try rebase if merge fails
            run_command("git merge --abort")
            stdout, stderr, returncode = run_command(f"git rebase origin/{base_branch}")
            if returncode == 0:
                print(f"    ✅ Rebase successful")
            else:
                print(f"    ⚠️  Update failed (conflicts need manual resolution)")
                run_command("git rebase --abort")
                return False
        
        # Push changes
        stdout, stderr, returncode = run_command(f"git push origin {branch_name}")
        if returncode != 0 and "non-fast-forward" in stderr:
            stdout, stderr, returncode = run_command(f"git push origin {branch_name} --force-with-lease")
        
        if returncode == 0:
            print(f"    ✅ Branch updated successfully")
            return True
        else:
            print(f"    ❌ Failed to push: {stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Error updating branch: {e}")
        return False
    finally:
        run_command(f"git checkout {current_branch}")

def is_pr_ready_for_merge(pr: Dict) -> bool:
    """Check if PR is ready for auto-merge"""
    # Check if approved
    review_decision = pr.get('reviewDecision', '')
    if review_decision != 'APPROVED':
        if review_decision:
            print(f"  ❌ Not approved: {review_decision}")
        else:
            print(f"  ⏳ Waiting for review approval")
        return False
    
    # Check if mergeable
    mergeable = pr.get('mergeable')
    if mergeable != 'MERGEABLE':
        print(f"  ❌ Not mergeable: {mergeable}")
        return False
    
    # Check merge state status
    merge_state = pr.get('mergeStateStatus')
    if merge_state != 'CLEAN':
        print(f"  ❌ Merge state not clean: {merge_state}")
        return False
    
    return True

def enable_auto_merge(pr_number: int) -> bool:
    """Enable auto-merge for a PR"""
    print(f"  🤖 Enabling auto-merge for PR #{pr_number}...")
    stdout, stderr, returncode = run_command(f"gh pr merge {pr_number} --auto --squash")
    if returncode == 0:
        print(f"  ✅ Auto-merge enabled successfully!")
        return True
    else:
        print(f"  ❌ Failed to enable auto-merge: {stderr}")
        return False

def process_prs_comprehensively() -> None:
    """Process PRs comprehensively with all enhancements"""
    print("🚀 Comprehensive PR Processor")
    print("=" * 60)
    
    prs = get_open_prs()
    if not prs:
        print("No open PRs found.")
        return
    
    print(f"📋 Found {len(prs)} open PRs")
    print("=" * 60)
    
    processed_count = 0
    ready_count = 0
    needs_approval_count = 0
    has_conflicts_count = 0
    
    for pr in prs:
        pr_number = pr['number']
        title = pr['title']
        
        print(f"\n🔍 PR #{pr_number}: {title}")
        processed_count += 1
        
        # Step 1: Resolve comments
        if resolve_pr_comments(pr_number):
            print(f"  ✅ Comments processed")
        
        # Step 2: Update branch if needed
        merge_state = pr.get('mergeStateStatus')
        if merge_state in ['BEHIND', 'DIRTY']:
            if update_pr_branch(pr):
                print(f"  ✅ Branch updated")
                # Refresh PR details after update
                pr = get_pr_details(pr_number)
                if not pr:
                    continue
            else:
                print(f"  ⚠️  Branch update failed")
                has_conflicts_count += 1
                continue
        
        # Step 3: Check if ready for auto-merge
        if is_pr_ready_for_merge(pr):
            if enable_auto_merge(pr_number):
                ready_count += 1
        else:
            needs_approval_count += 1
    
    print(f"\n📊 Processing Summary:")
    print(f"   ✅ Successfully processed: {ready_count}")
    print(f"   ⏳ Waiting for approval: {needs_approval_count}")
    print(f"   🔧 Has conflicts/needs manual work: {has_conflicts_count}")
    print(f"   📋 Total PRs processed: {processed_count}")
    
    if needs_approval_count > 0:
        print(f"\n🎯 Next Steps:")
        print(f"   1. Review and approve {needs_approval_count} PRs waiting for approval")
        if has_conflicts_count > 0:
            print(f"   2. Manually resolve conflicts in {has_conflicts_count} PRs")
        print(f"   3. Re-run this script to process newly-ready PRs")

def main():
    """Main function"""
    process_prs_comprehensively()

if __name__ == "__main__":
    main()
