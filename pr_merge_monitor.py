#!/usr/bin/env python3
"""
PR Merge Monitor - Tracks PR status and enables auto-merge when ready
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
        'gh pr list --state open --json number,title,reviewDecision,mergeable,mergeStateStatus'
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

def get_pr_checks_status(pr_number: int) -> Dict:
    """Get detailed check status for a PR"""
    stdout, stderr, returncode = run_command(f"gh pr checks {pr_number} --json")
    if returncode != 0:
        print(f"Failed to get checks for PR #{pr_number}: {stderr}")
        return {}
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse checks for PR #{pr_number}")
        return {}

def is_pr_ready_for_merge(pr: Dict) -> bool:
    """Check if PR is ready for auto-merge"""
    # Check if mergeable
    mergeable = pr.get('mergeable')
    if mergeable != 'MERGEABLE':
        return False
    
    # Check merge state status
    merge_state = pr.get('mergeStateStatus')
    if merge_state != 'CLEAN':
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

def monitor_prs_continuously(interval: int = 60, max_runs: int = 10) -> None:
    """Monitor PRs continuously and enable auto-merge when ready"""
    print("🚀 PR Merge Monitor")
    print("=" * 60)
    print(f"🔁 Monitoring every {interval} seconds (max {max_runs} runs)")
    print("=" * 60)
    
    for run in range(1, max_runs + 1):
        print(f"\n🔄 MONITORING RUN {run}/{max_runs}")
        print("-" * 60)
        
        prs = get_open_prs()
        if not prs:
            print("No open PRs found.")
            break
        
        print(f"📋 Found {len(prs)} open PRs")
        
        ready_count = 0
        waiting_for_ci_count = 0
        not_ready_count = 0
        
        for pr in prs:
            pr_number = pr['number']
            title = pr['title']
            
            print(f"\n🔍 PR #{pr_number}: {title}")
            
            # Check if ready for merge
            if is_pr_ready_for_merge(pr):
                print(f"  ✅ PR is ready for auto-merge!")
                if enable_auto_merge(pr_number):
                    ready_count += 1
            else:
                # Check why it's not ready
                mergeable = pr.get('mergeable')
                merge_state = pr.get('mergeStateStatus')
                
                if mergeable != 'MERGEABLE':
                    print(f"  ❌ Not mergeable: {mergeable}")
                    not_ready_count += 1
                elif merge_state != 'CLEAN':
                    print(f"  ⏳ Merge state: {merge_state}")
                    
                    # Check CI status
                    checks = get_pr_checks_status(pr_number)
                    if checks:
                        pending_checks = [c for c in checks if c.get('status') == 'PENDING' or c.get('status') == 'QUEUED']
                        if pending_checks:
                            print(f"  ⏳ Waiting for {len(pending_checks)} CI checks to complete")
                            waiting_for_ci_count += 1
                        else:
                            print(f"  ⚠️  Checks completed but merge state not clean")
                            not_ready_count += 1
                    else:
                        print(f"  ⏳ Checking status...")
                        waiting_for_ci_count += 1
        
        # Summary for this run
        print(f"\n📊 Run {run} Summary:")
        print(f"   ✅ Ready and auto-merge enabled: {ready_count}")
        print(f"   ⏳ Waiting for CI/checks: {waiting_for_ci_count}")
        print(f"   ❌ Not ready for merge: {not_ready_count}")
        print(f"   📋 Total PRs monitored: {len(prs)}")
        
        # Check if all PRs are processed
        remaining_prs = len(prs) - ready_count
        if remaining_prs == 0:
            print("\n🎉 All PRs have been processed successfully!")
            break
        
        # Delay before next run (unless this is the last run)
        if run < max_runs:
            print(f"\n⏳ Waiting {interval} seconds before next monitoring run...")
            for i in range(interval, 0, -10):
                print(f"   {i} seconds remaining...")
                time.sleep(10)
    
    print(f"\n🏁 MONITORING COMPLETE after {run} runs")
    print("🎯 Final Status:")
    print("   - Check GitHub for PR merge status")
    print("   - Manually review any PRs that didn't auto-merge")
    print("   - Re-run this monitor to process newly-ready PRs")

def main():
    """Main function"""
    # Monitor for 10 runs with 60 second intervals (about 10 minutes total)
    monitor_prs_continuously(interval=60, max_runs=10)

if __name__ == "__main__":
    main()
