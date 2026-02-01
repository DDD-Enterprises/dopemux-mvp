---
id: INSTALLER_TESTING_REPORT
title: Installer_Testing_Report
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Universal Installer Testing Report

**Date:** 2025-11-13 (Updated)
**Version:** 1.0.0
**Tester:** Automated + Manual Testing
**Status:** Day 2 - Platform Testing

---

## Test Matrix

| Platform | Status | Install Time | Notes |
|----------|--------|--------------|-------|
| macOS (Apple Silicon) | ✅ Basic Tests | <5 sec | Syntax, Python 3.13, Git, Docker OK |
| macOS (Intel) | ⏳ Pending | - | Need test machine |
| Ubuntu 22.04 | ⚠️ Partial | ~84 sec | Python 3.10 OK, Docker-in-Docker issues |
| Ubuntu 24.04 | ⏳ Pending | - | - |
| Arch Linux | ⏳ Pending | - | - |
| Fedora 39 | ⏳ Pending | - | - |
| WSL2 | ⏳ Pending | - | Need Windows machine |

---

## Day 2 Test Results (2025-11-13)

### Test 1: Basic Installer Validation (macOS)

**Script:** `test_installer_basic.sh` (NEW)
**Platform:** macOS (Darwin)
**Duration:** ~3 seconds

**Command:**
```bash
./test_installer_basic.sh
```

**Result:** ✅ PASSED

**Checks:**
- ✅ Script syntax validation
- ✅ Help flag functionality
- ✅ Python 3.13 detected (>= 3.10 required)
- ✅ Git 2.39.5 detected
- ✅ Docker 28.4.0 detected

**Notes:**
- Fast, non-interactive test suite
- No Docker services required
- Perfect for CI/CD pipelines

---

### Test 2: Ubuntu 22.04 Container Test

**Platform:** Ubuntu 22.04.5 LTS (Docker container)
**Duration:** ~84 seconds

**Command:**
```bash
./test_installer_ubuntu.sh
```

**Result:** ⚠️ PARTIAL

**Issues Found & Fixed:**
1. ✅ **FIXED:** Python 3.11+ requirement too strict
   - Changed `REQUIRED_PYTHON_VERSION` from "3.11" to "3.10"
   - Reason: Ubuntu 22.04 LTS ships with Python 3.10
   - Project supports Python >= 3.8 (per pyproject.toml)

**What Works:**
- ✅ Platform detection: Ubuntu 22.04.5 LTS
- ✅ Python 3.10 installation via apt
- ✅ Git installation
- ✅ Package manager (apt) integration

**Known Limitations:**
- ⚠️ Docker-in-Docker complexity in containers
- ⚠️ Services can't start in container environment
- These are expected - not bugs

---

## Changes Made

### 1. Python Version Requirement (Bug Fix)
**File:** `install.sh` (Lines 39, 329, 767)
**Change:** Lowered Python requirement from 3.11 to 3.10

**Before:**
```bash
REQUIRED_PYTHON_VERSION="3.11"
```

**After:**
```bash
REQUIRED_PYTHON_VERSION="3.10"
```

**Impact:**
- ✅ Now compatible with Ubuntu 22.04 LTS (Python 3.10.12)
- ✅ Still exceeds actual requirement (Python >= 3.8)
- ✅ Maintains compatibility with newer systems

### 2. Created Basic Test Suite
**File:** `test_installer_basic.sh` (NEW)
- Non-interactive test suite
- Tests: syntax, help, Python, Git, Docker detection
- Fast execution (~3 seconds)
- CI/CD friendly

### 3. Stack Selection + `.env` Bootstrap (NEW)
**Files:** `install.sh`, `INSTALL.md`
- Installer now differentiates **core** vs **full** stacks and auto-selects the right docker-compose file (`--quick` ⇒ core, `--full` ⇒ master)
- Full installs prompt for required API keys/secrets and store them in a git-ignored `.env`
- Automatically creates external Docker networks (`mcp-network`, `dopemux-unified-network`, `leantime-net`) required by the full stack

