import asyncio
from httpx import AsyncClient
from backend.app.services.krs_service import KRSService

async def main():
    krs = input("Enter Polish KRS number to lookup (e.g. 0000006865): ").strip()
    async with AsyncClient() as client:
        service = KRSService(client)
        try:
            company = await service.fetch_company(krs)
            print("✅ Company found:")
            print(company.model_dump_json(indent=2))
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
