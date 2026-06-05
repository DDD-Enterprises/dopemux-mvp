# Architecture: Read-Only MCP Evidence Facade

## 1. Overview
The read-only MCP evidence facade provides a secure, loopback-only projection of repository truth, execution state, and structured context to ChatGPT via the MCP protocol. It does not possess any write authority.

## 2. Component Boundaries
- **Project Registry**: Enforces eligibility of workspaces.
- **Resolver**: Maps requested projects to physical paths.
- **Response Envelope**: Standardizes metadata and structural layout for all responses.
- **Tools**: Exposed as MCP endpoints, strictly bounded to read operations.

## 3. Data Flow
- ChatGPT (Client) -> Secure Tunnel -> Facade (dopemux dcp) -> Internal Adapters -> (TO / dope-memory / ConPort)
- All paths pass through the multi-project registry.

## 4. Phase 1 Limitations
- No live writes.
- `dopecon-bridge` is denied.
- `search_all` is denied.
