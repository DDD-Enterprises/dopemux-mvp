# Dopemux Migration System

The migration system handles version-specific updates for Dopemux installations, ensuring smooth upgrades between versions with proper rollback capabilities.

## Directory Structure

```
migrations/
├── README.md                     # This file
├── examples/                     # Example migrations for reference
│   └── v0.1.0_to_v0.2.0/        # Version transition directory
│       ├── 001_update_mcp_configs.py
│       └── 002_upgrade_database_schema.py
└── v[from]_to_v[to]/             # Actual migration directories
    ├── 001_migration_name.py     # Migration files (numbered order)
    └── 002_another_migration.py
```

## Migration File Format

Each migration file must follow this structure:

```python
"""
Migration: v0.1.0 to v0.2.0 - Brief description

Detailed description of what this migration does.
"""

from pathlib import Path
from typing import Dict, Any

def migrate_forward(project_root: Path) -> bool:
    """
    Apply migration: version_from → version_to

    Returns:
        True if migration succeeded, False otherwise
    """
    try:
        # Implementation here
        print("  → Doing migration step")
        print("  ✅ Migration step complete")
        return True
    except Exception as e:
        print(f"  ❌ Migration failed: {e}")
        return False

def migrate_backward(project_root: Path) -> bool:
    """
    Rollback migration: version_to → version_from

    Returns:
        True if rollback succeeded, False otherwise
    """
    try:
        # Rollback implementation here
        print("  → Rolling back migration step")
        print("  ✅ Rollback complete")
        return True
    except Exception as e:
        print(f"  ❌ Rollback failed: {e}")
        return False

# Migration metadata
MIGRATION_INFO = {
    "version_from": "0.1.0",
    "version_to": "0.2.0",
    "description": "Brief description of migration",
    "breaking_changes": False,
    "estimated_duration_seconds": 30,
    "requires_restart": ["service1", "service2"],
    "backup_required": True  # Optional, defaults to True
}
```

## Creating New Migrations

### 1. Create Version Directory

Create a directory for the version transition:
```bash
mkdir -p migrations/v0.2.0_to_v0.3.0
```

### 2. Create Migration Files

Migration files should be numbered in execution order:
```bash
# 001_first_migration.py
# 002_second_migration.py
# etc.
```

### 3. Common Migration Types

**Configuration Updates:**
- Update YAML/JSON config files
- Add new configuration options
- Migrate old settings to new format

**Database Schema Changes:**
- Add/modify tables and columns
- Create new indexes
- Migrate data formats

**Docker Service Updates:**
- Update container configurations
- Add new environment variables
- Modify docker-compose files

**File System Changes:**
- Create new directories
- Move/rename files
- Update file permissions

## Migration Execution

Migrations are automatically discovered and executed by the UpdateManager during the Orchestration phase:

```python
# Automatic execution during update
await orchestration_phase.execute()
```

### Execution Order

1. Migrations are sorted by directory name (version order)
2. Within each directory, files are sorted numerically by prefix
3. Each migration's `migrate_forward()` is called
4. If any migration fails, automatic rollback begins

### Rollback Process

If a migration fails:
1. All completed migrations are rolled back in reverse order
2. Each migration's `migrate_backward()` is called
3. System is restored to pre-update state

## Best Practices

### Migration Development

1. **Keep migrations small and focused** - One logical change per migration
2. **Test both forward and backward migrations** - Ensure rollbacks work
3. **Use descriptive names** - Clear indication of what the migration does
4. **Handle errors gracefully** - Return False on failure, don't raise exceptions
5. **Print progress messages** - Users need visibility into what's happening

### Database Migrations

```python
# Good: Incremental schema changes
def migrate_forward(project_root: Path) -> bool:
    try:
        db_path = project_root / ".dopemux" / "conport.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")
            conn.commit()
        return True
    except sqlite3.OperationalError:
        # Column might already exist
        return True
```

### Configuration Migrations

```python
# Good: Preserve user customizations
def migrate_forward(project_root: Path) -> bool:
    config_file = project_root / "config" / "app.yaml"
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Add new settings while preserving existing
        config.setdefault('new_section', {})
        config['new_section']['timeout'] = 30

        with open(config_file, 'w') as f:
            yaml.dump(config, f)
    return True
```

### Service Restart Requirements

Use the `requires_restart` field to specify which services need restarting:

```python
MIGRATION_INFO = {
    "requires_restart": ["mcp-servers", "serena", "redis"]
}
```

Services will be restarted after all migrations complete.

## Testing Migrations

Before creating a production migration:

1. **Test on a clean installation** - Verify forward migration works
2. **Test rollback scenario** - Ensure backward migration restores state
3. **Test with existing data** - Ensure migration handles real user data
4. **Verify service functionality** - Check that services work after migration

## Example Scenarios

### Adding New MCP Server

```python
def migrate_forward(project_root: Path) -> bool:
    # Update docker-compose to include new MCP server
    # Update broker configuration
    # Create initial configuration files
    return True
```

### Changing Database Schema

```python
def migrate_forward(project_root: Path) -> bool:
    # Create backup
    # Apply schema changes
    # Migrate existing data if needed
    return True
```

### Configuration Format Changes

```python
def migrate_forward(project_root: Path) -> bool:
    # Read old format
    # Convert to new format
    # Write new configuration
    # Keep backup of old format
    return True
```

## Troubleshooting

**Migration fails during execution:**
- Check migration logs for specific error
- Verify file permissions and paths
- Ensure required services are running

**Rollback fails:**
- Manual intervention may be required
- Check backup integrity
- Restore from automated backup if available

**Services don't start after migration:**
- Check service logs
- Verify configuration syntax
- Ensure all required files exist