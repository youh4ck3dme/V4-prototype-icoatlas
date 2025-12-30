"""
Testy pre V4 klientov s mock API a property-based testing
"""
import pytest
import respx
from hypothesis import given, strategies as st, settings

from services.v4_clients import (
    SKRPOClient, CZARESClient, NormalizedCompany,
    V4APIError, RateLimitError, NotFoundError
)
from services.v4_service import V4Service


# Mock dáta pre rôzne krajiny
MOCK_SK_RPO_RESPONSE = {
    "id": 12345,
    "ico": "35763469",
    "name": "Slovenská sporiteľňa, a.s.",
    "legal_form": "Akciová spoločnosť",
    "address": {
        "street": "Tomášikova 48",
        "city": "Bratislava",
        "postal_code": "832 37"
    },
    "status": "active",
    "registration_date": "1994-01-01"
}

MOCK_CZ_ARES_RESPONSE = {
    "ekonomickeSubjekty": [
        {
            "ico": "27074358",
            "obchodniJmeno": "AGROFERT, a.s.",
            "sidlo": {
                "textovaAdresa": "Pyšelská 2327/2, 149 00 Praha 4"
            },
            "pravniForma": "Akciová společnost",
            "datumVzniku": "1993-07-29"
        }
    ]
}


@pytest.fixture
def mock_v4_apis():
    """Fixture pre mockovanie všetkých V4 API"""
    with respx.mock(assert_all_called=False) as respx_mock:
        # SK RPO API
        respx_mock.get("https://data.slovensko.sk/api/legal-subjects").respond(
            json=MOCK_SK_RPO_RESPONSE
        )
        respx_mock.get("https://data.slovensko.sk/api/autoform").respond(
            json={"results": [MOCK_SK_RPO_RESPONSE]}
        )

        # CZ ARES API
        respx_mock.post("https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat").respond(
            json=MOCK_CZ_ARES_RESPONSE
        )

        yield respx_mock


@pytest.fixture
def sk_client():
    """SK RPO klient s API kľúčom"""
    return SKRPOClient(api_key="test_key")


@pytest.fixture
def cz_client():
    """CZ ARES klient"""
    return CZARESClient()


@pytest.fixture
def v4_service():
    """V4Service instance"""
    return V4Service()


class TestSKRPOClient:
    """Testy pre SK RPO klienta"""

    @pytest.mark.asyncio
    async def test_search_by_ico_success(self, sk_client, mock_v4_apis):
        """Test úspešného vyhľadania podľa IČO"""
        result = await sk_client.search_by_ico("35763469")
        assert result["ico"] == "35763469"
        assert result["name"] == "Slovenská sporiteľňa, a.s."

    @pytest.mark.asyncio
    async def test_search_by_name_success(self, sk_client, mock_v4_apis):
        """Test úspešného vyhľadania podľa názvu"""
        result = await sk_client.search_by_name("Slovenská sporiteľňa", limit=10)
        assert "results" in result
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, sk_client):
        """Test rate limit handling"""
        with respx.mock() as respx_mock:
            respx_mock.get("https://data.slovensko.sk/api/legal-subjects").respond(
                status_code=429,
                headers={"Retry-After": "60"}
            )

            with pytest.raises(RateLimitError) as exc_info:
                await sk_client.search_by_ico("12345678")

            assert exc_info.value.retry_after == 60


class TestCZARESClient:
    """Testy pre CZ ARES klienta"""

    @pytest.mark.asyncio
    async def test_search_by_ico_success(self, cz_client, mock_v4_apis):
        """Test úspešného vyhľadania podľa IČO"""
        result = await cz_client.search_by_ico("27074358")
        assert result["ekonomickeSubjekty"][0]["ico"] == "27074358"
        assert "AGROFERT" in result["ekonomickeSubjekty"][0]["obchodniJmeno"]

    @pytest.mark.asyncio
    async def test_search_by_name_success(self, cz_client, mock_v4_apis):
        """Test úspešného vyhľadania podľa názvu"""
        result = await cz_client.search_by_name("Agrofert", limit=10)
        assert "ekonomickeSubjekty" in result
        assert len(result["ekonomickeSubjekty"]) > 0


