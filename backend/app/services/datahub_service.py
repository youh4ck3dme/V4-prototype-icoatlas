import httpx
import logging
import asyncio
from typing import List, Dict

logger = logging.getLogger(__name__)

class DatahubService:
    BASE_URL = "https://datahub.ekosystem.slovensko.digital/api/data"

    @classmethod
    async def check_debts(cls, ico: str) -> List[Dict]:
        """
        Asynchronously checks for state debts in Sociálna poisťovňa and VšZP.
        Returns a list of identified debt dictionaries.
        """
        debts = []

        # Mock interceptor for our test graph ID
        if ico == "88888888":
            return [
                {
                    "institution": "Sociálna Poisťovňa",
                    "amount": 785.98,
                    "published_on": "2024-01-15",
                    "type": "debtor"
                },
                {
                    "institution": "Všeobecná zdravotná poisťovňa",
                    "amount": 1205.50,
                    "published_on": "2024-02-20",
                    "type": "health_care_claim"
                }
            ]

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Concurrent requests for SP and VSZP
                sp_task = client.get(f"{cls.BASE_URL}/socpoist/debtors?cin={ico}")
                vszp_task = client.get(f"{cls.BASE_URL}/vszp/debtors?cin={ico}")
                
                responses = await asyncio.gather(sp_task, vszp_task, return_exceptions=True)
                
                sp_res, vszp_res = responses

                # Process Sociálna Poisťovňa
                if isinstance(sp_res, httpx.Response) and sp_res.status_code == 200:
                    data = sp_res.json()
                    # If endpoint returns a list of matched records
                    if isinstance(data, list) and len(data) > 0:
                        for record in data:
                            amount = float(record.get("amount", 0))
                            if amount > 5.0: # Tolerance filter
                                debts.append({
                                    "institution": "Sociálna Poisťovňa",
                                    "amount": amount,
                                    "published_on": record.get("published_on", "Neznáme"),
                                    "type": "debtor"
                                })

                # Process VšZP
                if isinstance(vszp_res, httpx.Response) and vszp_res.status_code == 200:
                    data = vszp_res.json()
                    if isinstance(data, list) and len(data) > 0:
                        for record in data:
                            amount = float(record.get("amount", 0))
                            if amount > 5.0:
                                debts.append({
                                    "institution": "Všeobecná zdravotná poisťovňa",
                                    "amount": amount,
                                    "published_on": record.get("published_on", "Neznáme"),
                                    "type": record.get("health_care_claim", "debtor")
                                })

        except Exception as e:
            logger.error(f"Error fetching datahub debts for {ico}: {e}")

        return debts

    @classmethod
    async def fetch_ubo_partners(cls, datahub_url: str) -> List[Dict]:
        """
        Fetches konecni uzivatelia vyhod (UBO) from RPVS via Datahub API.
        """
        if "88888888" in datahub_url:
            return [
                {
                    "formatted_name": "Kráľovský Majiteľ",
                    "address": "Zlatá 1, Bratislava",
                    "share": "Konečný užívateľ výhod (UBO) - 100% podiel",
                    "beneficiary": True
                }
            ]

        from ..core.config import settings
        if not settings.DATAHUB_API_TOKEN:
            return []

        ubos = []
        try:
            headers = {
                "Authorization": f"Token token={settings.DATAHUB_API_TOKEN}",
                "Accept": "application/json"
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(datahub_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    
                    raw_beneficiaries = []
                    if "beneficiaries" in data and isinstance(data["beneficiaries"], list):
                        raw_beneficiaries = data["beneficiaries"]
                    elif "public_sector_partner" in data and isinstance(data["public_sector_partner"], dict):
                        psp = data["public_sector_partner"]
                        if "beneficiaries" in psp and isinstance(psp["beneficiaries"], list):
                            raw_beneficiaries = psp["beneficiaries"]
                            
                    for b in raw_beneficiaries:
                        name = b.get("formatted_name")
                        if not name:
                            first = b.get("first_name", "") or ""
                            last = b.get("last_name", "") or ""
                            name = f"{first} {last}".strip()
                        
                        addr = b.get("formatted_address") or b.get("address") or ""
                        share = b.get("share") or ""
                        
                        ubos.append({
                            "formatted_name": name,
                            "address": addr,
                            "share": share,
                            "beneficiary": True
                        })
        except Exception as e:
            logger.error(f"Error fetching UBO partners from {datahub_url}: {e}")

        return ubos
