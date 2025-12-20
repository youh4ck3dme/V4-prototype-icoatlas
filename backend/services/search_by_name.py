"""
Vyhľadávanie podľa názvu - Hybridný model (lokálna DB + live V4 API)
"""

import asyncio
from typing import Dict, List, Optional

from sqlalchemy import func, or_, Text

from services.database import CompanyCache, get_db_session
from services.v4_service import V4Service
from services.v4_clients import V4APIError, RateLimitError, NotFoundError


def normalize_query(query: str) -> str:
    """
    Normalizuje vyhľadávací query.

    - Odstráni diakritiku
    - Zmení na lowercase
    - Odstráni extra medzery
    """
    import unicodedata

    # Odstrániť diakritiku
    normalized = unicodedata.normalize("NFD", query)
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # Lowercase a trim
    normalized = normalized.lower().strip()

    # Odstrániť extra medzery
    normalized = " ".join(normalized.split())

    return normalized


async def search_by_name(
    query: str, country: Optional[str] = None, limit: int = 20, include_live: bool = True
) -> List[Dict]:
    """
    Vyhľadá firmy podľa názvu - hybridný model (lokálna DB + live V4 API).

    Args:
        query: Vyhľadávací text (názov firmy)
        country: Krajina (SK, CZ, PL, HU) - voliteľné
        limit: Maximálny počet výsledkov
        include_live: Či zahrnúť live V4 API vyhľadávanie

    Returns:
        List s firmami (kombinované z DB a live API)
    """
    if not query or len(query) < 2:
        return []

    # Normalizovať query
    query_normalized = normalize_query(query)

    # Najprv vyhľadať v lokálnej DB
    local_results = _search_local_db(query_normalized, country, limit)

    # Ak je požadované live vyhľadávanie a je zadaná krajina
    live_results = []
    if include_live and country:
        try:
            live_results = await _search_live_api(country, query, limit)
        except Exception as e:
            print(f"⚠️ Live API search failed: {e}")

    # Kombinovať výsledky (odstrániť duplikáty, uprednostniť live dáta)
    combined_results = _combine_results(local_results, live_results, limit)

    return combined_results


def _search_local_db(query_normalized: str, country: Optional[str], limit: int) -> List[Dict]:
    """Vyhľadávanie v lokálnej databáze"""
    with get_db_session() as db:
        if not db:
            return []

        # PostgreSQL full-text search alebo LIKE/ILIKE
        results = None

        # Skontrolovať, či existuje pg_trgm rozšírenie
        try:
            # Full-text search s pg_trgm (similarity)
            from sqlalchemy import text

            # Použiť similarity search (pg_trgm)
            similarity_query = text(
                """
                SELECT id, company_name, data, company_data, country, risk_score,
                        updated_at, last_synced_at,
                        similarity(company_name, :query) as sim_score
                FROM company_cache
                WHERE company_name % :query
                    OR CAST(data AS text) % :query
                ORDER BY sim_score DESC, updated_at DESC
                LIMIT :limit
                """
            )

            results_raw = db.execute(
                similarity_query, {"query": query_normalized, "limit": limit}
            ).fetchall()

            if results_raw:
                # Konvertovať výsledky
                results = []
                for row in results_raw:
                    company = (
                        db.query(CompanyCache).filter(CompanyCache.id == row.id).first()
                    )
                    if company:
                        results.append(company)

                if results:
                    print(
                        f"✅ Full-text search (pg_trgm) použité pre: {query_normalized}"
                    )
        except Exception as e:
            db.rollback()  # Rollback transaction so we can continue with fallback
            print(f"⚠️ Full-text search nie je dostupný: {e}, používam ILIKE")
            results = None

        # Fallback na ILIKE ak full-text search zlyhal
        if not results:
            # Vytvoriť search pattern
            search_pattern = f"%{query_normalized}%"

            # Základný query
            db_query = db.query(CompanyCache).filter(
                or_(
                    CompanyCache.company_name.ilike(search_pattern),
                    # Môžeme hľadať aj v JSON dátach (adresa, atď.)
                    func.cast(CompanyCache.data, Text).ilike(search_pattern),
                )
            )

            # Filtrovať podľa krajiny ak je zadaná
            if country:
                db_query = db_query.filter(CompanyCache.country == country.upper())

            # Zoradiť podľa relevance (názov má prednosť)
            results = (
                db_query.order_by(
                    CompanyCache.company_name.ilike(
                        f"{query_normalized}%"
                    ).desc(),  # Začína sa s query
                    CompanyCache.company_name.ilike(
                        search_pattern
                    ).desc(),  # Obsahuje query
                    CompanyCache.updated_at.desc(),  # Najnovšie aktualizované
                )
                .limit(limit)
                .all()
            )

        # Konvertovať na dict s označením zdroja
        companies = []
        for company in results:
            company_data = company.company_data or company.data or {}
            companies.append(
                {
                    "identifier": company.identifier,
                    "country": company.country,
                    "name": company.company_name
                    or company_data.get("name", "Neznáma firma"),
                    "legal_form": company_data.get("legal_form"),
                    "address": company_data.get("address"),
                    "risk_score": company.risk_score,
                    "last_synced_at": company.last_synced_at.isoformat()
                    if company.last_synced_at
                    else None,
                    "source": "local_db",
                }
            )

        return companies


