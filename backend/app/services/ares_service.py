from httpx import AsyncClient, HTTPStatusError, TimeoutException
from fastapi import HTTPException
from bs4 import BeautifulSoup  # only if needed for fallback, but JSON preferred
from typing import Optional
from ..models.company import Company

class ARESService:
    BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"

    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetch_company(self, ico: str) -> Company:
        url = f"{self.BASE_URL}/{ico}"
        try:
            resp = await self.client.get(url, timeout=10.0)
            resp.raise_for_status()
            with open("debug_ares.txt", "w") as f:
                f.write(resp.text)
            data = resp.json()
        except TimeoutException:
            raise HTTPException(status_code=504, detail="ARES request timed out")
        except HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"IČO {ico} not found")
            raise HTTPException(status_code=exc.response.status_code, detail="ARES API error")

        # map JSON fields into our Company model
        try:
            company = Company(
                ico=data["ico"],
                name=data.get("obchodniJmeno", ""),
                address=data.get("sidlo", {}).get("textovaAdresa", ""),
                status=data.get("seznamRegistraci", {}).get("stavZdrojeRos", "UNKNOWN")
            )
        except (KeyError, TypeError) as e:
            raise HTTPException(status_code=502, detail=f"Unexpected ARES response format: {e}")

        return company
