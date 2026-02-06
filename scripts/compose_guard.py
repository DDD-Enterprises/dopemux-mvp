#!/usr/bin/env python3
"""
Compose Guard - Validates compose.yml for Dopemux standards.

This script ensures the canonical compose.yml file:
1. Passes `docker compose config` validation
2. Contains no *-2 duplicate service definitions
3. Contains no deploy.replicas directives (single-instance default)
4. Contains no exposed API keys/tokens (must use ${VAR} references)
5. Uses the new `docker compose` command format (not docker-compose)

Usage:
    python scripts/compose_guard.py
    python scripts/compose_guard.py --fix  # (not implemented yet)

Exit codes:
    0 - All checks passed
    1 - Validation failed
    2 - File not found or invalid arguments
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root():
    """Find the repository root directory."""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def validate_compose_syntax(compose_file):
    """Validate compose file syntax with docker compose config."""
    print(f"✓ Validating compose syntax: {compose_file}")
    
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"✗ Compose file failed validation:")
            print(result.stderr)
            return False
            
        print("✓ Compose syntax is valid")
        return True
        
    except FileNotFoundError:
        print("✗ docker compose command not found. Is Docker installed?")
        return False
    except subprocess.TimeoutExpired:
        print("✗ docker compose config timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"✗ Error running docker compose config: {e}")
        return False


def check_for_duplicate_services(compose_file):
    """Check for prohibited *-2 service definitions."""
    print(f"✓ Checking for duplicate *-2 services in: {compose_file}")
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Pattern to match service definitions ending in -2:
        # Look for lines like "  service-name-2:" at the service level
        pattern = r'^\s\s[a-z][a-z0-9_-]*-2:\s*$'
        
        matches = []
        for line_num, line in enumerate(content.splitlines(), 1):
            if re.match(pattern, line):
                service_name = line.strip().rstrip(':')
                matches.append((line_num, service_name))
        
        if matches:
            print(f"✗ Found {len(matches)} prohibited *-2 service definition(s):")
            for line_num, service_name in matches:
                print(f"   Line {line_num}: {service_name}")
            print()
            print("  Scaling should be done via 'docker compose up --scale service=N'")
            print("  Do not define task-orchestrator-2, adhd-engine-2, etc.")
            return False
        
        print("✓ No duplicate *-2 services found")
        return True
        
    except FileNotFoundError:
        print(f"✗ File not found: {compose_file}")
        return False
    except Exception as e:
        print(f"✗ Error checking file: {e}")
        return False


def check_for_deploy_replicas(compose_file):
    """Check for prohibited deploy.replicas in compose file."""
    print(f"✓ Checking for deploy.replicas scaling...")
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Pattern to match deploy.replicas blocks
        pattern = r'^\s+replicas:\s*\d+\s*$'
        
        matches = []
        for line_num, line in enumerate(content.splitlines(), 1):
            if re.match(pattern, line):
                matches.append((line_num, line.strip()))
        
        if matches:
            print(f"✗ Found {len(matches)} prohibited deploy.replicas directive(s):")
            for line_num, line in matches:
                print(f"   Line {line_num}: {line}")
            print()
            print("  Scaling should be done via 'docker compose up --scale service=N'")
            print("  Remove deploy.replicas from compose.yml for single-instance default")
            return False
        
        print("✓ No deploy.replicas directives found (single-instance default)")
        return True
        
    except FileNotFoundError:
        print(f"✗ File not found: {compose_file}")
        return False
    except Exception as e:
        print(f"✗ Error checking file: {e}")
        return False


def check_for_exposed_secrets(compose_file):
    """Check for hardcoded API keys/tokens in compose file."""
    print(f"✓ Checking for exposed secrets...")
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Patterns for common API key prefixes
        secret_patterns = [
            (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI/Anthropic key'),
            (r'tvly-[a-zA-Z0-9]{20,}', 'Tavily key'),
            (r'lt_[a-zA-Z0-9]{20,}', 'Leantime token'),
            (r'xai-[a-zA-Z0-9]{20,}', 'X.AI key'),
        ]
        
        matches = []
        for line_num, line in enumerate(content.splitlines(), 1):
            # Skip lines that are using ${VAR} references
            if '${' in line and '}' in line:
                continue
            
            for pattern, key_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append((line_num, key_type, line.strip()[:80]))
        
        if matches:
            print(f"✗ Found {len(matches)} potential exposed secret(s):")
            for line_num, key_type, line in matches:
                print(f"   Line {line_num}: {key_type} - {line}")
            print()
            print("  All secrets must use ${VAR} references, not hardcoded values")
            print("  Move secrets to .env and reference as ${VARIABLE_NAME}")
            return False
        
        print("✓ No exposed secrets found (all use ${VAR} references)")
        return True
        
    except FileNotFoundError:
        print(f"✗ File not found: {compose_file}")
        return False
    except Exception as e:
        print(f"✗ Error checking file: {e}")
        return False


def check_docker_compose_command(compose_file):
    """Check for deprecated docker-compose hyphenated command in comments/docs."""
    print(f"✓ Checking for deprecated 'docker-compose' references...")
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Look for docker-compose (with hyphen) in comments
        pattern = r'docker-compose'
        
        matches = []
        for line_num, line in enumerate(content.splitlines(), 1):
            if re.search(pattern, line) and line.strip().startswith('#'):
                matches.append((line_num, line.strip()))
        
        if matches:
            print(f"⚠ Found {len(matches)} reference(s) to deprecated 'docker-compose':")
            for line_num, line in matches:
                print(f"   Line {line_num}: {line[:80]}")
            print()
            print("  Consider updating to 'docker compose' (without hyphen)")
            print("  This is a warning, not a fatal error.")
        else:
            print("✓ No deprecated docker-compose references in comments")
        
        return True  # This is just a warning, not a failure
        
    except Exception as e:
        print(f"✗ Error checking docker-compose references: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate Dopemux compose.yml")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues (not yet implemented)"
    )
    args = parser.parse_args()
    
    if args.fix:
        print("✗ --fix is not yet implemented")
        return 2
    
    # Find compose.yml in repo root
    repo_root = find_repo_root()
    compose_file = repo_root / "compose.yml"
    
    if not compose_file.exists():
        print(f"✗ compose.yml not found at: {compose_file}")
        print("  Expected location: <repo-root>/compose.yml")
        return 2
    
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         Dopemux Compose Guard - Validation Suite         ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    print(f"Compose file: {compose_file}")
    print()
    
    # Run all checks
    checks = [
        validate_compose_syntax(compose_file),
        check_for_duplicate_services(compose_file),
        check_for_deploy_replicas(compose_file),
        check_for_exposed_secrets(compose_file),
        check_docker_compose_command(compose_file),
    ]
    
    print()
    print("=" * 60)
    
    if all(checks):
        print("✅ All checks passed! compose.yml is valid.")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
