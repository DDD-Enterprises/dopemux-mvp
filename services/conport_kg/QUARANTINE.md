# Quarantine Notice

`services/conport_kg/` is a non-canonical Apache AGE graph projection.

Per the Memory Trinity ADR, this directory is not the runtime-integrated
ConPort MCP server. The canonical ConPort MCP server lives at:

`docker/mcp-servers-source/conport/`

Do not import, deploy, or route runtime traffic to this code without explicit
operator approval and a new task packet that re-establishes authority,
integration scope, and validation evidence.
