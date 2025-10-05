# Dopemux Unified Architecture Guide

## 🎯 **Overview**

The unified architecture consolidates all Docker services into a single orchestration system, eliminating the container fragmentation and port conflicts that were causing health issues.

## 🏗️ **Architecture Layers**

### **Shared Infrastructure Layer**
- **PostgreSQL Primary**: Single database server with multiple databases
- **Redis Primary**: Event bus and general caching (port 6379)
- **Redis Leantime**: Dedicated for Leantime (port 6380)
- **MySQL**: Required for Leantime compatibility (port 3306)

### **Vector & Search Infrastructure**
- **Milvus + Dependencies**: Vector database with etcd and minio
- **Unified Network**: Single Docker network for all services

### **Two-Plane Architecture**

#### **Project Management Plane**
- **Leantime** (8080): Status authority, team dashboards
- **Task Master AI** (3005): Task decomposition and AI planning
- **Leantime Bridge** (3015): PM integration MCP server

#### **Cognitive Plane**
- **ConPort** (3004): Decision logging and memory authority
- **Serena LSP** (3006): Code navigation with ADHD accommodations
- **Context7** (3002): Documentation and API references
- **Zen** (3003): Multi-model orchestration

#### **Coordination Layer**
- **Integration Bridge** (3016): Cross-plane communication at PORT_BASE+16

## 🚀 **Migration Process**

### **Step 1: Run Migration Script**
```bash
# Execute the automated migration
./scripts/migrate-to-unified.sh
```

### **Step 2: Configure API Keys**
Edit `.env` and add your API keys:
```bash
# Required API keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
# ... etc
```

### **Step 3: Start Unified System**
```bash
# Start all services
docker-compose -f docker-compose.unified.yml up -d

# Check status
docker-compose -f docker-compose.unified.yml ps
```

## 🔧 **Management Commands**

### **Service Management**
```bash
# Start all services
docker-compose -f docker-compose.unified.yml up -d

# Stop all services
docker-compose -f docker-compose.unified.yml down

# Restart specific service
docker-compose -f docker-compose.unified.yml restart mcp-conport

# View logs
docker-compose -f docker-compose.unified.yml logs -f mcp-zen
```

### **Health Monitoring**
```bash
# Check all container status
docker-compose -f docker-compose.unified.yml ps

# Check specific service health
curl http://localhost:3004/health  # ConPort
curl http://localhost:3002/health  # Context7

# Monitor Redis
docker exec -it dopemux-redis-primary redis-cli ping
```

### **Database Access**
```bash
# Connect to primary PostgreSQL
docker exec -it dopemux-postgres-primary psql -U dopemux -d dopemux_unified

# Connect to ConPort database
docker exec -it dopemux-postgres-primary psql -U dopemux -d conport

# Connect to MySQL (Leantime)
docker exec -it dopemux-mysql-leantime mysql -u leantime -p leantime
```

## 🌐 **Service URLs**

### **Web Interfaces**
- **Leantime**: http://localhost:8080
- **Redis Commander**: http://localhost:8081
- **Minio Console**: http://localhost:9001

### **MCP Server Endpoints**
- **Context7**: http://localhost:3002
- **Zen**: http://localhost:3003
- **ConPort**: http://localhost:3004
- **Task Master**: http://localhost:3005
- **Serena**: http://localhost:3006
- **Claude Context**: http://localhost:3007
- **GPT-R MCP**: http://localhost:3009
- **Leantime Bridge**: http://localhost:3015
- **Integration Bridge**: http://localhost:3016

## 🧠 **ADHD-Optimized Features**

### **Context Preservation**
- ConPort automatically saves context every 30 seconds
- Integration Bridge maintains cross-plane state
- All services share unified network for seamless communication

### **Authority Boundaries**
- **Status Updates**: Only through Leantime
- **Decisions**: Only through ConPort
- **Code Navigation**: Only through Serena LSP
- **Cross-Plane**: Only through Integration Bridge

### **Progressive Disclosure**
- Start with critical services first (Context7, Zen, ConPort)
- Add optional services as needed
- Clear health checks and status monitoring

## 🔄 **Rollback Process**

If you need to rollback to the previous setup:

```bash
# Stop unified system
docker-compose -f docker-compose.unified.yml down

# Restore from backup
BACKUP_DIR="./backup/migration-YYYYMMDD_HHMMSS"
cp "$BACKUP_DIR/.env.backup" .env

# Start old system (if compose files exist)
docker-compose -f docker/docker-compose.event-bus.yml up -d
docker-compose -f docker/mcp-servers/docker-compose.yml up -d
# ... etc
```

## 🚨 **Troubleshooting**

### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :3004
netstat -tuln | grep 3004

# Kill process using port
kill -9 $(lsof -t -i:3004)
```

### **Container Health Issues**
```bash
# Check container logs
docker-compose -f docker-compose.unified.yml logs mcp-conport

# Restart unhealthy service
docker-compose -f docker-compose.unified.yml restart mcp-conport

# Check resource usage
docker stats
```

### **Database Connection Issues**
```bash
# Test PostgreSQL connection
docker exec -it dopemux-postgres-primary pg_isready -U dopemux

# Check database exists
docker exec -it dopemux-postgres-primary psql -U dopemux -l
```

## 📊 **Benefits of Unified Architecture**

1. **Eliminates Port Conflicts**: Unique ports for each service
2. **Reduces Resource Usage**: Single instances of databases
3. **Simplifies Management**: One docker-compose file
4. **Improves Health**: Proper dependencies and networking
5. **ADHD-Friendly**: Clear structure with authority boundaries
6. **Better Monitoring**: Centralized logging and health checks

## ⚡ **Quick Commands Reference**

```bash
# Full system restart
docker-compose -f docker-compose.unified.yml down && docker-compose -f docker-compose.unified.yml up -d

# Check MCP servers
curl -s http://localhost:3002/health && echo " Context7 ✅" || echo " Context7 ❌"
curl -s http://localhost:3003/health && echo " Zen ✅" || echo " Zen ❌"
curl -s http://localhost:3004/health && echo " ConPort ✅" || echo " ConPort ❌"

# View all logs
docker-compose -f docker-compose.unified.yml logs --tail=50

# Resource usage
docker-compose -f docker-compose.unified.yml top
```

This unified architecture provides a clean, manageable foundation for your ADHD-optimized development platform!