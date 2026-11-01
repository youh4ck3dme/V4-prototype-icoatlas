import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from httpx import AsyncClient
from typing import List, Dict, Any, Optional
from ...services.fs_iban_service import (
    FsIbanNotConfiguredError,
    FsIbanService,
    FsIbanUnavailableError,
    iban_checksum_ok,
    normalize_iban,
)
from ...services.ruz_service import RuzService
from ...services.autoform_service import AutoformService
from ...services.cache_service import cache_service
from ...services.company_store import CompanyStore, database_configured
from ...services.ruz_financials_service import (
    CACHE_TTL as RUZ_CACHE_TTL,
    RuzFinancialsService,
    RuzUnavailableError,
)
from ...models.company import Company

logger = logging.getLogger("uvicorn.error")

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

@router.get("/company/{ico}/financials", summary="Súvaha a VZaS z RÚZ (šablóny 687 a 699) + história rokov")
async def company_financials_sk(
    ico: str,
    years: int = Query(5, ge=1, le=10, description="Koľko posledných rokov vrátiť"),
    refresh: bool = Query(False, description="Ignorovať cache"),
    client: AsyncClient = Depends(get_httpx_client),
) -> Dict[str, Any]:
    if not re.fullmatch(r"\d{8}", ico):
        raise HTTPException(status_code=400, detail="IČO musí mať 8 číslic")

    cache_key = f"ruz:financials:{ico}:{years}"
    financials = None if refresh else await cache_service.get(cache_key)
    cached = financials is not None
    if not cached:
        try:
            financials = await RuzFinancialsService(client, max_years=years).fetch_financials(ico)
        except RuzUnavailableError:
            logger.warning("RÚZ unavailable for %s", ico, exc_info=True)
            raise HTTPException(status_code=503, detail="Register účtovných závierok je dočasne nedostupný")
        if financials is None:
            raise HTTPException(status_code=404, detail=f"Pre IČO {ico} nie sú v RÚZ účtovné závierky")
        await cache_service.set(cache_key, financials, expire_seconds=RUZ_CACHE_TTL)

    atlas_id = None
    if database_configured() and not cached:
        try:
            atlas_id = await run_in_threadpool(_persist_financials, ico, financials)
        except Exception:
            # zápis nesmie zhodiť odpoveď; dáta už máme
            logger.exception("Saving financials for %s failed", ico)

    return {"ico": ico, "financials": financials, "cached": cached, "atlas_id": atlas_id}


def _persist_financials(ico: str, financials: Dict[str, Any]) -> str:
    with CompanyStore() as store:
        atlas_id = store.ensure_company("SK", "ICO", ico, source="RUZ")
        store.save_financials(atlas_id, financials, request_id=ico)
        return atlas_id


@router.get("/company/{ico}/iban", summary="Overenie IBAN v zozname platiteľov DPH (Finančná správa SR)")
async def company_iban_sk(
    ico: str,
    iban: Optional[str] = Query(None, description="Voliteľne: IBAN, ktorý chcete overiť"),
    client: AsyncClient = Depends(get_httpx_client),
) -> Dict[str, Any]:
    if not re.fullmatch(r"\d{8}", ico):
        raise HTTPException(status_code=400, detail="IČO musí mať 8 číslic")
    checked = normalize_iban(iban) if iban else None
    if checked and not iban_checksum_ok(checked):
        raise HTTPException(status_code=400, detail="IBAN nemá platný formát alebo kontrolnú číslicu")

    try:
        result = await FsIbanService(client).lookup(ico)
    except FsIbanNotConfiguredError:
        logger.error("FS IBAN lookup not configured or key rejected")
        raise HTTPException(status_code=503, detail="Overenie IBAN nie je nakonfigurované")
    except FsIbanUnavailableError:
        logger.warning("FS IBAN unavailable for %s", ico, exc_info=True)
        raise HTTPException(status_code=503, detail="Zoznam Finančnej správy je dočasne nedostupný")

    result["checked_iban"] = checked
    result["iban_match"] = (checked in result["ibans"]) if checked else None

    atlas_id = None
    if database_configured():
        try:
            atlas_id = await run_in_threadpool(_persist_iban, ico, result)
        except Exception:
            logger.exception("Saving IBAN check for %s failed", ico)
    result["atlas_id"] = atlas_id
    return result


def _persist_iban(ico: str, result: Dict[str, Any]) -> str:
    with CompanyStore() as store:
        atlas_id = store.ensure_company("SK", "ICO", ico, source="FS")
        store.save_iban_check(atlas_id, result, request_id=ico)
        return atlas_id


@router.get("/autocomplete", summary="Search for companies (Autocomplete)")
async def autocomplete_sk(
    q: str = Query(..., min_length=2, description="Search query"),
    client: AsyncClient = Depends(get_httpx_client)
):
    service = AutoformService(client)
    return await service.autocomplete(q)
