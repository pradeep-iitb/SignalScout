from typing import List, Optional
from datetime import datetime
from backend.models.entities import ToolResult
from backend.services.crustdata import search_jobs

async def tool_job_search(company_domain: str, keywords: Optional[List[str]] = None, limit: int = 10) -> ToolResult:
    try:
        res = await search_jobs(company_domain=company_domain, keywords=keywords, limit=limit)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata"),
            query=f"job_search: {company_domain} [keywords: {keywords}]",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata",
            query=company_domain,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )
