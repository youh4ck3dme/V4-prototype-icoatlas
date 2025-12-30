import asyncio
from httpx import AsyncClient
from backend.app.services.orsr_service import ORSRService

async def main():
    ico = input("Enter Slovak IČO to lookup (e.g. 35760892): ").strip()
    async with AsyncClient() as client:
        service = ORSRService(client)
        try:
            company = await service.fetch_company(ico)
            print("✅ Company found:")
            print(company.model_dump_json(indent=2))
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
