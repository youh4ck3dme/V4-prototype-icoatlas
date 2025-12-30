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
    return bool(os.getenv("DATABASE_URL") or os.getenv("DB_DSN"))


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
        
        elif detected_country == "CZ":
            from ...services.ares_service import AresService
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
        
        elif detected_country == "HU":
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
                except:
                    # Fallback to CZ
                    from ...services.ares_service import AresService
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
    if graph == 1 and company["country"] == "SK":
        try:
            from ...services.orsr_people_integration import ensure_sk_people_for_company
            executives, owners = ensure_sk_people_for_company(company, executives, owners)
        except Exception:
            pass

    # Optional: Include relationship graph
    if graph == 1:
        if has_db():
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
