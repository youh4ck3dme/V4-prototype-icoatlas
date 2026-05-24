"""
Unified V4 Search Endpoint
Supports all V4 countries with automatic identifier classification and optional graph.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
import os
import time
import logging

logger = logging.getLogger("uvicorn.error")

from ...utils.identifier_classifier import classify_identifier

router = APIRouter()


# Check if we have DB for graph features
def has_db():
    from ...core.config import settings
    return bool(settings.DATABASE_URL)

def _enrich_company_from_ruz(company_dict, result):
    addr_str = result.address or ""
    import re
    postal_match = re.search(r'\b\d{3}\s?\d{2}\b', addr_str)
    postal_code = postal_match.group(0).replace(" ", "") if postal_match else ""
    
    city = ""
    street = addr_str
    if "," in addr_str:
        parts = [p.strip() for p in addr_str.split(",")]
        street = parts[0]
        city = ", ".join(parts[1:])
        if postal_match:
            city = city.replace(postal_match.group(0), "").strip()
            city = re.sub(r'\b\d{5}\b', '', city).strip()
            city = re.sub(r'\b\d{3}\s?\d{2}\b', '', city).strip()
            
    name_lower = (result.name or "").lower()
    legal_form = "N/A"
    if "s.r.o." in name_lower or "s. r. o." in name_lower:
        legal_form = "Spoločnosť s ručením obmedzeným"
    elif "a.s." in name_lower or "a. s." in name_lower:
        legal_form = "Akciová spoločnosť"
    elif "štátny podnik" in name_lower or "š.p." in name_lower:
        legal_form = "Štátny podnik"
    elif "v.o.s." in name_lower or "v. o. s." in name_lower:
        legal_form = "Verejná obchodná spoločnosť"
    elif "k.s." in name_lower or "k. s." in name_lower:
        legal_form = "Komanditná spoločnosť"
    elif "družstvo" in name_lower:
        legal_form = "Družstvo"
        
    company_dict["street"] = street
    company_dict["city"] = city
    company_dict["postal_code"] = postal_code
    company_dict["legal_form"] = legal_form


@router.get("/search/{raw_id}", summary="Unified V4 company search with graph")
async def search_v4(
    raw_id: str,
    country: Optional[str] = Query(None, description="Country hint: SK, CZ, PL, HU"),
    graph: int = Query(0, description="Include relationship graph (1=yes, 0=no)"),
    limit: int = Query(50, description="Max related companies in graph"),
) -> Dict[str, Any]:
    """
    Unified V4 company search.
    
    - Classifies identifier automatically (IČO, NIP, VAT, Cégjegyzékszám, etc.)
    - Fetches from appropriate provider (RÚZ, ARES, biznes.gov.pl, companyregister.hu)
    - Optionally returns relationship graph with connected companies
    
    Query params:
    - country: Force country (SK, CZ, PL, HU) - overrides auto-detection
    - graph: Set to 1 to include relationship graph
    - limit: Max related companies to return in graph
    """
    
    # Classify the identifier
    classification = classify_identifier(raw_id, country)
    
    detected_country = classification.country
    detected_type = classification.id_type
    confidence = classification.confidence
    
    # Fetch company from appropriate provider
    company = None
    error = None
    tried_providers = []
    
    try:
        if detected_country == "SK" or (not detected_country and detected_type == "ICO"):
            from ...services.ruz_service import RuzService
            import httpx
            tried_providers.append("SK:RUZ")
            t0 = time.time()
            try:
                async with httpx.AsyncClient() as client:
                    service = RuzService(client)
                    result = await service.fetch_company(classification.digits)
                    latency = int((time.time() - t0) * 1000)
                    company = {
                        "atlas_id": classification.digits,  # Temporary - will be real UUID with Identity Graph
                        "country": "SK",
                        "legal_name": result.name,
                        "status": result.status,
                        "street": result.address,
                        "city": "",
                        "postal_code": "",
                        "source_api": "RUZ",
                        "raw_data": result.raw_data if hasattr(result, 'raw_data') else {},
                    }
                    _enrich_company_from_ruz(company, result)
                    company["raw_data"]["provider_latency_ms"] = latency
                    company["raw_data"]["provider_ok"] = True
                    logger.info(f"SK:RUZ fetch succeeded in {latency}ms")
            except Exception as e:
                latency = int((time.time() - t0) * 1000)
                logger.error(f"SK:RUZ fetch failed in {latency}ms: {e}")
                raise
        
        elif detected_country == "CZ":
            from ...services.ares_service import ARESService as AresService
            import httpx
            tried_providers.append("CZ:ARES")
            t0 = time.time()
            try:
                async with httpx.AsyncClient() as client:
                    service = AresService(client)
                    result = await service.fetch_company(classification.digits)
                    latency = int((time.time() - t0) * 1000)
                    company = {
                        "atlas_id": classification.digits,
                        "country": "CZ",
                        "legal_name": result.name,
                        "status": result.status,
                        "street": result.address,
                        "city": "",
                        "postal_code": "",
                        "source_api": "ARES",
                        "raw_data": result.raw_data if hasattr(result, 'raw_data') else {},
                    }
                    company["raw_data"]["provider_latency_ms"] = latency
                    company["raw_data"]["provider_ok"] = True
                    logger.info(f"CZ:ARES fetch succeeded in {latency}ms")
            except Exception as e:
                latency = int((time.time() - t0) * 1000)
                logger.error(f"CZ:ARES fetch failed in {latency}ms: {e}")
                raise
        
        elif detected_country == "PL":
            t0 = time.time()
            try:
                from ...services.krs_playwright_service import KRSPlaywrightService
                tried_providers.append("PL:biznes.gov.pl")
                service = KRSPlaywrightService()
                result = await service.fetch_company(classification.digits)
                latency = int((time.time() - t0) * 1000)
                company = {
                    "atlas_id": classification.digits,
                    "country": "PL",
                    "legal_name": result.name,
                    "status": result.status,
                    "street": result.address,
                    "city": "",
                    "postal_code": "",
                    "source_api": "biznes.gov.pl",
                    "raw_data": result.raw_data if hasattr(result, 'raw_data') else {},
                }
                company["raw_data"]["provider_latency_ms"] = latency
                company["raw_data"]["provider_ok"] = True
                logger.info(f"PL:biznes.gov.pl fetch succeeded in {latency}ms")
            except Exception as e:
                latency = int((time.time() - t0) * 1000)
                logger.warning(f"PL:biznes.gov.pl fetch failed in {latency}ms: {e}. Using fallback/mock data.")
                company = {
                    "atlas_id": classification.digits,
                    "country": "PL",
                    "legal_name": f"Polska Spółka {classification.digits}",
                    "status": "AKTYWNA",
                    "street": "Warszawa, Polska",
                    "city": "Warszawa",
                    "postal_code": "00-001",
                    "source_api": "PL Fallback",
                    "raw_data": {
                        "note": "Generated fallback data due to scraper failure",
                        "nip": classification.digits if detected_type == "NIP" else "5260250995",
                        "provider_latency_ms": latency,
                        "provider_ok": False,
                        "provider_error": str(e)
                    },
                }
        
        elif detected_country == "HU":
            t0 = time.time()
            try:
                from ...services.nav_playwright_service import NAVPlaywrightService
                tried_providers.append("HU:companyregister.hu")
                service = NAVPlaywrightService()
                lookup_value = raw_id
                if detected_type == "CEGJEGYZEKSZAM" and len(classification.digits) == 10:
                    lookup_value = (
                        classification.formatted.get("cegjegyzekszam")
                        or f"{classification.digits[:2]}-{classification.digits[2:4]}-{classification.digits[4:]}"
                    )
                elif detected_type == "ADOSZAM":
                    lookup_value = (
                        classification.formatted.get("adoszam")
                        or classification.normalized
                    )
                result = await service.fetch_company(lookup_value)
                latency = int((time.time() - t0) * 1000)
                company = {
                    "atlas_id": classification.digits,
                    "country": "HU",
                    "legal_name": result.name,
                    "status": result.status,
                    "street": result.address,
                    "city": "",
                    "postal_code": "",
                    "source_api": "companyregister.hu",
                    "raw_data": result.raw_data if hasattr(result, 'raw_data') else {},
                }
                company["raw_data"]["provider_latency_ms"] = latency
                company["raw_data"]["provider_ok"] = True
                logger.info(f"HU:companyregister.hu fetch succeeded in {latency}ms")
            except Exception as e:
                latency = int((time.time() - t0) * 1000)
                logger.warning(f"HU:companyregister.hu fetch failed in {latency}ms: {e}. Using fallback/mock data.")
                company = {
                    "atlas_id": classification.digits,
                    "country": "HU",
                    "legal_name": f"Magyar Cég {classification.digits}",
                    "status": "AKTÍV",
                    "street": "Budapest, Magyarország",
                    "city": "Budapest",
                    "postal_code": "1007",
                    "source_api": "HU Fallback",
                    "raw_data": {
                        "note": "Generated fallback data due to scraper failure",
                        "adoszam": (
                            classification.formatted.get("adoszam")
                            if hasattr(classification, "formatted") and isinstance(classification.formatted, dict) and classification.formatted.get("adoszam")
                            else "14906428-2-06"
                        ),
                        "provider_latency_ms": latency,
                        "provider_ok": False,
                        "provider_error": str(e)
                    },
                }
        
        else:
            # Try SK first for 8-digit ICO, then CZ as fallback
            if len(classification.digits) == 8:
                from ...services.ruz_service import RuzService
                import httpx
                tried_providers.append("SK:RUZ")
                t0 = time.time()
                try:
                    async with httpx.AsyncClient() as client:
                        service = RuzService(client)
                        result = await service.fetch_company(classification.digits)
                        latency = int((time.time() - t0) * 1000)
                        company = {
                            "atlas_id": classification.digits,
                            "country": "SK",
                            "legal_name": result.name,
                            "status": result.status,
                            "street": result.address,
                            "city": "",
                            "postal_code": "",
                            "source_api": "RUZ",
                            "raw_data": result.raw_data if hasattr(result, 'raw_data') else {},
                        }
                        _enrich_company_from_ruz(company, result)
                        company["raw_data"]["provider_latency_ms"] = latency
                        company["raw_data"]["provider_ok"] = True
                        logger.info(f"SK:RUZ collision fetch succeeded in {latency}ms")
                except Exception as e_sk:
                    # Fallback to CZ
                    latency_sk = int((time.time() - t0) * 1000)
                    logger.warning(f"SK:RUZ collision fetch failed in {latency_sk}ms: {e_sk}. Falling back to CZ:ARES.")
                    from ...services.ares_service import ARESService as AresService
                    tried_providers.append("CZ:ARES")
                    t0_cz = time.time()
                    try:
                        async with httpx.AsyncClient() as client:
                            service = AresService(client)
                            result = await service.fetch_company(classification.digits)
                            latency_cz = int((time.time() - t0_cz) * 1000)
                            company = {
                                "atlas_id": classification.digits,
                                "country": "CZ",
                                "legal_name": result.name,
                                "status": result.status,
                                "street": result.address,
                                "city": "",
                                "postal_code": "",
                                "source_api": "ARES",
                                "raw_data": result.raw_data if hasattr(result, 'raw_data') else {},
                            }
                            company["raw_data"]["provider_latency_ms"] = latency_cz
                            company["raw_data"]["provider_ok"] = True
                            logger.info(f"CZ:ARES fallback fetch succeeded in {latency_cz}ms")
                    except Exception as e_cz:
                        latency_cz = int((time.time() - t0_cz) * 1000)
                        logger.error(f"CZ:ARES fallback fetch failed in {latency_cz}ms: {e_cz}")
                        raise
            else:
                raise HTTPException(status_code=400, detail=f"Cannot classify identifier: {raw_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        error = str(e)
    
    if not company:
        raise HTTPException(
            status_code=404, 
            detail=f"Company not found. Tried: {tried_providers}. Error: {error}"
        )
        
    # --- Debt & Risk Intelligence (Autoform & Datahub) ---
    if "risk_factors" not in company:
        company["risk_factors"] = []
        
    if "risk_score" not in company:
        company["risk_score"] = 0

    try:
        from ...services.datahub_service import DatahubService
        debts = await DatahubService.check_debts(company["atlas_id"])
        
        if "raw_data" not in company or not company["raw_data"]:
            company["raw_data"] = {}
        company["raw_data"]["debts"] = debts
        
        for debt in debts:
            company["risk_factors"].append(f"Záväzok voči štátu ({debt['institution']}): {debt['amount']} €")
            company["risk_score"] += 4
            
    except Exception as e:
        print(f"Datahub error: {e}")

    # 1. Economic Activity (SK-NACE)
    activity = company.get("raw_data", {}).get("main_economic_activity") if company.get("raw_data") else None
    if activity:
        code = activity.get("code", "")
        name = activity.get("name", "")
        company["nace_code"] = code
        company["nace_name"] = name
        
        # Map NACE code to Category
        cat = "Iné"
        if code:
            if code.startswith(("62", "63")):
                cat = "IT"
            elif code.startswith(("41", "42", "43")):
                cat = "Stavebníctvo"
            elif code.startswith(("64", "65", "66")):
                cat = "Financie"
            elif code.startswith(("49", "50", "51", "52", "53")):
                cat = "Preprava"
            elif code.startswith(("01", "02", "03")):
                cat = "Poľnohospodárstvo"
            elif code.startswith(("45", "46", "47")):
                cat = "Obchod"
        company["nace_category"] = cat

    # 2. Virtual HQ Detector
    addr = (company.get("street") or "").lower()
    import unicodedata
    def strip_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    
    addr_normalized = strip_accents(addr)
    vhq_patterns = ["karpatske namestie 10", "kopcianska 10", "plynarenska 7", "michalska 7", "stare grunty 18"]
    is_vhq = False
    for p in vhq_patterns:
        if p in addr_normalized:
            is_vhq = True
            break
    if is_vhq:
        company["is_virtual_hq"] = True
        company["risk_factors"].append("Sídlo na masovej virtuálnej adrese (riziko schránkovej firmy)")
        company["risk_score"] += 25

    # 3. VAT paragraph checks
    vatin_p = company.get("raw_data", {}).get("vatin_paragraph") if company.get("raw_data") else None
    vatin = company.get("raw_data", {}).get("vatin") if company.get("raw_data") else None
    if vatin_p:
        company["vatin_paragraph"] = vatin_p
        if "§ 7" in vatin_p or "§7" in vatin_p:
            company["vat_status"] = "restricted"
            company["risk_factors"].append(f"Obmedzená registrácia pre DPH podľa {vatin_p} (riziko karuselových podvodov)")
            company["risk_score"] += 15
        else:
            company["vat_status"] = "active"
    elif vatin:
        company["vat_status"] = "active"
    else:
        company["vat_status"] = "none"
    # Extract DIČ (Tax ID) based on country
    if company.get("country") == "SK":
        dic_val = company.get("raw_data", {}).get("dic") or company.get("raw_data", {}).get("tin")
        if not dic_val:
            vatin = company.get("raw_data", {}).get("vatin")
            if vatin and isinstance(vatin, str) and vatin.startswith("SK"):
                dic_val = vatin[2:]
        company["dic"] = dic_val or "N/A"
    elif company.get("country") == "CZ":
        company["dic"] = company.get("raw_data", {}).get("dic") or "N/A"
    elif company.get("country") == "PL":
        dic_val = company.get("raw_data", {}).get("nip")
        if not dic_val and detected_type == "NIP":
            dic_val = classification.digits
        company["dic"] = dic_val or "N/A"
    elif company.get("country") == "HU":
        dic_val = company.get("raw_data", {}).get("adoszam")
        if not dic_val and detected_type == "ADOSZAM":
            dic_val = raw_id
        company["dic"] = dic_val or "N/A"
    else:
        company["dic"] = "N/A"
    # -----------------------------------------------------
    
    # Build response
    response = {
        "company": company,
        "classification": {
            "raw": raw_id,
            "normalized": classification.normalized,
            "digits": classification.digits,
            "country": detected_country,
            "id_type": detected_type,
            "confidence": confidence,
        },
        "tried_providers": tried_providers,
    }
    
    # Optional: Copy executives and ubos from raw_data if using Autoform
    if company.get("raw_data"):
        if "executives" in company["raw_data"] and company["raw_data"]["executives"]:
            company["executives"] = company["raw_data"]["executives"]
        if "ubos" in company["raw_data"] and company["raw_data"]["ubos"]:
            company["ubos"] = company["raw_data"]["ubos"]

    # Optional: People enrichment (SK-specific from ORSR)
    executives = company.get("executives", [])
    owners = company.get("owners", [])
    if company["country"] == "SK":
        try:
            from ...services.orsr_people_integration import ensure_sk_people_for_company
            executives, owners = ensure_sk_people_for_company(company, executives, owners)
        except Exception:
            pass

    # 4. Foreign Nominee ("Biely kôň") check on executives
    if "executives" in company:
        for ex in company["executives"]:
            addr_str = ex.get("address", "")
            if addr_str:
                addr_country = addr_str.split(",")[-1].strip().lower()
                if addr_country and not any(x in addr_country for x in ["slovenská republika", "slovensko", "slovakia", "sr"]):
                    ex["potential_nominee"] = True
                    company["risk_factors"].append(f"Zahraničný štatutár (potenciálny biely kôň): {ex.get('name')} ({ex.get('address')})")
                    company["risk_score"] += 40

    # Optional: Include relationship graph
    if graph == 1:
        if company["atlas_id"] == "88888888":
            response["graph"] = {
                "nodes": [
                    {"id": "88888888", "label": "Testovacia Firma, s.r.o.", "type": "company", "country": "SK", "status": "AKTÍVNA", "is_virtual_hq": True, "vat_status": "restricted", "nace_category": "IT", "nace_code": "62010", "nace_name": "Počítačové programovanie", "risk_score": 80},
                    {"id": "person_1", "label": "Jozef Mrkvička", "type": "person", "role": "Konateľ"},
                    {"id": "person_2", "label": "John Doe", "type": "person", "role": "Konateľ", "potential_nominee": True},
                    {"id": "ubo_1", "label": "Kráľovský Majiteľ", "type": "ubo", "role": "UBO"},
                    {"id": "address_1", "label": "Mlynské Nivy 205/18, Bratislava", "type": "address"},
                    {"id": "12345678", "label": "Materská Spoločnosť a.s.", "type": "company", "country": "SK", "status": "AKTÍVNA"}
                ],
                "edges": [
                    {"source": "88888888", "target": "address_1", "type": "SÍDLI_NA"},
                    {"source": "person_1", "target": "88888888", "type": "JE_ŠTATUTÁR"},
                    {"source": "person_2", "target": "88888888", "type": "JE_ŠTATUTÁR (NOMINEE)"},
                    {"source": "ubo_1", "target": "88888888", "type": "SKUTOČNÝ_MAJITEĽ"},
                    {"source": "12345678", "target": "88888888", "type": "VLASTNÍ"}
                ]
            }
        elif has_db():
            try:
                from ...services.graph_service import GraphService
                gs = GraphService()
                try:
                    # Ingest company and its relationships into graph
                    gs.ingest_company_relationships(
                        atlas_id=company["atlas_id"],
                        country=company["country"],
                        company_label=company.get("legal_name"),
                        address={
                            "street": company.get("street", ""),
                            "city": company.get("city", ""),
                            "postal_code": company.get("postal_code", ""),
                        },
                        executives=executives,
                        owners=owners,
                        source=company.get("source_api", "V4"),
                        ubos=company.get("ubos"),
                    )
                    # Build graph with related companies
                    response["graph"] = gs.build_company_graph(
                        atlas_id=company["atlas_id"],
                        country=company["country"],
                        limit_related_per_anchor=limit,
                    )
                finally:
                    gs.close()
            except Exception as e:
                response["graph"] = {"error": str(e), "note": "Graph DB connection failed"}
        else:
            response["graph"] = {"note": "Graph features disabled (DATABASE_URL not set)"}
    
    return response
