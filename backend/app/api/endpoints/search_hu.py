from fastapi import APIRouter
from ...services.nav_playwright_service import NAVPlaywrightService
from ...models.company import Company

router = APIRouter()

@router.get("/company/{id_number}", response_model=Company, summary="Lookup company by Cégjegyzékszám (Playwright)")
async def lookup_company_hu(id_number: str):
    service = NAVPlaywrightService()
    return await service.fetch_company(id_number)
