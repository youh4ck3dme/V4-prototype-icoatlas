from fastapi import APIRouter, Depends
from httpx import AsyncClient
from ...services.krs_playwright_service import KRSPlaywrightService
from ...models.company import Company

router = APIRouter()

@router.get("/company/{krs_number}", response_model=Company, summary="Lookup company by KRS (Playwright)")
async def lookup_company_pl(krs_number: str):
    service = KRSPlaywrightService()
    return await service.fetch_company(krs_number)
