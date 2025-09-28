#!/bin/bash

# Claude Code Platform Evolution Configuration Wizard
# Interactive setup for optimal distributed multi-agent development

set -e

PLATFORM_DIR="${HOME}/.claude-platform"
CONFIG_FILE="${PLATFORM_DIR}/config/platform.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_banner() {
    echo -e "${CYAN}"
    cat << 'BANNER'
   ______ _                 _        ______ _         _    __                    
  / _____ | |               | |      (_____ | |       | |  / _|                   
 | /     | | ___  _   _  ___| | ___   _____) | | ___   | |_| |_ ___  ____ ____    
 | |     | |/ _ \| | | |/ _ \ |/ _ \ |  ____/| |/ _ \  |  _|  _/ _ \|  __/  _  \   
 | \___  | | |_| | |_| | |_| | |  | || |     | | |_| | | | | || |_| | | | | | |   
  \____| |_|\___/ \____|_|\___| |\___/|_|     |_|\___/  |_| |_| \___/|_|  |_| |_|   
                               |_|                                                 
         Platform Evolution Configuration Wizard
BANNER
    echo -e "${NC}"
    echo -e "${PURPLE}Universal distributed multi-agent enhancement for Claude Code${NC}"
    echo ""
}

check_installation() {
    if [ ! -d "$PLATFORM_DIR" ]; then
        log_error "Platform Evolution not installed"
        echo "Please run './install.sh' first"
        exit 1
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found at $CONFIG_FILE"
        exit 1
    fi
    
    log_success "Installation found at $PLATFORM_DIR"
}

prompt_user() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [ -n "$default" ]; then
        echo -ne "${YELLOW}${prompt} [${default}]: ${NC}"
    else
        echo -ne "${YELLOW}${prompt}: ${NC}"
    fi
    
    read response
    echo "${response:-$default}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    local response
    
    while true; do
        if [ "$default" = "y" ]; then
            echo -ne "${YELLOW}${prompt} [Y/n]: ${NC}"
        else
            echo -ne "${YELLOW}${prompt} [y/N]: ${NC}"
        fi
        
        read response
        response="${response:-$default}"
        
        case "$response" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo]) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    local choice
    
    echo -e "${YELLOW}${prompt}${NC}"
    for i in "${!options[@]}"; do
        echo "  $((i+1)). ${options[i]}"
    done
    
    while true; do
        echo -ne "${YELLOW}Select option (1-${#options[@]}): ${NC}"
        read choice
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
            echo "${options[$((choice-1))]}"
            return
        else
            echo "Invalid selection. Please choose 1-${#options[@]}."
        fi
    done
}

configure_token_budgets() {
    echo ""
    log_info "📊 Configuring Token Budgets"
    echo "Current total budget: 70,000 tokens distributed across 4 clusters"
    echo ""
    
    local research_budget
    local implementation_budget
    local quality_budget
    local coordination_budget
    
    if prompt_yes_no "Would you like to customize token budgets?" "n"; then
        echo ""
        echo "Recommended budgets based on workload type:"
        echo "  Research-Heavy: Research(30k), Implementation(25k), Quality(10k), Coordination(5k)"
        echo "  Implementation-Heavy: Research(15k), Implementation(35k), Quality(15k), Coordination(5k)"
        echo "  Quality-Heavy: Research(20k), Implementation(20k), Quality(25k), Coordination(5k)"
        echo "  Balanced: Research(20k), Implementation(25k), Quality(15k), Coordination(10k)"
        echo ""
        
        research_budget=$(prompt_user "Research cluster token budget" "20000")
        implementation_budget=$(prompt_user "Implementation cluster token budget" "25000")
        quality_budget=$(prompt_user "Quality cluster token budget" "15000")
        coordination_budget=$(prompt_user "Coordination cluster token budget" "10000")
        
        local total=$((research_budget + implementation_budget + quality_budget + coordination_budget))
        echo "Total budget: $total tokens"
        
        if [ "$total" -gt 100000 ]; then
            log_warning "High token budget may impact performance"
        fi
    else
        research_budget=20000
        implementation_budget=25000
        quality_budget=15000
        coordination_budget=10000
    fi
    
    # Update configuration
    python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f: config = yaml.safe_load(f)
config['clusters']['research']['token_budget'] = $research_budget
config['clusters']['implementation']['token_budget'] = $implementation_budget
config['clusters']['quality']['token_budget'] = $quality_budget
config['clusters']['coordination']['token_budget'] = $coordination_budget
with open('$CONFIG_FILE', 'w') as f: yaml.dump(config, f, default_flow_style=False)
"
    
    log_success "Token budgets configured"
}

configure_context7() {
    echo ""
    log_info "📚 Configuring Context7 Integration"
    echo "Context7 provides authoritative library documentation integration"
    echo ""
    
    local context7_enforced="true"
    local context7_timeout=30
    local context7_fallback="false"
    
    if prompt_yes_no "Enable mandatory Context7 enforcement?" "y"; then
        context7_enforced="true"
        echo "✅ Context7 enforcement enabled - all code operations will require documentation lookup"
        
        context7_timeout=$(prompt_user "Context7 query timeout (seconds)" "30")
        
        if prompt_yes_no "Enable fallback when Context7 unavailable?" "n"; then
            context7_fallback="true"
            log_warning "Fallback enabled - may reduce code quality when Context7 is unavailable"
        fi
    else
        context7_enforced="false"
        log_warning "Context7 enforcement disabled - reduced code quality and API compliance"
    fi
    
    # Update configuration
    python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f: config = yaml.safe_load(f)
config['platform']['context7_enforced'] = $context7_enforced == 'true'
config['context7']['enforced'] = $context7_enforced == 'true'
config['context7']['timeout'] = $context7_timeout
config['context7']['fallback_enabled'] = $context7_fallback == 'true'
with open('$CONFIG_FILE', 'w') as f: yaml.dump(config, f, default_flow_style=False)
"
    
    log_success "Context7 integration configured"
}

configure_monitoring() {
    echo ""
    log_info "📈 Configuring Monitoring & Analytics"
    echo ""
    
    local monitoring_enabled="true"
    local monitoring_port=8080
    local log_level="INFO"
    local metrics_retention="7d"
    
    if prompt_yes_no "Enable monitoring dashboard?" "y"; then
        monitoring_port=$(prompt_user "Monitoring dashboard port" "8080")
        
        log_level=$(select_option "Select log level:" "DEBUG" "INFO" "WARNING" "ERROR")
        
        metrics_retention=$(prompt_user "Metrics retention period" "7d")
        
        log_success "Monitoring dashboard will be available at http://localhost:$monitoring_port"
    else
        monitoring_enabled="false"
        log_warning "Monitoring disabled - reduced observability into agent performance"
    fi
    
    # Update configuration
    python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f: config = yaml.safe_load(f)
config['monitoring']['enabled'] = $monitoring_enabled == 'true'
config['monitoring']['port'] = $monitoring_port
config['monitoring']['log_level'] = '$log_level'
config['monitoring']['metrics_retention'] = '$metrics_retention'
with open('$CONFIG_FILE', 'w') as f: yaml.dump(config, f, default_flow_style=False)
"
    
    log_success "Monitoring configuration saved"
}

configure_agent_clusters() {
    echo ""
    log_info "🤖 Configuring Agent Clusters"
    echo ""
    
    local clusters=("research" "implementation" "quality" "coordination")
    
    for cluster in "${clusters[@]}"; do
        echo ""
        echo "--- $cluster Cluster ---"
        
        if prompt_yes_no "Enable $cluster cluster?" "y"; then
            case "$cluster" in
                research)
                    echo "Available agents: context7, exa, web-search"
                    ;;
                implementation)
                    echo "Available agents: serena, claude-context, taskmaster, sequential-thinking"
                    ;;
                quality)
                    echo "Available agents: zen, testing-frameworks, code-review"
                    ;;
                coordination)
                    echo "Available agents: conport, openmemory, cli"
                    ;;
            esac
            
            # Update cluster enabled status
            python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f: config = yaml.safe_load(f)
config['clusters']['$cluster']['enabled'] = True
with open('$CONFIG_FILE', 'w') as f: yaml.dump(config, f, default_flow_style=False)
"
        else
            python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f: config = yaml.safe_load(f)
config['clusters']['$cluster']['enabled'] = False
with open('$CONFIG_FILE', 'w') as f: yaml.dump(config, f, default_flow_style=False)
"
            log_warning "$cluster cluster disabled"
        fi
    done
    
    log_success "Agent clusters configured"
}

