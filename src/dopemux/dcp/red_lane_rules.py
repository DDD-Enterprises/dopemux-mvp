import re
from typing import List, Pattern
from dataclasses import dataclass

@dataclass
class Rule:
    rule_id: str
    category: str
    severity: str
    description: str
    patterns: List[Pattern]
    path_scope: str = ".*"
    recommended_action: str = ""

FORBIDDEN_PATHS = [
    re.compile(r"^src/dopemux" + r"_pr_merge_specialist/queue" + r"_drain\.py$"),
    re.compile(r"^dopemux" + r"_pr_merge_specialist/queue" + r"_drain\.py$"),
    re.compile(r"^scripts/batch" + r"_resolve_and_merge\.py$"),
    # DCP-RED-MERGE-SEAM-0001 narrow carve-out (ADR-224, TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
    # Phase A): exactly these two top-level workflow files are exempt from the path-level
    # block so their content can eventually be edited to wire embedded-audit schema
    # validation. Every other path under .github/workflows/ (including subdirectories and
    # any near-miss filename) remains hard-blocked. TEXT_RULES content scanning in
    # red_lane_scanner.py is untouched by this carve-out and still applies to these files.
    re.compile(
        r"^\.github/workflows/"
        r"(?!embedded-audit\.yml$)(?!pr-steward\.yml$)"
        r".*$"
    ),
    re.compile(r"^scripts/" + r"dopetask$"),
    re.compile(r"^scripts/" + r"taskx$"),
    re.compile(r"^services/task-orchestrator/.*$"),
    re.compile(r"^services/dopecon-bridge/.*$"),
    # DCP-RED-MERGE-SEAM-0001 narrow carve-out (ADR-226, TP-DOPECONTEXT-VECTOR-SPACE-0004
    # governance amendment 2026-09-03, extended by amendment A2 2026-09-04): the offline
    # benchmark harness directory services/dope-context/eval/ and exactly the five service
    # files named in packet 0004's Allowed Files are exempt from the path-level block.
    # A2 added src/index_profile.py and src/embeddings/model_registry.py, which are the
    # canonical writers the settled D1 decision actually needs; the two originally-named
    # service files neither set content_vec's model/endpoint nor need a query-side edit.
    # Every other path under services/dope-context/ (the rest of src/ and tests/,
    # Dockerfile, constraints, near-miss filenames, same-named files in other directories)
    # remains hard-blocked. TEXT_RULES content scanning in red_lane_scanner.py is untouched
    # by this carve-out and still applies to the exempted paths.
    re.compile(
        r"^services/dope-context/"
        r"(?!eval/)"
        r"(?!src/pipeline/indexing_pipeline\.py$)"
        r"(?!src/mcp/server\.py$)"
        r"(?!src/index_profile\.py$)"
        r"(?!src/embeddings/model_registry\.py$)"
        r"(?!tests/test_vector_space_invariants\.py$)"
        # A3 (2026-09-04): the landed D1 change invalidates four assertions in
        # this file, each of which pins the pre-D1 contract. They must be
        # rewritten, not deleted, so the file needs the same path-level
        # exemption. No other file under tests/ is exempted.
        r"(?!tests/test_vector_profiles_and_migration\.py$)"
        r".*$"
    ),
    # Companion to the carve-out above. The hook's primary path reading is lexical (no
    # `..` resolution); the realpath reading it also checks since the ADR-226 audit
    # (F-001) is defence-in-depth, so a directory-scoped exemption must still refuse any
    # traversal segment on its own or `services/dope-context/eval/../src/x.py` would
    # escape the block. Applies to the whole service subtree; an exact `..` segment is
    # the only thing it matches (`something..` or `..foo` are ordinary names).
    re.compile(r"^services/dope-context/(?:.*/)?\.\.(?:/|$)"),
    re.compile(r"^services/working-memory-assistant/.*$"),
    re.compile(r"^docker/mcp-servers-source/conport/.*$"),
    re.compile(r"^src/conport/.*$")
]

