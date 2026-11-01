"""
CZ ARES (otvorené REST API Ministerstva financí ČR, bez kľúča a bez poplatkov).
GET https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}

fetch_company vracia spoločný Company model; raw_data = celá odpoveď ARES
+ raw_data["normalized"] s poliami v tvare atlas_companies (normalize_ares).
"""
import asyncio
import logging
import re
from typing import Any, Dict, Optional

from fastapi import HTTPException
from httpx import AsyncClient, HTTPStatusError, TimeoutException, TransportError

from ..core.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker
from ..models.company import Company

logger = logging.getLogger("uvicorn.error")

MAX_RETRIES = 2
RETRY_DELAY = 1.0

STATUS_ACTIVE = "AKTÍVNA"
STATUS_DISSOLVED = "ZANIKNUTÁ"
STATUS_UNKNOWN = "NEZNÁMY"


def normalize_cz_ico(ico: str) -> Optional[str]:
    """ARES IČO má 8 číslic; staršie kratšie IČO sa dopĺňa nulami zľava."""
    digits = re.sub(r"\D+", "", ico or "")
    if not digits or len(digits) > 8:
        return None
    return digits.zfill(8)


def ares_status(data: Dict[str, Any]) -> str:
    if data.get("datumZaniku"):
        return STATUS_DISSOLVED
    regs = data.get("seznamRegistraci") or {}
    states = [regs.get("stavZdrojeVr"), regs.get("stavZdrojeRos"), regs.get("stavZdrojeRes")]
    if "AKTIVNI" in states:
        return STATUS_ACTIVE
    if any(s in ("ZANIKLY", "HISTORICKY") for s in states):
        return STATUS_DISSOLVED
    return STATUS_UNKNOWN


def normalize_ares(data: Dict[str, Any]) -> Dict[str, Any]:
    """Polia v tvare atlas_companies (+ dic, founded/dissolved) z odpovede ARES."""
    sidlo = data.get("sidlo") or {}
    street = sidlo.get("nazevUlice") or sidlo.get("nazevCastiObce") or sidlo.get("nazevObce")
    number = sidlo.get("cisloDomovni")
    if number is not None and sidlo.get("cisloOrientacni") is not None:
        number = f"{number}/{sidlo.get('cisloOrientacni')}{sidlo.get('cisloOrientacniPismeno') or ''}"
    psc = sidlo.get("psc")
    return {
        "ico": data.get("ico"),
        "legal_name": data.get("obchodniJmeno"),
        "status": ares_status(data),
        "legal_form": data.get("pravniForma"),
        "street": " ".join(str(p) for p in (street, number) if p not in (None, "")) or None,
        "city": sidlo.get("nazevObce"),
        "postal_code": str(psc) if psc is not None else None,
        "region": sidlo.get("nazevKraje"),
        "country_code": sidlo.get("kodStatu") or "CZ",
        "address": sidlo.get("textovaAdresa"),
        "nace_codes": data.get("czNace") or [],
        "dic": data.get("dic"),
        "founded": data.get("datumVzniku"),
        "dissolved": data.get("datumZaniku"),
        "updated": data.get("datumAktualizace"),
    }


class ARESService:
    BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"

    def __init__(self, client: AsyncClient):
        self.client = client
        self.breaker = get_circuit_breaker("ares", failure_threshold=5, recovery_timeout=60)

    async def fetch_company(self, ico: str) -> Company:
        norm_ico = normalize_cz_ico(ico)
        if not norm_ico:
            raise HTTPException(status_code=400, detail="IČO musí mať najviac 8 číslic")

        try:
            data = await self.breaker.acall(self._get_with_retry, norm_ico)
        except CircuitBreakerOpenError:
            raise HTTPException(status_code=503, detail="ARES je dočasne nedostupný")
        except TimeoutException:
            raise HTTPException(status_code=504, detail="ARES request timed out")
        except (HTTPStatusError, TransportError, ValueError) as exc:
            logger.warning("ARES %s failed: %s", norm_ico, exc)
            raise HTTPException(status_code=502, detail="ARES API error")

        if data is None:
            raise HTTPException(status_code=404, detail=f"IČO {norm_ico} not found")

        try:
            normalized = normalize_ares(data)
            return Company(
                ico=str(data["ico"]),
                name=normalized["legal_name"] or "",
                address=normalized["address"] or "",
                status=normalized["status"],
                raw_data={**data, "normalized": normalized},
            )
        except (KeyError, TypeError) as e:
            raise HTTPException(status_code=502, detail=f"Unexpected ARES response format: {e}")

    async def _get_with_retry(self, ico: str) -> Optional[Dict[str, Any]]:
        last_exc: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await self.client.get(f"{self.BASE_URL}/{ico}", timeout=10.0)
                if resp.status_code == 404:
                    return None
                if resp.status_code >= 500 or resp.status_code == 429:
                    resp.raise_for_status()
                if resp.status_code != 200:
                    # 4xx nie je výpadok; nepočítať do circuit breakera opakovaním
                    resp.raise_for_status()
                return resp.json()
            except HTTPStatusError as e:
                if e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                last_exc = e
            except (TransportError, ValueError) as e:
                last_exc = e
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
        raise last_exc  # type: ignore[misc]


# identity_graph.py a utils/id_router.py importujú AresService
AresService = ARESService
