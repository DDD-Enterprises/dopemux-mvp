#!/bin/bash

# vibe_tool_lockdown.sh - Create minimal allowlists for Vibe agents
# Input: .taskx/proof/vibe_tools.txt
# Output: Updated ~/.vibe/agents/tp-dev.toml and ~/.vibe/agents/indexing.toml

set -e

# Check if tool registry exists
if [ ! -f ".taskx/proof/vibe_tools.txt" ]; then
    echo "ERROR: Tool registry not found at .taskx/proof/vibe_tools.txt"
    echo "Run scripts/vibe_tool_dump.sh first"
    exit 1
fi

# Read the tool registry
TOOL_REGISTRY=".taskx/proof/vibe_tools.txt"

# Check for required tool patterns
MISSING_TOOLS=()

# Check for Dope-Context tools
if ! grep -q "dope_context_search_code\|dope_context_docs_search\|dope_context_search_all\|dope_context_get_index_status" "$TOOL_REGISTRY"; then
    MISSING_TOOLS+=("dope_context_* tools")
fi

# Check for Serena navigation tools
if ! grep -q "serena_find_symbol\|serena_goto_definition\|serena_find_references" "$TOOL_REGISTRY"; then
    MISSING_TOOLS+=("serena_navigation tools")
fi

# Check for ConPort ledger tools
if ! grep -q "conport_get_product_context\|conport_log_decision\|conport_log_progress" "$TOOL_REGISTRY"; then
    MISSING_TOOLS+=("conport_ledger tools")
fi

# Check for PAL/Zen reasoning tools
if ! grep -q "pal_planner\|pal_debug\|pal_version\|zen_planner\|zen_debug\|zen_version" "$TOOL_REGISTRY"; then
    MISSING_TOOLS+=("pal/zen_reasoning tools")
fi

# If any required tools are missing, fail
if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "ERROR: Required tools missing from registry:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "  - $tool"
    done
    exit 1
fi

# Create backups with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
cp ~/.vibe/agents/tp-dev.toml ~/.vibe/agents/tp-dev.toml.bak.$TIMESTAMP
cp ~/.vibe/agents/indexing.toml ~/.vibe/agents/indexing.toml.bak.$TIMESTAMP

echo "Created backups:"
echo "  ~/.vibe/agents/tp-dev.toml.bak.$TIMESTAMP"
echo "  ~/.vibe/agents/indexing.toml.bak.$TIMESTAMP"

# Build tp-dev allowlist
TP_DEV_TOOLS=(
    # Local tools
    "bash" "read_file" "write_file" "search_replace" "grep" "todo" "ask_user_question"
    
    # Dope-Context: search + status only
    "dope_context_search_all" "dope_context_search_code" "dope_context_docs_search" "dope_context_get_index_status"
    
    # Serena: navigation only
    "serena_find_symbol" "serena_goto_definition" "serena_find_references" "serena_read_file" "serena_list_dir" "serena_find_test_file" "serena_find_similar_code"
    
    # ConPort: project memory ledger only
    "conport_get_product_context" "conport_update_product_context" "conport_log_decision" "conport_get_decisions" "conport_search_decisions_fts" "conport_log_progress" "conport_get_progress" "conport_update_progress" "conport_get_recent_activity_summary"
    
    # PAL/Zen: thinking modes only
    "pal_planner" "pal_debug" "pal_codereview" "pal_challenge" "pal_consensus" "pal_version"
)

# Build indexing allowlist
INDEXING_TOOLS=(
    # Local tools
    "bash" "grep"
    
    # Dope-Context only
    "dope_context_index_workspace" "dope_context_index_docs" "dope_context_get_index_status" "dope_context_clear_index"
)

# Generate tp-dev.toml
echo "Generating ~/.vibe/agents/tp-dev.toml..."
cat > ~/.vibe/agents/tp-dev.toml << 'EOF'
active_model = "devstral-2"

enabled_tools = [
EOF

# Add tp-dev tools
for tool in "${TP_DEV_TOOLS[@]}"; do
    echo "  \"$tool\"," >> ~/.vibe/agents/tp-dev.toml
done

# Close the array
echo "]
" >> ~/.vibe/agents/tp-dev.toml

# Generate indexing.toml
echo "Generating ~/.vibe/agents/indexing.toml..."
cat > ~/.vibe/agents/indexing.toml << 'EOF'
active_model = "devstral-2"

enabled_tools = [
EOF

# Add indexing tools
for tool in "${INDEXING_TOOLS[@]}"; do
    echo "  \"$tool\"," >> ~/.vibe/agents/indexing.toml
done

# Close the array
echo "]
" >> ~/.vibe/agents/indexing.toml

echo "Lockdown complete!"
echo "Updated files:"
echo "  ~/.vibe/agents/tp-dev.toml (${#TP_DEV_TOOLS[@]} tools)"
echo "  ~/.vibe/agents/indexing.toml (${#INDEXING_TOOLS[@]} tools)"
