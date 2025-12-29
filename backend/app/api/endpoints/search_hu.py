from fastapi import APIRouter, Depends
from httpx import AsyncClient
from ...services.nav_service import NAVService
from ...models.company import Company

router = APIRouter()

async def get_httpx_client() -> AsyncClient:
    async with AsyncClient() as client:
        yield client

@router.get("/company/{id_number}", response_model=Company, summary="Lookup company by Cégjegyzékszám (Hungary)")
async def lookup_company_hu(
    id_number: str,
    client: AsyncClient = Depends(get_httpx_client)
):
    service = NAVService(client)
    return await service.fetch_company(id_number)
