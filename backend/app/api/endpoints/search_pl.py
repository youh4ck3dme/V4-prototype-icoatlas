from fastapi import APIRouter, Depends
from httpx import AsyncClient
from ...services.krs_service import KRSService
from ...models.company import Company

router = APIRouter()

async def get_httpx_client() -> AsyncClient:
    async with AsyncClient() as client:
        yield client

@router.get("/company/{krs_number}", response_model=Company, summary="Lookup company by KRS number")
async def lookup_company_pl(
    krs_number: str,
    client: AsyncClient = Depends(get_httpx_client)
):
    service = KRSService(client)
    return await service.fetch_company(krs_number)
