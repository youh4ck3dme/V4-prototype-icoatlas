from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .orsr_fetch import _get, ORSR_BASE
from .orsr_people_parser import normalize_text, normalize_label, get_br_split_lines


def parse_orsr_full_history(html_content: str, current_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses ORSR full extract with history (P=1).
    Extracts:
      - historical_names: previous company names with valid_from/valid_to
      - historical_addresses: previous registered offices
      - historical_executives: previous managers/statutories
      - historical_owners: previous shareholders/partners
      - historical_timeline: chronological lifecycle events
      - nominee_handover_analysis: risk audit for suspicious handover / exit scam
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    historical_names = []
    historical_addresses = []
    historical_executives = []
    historical_owners = []
    
    for table in soup.find_all("table"):
        rows = table.find_all("tr", recursive=False)
        if not rows:
            continue
        cells = rows[0].find_all("td", recursive=False)
        if len(cells) < 2:
            continue
            
        span_tl = cells[0].find("span", class_="tl")
        if not span_tl:
            continue
            
        label_norm = normalize_label(span_tl.get_text())
        nested = cells[1].find_all("table")
        
        for nt in nested:
            ro_spans = nt.find_all("span", class_="ro")
            if not ro_spans:
                continue
                
            full_text = nt.get_text(" ", strip=True)
            m_dates = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\s*do:\s*(\d{2}\.\d{2}\.\d{4})\)', full_text)
            valid_from = m_dates.group(1) if m_dates else ""
            valid_to = m_dates.group(2) if m_dates else ""
            
            # --- Obchodné meno ---
            if label_norm in ("obchodne meno", "obchodne meno subjektu"):
                name = normalize_text(ro_spans[0].get_text())
                if name and not any(h["name"] == name and h["valid_from"] == valid_from for h in historical_names):
                    historical_names.append({
                        "name": name,
                        "valid_from": valid_from,
                        "valid_to": valid_to
                    })
                    
            # --- Sídlo ---
            elif label_norm == "sidlo":
                lines = [
                    sp.get_text(strip=True) 
                    for sp in ro_spans 
                    if not (sp.get_text().startswith("(od:") or sp.get_text().startswith("(do:"))
                ]
                addr = ", ".join(lines)
                if addr and not any(h["address"] == addr for h in historical_addresses):
                    historical_addresses.append({
                        "address": addr,
                        "valid_from": valid_from,
                        "valid_to": valid_to
                    })
                    
            # --- Štatutárny orgán ---
            elif label_norm in ("statutarny organ", "predstavenstvo"):
                person_spans = [
                    sp.get_text(strip=True) 
                    for sp in ro_spans 
                    if not (
                        sp.get_text().startswith("(od:") 
                        or "funkcie" in sp.get_text().lower() 
                        or "stotožnená" in sp.get_text().lower()
                    )
                ]
                p_name = " ".join(person_spans[:2]) if len(person_spans) >= 2 else (person_spans[0] if person_spans else "")
                
                # Check for explicit termination date
                term_match = re.search(r'Skončenie funkcie:\s*(\d{2}\.\d{2}\.\d{4})', full_text)
                term_date = term_match.group(1) if term_match else valid_to
                
                start_match = re.search(r'Vznik funkcie:\s*(\d{2}\.\d{2}\.\d{4})', full_text)
                start_date = start_match.group(1) if start_match else valid_from
                
                if p_name and not any(h["name"] == p_name and h["since"] == start_date for h in historical_executives):
                    historical_executives.append({
                        "name": p_name,
                        "role": "konateľ",
                        "since": start_date,
                        "until": term_date,
                        "valid_from": valid_from,
                        "valid_to": valid_to
                    })
                    
            # --- Spoločníci ---
            elif label_norm in ("spolocnici", "akcionar"):
                person_spans = [
                    sp.get_text(strip=True) 
                    for sp in ro_spans 
                    if not (sp.get_text().startswith("(od:") or "vklad" in sp.get_text().lower() or "splatené" in sp.get_text().lower())
                ]
                p_name = " ".join(person_spans[:2]) if len(person_spans) >= 2 else (person_spans[0] if person_spans else "")
                
                # Check contribution if in text
                vklad_m = re.search(r'Vklad:\s*([\d\s]+)\s*([A-Z]{3})?', full_text)
                share_str = f"{vklad_m.group(1).strip()} {vklad_m.group(2) or 'EUR'}".strip() if vklad_m else ""
                
                if p_name and not any(h["name"] == p_name and h["since"] == valid_from for h in historical_owners):
                    historical_owners.append({
                        "name": p_name,
                        "share": share_str,
                        "since": valid_from,
                        "until": valid_to,
                        "valid_from": valid_from,
                        "valid_to": valid_to
                    })

    # --- Build Chronological Timeline ---
    timeline = []
    
    # 1. Foundation
    current_reg_date = (current_data or {}).get("registration_date") or ""
    initial_name = historical_names[-1]["name"] if historical_names else (current_data or {}).get("legal_name", "")
    initial_addr = historical_addresses[-1]["address"] if historical_addresses else (current_data or {}).get("street", "")
    
    if current_reg_date:
        timeline.append({
            "date": current_reg_date,
            "type": "FOUNDATION",
            "title": "Vznik a zápis spoločnosti",
            "description": f"Spoločnosť bola zapísaná do Obchodného registra s pôvodným obchodným menom '{initial_name}'."
        })
        
    # 2. Historical Name Changes
    for hn in historical_names:
        if hn.get("valid_to"):
            timeline.append({
                "date": hn["valid_to"],
                "type": "NAME_CHANGE",
                "title": "Zmena obchodného mena",
                "description": f"Ukončenie platnosti názvu '{hn['name']}' a premenovanie subjektu."
            })
            
    # 3. Historical Seat Relocations
    for ha in historical_addresses:
        if ha.get("valid_to"):
            timeline.append({
                "date": ha["valid_to"],
                "type": "SEAT_RELOCATION",
                "title": "Zmena sídla spoločnosti",
                "description": f"Presun sídla z pôvodnej adresy: {ha['address']}."
            })

    # 4. Executive Departures & Replacements
    for he in historical_executives:
        term_d = he.get("until") or he.get("valid_to")
        if term_d:
            timeline.append({
                "date": term_d,
                "type": "EXECUTIVE_EXIT",
                "title": f"Odchod štatutára: {he['name']}",
                "description": f"Zánik funkcie konateľa ({he['name']}), ktorý pôsobil v spoločnosti od {he.get('since', 'založenia')}."
            })
            
    # 5. Current Active Executives Entry
    for ce in (current_data or {}).get("executives", []):
        if ce.get("since") and ce["since"] != current_reg_date:
            timeline.append({
                "date": ce["since"],
                "type": "EXECUTIVE_ENTRY",
                "title": f"Nový štatutár: {ce['name']}",
                "description": f"Vymenovanie do funkcie konateľa ({ce['name']}) od {ce['since']}."
            })

    # 6. Ownership Transfers
    for ho in historical_owners:
        if ho.get("until"):
            timeline.append({
                "date": ho["until"],
                "type": "OWNERSHIP_EXIT",
                "title": f"Prevod podielu / Odchod spoločníka: {ho['name']}",
                "description": f"Ukončenie účasti spoločníka ({ho['name']}) v spoločnosti."
            })
            
    for co in (current_data or {}).get("owners", []):
        if co.get("since") and co["since"] != current_reg_date:
            timeline.append({
                "date": co["since"],
                "type": "OWNERSHIP_ENTRY",
                "title": f"Nový spoločník: {co['name']}",
                "description": f"Vstup nového spoločníka ({co['name']}) s vkladom {co.get('deposit', co.get('share', 'N/A'))}."
            })

    # Sort timeline chronologically (DD.MM.YYYY -> YYYY-MM-DD for sorting)
    def _parse_date_key(item):
        d_str = item.get("date", "")
        m = re.match(r'(\d{2})\.(\d{2})\.(\d{4})', d_str)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        return "1900-01-01"

    timeline.sort(key=_parse_date_key)

    # --- Nominee Handover & Exit Scam Audit ---
    suspicious_handover = False
    risk_score_delta = 0
    reasons = []

    has_full_exec_change = len(historical_executives) > 0 and len((current_data or {}).get("executives", [])) > 0
    has_full_owner_change = len(historical_owners) > 0 and len((current_data or {}).get("owners", [])) > 0
    has_relocation = len(historical_addresses) > 0

    if has_full_exec_change and has_full_owner_change:
        # Check if new executives are foreign or flagged nominees
        curr_execs = (current_data or {}).get("executives", [])
        has_foreign_incoming = any(e.get("potential_nominee") for e in curr_execs)
        
        if has_foreign_incoming:
            suspicious_handover = True
            risk_score_delta += 45
            reasons.append("Kompletný prepis spoločnosti (100% zmena štatutárov a spoločníkov) na zahraničnú osobu (vysoké riziko bieleho koňa).")
        elif has_relocation:
            reasons.append("Kompletná zmena vlastníctva sprevádzaná zmenou sídla a obchodného mena (štandardná reštrukturalizácia/akvizícia subjektu).")

    return {
        "historical_names": historical_names,
        "historical_addresses": historical_addresses,
        "historical_executives": historical_executives,
        "historical_owners": historical_owners,
        "timeline": timeline,
        "nominee_handover_analysis": {
            "suspicious_handover": suspicious_handover,
            "risk_score_delta": risk_score_delta,
            "reasons": reasons,
            "total_historical_executives": len(historical_executives),
            "total_historical_owners": len(historical_owners),
            "total_name_changes": len(historical_names),
            "total_relocations": len(historical_addresses)
        }
    }


