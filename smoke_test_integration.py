import asyncio
import json
from pathlib import Path
from src.dopemux.adhd.rte_adapter import RTEAdapter

async def run_smoke_test():
    print("🚀 Starting Phase 5 Smoke Test: RTE -> ConPort KG")
    
    adapter = RTEAdapter(Path("."))
    
    try:
        # 1. Read RTE Truth
        print("📥 Step 1: Reading RTE Truth artifact...")
        truth = adapter.get_latest_truth()
        print(f"✅ Truth artifact loaded (Generated at: {truth.get('generated_at')})")
        
        # 2. Map to Decision Payload
        print("🗺️ Step 2: Mapping to ConPort Decision payload...")
        payload = {
            "title": "RTE Integration Verified",
            "summary": f"Automated verification of RTE truth flow into ConPort KG.",
            "rationale": "Verify that the 2026 RTE architecture can successfully communicate with restored 2025 services.",
            "context": {
                "generated_at": truth.get("generated_at"),
                "phases": truth.get("phases", []),
                "source": "RTE_SMOKE_TEST"
            },
            "workspace_id": "dopemux-mvp-smoke-test"
        }
        
        # 3. Write to ConPort
        print("📤 Step 3: Writing to ConPort (localhost:3004/api/decisions)...")
        result = await adapter.write_decision_to_conport(payload)
        
        if result.get("status") in ["success", "logged"]:
            decision_id = result.get("decision_id") or result.get("decision", {}).get("id")
            print(f"✅ Successfully logged decision to ConPort! (ID: {decision_id})")
            print("🏆 Integration Verified: Truth flowed from 2026 RTE to 2025 ConPort KG.")
        else:
            print(f"❌ ConPort returned unexpected response: {result}")
        
    except Exception as e:
        print(f"❌ Smoke Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
