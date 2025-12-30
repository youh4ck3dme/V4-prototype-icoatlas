import asyncio
import sys
sys.path.insert(0, ".")
from backend.app.services.krs_playwright_service import KRSPlaywrightService

async def test_pl_playwright():
    krs = "14565"  # ORLEN S.A. without leading zeros
    print(f"Testing PL Playwright with KRS: {krs}")
    service = KRSPlaywrightService()
    try:
        company = await service.fetch_company(krs)
        print(f"✅ Success!")
        print(f"   Name: {company.name}")
        print(f"   Address: {company.address}")
        print(f"   Status: {company.status}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_pl_playwright())
