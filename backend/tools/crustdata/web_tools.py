from datetime import datetime
from backend.models.entities import ToolResult
from backend.services.crustdata import search_web, fetch_page

async def tool_web_search(query: str, limit: int = 5) -> ToolResult:
    try:
        res = await search_web(query=query, limit=limit)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata_web"),
            query=f"web_search: {query}",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata_web",
            query=query,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

async def tool_web_fetch(url: str) -> ToolResult:
    try:
        res = await fetch_page(url=url)
        return ToolResult(
            success=True,
            data=res,
            source=res.get("source", "crustdata_web_fetch"),
            query=f"web_fetch: {url}",
            timestamp=datetime.utcnow().isoformat(),
            error=None
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data={},
            source="crustdata_web_fetch",
            query=url,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )
