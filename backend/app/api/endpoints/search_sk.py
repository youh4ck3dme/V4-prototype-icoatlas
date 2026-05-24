from fastapi import APIRouter, Depends, Query
from httpx import AsyncClient
from typing import List, Dict, Any
from ...services.ruz_service import RuzService
from ...services.autoform_service import AutoformService
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

@router.get("/autocomplete", summary="Search for companies (Autocomplete)")
async def autocomplete_sk(
    q: str = Query(..., min_length=2, description="Search query"),
    client: AsyncClient = Depends(get_httpx_client)
):
    service = AutoformService(client)
    return await service.autocomplete(q)
