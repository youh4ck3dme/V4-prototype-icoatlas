import pytest
import asyncio
from httpx import AsyncClient
from hypothesis import given, strategies as st
from services.v4_clients import SKRPOClient, CZARESClient, NormalizedCompany
from services.sk_rpo import is_slovak_ico
from services.pl_biala_lista import is_polish_nip
from backend.tests.test_utils import validate_company_search_result


@pytest.mark.v4
@pytest.mark.asyncio
async def test_sk_rpo_mock(mock_v4_api):
    """Test SK client with mocked API"""
    client = SKRPOClient()
    response = await client.search_by_name("MOCK COMPANY SK")
    
    assert "results" in response
    assert response["results"][0]["name"] == "MOCK COMPANY SK"
    assert response["results"][0]["ico"] == "35763469"

@pytest.mark.v4
@pytest.mark.asyncio
async def test_cz_ares_mock(mock_v4_api):
    """Test CZ client with mocked API"""
    client = CZARESClient()
    response = await client.search_by_name("MOCK COMPANY CZ")
    
    assert "ekonomickeSubjekty" in response
    assert response["ekonomickeSubjekty"][0]["obchodniJmeno"] == "MOCK COMPANY CZ"
    assert response["ekonomickeSubjekty"][0]["ico"] == "27074358"

# Property-based testing
@given(ico=st.text(min_size=8, max_size=8, alphabet=st.characters(whitelist_categories=['Nd'])))
def test_ico_validation_properties(ico):
    """Test validity of is_slovak_ico with generated 8-digit numbers"""
    # This just ensures it doesn't crash and returns a boolean
    result = is_slovak_ico(ico)
    assert isinstance(result, bool)

@given(nip=st.text())
def test_nip_validation_properties(nip):
    """Test validity of is_polish_nip with random text"""
    # Should safely return False for random text, True only for valid
    result = is_polish_nip(nip)
    assert isinstance(result, bool)

@given(
    country=st.sampled_from(['SK', 'CZ', 'PL', 'HU']),
    primary_id=st.text(min_size=1),
    legal_name=st.text(min_size=1)
)
def test_normalized_company_properties(country, primary_id, legal_name):
    """Test NormalizedCompany creation with generated data"""
    company = NormalizedCompany(
        country=country,
        primary_id=primary_id,
        legal_name=legal_name,
        status="active",
        source_api="test",
        fetched_at="2024-01-01"
    )
    assert company.country == country
    assert company.primary_id == primary_id
    assert company.legal_name == legal_name

@pytest.mark.integration
class TestV4Integration:
    """Integration tests for V4 functionality"""

    def test_full_search_workflow(self, mock_v4_api):
        """Test complete search workflow using hybrid search"""
        from backend.services.search_by_name import search_by_name

        # Test hybrid search with live API (mocked via respx)
        # Note: search_by_name calls asyncio.run() internally, so this test MUST be sync
        results = search_by_name("MOCK COMPANY SK", country="SK", include_live=True)

        # Verify we have results
        assert len(results) > 0

        # Verify structure using test util
        # Note: Hybrid search returns dicts, not NormalizedCompany
        for company in results:
            validate_company_search_result(company)
            assert company['country'] == 'SK'

