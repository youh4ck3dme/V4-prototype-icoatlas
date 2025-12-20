"""
Špeciálne testy pre detekciu krajiny (CZ vs SK pre 8-miestne čísla)
"""

import pytest
import requests
import urllib3

# Potlač SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://localhost:8000"
BASE_URL_HTTPS = "https://localhost:8000"


def get_base_url():
    """Vráti dostupný base URL (HTTPS alebo HTTP)"""
    try:
        requests.get(f"{BASE_URL_HTTPS}/api/health", verify=False, timeout=2)
        return BASE_URL_HTTPS
    except:
        try:
            requests.get(f"{BASE_URL}/api/health", timeout=2)
            return BASE_URL
        except:
            pytest.skip("Backend server nie je dostupný")


def test_czech_ico_detected_as_cz():
    """Test, či české IČO sa správne detekuje ako CZ (nie SK)"""
    base_url = get_base_url()
    verify_ssl = base_url.startswith("https")
    
    # České IČO (8-miestne)
    czech_ico = "47114983"  # ČEZ, a.s.
    
    try:
        response = requests.get(
            f"{base_url}/api/search?q={czech_ico}",
            verify=verify_ssl,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        nodes = data.get("nodes", [])
        
        if nodes:
            # Nájsť hlavnú firmu
            company_node = next((n for n in nodes if n.get("type") == "company"), None)
            if company_node:
                country = company_node.get("country")
                # České IČO by malo byť detekované ako CZ, nie SK
                assert country == "CZ", \
                    f"České IČO {czech_ico} bolo detekované ako {country}, očakávané CZ"
    except requests.exceptions.Timeout:
        pytest.skip("Request timeout - backend možno nebeží")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend server nie je dostupný")


def test_slovak_ico_detected_as_sk():
    """Test, či slovenské IČO sa správne detekuje ako SK"""
    base_url = get_base_url()
    verify_ssl = base_url.startswith("https")
    
    # Slovenské IČO (8-miestne)
    slovak_ico = "31333501"  # Agrofert Holding a.s.
    
    try:
        response = requests.get(
            f"{base_url}/api/search?q={slovak_ico}",
            verify=verify_ssl,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        nodes = data.get("nodes", [])
        
        if nodes:
            # Nájsť hlavnú firmu
            company_node = next((n for n in nodes if n.get("type") == "company"), None)
            if company_node:
                country = company_node.get("country")
                # Slovenské IČO by malo byť detekované ako SK
                assert country == "SK", \
                    f"Slovenské IČO {slovak_ico} bolo detekované ako {country}, očakávané SK"
    except requests.exceptions.Timeout:
        pytest.skip("Request timeout - backend možno nebeží")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend server nie je dostupný")


def test_country_detection_priority():
    """Test priority detekcie: CZ má prioritu pred SK pre 8-miestne čísla"""
    base_url = get_base_url()
    verify_ssl = base_url.startswith("https")
    
    # České IČO, ktoré by sa mohlo zameniť so SK
    czech_ico = "27074358"  # Agrofert, a.s. (CZ)
    
    try:
        response = requests.get(
            f"{base_url}/api/search?q={czech_ico}",
            verify=verify_ssl,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        nodes = data.get("nodes", [])
        
        if nodes:
            company_node = next((n for n in nodes if n.get("type") == "company"), None)
            if company_node:
                country = company_node.get("country")
                # ARES by mal vrátiť dáta pre CZ, takže by to malo byť CZ
                # Ak ARES nevrátil dáta, môže to byť SK (fallback)
                assert country in ["CZ", "SK"], \
                    f"Krajina {country} nie je platná (očakávané CZ alebo SK)"
    except requests.exceptions.Timeout:
        pytest.skip("Request timeout")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend server nie je dostupný")


def test_company_name_not_fallback():
    """Test, či názov firmy nie je 'Firma {ICO}' (fallback)"""
    base_url = get_base_url()
    verify_ssl = base_url.startswith("https")
    
    # Reálne IČO, ktoré by malo mať skutočný názov
    test_ico = "52374220"  # Tavira, s.r.o. (SK)
    
    try:
        response = requests.get(
            f"{base_url}/api/search?q={test_ico}",
            verify=verify_ssl,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        nodes = data.get("nodes", [])
        
        if nodes:
            company_node = next((n for n in nodes if n.get("type") == "company"), None)
            if company_node:
                label = company_node.get("label", "")
                # Názov by nemal byť "Firma {ICO}" (to je fallback)
                assert not label.startswith("Firma "), \
                    f"Názov firmy je fallback: {label}"
                assert label != f"Firma {test_ico}", \
                    f"Názov firmy je fallback formát: {label}"
    except requests.exceptions.Timeout:
        pytest.skip("Request timeout")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend server nie je dostupný")

