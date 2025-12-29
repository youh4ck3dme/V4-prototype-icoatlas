from httpx import AsyncClient, HTTPStatusError, TimeoutException
from bs4 import BeautifulSoup
from fastapi import HTTPException
from typing import Optional
from ..models.company import Company
from urllib.parse import urlencode

class ORSRService:
    SEARCH_URL = "https://www.orsr.sk/hladaj_ico.asp"
    DETAIL_BASE = "https://www.orsr.sk"

    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetch_company(self, ico: str) -> Company:
        # Search via POST to be more reliable
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www.orsr.sk/search_ico.asp",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            # ORSR search form parameters
            data = {"ICO": ico, "SID": "0", "search": "1"}
            resp = await self.client.post(self.SEARCH_URL, data=data, headers=headers, timeout=10.0)
            resp.raise_for_status()
        except TimeoutException:
            raise HTTPException(status_code=504, detail="ORSR search timed out")
        except HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="ORSR search error")

        soup = BeautifulSoup(resp.text, "lxml")
        # Find the link to details (vypis.asp)
        link = soup.select_one("table.result a[href^='vypis.asp']")
        if not link:
             # Try direct access as fallback
             detail_url = f"{self.DETAIL_BASE}/vypis.asp?ID=0&SID=0&P=2&ICO={ico}"
             dresp = await self.client.get(detail_url, headers=headers, timeout=10.0)
             dsoup = BeautifulSoup(dresp.text, "lxml")
             if "Kritériám vyhľadávania nezodpovedá žiadny záznam" in dresp.text:
                 raise HTTPException(status_code=404, detail=f"IČO {ico} not found in ORSR")
        else:
             detail_url = self.DETAIL_BASE + "/" + link["href"].lstrip("/")
             dresp = await self.client.get(detail_url, headers=headers, timeout=10.0)
             dsoup = BeautifulSoup(dresp.text, "lxml")



        # Helper to extract the text from the cell next to a given label
        def extract(field_label: str) -> Optional[str]:
            label_cell = dsoup.find("td", string=lambda txt: txt and field_label in txt)
            if label_cell:
                val_cell = label_cell.find_next_sibling("td")
                return val_cell.get_text(strip=True) if val_cell else None
            return None

        name = extract("Obchodné meno") or extract("Názov")
        address_parts = [extract(lbl) for lbl in ("Sídlo", "Adresa")]
        address = ", ".join(filter(None, address_parts))
        status = extract("Stav zápisu") or "UNKNOWN"

        try:
            company = Company(
                ico=ico,
                name=name or "",
                address=address,
                status=status
            )
        except Exception:
            raise HTTPException(status_code=502, detail="Failed to parse ORSR data")

        return company
