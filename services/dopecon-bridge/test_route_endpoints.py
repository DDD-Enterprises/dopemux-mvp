"""
Test script for Two-Plane routing endpoints
"""
import asyncio
import httpx

async def test_routes():
    """Test the new /route/pm and /route/cognitive endpoints"""

    async with httpx.AsyncClient(base_url="http://localhost:3016", timeout=30.0) as client:

        # Test 1: Route to PM plane (get_tasks query)
        print("\n=== Test 1: Cognitive → PM (get_tasks) ===")
        try:
            response = await client.post(
                "/route/pm",
                json={
                    "source": "cognitive",
                    "operation": "get_tasks",
                    "data": {"status": "TODO"},
                    "requester": "TwoPlaneOrchestrator"
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: Route to Cognitive plane (get_complexity query)
        print("\n=== Test 2: PM → Cognitive (get_complexity) ===")
        try:
            response = await client.post(
                "/route/cognitive",
                json={
                    "source": "pm",
                    "operation": "get_complexity",
                    "data": {"file": "auth.py", "function": "login"},
                    "requester": "Leantime"
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 3: Check available routes via OpenAPI
        print("\n=== Test 3: Check OpenAPI Spec ===")
        try:
            response = await client.get("/openapi.json")
            spec = response.json()
            routes_with_route = [p for p in spec.get("paths", {}).keys() if "route" in p]
            print(f"Total API paths: {len(spec.get('paths', {}))}")
            print(f"Paths with 'route': {routes_with_route}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_routes())