create_development_profiles() {
    echo ""
    log_info "👨‍💻 Creating Development Profiles"
    echo ""
    
    local profiles_dir="${PLATFORM_DIR}/config/profiles"
    mkdir -p "$profiles_dir"
    
    if prompt_yes_no "Create development workflow profiles?" "y"; then
        
        # Frontend Development Profile
        cat > "$profiles_dir/frontend.yaml" << EOF
name: Frontend Development
description: Optimized for React, Vue, Angular, and modern frontend frameworks

clusters:
  research:
    token_budget: 25000
    agents: [context7, exa]
    focus: [react, vue, angular, typescript, css, webpack, vite]
  implementation:
    token_budget: 30000
    agents: [serena, claude-context, taskmaster]
    focus: [component-patterns, state-management, routing, testing]
  quality:
    token_budget: 20000
    agents: [zen]
    focus: [unit-testing, e2e-testing, accessibility, performance]
  coordination:
    token_budget: 5000
    agents: [conport, openmemory]

context7:
  preferred_docs: [react, typescript, jest, cypress, webpack]
EOF
        
        # Backend Development Profile
        cat > "$profiles_dir/backend.yaml" << EOF
name: Backend Development
description: Optimized for Node.js, Python, Go, and API development

clusters:
  research:
    token_budget: 20000
    agents: [context7, exa]
    focus: [nodejs, python, go, databases, apis, security]
  implementation:
    token_budget: 35000
    agents: [serena, claude-context, taskmaster, sequential-thinking]
    focus: [api-design, database-patterns, authentication, scaling]
  quality:
    token_budget: 15000
    agents: [zen]
    focus: [api-testing, load-testing, security-testing]
  coordination:
    token_budget: 10000
    agents: [conport, openmemory, cli]

context7:
  preferred_docs: [nodejs, express, fastapi, postgresql, redis]
EOF
        
        # Full-Stack Profile
        cat > "$profiles_dir/fullstack.yaml" << EOF
name: Full-Stack Development
description: Balanced for both frontend and backend development

clusters:
  research:
    token_budget: 22000
    agents: [context7, exa]
    focus: [react, nodejs, typescript, databases, deployment]
  implementation:
    token_budget: 32000
    agents: [serena, claude-context, taskmaster, sequential-thinking]
    focus: [end-to-end-features, api-integration, state-management]
  quality:
    token_budget: 18000
    agents: [zen]
    focus: [integration-testing, e2e-testing, performance]
  coordination:
    token_budget: 8000
    agents: [conport, openmemory, cli]

context7:
  preferred_docs: [react, nodejs, typescript, postgresql, docker]
EOF
        
        log_success "Created development profiles: frontend, backend, fullstack"
    fi
}

validate_configuration() {
    echo ""
    log_info "🔍 Validating Configuration"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file missing"
        return 1
    fi
    
    # Basic YAML validation
    if ! python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
        log_error "Invalid YAML configuration"
        return 1
    fi
    
    # Check required fields
    local required_fields=("platform.mode" "clusters.research.token_budget" "context7.enforced")
    local valid=true
    
    for field in "${required_fields[@]}"; do
        if ! python3 -c "
import yaml
config = yaml.safe_load(open('$CONFIG_FILE'))
keys = '$field'.split('.')
value = config
for key in keys:
    value = value[key]
" 2>/dev/null; then
            log_error "Missing required field: $field"
            valid=false
        fi
    done
    
    if [ "$valid" = true ]; then
        log_success "Configuration validation passed"
        return 0
    else
        log_error "Configuration validation failed"
        return 1
    fi
}

show_configuration_summary() {
    echo ""
    echo -e "${GREEN}🎉 Configuration Complete!${NC}"
    echo ""
    echo -e "${CYAN}Platform Evolution Configuration Summary:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show key configuration values
    python3 -c "
import yaml
config = yaml.safe_load(open('$CONFIG_FILE'))

print(f\"Mode: {config['platform']['mode']}\")
print(f\"Context7 Enforced: {'✅' if config['platform']['context7_enforced'] else '❌'}\")
print(f\"Monitoring: {'✅' if config['monitoring']['enabled'] else '❌'}\")
if config['monitoring']['enabled']:
    print(f\"Dashboard Port: {config['monitoring']['port']}\")

print(\"\nToken Budget Distribution:\")
total = 0
for cluster, settings in config['clusters'].items():
    if settings['enabled']:
        budget = settings['token_budget']
        total += budget
        print(f\"  {cluster.capitalize()}: {budget:,} tokens\")
print(f\"  Total: {total:,} tokens\")

print(\"\nEnabled Clusters:\")
for cluster, settings in config['clusters'].items():
    status = '✅' if settings['enabled'] else '❌'
    print(f\"  {cluster.capitalize()}: {status}\")
"
    
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Navigate to any project: cd /path/to/your/project"
    echo "2. Activate platform: claude-platform activate"
    echo "3. Start agents: claude-platform start"
    echo "4. Use Claude Code with distributed agents!"
    echo ""
    echo -e "${CYAN}Documentation:${NC} https://github.com/your-org/claude-platform-evolution"
}

main() {
    show_banner
    check_installation
    
    echo "This wizard will configure Platform Evolution for optimal distributed development."
    echo ""
    
    configure_token_budgets
    configure_context7
    configure_monitoring
    configure_agent_clusters
    create_development_profiles
    
    if validate_configuration; then
        show_configuration_summary
    else
        log_error "Configuration incomplete or invalid"
        exit 1
    fi
}

main "$@"