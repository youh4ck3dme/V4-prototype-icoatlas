"""
RÚZ financials: súvaha + výkaz ziskov a strát z otvoreného API Registra účtovných závierok.

Reťazec volaní (overené 2026-11-01):
  /api/uctovne-jednotky?zmenene-od=2000-01-01&ico=  -> {"id": [...]}
  /api/uctovna-jednotka?id=                         -> idUctovnychZavierok
  /api/uctovna-zavierka?id=                         -> obdobieOd/Do, typ, idUctovnychVykazov
  /api/uctovny-vykaz?id=                            -> idSablony, obsah.tabulky[].data

Podporované šablóny (štruktúrované tabuľky):
  687 = Úč MUJ (mikro účtovné jednotky)
  699 = Úč POD (malé, stredné a veľké účtovné jednotky)
Iné šablóny (napr. IFRS) majú v RÚZ len PDF; vrátia sa v histórii s "available": false.

Logika prevzatá z backend_legacy_20251229_195800/services/sk_ruz_provider.py:
retry (MAX_RETRIES, RETRY_DELAY), stub mode (IČO 52374220), normalizácia čísel.
Legacy endpoint /api/uctovne-zavierky?ico= už neexistuje (403), preto nový reťazec.
"""
import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..core.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker

logger = logging.getLogger("uvicorn.error")

BASE_URL = "https://www.registeruz.sk/cruz-public/api"
MAX_RETRIES = 2
RETRY_DELAY = 1.0  # s, exponenciálne: 1, 2
REQUEST_TIMEOUT = 15.0
MAX_CONCURRENCY = 5
CACHE_TTL = 12 * 3600
STUB_ICO = "52374220"

# (tabuľka, prvé číslo riadku tabuľky, počet dátových stĺpcov, stĺpec bežného obdobia)
_TABLES_687 = {"assets": (0, 1, 2, 0), "liabilities": (1, 24, 2, 0), "pl": (2, 1, 2, 0)}
_TABLES_699 = {"assets": (0, 1, 4, 2), "liabilities": (1, 79, 2, 0), "pl": (2, 1, 2, 0)}

# metrika -> [(sekcia, číslo riadku), ...]; viac riadkov = súčet
TEMPLATES: Dict[int, Dict[str, Any]] = {
    687: {
        "name": "Úč MUJ",
        "tables": _TABLES_687,
        "rows": {
            "assets": [("assets", 1)],                      # SPOLU MAJETOK
            "equity": [("liabilities", 25)],                # A. Vlastné imanie
            "liabilities": [("liabilities", 34)],           # B. Záväzky
            "revenue": [("pl", 2), ("pl", 3)],              # Tržby z predaja tovaru + vlastných výrobkov a služieb
            "operating_income": [("pl", 1)],                # Výnosy z hospodárskej činnosti spolu
            "profit": [("pl", 38)],                         # VH za účtovné obdobie po zdanení
        },
    },
    699: {
        "name": "Úč POD",
        "tables": _TABLES_699,
        "rows": {
            "assets": [("assets", 1)],                      # SPOLU MAJETOK (Netto bežné obdobie)
            "equity": [("liabilities", 80)],                # A. Vlastné imanie
            "liabilities": [("liabilities", 101)],          # B. Záväzky
            "revenue": [("pl", 3), ("pl", 4), ("pl", 5)],   # Tržby z predaja tovaru + výrobkov + služieb
            "net_turnover": [("pl", 1)],                    # Čistý obrat
            "operating_income": [("pl", 2)],                # Výnosy z hospodárskej činnosti spolu
            "profit": [("pl", 61)],                         # VH za účtovné obdobie po zdanení
        },
    },
}

_TABLE_ROWS = {687: (23, 22, 38), 699: (78, 67, 61)}


class RuzUnavailableError(Exception):
    """RÚZ neodpovedá (po retry) alebo je otvorený circuit breaker."""


