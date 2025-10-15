#!/usr/bin/env bash
# install_dopemux_claude_router.sh
# One-shot installer for Dopemux + Claude-flow (Claude Code router) + bridge
# Supports macOS (brew) and Debian/Ubuntu (apt). Safe & idempotent.
set -euo pipefail

echo "==> Dopemux / Claude Code Router Installer"
echo "    This will install: node/npm, claude-flow@alpha, a Node bridge deps,"
echo "    and a minimal MCP config for claude-context. It won't sudo without asking."

# --- helpers ------------------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }
confirm() {
  local prompt="${1:-Proceed?} [y/N] "
  read -r -p "$prompt" ans || true
  case "$ans" in [yY][eE][sS]|[yY]) return 0 ;; *) return 1 ;; esac
}
ensure_dir() { mkdir -p "$1"; }

# --- detect OS ----------------------------------------------------------------
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
elif [[ -f "/etc/os-release" ]]; then
  . /etc/os-release
  case "${ID,,}" in
    ubuntu|debian) OS="debian" ;;
    *) OS="${ID,,}" ;;
  esac
fi
echo "==> Detected OS: $OS"

# --- prerequisites ------------------------------------------------------------
install_homebrew() {
  echo "Homebrew is required on macOS."
  if confirm "Install Homebrew now?"; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv || true)"
  else
    echo "Please install Homebrew and re-run this script."; exit 1
  fi
}

install_node() {
  if have node && have npm; then
    echo "✔ Node present: $(node -v); npm: $(npm -v)"
    return
  fi
  echo "Node.js not found."
  if [[ "$OS" == "macos" ]]; then
    have brew || install_homebrew
    brew install node
  elif [[ "$OS" == "debian" ]]; then
    if confirm "Install Node.js LTS via NodeSource? (uses sudo)"; then
      curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
      sudo apt-get install -y nodejs build-essential
    else
      echo "Please install Node.js and re-run."; exit 1
    fi
  else
    echo "Please install Node.js (>=18) and re-run."; exit 1
  fi
}

install_python_tools() {
  if have python3; then echo "✔ Python: $(python3 -V)"; else
    if [[ "$OS" == "macos" ]]; then have brew || install_homebrew; brew install python; 
    elif [[ "$OS" == "debian" ]]; then sudo apt-get update && sudo apt-get install -y python3 python3-pip; 
    else echo "Please install Python 3 and re-run."; exit 1; fi
  fi
  if have pipx; then echo "✔ pipx: $(pipx --version)"; else
    python3 -m pip install --user -U pipx || python3 -m pip install -U pipx
    python3 -m pipx ensurepath || true
  fi
}

install_tmux() {
  if have tmux; then echo "✔ tmux: $(tmux -V)"; else
    if [[ "$OS" == "macos" ]]; then have brew || install_homebrew; brew install tmux;
    elif [[ "$OS" == "debian" ]] ; then sudo apt-get update && sudo apt-get install -y tmux;
    else echo "Please install tmux and re-run."; exit 1; fi
  fi
}

# --- STEP 1: prerequisites ----------------------------------------------------
install_node
install_python_tools
install_tmux

# --- STEP 2: install claude-flow (router/orchestrator) ------------------------
echo "==> Installing claude-flow@alpha globally (npm)..."
npm list -g claude-flow@alpha >/dev/null 2>&1 || npm install -g claude-flow@alpha

echo "==> Initializing claude-flow (with memory + MCP)..."
# init is idempotent; will skip if already configured
npx claude-flow@alpha init --with-memory --with-mcp || true

echo "==> Checking agents..."
npx claude-flow@alpha list-agents || true

# --- STEP 3: dopemux directories & tmux layout --------------------------------
DMUX_DIR="${HOME}/.dopemux"
ensure_dir "${DMUX_DIR}/"{config,memory,sessions,mcp-tools,bridge}
echo "✔ Created dopemux dirs under ${DMUX_DIR}"

# Create a minimal tmux layout helper (optional)
TMUX_LAYOUT="${DMUX_DIR}/tmux-layout.sh"
cat > "${TMUX_LAYOUT}" <<'EOF'
#!/usr/bin/env bash
session="dopemux"
tmux has-session -t "$session" 2>/dev/null && { echo "Session exists."; exit 0; }
tmux new-session -d -s "$session" -n orchestration
tmux split-window -v
tmux send-keys -t "${session}:0.0" 'claude-flow start --master --memory ~/.dopemux/memory/claude-flow.db' C-m
tmux send-keys -t "${session}:0.1" 'claude-flow monitor' C-m
tmux new-window -t "$session" -n execution
tmux split-window -v
tmux new-window -t "$session" -n memory
tmux split-window -v
tmux new-window -t "$session" -n project
tmux split-window -v
echo "Dopemux tmux session created. Attach with: tmux attach -t ${session}"
EOF
chmod +x "${TMUX_LAYOUT}"

# --- STEP 4: minimal MCP config (claude-context for semantic search) ----------
MCP_CFG="${DMUX_DIR}/mcp_config.json"
if [[ ! -f "${MCP_CFG}" ]]; then
  cat > "${MCP_CFG}" <<'EOF'
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "capabilities": {
        "description": "Semantic code search using embeddings",
        "features": {
          "semantic_search": "Search code by meaning",
          "embedding_index": "Chroma-backed index",
          "codebase_navigation": "Find implementations and usages"
        }
      }
    }
  }
}
EOF
  echo "✔ Wrote MCP config: ${MCP_CFG}"
else
  echo "ℹ MCP config exists at ${MCP_CFG} (left untouched)"
fi

# --- STEP 5: Node bridge deps for routing multiple Claude Code sessions -------
BRIDGE_DIR="${DMUX_DIR}/bridge"
pushd "${BRIDGE_DIR}" >/dev/null
echo "==> Installing Node bridge dependencies..."
# Create a minimal package.json if missing
if [[ ! -f package.json ]]; then
  cat > package.json <<'EOF'
{
  "name": "dopemux-bridge",
  "private": true,
  "type": "module",
  "version": "0.1.0",
  "dependencies": {
    "teen_process": "^2.3.2",
    "node-ipc": "^10.1.0",
    "stream-json": "^1.8.0",
    "bull": "^4.12.0",
    "better-sqlite3": "^8.7.0"
  }
}
EOF
fi
npm install
popd >/dev/null

# --- STEP 6: sanity tips ------------------------------------------------------
cat <<'NOTE'

==> Install complete.

Quick start:
  1) Launch the tmux layout:
       ~/.dopemux/tmux-layout.sh
     then attach:
       tmux attach -t dopemux

  2) Run a Claude-flow workflow (example):
       npx claude-flow@alpha sparc "hello world function"
       npx claude-flow@alpha hive-mind spawn "research Python async patterns" --agents 3

  3) (Optional) Add more MCP servers by editing:
       ~/.dopemux/mcp_config.json

Troubleshooting:
  - If npx can't find claude-flow, ensure Node is in PATH (e.g., eval \"$(/opt/homebrew/bin/brew shellenv)\" on macOS).
  - If 'better-sqlite3' fails to build on Linux, ensure build tools are installed (apt: build-essential).

NOTE
