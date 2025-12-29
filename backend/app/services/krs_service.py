from httpx import AsyncClient, HTTPStatusError, TimeoutException
from fastapi import HTTPException
from ..models.company import Company

class KRSService:
    BASE_URL = "https://api-krs.ms.gov.pl/api/krs/OdpisPelny"

    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetch_company(self, krs_number: str) -> Company:
        url = f"{self.BASE_URL}/{krs_number}"
        params = {"rejestr": "P", "format": "json"}
        try:
            resp = await self.client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            import json
            with open("debug_krs.json", "w") as f:
                json.dump(data, f, indent=2)
        except TimeoutException:
            raise HTTPException(status_code=504, detail="KRS API request timed out")
        except HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"KRS {krs_number} not found")
            raise HTTPException(status_code=exc.response.status_code, detail="KRS API error")
        except ValueError:
            raise HTTPException(status_code=502, detail="Invalid JSON from KRS API")

        # Helper to get the current item from a list of records
        def get_current(items):
            if not isinstance(items, list):
                return items
            for item in items:
                if "nrWpisuWykr" not in item:
                    return item
            return items[-1] if items else {}

        # map JSON fields into our Company model
        try:
            dane = data.get("odpis", {}).get("dane", {})
            dzial1 = dane.get("dzial1", {})
            dane_podmiotu_list = dzial1.get("danePodmiotu", {})
            
            # These can be lists or dicts depending on API version/data
            dane_podmiotu = get_current(dane_podmiotu_list) if isinstance(dane_podmiotu_list, dict) else {}
            if not dane_podmiotu and isinstance(dane_podmiotu_list, dict):
                 dane_podmiotu = dane_podmiotu_list # Fallback

            # Based on debug_krs.json:
            # danePodmiotu has "nazwa" as list, etc.
            dp = dzial1.get("danePodmiotu", {})
            name_item = get_current(dp.get("nazwa", []))
            name = name_item.get("nazwa") if isinstance(name_item, dict) else ""
            
            ident_item = get_current(dp.get("identyfikatory", []))
            ident = ident_item.get("identyfikatory", {}) if isinstance(ident_item, dict) else {}
            
            siedziba_item = get_current(dzial1.get("siedzibaIAdres", {}).get("adres", []))
            adres = siedziba_item if isinstance(siedziba_item, dict) else {}

            company = Company(
                ico=ident.get("regon") or krs_number,
                name=name,
                address=", ".join(filter(None, [
                    adres.get("ulica"),
                    adres.get("nrDomu"),
                    adres.get("kodPocztowy"),
                    adres.get("miejscowosc")
                ])),
                status="ACTIVE"
            )
        except (KeyError, TypeError) as e:
            raise HTTPException(status_code=502, detail=f"Unexpected KRS response format: {e}")

        return company
