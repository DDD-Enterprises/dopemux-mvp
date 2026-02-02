#!/usr/bin/env python3
"""
Test ConPort Integration
Quick validation that F001/F002 can connect to ConPort database
"""

import asyncio
from pathlib import Path

async def test_conport_connection():
    """Test ConPort database connection"""
    print("=" * 70)
    print("TEST: ConPort Database Connection")
    print("=" * 70)

    try:
        from conport_db_client import ConPortDBClient

        client = ConPortDBClient()
        await client.connect()

        print("✅ Connected to ConPort database")
        print(f"   Host: {client.host}:{client.port}")
        print(f"   Database: {client.database}")
        print(f"   User: {client.user}")

        # Test query
        workspace_id = "/Users/hue/code/dopemux-mvp"
        context = await client.get_active_context(workspace_id)

        if context:
            print(f"\n✅ Active context found:")
            print(f"   Workspace: {context.get('workspace_id')}")
            print(f"   Session: {context.get('session_id')}")
            print(f"   Focus: {context.get('active_context')}")
        else:
            print("\n⚠️  No active context (this is okay)")

        # Test multi-session query
        sessions = await client.get_all_active_sessions(workspace_id)
        print(f"\n✅ Active sessions query:")
        print(f"   Count: {len(sessions)}")

        await client.disconnect()
        print("\n✅ ConPort integration test PASSED\n")
        return True

    except Exception as e:
        print(f"\n❌ ConPort integration test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run integration tests"""
    print("\n" + "=" * 70)
    print("F001/F002 CONPORT INTEGRATION TEST")
    print("=" * 70 + "\n")

    success = await test_conport_connection()

    if success:
        print("=" * 70)
        print("🎉 CONPORT INTEGRATION READY!")
        print("=" * 70)
        print("\n✅ F001/F002 can now use real ConPort data")
        print("\nNext: Test F002 multi-session and F001 enhanced detection")
    else:
        print("=" * 70)
        print("❌ Integration needs debugging")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
