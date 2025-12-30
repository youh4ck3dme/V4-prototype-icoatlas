import httpx
import asyncio
from backend.app.services.nav_service import NAVService

async def test_hu_lookup():
    ico = "0110041145" # OTP Bank Nyrt.
    async with httpx.AsyncClient() as client:
        service = NAVService(client)
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
    asyncio.run(test_hu_lookup())
