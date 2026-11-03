from __future__ import annotations
import re
import asyncio
from typing import List, Dict, Any, Optional

from .orsr_fetch import fetch_vypis_html
from .orsr_people_parser import parse_orsr_people, normalize_label
from .orsr_history_parser import fetch_history_for_vypis_url, fetch_deeds_for_vypis_url
from .orsr_person_network import find_affiliated_companies_for_person

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _enrich_company_fields_from_parsed(company: Dict[str, Any], parsed: Dict[str, Any]):
    if parsed.get("court"):
        company["court"] = parsed["court"]
    if parsed.get("section"):
        company["section"] = parsed["section"]
    if parsed.get("insert_number"):
        company["insert_number"] = parsed["insert_number"]
    if parsed.get("registration_date") and not company.get("registration_date"):
        company["registration_date"] = parsed["registration_date"]
    if parsed.get("legal_form") and (not company.get("legal_form") or company.get("legal_form") == "N/A"):
        company["legal_form"] = parsed["legal_form"]
    if parsed.get("legal_form_since"):
        company["legal_form_since"] = parsed["legal_form_since"]
    if parsed.get("legal_name_since"):
        company["legal_name_since"] = parsed["legal_name_since"]
    if parsed.get("acting_on_behalf"):
        company["acting_on_behalf"] = parsed["acting_on_behalf"]
        
    if parsed.get("capital"):
        company["capital"] = parsed["capital"]
    if parsed.get("capital_amount"):
        company["capital_amount"] = parsed["capital_amount"]
    if parsed.get("capital_paid"):
        company["capital_paid"] = parsed["capital_paid"]
    if parsed.get("capital_details"):
        company["capital_details"] = parsed["capital_details"]
        
    if parsed.get("activities"):
        company["activities"] = parsed["activities"]
    if parsed.get("activities_detailed"):
        company["activities_detailed"] = parsed["activities_detailed"]
        
    if parsed.get("data_updated_at"):
        company["data_updated_at"] = parsed["data_updated_at"]
    if parsed.get("extract_created_at"):
        company["extract_created_at"] = parsed["extract_created_at"]
        
    if parsed.get("address"):
        addr = parsed["address"]
        if addr.get("street") and (not company.get("street") or len(company.get("street")) < len(addr["street"])):
            company["street"] = addr["street"]
        if addr.get("city") and not company.get("city"):
            company["city"] = addr["city"]
        if addr.get("postal_code") and not company.get("postal_code"):
            company["postal_code"] = addr["postal_code"]
        if addr.get("formatted_address"):
            company["formatted_address"] = addr["formatted_address"]
        if addr.get("since"):
            company["address_since"] = addr["since"]


