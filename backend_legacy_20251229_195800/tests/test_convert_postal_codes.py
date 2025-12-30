import pytest
from scripts.convert_postal_codes import normalize_postal_code, get_kraj_name

@pytest.mark.parametrize("input_psc,expected", [
    ("12345", "12345"),
    (" 12345 ", "12345"),
    ("1234", "01234"),
    ("12 34", "01234"),  # spaces removed then padded to 5 digits
])
def test_normalize_postal_code(input_psc, expected):
    assert normalize_postal_code(input_psc) == expected

def test_get_kraj_name_known():
    assert get_kraj_name("BC") == "Banskobystrický"
    assert get_kraj_name("BL") == "Bratislavský"

def test_get_kraj_name_unknown():
    assert get_kraj_name("XX") == ""