TEXT_RULES = [
    Rule(
        rule_id="MERGE_SEAM_001",
        category="MERGE_SEAM_VIOLATION",
        severity="BLOCKER",
        description="Forbidden merge-seam import or call",
        patterns=[
            re.compile(r"queue" + r"_drain"),
            re.compile(r"batch" + r"_resolve_and_merge"),
            re.compile(r"dopemux" + r"_pr_merge_specialist"),
            re.compile(r"gh pr " + r"merge"),
            re.compile(r"gh " + r"api"),
            re.compile(r"gh pr " + r"review"),
            re.compile(r"gh pr " + r"comment"),
            re.compile(r"gh pr " + r"edit")
        ],
        recommended_action="Remove merge-seam invocation. DCP Core must not orchestrate PR logic."
    ),
    Rule(
        rule_id="DOPETASK_001",
        category="DOPETASK_EXECUTION",
        severity="BLOCKER",
        description="Forbidden Dopetask execution path",
        patterns=[
            re.compile(r"dopetask " + r"tp"),
            re.compile(r"scripts/" + r"dopetask"),
            re.compile(r"scripts/" + r"taskx")
        ],
        recommended_action="Remove Dopetask invocation."
    ),
    Rule(
        rule_id="NETWORK_001",
        category="FORBIDDEN_CALL",
        severity="BLOCKER",
        description="Forbidden network library or sub" + "process call",
        patterns=[
            re.compile(r"sub" + r"process"),
            re.compile(r"requests" + r"\."),
            re.compile(r"httpx" + r"\."),
            re.compile(r"urllib"),
            re.compile(r"aiohttp")
        ],
        recommended_action="Remove network/sub" + "process calls from DCP Core."
    ),
    Rule(
        rule_id="EXTERNAL_WRITE_001",
        category="EXTERNAL_WRITE_STATUS",
        severity="BLOCKER",
        description="Forbidden external state mutation via Task-Orchestrator, memory, etc.",
        patterns=[
            re.compile(r"mem\.upsert"),
            re.compile(r"memory" + r"_store"),
            re.compile(r"/tools/memory" + r"_store"),
            re.compile(r"/tools/memory" + r"_correct"),
            re.compile(r"/api/" + r"decisions"),
            re.compile(r"/api/" + r"progress"),
            re.compile(r"/api/" + r"custom_data"),
            re.compile(r"/api/" + r"workflow"),
            re.compile(r"/api/" + r"pm"),
            re.compile(r"/route/" + r"pm")
        ],
        recommended_action="Remove external state mutations."
    ),
    Rule(
        rule_id="LIVE_WRITE_001",
        category="LIVE_WRITE_CREEP",
        severity="BLOCKER",
        description="Forbidden enablement of LIVE_WRITE_READY",
        patterns=[
            re.compile(r"LIVE_WRITE_READY\s*=\s*True"),
            re.compile(r"LIVE_WRITE_READY:\s*true"),
            re.compile(r"\"live_write_ready\":\s*true"),
            re.compile(r"\"live_write_status\":\s*\"ENABLED\""),
            re.compile(r"\"live_write_status\":\s*\"ACTIVE\"")
        ],
        recommended_action="Do not enable LIVE_WRITE_READY."
    )
]

def is_safe_false_positive(file_path: str) -> bool:
    """Check if the file is a scanner declaration that should be ignored. Test fixtures are NOT exempted and will be blocked."""
    if file_path.endswith("dcp/red_lane_rules.py") or file_path.endswith("dcp/red_lane_scanner.py"):
        return True
    return False

def redact_secret_like(text: str) -> str:
    """Redacts values that look like secrets (hex tokens, typical credentials)."""
    # Just a placeholder basic redaction logic. Real logic would match keys/tokens.
    # We redact tokens resembling hex/auth keys if found in match context.
    redacted = re.sub(r"([a-zA-Z0-9_-]{20,})", "***REDACTED***", text)
    return redacted
