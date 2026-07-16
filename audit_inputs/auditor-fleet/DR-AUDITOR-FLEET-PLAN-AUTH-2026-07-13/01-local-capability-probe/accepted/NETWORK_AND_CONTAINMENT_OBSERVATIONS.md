# Network And Containment Observations

## Static Helper

`RAW_RECEIPTS/static/STATIC_TOOL_DISCOVERY.json` declares `network_used: false`,
`credential_files_read: false`, `model_invocation: false`, and
`mutation_performed: false`. These claims apply to the supplied static helper run.

## Containment Defect

Importing the aggregate `dopemux` CLI for `pr-steward --help` attempted a remote
LiteLLM cost-map fetch. DNS failed, no response data was obtained, and the command
returned zero. This is `OBSERVED` evidence that aggregate CLI import is unsuitable
for a no-network evidence path.

## Live Tools

All live invocations are `NOT_RUN`. Static help reveals partial controls on several
tools, but it does not prove a complete disablement set for inherited configuration,
MCP, hooks, plugins, skills, memory, subagents, shell, file writes, and web access.
The packet requires proof of every relevant control, so missing proof blocks live
execution.

## OpenRouter

Tracked policy classifies OpenRouter as a broker rather than a model family and
requires a pinned model plus explicit provider, price, and data policy. The tracked
RTE discovery path additionally requires explicit live-fetch and consent gates. No
OpenRouter request, key read, or API call occurred in this packet.
