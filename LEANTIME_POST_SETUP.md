# Leantime Post-Setup Tasks

## 🎯 After completing the web installation, follow these steps:

### 1. Login and Initial Configuration
- Login with your admin credentials
- Navigate to Settings → User Settings
- Generate a Personal Access Token (API section)

### 2. Update Environment Configuration
Replace the token in `.env`:
```bash
cd /Users/hue/code/dopemux-mvp/docker/leantime
# Edit .env file and update:
LEAN_MCP_TOKEN=your_new_generated_token_here
```

### 3. Test API Integration
```bash
# Test basic API connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/v1/projects

# Test Python bridge
python3 -c "
import sys
sys.path.insert(0, '/Users/hue/code/dopemux-mvp/src')
# We'll run this after token is configured
"
```

### 4. Create ADHD-Optimized Project Structure

#### Project Setup:
- **Name**: "ADHD Development Workflow"
- **Description**: "Testing cognitive load tracking and attention management"
- **Tags**: #adhd #focus #productivity

#### Initial Tasks to Create:
1. **High Cognitive Load Task**
   - Title: "Complex Algorithm Implementation"
   - Priority: Hyperfocus
   - Cognitive Load: 8/10
   - Estimated Time: 2 hours
   - Break Frequency: Every 25 minutes

2. **Medium Cognitive Load Task**
   - Title: "Code Review and Documentation"
   - Priority: Focused
   - Cognitive Load: 5/10
   - Estimated Time: 1 hour
   - Break Frequency: Every 30 minutes

3. **Low Cognitive Load Task**
   - Title: "Update Project README"
   - Priority: Scattered
   - Cognitive Load: 2/10
   - Estimated Time: 30 minutes
   - Break Frequency: Every 45 minutes

### 5. Test ADHD Features

#### Attention State Testing:
- Filter tasks by cognitive load
- Test priority sorting (hyperfocus → scattered)
- Verify break reminders appear
- Check context preservation between tasks

#### Workflow Integration:
- Test task creation via API
- Verify status updates work
- Check time tracking functionality
- Test project switching

### 6. Integration Validation Commands

```bash
# Health check after setup
cd /Users/hue/code/dopemux-mvp/docker/leantime
docker-compose ps

# Test API with real token
export LEANTIME_TOKEN="your_token_here"
curl -H "Authorization: Bearer $LEANTIME_TOKEN" http://localhost:8080/api/v1/users/me

# Test MCP integration
python3 /Users/hue/code/dopemux-mvp/tests/integration/test_leantime_taskmaster_integration.py
```

## 🧠 ADHD Success Indicators

You'll know it's working when:
- ✅ Tasks filter by attention state
- ✅ Break reminders appear based on cognitive load
- ✅ Context is preserved when switching between tasks
- ✅ Visual progress indicators update smoothly
- ✅ Notifications are gentle and batched appropriately

## 🚨 If Something Goes Wrong

1. **Check logs**: `docker-compose logs leantime`
2. **Restart services**: `docker-compose restart`
3. **Reset if needed**: `docker-compose down -v && docker-compose up -d`
4. **Apply nginx fix**:
   ```bash
   docker exec -u root leantime sed -i 's/listen 8080;/listen 80;/' /etc/nginx/nginx.conf
   docker exec -u root leantime nginx -s reload
   ```

## 🎉 Next Steps After Validation

1. Connect to Dopemux session management
2. Add Leantime to MCP orchestration system
3. Implement automatic attention detection
4. Build context switching workflows
5. Create ADHD-specific reporting dashboard

---
**Ready to validate**: Once setup is complete, we'll test everything together!