#!/bin/bash
#
# Basic installer tests (platform detection, Python checks, dependencies)
# Does NOT require Docker - tests core functionality only
#

set -e

strip_ansi_tail() {
    perl -pe 's/\e\[[0-9;]*[A-Za-z]//g' "$1" | tail -n 40
}

run_install_smoke() {
    local label="$1"
    local stack="$2"
    local auto="$3"
    local stdin_input="${4:-y}"
    
    local tmp_root
    tmp_root=$(mktemp -d)
    local home_dir="$tmp_root/home"
    mkdir -p "$home_dir"
    local env_file="$tmp_root/.env"
    local log_file="$tmp_root/install.log"

    if [ "$stack" = "full" ]; then
        cat > "$env_file" <<'EOF'
AGE_PASSWORD=test_age_password
ANTHROPIC_API_KEY=test_anthropic_key
OPENAI_API_KEY=test_openai_key
OPENROUTER_API_KEY=test_openrouter_key
GEMINI_API_KEY=test_gemini_key
XAI_API_KEY=test_xai_key
LEANTIME_URL=http://localhost:8097
LEANTIME_TOKEN=test_leantime_token
TASK_ORCHESTRATOR_API_KEY=test_task_key
ADHD_ENGINE_API_KEY=test_adhd_key
LITELLM_DATABASE_URL=postgresql://dopemux_age:test_age_password@localhost:5432/litellm
EOF
    fi
    
    local cmd=(./install.sh --stack "$stack" --env-file "$env_file")
    if [ "$auto" = "yes" ]; then
        cmd+=(--yes)
        if INSTALLER_TEST_MODE=1 HOME="$home_dir" DOPEMUX_HOME="$home_dir/.dopemux" "${cmd[@]}" >"$log_file" 2>&1; then
            echo "✅ $label"
        else
            echo "❌ $label"
            strip_ansi_tail "$log_file"
            rm -rf "$tmp_root"
            exit 1
        fi
    else
        if INSTALLER_TEST_MODE=1 HOME="$home_dir" DOPEMUX_HOME="$home_dir/.dopemux" "${cmd[@]}" >"$log_file" 2>&1 <<<"$stdin_input"; then
            echo "✅ $label"
        else
            echo "❌ $label"
            strip_ansi_tail "$log_file"
            rm -rf "$tmp_root"
            exit 1
        fi
    fi
    
    rm -rf "$tmp_root"
}

echo "🧪 Running basic installer tests..."
echo ""

# Test 1: Script Syntax Check
echo "Test 1: Script Syntax Check"
echo "==========================="
if bash -n install.sh; then
    echo "✅ install.sh syntax valid"
else
    echo "❌ install.sh has syntax errors"
    exit 1
fi
echo ""

# Test 2: Help Output
echo "Test 2: Help Output"
echo "==================="
if ./install.sh --help >/dev/null 2>&1; then
    echo "✅ Help flag works"
else
    echo "❌ Help flag failed"
fi
echo ""

# Test 3: Python Check
echo "Test 3: Python Version"
echo "======================"
if python3 --version; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✅ Python found: $PY_VERSION"
    
    MIN_VERSION="3.10"
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        echo "✅ Python version >= $MIN_VERSION"
    else
        echo "⚠️  Python < $MIN_VERSION (installer requires 3.10+)"
    fi
else
    echo "❌ Python not found"
fi
echo ""

# Test 4: Git Check
echo "Test 4: Git Check"
echo "================="
if command -v git >/dev/null 2>&1; then
    GIT_VERSION=$(git --version)
    echo "✅ Git found: $GIT_VERSION"
else
    echo "❌ Git not found"
fi
echo ""

# Test 5: Docker Check (optional)
echo "Test 5: Docker Check"
echo "===================="
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version 2>/dev/null || echo "found but not running")
    echo "✅ Docker found: $DOCKER_VERSION"
else
    echo "⚠️  Docker not found (optional for testing)"
fi
echo ""

# Test 6: Installer Smoke (Core stack, auto-confirm, test mode)
echo "Test 6: Installer Smoke (Core stack, auto-confirm, test mode)"
echo "============================================================"
run_install_smoke "Core stack smoke test" "core" "yes"
echo ""

# Test 7: Installer Smoke (Full stack, interactive, test mode)
echo "Test 7: Installer Smoke (Full stack, interactive, test mode)"
echo "==========================================================="
run_install_smoke "Full stack interactive smoke test" "full" "no" "y"
echo ""

echo "📊 Test Summary"
echo "==============="
echo "Basic tests complete! ✅"
echo ""
echo "Note: Full installation tests require:"
echo "  - Docker (for service deployment)"
echo "  - Platform-specific package managers"
echo "  - Root/sudo access (for system packages)"
