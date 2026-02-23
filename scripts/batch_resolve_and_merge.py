import subprocess
import json
import os

# Read PAT from environment variable
PAT = os.environ.get("GH_TOKEN")
if not PAT:
    raise ValueError("GH_TOKEN environment variable not set. Please set it in your shell config.")

def resolve_threads(pr_number):
    print(f"--- Resolving threads for PR #{pr_number} ---")
    query = f"""
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
    """
    
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": PAT}
    )
    
    if result.returncode != 0:
        print(f"Error querying threads: {result.stderr}")
        return False
        
    data = json.loads(result.stdout)
    threads = data.get("data", {}).get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])
    
    for thread in threads:
        if not thread.get("isResolved"):
            thread_id = thread["id"]
            print(f"Resolving thread {thread_id}")
            resolve_result = subprocess.run(
                ["gh", "api", "graphql", "-f", f"query=mutation {{resolveReviewThread(input: {{threadId: '{thread_id}'}}) {{clientMutationId}}}}"],
                capture_output=True,
                text=True,
                env={**os.environ, "GH_TOKEN": PAT}
            )
            if resolve_result.returncode != 0:
                print(f"Failed to resolve thread {thread_id}: {resolve_result.stderr}")
                return False
    
    return True

def merge_pr(pr_number):
    print(f"--- Merging PR #{pr_number} ---")
    result = subprocess.run(
        ["gh", "pr", "merge", str(pr_number), "--squash", "--delete-branch"],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": PAT}
    )
    
    if result.returncode != 0:
        print(f"Error merging PR: {result.stderr}")
        return False
    
    print(f"Successfully merged PR #{pr_number}")
    return True

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python batch_resolve_and_merge.py <PR_NUMBER>")
        sys.exit(1)
    
    pr_number = int(sys.argv[1])
    
    if not resolve_threads(pr_number):
        print("Failed to resolve threads")
        sys.exit(1)
    
    if not merge_pr(pr_number):
        print("Failed to merge PR")
        sys.exit(1)
    
    print(f"✅ Successfully resolved threads and merged PR #{pr_number}")

if __name__ == "__main__":
    main()