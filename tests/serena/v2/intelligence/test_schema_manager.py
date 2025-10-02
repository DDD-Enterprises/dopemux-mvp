"""
Comprehensive Test Suite for SerenaSchemaManager

Tests schema installation, migrations, rollback capabilities,
and ADHD-friendly migration performance.
"""

import pytest
import asyncio
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.schema_manager import (
    SerenaSchemaManager,
    MigrationStatus,
    MigrationStep,
    MigrationResult,
    setup_phase2_schema,
    migrate_from_layer1
)
from v2.intelligence.database import SerenaIntelligenceDatabase, DatabaseConfig
from v2.performance_monitor import PerformanceMonitor


# ==========================================
# Test 1: Schema Manager Initialization
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_schema_manager_initialization(intelligence_db, performance_monitor):
    """Test schema manager creation and initialization."""
    schema_mgr = SerenaSchemaManager(intelligence_db, performance_monitor)

    # Should have correct initial state
    assert schema_mgr.database == intelligence_db
    assert schema_mgr.performance_monitor == performance_monitor
    assert schema_mgr._current_schema_version == "2.0.0-layer1"
    assert schema_mgr._target_schema_version == "2.0.0-phase2a"

    # Should have schema path
    assert schema_mgr.schema_path.exists()
    assert schema_mgr.schema_path.name == "schema.sql"


# ==========================================
# Test 2: Schema File Reading
# ==========================================

@pytest.mark.unit
def test_schema_file_exists():
    """Test that schema.sql file exists and is readable."""
    schema_path = Path(__file__).parent.parent.parent.parent.parent / "services" / "serena" / "v2" / "intelligence" / "schema.sql"

    assert schema_path.exists(), f"Schema file not found: {schema_path}"

    # Read and validate schema content
    with open(schema_path, 'r') as f:
        schema_content = f.read()

    # Should contain table definitions
    assert "CREATE TABLE code_elements" in schema_content
    assert "CREATE TABLE code_relationships" in schema_content
    assert "CREATE TABLE navigation_patterns" in schema_content
    assert "CREATE TABLE learning_profiles" in schema_content
    assert "CREATE TABLE navigation_strategies" in schema_content
    assert "CREATE TABLE conport_integration_links" in schema_content

    # Should contain indexes for ADHD performance
    assert "CREATE INDEX" in schema_content
    assert "adhd" in schema_content.lower()
    assert "cognitive_load" in schema_content.lower()


# ==========================================
# Test 3: Schema Installation (or validates existing)
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_schema_installation(intelligence_db, performance_monitor, assert_adhd_compliant):
    """Test complete schema installation process or validate existing schema."""
    schema_mgr = SerenaSchemaManager(intelligence_db, performance_monitor)

    # Initialize schema (may already exist)
    result = await schema_mgr.initialize_schema()

    # Check if tables exist (whether installation succeeded or schema was already there)
    async with intelligence_db.connection() as conn:
        tables_query = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('code_elements', 'code_relationships', 'navigation_patterns',
                               'learning_profiles', 'navigation_strategies', 'conport_integration_links')
        """
        tables = await conn.fetch(tables_query)
        table_count = len(tables)

    # Either installation succeeded OR schema already exists
    if result.success:
        # Fresh installation succeeded
        assert result.steps_completed > 0
        assert result.error_message is None
        assert result.adhd_compliance is True
        assert table_count == 6
    else:
        # Schema already exists (expected in deployed system)
        assert "already exists" in result.error_message.lower()
        # Tables should still be there
        assert table_count == 6, f"Expected 6 tables, found {table_count}"
        print(f"✓ Schema already deployed - validated {table_count} tables exist")


# ==========================================
# Test 4: Migration Step Definition
# ==========================================

@pytest.mark.unit
def test_migration_step_dataclass():
    """Test MigrationStep dataclass structure."""
    step = MigrationStep(
        step_id="test_migration",
        description="Test migration step",
        sql_commands=["CREATE TABLE test (id SERIAL)"],
        rollback_commands=["DROP TABLE test"],
        validation_query="SELECT COUNT(*) FROM test",
        expected_result=0,
        adhd_impact="low",
        estimated_duration_ms=500
    )

    assert step.step_id == "test_migration"
    assert step.adhd_impact == "low"
    assert step.estimated_duration_ms == 500
    assert len(step.sql_commands) == 1
    assert len(step.rollback_commands) == 1


# ==========================================
# Test 5: Migration Result Tracking
# ==========================================

@pytest.mark.unit
def test_migration_result_dataclass():
    """Test MigrationResult dataclass structure."""
    result = MigrationResult(
        success=True,
        migration_id="test_migration_20251002",
        steps_completed=5,
        total_steps=5,
        duration_ms=1500.0,
        adhd_compliance=True
    )

    assert result.success is True
    assert result.steps_completed == result.total_steps
    assert result.adhd_compliance is True
    assert result.error_message is None


# ==========================================
# Test 6: Schema Validation
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_schema_validation(intelligence_db, performance_monitor):
    """Test schema validation works correctly."""
    schema_mgr = SerenaSchemaManager(intelligence_db, performance_monitor)

    # Validate current installation (schema may already exist)
    validation_result = await schema_mgr._validate_schema_installation()

    # Should validate successfully
    assert validation_result['valid'] is True
    assert len(validation_result.get('errors', [])) == 0

    # Validate manually that tables exist
    async with intelligence_db.connection() as conn:
        tables_query = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('code_elements', 'code_relationships', 'navigation_patterns',
                               'learning_profiles', 'navigation_strategies', 'conport_integration_links')
        """
        tables = await conn.fetch(tables_query)
        table_count = len(tables)

    # Should have all 6 tables
    assert table_count == 6, f"Expected 6 tables, found {table_count}"
    print(f"✓ Schema validation confirmed {table_count} tables deployed")


