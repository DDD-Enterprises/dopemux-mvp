#!/usr/bin/env python3
"""
Phase 2 verification script for working-memory-assistant.

Verifies:
- Core imports succeed
- Optional mirror import is explicitly skipped when asyncpg is unavailable
- Phase 2 methods/endpoints/models exist
- SQLite schema includes reflection + trajectory tables
"""

import inspect
import sys
from pathlib import Path

# Add service dir to path
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))

def verify_imports():
    """Verify all critical imports."""
    print("=== Verifying Imports ===")

    try:
        from chronicle.store import ChronicleStore
        print("✓ chronicle.store.ChronicleStore")
    except Exception as e:
        print(f"✗ chronicle.store.ChronicleStore: {e}")
        return False

    try:
        from eventbus_consumer import EventBusConsumer
        print("✓ eventbus_consumer.EventBusConsumer")
    except Exception as e:
        print(f"✗ eventbus_consumer.EventBusConsumer: {e}")
        return False

    mirror_check_passed = True
    try:
        from postgres_mirror_sync import PostgresMirrorSync
        print("✓ postgres_mirror_sync.PostgresMirrorSync")
    except Exception as e:
        if "No module named 'asyncpg'" in str(e):
            print(
                "⚠ postgres_mirror_sync.PostgresMirrorSync skipped: "
                "asyncpg not installed in local environment"
            )
            mirror_check_passed = True
        else:
            print(f"✗ postgres_mirror_sync.PostgresMirrorSync: {e}")
            mirror_check_passed = False

    try:
        from dope_memory_main import DopeMemoryMCPServer
        print("✓ dope_memory_main.DopeMemoryMCPServer")
    except Exception as e:
        print(f"✗ dope_memory_main.DopeMemoryMCPServer: {e}")
        return False
    return mirror_check_passed


def verify_constructor_signatures():
    """Verify current MCP server constructor signatures."""
    print("\n=== Verifying Constructor Signatures ===")

    from dope_memory_main import DopeMemoryMCPServer as HttpServer
    from mcp.server import DopeMemoryMCPServer as CoreServer

    http_sig = str(inspect.signature(HttpServer.__init__))
    core_sig = str(inspect.signature(CoreServer.__init__))
    print(f"✓ dope_memory_main.DopeMemoryMCPServer.__init__{http_sig}")
    print(f"✓ mcp.server.DopeMemoryMCPServer.__init__{core_sig}")
    return True


def verify_phase2_methods():
    """Verify Phase 2 methods exist."""
    print("\n=== Verifying Phase 2 Methods ===")

    from dope_memory_main import DopeMemoryMCPServer

    required_methods = [
        "memory_generate_reflection",
        "memory_reflections",
        "memory_trajectory",
    ]

    for method in required_methods:
        if hasattr(DopeMemoryMCPServer, method):
            print(f"✓ DopeMemoryMCPServer.{method}")
        else:
            print(f"✗ DopeMemoryMCPServer.{method} - MISSING")
            return False
    
    return True


def verify_endpoints():
    """Verify Phase 2 endpoints are registered."""
    print("\n=== Verifying Endpoints ===")

    from dope_memory_main import app

    phase2_endpoints = [
        "/tools/memory_generate_reflection",
        "/tools/memory_reflections",
        "/tools/memory_trajectory",
    ]

    routes = {route.path for route in app.routes}

    for endpoint in phase2_endpoints:
        if endpoint in routes:
            print(f"✓ {endpoint}")
        else:
            print(f"✗ {endpoint} - MISSING")
            return False
    
    return True


def verify_request_models():
    """Verify Phase 2 request models exist."""
    print("\n=== Verifying Request Models ===")

    from dope_memory_main import (
        MemoryGenerateReflectionRequest,
        MemoryReflectionsRequest,
        MemoryTrajectoryRequest,
    )

    models = [
        ("MemoryGenerateReflectionRequest", MemoryGenerateReflectionRequest),
        ("MemoryReflectionsRequest", MemoryReflectionsRequest),
        ("MemoryTrajectoryRequest", MemoryTrajectoryRequest),
    ]

    for name, model in models:
        try:
            # Verify it's a Pydantic model
            model.model_json_schema()
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name}: {e}")
            return False
    
    return True


def verify_database_schema():
    """Verify database schema has Phase 2 tables."""
    print("\n=== Verifying Database Schema ===")

    import tempfile
    from chronicle.store import ChronicleStore

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = ChronicleStore(db_path)
        store.initialize_schema()
        
        conn = store.connect()

        # Check for reflection_cards table
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='reflection_cards'"
        ).fetchone()

        if result:
            print("✓ reflection_cards table exists")
        else:
            print("✗ reflection_cards table - MISSING")
            return False

        # Check for trajectory_state table
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trajectory_state'"
        ).fetchone()

        if result:
            print("✓ trajectory_state table exists")
        else:
            print("✗ trajectory_state table - MISSING")
            return False
        
        store.close()

    return True


def main():
    """Run all verifications."""
    print("Phase 2 Reflection + Trajectory Verification")
    print("=" * 50)

    checks = [
        ("Imports", verify_imports),
        ("Constructor Signatures", verify_constructor_signatures),
        ("Phase 2 Methods", verify_phase2_methods),
        ("Endpoints", verify_endpoints),
        ("Request Models", verify_request_models),
        ("Database Schema", verify_database_schema),
    ]

    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"\n✗ {name} verification failed with exception: {e}")
            results[name] = False

    print("\n" + "=" * 50)
    print("=== Verification Summary ===")
    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("✅ All Phase 2 verifications passed!")
        return 0
    else:
        print("❌ Some verifications failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
