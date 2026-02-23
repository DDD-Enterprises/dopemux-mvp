#!/usr/bin/env python3
"""
Working PR Merger - Based on the simple version that works
"""

import subprocess
import json
from typing import List, Dict

def get_open_prs() -> List[Dict]:
    """Get list of open PRs using gh CLI"""
    result = subprocess.run(
        'gh pr list --state open --json number,title,reviewDecision,mergeable,mergeStateStatus',
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Error getting PRs: {result.stderr}")
        return []
    
    try:
        prs = json.loads(result.stdout)
        return sorted(prs, key=lambda x: x['number'])
    except json.JSONDecodeError:
        print(f"Failed to parse PR list")
        return []

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
    result = subprocess.run(
        f"gh pr merge {pr_number} --auto --squash",
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print(f"  ✅ Auto-merge enabled successfully!")
        return True
    else:
        print(f"  ❌ Failed to enable auto-merge: {result.stderr}")
        return False

def main():
    """Main function"""
    print("🚀 PR Merger - Enabling auto-merge for ready PRs")
    print("=" * 60)
    
    prs = get_open_prs()
    if not prs:
        print("No open PRs found.")
        return
    
    print(f"📋 Found {len(prs)} open PRs")
    print("=" * 60)
    
    ready_count = 0
    not_ready_count = 0
    
    for pr in prs:
        pr_number = pr['number']
        title = pr['title']
        
        print(f"\n🔍 PR #{pr_number}: {title}")
        
        if is_pr_ready_for_merge(pr):
            print(f"  ✅ PR is ready for auto-merge!")
            if enable_auto_merge(pr_number):
                ready_count += 1
        else:
            not_ready_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Ready and auto-merge enabled: {ready_count}")
    print(f"   ❌ Not ready for auto-merge: {not_ready_count}")
    print(f"   📋 Total PRs processed: {len(prs)}")

if __name__ == "__main__":
    main()
