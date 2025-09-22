# Dopemux MCP Servers - Multi-Instance Guide

Run multiple isolated Dopemux instances without conflicts. Each instance gets its own ports, networks, volumes, and containers.

## Quick Start

### 1. Launch Your First Instance
```bash
# Default instance on ports 3000-3020
./launch-instance.sh default 3000

# Edit the generated .env file with your API keys
nano .env.default

# Start the instance
docker-compose --env-file .env.default -f docker-compose.multi-instance.yml up -d
```

### 2. Launch Additional Instances
```bash
# Development instance on ports 3030-3050
./launch-instance.sh dev 3030
nano .env.dev
docker-compose --env-file .env.dev -f docker-compose.multi-instance.yml up -d

# Staging instance on ports 3060-3080
./launch-instance.sh staging 3060
nano .env.staging
docker-compose --env-file .env.staging -f docker-compose.multi-instance.yml up -d
```

## Instance Management

### Using Helper Scripts
Each instance gets its own helper scripts in `instance-{name}/`:

```bash
# Start instance
./instance-default/start.sh
./instance-dev/start.sh

# Stop instance
./instance-default/stop.sh
./instance-dev/stop.sh

# View logs
./instance-default/logs.sh

# Check status
./instance-default/status.sh
```

### Manual Commands
```bash
# Start instance
docker-compose --env-file .env.{instance} -f docker-compose.multi-instance.yml up -d

# Stop instance
docker-compose --env-file .env.{instance} -f docker-compose.multi-instance.yml down

# View logs
docker-compose --env-file .env.{instance} -f docker-compose.multi-instance.yml logs -f

# Check status
docker-compose --env-file .env.{instance} -f docker-compose.multi-instance.yml ps
```

## Port Allocation

Each instance uses 21 consecutive ports starting from `PORT_BASE`:

| Service | Port Offset | Example (BASE=3000) | Example (BASE=3030) |
|---------|-------------|---------------------|---------------------|
| MAS Sequential | +1 | 3001 | 3031 |
| Context7 | +2 | 3002 | 3032 |
| Zen | +3 | 3003 | 3033 |
| ConPort | +4 | 3004 | 3034 |
| Task Master | +5 | 3005 | 3035 |
| Serena | +6 | 3006 | 3036 |
| Claude Context | +7 | 3007 | 3037 |
| Exa | +8 | 3008 | 3038 |
| MorphLLM | +11 | 3011 | 3041 |
| Desktop Commander | +12 | 3012 | 3042 |
| Minio Console | +15 | 3015 | 3045 |
| Minio API | +16 | 3016 | 3046 |
| Milvus | +17 | 3017 | 3047 |
| Milvus WebUI | +18 | 3018 | 3048 |

**Recommended Port Bases (multiples of 30):**
- Instance 1: 3000
- Instance 2: 3030
- Instance 3: 3060
- Instance 4: 3090
- Instance 5: 3120

## Instance Isolation Strategy

### 🔄 **Shared Data (Efficient Resource Usage)**
These volumes are shared across ALL instances for efficiency:

**📚 Code Indexing & Search:**
- `mcp_shared_claude_context_data` - Semantic code embeddings
- `mcp_shared_claude_context_cache` - Search result cache
- `mcp_shared_milvus_data` - Vector database
- `mcp_shared_etcd_data` - Milvus metadata
- `mcp_shared_minio_data` - Object storage

**📖 Documentation Cache:**
- `mcp_shared_context7_cache` - API reference cache

**💾 Session State & Context:**
- `mcp_shared_dopemux_sessions` - Dopemux session data (.dopemux/)
- `mcp_shared_claude_sessions` - Claude Code session data (.claude/)

✅ **Why shared?** All instances work on the same codebase, so they benefit from shared:
- Code embeddings and semantic search indexes
- Documentation caches
- Vector database with code understanding
- **Session continuity across instances** - switch between dev/staging/prod seamlessly

### 🔒 **Isolated Data (Instance-Specific)**
These volumes are separate per instance:

**📝 Instance State:**
- `mcp_{instance}_logs` - Server logs
- `mcp_{instance}_cache` - Instance-specific cache
- `mcp_{instance}_zen_logs` - Zen server logs
- `mcp_{instance}_zen_config` - Zen configuration

**🎯 Project Data:**
- `mcp_{instance}_conport_data` - Project memory & decisions
- `mcp_{instance}_task_master_data` - Task management
- `mcp_{instance}_serena_data` - Code navigation state

✅ **Why isolated?** These contain instance-specific:
- Development session state
- Task management data
- Project decisions and memory
- Configuration preferences

### 🌐 **Networks (Fully Isolated)**
- `mcp-network-default`
- `mcp-network-dev`
- `mcp-network-staging`

### 📦 **Containers (Fully Isolated)**
- `mcp-default-*`
- `mcp-dev-*`
- `mcp-staging-*`

### 🔌 **Ports (Fully Isolated)**
- Non-overlapping port ranges
- Automatic conflict detection

### 🎯 **Benefits of This Approach**

