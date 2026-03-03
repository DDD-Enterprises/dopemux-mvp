# Semantic Search Privacy Guidelines

## Source Classification

- **Sensitive:** Internal code, proprietary docs, customer data
- **Non-sensitive:** Public documentation, open source references

## Security Controls

### Self-hosted Infrastructure
- Keep sensitive indexing to self-hosted Milvus
- Disable external proxies for sensitive sources
- Encrypt data at rest and in transit

### Access Control
- Log anonymized telemetry only
- Rotate API keys regularly
- Implement query-time ACL enforcement

### Data Processing
- **PII Redaction:** Remove personal information in loaders
- **Opt-out Support:** Honor robots.txt-like exclusion tags
- **Retention Policy:** Define data lifecycle and deletion procedures

## PluggedIn MCP Proxy Guidelines

- **Environment Gating:** Require explicit env flag to enable
- **Non-sensitive Only:** Never use for proprietary or customer data
- **Audit Logging:** Track all external service interactions
- **Fallback Strategy:** Graceful degradation when external services unavailable

## Compliance Considerations

- Document data flow for privacy impact assessments
- Implement data subject access request handling
- Maintain audit trails for compliance reporting