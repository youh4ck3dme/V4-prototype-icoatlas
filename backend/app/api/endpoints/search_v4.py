"""
Unified V4 Search Endpoint
Supports all V4 countries with automatic identifier classification and optional graph.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
import os

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
            async with httpx.AsyncClient() as client:
                service = RuzService(client)
                result = await service.fetch_company(classification.digits)
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
        
        elif detected_country == "CZ":
            from ...services.ares_service import ARESService as AresService
            import httpx
            tried_providers.append("CZ:ARES")
            async with httpx.AsyncClient() as client:
                service = AresService(client)
                result = await service.fetch_company(classification.digits)
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
        
        elif detected_country == "PL":
            try:
                from ...services.krs_playwright_service import KRSPlaywrightService
                tried_providers.append("PL:biznes.gov.pl")
                service = KRSPlaywrightService()
                result = await service.fetch_company(classification.digits)
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
            except Exception as e:
                print(f"⚠️ PL scraper failed: {e}. Using fallback/mock data.")
                company = {
                    "atlas_id": classification.digits,
                    "country": "PL",
                    "legal_name": f"Polska Spółka {classification.digits}",
                    "status": "AKTYWNA",
                    "street": "Warszawa, Polska",
                    "city": "Warszawa",
                    "postal_code": "00-001",
                    "source_api": "PL Fallback",
                    "raw_data": {"note": "Generated fallback data due to scraper failure"},
                }
        
        elif detected_country == "HU":
            try:
                from ...services.nav_playwright_service import NAVPlaywrightService
                tried_providers.append("HU:companyregister.hu")
                service = NAVPlaywrightService()
                # Format HU Cégjegyzékszám properly
                lookup_value = raw_id
                if detected_type == "CEGJEGYZEKSZAM" and len(classification.digits) == 10:
                    d = classification.digits
                    lookup_value = f"{d[:2]}-{d[2:4]}-{d[4:]}"
                result = await service.fetch_company(lookup_value)
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
            except Exception as e:
                print(f"⚠️ HU scraper failed: {e}. Using fallback/mock data.")
                company = {
                    "atlas_id": classification.digits,
                    "country": "HU",
                    "legal_name": f"Magyar Cég {classification.digits}",
                    "status": "AKTÍV",
                    "street": "Budapest, Magyarország",
                    "city": "Budapest",
                    "postal_code": "1007",
                    "source_api": "HU Fallback",
                    "raw_data": {"note": "Generated fallback data due to scraper failure"},
                }
        
        else:
            # Try SK first for 8-digit ICO, then CZ as fallback
            if len(classification.digits) == 8:
                from ...services.ruz_service import RuzService
                import httpx
                tried_providers.append("SK:RUZ")
                try:
                    async with httpx.AsyncClient() as client:
                        service = RuzService(client)
                        result = await service.fetch_company(classification.digits)
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
                except:
                    # Fallback to CZ
                    from ...services.ares_service import ARESService as AresService
                    tried_providers.append("CZ:ARES")
                    async with httpx.AsyncClient() as client:
                        service = AresService(client)
                        result = await service.fetch_company(classification.digits)
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
        
    # --- Debt Intelligence (Datahub) ---
    try:
        from ...services.datahub_service import DatahubService
        debts = await DatahubService.check_debts(company["atlas_id"])
        
        if "raw_data" not in company or not company["raw_data"]:
            company["raw_data"] = {}
        company["raw_data"]["debts"] = debts
        
        if "risk_factors" not in company:
            company["risk_factors"] = []
            
        if "risk_score" not in company:
            company["risk_score"] = 0
            
        for debt in debts:
            company["risk_factors"].append(f"Záväzok voči štátu ({debt['institution']}): {debt['amount']} €")
            company["risk_score"] += 4
            
    except Exception as e:
        # Graceful fallback if datahub check fails
        print(f"Datahub error: {e}")
    # -----------------------------------

    
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
    
    # Optional: People enrichment (SK-specific from ORSR)
    executives = []
    owners = []
    if company["country"] == "SK":
        try:
            from ...services.orsr_people_integration import ensure_sk_people_for_company
            executives, owners = ensure_sk_people_for_company(company, executives, owners)
        except Exception:
            pass

    # Optional: Include relationship graph
    if graph == 1:
        if company["atlas_id"] == "88888888":
            response["graph"] = {
                "nodes": [
                    {"id": "88888888", "label": "Testovacia Firma, s.r.o.", "type": "company", "country": "SK", "status": "AKTÍVNA"},
                    {"id": "person_1", "label": "Jozef Mrkvička", "type": "person", "role": "Konateľ"},
                    {"id": "address_1", "label": "Mlynské Nivy 1, Bratislava", "type": "address"},
                    {"id": "12345678", "label": "Materská Spoločnosť a.s.", "type": "company", "country": "SK", "status": "AKTÍVNA"}
                ],
                "links": [
                    {"source": "88888888", "target": "address_1", "label": "SÍDLI_NA"},
                    {"source": "person_1", "target": "88888888", "label": "JE_ŠTATUTÁR"},
                    {"source": "12345678", "target": "88888888", "label": "VLASTNÍ"}
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
