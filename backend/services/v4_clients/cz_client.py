import asyncio
import httpx
from typing import Dict
from .models import RateLimitError, V4APIError, NotFoundError


class CZARESClient:
    """Klient pre český ARES v2"""

    BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"

    async def _fetch_with_retry(self, url: str, json_data: Dict = None, max_retries: int = 3) -> Dict:
        """Fetch with exponential backoff"""
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=json_data, headers={"Content-Type": "application/json"})
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise RateLimitError(retry_after)
                    response.raise_for_status()
                    return response.json()
            except RateLimitError as e:
                wait_time = e.retry_after * (2 ** attempt)
                await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundError(f"Company not found")
                raise V4APIError(f"HTTP error: {e}")
            except Exception as e:
                raise V4APIError(f"Request failed: {e}")
        raise V4APIError("Max retries exceeded")

    async def search_by_ico(self, ico: str) -> Dict:
        """Vyhľadanie podľa IČO"""
        url = f"{self.BASE_URL}/ekonomicke-subjekty/vyhledat"
        json_data = {"ico": ico}
        return await self._fetch_with_retry(url, json_data)

    async def search_by_name(self, name: str, limit: int = 10) -> Dict:
        """Vyhľadanie podľa názvu"""
        url = f"{self.BASE_URL}/ekonomicke-subjekty/vyhledat"
        json_data = {"obchodniJmeno": name, "pocet": limit}
        return await self._fetch_with_retry(url, json_data)