import re
import sys
import os

# Add the src dir to path so we can import the module
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

try:
    from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

def check_scanner(path):
    # Scanner uses pattern.match()
    return any(p.match(path) for p in FORBIDDEN_PATHS)

def check_guard(path):
    # Guard uses pattern.search()
    return any(p.search(path) for p in FORBIDDEN_PATHS)

def test_case(name, paths, expected_block):
    print(f"Testing {name} (Expect Block: {expected_block})")
    failures = []
    for p in paths:
        scanner_blocked = check_scanner(p)
        guard_blocked = check_guard(p)
        if scanner_blocked != expected_block or guard_blocked != expected_block:
            failures.append(f"  Path '{repr(p)}': scanner_blocked={scanner_blocked}, guard_blocked={guard_blocked}")

    if failures:
        print("  FAIL:")
        for f in failures: print(f)
        return False
    else:
        print("  PASS")
        return True

all_passed = True

# 1-3. Newlines, CR, tabs
all_passed &= test_case("Newline/Control in path", [
    "services/dope-context/src/\nsecret.py",
    "services/dope-context/src/index_profile.py\n",
    ".github/workflows/embedded-audit.yml\n",
    "services/task-orchestrator/x/\ny",
    "services/dope-context/src/index_profile.py\t",
    "services/dope-context/src/index_profile.py\r",
    "services/dope-context/eval/\n/../../src/secret.py"
], True)

# 4. Exact-exemption spoof
all_passed &= test_case("Exact-exemption spoof", [
    "services/dope-context/src/index_profile.py\n",
    "services/dope-context/src/index_profile.py\r",
    ".github/workflows/embedded-audit.yml\n",
    ".github/workflows/pr-steward.yml\t",
], True)

# 5. Path traversal with newline
all_passed &= test_case("Traversal + newline", [
    "services/dope-context/eval/\n/../../src/secret.py",
    "services/dope-context/eval/..\n/src/secret.py",
], True)

# 8. Near miss with control chars
all_passed &= test_case("Near-miss with control chars", [
    "services/dope-context/src/index_profile.py.bak\n",
    ".github/workflows/embedded-audit.yml.orig\r",
], True)

# 9. Intended exemptions
all_passed &= test_case("Intended exemptions", [
    ".github/workflows/embedded-audit.yml",
    ".github/workflows/pr-steward.yml",
    "services/dope-context/eval/run_eval.py",
    "services/dope-context/eval/subdir/test.py",
    "services/dope-context/src/pipeline/indexing_pipeline.py",
    "services/dope-context/src/mcp/server.py",
    "services/dope-context/src/index_profile.py",
    "services/dope-context/src/embeddings/model_registry.py",
    "services/dope-context/tests/test_vector_space_invariants.py",
    "services/dope-context/tests/test_vector_profiles_and_migration.py",
    "services/dope-context/src/embeddings/voyage_embedder.py",
    "services/dope-context/src/search/dense_search.py",
], False)

# 10. Legitimate paths (no control characters, normal)
all_passed &= test_case("Ordinary paths", [
    "src/some_normal_file.py",
    "services/some_other_service/main.py",
], False)

if not all_passed:
    sys.exit(1)
print("ALL TESTS PASSED")
