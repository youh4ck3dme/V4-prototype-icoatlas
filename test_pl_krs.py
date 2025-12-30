import httpx
import asyncio
from backend.app.services.krs_service import KRSService

async def test_pl_lookup():
    ico = "0000014565" # ORLEN S.A.
    async with httpx.AsyncClient() as client:
        service = KRSService(client)
        try:
            company = await service.fetch_company(ico)
            print(f"Success!")
            print(f"ICO: {company.ico}")
            print(f"Name: {company.name}")
            print(f"Address: {company.address}")
            print(f"Status: {company.status}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_pl_lookup())
