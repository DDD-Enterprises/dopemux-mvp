#!/usr/bin/env python3
"""
Real-World Worktree Validation Script

Tests multi-instance isolation by simulating:
1. Main worktree creates shared task
2. Feature worktree creates isolated task
3. Verify isolation works correctly
4. Test status transitions

Run from either worktree with environment variables set.
"""

import os
import sys
import asyncio
import asyncpg

# Database connection
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph'
)

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)


async def test_instance_detector():
    """Test SimpleInstanceDetector module"""
    print("\n=== Testing SimpleInstanceDetector ===")

    sys.path.insert(0, os.path.dirname(__file__))
    from instance_detector import SimpleInstanceDetector

    instance_id = SimpleInstanceDetector.get_instance_id()
    workspace_id = SimpleInstanceDetector.get_workspace_id()
    context = SimpleInstanceDetector.get_context()

    print(f"Instance ID: {instance_id or 'None (main worktree)'}")
    print(f"Workspace ID: {workspace_id}")
    print(f"Is Main Worktree: {context['is_main_worktree']}")
    print(f"Is Multi-Worktree: {context['is_multi_worktree']}")

    return context


async def create_test_task(status, description, workspace_id, instance_id):
    """Create a test task with given parameters"""
    conn = await get_db_connection()
    try:
        # Determine final instance_id based on status
        from instance_detector import SimpleInstanceDetector
        if SimpleInstanceDetector.is_isolated_status(status):
            final_instance_id = instance_id
        else:
            final_instance_id = None

        result = await conn.fetchrow("""
            INSERT INTO progress_entries
            (workspace_id, instance_id, description, status)
            VALUES ($1, $2, $3, $4)
            RETURNING id, instance_id, status, description
        """, workspace_id, final_instance_id, description, status)

        print(f"\nCreated task:")
        print(f"  ID: {result['id']}")
        print(f"  Status: {result['status']}")
        print(f"  Instance: {result['instance_id'] or 'NULL (shared)'}")
        print(f"  Description: {result['description']}")

        return result['id']
    finally:
        await conn.close()


async def query_visible_tasks(workspace_id, instance_id):
    """Query tasks visible to current instance"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT id, status, instance_id, description
            FROM progress_entries
            WHERE workspace_id = $1
              AND (instance_id IS NULL OR instance_id = $2)
            ORDER BY created_at DESC
        """, workspace_id, instance_id)

        print(f"\n=== Tasks Visible to Instance '{instance_id or 'main'}' ===")
        if not rows:
            print("  No tasks visible")
        for row in rows:
            print(f"  [{row['status']}] {row['description'][:50]}")
            print(f"    Instance: {row['instance_id'] or 'NULL (shared)'}")

        return rows
    finally:
        await conn.close()


async def update_task_status(task_id, new_status, instance_id):
    """Update task status and test instance_id clearing"""
    conn = await get_db_connection()
    try:
        from instance_detector import SimpleInstanceDetector

        # Determine final instance_id based on new status
        if SimpleInstanceDetector.is_isolated_status(new_status):
            final_instance_id = instance_id
        else:
            final_instance_id = None

        await conn.execute("""
            UPDATE progress_entries
            SET status = $1, instance_id = $2, updated_at = NOW()
            WHERE id = $3
        """, new_status, final_instance_id, task_id)

        row = await conn.fetchrow("""
            SELECT id, status, instance_id, description
            FROM progress_entries
            WHERE id = $1
        """, task_id)

        print(f"\nUpdated task {task_id}:")
        print(f"  New Status: {row['status']}")
        print(f"  New Instance: {row['instance_id'] or 'NULL (shared)'}")

        return row
    finally:
        await conn.close()


async def cleanup_test_tasks():
    """Clean up test tasks"""
    conn = await get_db_connection()
    try:
        result = await conn.execute("""
            DELETE FROM progress_entries
            WHERE description LIKE '%[TEST]%'
        """)
        print(f"\nCleaned up test tasks: {result}")
    finally:
        await conn.close()


async def main():
    """Run validation tests"""
    print("=" * 60)
    print("WORKTREE MULTI-INSTANCE VALIDATION")
    print("=" * 60)

    # Test 1: Instance detector
    context = await test_instance_detector()
    instance_id = context['instance_id']
    workspace_id = context['workspace_id']

    # Test 2: Create isolated task (if in worktree)
    if instance_id:
        print(f"\n--- Test: Create isolated IN_PROGRESS task ---")
        task_id = await create_test_task(
            'IN_PROGRESS',
            f'[TEST] Isolated task in {instance_id}',
            workspace_id,
            instance_id
        )
    else:
        print(f"\n--- Test: Create shared COMPLETED task (main worktree) ---")
        task_id = await create_test_task(
            'COMPLETED',
            '[TEST] Shared task from main',
            workspace_id,
            None
        )

    # Test 3: Query visible tasks
    await query_visible_tasks(workspace_id, instance_id)

    # Test 4: Status transition (if isolated task exists)
    if instance_id:
        print(f"\n--- Test: Transition to COMPLETED (should clear instance_id) ---")
        await update_task_status(task_id, 'COMPLETED', instance_id)
        await query_visible_tasks(workspace_id, instance_id)

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

    # Optional: Cleanup
    cleanup = input("\nCleanup test tasks? (y/n): ").strip().lower()
    if cleanup == 'y':
        await cleanup_test_tasks()


if __name__ == '__main__':
    asyncio.run(main())
