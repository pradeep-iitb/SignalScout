from typing import Dict, Any
from backend.services.crustdata.client import crustdata_client


async def search_web(query: str, limit: int = 5) -> Dict[str, Any]:
    result = await crustdata_client.execute_request("POST", "/web/search", json_body={"query": query, "limit": limit})
    data = result.get("data")
    if not data:
        return {"source": "crustdata_live", "results": [], "error": result.get("error")}
    results = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results, list):
        results = []
    return {"source": "crustdata_live", "results": results}


async def fetch_page(url: str) -> Dict[str, Any]:
    result = await crustdata_client.execute_request("POST", "/web/fetch", json_body={"url": url})
    data = result.get("data")
    if not isinstance(data, dict):
        return {"source": "crustdata_live", "url": url, "title": "", "content": "", "error": result.get("error")}
    return {"source": "crustdata_live", "url": url, "title": data.get("title", ""), "content": data.get("text", "")}
