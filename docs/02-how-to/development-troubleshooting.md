---
id: DEV_TROUBLESHOOTING
title: Development Troubleshooting
type: how-to
owner: '@hu3mann'
date: '2026-02-02'
tags:
- troubleshooting
- development
- debugging
- dev-mode
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Development Troubleshooting Guide

**Goal**: Solve common development issues quickly
**Audience**: Contributors experiencing setup or development problems
**Format**: Problem → Diagnosis → Solution

---

## 🔍 Quick Diagnostics

**First steps for any issue:**

```bash
# 1. Check dev mode status
dopemux dev status

# 2. Check component paths
dopemux dev paths

# 3. Check system health
dopemux health --verbose

# 4. View recent logs
tail -50 ~/.dopemux/logs/dopemux.log
```

---

## 🚫 Dev Mode Not Detected

### Symptom

```bash
$ dopemux dev status
❌ Dev Mode: Inactive
```

### Diagnosis

Dev mode is not activating automatically.

### Solutions

#### Solution 1: Enable Explicitly

```bash
export DOPEMUX_DEV_MODE=true
dopemux dev status
# Should now show: "✅ ACTIVE"
```

#### Solution 2: Clone to Standard Location

```bash
# Ensure you're in the right place
pwd
# Should be: ~/code/dopemux-mvp

# If not, move it
mv /current/path/dopemux-mvp ~/code/dopemux-mvp
cd ~/code/dopemux-mvp

# Verify detection
dopemux dev status
```

#### Solution 3: Custom Path Override

```bash
# If using non-standard location
export DOPEMUX_DEV_MODE=true
export ZEN_DEV_PATH=/custom/path/zen-mcp-server

# Verify
dopemux dev paths
```

#### Solution 4: Verify Repository Structure

```bash
# Dev mode checks for these files
ls pyproject.toml        # Should exist
ls src/dopemux/          # Should exist

# If missing, you might be in wrong directory
```

---

## 🔄 Changes Not Taking Effect

### Symptom

You edit code but changes don't appear when you run commands.

### Diagnosis

Code not loaded from editable install.

### Solutions

#### Solution 1: Verify Editable Install

```bash
pip show dopemux
# Look for: Location: /path/to/dopemux-mvp/src
# If shows site-packages, not editable!

# Reinstall in editable mode
pip uninstall dopemux
cd ~/code/dopemux-mvp
pip install -e ".[dev]"
```

#### Solution 2: Restart Services

```bash
# Restart Dopemux
dopemux restart

# Or restart specific service
docker-compose restart zen
```

#### Solution 3: Clear Python Cache

```bash
# Remove cached .pyc files
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reinstall
pip install -e ".[dev]"
```

#### Solution 4: Check Which Code is Running

```bash
# Find Dopemux installation
python -c "import dopemux; print(dopemux.__file__)"
# Should point to ~/code/dopemux-mvp/src/dopemux/

# Not there? Wrong installation active
```

---

## 💾 Test Database Issues

### Symptom

Production data appearing in dev mode, or test data missing.

### Diagnosis

Dev mode not using test databases correctly.

### Solutions

#### Solution 1: Verify Test Database Setting

```bash
dopemux dev status
# Should show: "Test Databases: ✅"

# If not:
export DOPEMUX_USE_TEST_DB=true
dopemux dev status
```

#### Solution 2: Check Database Path

```bash
# Production database
ls ~/.dopemux/databases/conport.db

# Test database (should be used in dev)
ls ~/.dopemux/dev/databases/conport-test.db

# If test DB doesn't exist, create it
mkdir -p ~/.dopemux/dev/databases
# Will be auto-created on first use
```

#### Solution 3: Force Test Database Mode

```bash
# Explicit override
export DOPEMUX_USE_TEST_DB=true
export DOPEMUX_DEV_MODE=true

# Restart
dopemux restart

# Verify
dopemux dev status
```

#### Solution 4: Reset Test Database

```bash
# Backup if needed
cp ~/.dopemux/dev/databases/conport-test.db ~/backup.db

# Delete and recreate
rm ~/.dopemux/dev/databases/conport-test.db
dopemux restart
# Fresh test database created
```

---

## 📝 Excessive Debug Logging

### Symptom

Terminal flooded with DEBUG logs, hard to see important info.

### Diagnosis

Dev mode automatically enables DEBUG logging.

### Solutions

#### Solution 1: Filter Logs

```bash
# Filter out DEBUG lines
dopemux start 2>&1 | grep -v "DEBUG"

# Show only errors and warnings
dopemux start 2>&1 | grep -E "ERROR|WARNING"
```

#### Solution 2: Temporarily Reduce Log Level

```bash
# Use INFO level
export LOG_LEVEL=INFO
dopemux start

# Restore DEBUG when debugging
export LOG_LEVEL=DEBUG
```

#### Solution 3: Log to File

