import asyncio
from httpx import AsyncClient
from backend.app.services.nav_service import NAVService

async def main():
    id_number = input("Enter Hungarian Cégjegyzékszám (e.g. 10537914): ").strip()
    async with AsyncClient() as client:
        service = NAVService(client)
        try:
            company = await service.fetch_company(id_number)
            print("✅ Company found:")
            print(company.model_dump_json(indent=2))
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