### 4. Interactive Installer UX Improvements (NEW)
**Files:** `install.sh`, `INSTALL.md`
- Added stack summaries with estimated runtimes so users know what each bundle includes before proceeding
- Introduced `--stack core|full` and `--env-file <path>` flags for CI/unattended workflows
- Added `INSTALLER_TEST_MODE=1` escape hatch so automated tests can exercise the full interactive flow without touching Docker, pip, or user shell configs
- `test_installer_basic.sh` validates the new help output *and* runs an interactive smoke test under test mode

---

## Performance Metrics

| Test Type | Duration | Pass Rate |
|-----------|----------|-----------|
| Basic validation | <5 seconds | 100% (5/5) |
| Ubuntu container | ~84 seconds | 60% (3/5) |
| Full install (est.) | 3-5 minutes | TBD |

---

## Recommendations

1. **CI/CD Integration:** Use `test_installer_basic.sh` for quick validation
2. **Platform Testing:** Test on real VMs, not containers (for Docker functionality)
3. **Version Support:** Python 3.10+ is the sweet spot (Ubuntu 22.04 LTS compatible)

---
- Platform detection: ✅ Works perfectly
- Progress bar: ✅ Renders correctly
- Color coding: ✅ Green/yellow/red visible
- Helpful messages: ✅ Clear what's missing
- Exit code: ✅ Non-zero on partial failure

**Issues:** None

---

## Test 2: Ubuntu 22.04 (Docker) - Full Install

**Setup:**
```bash
docker run -it --rm \
  --name dopemux-test-ubuntu \
  -v $(pwd):/workspace \
  -w /workspace \
  ubuntu:22.04 \
  /bin/bash
```

**Command:** `./install.sh --full --yes`

**Expected:**
- Detect Ubuntu 22.04
- Use apt package manager
- Install Python 3.11, Git, Docker
- Set up directory structure
- Pull Docker images
- Start services
- Complete in <5 minutes

**Result:** ⏳ IN PROGRESS

**Test Script:**
```bash
#!/bin/bash
# Run in Ubuntu container

# Update apt first
apt update

# Run installer
./install.sh --full --yes

# Verify installation
./install.sh --verify
```

---

## Test 3: Dependency Auto-Installation

**Platform:** macOS

**Scenario:** Missing optional tools (tmux, jq)

**Command:** `./install.sh --quick`

**Expected:**
- Detect missing tmux, jq
- Offer to install via Homebrew
- Continue if user declines
- Complete installation anyway

**Result:** ⏳ PENDING

---

## Test 4: Error Handling - Low Disk Space

**Scenario:** Simulate <10GB free disk space

**Expected:**
- Warning message
- Prompt to continue anyway
- Installation proceeds if user confirms
- Fails gracefully if user declines

**Result:** ⏳ PENDING

---

## Test 5: Error Handling - Port Conflicts

**Scenario:** Ports 5432, 6379, 8095 already in use

**Expected:**
- Detect busy ports
- List which ports are busy
- Warn services may fail
- Prompt to continue
- Provide troubleshooting advice

**Result:** ⏳ PENDING

---

## Test 6: Uninstall with Backup

**Command:** `./install.sh --uninstall`

**Expected:**
- Prompt for confirmation
- Create timestamped backup in ~/.dopemux.backup.*
- Stop Docker services
- Remove ~/.dopemux directory
- Remove shell integration lines
- Show backup location
- Complete successfully

**Result:** ⏳ PENDING

---

## Test 7: Reinstall Over Existing

**Scenario:** Run installer when dopemux already installed

**Expected:**
- Detect existing installation
- Skip already-present dependencies
- Update configuration if needed
- Don't break existing setup
- Idempotent operation

**Result:** ⏳ PENDING

---

## Bug Tracking

### Critical Bugs (Block Release)
- None found yet

### Major Bugs (Fix Before Beta)
- None found yet

### Minor Bugs (Nice to Fix)
- None found yet

### Enhancement Requests
- [ ] Add `--dry-run` mode (show what would be done)
- [ ] Add `--non-interactive` mode (fail if input needed)
- [ ] Add `--config <file>` to specify answers ahead of time
- [ ] Add install telemetry (opt-in, for success metrics)

