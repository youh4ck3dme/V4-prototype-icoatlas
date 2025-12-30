import pytest
from datetime import datetime
from services.database import CompanyCache

def test_company_cache_extended_fields(db_session):
    """Test that CompanyCache supports new Phase 17 fields"""

    # Ensure clean state
    db_session.query(CompanyCache).filter(CompanyCache.identifier == "99999999").delete()
    db_session.commit()

    # Create
    company = CompanyCache(
        identifier="99999999",
        country="SK",
        company_name="Deep Intel Corp",
        data={},
        company_data={},
        risk_score=10,
        # New fields (Phase 17):
        executives=["CEO John", "CTO Jane"],
        shareholders=["Big Corp Ltd", "Founder Joe"],
        establishment_date=datetime(2020, 1, 1),
        legal_form="s.r.o.",
        status="active",
        financials={"revenue": 100000, "currency": "EUR"},
        employees_count=50,
        website="https://example.com",
        contact_email="info@example.com",
        contact_phone="+421900000000",
        activity_codes=["62010", "62020"]
    )
    db_session.add(company)
    db_session.commit()

    # Retrieve
    retrieved = db_session.query(CompanyCache).filter_by(identifier="99999999").first()
    assert retrieved is not None
    assert retrieved.company_name == "Deep Intel Corp"
    
    # Assert New Fields
    assert retrieved.executives == ["CEO John", "CTO Jane"]
    assert retrieved.shareholders == ["Big Corp Ltd", "Founder Joe"]
    assert retrieved.establishment_date == datetime(2020, 1, 1)
    assert retrieved.legal_form == "s.r.o."
    assert retrieved.status == "active"
    assert retrieved.financials == {"revenue": 100000, "currency": "EUR"}
    assert retrieved.employees_count == 50
    assert retrieved.website == "https://example.com"
    assert retrieved.contact_email == "info@example.com"
    assert retrieved.contact_phone == "+421900000000"
    assert retrieved.activity_codes == ["62010", "62020"]

    # Verify to_dict includes new fields
    d = retrieved.to_dict()
    assert d["executives"] == ["CEO John", "CTO Jane"]
    assert d["status"] == "active"
    assert d["contact_email"] == "info@example.com"
    assert d["financials"]["revenue"] == 100000

    # Cleanup
    db_session.delete(retrieved)
    db_session.commit()