def parse_orsr_deeds(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses Zbierka listín / dokumentov (zbl.asp).
    Extracts all deposited legal and financial documents:
      - title
      - doc_type
      - delivery_date
      - category (LEGAL_CONTRACT, FINANCIAL_STATEMENT, OFFICIAL_MINUTES, TRADE_LICENSE, SIGNATURE_SPECIMEN, OTHER)
    """
    soup = BeautifulSoup(html_content, "lxml")
    deeds = []
    
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 2:
            continue
        td_left = tds[0]
        td_right = tds[1]
        
        txt_left = td_left.get_text(" ", strip=True)
        txt_right = td_right.get_text(" ", strip=True)
        
        if "názov dokumentu:" in txt_left.lower():
            title_m = re.search(r'Názov dokumentu:\s*(.*?)(?:\s*Typ dokumentu:|$)', txt_left)
            type_m = re.search(r'Typ dokumentu:\s*(.*)', txt_left)
            date_m = re.search(r'Dátum doručenia:\s*(\d{2}\.\d{2}\.\d{4})', txt_right)
            
            title = normalize_text(title_m.group(1)) if title_m else ""
            doc_type = normalize_text(type_m.group(1)) if type_m else ""
            delivery_date = date_m.group(1) if date_m else ""
            
            # Categorize document
            category = "OTHER"
            low = f"{title} {doc_type}".lower()
            if "účtovná závierka" in low or "1-g" in low or "finančných výsledkoch" in low:
                category = "FINANCIAL_STATEMENT"
            elif "spoločenská zmluva" in low or "zakladateľsk" in low:
                category = "LEGAL_CONTRACT"
            elif "zápisnica" in low or "valného zhromaždenia" in low or "rozhodnutie" in low:
                category = "OFFICIAL_MINUTES"
            elif "živnostensk" in low or "oprávnenie" in low or "1-d" in low:
                category = "TRADE_LICENSE"
            elif "podpisový vzor" in low or "1-e,f" in low:
                category = "SIGNATURE_SPECIMEN"
                
            deeds.append({
                "title": title,
                "doc_type": doc_type,
                "delivery_date": delivery_date,
                "category": category
            })
            
    return deeds


def fetch_deeds_for_vypis_url(vypis_url: str) -> List[Dict[str, Any]]:
    """
    Given a current vypis.asp URL, fetches and parses zbl.asp.
    """
    if not vypis_url or "vypis.asp" not in vypis_url:
        return []
        
    zbl_url = vypis_url.replace("vypis.asp", "zbl.asp")
    # Clean P=0 or P=1 param
    zbl_url = re.sub(r'&P=\d+', '', zbl_url)
    
    try:
        r = _get(zbl_url, timeout=15)
        if r.status_code == 200:
            return parse_orsr_deeds(r.text)
    except Exception:
        pass
    return []


def fetch_history_for_vypis_url(vypis_url: str, current_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Given a current vypis.asp URL, resolves P=1 and returns the full history.
    """
    if not vypis_url or "vypis.asp" not in vypis_url:
        return {}
        
    hist_url = re.sub(r'&P=\d+', '', vypis_url) + "&P=1"
    try:
        r = _get(hist_url, timeout=15)
        if r.status_code == 200:
            return parse_orsr_full_history(r.text, current_data=current_data)
    except Exception:
        pass
    return {}
