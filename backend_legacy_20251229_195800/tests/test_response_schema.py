from backend.services.v4_clients.models import NormalizedCompany
from datetime import date

def validate_company_schema(company: NormalizedCompany):
    """
    Manual schema check for NormalizedCompany contract.
    Ensures all Phase 17 fields are present and have correct types.
    """
    assert isinstance(company.primary_id, str), "primary_id must be str"
    assert isinstance(company.legal_name, str), "legal_name must be str"
    assert isinstance(company.country, str), "country must be str"
    assert company.country in ["SK", "CZ", "PL", "HU"], "Invalid country"
    
    # Phase 17 fields
    assert isinstance(company.executives, list), "executives must be list"
    for exec_name in company.executives:
        assert isinstance(exec_name, str), "each executive must be str"
        
    assert isinstance(company.raw_data, dict), "raw_data must be dict"
    
    # Optional fields (should be None or their type)
    if company.street: assert isinstance(company.street, str)
    if company.city: assert isinstance(company.city, str)
    if getattr(company, 'city_part', None): assert isinstance(company.city_part, str)
    
    print(f"Schema validation passed for {company.primary_id} ({company.country})")

def test_sk_schema_contract():
    # Mock data for Tatra banka
    sample_data = {
        "ico": "00686930",
        "name": "Tatra banka, a.s.",
        "legal_form": "Akciová spoločnosť",
        "status": "Aktívna",
        "executives": ["Michal Liday", "Natália Major"],
        "address": "Hodžovo námestie 3 Bratislava 1 811 06"
    }
    
    from backend.services.v4_service import V4Service
    svc = V4Service()
    norm = svc._normalize_sk(sample_data)
    
    validate_company_schema(norm)
    
    # Check address parsing specifically
    assert norm.street == "Hodžovo námestie 3"
    assert norm.city == "Bratislava"
    assert norm.city_part == "Bratislava 1"
    assert norm.postal_code == "811 06"

if __name__ == "__main__":
    try:
        test_sk_schema_contract()
        print("All contract tests passed!")
    except Exception as e:
        print(f"Contract test failed: {e}")
        exit(1)
