"""
V4 Identifier Router
Routes company lookups to appropriate providers based on identifier classification.
Implements smart fallback logic for ambiguous cases.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from .identifier_classifier import classify_identifier, IdClassification


@dataclass
class ProviderResult:
    """Result from a single provider call."""
    provider: str
    country: str
    id_type: str
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]


@dataclass
class RouterResponse:
    """Complete response from the router."""
    input: str
    classification: Dict[str, Any]
    detected_country: Optional[str]
    detected_type: str
    confidence: float
    tried_providers: List[str]
    fallback_used: bool
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class IdentifierRouter:
    """
    Routes identifier lookups to appropriate V4 providers.
    Implements smart fallback for ambiguous cases (SK/CZ IČO, 10-digit chaos).
    """
    
    def __init__(self, providers: Dict[str, Any]):
        """
        Initialize router with provider instances.
        
        Args:
            providers: Dict with keys like 'sk', 'cz', 'pl', 'hu' pointing to service instances
        """
        self.providers = providers
    
    async def route(self, identifier: str, country_hint: Optional[str] = None) -> RouterResponse:
        """
        Route an identifier to the appropriate provider(s).
        
        Args:
            identifier: The company identifier to look up
            country_hint: Optional country code to prioritize
            
        Returns:
            RouterResponse with classification details and lookup results
        """
        # Classify the identifier
        classification = classify_identifier(identifier, country_hint)
        
        tried_providers: List[str] = []
        fallback_used = False
        result = None
        error = None
        
        # High confidence cases - direct routing
        if classification.confidence >= 0.85:
            result, error = await self._direct_lookup(classification)
            tried_providers.append(f"{classification.country}:{classification.id_type}")
        
        # IČO 8 digits - SK/CZ collision
        elif classification.id_type == "ICO" and len(classification.digits) == 8:
            result, error, tried_providers, fallback_used = await self._handle_ico_collision(classification)
        
        # 10 digits chaos
        elif len(classification.digits) == 10 and classification.id_type in ("UNKNOWN", "NIP", "KRS", "DIC"):
            result, error, tried_providers, fallback_used = await self._handle_ten_digit_chaos(classification)
        
        # Other cases with candidates - try primary then fallbacks
        elif classification.candidates:
            result, error, tried_providers, fallback_used = await self._try_with_fallbacks(classification)
        
        # Unknown - return error
        else:
            error = f"Cannot classify identifier: {identifier}"
        
        return RouterResponse(
            input=identifier,
            classification=asdict(classification),
            detected_country=classification.country,
            detected_type=classification.id_type,
            confidence=classification.confidence,
            tried_providers=tried_providers,
            fallback_used=fallback_used,
            result=result,
            error=error
        )
    
    async def _direct_lookup(self, classification: IdClassification) -> tuple:
        """Direct lookup for high-confidence classifications."""
        country = classification.country.lower() if classification.country else None
        
        if not country or country not in self.providers:
            return None, f"No provider for country: {country}"
        
        provider = self.providers[country]
        
        try:
            # Get the appropriate lookup value
            lookup_value = self._get_lookup_value(classification)
            result = await provider.fetch_company(lookup_value)
            return self._company_to_dict(result), None
        except Exception as e:
            return None, str(e)
    
    async def _handle_ico_collision(self, classification: IdClassification) -> tuple:
        """Handle SK/CZ IČO collision with smart fallback."""
        tried = []
        fallback = False
        
        # Determine order based on hint or default to SK first
        if classification.country == "CZ":
            order = ["cz", "sk"]
        else:
            order = ["sk", "cz"]
        
        for country in order:
            if country not in self.providers:
                continue
            
            tried.append(f"{country.upper()}:ICO")
            
            try:
                result = await self.providers[country].fetch_company(classification.digits)
                if result:
                    return self._company_to_dict(result), None, tried, fallback
            except Exception as e:
                # Try next provider
                fallback = True
                continue
        
        return None, "Not found in SK or CZ registers", tried, fallback
    
    async def _handle_ten_digit_chaos(self, classification: IdClassification) -> tuple:
        """Handle 10-digit identifiers (PL NIP/KRS, SK DIČ)."""
        tried = []
        fallback = False
        digits = classification.digits
        
        # Import here to check NIP checksum
        from .identifier_classifier import pl_nip_checksum_ok
        
        # If NIP checksum passes, try PL NIP first
        if pl_nip_checksum_ok(digits) and "pl" in self.providers:
            tried.append("PL:NIP")
            try:
                result = await self.providers["pl"].fetch_company(digits)
                if result:
                    return self._company_to_dict(result), None, tried, fallback
            except:
                fallback = True
        
        # Try based on hint
        if classification.country == "SK" and "sk" in self.providers:
            tried.append("SK:DIC")
            try:
                result = await self.providers["sk"].fetch_company(digits)
                if result:
                    return self._company_to_dict(result), None, tried, fallback
            except:
                fallback = True
        
        elif classification.country == "PL" and "pl" in self.providers:
            tried.append("PL:KRS")
            try:
                result = await self.providers["pl"].fetch_company(digits)
                if result:
                    return self._company_to_dict(result), None, tried, fallback
            except:
                fallback = True
        
        # No hint - try PL KRS then SK DIČ
        else:
            for country, id_type in [("pl", "KRS"), ("sk", "DIC")]:
                if country not in self.providers:
                    continue
                tried.append(f"{country.upper()}:{id_type}")
                try:
                    result = await self.providers[country].fetch_company(digits)
                    if result:
                        return self._company_to_dict(result), None, tried, fallback
                except:
                    fallback = True
                    continue
        
        return None, "Not found in PL or SK registers", tried, fallback
    
    async def _try_with_fallbacks(self, classification: IdClassification) -> tuple:
        """Try primary classification then fallback candidates."""
        tried = []
        fallback = False
        
        # Sort candidates by confidence
        candidates = sorted(
            classification.candidates,
            key=lambda x: x.get("confidence", 0),
            reverse=True
        )
        
        for candidate in candidates:
            country = candidate["country"].lower()
            id_type = candidate["id_type"]
            
            if country not in self.providers:
                continue
            
            tried.append(f"{country.upper()}:{id_type}")
            
            try:
                lookup_value = self._get_lookup_value_for_candidate(classification, candidate)
                result = await self.providers[country].fetch_company(lookup_value)
                if result:
                    return self._company_to_dict(result), None, tried, fallback
            except:
                fallback = True
                continue
        
        return None, "Not found in any register", tried, fallback
    
    def _get_lookup_value(self, classification: IdClassification) -> str:
        """Get the appropriate lookup value based on classification."""
        if classification.id_type == "CEGJEGYZEKSZAM":
            # Format HU Cégjegyzékszám properly
            if "cegjegyzekszam" in classification.formatted:
                return classification.formatted["cegjegyzekszam"]
            d = classification.digits
            if len(d) == 10:
                return f"{d[:2]}-{d[2:4]}-{d[4:]}"
        
        if classification.id_type == "ADOSZAM":
            if "adoszam" in classification.formatted:
                return classification.formatted["adoszam"]
        
        return classification.digits
    
    def _get_lookup_value_for_candidate(self, classification: IdClassification, candidate: Dict) -> str:
        """Get lookup value for a specific candidate."""
        id_type = candidate["id_type"]
        
        if id_type == "CEGJEGYZEKSZAM":
            d = classification.digits
            if len(d) == 10:
                return f"{d[:2]}-{d[2:4]}-{d[4:]}"
        
        return classification.digits
    
    def _company_to_dict(self, company) -> Dict[str, Any]:
        """Convert Company object to dict."""
        if hasattr(company, '__dict__'):
            return {
                "ico": getattr(company, "ico", None),
                "name": getattr(company, "name", None),
                "address": getattr(company, "address", None),
                "status": getattr(company, "status", None),
                "raw_data": getattr(company, "raw_data", {}),
            }
        return dict(company) if isinstance(company, dict) else {}


# Convenience function for creating router with default providers
async def create_default_router():
    """Create router with default V4 providers."""
    from ..services.ares_service import AresService
    from ..services.ruz_service import RuzService
    from ..services.krs_playwright_service import KRSPlaywrightService
    from ..services.nav_playwright_service import NAVPlaywrightService
    from httpx import AsyncClient
    
    async with AsyncClient() as client:
        providers = {
            "sk": RuzService(client),
            "cz": AresService(client),
            "pl": KRSPlaywrightService(),
            "hu": NAVPlaywrightService(),
        }
        return IdentifierRouter(providers)
