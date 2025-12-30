import pytest
from services.sk_region_resolver import resolve_region, enrich_address_with_region

def test_resolve_region_known():
    result = resolve_region('81101')
    assert result is not None
    assert result['kraj'] == 'Bratislavský'
    assert result['okres'] == 'Bratislava I'

def test_resolve_region_unknown():
    result = resolve_region('99999')
    assert result is None

def test_enrich_address_with_region():
    address = "Some Street 123, Bratislava, 81101"
    enriched = enrich_address_with_region(address)
    assert enriched['region'] == 'Bratislavský'
    assert enriched['district'] == 'Bratislava I'
    assert enriched['postal_code'] == '81101'
