import asyncio
import httpx
from typing import Optional, Dict
from .models import RateLimitError, V4APIError, NotFoundError


class SKRPOClient:
    """Klient pre slovenský Register právnických osôb"""

    BASE_URL = "https://data.slovensko.sk/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def _fetch_with_retry(self, url: str, params: Dict = None, max_retries: int = 3) -> Dict:
        """Fetch with exponential backoff"""
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params, headers=self.headers)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        raise RateLimitError(retry_after)
                    response.raise_for_status()
                    return response.json()
            except RateLimitError as e:
                wait_time = e.retry_after * (2 ** attempt)
                await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundError(f"Company not found: {url}")
                raise V4APIError(f"HTTP error: {e}")
            except Exception as e:
                raise V4APIError(f"Request failed: {e}")
        raise V4APIError("Max retries exceeded")

    async def search_by_ico(self, ico: str) -> Dict:
        """Vyhľadanie podľa IČO"""
        url = f"{self.BASE_URL}/legal-subjects"
        params = {"ico": ico}
        return await self._fetch_with_retry(url, params)

    async def sync_changes(self, since: str, only_ids: bool = False) -> Dict:
        """Synchronizácia zmien od určitého času"""
        url = f"{self.BASE_URL}/sync"
        params = {"since": since}
        if only_ids:
            params["only_ids"] = "true"
        return await self._fetch_with_retry(url, params)

    async def search_by_name(self, name: str, limit: int = 10) -> Dict:
        """Vyhľadanie podľa názvu cez autoform API"""
        url = f"{self.BASE_URL}/autoform"
        params = {"q": name, "limit": limit}
        return await self._fetch_with_retry(url, params)