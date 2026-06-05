# Security Model

## 1. Secure MCP Tunnel
The facade communicates with ChatGPT exclusively via the secure loopback MCP tunnel. No external ingress is allowed.

## 2. Prompt-Injection Controls
All parsed arguments from the client are treated as untrusted and must pass regex/typing validation before being passed to internal adapters.

## 3. Redaction
Sensitive fields (secrets, tokens, PII) are redacted by the facade before inclusion in the response envelope.

## 4. Side-Effect Controls
No mutable operations are permitted. The facade operates entirely in a read-only projection context.
