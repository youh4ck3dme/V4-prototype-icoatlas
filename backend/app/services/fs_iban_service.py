"""
Overenie IBAN cez OpenData Finančnej správy SR: zoznam platiteľov DPH s číslami bankových účtov
(slug ds_dph_iban, § 52 ods. 15 daňového poriadku).

API: https://iz.opendata.financnasprava.sk/api  (hlavička `key`, bezplatná registrácia)
Licencia portálu OpenData FS: CC BY 4.0, povinné uvedenie zdroja (ATTRIBUTION).
Pozor: XML export report.financnasprava.sk/ds_dph_iban.zip nesie v sebe CC BY-NC-ND,
preto ho nepoužívame.

Názvy stĺpcov sa nehádajú: vyhľadávací stĺpec sa vyberie zo `searchable` v /lists/{slug},
kľúče položiek sa čítajú bez ohľadu na veľkosť písmen (export používa ICO, IC_DPH, IBAN).
"""
import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from ..core.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker

logger = logging.getLogger("uvicorn.error")

BASE_URL = "https://iz.opendata.financnasprava.sk/api"
SLUG = "ds_dph_iban"
ATTRIBUTION = "Zdroj údajov: Finančná správa SR - https://opendata.financnasprava.sk/"
MAX_RETRIES = 2
RETRY_DELAY = 1.0
REQUEST_TIMEOUT = 15.0
MAX_PAGES = 20
STUB_ICO = "52374220"
STUB_IBAN = "SK3112000000198742637541"


class FsIbanUnavailableError(Exception):
    """FS API neodpovedá, aktualizuje zoznam (503) alebo je otvorený circuit breaker."""


class FsIbanNotConfiguredError(Exception):
    """Chýba FS_OPENDATA_API_KEY."""


def normalize_iban(iban: str) -> str:
    return re.sub(r"\s+", "", iban or "").upper()


def iban_checksum_ok(iban: str) -> bool:
    """ISO 13616 mod-97 kontrola (SK IBAN má 24 znakov)."""
    s = normalize_iban(iban)
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    if s.startswith("SK") and len(s) != 24:
        return False
    rearranged = s[4:] + s[:4]
    digits = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(digits) % 97 == 1


def _field(item: Dict[str, Any], name: str) -> Optional[str]:
    for k, v in item.items():
        if k.lower() == name.lower():
            return None if v is None else str(v).strip()
    return None


class FsIbanService:
    def __init__(self, client: httpx.AsyncClient, api_key: Optional[str] = None):
        self.client = client
        self.api_key = api_key if api_key is not None else os.getenv("FS_OPENDATA_API_KEY")
        self.breaker = get_circuit_breaker("fs_iban", failure_threshold=5, recovery_timeout=60)

    @staticmethod
    def stub_mode() -> bool:
        return os.getenv("FS_IBAN_STUB_MODE", "").lower() in ("1", "true", "yes")

    async def lookup(self, ico: str) -> Dict[str, Any]:
        """Vráti zverejnené účty firmy. `registered` = firma je v zozname aspoň s jedným účtom."""
        if not re.fullmatch(r"\d{8}", ico or ""):
            raise ValueError("IČO musí mať 8 číslic")

        if self.stub_mode():
            items = [{"ICO": STUB_ICO, "IC_DPH": "SK2023456789", "IBAN": STUB_IBAN}] if ico == STUB_ICO else []
            list_updated = None
        else:
            if not self.api_key:
                raise FsIbanNotConfiguredError("FS_OPENDATA_API_KEY nie je nastavený")
            meta = await self._get(f"lists/{SLUG}", {})
            column = self._search_column(meta or {})
            items = await self._search(column, ico)
            list_updated = (meta or {}).get("update_date")

        ibans: List[str] = []
        vat_ids: List[str] = []
        for it in items:
            if _field(it, "ICO") not in (None, ico):
                continue  # vyhľadávanie môže byť podreťazcové
            iban = normalize_iban(_field(it, "IBAN") or "")
            if iban and iban not in ibans:
                ibans.append(iban)
            vat = _field(it, "IC_DPH")
            if vat and vat not in vat_ids:
                vat_ids.append(vat)

        return {
            "ico": ico,
            "registered": bool(ibans),
            "ibans": ibans,
            "vat_ids": vat_ids,
            "list_updated": list_updated,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "FS_STUB" if self.stub_mode() else "FS_OPENDATA",
            "attribution": ATTRIBUTION,
        }

    @staticmethod
    def _search_column(meta: Dict[str, Any]) -> str:
        searchable = meta.get("searchable") or []
        for col in searchable:
            if col.lower() == "ico":
                return col
        raise FsIbanUnavailableError(f"Zoznam {SLUG} nemá vyhľadávateľný stĺpec ICO (searchable={searchable})")

    async def _search(self, column: str, ico: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        page, pages = 1, 1
        while page <= pages:
            data = await self._get(f"data/{SLUG}/search", {"page": page, "column": column, "search": ico})
            if not data:
                break  # 404 = nič nenájdené
            items.extend(data.get("data") or [])
            pages = int(data.get("pages") or 1)
            if pages > MAX_PAGES:
                # neúplný zoznam by dal falošné iban_match=false; radšej žiadny výsledok
                raise FsIbanUnavailableError(f"FS vrátilo {pages} strán, limit je {MAX_PAGES}")
            page += 1
        return items

    async def _get(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return await self.breaker.acall(self._get_with_retry, path, params)
        except CircuitBreakerOpenError as e:
            raise FsIbanUnavailableError(str(e)) from e

    async def _get_with_retry(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{BASE_URL}/{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await self.client.get(url, params=params, timeout=REQUEST_TIMEOUT,
                                             headers={"key": self.api_key or "", "Accept": "application/json"})
                if resp.status_code == 404:
                    return None
                if resp.status_code in (401, 403):
                    raise FsIbanNotConfiguredError(f"FS API odmietlo kľúč ({resp.status_code})")
                if resp.status_code >= 500 or resp.status_code == 429:
                    # 503 = zoznam sa práve aktualizuje
                    raise httpx.HTTPStatusError(f"FS {resp.status_code}", request=resp.request, response=resp)
                if resp.status_code != 200:
                    raise FsIbanUnavailableError(f"FS API {path} -> {resp.status_code}")
                return resp.json()
            except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
        raise FsIbanUnavailableError(f"FS {path} zlyhalo po {MAX_RETRIES + 1} pokusoch: {last_exc}")
