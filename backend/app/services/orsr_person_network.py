from __future__ import annotations
import re
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .orsr_fetch import _get, ORSR_BASE
from .orsr_people_parser import normalize_text, normalize_label


def find_affiliated_companies_for_person(full_name: str) -> Dict[str, Any]:
    """
    Searches ORSR for other companies affiliated with a given person (hladaj_osoba.asp).
    Returns:
      - person_name: clean name
      - affiliated_companies: list of dicts with company name, url, is_historical, status
      - total_affiliations: count of unique entities
      - serial_liquidator_risk: boolean flag if person has multiple entities in liquidation/bankruptcy
      - liquidation_count: number of affiliated entities in liquidation
    """
    name_clean = normalize_text(full_name)
    parts = name_clean.split()
    if len(parts) < 2:
        return {
            "person_name": full_name,
            "affiliated_companies": [],
            "total_affiliations": 0,
            "serial_liquidator_risk": False,
            "liquidation_count": 0
        }
        
    first_name = parts[0]
    last_name = " ".join(parts[1:])
    
    # Try last_name as first part if title like Ing./Mgr. was stripped
    if len(parts) == 2:
        # Common Slovak format: "Meno Priezvisko"
        first_name = parts[0]
        last_name = parts[1]

    try:
        pr_enc = urllib.parse.quote(last_name.encode("windows-1250", errors="ignore"))
        meno_enc = urllib.parse.quote(first_name.encode("windows-1250", errors="ignore"))
    except Exception:
        pr_enc = urllib.parse.quote(last_name)
        meno_enc = urllib.parse.quote(first_name)

    url = f"{ORSR_BASE}/hladaj_osoba.asp?PR={pr_enc}&MENO={meno_enc}&SID=0&T=f0&R=0"
    
    affiliated = []
    seen_names = set()
    liquidation_count = 0
    
    try:
        r = _get(url, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            
            for tr in soup.find_all("tr"):
                link = tr.find("a", href=re.compile(r"vypis\.asp"))
                if not link:
                    continue
                comp_name = normalize_text(link.get_text())
                if not comp_name or comp_name in ("Aktuálny", "Úplný"):
                    continue
                    
                norm_key = normalize_label(comp_name)
                if norm_key in seen_names:
                    continue
                seen_names.add(norm_key)
                
                href = link.get("href", "")
                is_historical = bool(link.find_parent("strike") or link.find("strike") or tr.find("strike"))
                
                # Check liquidation / bankruptcy status in text
                row_text = tr.get_text(" ", strip=True).lower()
                status = "AKTÍVNA"
                if "likvidáci" in row_text or "likvidaci" in comp_name.lower():
                    status = "V LIKVIDÁCII"
                    liquidation_count += 1
                elif "konkurz" in row_text or "konkurz" in comp_name.lower():
                    status = "V KONKURZE"
                    liquidation_count += 1
                elif is_historical:
                    status = "HISTORICKÁ ÚČASŤ"
                    
                affiliated.append({
                    "name": comp_name,
                    "url": f"{ORSR_BASE}/{href.lstrip('/')}" if href else "",
                    "is_historical": is_historical,
                    "status": status
                })
    except Exception:
        pass

    # Flag serial liquidator if > 10 affiliations or >= 2 in liquidation
    is_serial_liquidator = len(affiliated) >= 10 or liquidation_count >= 2

    return {
        "person_name": full_name,
        "affiliated_companies": affiliated,
        "total_affiliations": len(affiliated),
        "serial_liquidator_risk": is_serial_liquidator,
        "liquidation_count": liquidation_count
    }
