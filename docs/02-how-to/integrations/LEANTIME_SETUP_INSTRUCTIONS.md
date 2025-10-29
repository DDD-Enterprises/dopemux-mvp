# Leantime Setup Instructions - Quick Start

**Status**: MCP Integration Complete ✅ | Leantime Installation Required ⏳

## Quick Setup (5 minutes)

### Step 1: Access Leantime
```bash
# Open Leantime in your browser
open http://localhost:8080
```

### Step 2: Complete Installation Wizard

1. **Welcome Screen**: Click "Start Installation"
2. **Database**: Already configured (skip/auto-filled)
   - Host: `mysql_leantime`
   - Database: `leantime`
   - User: Auto-configured
3. **Admin Account**: Create your admin user
   - Username: `admin` (recommended)
   - Email: your@email.com
   - Password: Choose a strong password
4. **Company Details**: Optional

### Step 3: Generate API Token

After installation:

1. Log in as admin
2. Go to **Settings** → **API**
3. Click **Generate New Token**
4. Copy the generated token

### Step 4: Configure Bridge

```bash
# Update the API token
cd docker/mcp-servers/leantime-bridge

# Edit .env file
nano .env
# Update this line:
# LEANTIME_API_TOKEN=<paste_your_token_here>

# Or use sed:
sed -i '' 's/LEANTIME_API_TOKEN=.*/LEANTIME_API_TOKEN=your_new_token/' .env
```

### Step 5: Restart Bridge

```bash
docker-compose -f docker/mcp-servers/docker-compose.yml restart leantime-bridge
```

### Step 6: Test Integration

```bash
cd docker/mcp-servers/leantime-bridge
python test_http_server.py
```

**Expected output**:
```
✓ TEST PASSED: Successfully connected via SSE
✓ TEST PASSED: MCP initialize successful
✓ TEST PASSED: Successfully listed tools
```

## Verify in Claude

```
# List available tools
What tools do you have available from leantime?

# Create a test project
Create a new Leantime project called "Test Project" with description "Testing MCP integration"

# List projects
Show me all projects in Leantime
```

## Troubleshooting

### "Redirect to /install" Error
**Cause**: Installation not complete
**Solution**: Complete steps 1-2 above

### "API Token Invalid"  
**Cause**: Token not configured or incorrect
**Solution**: Regenerate token in Leantime UI and update .env

### "Cannot connect to Leantime"
**Cause**: Leantime container not running
**Solution**:
```bash
docker-compose -f docker/leantime/docker-compose.yml up -d
```

## Health Check

```bash
# Check all services
docker ps --filter "name=leantime"

# Expected:
# ✅ leantime - Up (healthy)
# ✅ mysql_leantime - Up (healthy)  
# ✅ redis_leantime - Up (healthy)
# ✅ mcp-leantime-bridge - Up (healthy)

# Test API directly
curl http://localhost:3015/sse --head
# Expected: HTTP/1.1 200 OK
```

## What You Get

After setup, you can:
- ✅ Create and manage projects via Claude
- ✅ Add tasks and tickets
- ✅ Track progress and time
- ✅ Create milestones  
- ✅ Sync with other task management systems
- ✅ Use ADHD-optimized workflows

## Support

- **Documentation**: `LEANTIME_MCP_INTEGRATION_COMPLETE.md`
- **API Reference**: `docker/mcp-servers/leantime-bridge/HTTP_SERVER_README.md`
- **Test Suite**: `docker/mcp-servers/leantime-bridge/test_http_server.py`

---

**Total Setup Time**: ~5 minutes
**Integration Status**: Production Ready
**Next**: Complete installation at http://localhost:8080
