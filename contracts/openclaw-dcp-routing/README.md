# OpenClaw DCP Routing Contracts

Status: `PROPOSED`.

These artifacts are contracts only. Runtime routing is not enabled by this directory, and no provider API integration, OpenClaw integration, OpenRouter integration, benchmark harness execution, or production route enablement is implemented here.

Local benchmark certification is still required before any route can be enabled for production, high-trust, schema-authority, private-repo, security, or release use.

Authority posture:

- OpenClaw is worker/runtime substrate, not policy authority.
- OpenRouter is routing fabric, not a trust oracle.
- Direct APIs are preferred for automation, structured outputs, reproducible logs, and high-trust lanes.
- Consumer app outputs require proof capture if used in a DCP workflow.

## Normalization Notes

- The mission names these as Turn 4 artifacts; the supplied source text says the artifacts encode the Turn 3 routing policy. This contradiction is preserved here instead of resolved by inference.
- JSON and JSON Schema files contain only the balanced JSON object bodies from the supplied source. Adjacent prose `validation_notes` were excluded from JSON files so the artifacts parse mechanically.
- YAML artifacts retain source `validation_notes` as YAML keys where present.
- Markdown artifacts retain source prose, including their validation notes.
- This repository change does not select runtime locations for route certification storage, PR Steward runtime, or a DCP wrapper runtime; those remain `UNKNOWN` in the supplied checklist.
