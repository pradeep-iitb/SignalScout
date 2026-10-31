from typing import List, Optional
from datetime import datetime
from backend.models.entities import ToolResult
from backend.services.crustdata import search_people, enrich_person

async def tool_person_search(company_domain: str, title_keywords: Optional[List[str]] = None, limit: int = 5) -> ToolResult:
    try:
        res = await search_people(company_domain=company_domain, title_keywords=title_keywords, limit=limit)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata"),
            query=f"person_search: {company_domain} [titles: {title_keywords}]",
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

async def tool_person_enrich(person_id: str) -> ToolResult:
    try:
        res = await enrich_person(person_id=person_id)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata"),
            query=f"person_enrich: {person_id}",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata",
            query=person_id,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )
