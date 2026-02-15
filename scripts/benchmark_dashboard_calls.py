import asyncio
import time
from typing import Any, Dict, List

# Simulating the functions from app.py
async def get_cognitive_state(user_id: str) -> Dict[str, Any]:
    # Simulate network latency (average of 1.5s timeout or faster)
    await asyncio.sleep(0.5)
    return {
        "cognitive_state": {
            "energy": 0.65,
            "attention": 0.62,
            "load": 0.48,
            "status": "optimal",
            "recommendation": "Continue",
        },
        "source": "adhd-engine"
    }

async def get_tasks(limit: int) -> List[Dict[str, Any]]:
    # Simulate network latency
    await asyncio.sleep(0.5)
    return [{"id": "task-1", "title": "Test Task"}]

async def get_team_members() -> List[Dict[str, Any]]:
    # This one is currently just a fallback, so it's fast
    await asyncio.sleep(0.01)
    return [{"id": "1", "name": "Alice"}]

async def sequential_dashboard_snapshot(user_id: str, limit: int):
    start = time.perf_counter()

    cognitive_payload = await get_cognitive_state(user_id=user_id)
    tasks = await get_tasks(limit=limit)
    team_members = await get_team_members()

    end = time.perf_counter()
    return end - start

async def parallel_dashboard_snapshot(user_id: str, limit: int):
    start = time.perf_counter()

    # Using gather to run in parallel
    cognitive_payload, tasks, team_members = await asyncio.gather(
        get_cognitive_state(user_id=user_id),
        get_tasks(limit=limit),
        get_team_members()
    )

    end = time.perf_counter()
    return end - start

async def run_benchmark(iterations: int = 5):
    print(f"Running benchmark with {iterations} iterations...")

    seq_times = []
    for _ in range(iterations):
        t = await sequential_dashboard_snapshot("user1", 4)
        seq_times.append(t)

    par_times = []
    for _ in range(iterations):
        t = await parallel_dashboard_snapshot("user1", 4)
        par_times.append(t)

    avg_seq = sum(seq_times) / iterations
    avg_par = sum(par_times) / iterations

    print(f"\nResults:")
    print(f"Average Sequential Time: {avg_seq:.4f}s")
    print(f"Average Parallel Time:   {avg_par:.4f}s")
    print(f"Improvement:            {avg_seq - avg_par:.4f}s ({(avg_seq - avg_par) / avg_seq * 100:.2f}%)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
