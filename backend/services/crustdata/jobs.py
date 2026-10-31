from typing import List, Dict, Any, Optional
from backend.services.crustdata.client import crustdata_client


async def search_jobs(company_domain: str, keywords: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    result = await crustdata_client.execute_request(
        "POST",
        "/jobs/search",
        json_body={"company_domain": company_domain, "keywords": keywords or [], "limit": limit},
    )
    data = result.get("data")
    if not data:
        return {"source": "crustdata_live", "jobs": [], "total_openings": 0, "error": result.get("error")}
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    if not isinstance(jobs, list):
        jobs = []
    return {"source": "crustdata_live", "jobs": jobs, "total_openings": len(jobs)}
