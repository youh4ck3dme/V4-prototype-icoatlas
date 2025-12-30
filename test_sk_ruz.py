import httpx
import asyncio
from backend.app.services.ruz_service import RuzService

async def test_sk_lookup():
    ico = "00686930" # Tatra banka, a.s.
    async with httpx.AsyncClient() as client:
        service = RuzService(client)
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
    asyncio.run(test_sk_lookup())
