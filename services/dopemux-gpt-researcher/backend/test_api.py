#!/usr/bin/env python3
"""
Test script for GPT-Researcher Phase 2 API
Tests all major endpoints and WebSocket functionality
"""

import asyncio
import json
import sys
from datetime import datetime

import httpx
import websockets


async def test_api():
    """Test the Phase 2 API endpoints"""

    base_url = "http://localhost:8000"

    print("🧪 Testing GPT-Researcher Phase 2 API")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        # 1. Test health endpoint
        print("\n1️⃣ Testing /health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Version: {data.get('version')}")
                print(f"   Orchestrator: {data.get('orchestrator')}")
                print(f"   Active tasks: {data.get('active_tasks')}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")

        # 2. Test status endpoint
        print("\n2️⃣ Testing /api/v1/status endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status check passed")
                print(f"   Capabilities: {len(data.get('capabilities', {}))} features")
                print(f"   ADHD features: {data.get('capabilities', {}).get('adhd_features', [])[:3]}...")
            else:
                print(f"❌ Status check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Status check error: {e}")

        # 3. Test research creation
        print("\n3️⃣ Testing POST /api/v1/research endpoint...")
        research_request = {
            "topic": "Python async best practices for ADHD developers",
            "research_type": "technology_evaluation",
            "depth": "balanced",
            "adhd_config": {
                "break_interval": 25,
                "focus_duration": 25,
                "notification_style": "gentle",
                "hyperfocus_protection": True
            },
            "max_sources": 5,
            "timeout_minutes": 25
        }

        try:
            response = await client.post(
                f"{base_url}/api/v1/research",
                json=research_request
            )
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                session_id = data.get('session_id')
                print(f"✅ Research task created")
                print(f"   Task ID: {task_id}")
                print(f"   Session ID: {session_id}")
                print(f"   Status: {data.get('status')}")
                print(f"   Estimated time: {data.get('estimated_time_minutes')} minutes")

                # Save for later tests
                test_task_id = task_id
                test_session_id = session_id

                # 4. Test task status
                print("\n4️⃣ Testing GET /api/v1/research/{task_id} endpoint...")
                await asyncio.sleep(2)  # Wait a bit for task to start

                response = await client.get(f"{base_url}/api/v1/research/{test_task_id}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Task status retrieved")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Progress: {data.get('progress')}%")
                else:
                    print(f"❌ Task status failed: {response.status_code}")

                # 5. Test session info
                print("\n5️⃣ Testing GET /api/v1/sessions/{session_id} endpoint...")
                response = await client.get(f"{base_url}/api/v1/sessions/{test_session_id}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Session info retrieved")
                    print(f"   Task count: {len(data.get('task_ids', []))}")
                    print(f"   Attention state: {data.get('attention_state')}")
                    print(f"   Focus time: {data.get('total_focus_minutes')} minutes")
                else:
                    print(f"❌ Session info failed: {response.status_code}")

                # 6. Test session pause
                print("\n6️⃣ Testing POST /api/v1/sessions/{session_id}/pause endpoint...")
                response = await client.post(f"{base_url}/api/v1/sessions/{test_session_id}/pause")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Session paused")
                    print(f"   {data.get('tip')}")
                else:
                    print(f"❌ Session pause failed: {response.status_code}")

                # 7. Test session resume
                print("\n7️⃣ Testing POST /api/v1/sessions/{session_id}/resume endpoint...")
                await asyncio.sleep(2)  # Simulate break
                response = await client.post(f"{base_url}/api/v1/sessions/{test_session_id}/resume")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Session resumed")
                    print(f"   Context: {data.get('context_reminder')}")
                    print(f"   {data.get('tip')}")
                else:
                    print(f"❌ Session resume failed: {response.status_code}")

            else:
                print(f"❌ Research creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                test_task_id = None
                test_session_id = None

        except Exception as e:
            print(f"❌ Research creation error: {e}")
            test_task_id = None


async def test_websocket():
    """Test WebSocket functionality"""

    print("\n8️⃣ Testing WebSocket connection...")

    # Create a test task first
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/research",
            json={
                "topic": "WebSocket test",
                "research_type": "feature_research",
                "depth": "shallow"
            }
        )

        if response.status_code != 200:
            print("❌ Could not create test task for WebSocket")
            return

        task_id = response.json().get('task_id')

    # Test WebSocket
    try:
        uri = f"ws://localhost:8000/ws/{task_id}"
        async with websockets.connect(uri) as websocket:
            print(f"✅ WebSocket connected for task {task_id}")

            # Receive a few messages
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    if data.get('type') == 'connected':
                        print(f"   Connected: {data.get('message')}")
                    elif data.get('type') == 'progress':
                        print(f"   Progress: {data.get('progress')}% - {data.get('stage')}")
                        if data.get('break_suggested'):
                            print(f"   💡 Break suggested!")
                    elif data.get('type') == 'completed':
                        print(f"   ✅ Task completed!")
                        break
                    elif data.get('type') == 'error':
                        print(f"   ❌ Error: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    print("   ⏱️ WebSocket timeout (normal for test)")
                    break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")


async def main():
    """Main test runner"""

    print("\n" + "=" * 50)
    print("🚀 GPT-Researcher Phase 2 API Test Suite")
    print("=" * 50)

    # Check if API is running
    print("\n📡 Checking if API is running...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=2.0)
            if response.status_code == 200:
                print("✅ API is running!")
            else:
                print("⚠️ API returned unexpected status")
    except:
        print("❌ API is not running. Please start it with:")
        print("   cd backend && ./start_api.sh")
        return

    # Run tests
    await test_api()
    await test_websocket()

    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())