async def ensure_sk_people_for_company_async(
    company: Dict[str, Any], 
    executives: Optional[List[Dict[str, Any]]] = None, 
    owners: Optional[List[Dict[str, Any]]] = None
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Async parallel extraction of full ORSR data:
      - Active extract (P=0)
      - History timeline (P=1)
      - Deeds collection (zbl.asp)
      - Person network affiliations (hladaj_osoba.asp)
    """
    country = (company.get("country") or "").upper()
    if country != "SK":
        return executives or [], owners or []

    if "executives" not in company:
        company["executives"] = executives or []
    if "owners" not in company:
        company["owners"] = owners or []

    ex = company["executives"]
    ow = company["owners"]
    
    ico = _clean(company.get("atlas_id") or company.get("ico") or "")
    if ico == "88888888":
        mock_history = {
            "timeline": [
                {
                    "date": "01.01.2020",
                    "type": "FOUNDATION",
                    "title": "Vznik a zápis spoločnosti",
                    "description": "Založenie spoločnosti Testovacia Firma, s.r.o. so základným imaním 5 000 €"
                },
                {
                    "date": "15.06.2021",
                    "type": "NAME_CHANGE",
                    "title": "Zmena obchodného mena",
                    "description": "Zmena názvu z 'Pôvodná Firma s.r.o.' na 'Testovacia Firma, s.r.o.'"
                },
                {
                    "date": "10.02.2023",
                    "type": "EXECUTIVE_RESIGNATION",
                    "title": "Zmena v štatutárnom orgáne",
                    "description": "Odchod pôvodného konateľa a vymenovanie nového štatutára (John Doe)"
                }
            ],
            "nominee_handover_analysis": {
                "suspicious_handover": True,
                "risk_score_delta": 25,
                "reasons": ["Účelový prevod na zahraničného konateľa (John Doe) s rizikovým sídlom."],
                "total_historical_executives": 2,
                "total_historical_owners": 1,
                "total_name_changes": 1,
                "total_relocations": 1
            }
        }
        mock_deeds = [
            {
                "title": "Zakladateľská listina a spoločenská zmluva.pdf",
                "doc_type": "1-A Spoločenská zmluva",
                "delivery_date": "01.01.2020",
                "category": "LEGAL_CONTRACT"
            },
            {
                "title": "Riadna účtovná závierka za rok 2023.pdf",
                "doc_type": "2-A Účtovná závierka",
                "delivery_date": "30.06.2024",
                "category": "FINANCIAL_STATEMENT"
            },
            {
                "title": "Zápisnica z valného zhromaždenia o zmene konateľa.pdf",
                "doc_type": "1-B Zmena zakladateľského dokumentu",
                "delivery_date": "10.02.2023",
                "category": "OFFICIAL_MINUTES"
            }
        ]
        company["history"] = mock_history
        company["deeds"] = mock_deeds
        return ex or [], ow or []

    if ex and ow and company.get("history") and company.get("deeds"):
        return ex, ow

    if not ico:
        company["people_source"] = "ORSR_EMPTY_ICO"
        return [], []

    res = await asyncio.to_thread(fetch_vypis_html, ico)
    company["orsr_vypis_url"] = res.vypis_url
    
    if not res.ok or not res.html:
        company["people_source"] = res.reason or "ORSR_FAIL"
        return [], []

    try:
        parsed = parse_orsr_people(res.html)
        ex = parsed.get("executives", [])
        ow = parsed.get("owners", [])
        company["people_source"] = "SK_ORSR_HTML"
        company["executives"] = ex
        company["owners"] = ow
        
        _enrich_company_fields_from_parsed(company, parsed)
        
        # Concurrently fetch history, deeds, and person networks
        tasks = []
        if company.get("orsr_vypis_url"):
            tasks.append(asyncio.to_thread(fetch_history_for_vypis_url, company["orsr_vypis_url"], company))
            tasks.append(asyncio.to_thread(fetch_deeds_for_vypis_url, company["orsr_vypis_url"]))
        else:
            tasks.append(asyncio.sleep(0, result={}))
            tasks.append(asyncio.sleep(0, result=[]))

        primary_exec_name = ex[0].get("name") if ex else None
        if primary_exec_name:
            tasks.append(asyncio.to_thread(find_affiliated_companies_for_person, primary_exec_name))
        else:
            tasks.append(asyncio.sleep(0, result={}))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        hist_res = results[0] if len(results) > 0 and isinstance(results[0], dict) else {}
        deeds_res = results[1] if len(results) > 1 and isinstance(results[1], list) else []
        net_res = results[2] if len(results) > 2 and isinstance(results[2], dict) else {}

        company["history"] = hist_res
        company["deeds"] = deeds_res

        # Check for suspicious nominee handover
        handover = hist_res.get("nominee_handover_analysis", {})
        if handover.get("suspicious_handover") and handover.get("risk_score_delta"):
            company["risk_score"] = company.get("risk_score", 0) + handover["risk_score_delta"]
            for reason in handover.get("reasons", []):
                company["risk_factors"].append(reason)

        # Affiliated network for primary executive
        if ex and net_res:
            cur_norm = normalize_label(company.get("legal_name") or "")
            aff_filtered = [
                c for c in net_res.get("affiliated_companies", [])
                if normalize_label(c.get("name", "")) != cur_norm
            ]
            ex[0]["affiliated_companies"] = aff_filtered
            ex[0]["total_affiliations"] = len(aff_filtered)
            if net_res.get("serial_liquidator_risk"):
                ex[0]["serial_liquidator_risk"] = True
                company["risk_score"] = company.get("risk_score", 0) + 30
                company["risk_factors"].append(f"Konateľ {ex[0].get('name')} má väzby na subjekty v likvidácii/konkurze (riziko sériového likvidátora).")

        return ex, ow
    except Exception as e:
        company["people_source"] = f"PARSE_ERROR:{type(e).__name__}"
        return [], []


def ensure_sk_people_for_company(
    company: Dict[str, Any], 
    executives: Optional[List[Dict[str, Any]]] = None, 
    owners: Optional[List[Dict[str, Any]]] = None
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Synchronous wrapper for backward compatibility"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If in running loop, run in thread or basic sync
            ico = _clean(company.get("atlas_id") or company.get("ico") or "")
            res = fetch_vypis_html(ico)
            company["orsr_vypis_url"] = res.vypis_url
            if res.ok and res.html:
                parsed = parse_orsr_people(res.html)
                ex = parsed.get("executives", [])
                ow = parsed.get("owners", [])
                company["executives"] = ex
                company["owners"] = ow
                _enrich_company_fields_from_parsed(company, parsed)
                return ex, ow
            return [], []
        else:
            return loop.run_until_complete(ensure_sk_people_for_company_async(company, executives, owners))
    except Exception:
        # Fallback simple sync
        ico = _clean(company.get("atlas_id") or company.get("ico") or "")
        res = fetch_vypis_html(ico)
        company["orsr_vypis_url"] = res.vypis_url
        if res.ok and res.html:
            parsed = parse_orsr_people(res.html)
            ex = parsed.get("executives", [])
            ow = parsed.get("owners", [])
            company["executives"] = ex
            company["owners"] = ow
            _enrich_company_fields_from_parsed(company, parsed)
            return ex, ow
        return [], []