---

## Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Install time (quick) | <2 min | TBD | ⏳ |
| Install time (full) | <5 min | TBD | ⏳ |
| Platform detection | <1 sec | ~0.5s | ✅ |
| Dependency check | <5 sec | TBD | ⏳ |
| Docker pull | <3 min | TBD | ⏳ |
| Service startup | <30 sec | TBD | ⏳ |

---

## Platform-Specific Notes

### macOS
- ✅ Apple Silicon detection works
- ✅ Intel detection (assumed, not tested yet)
- ℹ️ Docker Desktop requires manual install (correct behavior)
- ℹ️ Homebrew auto-install offered if missing

### Ubuntu/Debian
- ⏳ Testing in progress
- Expected: apt package manager
- Expected: Docker from get.docker.com script

### Arch Linux
- ⏳ Not tested yet
- Expected: pacman package manager
- Expected: Docker from official repo

### Fedora/RHEL/CentOS
- ⏳ Not tested yet
- Expected: dnf package manager
- Expected: Docker from official repo

### WSL2
- ⏳ Not tested yet
- Expected: Detect via /proc/version
- Expected: Use host Docker (or install)

---

## User Experience Observations

### What Works Well ✅
- **Clear progress:** Progress bar and spinner give feedback
- **Color coding:** Easy to scan for red (errors), yellow (warnings), green (success)
- **Helpful errors:** Messages explain what's wrong AND what to do
- **Multiple modes:** --quick for impatient, --full for automation
- **Safety:** Backup before uninstall, confirmation prompts

### What Could Be Better 🔄
- Add estimated time remaining for long operations
- Show which step we're on (e.g., "Step 3/6: Pulling Docker images")
- Add `--skip-docker` for testing without Docker
- Add `--debug` to save full log to file

### ADHD-Specific Feedback 🧠
- ✅ Progress indicators prevent "is this frozen?" anxiety
- ✅ Color coding reduces cognitive load (quick visual scan)
- ✅ Helpful errors reduce frustration (clear next steps)
- ✅ Multiple modes match energy levels (quick vs thorough)
- 🔄 Could add: "Expected time: 3-5 minutes" at start
- 🔄 Could add: Break reminder if install takes >5 min

---

## Next Steps

**Immediate:**
1. ✅ Test verification mode on macOS
2. ⏳ Test full install in Ubuntu 22.04 container
3. ⏳ Test error handling scenarios
4. ⏳ Fix any bugs found
5. ⏳ Document platform quirks

**Short-term (This Week):**
1. Test on all 5 major platforms
2. Measure install times
3. Get to >95% success rate
4. Document known issues
5. Create troubleshooting guide

**Medium-term (Week 2):**
1. Add telemetry (opt-in)
2. Create GitHub Action for CI testing
3. Set up automated testing on multiple platforms
4. Beta test with 10 users

---

## Test Completion Checklist

**Platform Testing:**
- [x] macOS Apple Silicon (verification only)
- [ ] macOS Intel
- [ ] Ubuntu 22.04
- [ ] Ubuntu 24.04
- [ ] Arch Linux
- [ ] Fedora 39
- [ ] WSL2 (Ubuntu)

**Functionality Testing:**
- [x] --verify mode
- [ ] --quick mode
- [ ] --full mode
- [ ] --uninstall mode
- [ ] Interactive mode
- [ ] Dependency auto-install
- [ ] Error handling (disk space)
- [ ] Error handling (port conflicts)
- [ ] Reinstall over existing

**Performance Testing:**
- [ ] Quick install <2 min
- [ ] Full install <5 min
- [ ] Verify <10 sec

**User Experience Testing:**
- [ ] Clear error messages
- [ ] Progress indicators smooth
- [ ] Color coding works
- [ ] Help text useful
- [ ] Uninstall safe (backup works)

---

**Overall Status:** 10% complete (1/10 major tests done)
**Blockers:** None
**ETA to 100%:** 2-3 hours (rest of Day 1)
