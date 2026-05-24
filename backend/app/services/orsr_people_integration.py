from __future__ import annotations
import re
from typing import List, Dict, Any, Optional

from .orsr_fetch import fetch_vypis_html
from .orsr_people_parser import parse_orsr_people

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def ensure_sk_people_for_company(
    company: Dict[str, Any], 
    executives: Optional[List[Dict[str, Any]]] = None, 
    owners: Optional[List[Dict[str, Any]]] = None
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    If company is SK and executives/owners are empty, fetches them from ORSR.
    Returns (executives, owners) and enriches company dict with:
      - people_source
      - orsr_vypis_url
    """
    country = (company.get("country") or "").upper()
    if country != "SK":
        return executives or [], owners or []

    # Initialize keys to ensure they exist in response if graph=1 requested
    if "executives" not in company:
        company["executives"] = executives or []
    if "owners" not in company:
        company["owners"] = owners or []

    ex = company["executives"]
    ow = company["owners"]
    
    # If we already have list of people (e.g. from a data sync), 
    # we might still want to refresh from ORSR if we are in graph=1 mode 
    # and the source was generic RUZ (which often has only basic data).
    # For now, if we have them, we skip.
    if ex or ow:
        return ex, ow

    ico = _clean(company.get("atlas_id") or company.get("ico") or "")
    if not ico:
        company["people_source"] = "ORSR_EMPTY_ICO"
        return [], []

    res = fetch_vypis_html(ico)
    company["orsr_vypis_url"] = res.vypis_url
    
    if not res.ok or not res.html:
        company["people_source"] = res.reason or "ORSR_FAIL"
        return [], []

    try:
        parsed = parse_orsr_people(res.html)
        ex = parsed.get("executives", [])
        ow = parsed.get("owners", [])
        company["people_source"] = "SK_ORSR_HTML"
        
        # Enrich the company object itself
        company["executives"] = ex
        company["owners"] = ow
        
        # Enrich additional ORSR fields
        if parsed.get("capital"):
            company["capital"] = parsed["capital"]
        if parsed.get("activities"):
            company["activities"] = parsed["activities"]
        if parsed.get("address"):
            addr = parsed["address"]
            if addr.get("street") and (not company.get("street") or len(company.get("street")) < len(addr["street"])):
                company["street"] = addr["street"]
            if addr.get("postal_code") and not company.get("postal_code"):
                company["postal_code"] = addr["postal_code"]
        
        return ex, ow
    except Exception as e:
        company["people_source"] = f"PARSE_ERROR:{type(e).__name__}"
        return [], []
