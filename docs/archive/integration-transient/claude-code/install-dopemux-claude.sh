#!/bin/bash

set -e

# Dopemux-Claude Code Integration Installer
# This script configures Claude Code to use the enhanced Dopemux MCP server stack

echo "🚀 Dopemux-Claude Code Integration Installer"
echo "============================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_CONFIG_DIR="$HOME/.claude"
BACKUP_DIR="$CLAUDE_CONFIG_DIR/backup-$(date +%Y%m%d-%H%M%S)"

# Detect OS for Claude config location
detect_claude_config_location() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
        CLAUDE_CONFIG_PATH="$HOME/.claude/config.json"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        CLAUDE_DESKTOP_CONFIG="$HOME/.config/claude/claude_desktop_config.json"
        CLAUDE_CONFIG_PATH="$HOME/.claude/config.json"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        CLAUDE_DESKTOP_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
        CLAUDE_CONFIG_PATH="$HOME/.claude/config.json"
    else
        echo "❌ Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Backup existing configuration
backup_existing_config() {
    echo "📦 Creating backup of existing configuration..."

    mkdir -p "$BACKUP_DIR"

    if [ -f "$CLAUDE_CONFIG_PATH" ]; then
        cp "$CLAUDE_CONFIG_PATH" "$BACKUP_DIR/config.json.backup"
        echo "✅ Backed up Claude Code config to $BACKUP_DIR"
    fi

    if [ -f "$CLAUDE_DESKTOP_CONFIG" ]; then
        cp "$CLAUDE_DESKTOP_CONFIG" "$BACKUP_DIR/claude_desktop_config.json.backup"
        echo "✅ Backed up Claude Desktop config to $BACKUP_DIR"
    fi

    echo "📋 Backup location: $BACKUP_DIR"
}