```bash
# Redirect logs to file
dopemux start 2>&1 | tee ~/dopemux-dev.log

# Monitor in separate terminal
tail -f ~/dopemux-dev.log | grep -v "DEBUG"
```

---

## 🔌 Component Path Issues

### Symptom

```bash
$ dopemux dev paths
No development components detected
```

### Diagnosis

Components not in expected locations.

### Solutions

#### Solution 1: Clone to Standard Locations

```bash
# For Zen MCP (when extracted)
git clone ... ~/code/zen-mcp-server

# For ConPort
git clone ... ~/code/conport-mcp

# For Serena
git clone ... ~/code/serena-lsp

# Verify detection
dopemux dev paths
```

#### Solution 2: Use Environment Variables

```bash
# Point to custom locations
export ZEN_DEV_PATH=/custom/path/zen
export CONPORT_DEV_PATH=/custom/path/conport
export SERENA_DEV_PATH=/custom/path/serena

# Verify
dopemux dev paths
```

#### Solution 3: Verify Directory Structure

```bash
# Check Zen structure
ls ~/code/zen-mcp-server/server.py
# Should exist for Zen to be detected

# Check Dopemux structure
ls ~/code/dopemux-mvp/pyproject.toml
ls ~/code/dopemux-mvp/src/dopemux/
# Both should exist
```

---

## ⚙️ Service Skipping Problems

### Symptom

Services you need aren't starting, or services you want to skip are running.

### Diagnosis

`DOPEMUX_SKIP_SERVICES` misconfigured.

### Solutions

#### Solution 1: Check Current Setting

```bash
echo $DOPEMUX_SKIP_SERVICES
# Shows: leantime,milvus,task-master

dopemux dev status
# Shows: "Skipped Services: ..."
```

#### Solution 2: Correct Format

```bash
# Wrong: spaces after commas
export DOPEMUX_SKIP_SERVICES="leantime, milvus, task-master"

# Right: no spaces
export DOPEMUX_SKIP_SERVICES="leantime,milvus,task-master"
```

#### Solution 3: Start All Services

```bash
# Temporarily disable skipping
unset DOPEMUX_SKIP_SERVICES
dopemux start

# All services now run
```

#### Solution 4: Custom Service Selection

```bash
# Skip only what you don't need
export DOPEMUX_SKIP_SERVICES="leantime,milvus"
dopemux start
# Zen, ConPort, Serena, Task-Master will run
```

---

## 🔒 Permission Errors

### Symptom

```bash
Permission denied: /path/to/file
```

### Diagnosis

File/directory permission issues.

### Solutions

#### Solution 1: Fix Ownership

```bash
# Fix Dopemux directory ownership
sudo chown -R $USER:$USER ~/code/dopemux-mvp

# Fix config directory
sudo chown -R $USER:$USER ~/.dopemux
```

#### Solution 2: Fix Permissions

```bash
# Make scripts executable
chmod +x ~/code/dopemux-mvp/scripts/*.sh

# Fix directory permissions
chmod 755 ~/.dopemux
chmod 755 ~/.dopemux/dev
chmod 755 ~/.dopemux/dev/databases
```

#### Solution 3: Docker Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker ps
# Should work without sudo
```

---

## 🐛 Import Errors

### Symptom

```python
ModuleNotFoundError: No module named 'dopemux'
```

### Diagnosis

Package not installed or Python path issues.

### Solutions

#### Solution 1: Reinstall in Editable Mode

```bash
cd ~/code/dopemux-mvp
pip uninstall dopemux
pip install -e ".[dev]"

# Verify
python -c "import dopemux; print(dopemux.__file__)"
```

#### Solution 2: Check Virtual Environment

```bash
# Check if venv active
which python
# Should be in venv path if using venv

# Activate if needed
source venv/bin/activate
pip install -e ".[dev]"
```

#### Solution 3: Check Python Path

```bash
# See Python search paths
python -c "import sys; print('\n'.join(sys.path))"

# Should include: /path/to/dopemux-mvp/src
```

---

## 📦 Dependency Conflicts

### Symptom

```bash
ERROR: pip's dependency resolver does not currently take into account...
```

### Diagnosis

Package version conflicts.

### Solutions

#### Solution 1: Fresh Virtual Environment

```bash
# Create new venv
python3 -m venv venv-fresh
source venv-fresh/bin/activate

# Install from scratch
cd ~/code/dopemux-mvp
pip install -e ".[dev]"
```

#### Solution 2: Update Dependencies

```bash
# Update all dependencies
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]" --upgrade
```

#### Solution 3: Check Requirements

```bash
# View all requirements
cat requirements.txt
cat requirements-dev.txt

# Install specific versions
pip install package==version
```

---

## 🔥 Docker Issues

### Symptom

Docker containers not starting or crashing.

### Diagnosis

Docker configuration or resource issues.

### Solutions

#### Solution 1: Check Docker Running

```bash
# Verify Docker running
docker ps
# Should show list of containers