class TestV4Service:
    """Testy pre V4Service"""

    @pytest.mark.asyncio
    async def test_search_v4_by_name_sk(self, v4_service, mock_v4_apis):
        """Test vyhľadania podľa názvu pre SK"""
        companies = await v4_service.search_v4_by_name("SK", "Slovenská sporiteľňa")
        assert len(companies) > 0
        assert companies[0].country == "SK"
        assert companies[0].primary_id == "35763469"

    @pytest.mark.asyncio
    async def test_search_v4_by_name_cz(self, v4_service, mock_v4_apis):
        """Test vyhľadania podľa názvu pre CZ"""
        companies = await v4_service.search_v4_by_name("CZ", "Agrofert")
        assert len(companies) > 0
        assert companies[0].country == "CZ"
        assert companies[0].primary_id == "27074358"

    @pytest.mark.asyncio
    async def test_unsupported_country(self, v4_service):
        """Test nepodporovanej krajiny"""
        with pytest.raises(V4APIError, match="not supported"):
            await v4_service.search_v4_by_name("XX", "Test Company")


# Property-based testing
class TestPropertyBased:
    """Property-based testy pomocou Hypothesis"""

    @given(
        ico=st.text(min_size=8, max_size=8, alphabet=st.characters(whitelist_categories=['Nd']))
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_sk_ico_format_validation(self, ico):
        """Test validácie SK IČO formátu"""
        client = SKRPOClient()

        with respx.mock() as respx_mock:
            respx_mock.get("https://data.slovensko.sk/api/legal-subjects").respond(
                json={"ico": ico, "name": "Test Company"}
            )

            result = await client.search_by_ico(ico)
            assert result["ico"] == ico

    @given(
        company_name=st.text(min_size=3, max_size=50, alphabet=st.characters(
            whitelist_categories=['L', 'N', 'P', 'Z', 'S'],
            blacklist_characters=['<', '>', '&']
        ))
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_company_name_search(self, company_name):
        """Test vyhľadania podľa názvu firmy s rôznymi názvami"""
        client = CZARESClient()

        with respx.mock() as respx_mock:
            respx_mock.post("https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat").respond(
                json={"ekonomickeSubjekty": [{"obchodniJmeno": company_name}]}
            )

            result = await client.search_by_name(company_name)
            assert "ekonomickeSubjekty" in result


# Integration testy
@pytest.mark.integration
class TestV4Integration:
    """Integration testy pre V4 funkcionality"""

    @pytest.mark.asyncio
    async def test_full_search_workflow(self, mock_v4_apis):
        """Test kompletného workflow vyhľadania"""
        from services.search_by_name import search_by_name

        # Test hybrid search s live API
        results = await search_by_name("Slovenská sporiteľňa", country="SK", include_live=True)

        # Overíme, že máme výsledky
        assert len(results) > 0

        # Overíme štruktúru výsledkov
        company = results[0]
        required_fields = ['identifier', 'country', 'name', 'source']
        for field in required_fields:
            assert field in company

    @pytest.mark.asyncio
    async def test_error_resilience(self, mock_v4_apis):
        """Test odolnosti voči chybám"""
        from services.search_by_name import search_by_name

        # Test s neexistujúcou krajinou - malo by fungovať len lokálne
        results = await search_by_name("Test", country="XX", include_live=True)
        assert isinstance(results, list)  # Nemalo by spadnúť


# Utility funkcie pre testy
def create_mock_company(country: str, identifier: str, name: str) -> dict:
    """Vytvorí mock company dáta pre testovanie"""
    return {
        "identifier": identifier,
        "country": country,
        "name": name,
        "legal_form": "s.r.o.",
        "address": "Test Address 123",
        "risk_score": 25,
        "source": "mock"
    }


def assert_company_structure(company: dict):
    """Overí štruktúru company objektu"""
    required_fields = ['identifier', 'country', 'name', 'source']
    for field in required_fields:
        assert field in company
        assert company[field] is not None


@pytest.fixture
def sample_companies():
    """Fixture s ukážkovými company dátami"""
    return [
        create_mock_company("SK", "12345678", "Test SK Company"),
        create_mock_company("CZ", "87654321", "Test CZ Company"),
        create_mock_company("PL", "000012345", "Test PL Company"),
    ]