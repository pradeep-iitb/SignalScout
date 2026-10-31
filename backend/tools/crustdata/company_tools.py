from typing import List, Optional
from datetime import datetime
from backend.models.entities import ToolResult
from backend.services.crustdata import search_companies, identify_company, enrich_company

async def tool_company_search(query: str, geography: Optional[List[str]] = None, stage: Optional[List[str]] = None, limit: int = 50) -> ToolResult:
    try:
        res = await search_companies(query=query, geography=geography, stage=stage, limit=limit)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata"),
            query=f"search: {query} [geo: {geography}, stage: {stage}]",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata",
            query=query,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

async def tool_company_identify(query: str) -> ToolResult:
    try:
        res = await identify_company(name_or_domain=query)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata"),
            query=f"identify: {query}",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata",
            query=query,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

async def tool_company_enrich(domain: str, fields: Optional[List[str]] = None) -> ToolResult:
    try:
        res = await enrich_company(domain=domain, fields=fields)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata"),
            query=f"enrich: {domain}",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata",
            query=domain,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )
