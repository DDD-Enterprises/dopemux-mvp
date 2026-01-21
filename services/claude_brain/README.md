# Claude Brain Service

**Advanced prompt optimization and brain integration with ADHD accommodations.**

This service implements Phase 1 of the Claude Code Brain Integration, providing meta-prompting, chain-of-thought reasoning, few-shot learning, and dynamic ADHD formatting with self-improving loops.

## 🚀 Features

### Core Capabilities
- **Meta-Prompting**: Generate/critique/evolve cycles for self-improvement
- **Chain-of-Thought Reasoning**: Enhanced logical reasoning capabilities
- **Few-Shot Learning**: Dynamic example selection and application
- **ADHD Dynamic Formatting**: Cognitive load-aware response formatting
- **Self-Improving Loops**: Continuous optimization based on performance

### Advanced Components
- **ClaudeBrainManager**: LiteLLM routing with intelligent provider selection
- **PromptOptimizer**: Meta-prompting with critique and evolution
- **MetaPromptGenerator**: Self-improving prompt evolution
- **CritiqueAnalyzer**: Multi-dimensional quality assessment
- **FailureHandler**: Circuit breaker pattern with graceful degradation
- **CacheManager**: Redis caching with ADHD optimizations

### ADHD Optimizations
- **Progressive Disclosure**: Essential info first, details on demand
- **Visual Indicators**: ✅ ❌ ⚠️ 💡 🎯 for better scanning
- **Cognitive Load Management**: Response complexity based on user state
- **Gentle Error Messages**: Encouraging language for debugging

## 🏗️ Architecture

```
Claude Brain Service
├── brain_manager.py      # Core orchestration & routing
├── prompt_optimizer.py   # Meta-prompting engine
├── meta_prompt_generator.py  # Self-improvement loops
├── critique_analyzer.py  # Quality assessment
├── failure_handler.py    # Circuit breaker & recovery
├── cache_manager.py      # Redis caching & formatting
├── main.py              # FastAPI application
├── config.py            # Configuration management
└── requirements.txt     # Dependencies
```

## 📡 API Endpoints

### Core Operations
- `POST /api/v1/optimize-prompt` - Optimize prompts using meta-prompting
- `POST /api/v1/generate-meta-prompt` - Generate evolved meta-prompts
- `POST /api/v1/analyze-critique` - Analyze prompt quality
- `POST /api/v1/brain-request` - General brain operations

### Management
- `GET /health` - Comprehensive health check
- `GET /api/v1/status` - Service status and metrics
- `POST /api/v1/reset-cache` - Clear cache (admin)

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_URL="redis://localhost:6379"
export ANTHROPIC_API_KEY="your_key"
export OPENAI_API_KEY="your_key"

# Run the service
python main.py
```

### Docker Deployment
```bash
# Build the image
docker build -t claude-brain .

# Run with environment variables
docker run -p 8080:8080 \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  -e ANTHROPIC_API_KEY="your_key" \
  claude-brain
```

## ⚙️ Configuration

### Environment Variables
```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8080
DEBUG=false

# AI Providers (at least one required)
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
GROQ_API_KEY=your_key

# Integrated Services
ADHD_ENGINE_URL=http://localhost:8095
CONPORT_URL=http://localhost:5455
SERENA_URL=http://localhost:8003

# Redis Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=3600
CACHE_MAX_MEMORY_MB=100

# Cost Optimization
COST_OPTIMIZATION_ENABLED=true
DAILY_BUDGET_LIMIT=10.0
MONTHLY_BUDGET_LIMIT=100.0
```

### Service Integration
The service integrates with:
- **ADHD Engine** (port 8095): Real-time cognitive load and attention state
- **ConPort** (port 5455): Decision logging and pattern tracking
- **Serena** (port 8003): Code intelligence and complexity scoring
- **Redis** (port 6379): High-performance caching

## 📊 Usage Examples

### Prompt Optimization
```python
import requests

response = requests.post("http://localhost:8080/api/v1/optimize-prompt", json={
    "prompt": "Write code for a login form",
    "optimization_level": "intermediate",
    "user_context": {"cognitive_load": 0.6, "attention_state": "focused"}
})

result = response.json()
print(result["optimized_prompt"])
```

### Meta-Prompt Generation
```python
response = requests.post("http://localhost:8080/api/v1/generate-meta-prompt", json={
    "optimization_focus": "adhd_friendly",
    "performance_history": []  # Historical performance data
})

meta_prompt = response.json()["meta_prompt"]
```

### Quality Analysis
```python
response = requests.post("http://localhost:8080/api/v1/analyze-critique", json={
    "prompt": "Debug this error"
})

analysis = response.json()["analysis"]
print(f"Quality: {analysis['overall_quality']:.1f}")
print("Issues:", analysis["issues"])
```

## 🧠 ADHD Optimizations

### Progressive Disclosure
- Essential information shown first
- Details revealed on demand
- Cognitive load-appropriate complexity

### Visual Indicators
- ✅ Success/completion
- ❌ Errors/problems
- ⚠️ Warnings/attention needed
- 💡 Tips/suggestions
- 🎯 Key points/objectives

### Cognitive Load Management
- Response length adapts to user state
- Step-by-step guidance for complex tasks
- Encouraging language and gentle error messages

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Type checking
mypy .

# Linting
flake8 .
```

### Adding New Features
1. Add new components in separate modules
2. Update main.py with new API endpoints
3. Add configuration in config.py
4. Update requirements.txt if needed
5. Add tests for new functionality

## 📈 Monitoring & Health

### Health Checks
The service provides comprehensive health monitoring:
- Component status (brain manager, optimizer, cache)
- Service integrations (ADHD Engine, ConPort, Serena)
- Circuit breaker status
- Cache performance metrics

### Metrics Available
- Requests processed and success rates
- Cache hit rates and performance
- Cost tracking and optimization
- Failure patterns and recovery

## 🤝 Integration

### With Dopemux Services
```python
# ADHD Engine integration
adhd_context = await query_adhd_engine(user_id, session_id)
brain_manager.update_adhd_context(adhd_context["cognitive_load"], adhd_context["attention_state"])

# ConPort decision logging
await log_decision("prompt_optimization", "anthropic", cost, success)

# Serena complexity scoring
complexity = await get_code_complexity(file_path, function_name)
```

### With External Systems
```python
# Custom integrations
class CustomIntegration:
    async def enhance_prompt(self, prompt: str, context: dict) -> str:
        # Custom enhancement logic
        return enhanced_prompt
```

## 🛡️ Security & Reliability

### Circuit Breaker Protection
- Automatic failure detection
- Graceful degradation
- Recovery strategies

### Cost Management
- Budget limits and monitoring
- Provider optimization
- Usage tracking

### Error Handling
- Comprehensive error classification
- ADHD-friendly error messages
- Recovery strategies

## 📚 Documentation

### API Documentation
- Interactive docs: `http://localhost:8080/docs`
- OpenAPI schema: `http://localhost:8080/openapi.json`

### Architecture Docs
- See main Dopemux documentation for system architecture
- Component-specific documentation in docstrings

## 🤝 Contributing

1. Follow the established patterns for ADHD optimization
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all integrations work correctly

## 📄 License

Part of the Dopemux project - see main project license.

---

**Status**: ✅ **PHASE 1 COMPLETE** - All core components implemented and integrated
**Version**: 1.0.0
**Ready for**: Phase 2 ADHD dynamic prompting enhancements</content>
</xai:function_call">The file content contains invalid XML/HTML markup. Please provide clean Python code only.