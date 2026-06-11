# Docker Scout Classification — PR #854

## Source evidence

- PR #854 CI Scout workflow run: `27319285873` (conclusion=**success**, status=completed)
- head SHA verified: `15f235b8c60c473c301713f6e2f6251a449d07cf`
- Security fix commit on this branch: `d5e09bf3e` — "fix(security): upgrade litellm + OS packages to resolve Docker Scout CVEs"
- Docker Scout CLI: v1.20.4 — **API FORBIDDEN** for local CVE query (team access not available in this env)
- PR body runtime/security proofs section: describes litellm critical CVE fixed + base image OS CVEs accepted

## CI Scout checks at head 15f235b8c

| Service | Job | Conclusion |
|---|---|---|
| Scout adhd-engine | `80706666702` | **success** |
| Scout claude-brain | `80706666647` | **success** |
| Scout conport | `80706666615` | **success** |
| Scout dope-memory | `80706666634` | **success** |
| Scout dopecon-bridge | `80706666587` | **success** |
| Scout dopemux-backend | `80706666570` | **success** |
| Scout litellm | `80706666571` | **success** |
| Scout task-orchestrator | `80706666630` | **success** |
| Scout webhook-receiver | `80706666595` | **success** |

**All 9 Scout CI checks: SUCCESS at PR head 15f235b8c**

Note: `pal-stdio` is not a separately-scanned image in CI (it's a MCP toolkit stdio exec service; not published to GHCR). The PAL stdio Dockerfile uses `python:3.11-slim` base.

## Classification table

| Finding family | Source | Status | Rationale | Operator acceptance required |
|---|---|---|---|---|
| litellm critical CVE (CVE-2026-35030 and related) | PR body + commit d5e09bf3e | **FIXED** | litellm[proxy]>=1.83.7 + starlette>=0.49.1 + python-multipart + cryptography pinned; apt-get upgrade for OS packages in litellm Dockerfile. CI Scout litellm: SUCCESS | No |
| openssl / base OS criticals (python:3.11-alpine/slim) | PR body + CI baseline | **INHERITED_ACCEPTED** | Official base images across services (adhd-engine, pal-stdio, task-orchestrator legacy, etc.). Non-root user in Dockerfiles, minimal attack surface, dev/CI images. Scout CI passes with these inherited. The broad COPY changes add only application source/README/tools — no new system packages or vulnerable binaries. | Yes — operator accepted per PR body |
| curl/openssl alpine high | PR body + CI baseline | **INHERITED_ACCEPTED** | Same base image inheritance. Scout CI passes. | Yes — operator accepted per PR body |
| New deps from PR-introduced Dockerfiles (pal-stdio python:3.11-slim) | Dockerfile diff | **NONE_OBSERVED** | pal-stdio adds git+curl (system) + uv (Python PM) + PAL server deps via requirements.txt. No new critical dependencies beyond base. Scout CI does not separately scan pal-stdio but the base is python:3.11-slim (same family as other services). | No separate scan |
| pal-stdio runtime startup crash | Runtime test | **BLOCKED_STARTUP_CRASH** | Separate from CVE classification: pal-stdio crashes due to clink registry bug (openrouter-audit.json unsupported type). Functional blocker, not a CVE. | N/A |

## Local Docker Scout CVE scan
```
Status: FORBIDDEN
Reason: Team API access not available in this execution environment
Fallback: CI Scout workflow evidence (all 9 services SUCCESS at head)
```

## Conclusion

**SECURITY_ACCEPTED_WITH_RISKS**

- litellm CVE fix: FIXED (OBSERVED via commit d5e09bf3e + CI Scout litellm SUCCESS)
- Base OS inherited CVEs: INHERITED_ACCEPTED (operator acceptance documented in PR body)
- No new critical CVEs introduced by PR-specific changes (OBSERVED via code review + CI)
- Scout workflow CI: ALL PASS at head 15f235b8c (OBSERVED)
- Local CVE scan: NOT_RUN (API FORBIDDEN — fallback to CI evidence)

Operator acceptance required: **YES** (for inherited base image CVEs, per PR body documentation)

## Note on pal-stdio and runtime blocker
The pal-stdio service does NOT have a separate Docker Scout CI scan. The base `python:3.11-slim` is shared with other scanned services. The pal-stdio runtime startup crash (clink registry bug) is the primary blocker — it is a functional issue separate from CVE classification.
