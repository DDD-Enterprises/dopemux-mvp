#!/usr/bin/env python3

"""
MCP Server Migration System
Migrates existing MCP servers to the distributed Platform Evolution architecture
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import shutil

class MCPMigrationOrchestrator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.platform_root = self.project_root / ".claude" / "platform-evolution"
        self.existing_mcp_config = self.project_root / ".mcp.json"
        self.agent_architecture_config = self.platform_root / "agent-architecture.yaml"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def load_existing_mcp_config(self) -> Dict[str, Any]:
        """Load current .mcp.json configuration"""
        if not self.existing_mcp_config.exists():
            self.logger.warning("No existing .mcp.json found - creating minimal config")
            return {"mcpServers": {}}
            
        with open(self.existing_mcp_config, 'r') as f:
            return json.load(f)
    
    def load_agent_architecture(self) -> Dict[str, Any]:
        """Load agent architecture configuration"""
        with open(self.agent_architecture_config, 'r') as f:
            return yaml.safe_load(f)
    
    def analyze_mcp_servers(self, mcp_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze existing MCP servers and categorize by agent cluster"""
        servers = mcp_config.get("mcpServers", {})
        
        # Server categorization based on functionality
        server_categories = {
            "research_cluster": [
                "exa", "context7", "perplexity", "web-search"
            ],
            "implementation_cluster": [
                "serena", "claude-context", "task-master-ai", 
                "sequential-thinking", "smithery-ai-server-sequential-thinking"
            ],
            "quality_cluster": [
                "zen", "codereview", "testgen", "precommit"
            ],
            "coordination_cluster": [
                "conport", "openmemory", "cli"
            ]
        }
        
        categorized_servers = {
            "research_cluster": {},
            "implementation_cluster": {},
            "quality_cluster": {},
            "coordination_cluster": {}
        }
        
        for server_name, server_config in servers.items():
            assigned = False
            
            # Check each category for matching servers
            for cluster, server_patterns in server_categories.items():
                for pattern in server_patterns:
                    if pattern in server_name.lower():
                        categorized_servers[cluster][server_name] = server_config
                        assigned = True
                        break
                if assigned:
                    break
            
            # Default to coordination cluster if unmatched
            if not assigned:
                categorized_servers["coordination_cluster"][server_name] = server_config
                self.logger.warning(f"Server '{server_name}' not categorized - defaulting to coordination_cluster")
        
        return categorized_servers
    
    def generate_distributed_configs(self, categorized_servers: Dict[str, Dict[str, Any]]) -> None:
        """Generate distributed MCP configurations for each agent cluster"""
        
        for cluster_name, servers in categorized_servers.items():
            if not servers:
                continue
                
            cluster_config = {
                "mcpServers": servers,
                "cluster": {
                    "name": cluster_name,
                    "context7_enforced": True if cluster_name in ["research_cluster", "implementation_cluster"] else False,
                    "token_budget": self._get_cluster_token_budget(cluster_name)
                }
            }
            
            # Write cluster-specific MCP config
            cluster_config_path = self.platform_root / f"mcp-{cluster_name}.json"
            with open(cluster_config_path, 'w') as f:
                json.dump(cluster_config, f, indent=2)
            
            self.logger.info(f"Generated MCP config for {cluster_name}: {cluster_config_path}")
    
    def _get_cluster_token_budget(self, cluster_name: str) -> int:
        """Get token budget allocation for cluster"""
        budgets = {
            "research_cluster": 20000,    # High budget for Context7 + Exa research
            "implementation_cluster": 25000,  # Highest budget for code generation
            "quality_cluster": 15000,     # Medium budget for testing/review
            "coordination_cluster": 10000  # Lower budget for orchestration
        }
        return budgets.get(cluster_name, 10000)
    
    def create_migration_docker_configs(self) -> None:
        """Create Docker configurations for migrated MCP servers"""
        
        # Create agent-specific Dockerfiles
        agent_configs = {
            "research-agent": {
                "base_image": "python:3.11-slim",
                "requirements": ["requests", "aiohttp", "beautifulsoup4"],
                "mcp_servers": ["exa", "context7"]
            },
            "implementation-agent": {
                "base_image": "node:18-slim",
                "requirements": ["python3", "pip"],
                "mcp_servers": ["serena", "claude-context", "task-master-ai"]
            },
            "quality-agent": {
                "base_image": "python:3.11-slim",
                "requirements": ["pytest", "ruff", "mypy"],
                "mcp_servers": ["zen"]
            },
            "coordination-agent": {
                "base_image": "python:3.11-slim",
                "requirements": ["fastapi", "uvicorn"],
                "mcp_servers": ["conport", "openmemory"]
            }
        }
        
        for agent_name, config in agent_configs.items():
            dockerfile_content = self._generate_dockerfile(config)
            dockerfile_path = self.platform_root / f"Dockerfile.{agent_name}"
            
            # Ensure directory exists
            dockerfile_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            self.logger.info(f"Generated Dockerfile for {agent_name}")
    
    def _generate_dockerfile(self, config: Dict[str, Any]) -> str:
        """Generate Dockerfile content for agent"""
        base_image = config["base_image"]
        requirements = config["requirements"]
        mcp_servers = config["mcp_servers"]
        
        dockerfile = f"""FROM {base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Node.js if needed
{self._get_nodejs_install() if 'node' not in base_image else ''}

# Create app directory
WORKDIR /app

# Copy platform files
COPY . .

# Install Python requirements
RUN pip install {' '.join(requirements)}

# Install MCP servers
{self._get_mcp_install_commands(mcp_servers)}

# Create entrypoint
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
"""
        return dockerfile
    
    def _get_nodejs_install(self) -> str:
        """Get Node.js installation commands"""
        return """
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs
"""
    
    def _get_mcp_install_commands(self, mcp_servers: List[str]) -> str:
        """Generate MCP server installation commands"""
        commands = []
        
        for server in mcp_servers:
            if server == "task-master-ai":
                commands.append("RUN npm install -g task-master-ai")
            elif server == "serena":
                commands.append("RUN pip install serena-mcp")
            elif server in ["exa", "context7", "zen"]:
                commands.append(f"# {server} server will be configured via MCP")
        
        return '\n'.join(commands)
    
    def update_main_docker_compose(self) -> None:
        """Update main docker-compose.yml with migration configurations"""
        compose_path = self.platform_root / "docker-compose.yml"
        
        if not compose_path.exists():
            self.logger.error("Main docker-compose.yml not found")
            return
        
        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Add volume mounts for MCP configs
        for service_name, service_config in compose_config.get('services', {}).items():
            if 'agent' in service_name:
                volumes = service_config.get('volumes', [])
                
                # Add MCP config volume mount
                cluster_name = self._get_cluster_from_service(service_name)
                if cluster_name:
                    mcp_config_mount = f"./mcp-{cluster_name}.json:/app/mcp-config.json:ro"
                    if mcp_config_mount not in volumes:
                        volumes.append(mcp_config_mount)
                
                service_config['volumes'] = volumes
        
        # Write updated compose config
        with open(compose_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        self.logger.info("Updated docker-compose.yml with MCP configurations")
    
    def _get_cluster_from_service(self, service_name: str) -> str:
        """Map service name to cluster name"""
        cluster_mapping = {
            "research": "research_cluster",
            "implementation": "implementation_cluster", 
            "quality": "quality_cluster",
            "coordination": "coordination_cluster"
        }
        
        for key, cluster in cluster_mapping.items():
            if key in service_name:
                return cluster
        
        return "coordination_cluster"
    
    def create_migration_validation(self) -> None:
        """Create validation script to test migrated configuration"""
        validation_script = """#!/bin/bash

# MCP Migration Validation Script
echo "🔍 Validating MCP migration..."

# Check cluster configs exist
for cluster in research implementation quality coordination; do
    config_file=".claude/platform-evolution/mcp-${cluster}_cluster.json"
    if [ -f "$config_file" ]; then
        echo "✅ $config_file exists"
    else
        echo "❌ $config_file missing"
        exit 1
    fi
done

# Test Context7 integration
python3 .claude/platform-evolution/context7-enforcer.py --validate
if [ $? -eq 0 ]; then
    echo "✅ Context7 integration validated"
else
    echo "❌ Context7 integration failed"
    exit 1
fi

# Test agent connectivity
docker-compose -f .claude/platform-evolution/docker-compose.yml config
if [ $? -eq 0 ]; then
    echo "✅ Docker compose configuration valid"
else
    echo "❌ Docker compose configuration invalid"
    exit 1
fi

echo "🎉 MCP migration validation passed!"
"""
        
        validation_path = self.platform_root / "validate-migration.sh"
        with open(validation_path, 'w') as f:
            f.write(validation_script)
        
        # Make executable
        subprocess.run(["chmod", "+x", str(validation_path)])
        self.logger.info(f"Created migration validation script: {validation_path}")
    
    def backup_existing_config(self) -> None:
        """Backup existing MCP configuration"""
        if self.existing_mcp_config.exists():
            backup_path = self.project_root / ".mcp.json.backup"
            shutil.copy2(self.existing_mcp_config, backup_path)
            self.logger.info(f"Backed up existing MCP config to {backup_path}")
    
    def migrate_mcp_servers(self) -> None:
        """Execute complete MCP server migration"""
        self.logger.info("🚀 Starting MCP server migration to Platform Evolution...")
        
        # Step 1: Backup existing configuration
        self.backup_existing_config()
        
        # Step 2: Load configurations
        mcp_config = self.load_existing_mcp_config()
        servers_count = len(mcp_config.get('mcpServers', {}))
        self.logger.info(f"Loaded {servers_count} existing MCP servers")
        
        # Step 3: Analyze and categorize servers
        categorized_servers = self.analyze_mcp_servers(mcp_config)
        for cluster, servers in categorized_servers.items():
            if servers:
                self.logger.info(f"{cluster}: {len(servers)} servers")
        
        # Step 4: Generate distributed configurations
        self.generate_distributed_configs(categorized_servers)
        
        # Step 5: Create Docker configurations
        self.create_migration_docker_configs()
        
        # Step 6: Update main Docker Compose
        self.update_main_docker_compose()
        
        # Step 7: Create validation script
        self.create_migration_validation()
        
        self.logger.info("✅ MCP server migration completed!")
        self.logger.info("Next steps:")
        self.logger.info("1. Run ./validate-migration.sh to test configuration")
        self.logger.info("2. Run ./start-platform.sh to deploy distributed platform")
        self.logger.info("3. Monitor with dashboard at http://localhost:8080")

def main():
    """Main execution function"""
    migrator = MCPMigrationOrchestrator()
    migrator.migrate_mcp_servers()

if __name__ == "__main__":
    main()