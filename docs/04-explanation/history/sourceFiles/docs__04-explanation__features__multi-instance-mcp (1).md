# 🔄 Multi-Instance MCP Hub

**Run multiple isolated Dopemux environments simultaneously with smart resource sharing.**

## 🎯 Overview

The Multi-Instance MCP system allows you to run multiple Dopemux environments (dev, staging, prod, user1, etc.) simultaneously without conflicts, while intelligently sharing resources like code indexing and session state.

## 🏗️ Core Architecture

### 🔄 Smart Volume Strategy

**Shared Across All Instances:**
- **Code Indexing** → Semantic search, vector database, embeddings
- **Documentation Cache** → API references, context7 cache
- **Session State** → Dopemux and Claude session continuity

**Isolated Per Instance:**
- **Project Data** → Task management, project memory, decisions
- **Logs & Config** → Instance-specific logs and settings
- **Networks & Ports** → Complete isolation for services

### 🎯 Benefits

**💡 Efficiency:**
- Code indexed once, used by all instances (70% storage reduction)
- Shared documentation cache for faster responses
- Session state preserved across instance switches

**🔒 Proper Isolation:**
- Independent project states per instance
- Separate logs for debugging
- No cross-instance interference

**⚡ Performance:**
- Faster semantic search (shared embeddings)
- Reduced startup time (cached data ready)
- Seamless context switching between environments

## 📚 Related Documentation

### 🔧 How-To Guides
- [Setting Up Multi-Instance MCP](../../02-how-to/mcp/multi-instance-setup.md)
- [Managing Multiple Environments](../../02-how-to/mcp/environment-management.md)
- [Troubleshooting Instance Conflicts](../../02-how-to/mcp/instance-troubleshooting.md)

### 📖 Technical Reference
- [Multi-Instance Configuration Reference](../../03-reference/mcp/multi-instance-config.md)
- [Port Allocation Schema](../../03-reference/mcp/port-allocation.md)
- [Volume Mapping Reference](../../03-reference/mcp/volume-mapping.md)

### 📚 Tutorials
- [Creating Your First Multi-Instance Setup](../../01-tutorials/mcp/multi-instance-tutorial.md)
- [Dev-Staging-Prod Workflow](../../01-tutorials/mcp/dev-staging-prod.md)

### 💡 Deep Explanations
- [Multi-Instance Architecture Design](../architecture/multi-instance-design.md)
- [Session State Management](../architecture/session-continuity.md)
- [Resource Sharing Strategy](../architecture/resource-optimization.md)

## 🚀 Quick Start

### Basic Setup
```bash
# Create default instance (ports 3000-3020)
cd docker/mcp-servers
./launch-instance.sh default 3000

# Create dev instance (ports 3030-3050)
./launch-instance.sh dev 3030

# Create staging instance (ports 3060-3080)
./launch-instance.sh staging 3060
```

### Instance Management
```bash
# Start instances
./instance-default/start.sh
./instance-dev/start.sh

# Check status
./instance-default/status.sh

# View logs
./instance-dev/logs.sh

# Stop instances
./instance-staging/stop.sh
```

## 🎛️ Use Cases

### 🔬 **Development Workflows**
- **Feature Development** → `dev` instance for experimental work
- **Testing & QA** → `staging` instance for validation
- **Production Deployment** → `prod` instance for live releases
- **Session continuity maintained across all environments**

### 👥 **Multi-User Environments**
- **Team Collaboration** → `user1`, `user2`, `user3` instances
- **Shared code indexing** → Everyone benefits from same embeddings
- **Isolated project state** → No interference between team members

### 🧪 **Experimentation**
- **A/B Testing** → Multiple instances with different configurations
- **Version Comparison** → Run different Dopemux versions simultaneously
- **Feature Flagging** → Enable features per instance

## 🔌 Integration Points

### 🤖 **Claude Code Integration**
- Session state shared across instances
- Context preservation during environment switches
- MCP server coordination

### 📋 **Leantime Integration**
- Project data isolation per instance
- Shared team resources where appropriate
- Environment-specific project configurations

### 🧠 **ADHD Optimizations**
- Attention state preserved across switches
- Context switching support (environment transitions)
- Task continuation between instances

## ⚠️ Important Considerations

### 🔒 **Security**
- Use different API keys per environment when possible
- Isolate production instances on separate networks
- Regular backup of important volumes

### 🚀 **Performance**
- Don't run more instances than needed
- Monitor resource usage with `docker stats`
- Use specific service commands to reduce overhead

### 📊 **Maintenance**
- Regularly update images: `docker-compose pull`
- Clean up unused volumes: `docker volume prune`
- Monitor logs for errors across all instances

## 🆘 Troubleshooting

### 🔧 **Common Issues**
- **Port Conflicts** → [Port Resolution Guide](../../02-how-to/mcp/port-conflicts.md)
- **Volume Permissions** → [Volume Troubleshooting](../../02-how-to/mcp/volume-issues.md)
- **Resource Limits** → [Performance Optimization](../../02-how-to/mcp/performance-tuning.md)

### 📋 **Emergency Procedures**
- **Instance Recovery** → [Instance Recovery Runbook](../../92-runbooks/mcp/instance-recovery.md)
- **Data Backup** → [Multi-Instance Backup](../../92-runbooks/mcp/multi-instance-backup.md)

## 🏗️ Architecture Details

### 📝 **Related ADRs**
- [ADR-015: Multi-Instance Architecture](../../90-adr/ADR-015-multi-instance-architecture.md)
- [ADR-016: Session State Sharing](../../90-adr/ADR-016-session-state-sharing.md)
- [ADR-017: Resource Optimization Strategy](../../90-adr/ADR-017-resource-optimization.md)

### 🎯 **Implementation Status**
- ✅ **Core Infrastructure** → Multi-instance Docker orchestration
- ✅ **Volume Strategy** → Smart shared/isolated volume mapping
- ✅ **Session Management** → Cross-instance session continuity
- ✅ **Port Management** → Automatic conflict resolution
- 🚧 **Advanced Features** → Load balancing, auto-scaling (future)

---

**🎯 Next Steps:**
1. [Set up your first multi-instance environment](../../01-tutorials/mcp/multi-instance-tutorial.md)
2. [Configure environment-specific settings](../../02-how-to/mcp/environment-configuration.md)
3. [Learn about session continuity](../architecture/session-continuity.md)

*Making multi-environment development seamless for ADHD developers! 🧠*