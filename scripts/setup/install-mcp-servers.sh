#!/bin/bash
# Dopemux MCP Servers Installation Script
# This script installs all supported MCP servers for optimal ADHD development support

set -e

echo "🚀 Dopemux MCP Servers Installation"
echo "=================================="
echo ""

# Function to print status messages (respects terminal theme)
print_status() {
    local level=$1
    local message=$2
    echo "$message"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status info "📋 Checking prerequisites..."

if ! command_exists node; then
    print_status error "❌ Node.js not found. Please install Node.js 16+ first."
    exit 1
fi

if ! command_exists npm; then
    print_status error "❌ npm not found. Please install npm first."
    exit 1
fi

print_status success "✅ Node.js and npm found"

# Install TypeScript compiler (required for some servers)
print_status info "📦 Installing TypeScript compiler..."
npm install -g typescript || {
    print_status warning "⚠️ TypeScript installation failed, but continuing..."
}

echo ""
print_status info "🔧 Installing MCP Servers..."
echo ""

# Array of MCP servers to install
declare -A MCP_SERVERS
MCP_SERVERS[context7]="context7-mcp"
MCP_SERVERS[claude-context]="@zilliz/claude-context-mcp@latest"
MCP_SERVERS[morphllm-fast-apply]="morphllm-fast-apply-mcp"
MCP_SERVERS[exa]="exa-mcp"
MCP_SERVERS[zen]="zen-mcp"
MCP_SERVERS[leantime]="leantime-mcp"

# Install each server
for server_name in "${!MCP_SERVERS[@]}"; do
    package_name="${MCP_SERVERS[$server_name]}"

    print_status info "📦 Installing $server_name ($package_name)..."

    if npm install -g "$package_name"; then
        print_status success "✅ $server_name installed successfully"
    else
        print_status warning "⚠️ Failed to install $server_name - may have build issues"

        # Special handling for problematic servers
        if [[ "$server_name" == "leantime" ]]; then
            print_status warning "   Note: Leantime MCP server has known TypeScript compilation issues"
            print_status warning "   It will be disabled by default in Dopemux configuration"
        fi
    fi
    echo ""
done

echo ""
print_status info "🔍 Verifying installations..."

# Check which servers are available
available_servers=()
failed_servers=()

for server_name in "${!MCP_SERVERS[@]}"; do
    package_name="${MCP_SERVERS[$server_name]}"

    # Try to find the installed package
    if npm list -g "$package_name" >/dev/null 2>&1; then
        available_servers+=("$server_name")
        print_status success "✅ $server_name is available"
    else
        failed_servers+=("$server_name")
        print_status error "❌ $server_name installation failed"
    fi
done

echo ""
print_status info "📊 Installation Summary"
print_status success "✅ Successfully installed: ${#available_servers[@]} servers"
if [[ ${#failed_servers[@]} -gt 0 ]]; then
    print_status warning "⚠️ Failed installations: ${#failed_servers[@]} servers"
    print_status warning "   Failed servers: ${failed_servers[*]}"
fi

echo ""
print_status info "🔧 Next Steps:"
echo "1. Set up required environment variables:"
echo "   export OPENAI_API_KEY='your_openai_key'"
echo "   export OPENROUTER_API_KEY='your_openrouter_key'"
echo "   export EXA_API_KEY='your_exa_key'"
echo "   export LEANTIME_URL='https://your-leantime-instance.com'"
echo "   export LEANTIME_API_KEY='your_leantime_key'"
echo ""
echo "2. Run 'dopemux start' to launch with MCP servers enabled"
echo ""

if [[ ${#failed_servers[@]} -gt 0 ]]; then
    print_status warning "⚠️ Some servers failed to install. Dopemux will work with available servers."
    print_status warning "   Check the Dopemux documentation for troubleshooting steps."
fi

print_status success "🎉 NPM MCP server installation complete!"

echo ""
print_status info "🐳 Installing Docker-based MCP servers..."

# Check if Docker installer exists and run it
DOCKER_INSTALLER="$(dirname "$0")/install-docker-mcp-servers.sh"
if [[ -f "$DOCKER_INSTALLER" ]]; then
    print_status info "📦 Running Docker MCP servers installer..."
    bash "$DOCKER_INSTALLER"
else
    print_status warning "⚠️ Docker MCP installer not found at $DOCKER_INSTALLER"
    print_status warning "   Skipping Docker-based MCP servers"
fi

echo ""
print_status success "🎉 Complete MCP server installation finished!"
print_status info "📊 Summary:"
echo "   • NPM-based servers: Available for immediate use"
echo "   • Docker-based servers: Advanced reasoning and specialized tools"
echo ""
print_status info "🔧 To manage Docker MCP servers:"
echo "   Start: docker/mcp-servers/start-all-mcp-servers.sh"
echo "   Stop:  docker/mcp-servers/stop-all-mcp-servers.sh"
echo "   Logs:  docker/mcp-servers/view-logs.sh"