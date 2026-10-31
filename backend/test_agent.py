import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.storage import storage
from backend.agent.graph import run_investigation

async def main():
    inv_id = "test_verify_fast"
    thesis = "Find ten Indian B2B software companies founded since 2023 whose team grew by half in the last six months, and tell me who founded each and what they did before"
    storage.create(inv_id, thesis)
    print("Starting fast investigation test...")
    res = await run_investigation(inv_id, thesis)
    print("Finished! Status:", res.get("status"))
    print("Discovered candidates:", len(res.get("candidate_companies", [])))
    print("Ranked candidates:", len(res.get("ranked_candidates", [])))
    print("Investment memos:", len(res.get("investment_memos", [])))
    for c in res.get("ranked_candidates", [])[:3]:
        print(f"  #{c['rank']} {c['name']} - Score: {c['overall_score']}, Confidence: {c['confidence']}%")

if __name__ == "__main__":
    asyncio.run(main())
