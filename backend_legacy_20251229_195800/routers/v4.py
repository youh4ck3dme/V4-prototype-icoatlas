from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from typing import List
from services.v4_service import V4Service
from services.v4_clients.models import NormalizedCompany

router = APIRouter()

def get_v4_service():
    return V4Service()

@router.get("/search")
async def search_v4(
    country: str = Query(..., regex="^(SK|CZ|PL|HU|sk|cz|pl|hu)$", description="ISO code of the country"),
    q: str = Query(..., min_length=3, description="Company ID (IČO, KRS) or Identifier"),
    service: V4Service = Depends(get_v4_service)
):
    """
    Unified search endpoint for V4 countries.
    """
    country = country.upper()
    result = await service.search_company(country, q)

    if "error" in result:
        # Check for specific errors if needed, or return 500
        # For not found, service returns {"found": False} sometimes?
        # V4Service.search_company returns dict.
        raise HTTPException(status_code=400, detail=result["error"])

    return result

@router.get("/search/{country}/{identifier}")
async def search_v4_by_path(
    country: str = Path(..., regex="^(SK|CZ|PL|HU)$", description="ISO code of the country"),
    identifier: str = Path(..., min_length=3, description="Company identifier (IČO, KRS, etc.)"),
    service: V4Service = Depends(get_v4_service),
    request: Request = None
) -> NormalizedCompany:
    """
    Search for a company by country and identifier.
    """
    return await service.search_v4_company(country, identifier, request)

@router.get("/sync/{country}")
async def sync_v4(
    country: str = Path(..., regex="^(SK|CZ|PL|HU)$", description="ISO code of the country"),
    since: str = Query(..., description="ISO timestamp since when to sync changes"),
    service: V4Service = Depends(get_v4_service),
    request: Request = None
) -> List[NormalizedCompany]:
    """
    Sync company changes since the given timestamp.
    """
    return await service.sync_v4_changes(country, since, request)

@router.get("/validate/{country}/{identifier}")
async def validate_v4(
    country: str = Path(..., regex="^(SK|CZ|PL|HU)$", description="ISO code of the country"),
    identifier: str = Path(..., min_length=3, description="Company identifier to validate"),
    service: V4Service = Depends(get_v4_service),
    request: Request = None
) -> NormalizedCompany:
    """
    Validate a company identifier and return company data if valid.
    """
    return await service.validate_v4_identifier(country, identifier, request)
