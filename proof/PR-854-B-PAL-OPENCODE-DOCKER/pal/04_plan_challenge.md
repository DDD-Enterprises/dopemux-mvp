# PAL-4 — Plan Challenge

## stage
PAL-4 Challenge

## tool_or_mode
UNAVAILABLE_MANUAL_STAGE — same-tool challenge (PAL MCP unavailable; Claude Sonnet self-challenging)
NOTE: This is NOT an independent challenge. Same model. Confidence is accordingly lower.

## model
claude-sonnet-4-6

---

## Attacks on the Runtime Test Plan

### Attack 1: Could tests print secrets?

**Test 3/4 (docker run):** No env vars are passed to `docker run`. The container receives no API keys. Server.py will likely fail to start or start in a degraded mode, but won't print secrets it doesn't have.
**Verdict:** LOW risk. Shell environment secrets are NOT passed unless `-e` flags used. SAFE.

**Test 5 (compose up):** The compose.yml passes `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` from the shell environment. If these are set in the dev environment, they WILL be in the container's environment. However:
- We're capturing `docker compose logs` (container stdout/stderr), not `docker inspect env`
- If server.py logs API keys on startup, they'd appear in the log
- Mitigation: We will review logs before saving; if keys appear, we'll mask them and note the masking
**Verdict:** MEDIUM risk in theory. Addressed by log review. Will not use `docker inspect` for env.

### Attack 2: Could compose restart-loop test mutate service state dangerously?

We bring `pal-stdio` up detached, wait 15 seconds, then stop + rm. If other services depend on `pal-stdio`:
- Looking at compose.yml: no `depends_on: pal-stdio` observed in other services
- The service has no data volumes (no persistence)
- Cleanup: explicit `stop + rm -f`
**Verdict:** LOW risk. No state mutation. Cleanup is explicit.

### Attack 3: Could verify-pal prove only config, not real runtime?

YES — this is known and stated in the evidence inventory. verify-pal.sh checks:
- File existence (structural)
- Optionally: `opencode debug config` output (structural config resolution, not actual tool invocation)

It does NOT: start PAL, call any tool, verify API key validity, or test actual tool routing.

**Verdict:** ACCEPTED RISK. Must be documented as "structural wiring verified, not runtime behavior." The runtime tests (build + stdin) provide the runtime evidence. verify-pal.sh provides the OpenCode integration evidence.

### Attack 4: Could Docker Scout classification be hand-wavy?

The plan captures PR comments + workflow run state via `gh run list` and `gh pr view`. However:
- We may not have Docker Scout CLI installed locally
- We're relying on CI workflow evidence (Scout * jobs all PASS at current head)
- If Scout jobs are PASS but a specific image wasn't scanned at current head, the classification is stale

**Mitigation:** We will note per-image Scout job status from CI at exactly `15f235b8c`. If `docker scout cves` CLI is unavailable, we document that explicitly and rely on CI evidence with HEAD SHA verification.
**Verdict:** MEDIUM risk. Must be explicit about what evidence is CI-derived vs locally-verified.

### Attack 5: Could proof files claim readiness without latest-head PR Steward?

The plan includes explicit PR Steward capture (Phase 7) at the exact PR #854 head `15f235b8c`. We will NOT populate `merge_readiness` with anything other than `BLOCKED_NOT_REQUESTED`.
**Verdict:** ADDRESSED. Hard invariant enforced throughout.

### Attack 6: Could this packet accidentally edit forbidden files?

The packet scope is limited to `proof/PR-854-B-PAL-OPENCODE-DOCKER/**` and the three PROOF.json family files. All runtime tests are read-only or write to log files in the proof directory.
No `Edit` calls will be made to source/config/docker/scripts files.
**Verdict:** LOW risk. Enforced by diff allowlist check before commit.

### Attack 7: Could the same-tool challenge miss something an independent reviewer would catch?

YES — this is the acknowledged limitation of PAL MCP being unavailable. Mitigations:
- Explicit labeling of all PAL stages as `UNAVAILABLE_MANUAL_STAGE`
- Final handoff explicitly routes to GPT-5.5 Pro for independent supervisor review
- merge_readiness stays BLOCKED_NOT_REQUESTED regardless of our own verdict
**Verdict:** KNOWN LIMITATION — documented, escalated to supervisor.

---

## Overall Challenge Verdict

**PASS_WITH_RISKS**

Risks accepted with mitigations:
1. Log review for secret exposure before save (compose test)
2. verify-pal is structural only — documented limitation
3. Docker Scout classification may be CI-derived only — will be explicit about source
4. Same-tool challenge — supervisor escalation mandatory

No FAIL conditions found in the test plan.
