from fastapi import APIRouter, Depends
from httpx import AsyncClient
from ...services.ares_service import ARESService
from ...models.company import Company
from ...core.config import settings

router = APIRouter()

async def get_httpx_client() -> AsyncClient:
    async with AsyncClient() as client:
        yield client

@router.get("/company/{ico}", response_model=Company, summary="Lookup company by IČO (ARES)")
async def lookup_company(
    ico: str,
    client: AsyncClient = Depends(get_httpx_client)
):
    service = ARESService(client)
    return await service.fetch_company(ico)
