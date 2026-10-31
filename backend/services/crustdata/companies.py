from typing import List, Dict, Any, Optional
from backend.services.crustdata.client import crustdata_client


async def search_companies(query: str, geography: Optional[List[str]] = None, stage: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
    payload = {
        "query": query,
        "filters": [{"field": "hq_country", "operator": "in", "value": geography or []}],
        "stages": stage or [],
        "limit": min(limit, 50),
    }
    result = await crustdata_client.execute_request("POST", "/screener/company", json_body=payload)
    data = result.get("data")
    if not data:
        return {"source": "crustdata_live", "companies": [], "total_count": 0, "error": result.get("error")}
    companies = data.get("companies", data) if isinstance(data, dict) else data
    if not isinstance(companies, list):
        companies = []
    return {"source": "crustdata_live", "companies": companies, "total_count": len(companies)}


async def identify_company(name_or_domain: str) -> Dict[str, Any]:
    target = name_or_domain.lower().replace("https://", "").replace("http://", "").strip("/ ")
    payload = {"domains": [target]} if "." in target else {"names": [name_or_domain]}
    result = await crustdata_client.execute_request("POST", "/company/identify", json_body=payload)
    data = result.get("data")
    if not isinstance(data, list) or not data:
        return {"source": "crustdata_live", "entity": None, "error": result.get("error") or "No match returned"}
    match = (data[0].get("matches") or [None])[0]
    if not match:
        return {"source": "crustdata_live", "entity": None, "error": "No matching entity found"}
    company_data = match.get("company_data", {})
    basic = company_data.get("basic_info", {})
    return {
        "source": "crustdata_live",
        "entity": {
            "company_id": str(basic.get("crustdata_company_id") or company_data.get("crustdata_company_id") or target),
            "canonical_name": basic.get("name") or name_or_domain,
            "domain": basic.get("primary_domain") or target,
            "legal_name": basic.get("legal_name") or basic.get("name"),
            "resolution_confidence": match.get("confidence_score"),
            "raw": company_data,
        },
    }


async def enrich_company(domain: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").strip("/ ")
    payload = {"domains": [clean_domain], "fields": fields or ["basic_info", "headcount", "funding"]}
    result = await crustdata_client.execute_request("POST", "/company/enrich", json_body=payload)
    data = result.get("data")
    if not isinstance(data, list) or not data:
        return {"source": "crustdata_live", "profile": None, "error": result.get("error") or "No enrichment data"}
    match = (data[0].get("matches") or [None])[0]
    if not match:
        return {"source": "crustdata_live", "profile": None, "error": "No match found in enrichment"}
    company_data = match.get("company_data", {})
    basic = company_data.get("basic_info", {})
    headcount = company_data.get("headcount", {})
    return {
        "source": "crustdata_live",
        "profile": {
            "company_id": str(basic.get("crustdata_company_id") or company_data.get("crustdata_company_id") or clean_domain),
            "name": basic.get("name") or clean_domain.split(".")[0].title(),
            "domain": basic.get("primary_domain") or clean_domain,
            "description": basic.get("description", ""),
            "headquarter": basic.get("hq_country", ""),
            "employee_count": headcount.get("employee_count", 0),
            "raw_headcount": headcount,
            "raw": company_data,
        },
    }
