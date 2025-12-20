import httpx
from typing import Dict, List
from .models import V4APIError

class PLKRSClient:
    """Klient pre poľský KRS"""
    
    BASE_URL = "https://api-krs.ms.gov.pl/api/krs"
    
    async def get_current_extract(self, krs: str) -> Dict:
        """Aktuálny výpis"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/OdpisAktualny/{krs}",
                    params={"rejestr": "P", "format": "json"}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise V4APIError(f"KRS Request failed: {e}")

    async def get_full_history(self, krs: str) -> Dict:
        """Úplná história"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/OdpisPelny/{krs}",
                    params={"rejestr": "P", "format": "json"}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise V4APIError(f"KRS Request failed: {e}")

    async def get_daily_bulletin(self, date: str) -> Dict:
        """Denný bulletin zmien (YYYY-MM-DD)"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.BASE_URL}/Biuletyn/{date}")
                return response.json()
            except Exception as e:
                raise V4APIError(f"KRS Request failed: {e}")


class PLBialaListaClient:
    """Klient pre poľskú Bielu listinu VAT"""
    
    BASE_URL = "https://wl-api.mf.gov.pl"
    
    async def check_vat_status(self, nip: str, date: str) -> Dict:
        """Overenie VAT statusu"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/api/search/nip/{nip}",
                    params={"date": date}
                )
                return response.json()
            except Exception as e:
                raise V4APIError(f"Whitelist Request failed: {e}")

    async def verify_bank_account(self, nip: str, account: str, date: str) -> Dict:
        """Overenie bankového účtu"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/api/check/nip/{nip}/bank-account/{account}",
                    params={"date": date}
                )
                return response.json()
            except Exception as e:
                raise V4APIError(f"Whitelist Request failed: {e}")