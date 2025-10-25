#!/usr/bin/env python3
"""
Fix duplicate serena-v2 MCP configuration in ~/.claude.json
Keeps only the SSE entry, removes stdio duplicates.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

def fix_serena_config():
    config_path = Path.home() / '.claude.json'
    backup_path = Path.home() / f'.claude.json.backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}'

    # Backup original
    print(f"📦 Backing up config to: {backup_path}")
    shutil.copy2(config_path, backup_path)

    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Check if serena-v2 exists
    if 'mcpServers' not in config:
        print("❌ No mcpServers section found")
        return

    if 'serena-v2' not in config['mcpServers']:
        print("❌ No serena-v2 entry found")
        return

    # Get current serena-v2 config
    current_config = config['mcpServers']['serena-v2']
    print(f"\n📋 Current serena-v2 config:")
    print(f"   Type: {current_config.get('type')}")

    if current_config.get('type') == 'sse':
        print(f"   URL: {current_config.get('url')}")
        print("\n✅ Already configured as SSE - no changes needed!")
        return

    # Set correct SSE configuration
    print("\n🔧 Fixing configuration...")
    config['mcpServers']['serena-v2'] = {
        "type": "sse",
        "url": "http://localhost:3006/sse"
    }

    # Write fixed config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Fixed! serena-v2 now configured as SSE on port 3006")
    print(f"\n📌 Next steps:")
    print(f"   1. Restart Claude Code")
    print(f"   2. Verify with /mcp command")
    print(f"\n💾 Backup saved at: {backup_path}")

if __name__ == '__main__':
    fix_serena_config()
