# TP-DCP-MCP-RO-0014 Command Log

Branch: `codex/dcp-mcp-ro-0014-loopback-ingress`
Base: `origin/main` @ `4079da8387bae0cf8b2971de547f092a3f6b8408` (includes merged TP-0013 / PR #1059)

| Command | Result |
| --- | --- |
| Package SHA-256 c0cb9d34…2447 | PASS (advisory) |
| 0013 dependency on main | PASS |
| 0014 collision search | PASS (none) |
| Focused ingress/loopback tests | PASS (11) |
| Full facade suite | PASS; 1 live skip |
| compileall | PASS |
| packet jsonschema | PASS |
| pre-commit allowlist | PASS |
| agy advisory | PASS_WITH_RISKS |
| Trusted embedded audit / PR Steward | NOT_RUN / not claimed |

No tunnel, public bind default, provider credential, or backend mutation run.
