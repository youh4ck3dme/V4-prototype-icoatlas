import os
from datetime import datetime
from typing import Dict, Optional, List
from .v4_clients import (
    SKRPOClient, CZARESClient, PLKRSClient, HUNAVClient,
    NormalizedCompany, V4APIError, NotFoundError, RateLimitError
)
from .cache import get, set as cache_set, get_cache_key
from .rate_limiter import is_allowed, get_client_id
from .error_handler import log_error, ExternalAPIError
from .sk_orsr_provider import get_orsr_provider # Import Phase 17 provider
from fastapi import Request

class V4Service:
    """Unified Service for V4 Company Data"""

    def __init__(self):
        # Initialize Clients with ENV credentials
        self.sk_client = SKRPOClient(api_key=os.getenv("SK_RPO_API_KEY"))
        self.cz_client = CZARESClient()
        self.pl_client = PLKRSClient()
        # HU client requires complex auth, only init if creds exist
        hu_login = os.getenv("HU_NAV_LOGIN")
        if hu_login:
            self.hu_client = HUNAVClient(
                login=hu_login,
                password=os.getenv("HU_NAV_PASSWORD", ""),
                signing_key=os.getenv("HU_NAV_SIGNING_KEY", ""),
                tax_number=os.getenv("HU_NAV_TAX_NUMBER", "")
            )
        else:
            self.hu_client = None

    async def search_company(self, country: str, query: str) -> Dict:
        """
        Unified search method.
        country: SK, CZ, PL, HU
        query: IČO, KRS, or Tax Number
        """
        country = country.upper()
        
        try:
            if country == "SK":
                # Use Phase 17 ORSR Provider
                # Assuming query is IČO
                provider = get_orsr_provider()
                data = provider.lookup_by_ico(query)
                if not data:
                    raise NotFoundError(f"Company {query} not found in ORSR")
                return self._normalize_sk(data)
            
            elif country == "CZ":
                data = await self.cz_client.search_by_ico(query)
                return self._normalize_cz(data)

            elif country == "PL":
                # Assuming query is KRS
                data = await self.pl_client.get_current_extract(query)
                return self._normalize_pl(data)
            
            elif country == "HU":
                if not self.hu_client:
                    raise V4APIError("HU Client not configured (missing credentials)")
                # Query is tax number
                data = await self.hu_client.query_taxpayer(query)
                return self._normalize_hu(data)
            
            else:
                raise V4APIError(f"Unsupported country: {country}")

        except NotFoundError:
            return {"found": False, "message": "Company not found in register"}
        except Exception as e:
            return {"error": str(e), "country": country}

    async def search_v4_company(self, country: str, identifier: str, request: Optional[Request] = None) -> NormalizedCompany:
        """
        Search for a company by identifier with caching, rate limiting, and error handling.

        Args:
            country: Country code (SK, CZ, PL, HU)
            identifier: Company identifier (IČO, KRS, etc.)
            request: FastAPI request for rate limiting

        Returns:
            NormalizedCompany object

        Raises:
            V4APIError: For API errors
            RateLimitError: When rate limit exceeded
            NotFoundError: When company not found
        """
        country = country.upper()

        # Rate limiting check
        if request:
            client_id = get_client_id(request)
            allowed, info = is_allowed(client_id)
            if not allowed:
                raise RateLimitError(info.get('retry_after', 60))

        # Cache key
        cache_key = get_cache_key(f"{country}:{identifier}", "v4_search")

        # Check cache first
        cached_result = get(cache_key)
        if cached_result:
            from .error_handler import logger
            logger.info(f"V4 Search: {country}:{identifier} | Cache: True")
            return cached_result

        start_time = datetime.now()
        cache_hit = False
        try:
            # Perform search based on country
            if country == "SK":
                provider = get_orsr_provider()
                data = provider.lookup_by_ico(identifier)
                if not data:
                    raise NotFoundError(f"Company {identifier} not found in ORSR")
                result = self._normalize_sk(data)
            elif country == "CZ":
                data = await self.cz_client.search_by_ico(identifier)
                result = self._normalize_cz(data)
            elif country == "PL":
                data = await self.pl_client.get_current_extract(identifier)
                result = self._normalize_pl(data)
            elif country == "HU":
                if not self.hu_client:
                    raise V4APIError("HU Client not configured")
                data = await self.hu_client.query_taxpayer(identifier)
                result = self._normalize_hu(data)
            else:
                raise V4APIError(f"Unsupported country: {country}")

            duration = (datetime.now() - start_time).total_seconds() * 1000
            from .error_handler import logger
            logger.info(f"V4 Search: {country}:{identifier} | Provider: {result.source_api} | Duration: {duration:.2f}ms | Cache: {cache_hit}")

            # Cache the result
            cache_set(cache_key, result)

            return result

        except (V4APIError, NotFoundError, RateLimitError):
            # Re-raise V4 specific errors
            raise
        except Exception as e:
            # Log unexpected errors
            log_error(e, context={"country": country, "identifier": identifier})
            raise V4APIError(f"Unexpected error during search: {str(e)}")

    async def validate_v4_identifier(self, country: str, identifier: str, request: Optional[Request] = None) -> NormalizedCompany:
        """
        Validate an identifier and return company data if valid.
        Essentially the same as search_v4_company but focused on validation.

        Args:
            country: Country code (SK, CZ, PL, HU)
            identifier: Company identifier to validate
            request: FastAPI request for rate limiting

        Returns:
            NormalizedCompany object if identifier is valid

        Raises:
            V4APIError: For API errors
            RateLimitError: When rate limit exceeded
            NotFoundError: When identifier is invalid/not found
        """
        # For now, validation is the same as search - if we can retrieve data, it's valid
        return await self.search_v4_company(country, identifier, request)

    async def search_v4_by_name(self, country: str, name: str, limit: int = 10, request: Optional[Request] = None) -> List[NormalizedCompany]:
        """
        Search for companies by name using live V4 APIs.

        Args:
            country: Country code (SK, CZ, PL, HU)
            name: Company name to search for
            limit: Maximum number of results
            request: FastAPI request for rate limiting

        Returns:
            List of NormalizedCompany objects

        Raises:
            V4APIError: For API errors
            RateLimitError: When rate limit exceeded
        """
        country = country.upper()

        # Rate limiting check
        if request:
            client_id = get_client_id(request)
            allowed, info = is_allowed(client_id)
            if not allowed:
                raise RateLimitError(info.get('retry_after', 60))

        # Cache key
        cache_key = get_cache_key(f"{country}:name:{name}:{limit}", "v4_search_name")

        # Check cache first
        cached_result = get(cache_key)
        if cached_result:
            return cached_result

        try:
            companies = []

            if country == "SK":
                data = await self.sk_client.search_by_name(name, limit)
                # Parse autoform response - assuming it returns a list of companies
                for item in data.get("results", []):
                    companies.append(self._normalize_sk(item))

            elif country == "CZ":
                data = await self.cz_client.search_by_name(name, limit)
                # Parse ARES response
                ek_subs = data.get("ekonomickeSubjekty", [])
                for sub in ek_subs[:limit]:
                    companies.append(self._normalize_cz({"ekonomickeSubjekty": [sub]}))

            else:
                # Countries without name search API
                raise V4APIError(f"Name search not supported for country: {country}")

            # Cache the result
            cache_set(cache_key, companies)

            return companies

        except (V4APIError, NotFoundError, RateLimitError):
            raise
        except Exception as e:
            log_error(e, context={"country": country, "name": name})
            raise V4APIError(f"Unexpected error during name search: {str(e)}")

    async def sync_v4_changes(self, country: str, since: str, request: Optional[Request] = None) -> List[NormalizedCompany]:
        """
        Sync changes since a given timestamp.

        Args:
            country: Country code (SK, CZ, PL, HU)
            since: ISO timestamp string
            request: FastAPI request for rate limiting

        Returns:
            List of NormalizedCompany objects with changes

        Raises:
            V4APIError: For API errors
            RateLimitError: When rate limit exceeded
            NotImplementedError: For countries without sync support
        """
        country = country.upper()

        # Rate limiting check
        if request:
            client_id = get_client_id(request)
            allowed, info = is_allowed(client_id, tokens_required=5)  # Sync might be more expensive
            if not allowed:
                raise RateLimitError(info.get('retry_after', 60))

        # Cache key
        cache_key = get_cache_key(f"{country}:sync:{since}", "v4_sync")

        # Check cache first
        cached_result = get(cache_key)
        if cached_result:
            return cached_result

        try:
            companies = []

            if country == "SK":
                data = await self.sk_client.sync_changes(since)
                # Assuming data contains list of company changes
                # This depends on the actual API response structure
                for item in data.get("changes", []):
                    companies.append(self._normalize_sk(item))

            elif country == "PL":
                # Use daily bulletin for changes
                # Parse since date
                from datetime import datetime
                since_date = datetime.fromisoformat(since.replace('Z', '+00:00')).date().isoformat()
                data = await self.pl_client.get_daily_bulletin(since_date)
                # Parse bulletin data - this is simplified
                for item in data.get("entries", []):
                    companies.append(self._normalize_pl({"odpis": {"naglowekA": item}}))

            else:
                raise NotImplementedError(f"Sync not implemented for country: {country}")

            # Cache the result
            cache_set(cache_key, companies)

            return companies

        except (V4APIError, NotFoundError, RateLimitError):
            raise
        except Exception as e:
            log_error(e, context={"country": country, "since": since})
            raise V4APIError(f"Unexpected error during sync: {str(e)}")

    def _normalize_sk(self, data: Dict) -> NormalizedCompany:
        # Normalization for Slovak ORSR data
        # Use address normalizer to split address components
        from .address_normalizer import normalize_address
        addr = normalize_address(data.get("address", ""))
        return NormalizedCompany(
            country="SK",
            primary_id=data.get("ico") or data.get("company_id"), # Fallback
            tax_id=data.get("dic"),
            legal_name=data.get("name", ""),
            legal_form=data.get("legal_form"),
            status=data.get("status", "active"),
            street=addr.get("street"),
            city=addr.get("city"),
            city_part=addr.get("city_part"),
            postal_code=addr.get("postal_code"),
            executives=data.get("executives", []),
            shareholders=data.get("shareholders", []),
            source_api="SK_ORSR",
            fetched_at=datetime.now().isoformat(),
            raw_data=data
        )

    def _normalize_cz(self, data: Dict) -> NormalizedCompany:
        # ARES v2 structure
        ek_subs = data.get("ekonomickeSubjekty", [])
        if not ek_subs:
            raise NotFoundError("No data in ARES response")
        sub = ek_subs[0]
        sidlo = sub.get("sidlo", {})

        return NormalizedCompany(
            country="CZ",
            primary_id=sub.get("ico"),
            tax_id=sub.get("dic"),
            legal_name=sub.get("obchodniJmeno", ""),
            legal_form=sub.get("pravniForma"),
            status="active",  # Default
            street=sidlo.get("textovaAdresa"),
            source_api="CZ_ARES",
            fetched_at=datetime.now().isoformat(),
            raw_data=sub
        )

    def _normalize_pl(self, data: Dict) -> NormalizedCompany:
        # KRS structure
        odpis = data.get("odpis", {})
        header = odpis.get("naglowekA", {})
        return NormalizedCompany(
            country="PL",
            primary_id=header.get("numerKRS"),
            legal_name=header.get("nazwa", ""),
            legal_form=header.get("formaP"),
            status="active",  # Default
            source_api="PL_KRS",
            fetched_at=datetime.now().isoformat(),
            raw_data=data
        )

    def _normalize_hu(self, data: Dict) -> NormalizedCompany:
        # NAV XML structure (parsed)
        # TODO: Implement proper XML parsing normalization
        return NormalizedCompany(
            country="HU",
            primary_id=data.get("tax_number", ""),
            legal_name=data.get("name", ""),
            status="active",  # Default
            source_api="HU_NAV",
            fetched_at=datetime.now().isoformat(),
            raw_data=data
        )
