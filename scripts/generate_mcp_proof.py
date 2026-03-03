import asyncio
from pathlib import Path
from dopemux.mcp.gate import DiscoveryGate

async def main():
    project_root = Path.cwd()
    run_id = "TP-MCP-MULTIINSTANCE-GATE-0001"
    
    print(f"Running Discovery Gate for {project_root}...")
    gate = DiscoveryGate(project_root, run_id=run_id)
    
    # We run it and it will generate reports in proof/RUN_ID/
    passed = await gate.run()
    
    print(f"Gate result: {'PASS' if passed else 'BLOCK'}")
    if not passed:
        gate.print_block_report()

if __name__ == "__main__":
    asyncio.run(main())
