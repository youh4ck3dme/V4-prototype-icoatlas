from typing import Dict, Any, List
from services.v4_clients import NormalizedCompany

def create_mock_v4_response(country: str, identifier: str, name: str) -> Dict[str, Any]:
    """Generuje mock API response based on country"""
    if country == "SK":
        return {
            "id": 12345,
            "ico": identifier,
            "name": name,
            "legal_form": "s.r.o.",
            "address": {"street": "Test 1", "city": "Bratislava", "postal_code": "81101"},
            "status": "active",
            "registration_date": "2020-01-01"
        }
    elif country == "CZ":
        return {
            "ekonomickeSubjekty": [{
                "ico": identifier,
                "obchodniJmeno": name,
                "sidlo": {"textovaAdresa": "Test 1, Praha"},
                "pravniForma": "s.r.o.",
                "datumVzniku": "2020-01-01"
            }]
        }
    return {}

def create_normalized_company_from_mock(country: str, identifier: str, name: str) -> NormalizedCompany:
    """Helper to create normalized company object"""
    return NormalizedCompany(
        country=country,
        primary_id=identifier,
        legal_name=name,
        status="active",
        source_api="test_utils",
        fetched_at="2024-01-01T00:00:00Z"
    )

def generate_test_identifiers(country: str, count: int = 5) -> List[str]:
    """Generates valid-looking test identifiers for a given country"""
    if country == "SK":
        return [f"35{i:06d}" for i in range(count)]
    elif country == "CZ":
        return [f"27{i:06d}" for i in range(count)]
    return [f"00{i:06d}" for i in range(count)]

def validate_company_search_result(result: Dict[str, Any], expected_fields: List[str] = None):
    """Validates structure of a search result"""
    if expected_fields is None:
        expected_fields = ["identifier", "country", "name", "source"]
    
    for field in expected_fields:
        assert field in result, f"Field {field} missing in result"