**💡 Efficiency:**
- Code only indexed once across all instances
- Shared vector database reduces storage overhead
- Documentation cache shared for faster responses
- **Session state preserved across instance switches**

**🔒 Isolation Where It Matters:**
- Each instance has independent project state
- Separate logs for debugging
- No cross-instance interference in decision tracking

**⚡ Performance:**
- Faster semantic search (shared embeddings)
- Reduced startup time (cached data available)
- Lower resource usage overall
- **Seamless context switching between instances**

**🎛️ Flexibility:**
- Can run dev/staging/prod simultaneously
- Each instance can have different configurations
- Easy to add/remove instances
- **Pick up exactly where you left off in any instance**

## Environment Variables

Each `.env.{instance}` file contains:

```bash
# Instance identity
DOPEMUX_INSTANCE=default
PORT_BASE=3000

# Auto-generated names
CONTAINER_PREFIX=mcp-default
NETWORK_NAME=mcp-network-default
VOLUME_PREFIX=mcp_default

# Your API keys
OPENAI_API_KEY=your_key_here
VOYAGEAI_API_KEY=your_key_here
# ... etc
```

## Monitoring Multiple Instances

### List All Running Instances
```bash
docker ps --filter "label=mcp.instance" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### View Logs by Instance
```bash
# All containers for an instance
docker-compose --env-file .env.default -f docker-compose.multi-instance.yml logs -f

# Specific service in instance
docker logs -f mcp-default-zen
```

### Check Resource Usage
```bash
# All MCP containers
docker stats $(docker ps --filter "label=mcp.instance" --format "{{.Names}}")
```

## Troubleshooting

### Port Conflicts
```bash
# Check what's using a port
lsof -i :3001

# The launch script automatically checks for conflicts
./launch-instance.sh dev 3030
```

### Clean Up Instance
```bash
# Stop and remove everything for an instance
docker-compose --env-file .env.dev -f docker-compose.multi-instance.yml down -v

# Remove volumes (⚠️ destroys data!)
docker volume ls | grep "mcp_dev_" | awk '{print $2}' | xargs docker volume rm
```

### Reset All Instances
```bash
# Stop all MCP instances
docker ps --filter "label=mcp.instance" --format "{{.Names}}" | xargs docker stop

# Remove all MCP containers
docker ps -a --filter "label=mcp.instance" --format "{{.Names}}" | xargs docker rm
```

## Best Practices

### 🎯 Use Cases
- **default**: Your main development environment
- **dev**: Experimental features and testing
- **staging**: Pre-production testing
- **prod**: Production deployments
- **user1, user2**: Multi-user environments

### 🔒 Security
- Use different API keys per environment when possible
- Isolate production instances on separate networks
- Regular backup of important volumes

### 🚀 Performance
- Don't run more instances than needed
- Monitor resource usage with `docker stats`
- Use specific service commands to reduce overhead

### 📊 Maintenance
- Regularly update images: `docker-compose pull`
- Clean up unused volumes: `docker volume prune`
- Monitor logs for errors across all instances

## Migration from Single Instance

If you're currently using the original `docker-compose.yml`:

```bash
# Stop current instance
docker-compose down

# Launch as "default" instance
./launch-instance.sh default 3000

# Copy your existing .env values to .env.default
# Start new multi-instance setup
docker-compose --env-file .env.default -f docker-compose.multi-instance.yml up -d
```

Your data volumes will be preserved if using the same volume names.

## Session State Management

### 🔄 **Cross-Instance Session Continuity**

Dopemux now shares session state across all instances, so you can:

- Start work in the `dev` instance
- Switch to `staging` for testing
- Continue in `prod` for deployment
- **All while maintaining your session context!**

### 📁 **Shared Session Data**

These directories are automatically shared across instances:

```
/workspace/.dopemux/     # Dopemux session state
├── sessions/           # Active sessions
├── context.db         # Context database
├── context.json       # Context metadata
├── attention.json     # ADHD attention tracking
└── config.json        # Instance configuration

/workspace/.claude/     # Claude Code session state
├── session.md         # Session persistence
├── context.md         # Context management
└── claude.md          # Project instructions
```

### 🎯 **How It Works**

1. **Session Data**: Stored in shared volumes `mcp_shared_dopemux_sessions` and `mcp_shared_claude_sessions`
2. **Automatic Sync**: All instances access the same session data in real-time
3. **Context Preservation**: Switch instances without losing your mental model
4. **ADHD Support**: Attention metrics and task state persist across switches

### 💡 **Usage Examples**

```bash
# Start development work
./instance-dev/start.sh
# Work on features, build context...

# Switch to staging for testing (keeps all context!)
./instance-staging/start.sh
# Run tests with full session awareness...

# Deploy to production (session continuity maintained!)
./instance-prod/start.sh
# Deploy with complete context of what was built and tested
```

### ⚠️ **Important Notes**

- Session state is **shared** - changes in one instance affect others
- For completely isolated work, use separate project directories
- Session files are no longer created randomly in repo root
- All session data is properly containerized and persistent