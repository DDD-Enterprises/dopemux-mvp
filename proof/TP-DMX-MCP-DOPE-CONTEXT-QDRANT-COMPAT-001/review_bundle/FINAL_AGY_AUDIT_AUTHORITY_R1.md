# Replacement AGY/Claude Final Audit Authority

AUDIT_ID=TP-DMX-MCP-DOPE-CONTEXT-QDRANT-COMPAT-001-FINAL-L3-R1
REPOSITORY=DDD-Enterprises/dopemux-mvp
MODE=READ_ONLY_INDEPENDENT_FINAL_L3_AUDIT

RUNNER=AGY
MODEL=claude-sonnet-4-6
UNSUPPORTED_EFFORT_OPTION=DO_NOT_PASS

REPO_WORKTREE=/Users/hue/code/dopemux-mvp/.worktrees/dope-context-qdrant-compat-001
REPO_MOUNT=REQUIRED_READ_ONLY
MOUNT_MECHANISM=USE_LIVE_DISCOVERED_AGY_REPOSITORY_MOUNT_OPTION
NETWORK=ONLY_WHAT_AGY_REQUIRES_FOR_MODEL_INVOCATION
REPO_MUTATION=FORBIDDEN
GITHUB_MUTATION=FORBIDDEN
PROOF_MUTATION=FORBIDDEN
CONTAINER_MUTATION=FORBIDDEN
PROVIDER_APPLICATION_CALLS=FORBIDDEN
MERGE=FORBIDDEN
ACTIVATION=FORBIDDEN

BASE_SHA=c7bc2fb479d7386825df73e028acdce723ee3388
FROZEN_SUBSTANTIVE_DIFF_SHA256=5dee0a6410608cdf310c1370941a778c8ccd3d5755ef1a438aef09b705ea7ad9
CANONICAL_PACKET_SHA256=bc24427a71a600b2bb57c6c6322caf2f06ba0531928f84af470b6f6be2dde662

PREVIOUS_AGY_RESULT=INVALID_AUDIT_ENVIRONMENT_NOT_SUBSTANTIVE
REASON=auditor sandbox lacked repository access and marked claims unverified

DISPATCH_CONDITION:
- first create immutable two-file content commit with no metadata/proof files
- run changed-contract validation against BASE..CONTENT_HEAD
- complete image build/import probe
- recreate only dope-context
- complete provider-free health/MCP/workspace readback
- verify foreign-project services untouched

BEFORE SUBSTANTIVE REVIEW, AUDITOR MUST PROVE:
1. repository is readable inside sandbox
2. repo identity matches DDD-Enterprises/dopemux-mvp
3. exact BASE_SHA is an ancestor of CONTENT_HEAD
4. CONTENT_HEAD and CONTENT_TREE are recorded
5. exact two-file substantive diff is readable
6. recomputed frozen diff hash matches FROZEN_SUBSTANTIVE_DIFF_SHA256
7. canonical supervisor packet bytes are available in the review bundle and hash to CANONICAL_PACKET_SHA256

REQUIRED REVIEW:
1. dense_search.py removes only the unused SearchRequest import
2. no pyproject.toml, uv.lock, compose.yml, or Dockerfile change
3. historical qdrant-client 1.19.0 negative control genuinely reproduced pre-fix SearchRequest ImportError
4. locked 1.17.1 focused suite passes
5. ephemeral 1.19.0 focused suite passes
6. complete locked dope-context suite passes
7. subprocess regression probe imports real Qdrant SDK
8. parent pytest sys.modules binding remains unchanged
9. image import probe passes
10. recreated dope-context becomes healthy
11. provider-free MCP initialize and tools/list pass
12. workspace mount/readback is correct
13. no provider application call occurred
14. dNh CRM Task Orchestrator and foreign-project services were untouched
15. no secret values appear in evidence
16. late packet materialization is disclosed truthfully and does not pretend the packet existed before implementation

IDENTITY RECORD:
- requested_model
- configured_model
- response_claimed_model
- proxy_reported_model
- provider_attested_model
Record UNKNOWN where evidence is absent. Never infer identity.

VERDICT:
PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR

PASS_WITH_RISKS is acceptable only when each risk is explicit and non-blocking.
FAIL or NEEDS_SUPERVISOR blocks proof closure.
