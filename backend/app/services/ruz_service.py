import httpx
import re
from bs4 import BeautifulSoup
from fastapi import HTTPException
from ..models.company import Company

class RuzService:
    BASE_URL = "https://www.registeruz.sk/cruz-public"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def fetch_company(self, ico: str) -> Company:
        if not re.match(r'^\d{8}$', ico):
            raise HTTPException(status_code=400, detail="IČO musí mať 8 číslic")

        try:
            # 1. Resolve ID via Suggestion API
            internal_id = await self._resolve_id(ico)
            if not internal_id:
                 # Fallback to direct search message or raise not found
                 raise HTTPException(status_code=404, detail=f"IČO {ico} nebolo nájdené v RÚZ")

            # 2. Fetch Detail HTML
            html = await self._fetch_detail_html(internal_id)
            if not html:
                raise HTTPException(status_code=502, detail="Nepodarilo sa stiahnuť detail firmy z RÚZ")

            # 3. Parse HTML
            data = self._parse_html(html, ico)

            return Company(
                ico=ico,
                name=data['name'] or f"Firma {ico}",
                address=data['address'] or "Neznáma adresa",
                status=data['status'] or "AKTÍVNA",
                raw_data=data['raw_data']
            )

        except HTTPException:
            raise
        except Exception as e:
            print(f"RUZ Scraper error: {e}")
            raise HTTPException(status_code=502, detail=f"Chyba pri spracovaní dát z RÚZ: {str(e)}")

    async def _resolve_id(self, ico: str) -> str | None:
        url = f"{self.BASE_URL}/domain/suggestion/search"
        params = {"query": ico}
        headers = {"Accept": "application/json"}
        
        try:
            resp = await self.client.get(url, params=params, headers=headers, timeout=10.0)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                return None
                
            # Usually the first entry is the most relevant
            return str(data[0].get("id"))
        except Exception:
            return None

    async def _fetch_detail_html(self, internal_id: str) -> str | None:
        url = f"{self.BASE_URL}/domain/accountingentity/show/{internal_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = await self.client.get(url, headers=headers, timeout=10.0)
            return resp.text if resp.status_code == 200 else None
        except Exception:
            return None

    def _parse_html(self, html: str, ico: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        
        # 1. Name - using h3.fs-24 as suggested
        name = None
        title_node = soup.select_one("h3.fs-24")
        if title_node:
            name = title_node.get_text(strip=True)

        # 2. Address - logic for div.fs-14 containing "Adresa:" or "Sídlo:"
        address = None
        sidlo_div = None
        for div in soup.select("div.fs-14"):
            txt = div.get_text()
            if "Adresa:" in txt or "Sídlo:" in txt:
                sidlo_div = div
                break
        
        if sidlo_div:
            span = sidlo_div.select_one("span.fs-16")
            if span:
                # Get text with newlines preservation by joining stripped strings
                parts = [p.strip() for p in span.stripped_strings]
                address = ", ".join(parts)

        # 3. Registration Date
        reg_date = None
        for div in soup.select("div.fs-14"):
            if "Dátum vzniku:" in div.get_text():
                span = div.select_one("span.fs-16")
                if span:
                    reg_date = span.get_text(strip=True)
                    break

        # 4. Status extraction (lightweight check)
        status = "AKTÍVNA"
        if "zaniknutá" in html.lower() or "zrušená" in html.lower():
            status = "ZANIKNUTÁ"
        elif "v likvidácii" in html.lower():
            status = "V LIKVIDÁCII"

        return {
            "name": name,
            "address": address,
            "status": status,
            "raw_data": {
                "registration_date": reg_date,
                "source": "RÚZ Hybrid Scraper"
            }
        }
