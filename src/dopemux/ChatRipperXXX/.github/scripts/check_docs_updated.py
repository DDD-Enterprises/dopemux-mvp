
import os
import subprocess
import sys

BASE_SHA = os.environ.get("GITHUB_BASE_SHA", "")
HEAD_SHA = os.environ.get("GITHUB_HEAD_SHA", "")

if not BASE_SHA or not HEAD_SHA:
    # Try to infer in PR context
    BASE_SHA = os.environ.get("GITHUB_EVENT_PULL_REQUEST_BASE_SHA", "")
    HEAD_SHA = os.environ.get("GITHUB_SHA", "")

if not BASE_SHA or not HEAD_SHA:
    print("Skipping docs check: missing SHAs")
    sys.exit(0)

def changed_files(base, head):
    out = subprocess.check_output(["git", "diff", "--name-only", f"{base}...{head}"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]

files = changed_files(BASE_SHA, HEAD_SHA)
code_changed = any(
    f.startswith(("src/", "cli/",)) or f.endswith(".py") for f in files
)
docs_changed = any(
    f.startswith(("docs/",)) or f in ("README.md", "CLAUDE.md", "mkdocs.yml")
    for f in files
)

if code_changed and not docs_changed:
    print("❌ Code changed but docs were not updated. Please update docs/ or README/CLAUDE.md.")
    sys.exit(1)

print("✅ Docs check passed.")
sys.exit(0)
