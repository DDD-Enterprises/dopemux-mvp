import json
import subprocess
import pathlib

def main():
    repo_root = pathlib.Path(".")
    
    # 1. Main SHA
    main_sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    (repo_root / "FINAL_MAIN_SHA.txt").write_text(main_sha + "\n")
    print(f"FINAL_MAIN_SHA: {main_sha}")
    
    # 2. Fetch PR lists
    def gh_json(cmd):
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    
    raw_open_summary = gh_json(["gh", "pr", "list", "--state", "open", "--limit", "300", "--json", "number,title,headRefName,url,isDraft,mergeable,state,createdAt,updatedAt,reviewDecision"])
    raw_closed_prs = gh_json(["gh", "pr", "list", "--state", "closed", "--limit", "300", "--json", "number,title,headRefName,url,state,closedAt,mergedAt"])
    
    merged_prs = [pr for pr in raw_closed_prs if pr.get("mergedAt")]
    closed_prs = [pr for pr in raw_closed_prs if not pr.get("mergedAt")]
    
    (repo_root / "FINAL_MERGED_PRS.json").write_text(json.dumps(merged_prs, indent=2) + "\n")
    (repo_root / "FINAL_CLOSED_PRS.json").write_text(json.dumps(closed_prs, indent=2) + "\n")
    
    open_inventory = []
    blockers = []
    
    for item in raw_open_summary:
        pr_num = item["number"]
        # View full PR detail
        pr = gh_json(["gh", "pr", "view", str(pr_num), "--json", "number,title,headRefName,url,isDraft,mergeable,state,createdAt,updatedAt,reviewDecision,commits,statusCheckRollup"])
        
        title = pr["title"]
        branch = pr["headRefName"]
        url = pr["url"]
        mergeable = pr.get("mergeable", "UNKNOWN")
        review = pr.get("reviewDecision", "UNKNOWN")
        
        # Determine check status
        rollup = pr.get("statusCheckRollup") or []
        check_conclusions = [item.get("conclusion") for item in rollup if item.get("conclusion")]
        check_states = [item.get("state") for item in rollup if item.get("state")]
        
        has_failed_check = "FAILURE" in check_conclusions or "FAILURE" in check_states
        
        # Classification rules
        reasons = []
        classification = "OPEN_BLOCKED"
        
        if mergeable == "CONFLICTING":
            reasons.append("Merge conflict with main")
        if has_failed_check:
            reasons.append("Failed status checks")
        if review in ("UNKNOWN", None, ""):
            reasons.append("Unknown or unassigned reviewer decision")
        elif review == "CHANGES_REQUESTED":
            reasons.append("Changes requested by reviewer")
        elif review == "REVIEW_REQUIRED":
            reasons.append("Pending required review")
            
        # Check proof directory existence and freshness
        proof_path = repo_root / f"proof/pr-{pr_num}/PROOF.json"
        proof_path_alt = repo_root / f"proof/pr_merge/embedded-audit/pr-{pr_num}/PROOF.json"
        
        if not proof_path.exists() and not proof_path_alt.exists():
            reasons.append("Missing embedded audit proof bundle")
        else:
            p_file = proof_path if proof_path.exists() else proof_path_alt
            try:
                proof_data = json.loads(p_file.read_text())
                last_commit = pr.get("commits", [{}])[-1].get("oid", "")
                if proof_data.get("commit_sha") != last_commit and proof_data.get("head_sha") != last_commit:
                    reasons.append("Stale proof bundle head SHA mismatch")
            except Exception:
                reasons.append("Malformed proof bundle")

        if not reasons:
            classification = "OPEN_READY"
        else:
            blockers.append({
                "pr_number": pr_num,
                "title": title,
                "branch": branch,
                "url": url,
                "reasons": reasons
            })
            
        open_inventory.append({
            "pr_number": pr_num,
            "title": title,
            "branch": branch,
            "url": url,
            "mergeable": mergeable,
            "review_decision": review,
            "classification": classification,
            "reasons": reasons
        })
        
    (repo_root / "FINAL_OPEN_PR_INVENTORY.json").write_text(json.dumps(open_inventory, indent=2) + "\n")
    (repo_root / "FINAL_BLOCKERS.json").write_text(json.dumps(blockers, indent=2) + "\n")
    
    # Write summary MD
    summary_md = f"""# Final Merge Readiness Summary

- **Final Main SHA**: `{main_sha}`
- **Open PR Count**: {len(open_inventory)}
- **Merged PR Count**: {len(merged_prs)}
- **Closed (Custody/Superseded) PR Count**: {len(closed_prs)}

## Drain Status

Every remaining open PR has been audited and classified according to execution policy.

### Inventory & Classifications

"""
    for pr in open_inventory:
        summary_md += f"### PR #{pr['pr_number']}: {pr['title']}\n"
        summary_md += f"- **Branch**: `{pr['branch']}`\n"
        summary_md += f"- **URL**: {pr['url']}\n"
        summary_md += f"- **Classification**: `{pr['classification']}`\n"
        if pr["reasons"]:
            summary_md += f"- **Blockers**: {', '.join(pr['reasons'])}\n"
        summary_md += "\n"
        
    (repo_root / "FINAL_MERGE_READINESS_SUMMARY.md").write_text(summary_md)
    print("All final drain artifacts generated successfully.")

if __name__ == "__main__":
    main()
