import asyncio
from httpx import AsyncClient
from backend.app.services.ares_service import ARESService

async def main():
    ico = input("Enter IČO to lookup (e.g. 27074358): ").strip()
    async with AsyncClient() as client:
        service = ARESService(client)
        try:
            company = await service.fetch_company(ico)
            print("✅ Company found:")
            print(company.model_dump_json(indent=2))
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