def normalize_number(value: Any) -> Optional[float]:
    """'1 234,50' -> 1234.5, '' -> None. Prevzaté zo sk_ruz_provider._normalize_number."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = re.sub(r"[\s ]", "", str(value)).replace(",", ".")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_statement(template_id: int, tables: List[Dict[str, Any]]) -> Optional[Dict[str, Optional[float]]]:
    """Vytiahne kľúčové metriky z obsah.tabulky výkazu. None, ak šablóna/tvar nesedí."""
    spec = TEMPLATES.get(template_id)
    if not spec or len(tables) < 3:
        return None

    for idx, n_rows in enumerate(_TABLE_ROWS[template_id]):
        cols = list(spec["tables"].values())[idx][2]
        if len(tables[idx].get("data") or []) != n_rows * cols:
            return None

    def cell(section: str, row: int) -> Optional[float]:
        t_idx, first_row, cols, col = spec["tables"][section]
        data = tables[t_idx]["data"]
        return normalize_number(data[(row - first_row) * cols + col])

    out: Dict[str, Optional[float]] = {}
    for metric, refs in spec["rows"].items():
        values = [cell(sec, row) for sec, row in refs]
        present = [v for v in values if v is not None]
        out[metric] = sum(present) if present else None
    return out


def _stub_financials(ico: str) -> Optional[Dict[str, Any]]:
    if ico != STUB_ICO:
        return None
    history = [
        {"year": 2023, "template": "687", "available": True, "assets": 900000.0, "liabilities": 600000.0,
         "equity": 300000.0, "revenue": 2000000.0, "profit": 50000.0},
        {"year": 2022, "template": "687", "available": True, "assets": 800000.0, "liabilities": 550000.0,
         "equity": 250000.0, "revenue": 1500000.0, "profit": 30000.0},
    ]
    return _build_result(ico, history, stub=True)


def _build_result(ico: str, history: List[Dict[str, Any]], stub: bool = False) -> Optional[Dict[str, Any]]:
    if not history:
        return None
    history = sorted(history, key=lambda h: h["year"], reverse=True)
    latest = next((h for h in history if h.get("available")), None)
    base = dict(latest) if latest else {"year": None, "template": None, "available": False}
    base.update({
        "ico": ico,
        "source": "RUZ_STUB" if stub else "RUZ",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "history": history,
    })
    return base


class RuzFinancialsService:
    def __init__(self, client: httpx.AsyncClient, max_years: int = 5):
        self.client = client
        self.max_years = max_years
        self.breaker = get_circuit_breaker("ruz", failure_threshold=5, recovery_timeout=60)
        self._sem = asyncio.Semaphore(MAX_CONCURRENCY)

    @staticmethod
    def stub_mode() -> bool:
        return os.getenv("RUZ_STUB_MODE", "").lower() in ("1", "true", "yes")

    async def fetch_financials(self, ico: str) -> Optional[Dict[str, Any]]:
        if not re.fullmatch(r"\d{8}", ico or ""):
            raise ValueError("IČO musí mať 8 číslic")
        if self.stub_mode():
            return _stub_financials(ico)

        unit_ids = (await self._get("uctovne-jednotky", {"zmenene-od": "2000-01-01", "ico": ico}) or {}).get("id") or []
        if not unit_ids:
            return None

        units = await asyncio.gather(*(self._get("uctovna-jednotka", {"id": uid}) for uid in unit_ids))
        statement_ids: List[int] = []
        for u in units:
            if u and str(u.get("ico", ico)) == ico:
                statement_ids.extend(u.get("idUctovnychZavierok") or [])
        if not statement_ids:
            return None

        statements = await asyncio.gather(*(self._get("uctovna-zavierka", {"id": sid}) for sid in set(statement_ids)))
        chosen = self._pick_statements([s for s in statements if s])

        history = await asyncio.gather(*(self._statement_entry(year, st) for year, st in chosen))
        return _build_result(ico, [h for h in history if h])

    def _pick_statements(self, statements: List[Dict[str, Any]]) -> List[Tuple[int, Dict[str, Any]]]:
        """Jedna závierka na rok: riadna pred mimoriadnou, potom najnovšia úprava. Priebežné sa vynechajú."""
        by_year: Dict[int, Dict[str, Any]] = {}
        for st in statements:
            typ = (st.get("typ") or "").lower()
            if typ.startswith("priebe"):
                continue
            m = re.match(r"(\d{4})", st.get("obdobieDo") or "")
            if not m:
                continue
            year = int(m.group(1))
            rank = (typ == "riadna", st.get("datumPoslednejUpravy") or "")
            cur = by_year.get(year)
            if cur is None or rank > cur["_rank"]:
                by_year[year] = {**st, "_rank": rank}
        years = sorted(by_year, reverse=True)[: self.max_years]
        return [(y, by_year[y]) for y in years]

    async def _statement_entry(self, year: int, st: Dict[str, Any]) -> Dict[str, Any]:
        entry: Dict[str, Any] = {
            "year": year,
            "period_from": st.get("obdobieOd"),
            "period_to": st.get("obdobieDo"),
            "statement_type": st.get("typ"),
            "template": None,
            "available": False,
            "raw": {"id_zavierky": st.get("id"), "datum_poslednej_upravy": st.get("datumPoslednejUpravy")},
        }
        for report_id in st.get("idUctovnychVykazov") or []:
            report = await self._get("uctovny-vykaz", {"id": report_id})
            if not report:
                continue
            template_id = report.get("idSablony")
            entry["template"] = str(template_id) if template_id is not None else None
            entry["raw"]["id_vykazu"] = report_id
            metrics = parse_statement(template_id, (report.get("obsah") or {}).get("tabulky") or [])
            if metrics is not None:
                entry.update(metrics)
                entry["available"] = True
                break
        return entry

    async def _get(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return await self.breaker.acall(self._get_with_retry, path, params)
        except CircuitBreakerOpenError as e:
            raise RuzUnavailableError(str(e)) from e

    async def _get_with_retry(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{BASE_URL}/{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with self._sem:
                    resp = await self.client.get(url, params=params, timeout=REQUEST_TIMEOUT,
                                                 headers={"Accept": "application/json"})
                if resp.status_code == 404:
                    return None
                if resp.status_code >= 500 or resp.status_code == 429:
                    raise httpx.HTTPStatusError(f"RÚZ {resp.status_code}", request=resp.request, response=resp)
                if resp.status_code != 200:
                    # 4xx okrem 404/429 sa neopakuje, ale nie je to výpadok RÚZ
                    logger.warning("RÚZ %s %s -> %s", path, params, resp.status_code)
                    return None
                return resp.json()
            except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
        raise RuzUnavailableError(f"RÚZ {path} zlyhal po {MAX_RETRIES + 1} pokusoch: {last_exc}")