# Start Docker if not running
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker
```

#### Solution 2: Clean Docker State

```bash
# Stop all containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild
docker-compose up -d --build
```

#### Solution 3: Check Docker Resources

```bash
# View resource usage
docker stats

# Increase Docker memory (Docker Desktop):
# Settings → Resources → Memory → 8GB+
```

#### Solution 4: View Container Logs

```bash
# Check specific container
docker logs mcp-zen

# Follow logs
docker logs -f mcp-conport
```

---

## 🧪 Test Failures

### Symptom

Tests failing unexpectedly.

### Diagnosis

Test environment issues or code changes broke tests.

### Solutions

#### Solution 1: Run Tests Verbosely

```bash
# See detailed test output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Show locals on failure
pytest tests/ -l
```

#### Solution 2: Run Specific Test

```bash
# Debug single test
pytest tests/test_decisions.py::test_log_decision -v

# Run only failed tests
pytest --lf
```

#### Solution 3: Update Test Data

```bash
# Tests may expect specific test data
# Check test fixtures
cat tests/fixtures/sample_data.json

# Regenerate if needed
python tests/generate_fixtures.py
```

#### Solution 4: Check Test Environment

```bash
# Ensure test mode
export DOPEMUX_DEV_MODE=true
export DOPEMUX_USE_TEST_DB=true

# Run tests
pytest tests/ -v
```

---

## 🌐 MCP Server Connection Issues

### Symptom

Claude Code can't connect to MCP server.

### Diagnosis

MCP server not running or configuration incorrect.

### Solutions

#### Solution 1: Verify MCP Server Running

```bash
# Check Docker containers
docker ps | grep mcp

# Should see: mcp-zen, mcp-conport, mcp-serena, etc.

# Start if not running
docker-compose up -d
```

#### Solution 2: Check MCP Configuration

```bash
# View Claude Code config
cat ~/.claude/config.json

# Verify MCP server paths
# Should point to correct Docker containers or stdio paths
```

#### Solution 3: Test MCP Connection

```bash
# Test Zen MCP
echo '{"jsonrpc":"2.0","method":"ping","id":1}' | docker exec -i mcp-zen python server.py

# Should respond with pong
```

#### Solution 4: Restart MCP Servers

```bash
# Restart all MCP servers
docker-compose restart

# Or specific server
docker-compose restart zen
```

---

## 💡 Common Mistakes

### Mistake 1: Forgetting Editable Install

**Problem**: Changes don't take effect
**Solution**: Always use `pip install -e ".[dev]"` for development

### Mistake 2: Wrong Directory

**Problem**: Dev mode not detected
**Solution**: Must be in `~/code/dopemux-mvp` or set env vars

### Mistake 3: Not Restarting After Changes

**Problem**: Old code still running
**Solution**: `dopemux restart` after significant changes

### Mistake 4: Production DB in Dev Mode

**Problem**: Test data in production
**Solution**: Verify `dopemux dev status` shows test databases

### Mistake 5: Skipping Service Needed

**Problem**: Feature not working
**Solution**: Check `DOPEMUX_SKIP_SERVICES` doesn't skip required service

---

## 🆘 Getting More Help

### Before Asking for Help

1. **Check status**: `dopemux dev status`
2. **View logs**: `dopemux health --verbose`
3. **Search docs**: Check [Development Setup](./DEVELOPMENT_SETUP.md)
4. **Check GitHub**: Search existing issues

### When Asking for Help

Include:

```bash
# System info
uname -a
python --version
docker --version

# Dev mode status
dopemux dev status

# Recent logs
tail -50 ~/.dopemux/logs/dopemux.log

# Error message (full text)
```

### Where to Get Help

- **GitHub Issues**: For bugs and problems
- **GitHub Discussions**: For questions and ideas
- **Pull Requests**: For code review

---

## 🔧 Debug Mode

Enable maximum debugging:

```bash
# Full debug mode
export DOPEMUX_DEV_MODE=true
export LOG_LEVEL=DEBUG
export PYTHONVERBOSE=1

# Start with verbose output
dopemux start --verbose 2>&1 | tee debug.log

# Analyze debug.log for issues
```

---

## 📋 Troubleshooting Checklist

Use this checklist for systematic debugging:

- [ ] `dopemux dev status` shows dev mode active
- [ ] Editable install: `pip show dopemux` points to src/
- [ ] Components detected: `dopemux dev paths` shows paths
- [ ] Test databases enabled: `dopemux dev status` confirms
- [ ] Docker running: `docker ps` shows containers
- [ ] Logs accessible: `~/.dopemux/logs/dopemux.log` exists
- [ ] Changes saved: `git status` shows modifications
- [ ] Service restarted: `dopemux restart` completed
- [ ] No permission errors: Files owned by current user
- [ ] Dependencies installed: `pip list` shows required packages

---

**Still Stuck?**

Open a GitHub Issue with:
- Problem description
- Steps to reproduce
- Output from checklist above
- Error logs

We're here to help! 🚀
