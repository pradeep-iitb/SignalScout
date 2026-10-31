from typing import List, Dict, Any, Optional
from backend.services.crustdata.client import crustdata_client


async def search_people(company_domain: str, title_keywords: Optional[List[str]] = None, limit: int = 5) -> Dict[str, Any]:
    payload = {
        "company_domain": company_domain,
        "titles": title_keywords or ["Founder", "Co-Founder", "CEO", "CTO", "Head of AI", "VP Engineering"],
        "limit": limit,
    }
    result = await crustdata_client.execute_request("POST", "/people/search", json_body=payload)
    data = result.get("data")
    if not data:
        return {"source": "crustdata_live", "people": [], "error": result.get("error")}
    people = data.get("people", data) if isinstance(data, dict) else data
    if not isinstance(people, list):
        people = []
    return {"source": "crustdata_live", "people": people}


async def enrich_person(person_id: str) -> Dict[str, Any]:
    result = await crustdata_client.execute_request("POST", "/people/enrich", json_body={"person_id": person_id})
    data = result.get("data")
    return {"source": "crustdata_live", "profile": data or {}}
