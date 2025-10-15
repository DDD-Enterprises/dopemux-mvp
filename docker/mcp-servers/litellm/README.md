# LiteLLM Proxy Server for Dopemux

## Overview

LiteLLM provides a unified proxy interface for multiple LLM providers with intelligent routing, fallbacks, and load balancing. This service is part of the Dopemux critical path infrastructure.

## Features

- **Unified API**: Single endpoint for OpenAI, xAI (Grok), OpenRouter, and other providers
- **Intelligent Fallbacks**: Automatic failover to backup models on errors
- **Latency-Based Routing**: Routes requests to fastest available model
- **Cost Optimization**: Balance cost vs performance with routing strategies
- **Rate Limit Handling**: Automatic retry with exponential backoff

## Configuration

The service is configured via `/app/config.yaml` (mounted from project root `litellm.config.yaml`).

### Configured Models

1. **openai-gpt-5** - Primary reasoning model
2. **openai-gpt-5-mini** - Fast inference model
3. **xai-grok-4** - Alternative reasoning model
4. **xai-grok-4-heavy** - Heavy computation model

### Fallback Chain

```
openai-gpt-5 → openai-gpt-5-mini → xai-grok-4
openai-gpt-5-mini → xai-grok-4
xai-grok-4 → xai-grok-4-heavy → openai-gpt-5-mini
xai-grok-4-heavy → xai-grok-4 → openai-gpt-5
```

## Environment Variables

Required:
- `OPENAI_API_KEY` - OpenAI API key
- `XAI_API_KEY` - xAI (Grok) API key

Optional:
- `OPENROUTER_API_KEY` - OpenRouter API key
- `GEMINI_API_KEY` - Google Gemini API key
- `LITELLM_LOG` - Log level (default: INFO)

## Usage

### Via Docker Compose (Recommended)

```bash
cd docker/mcp-servers
./start-all-mcp-servers.sh
```

### Direct Access

```bash
# Health check
curl http://localhost:4000/health

# List models
curl http://localhost:4000/models

# Chat completion
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai-gpt-5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### From Claude Code / MCP

```python
# LiteLLM automatically handles routing and fallbacks
response = litellm.completion(
    model="openai-gpt-5",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Troubleshooting

### Server Won't Start

1. **Check YAML syntax**: `python -c "import yaml; yaml.safe_load(open('litellm.config.yaml'))"`
2. **Verify API keys**: Ensure environment variables are set
3. **Check logs**: `docker logs mcp-litellm`

### Database Errors

If you see "prisma package not found":
- Install: `pip install prisma`
- Or disable DB: Unset `DATABASE_URL` in config

### Port Conflicts

If port 4000 is in use:
1. Edit `docker-compose.yml` to change port mapping
2. Update health check URLs in `start-all-mcp-servers.sh`

## Architecture Integration

- **Role**: Critical Path Infrastructure
- **Priority**: High
- **Dependencies**: None (standalone proxy)
- **Dependents**: All MCP servers using LLM calls
- **Port**: 4000
- **Health**: `/health` endpoint

## Performance

- **Startup Time**: ~30 seconds
- **Request Latency**: +5-10ms proxy overhead
- **Throughput**: Limited by upstream providers
- **Failover Time**: <2 seconds with retry policy

## Security

- API keys stored in environment variables (not in config)
- Master key for admin operations (rotate regularly)
- SQLite database for request logging (optional)
- No PII stored in logs by default

## Monitoring

- Health endpoint: `http://localhost:4000/health`
- Metrics endpoint: `http://localhost:4000/metrics`
- Log location: Container stdout (`docker logs mcp-litellm`)

## Development

To modify configuration:

1. Edit `litellm.config.yaml` in project root
2. Restart service: `docker-compose restart litellm`
3. Verify: `curl http://localhost:4000/health`

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Dopemux Architecture](../../docs/02-architecture/)
- [MCP Integration Patterns](../../docs/90-adr/ADR-012-mcp-integration-patterns.md)
