import asyncio
import sys
sys.path.insert(0, ".")
from backend.app.services.nav_playwright_service import NAVPlaywrightService

async def test_hu_playwright():
    cegjegyzek = "01-10-041585"  # OTP Bank
    print(f"Testing HU Playwright with Cégjegyzékszám: {cegjegyzek}")
    service = NAVPlaywrightService()
    try:
        company = await service.fetch_company(cegjegyzek)
        print(f"✅ Success!")
        print(f"   Name: {company.name}")
        print(f"   Address: {company.address}")
        print(f"   Status: {company.status}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_hu_playwright())
