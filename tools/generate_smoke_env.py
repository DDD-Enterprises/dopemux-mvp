#!/usr/bin/env python3
"""
Generate .env.smoke from services/registry.yaml

This ensures docker-compose.smoke.yml uses registry as single source of truth for ports.

Usage:
    python tools/generate_smoke_env.py [--output .env.smoke]
"""
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_registry(registry_path: Path) -> Dict[str, Any]:
    """Load and parse registry.yaml."""
    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(registry_path) as f:
        return yaml.safe_load(f)


def generate_env_content(registry: Dict[str, Any]) -> str:
    """Generate .env file content from registry."""
    lines = [
        "# Generated from services/registry.yaml",
        "# DO NOT EDIT MANUALLY - Regenerate with: python tools/generate_smoke_env.py",
        f"# Generated: {registry.get('last_updated', 'unknown')}",
        "",
        "# Common settings",
        "LOG_LEVEL=INFO",
        "",
    ]
    
    services = registry.get("services", [])
    smoke_services = [s for s in services if s.get("enabled_in_smoke", False)]
    
    # Group by category
    categories = {}
    for svc in smoke_services:
        cat = svc.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(svc)
    
    for category, svcs in sorted(categories.items()):
        lines.append(f"# {category.upper()} Services")
        for svc in svcs:
            name = svc["name"]
            port = svc["port"]
            container_port = svc.get("container_port", port)
            
            # Use uppercase with underscores for env var names
            env_prefix = name.upper().replace("-", "_")
            
            lines.append(f"{env_prefix}_PORT={port}")
            if container_port != port:
                lines.append(f"{env_prefix}_CONTAINER_PORT={container_port}")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate .env.smoke from registry.yaml")
    parser.add_argument(
        "--output",
        default=".env.smoke",
        help="Output file path (default: .env.smoke)"
    )
    parser.add_argument(
        "--registry",
        default="services/registry.yaml",
        help="Registry file path (default: services/registry.yaml)"
    )
    args = parser.parse_args()
    
    # Resolve paths relative to repo root
    repo_root = Path(__file__).parent.parent
    registry_path = repo_root / args.registry
    output_path = repo_root / args.output
    
    # Load registry
    registry = load_registry(registry_path)
    
    # Generate env content
    content = generate_env_content(registry)
    
    # Write to file
    output_path.write_text(content)
    print(f"✅ Generated {output_path}")
    print(f"   Services: {len([s for s in registry.get('services', []) if s.get('enabled_in_smoke')])} enabled in smoke stack")
    print(f"\nNext steps:")
    print(f"  1. Review {output_path}")
    print(f"  2. Start smoke stack: docker compose -f docker-compose.smoke.yml up -d --build")
    print(f"  3. Validate: python tools/ports_health_audit.py --mode runtime")


if __name__ == "__main__":
    main()
