# Dopemux Installation Guide

Complete installation guide for Dopemux with Leantime and Task-Master AI integration.

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows with WSL2
- **Docker**: Version 20.10+ with Docker Compose
- **Python**: 3.8+ (for installer and health checks)
- **Node.js**: 18+ (for Task-Master AI)
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: 10GB available space

### ADHD Considerations
- Installation takes 15-25 minutes total
- Progress is shown with visual indicators
- Can be paused/resumed if attention breaks needed
- Health checks ensure everything works before finishing

## Quick Installation

### Option 1: Automated Installer (Recommended)
```bash
cd /path/to/dopemux-mvp
python installers/leantime/install.py --interactive
```

The installer will:
- ✅ Check prerequisites
- 🐳 Deploy Leantime with Docker
- 🤖 Install Task-Master AI
- 🔗 Configure MCP integrations
- 🧠 Set up ADHD optimizations
- 🏥 Run health checks

### Option 2: Manual Installation

#### Step 1: Deploy Leantime
```bash
cd docker/leantime
docker-compose up -d
```

#### Step 2: Install Task-Master AI
```bash
npm install -g claude-task-master
```

#### Step 3: Configure MCP Servers
```bash
# Add to your Claude Desktop config
{
  "mcpServers": {
    "task-master": {
      "command": "task-master-mcp",
      "args": ["--port", "3001"]
    }
  }
}
```

#### Step 4: Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create `.env` file:
```bash
# Leantime Configuration
LEANTIME_URL=http://localhost:8080
LEANTIME_API_KEY=your_api_key_here
LEANTIME_DB_PASSWORD=secure_password_here

# Task-Master Configuration
TASKMASTER_PORT=3001
TASKMASTER_API_KEY=your_taskmaster_key

# ADHD Optimizations
ADHD_FOCUS_DURATION=25  # minutes
ADHD_BREAK_DURATION=5   # minutes
ADHD_ATTENTION_TRACKING=true
ADHD_GENTLE_MODE=true

# ADHD Feature Flags
ADHD_AUTO_BREAK_REMINDERS=true
ADHD_CONTEXT_PRESERVATION=true
ADHD_COGNITIVE_LOAD_TRACKING=true
ADHD_ATTENTION_STATE_DETECTION=true
ADHD_SCHEDULE_OPTIMIZATION=true
```

### Database Setup

Leantime automatically creates required tables. For custom setup:

```sql
-- Database will be created automatically
-- Default credentials in docker-compose.yml
-- Change LEANTIME_DB_PASSWORD in production
```

### MCP Integration Setup

The system uses Model Context Protocol for AI integrations:

1. **Leantime MCP Bridge**: Manages project/task operations
2. **Task-Master MCP Bridge**: Handles PRD parsing and task decomposition
3. **Sync Manager**: Bidirectional synchronization between systems

## ADHD-Optimized Features

### Attention Management
- **Focus Sessions**: 25-minute work blocks with 5-minute breaks
- **Context Preservation**: Auto-save every 30 seconds
- **Gentle Notifications**: Non-intrusive progress updates
- **Task Chunking**: Large tasks broken into manageable pieces

### Cognitive Load Reduction
- **Progressive Disclosure**: Essential info shown first
- **Visual Indicators**: Progress bars and status emojis
- **Decision Support**: Maximum 3 options presented
- **Executive Function**: Clear next steps always provided

## Health Checks

Verify installation:
```bash
python installers/leantime/health_check.py
```

Expected output:
```
🏥 Dopemux Health Check
======================

🐳 Docker Services... ✅
📊 Leantime API... ✅
🤖 Task-Master AI... ✅
🔗 MCP Integration... ✅
🧠 ADHD Optimizations... ✅

All systems operational! 🎉
```

## Troubleshooting

### Common Issues

#### Docker Services Not Starting
```bash
# Check Docker status
docker ps -a

# Restart services
cd docker/leantime
docker-compose down && docker-compose up -d
```

#### Leantime Database Connection
```bash
# Check database logs
docker-compose logs mysql_leantime

# Reset database (WARNING: loses data)
docker-compose down -v
docker-compose up -d
```

#### Task-Master AI Not Responding
```bash
# Check if Task-Master is running
ps aux | grep task-master

# Restart Task-Master
pkill -f task-master
npm install -g claude-task-master
```

#### MCP Integration Issues
```bash
# Test MCP connections
python -c "
from src.integrations.leantime_bridge import LeantimeMCPClient
client = LeantimeMCPClient()
print(client.health_check())
"
```

### Performance Optimization

#### For Limited Resources
```bash
# Reduce Docker memory usage
echo 'LEANTIME_DB_POOL_SIZE=5' >> .env
docker-compose restart
```

#### For High Load
```bash
# Scale Redis cache
echo 'REDIS_MAXMEMORY=1gb' >> .env
docker-compose restart redis_leantime
```

## Uninstallation

### Complete Removal
```bash
# Stop all services
cd docker/leantime
docker-compose down -v

# Remove Docker images
docker rmi leantime/leantime:latest mysql:8.0 redis:alpine

# Uninstall Task-Master
npm uninstall -g claude-task-master

# Remove Python packages
pip uninstall -r requirements.txt
```

### Partial Removal (Keep Data)
```bash
# Stop services but keep volumes
docker-compose down

# Remove only application containers
docker rmi leantime/leantime:latest
```

## Support

### Getting Help
- 📖 Check [User Guide](USER_GUIDE.md) for usage instructions
- 🐛 Report issues at: https://github.com/your-repo/dopemux-mvp/issues
- 💬 Community support: [Discord/Slack link]

### ADHD-Friendly Support
- Issues can be reported in any format (bullet points, voice notes, etc.)
- Include health check output when possible
- Attention-friendly responses provided
- No judgment for "obvious" questions

---

**Installation complete!** 🎉 Ready to use Dopemux with ADHD-optimized project management.