from httpx import AsyncClient, HTTPStatusError, TimeoutException
from fastapi import HTTPException
from bs4 import BeautifulSoup
from ..models.company import Company

class NAVService:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetch_company(self, id_number: str) -> Company:
        # Nemzeti Cegtar direct detail URL pattern: cegadat/0110041305
        clean_id = id_number.replace("-", "").replace(" ", "")
        url = f"https://www.nemzeticegtar.hu/cegadat/{clean_id}"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = await self.client.get(url, headers=headers, timeout=10.0)
            resp.raise_for_status()
            with open("debug_nav_detail.html", "w") as f:
                f.write(resp.text)
        except TimeoutException:
            raise HTTPException(status_code=504, detail="NAV search timed out")
        except HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="NAV API error")

        soup = BeautifulSoup(resp.text, "lxml")
        # Find the main info table - structure might differ in detail page
        # Based on usual Nemzeti Cegtar detail, look for name in H1 or specific spans
        name = ""
        name_tag = soup.find("h1")
        if name_tag:
            name = name_tag.get_text(strip=True)
            
        address = ""
        # Address is often next to a label "Székhely"
        addr_label = soup.find(string=lambda t: t and "Székhely" in t)
        if addr_label:
            addr_cell = addr_label.find_parent().find_next_sibling()
            if addr_cell:
                address = addr_cell.get_text(strip=True)

        status_tag = soup.find("span", {"class": "label-cegstatusz"})
        status = status_tag.get_text(strip=True) if status_tag else "UNKNOWN"

        return Company(
            ico=id_number,
            name=name,
            address=address,
            status=status
        )
