"""
Shared pytest fixtures and configuration for V4 testing
"""
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock
import respx
from httpx import Response


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.database import get_db_session, init_database
from services.cache import clear
from services.v4_clients import (
    SKRPOClient, CZARESClient, NormalizedCompany
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test"""
    clear()


@pytest.fixture
def mock_sk_response() -> Dict[str, Any]:
    """Mock SK RPO API response"""
    return {
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


@pytest.fixture
def mock_cz_response() -> Dict[str, Any]:
    """Mock CZ ARES API response"""
    return {
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
def mock_pl_response() -> Dict[str, Any]:
    """Mock PL KRS API response"""
    return {
        "odpis": {
            "naglowekA": {
                "numerKRS": "0000028860",
                "nazwa": "ORLEN SPÓŁKA AKCYJNA",
                "formaP": "SPÓŁKA AKCYJNA"
            },
            "adres": {
                "ulica": "Chemików",
                "nrDomu": "7",
                "miejscowosc": "Płock",
                "kodPocztowy": "09-411"
            }
        }
    }


@pytest.fixture
def sample_normalized_company() -> NormalizedCompany:
    """Sample NormalizedCompany for testing"""
    return NormalizedCompany(
        country="SK",
        primary_id="35763469",
        legal_name="Slovenská sporiteľňa, a.s.",
        status="active",
        source_api="SK_RPO",
        fetched_at="2024-01-01T12:00:00Z"
    )


@pytest.fixture
def mock_clients():
    """Mock V4 clients for testing"""
    sk_client = AsyncMock(spec=SKRPOClient)
    cz_client = AsyncMock(spec=CZARESClient)

    # Configure mock responses
    sk_client.search_by_ico.return_value = {
        "ico": "35763469",
        "name": "Test Company SK"
    }
    sk_client.search_by_name.return_value = {
        "results": [{"ico": "35763469", "name": "Test Company SK"}]
    }

    cz_client.search_by_ico.return_value = {
        "ekonomickeSubjekty": [{"ico": "27074358", "obchodniJmeno": "Test Company CZ"}]
    }
    cz_client.search_by_name.return_value = {
        "ekonomickeSubjekty": [{"ico": "27074358", "obchodniJmeno": "Test Company CZ"}]
    }

    return {
        'sk': sk_client,
        'cz': cz_client
    }


@pytest.fixture
def mock_v4_api():
    """
    Mock V4 API endpoints using respx.
    Automatically handles common endpoints for SK and CZ.
    """
    with respx.mock(assert_all_called=False) as respx_mock:
        # SK RPO Mocks
        respx_mock.get(url__regex=r"https://data.slovensko.sk/api/.*").mock(
            return_value=Response(200, json={"results": [{"ico": "35763469", "name": "MOCK COMPANY SK"}]})
        )
        # CZ ARES Mocks
        respx_mock.post("https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat").mock(
            return_value=Response(200, json={"ekonomickeSubjekty": [{"ico": "27074358", "obchodniJmeno": "MOCK COMPANY CZ"}]})
        )
        
        yield respx_mock



# Custom pytest marks
def pytest_configure(config):
    """Configure custom pytest marks"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "v4: mark test as V4 API related"
    )


# Test utilities
def assert_api_response_structure(response: Dict[str, Any], expected_fields: list):
    """Assert that API response has expected structure"""
    for field in expected_fields:
        assert field in response, f"Missing field: {field}"


def create_test_company_data(country: str, identifier: str, **kwargs) -> Dict[str, Any]:
    """Create test company data with defaults"""
    defaults = {
        'identifier': identifier,
        'country': country,
        'name': f'Test Company {country}',
        'legal_form': 's.r.o.',
        'address': 'Test Address 123',
        'risk_score': 50,
        'source': 'test'
    }
    defaults.update(kwargs)
    return defaults


# Async test utilities
async def async_assert_raises(exc_class, coro):
    """Async version of pytest.raises"""
    try:
        await coro
        pytest.fail(f"Expected {exc_class.__name__} but no exception was raised")
    except exc_class as e:
        return e
    except Exception as e:
        pytest.fail(f"Expected {exc_class.__name__} but got {type(e).__name__}: {e}")


# Database test utilities
@pytest.fixture
def db_session():
    """Database session for testing"""
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    """Setup test database"""
    # This would initialize test database if needed
    # For now, just ensure we have a clean state
    pass