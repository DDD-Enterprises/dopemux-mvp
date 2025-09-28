#!/usr/bin/env python3
"""
Test Session Persistence for GPT-Researcher
Comprehensive test to verify session creation, persistence, and restoration
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from services.session_manager import SessionManager


async def test_session_persistence():
    """Test complete session persistence workflow"""
    print("🧪 Testing Session Persistence System")
    print("=" * 50)

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temp directory: {temp_dir}")

        # Initialize session manager
        session_manager = SessionManager(storage_path=temp_dir)
        await session_manager.initialize()

        # Test 1: Create new session
        print("\n1️⃣  Testing session creation...")
        session_id = str(uuid4())
        session = await session_manager.get_or_create_session(session_id)

        assert session['session_id'] == session_id
        assert session['attention_state'] == 'fresh'
        assert len(session['task_ids']) == 0
        print("✅ Session created successfully")

        # Test 2: Add task results
        print("\n2️⃣  Testing task result storage...")
        task_id = str(uuid4())
        task_results = {
            'summary': 'Test research on Python async patterns',
            'key_findings': ['Use asyncio for I/O', 'Avoid blocking calls'],
            'execution_time_minutes': 15
        }

        await session_manager.save_task_results(session_id, task_id, task_results)

        updated_session = await session_manager.get_session(session_id)
        assert task_id in updated_session['task_ids']
        assert updated_session['total_focus_minutes'] == 15
        assert len(updated_session['completed_tasks']) == 1
        print("✅ Task results saved successfully")

        # Test 3: Pause and resume
        print("\n3️⃣  Testing pause/resume functionality...")
        await session_manager.pause_session(session_id)

        paused_session = await session_manager.get_session(session_id)
        assert paused_session['attention_state'] == 'paused'
        assert paused_session['interruptions'] == 1
        assert len(paused_session['break_history']) == 1

        # Wait a moment, then resume
        await asyncio.sleep(1)
        resumed_session = await session_manager.resume_session(session_id)

        assert resumed_session['attention_state'] == 'resuming'
        assert resumed_session['context_switches'] == 1
        assert len(resumed_session['break_history']) == 2  # pause + resume
        print("✅ Pause/resume working correctly")

        # Test 4: Context reminder
        print("\n4️⃣  Testing context reminders...")
        reminder = await session_manager.get_context_reminder(session_id)
        assert "Test research on Python async patterns" in reminder
        assert "15 minutes" in reminder
        print(f"✅ Context reminder: {reminder[:100]}...")

        # Test 5: Session statistics
        print("\n5️⃣  Testing session statistics...")
        stats = session_manager.get_session_stats(session_id)
        assert stats['total_tasks'] == 1
        assert stats['completed_tasks'] == 1
        assert stats['total_focus_minutes'] == 15
        assert stats['interruptions'] == 1
        assert stats['productivity_score'] > 0
        print(f"✅ Session stats: {stats}")

        # Test 6: File persistence
        print("\n6️⃣  Testing file persistence...")
        session_file = Path(temp_dir) / f"{session_id}.json"
        assert session_file.exists()

        with open(session_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data['session_id'] == session_id
        assert saved_data['total_focus_minutes'] == 15
        print("✅ Session data persisted to file")

        # Test 7: Session restoration
        print("\n7️⃣  Testing session restoration...")

        # Create new session manager (simulating restart)
        new_session_manager = SessionManager(storage_path=temp_dir)
        await new_session_manager.initialize()

        # Check if session was restored
        restored_session = await new_session_manager.get_session(session_id)
        assert restored_session is not None
        assert restored_session['session_id'] == session_id
        assert restored_session['total_focus_minutes'] == 15
        assert len(restored_session['completed_tasks']) == 1
        print("✅ Session restored successfully after restart")

        # Test 8: Auto-save functionality
        print("\n8️⃣  Testing auto-save...")

        # Modify session data
        original_session = await new_session_manager.get_session(session_id)
        original_session['test_field'] = 'auto_save_test'

        # Wait for auto-save interval
        print("⏳ Waiting for auto-save (31 seconds)...")
        await asyncio.sleep(31)

        # Check if changes were persisted
        with open(session_file, 'r') as f:
            auto_saved_data = json.load(f)

        assert 'test_field' in auto_saved_data
        print("✅ Auto-save working correctly")

        # Test 9: Session cleanup
        print("\n9️⃣  Testing session cleanup...")

        # Create an old session by modifying the timestamp
        old_session_id = str(uuid4())
        old_session = await new_session_manager.get_or_create_session(old_session_id)

        # Manually set old timestamp
        old_session['last_activity'] = '2023-01-01T00:00:00'
        old_session['created_at'] = '2023-01-01T00:00:00'
        await new_session_manager._save_session(old_session_id)

        # Run cleanup
        await new_session_manager.cleanup_old_sessions(days=1)

        # Check if old session was removed
        cleaned_session = await new_session_manager.get_session(old_session_id)
        assert cleaned_session is None
        print("✅ Old session cleanup working")

        # Test 10: Memory usage and performance
        print("\n🔟 Testing performance with multiple sessions...")

        session_ids = []
        start_time = time.time()

        # Create 50 sessions quickly
        for i in range(50):
            test_session_id = str(uuid4())
            await new_session_manager.get_or_create_session(test_session_id)
            session_ids.append(test_session_id)

        creation_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        for session_id in session_ids:
            await new_session_manager.get_session(session_id)

        retrieval_time = time.time() - start_time

        print(f"✅ Created 50 sessions in {creation_time:.2f}s")
        print(f"✅ Retrieved 50 sessions in {retrieval_time:.2f}s")
        print(f"✅ Total sessions in memory: {len(new_session_manager.sessions)}")

        print("\n" + "=" * 50)
        print("🎉 ALL SESSION PERSISTENCE TESTS PASSED!")
        print(f"📊 Final session count: {len(new_session_manager.sessions)}")

        # Cleanup test sessions
        await new_session_manager.save_all_sessions()


async def test_adhd_features():
    """Test ADHD-specific features"""
    print("\n🧠 Testing ADHD-Optimized Features")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        session_manager = SessionManager(storage_path=temp_dir)
        await session_manager.initialize()

        session_id = str(uuid4())
        session = await session_manager.get_or_create_session(session_id)

        # Test focus time tracking
        print("\n1️⃣  Testing focus time tracking...")

        # Simulate 25 minute focus session
        task_results = {'execution_time_minutes': 25}
        await session_manager.save_task_results(session_id, str(uuid4()), task_results)

        stats = session_manager.get_session_stats(session_id)
        assert stats['total_focus_minutes'] == 25
        print("✅ Focus time tracked correctly")

        # Test break recommendations
        print("\n2️⃣  Testing break recommendations...")

        reminder = await session_manager.get_context_reminder(session_id)
        # After 25 minutes, should suggest a break
        print(f"📝 Reminder after 25 min focus: {reminder}")

        # Test productivity scoring
        print("\n3️⃣  Testing ADHD productivity scoring...")

        # Take a break (ADHD-friendly behavior)
        await session_manager.pause_session(session_id)
        await session_manager.resume_session(session_id)

        stats = session_manager.get_session_stats(session_id)
        productivity_score = stats['productivity_score']

        print(f"📊 Productivity score with break: {productivity_score}")
        assert productivity_score > 0
        print("✅ ADHD productivity scoring working")

        # Test attention state transitions
        print("\n4️⃣  Testing attention state transitions...")

        session = await session_manager.get_session(session_id)
        states = ['fresh', 'paused', 'resuming']

        current_state = session['attention_state']
        assert current_state in states
        print(f"✅ Attention state: {current_state}")

        print("\n🎉 ALL ADHD FEATURES WORKING!")


if __name__ == "__main__":
    print("🚀 Starting GPT-Researcher Session Persistence Tests")

    try:
        # Run main persistence tests
        asyncio.run(test_session_persistence())

        # Run ADHD feature tests
        asyncio.run(test_adhd_features())

        print("\n" + "=" * 60)
        print("🏆 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅ Session persistence system is fully operational")
        print("✅ ADHD features are working correctly")
        print("✅ Auto-save, restoration, and cleanup all functional")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)