async def _search_live_api(country: str, query: str, limit: int) -> List[Dict]:
    """Vyhľadávanie cez live V4 API"""
    v4_service = V4Service()
    try:
        companies = await v4_service.search_v4_by_name(country, query, limit)

        # Konvertovať NormalizedCompany na dict formát
        results = []
        for company in companies:
            results.append(
                {
                    "identifier": company.primary_id,
                    "country": company.country,
                    "name": company.legal_name,
                    "legal_form": company.legal_form,
                    "address": f"{company.city}, {company.street}".strip(", "),
                    "risk_score": company.risk_score,
                    "last_synced_at": company.fetched_at,
                    "source": "live_api",
                }
            )
        return results
    except (V4APIError, RateLimitError, NotFoundError) as e:
        print(f"⚠️ Live API search error: {e}")
        return []


def _combine_results(local_results: List[Dict], live_results: List[Dict], limit: int) -> List[Dict]:
    """Kombinovať výsledky z lokálnej DB a live API, odstrániť duplikáty"""
    # Vytvoriť map pre rýchle vyhľadávanie duplikátov (kľúč: country + identifier)
    seen = set()
    combined = []

    # Najprv pridať live výsledky (uprednostniť aktuálne dáta)
    for result in live_results:
        key = f"{result['country']}_{result['identifier']}"
        if key not in seen:
            seen.add(key)
            combined.append(result)

    # Potom pridať lokálne výsledky, ktoré nie sú v live výsledkoch
    for result in local_results:
        key = f"{result['country']}_{result['identifier']}"
        if key not in seen:
            seen.add(key)
            combined.append(result)

    # Obmedziť na limit
    return combined[:limit]


def search_by_address(
    query: str, country: Optional[str] = None, limit: int = 20
) -> List[Dict]:
    """
    Vyhľadá firmy podľa adresy v lokálnej DB.

    Args:
        query: Vyhľadávací text (adresa)
        country: Krajina (SK, CZ, PL, HU) - voliteľné
        limit: Maximálny počet výsledkov

    Returns:
        List s firmami
    """
    if not query or len(query) < 2:
        return []

    # Normalizovať query
    query_normalized = normalize_query(query)
    search_pattern = f"%{query_normalized}%"

    with get_db_session() as db:
        if not db:
            return []

        # Hľadať v JSON dátach (adresa)
        db_query = db.query(CompanyCache).filter(
            func.cast(CompanyCache.data, Text).ilike(search_pattern)
        )

        if country:
            db_query = db_query.filter(CompanyCache.country == country.upper())

        results = db_query.order_by(CompanyCache.updated_at.desc()).limit(limit).all()

        companies = []
        for company in results:
            company_data = company.company_data or company.data or {}
            address = company_data.get("address", "")

            # Skontrolovať, či adresa obsahuje query
            if query_normalized in normalize_query(address):
                companies.append(
                    {
                        "identifier": company.identifier,
                        "country": company.country,
                        "name": company.company_name
                        or company_data.get("name", "Neznáma firma"),
                        "address": address,
                        "risk_score": company.risk_score,
                    }
                )

        return companies
