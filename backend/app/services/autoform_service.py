import httpx
from typing import List, Dict, Any
from ..core.config import settings

class AutoformService:
    BASE_URL = "https://autoform.ekosystem.slovensko.digital/api/corporate_bodies/search"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def autocomplete(self, query: str) -> List[Dict[str, Any]]:
        # Check mock fallbacks first
        mock_results = self._get_mock_fallbacks(query)
        if mock_results:
            return mock_results

        # If no mock matched and we have a token, call the Autoform API
        if settings.AUTOFORM_API_TOKEN:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.AUTOFORM_API_TOKEN}",
                    "Accept": "application/json"
                }
                params = {"q": f"name:{query}", "limit": 10}
                
                resp = await self.client.get(self.BASE_URL, headers=headers, params=params, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    # Map autoform response to our standard format
                    return [
                        {
                            "id": item.get("cin"),  # IČO
                            "name": item.get("name"),
                            "address": item.get("formatted_address", ""),
                            "status": "AKTÍVNA" if item.get("status") == "active" else "ZANIKNUTÁ"
                        }
                        for item in data
                    ]
            except Exception as e:
                print(f"Autoform API error: {e}")
                
        # If API failed or no token, return empty if no mocks matched
        return []

    def _get_mock_fallbacks(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        mocks = [
            {"id": "88888888", "name": "Testovacia Firma, s.r.o.", "address": "Mlynské Nivy 1, Bratislava", "status": "AKTÍVNA"},
            {"id": "50158635", "name": "Slovensko.Digital", "address": "Staré Grunty 18, 841 04 Bratislava", "status": "AKTÍVNA"},
            {"id": "36241031", "name": "Websupport, s.r.o.", "address": "Karadžičova 12, 821 08 Bratislava", "status": "AKTÍVNA"},
            {"id": "31333532", "name": "ESET, spol. s r.o.", "address": "Einsteinova 24, 851 01 Bratislava", "status": "AKTÍVNA"},
            {"id": "45503249", "name": "Martinus, s.r.o.", "address": "Gorkého 4, 036 01 Martin", "status": "AKTÍVNA"},
            {"id": "35892030", "name": "Sygic a. s.", "address": "Mlynské nivy 16, 821 09 Bratislava", "status": "AKTÍVNA"},
        ]
        
        results = [m for m in mocks if query_lower in m["name"].lower() or query_lower in m["id"]]
        return results
