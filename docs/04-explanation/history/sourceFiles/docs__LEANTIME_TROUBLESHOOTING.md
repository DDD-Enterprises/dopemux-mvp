# Leantime Integration Troubleshooting Guide

## 🔧 Critical Nginx Port Fix

### Problem: "Empty Reply from Server" Error

**Symptoms:**
- `curl` returns HTTP status 000
- Connection established but no response
- "Empty reply from server" message

**Root Cause:**
The Leantime Docker image has nginx configured to listen on port 8080 inside the container, but Docker Compose maps host port 8080 to container port 80, creating a mismatch.

**Solution:**
```bash
# Fix nginx port configuration
docker exec -u root leantime sed -i 's/listen 8080;/listen 80;/' /etc/nginx/nginx.conf
docker exec -u root leantime nginx -s reload
```

**Verification:**
```bash
# Check nginx is listening on port 80
docker exec leantime netstat -tlnp | grep :80

# Test connectivity
curl -s http://localhost:8080/
```

### Alternative Solutions

**Option 1: Change Docker Port Mapping**
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:8080"  # Instead of "8080:80"
```

**Option 2: Persistent Nginx Configuration**
Create a custom nginx config file and mount it:
```yaml
volumes:
  - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

## 🐳 Docker Issues

### Container Startup Problems

**Issue**: Containers fail to start or become unhealthy

**Debug Steps:**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs leantime
docker-compose logs mysql_leantime
docker-compose logs redis_leantime

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

### Port Conflicts

**Issue**: Port already in use errors

**Solutions:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill conflicting processes
sudo kill -9 <PID>

# Use different ports in docker-compose.yml
ports:
  - "8081:80"  # Use port 8081 instead
```

### Volume Permission Issues

**Issue**: Permission denied errors for volumes

**Fix:**
```bash
# Set correct ownership
docker exec -u root leantime chown -R www-data:www-data /var/www/html
docker exec -u root leantime chmod -R 755 /var/www/html
```

## 🔗 Network Connectivity

### Internal Container Communication

**Test Database Connection:**
```bash
# From Leantime container
docker exec leantime mysql -h mysql_leantime -u leantime_user -p leantime_db
```

**Test Redis Connection:**
```bash
# From Leantime container
docker exec leantime redis-cli -h redis_leantime -a "dopemux_redis_2024_secure_key_cache" ping
```

### External Access Issues

**Issue**: Cannot access from host machine

**Checks:**
```bash
# Verify Docker port mapping
docker port leantime

# Test from different interfaces
curl -4 http://127.0.0.1:8080/
curl -6 http://[::1]:8080/
curl http://localhost:8080/
```

## 🐛 PHP/Application Issues

### PHP-FPM Problems

**Check PHP-FPM Status:**
```bash
docker exec leantime ps aux | grep php-fpm
docker exec leantime netstat -tlnp | grep :9000
```

**Restart PHP-FPM:**
```bash
docker exec -u root leantime supervisorctl restart php-fpm
```

### Database Connection Issues

**Check Environment Variables:**
```bash
docker exec leantime env | grep -E "(LEAN_DB|MYSQL)"
```

**Test Database Connection:**
```bash
docker exec leantime php -r "
$pdo = new PDO('mysql:host=mysql_leantime;dbname=leantime_db', 'leantime_user', 'dopemux_db_2024_secure_random_key_abc');
echo 'Database connection successful';
"
```

## 🔐 Authentication & API Issues

### API Token Problems

**Generate New Token:**
1. Complete Leantime web setup
2. Go to User Settings → API
3. Generate new personal access token
4. Update `.env` file with new token

**Test API Access:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/v1/projects
```

### MCP Integration Issues

**Check Python Dependencies:**
```bash
pip list | grep -E "(aiohttp|pyjwt|pydantic)"
```

**Test HTTP Connectivity:**
```bash
python3 -c "
import aiohttp
import asyncio

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/') as resp:
            print(f'Status: {resp.status}')

asyncio.run(test())
"
```

## 🧠 ADHD Feature Issues

### Context Preservation Not Working

**Check Environment Variables:**
```bash
docker exec leantime env | grep -E "LEAN_.*ADHD|LEAN_.*CONTEXT"
```

**Expected Values:**
```env
LEAN_ADHD_MODE=true
LEAN_CONTEXT_PRESERVATION=true
LEAN_NOTIFICATION_BATCH=true
```

### Task Filtering Problems

**Verify Database Schema:**
```bash
docker exec mysql_leantime mysql -u leantime_user -p leantime_db -e "SHOW TABLES LIKE '%task%';"
```

## 🔄 Restart Procedures

### Clean Restart (Preserves Data)
```bash
cd /Users/hue/code/dopemux-mvp/docker/leantime
docker-compose restart
```

### Full Reset (Destroys Data)
```bash
cd /Users/hue/code/dopemux-mvp/docker/leantime
docker-compose down -v
docker-compose up -d
```

### Nginx-Only Restart
```bash
docker exec -u root leantime nginx -s reload
```

## 📋 Health Check Commands

### Quick Health Check
```bash
#!/bin/bash
echo "🏥 Leantime Health Check"
echo "======================="

# Check containers
echo "📦 Container Status:"
docker-compose ps

# Check HTTP
echo "🌐 HTTP Status:"
curl -s -w "Status: %{http_code}\n" http://localhost:8080/ -o /dev/null

# Check ports
echo "🔌 Port Status:"
nc -z localhost 8080 && echo "✅ Port 8080 accessible" || echo "❌ Port 8080 blocked"

echo "🎉 Health check complete"
```

### Detailed Diagnostics
```bash
#!/bin/bash
echo "🔍 Detailed Leantime Diagnostics"
echo "================================"

# Nginx status
echo "Nginx listening ports:"
docker exec leantime netstat -tlnp | grep nginx

# PHP-FPM status
echo "PHP-FPM processes:"
docker exec leantime ps aux | grep php-fpm | head -3

# Database connectivity
echo "Database connection test:"
docker exec mysql_leantime mysqladmin -u leantime_user -p"dopemux_db_2024_secure_random_key_abc" ping

# Redis connectivity
echo "Redis connection test:"
docker exec redis_leantime redis-cli -a "dopemux_redis_2024_secure_key_cache" ping

echo "🏁 Diagnostics complete"
```

## 📞 Emergency Recovery

If all else fails, use this complete reset procedure:

```bash
#!/bin/bash
echo "🚑 Emergency Leantime Recovery"
echo "============================="

# Stop everything
docker-compose down -v
docker system prune -f

# Remove orphaned containers
docker container prune -f

# Restart fresh
docker-compose up -d

# Wait for startup
sleep 30

# Apply nginx fix
docker exec -u root leantime sed -i 's/listen 8080;/listen 80;/' /etc/nginx/nginx.conf
docker exec -u root leantime nginx -s reload

# Test
curl -s http://localhost:8080/ && echo "✅ Recovery successful" || echo "❌ Recovery failed"
```

---

**Last Updated**: September 21, 2025
**Status**: Verified working configuration