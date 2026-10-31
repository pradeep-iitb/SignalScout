import asyncio
import httpx
import logging
from typing import Dict, Any, Optional
from backend.config.settings import settings

logger = logging.getLogger("crustdata.client")


class CrustDataClient:
    """Direct live Crustdata API client without mock fallbacks."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, api_version: Optional[str] = None):
        self.api_key = api_key or settings.CRUSTDATA_API_KEY
        self.base_url = (base_url or settings.CRUSTDATA_BASE_URL).rstrip("/")
        self.api_version = api_version or settings.CRUSTDATA_API_VERSION or "2025-11-01"

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    def get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "x-api-version": self.api_version}
        if self.api_key:
            auth_val = self.api_key if self.api_key.startswith("Bearer ") else f"Bearer {self.api_key}"
            headers["authorization"] = auth_val
        return headers

    async def execute_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        max_retries: int = 1,
    ) -> Dict[str, Any]:
        normalized_ep = "/" + endpoint.lstrip("/")
        if not self.is_live:
            return {"data": None, "error": "CRUSTDATA_API_KEY is not configured"}

        url = f"{self.base_url}{normalized_ep}"
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.get_headers(),
                        params=params,
                        json=json_body,
                    )
                if response.status_code == 200:
                    print(f"[CRUSTDATA LIVE 200] {normalized_ep}", flush=True)
                    return {"data": response.json(), "error": None}
                if response.status_code == 429 and attempt < max_retries:
                    await asyncio.sleep(1.0)
                    continue

                error_msg = f"HTTP {response.status_code}: {response.text[:150]}"
                print(f"[CRUSTDATA LIVE {response.status_code}] {normalized_ep}", flush=True)
                return {"data": None, "error": error_msg}

            except Exception as error:
                print(f"[CRUSTDATA EXCEPTION] {normalized_ep}: {error}", flush=True)
                return {"data": None, "error": str(error)}

        return {"data": None, "error": "Max retries exceeded"}


crustdata_client = CrustDataClient()
