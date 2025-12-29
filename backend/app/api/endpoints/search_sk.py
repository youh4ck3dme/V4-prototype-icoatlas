from fastapi import APIRouter, Depends
from httpx import AsyncClient
from ...services.ruz_service import RuzService
from ...models.company import Company

router = APIRouter()

async def get_httpx_client() -> AsyncClient:
    async with AsyncClient() as client:
        yield client

@router.get("/company/{ico}", response_model=Company, summary="Lookup company by IČO (RÚZ Hybrid)")
async def lookup_company_sk(
    ico: str,
    client: AsyncClient = Depends(get_httpx_client)
):
    service = RuzService(client)
    return await service.fetch_company(ico)