# Validate Dopemux infrastructure
validate_dopemux_infrastructure() {
    echo "🔍 Validating Dopemux infrastructure..."

    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/metamcp_server.py" ]; then
        echo "❌ Error: MetaMCP server not found. Please run from Dopemux project root."
        exit 1
    fi

    # Check if MCP servers are running
    local servers_down=()

    # Critical servers that must be running
    local critical_servers=(
        "localhost:3002"  # context7
        "localhost:3003"  # zen
        "localhost:3005"  # task-master-ai
        "localhost:3010"  # conport-memory
    )

    for server in "${critical_servers[@]}"; do
        if ! curl -sf "http://$server/health" &>/dev/null; then
            servers_down+=("$server")
        fi
    done

    if [ ${#servers_down[@]} -gt 0 ]; then
        echo "⚠️  Warning: Some MCP servers are not responding:"
        printf '%s\n' "${servers_down[@]}"
        echo ""
        echo "🔧 To start all servers, run:"
        echo "   cd $PROJECT_ROOT && ./docker/mcp-servers/start-all-mcp-servers.sh"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ All critical MCP servers are responding"
    fi

    # Check if Docker containers are running
    if ! docker ps | grep -q "mcp-mas-sequential-thinking"; then
        echo "⚠️  Sequential thinking container not running"
        echo "   Starting container..."
        docker start mcp-mas-sequential-thinking || true
    fi
}

# Install enhanced configuration
install_enhanced_config() {
    echo "🔧 Installing enhanced Claude Code configuration..."

    # Create Claude config directory if it doesn't exist
    mkdir -p "$CLAUDE_CONFIG_DIR"

    # Copy enhanced configuration
    cp "$SCRIPT_DIR/enhanced-config.json" "$CLAUDE_CONFIG_PATH"

    # Update paths to be absolute
    sed -i.tmp "s|/Users/hue/code/dopemux-mvp|$PROJECT_ROOT|g" "$CLAUDE_CONFIG_PATH"
    rm "$CLAUDE_CONFIG_PATH.tmp" 2>/dev/null || true

    # Set appropriate permissions
    chmod 600 "$CLAUDE_CONFIG_PATH"

    echo "✅ Enhanced configuration installed to $CLAUDE_CONFIG_PATH"
}

# Setup environment integration
setup_environment_integration() {
    echo "🌍 Setting up environment integration..."

    # Create environment setup script
    cat > "$CLAUDE_CONFIG_DIR/setup-dopemux-env.sh" << 'EOF'
#!/bin/bash
# Dopemux environment setup for Claude Code

export DOPEMUX_INTEGRATION=true
export ADHD_OPTIMIZATIONS=enabled
export METAMCP_CONFIG_PATH="$PROJECT_ROOT/config/mcp"

# Source project-specific environment if available
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

echo "🧠 Dopemux environment loaded for Claude Code"
EOF

    # Replace PROJECT_ROOT placeholder
    sed -i.tmp "s|\$PROJECT_ROOT|$PROJECT_ROOT|g" "$CLAUDE_CONFIG_DIR/setup-dopemux-env.sh"
    rm "$CLAUDE_CONFIG_DIR/setup-dopemux-env.sh.tmp" 2>/dev/null || true

    chmod +x "$CLAUDE_CONFIG_DIR/setup-dopemux-env.sh"

    echo "✅ Environment integration setup complete"
}

# Install Claude Code slash commands
install_slash_commands() {
    echo "⚡ Installing Dopemux slash commands for Claude Code..."

    # Create commands directory
    mkdir -p "$CLAUDE_CONFIG_DIR/commands"

    # Install dopemux command integration
    cat > "$CLAUDE_CONFIG_DIR/commands/dopemux.js" << 'EOF'
// Dopemux integration commands for Claude Code
const { exec } = require('child_process');
const path = require('path');

const DOPEMUX_ROOT = '$PROJECT_ROOT';

const commands = {
  'dopemux-start': {
    description: 'Start Dopemux instance with enhanced MCP servers',
    handler: async (args) => {
      const instance = args[0] || 'main';
      const branch = args[1] || 'main';

      return new Promise((resolve, reject) => {
        exec(`cd ${DOPEMUX_ROOT} && dopemux start ${instance} ${branch}`,
          (error, stdout, stderr) => {
            if (error) {
              reject(`Failed to start Dopemux: ${error.message}`);
            } else {
              resolve(`✅ Dopemux instance '${instance}' started successfully\n${stdout}`);
            }
          });
      });
    }
  },

  'dopemux-status': {
    description: 'Show Dopemux status and MCP server health',
    handler: async () => {
      return new Promise((resolve, reject) => {
        exec(`cd ${DOPEMUX_ROOT} && dopemux status`,
          (error, stdout, stderr) => {
            if (error) {
              reject(`Failed to get status: ${error.message}`);
            } else {
              resolve(stdout);
            }
          });
      });
    }
  },

  'mcp-health': {
    description: 'Check health of all MCP servers',
    handler: async () => {
      const servers = [
        'localhost:3002', 'localhost:3003', 'localhost:3005',
        'localhost:3010', 'localhost:3011', 'localhost:3012'
      ];

      const results = await Promise.all(
        servers.map(async (server) => {
          try {
            const response = await fetch(`http://${server}/health`);
            return `✅ ${server} - Healthy`;
          } catch (e) {
            return `❌ ${server} - Unhealthy`;
          }
        })
      );

      return results.join('\n');
    }
  }
};

module.exports = commands;
EOF

    # Replace PROJECT_ROOT placeholder
    sed -i.tmp "s|\$PROJECT_ROOT|$PROJECT_ROOT|g" "$CLAUDE_CONFIG_DIR/commands/dopemux.js"
    rm "$CLAUDE_CONFIG_DIR/commands/dopemux.js.tmp" 2>/dev/null || true

    echo "✅ Slash commands installed"
}

# Verify installation
verify_installation() {
    echo "🔍 Verifying installation..."

    # Check if configuration file exists and is valid
    if [ ! -f "$CLAUDE_CONFIG_PATH" ]; then
        echo "❌ Configuration file not found"
        exit 1
    fi

    # Validate JSON
    if ! python3 -m json.tool "$CLAUDE_CONFIG_PATH" > /dev/null 2>&1; then
        echo "❌ Configuration file contains invalid JSON"
        exit 1
    fi

    # Check MetaMCP server accessibility
    if ! python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT/src'); from dopemux.mcp.broker import MetaMCPBroker" 2>/dev/null; then
        echo "⚠️  Warning: MetaMCP broker not accessible. Please check Python path."
    else
        echo "✅ MetaMCP broker accessible"
    fi

    echo "✅ Installation verification complete"
}

# Main installation process
main() {
    echo "Starting Dopemux-Claude Code integration..."
    echo ""

    detect_claude_config_location
    backup_existing_config
    validate_dopemux_infrastructure
    install_enhanced_config
    setup_environment_integration
    install_slash_commands
    verify_installation

    echo ""
    echo "🎉 Installation Complete!"
    echo "========================"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Restart Claude Code to load the new configuration"
    echo "2. Test the integration with: claude mcp list"
    echo "3. Try a role switch: /switch-role researcher"
    echo "4. Check server health: /mcp-health"
    echo ""
    echo "📁 Configuration Files:"
    echo "   Claude Config: $CLAUDE_CONFIG_PATH"
    echo "   Environment:   $CLAUDE_CONFIG_DIR/setup-dopemux-env.sh"
    echo "   Commands:      $CLAUDE_CONFIG_DIR/commands/dopemux.js"
    echo "   Backup:        $BACKUP_DIR"
    echo ""
    echo "🆘 Troubleshooting:"
    echo "   View logs: docker-compose logs -f metamcp"
    echo "   Restore backup: cp $BACKUP_DIR/config.json.backup $CLAUDE_CONFIG_PATH"
    echo "   Start servers: $PROJECT_ROOT/docker/mcp-servers/start-all-mcp-servers.sh"
    echo ""
    echo "🧠 ADHD optimizations are now active!"
    echo "     • 25-minute focused sessions"
    echo "     • Gentle break reminders"
    echo "     • Progressive tool disclosure"
    echo "     • Cross-session context preservation"
}

# Run installation
main "$@"