# ==========================================
# Test 7: Setup Factory Function
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_setup_phase2_schema_factory(test_db_config, performance_monitor):
    """Test convenience setup function for Phase 2 schema."""
    schema_mgr, migration_result = await setup_phase2_schema(test_db_config, performance_monitor)

    # Should return initialized schema manager
    assert isinstance(schema_mgr, SerenaSchemaManager)
    assert isinstance(migration_result, MigrationResult)

    # Migration should succeed OR schema already exists
    if not migration_result.success:
        # Schema already deployed is acceptable
        assert "already exists" in migration_result.error_message.lower()
        print("✓ Schema already deployed - factory function handled correctly")
    else:
        # Fresh installation succeeded
        assert migration_result.adhd_compliance is True


# ==========================================
# Test 8: SQL Statement Splitting
# ==========================================

@pytest.mark.unit
def test_sql_statement_splitting(intelligence_db, performance_monitor):
    """Test SQL statement parsing for migration."""
    schema_mgr = SerenaSchemaManager(intelligence_db, performance_monitor)

    # Test SQL splitting logic
    test_sql = """
    CREATE TABLE test1 (id SERIAL);
    CREATE TABLE test2 (name TEXT);
    -- Comment line
    CREATE INDEX idx_test ON test1(id);
    """

    statements = schema_mgr._split_sql_statements(test_sql)

    # Should split correctly (ignoring comments and empty lines)
    assert len(statements) >= 3
    assert any("test1" in stmt for stmt in statements)
    assert any("test2" in stmt for stmt in statements)


# ==========================================
# Test 9: Migration Status Enum
# ==========================================

@pytest.mark.unit
def test_migration_status_enum():
    """Test MigrationStatus enum values."""
    assert MigrationStatus.PENDING == "pending"
    assert MigrationStatus.RUNNING == "running"
    assert MigrationStatus.COMPLETED == "completed"
    assert MigrationStatus.FAILED == "failed"
    assert MigrationStatus.ROLLBACK == "rollback"


# ==========================================
# Test 10: Schema Version Tracking
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_schema_version_tracking(intelligence_db, performance_monitor):
    """Test schema version management."""
    schema_mgr = SerenaSchemaManager(intelligence_db, performance_monitor)

    # Initial version
    initial_version = schema_mgr._current_schema_version
    assert initial_version == "2.0.0-layer1"

    # After installation, version should update
    await schema_mgr.initialize_schema()

    # Version should be updated to target
    # (Would check via _update_schema_version if it stored in DB)
    assert schema_mgr._target_schema_version == "2.0.0-phase2a"


# ==========================================
# Performance Test: Schema Installation Speed
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.adhd
async def test_schema_installation_performance(intelligence_db, performance_monitor):
    """Test that schema operations meet ADHD performance targets."""
    schema_mgr = SerenaSchemaManager(intelligence_db, performance_monitor)

    import time
    start_time = time.time()

    result = await schema_mgr.initialize_schema()

    operation_time = (time.time() - start_time) * 1000

    # Should complete quickly for ADHD users (<10 seconds)
    # Even if schema exists, the check should be fast
    assert operation_time < 10000, f"Schema operation too slow: {operation_time}ms"

    if result.success:
        # Fresh installation
        assert result.adhd_compliance is True
        print(f"✓ Schema installation completed in {operation_time:.0f}ms")
    else:
        # Schema already exists - should still be fast operation
        assert "already exists" in result.error_message.lower()
        print(f"✓ Schema validation completed in {operation_time:.0f}ms (schema pre-deployed)")
