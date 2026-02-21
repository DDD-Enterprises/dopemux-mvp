#!/usr/bin/env python3
"""
LeanTime API Test Script
Quick verification tool for when API key is properly activated
"""

import os
import requests
import json

# API Configuration
LEANTIME_API_URL = "http://localhost:8080"
LEANTIME_API_TOKEN = os.getenv("LEANTIME_API_TOKEN", "REPLACE_WITH_LEANTIME_API_TOKEN")

def test_leantime_api():
    """Test LeanTime API connectivity and basic endpoints"""

    headers = {
        "Authorization": f"Bearer {LEANTIME_API_TOKEN}",
        "Content-Type": "application/json"
    }

    print("🔧 Testing LeanTime API Integration...")
    print(f"📍 URL: {LEANTIME_API_URL}")
    print(f"🔑 Token: {LEANTIME_API_TOKEN[:20]}...")
    print()

    # Test endpoints
    endpoints = [
        "/api/projects",
        "/api/users",
        "/api/tasks",
        "/api/milestones"
    ]

    for endpoint in endpoints:
        try:
            url = f"{LEANTIME_API_URL}{endpoint}"
            response = requests.get(url, headers=headers, timeout=10)

            print(f"🌐 {endpoint}")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS: {len(data) if isinstance(data, list) else 'Data received'}")
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED: API key needs activation in LeanTime")
            else:
                print(f"   ⚠️  Response: {response.text[:100]}")
            print()

        except requests.exceptions.RequestException as e:
            print(f"   ❌ CONNECTION ERROR: {e}")
            print()

    print("🎯 Next Steps:")
    print("1. Verify API key is ACTIVE in LeanTime web interface")
    print("2. Check API key has PROJECT permissions")
    print("3. Ensure API key is associated with your user account")
    print("4. Re-run this script when API key is activated")

if __name__ == "__main__":
    test_leantime_api()
