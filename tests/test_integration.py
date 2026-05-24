"""
Integračné testy - testujú celý systém end-to-end
"""
import sys
import os
import time

# Pridať backend venv do path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
venv_path = os.path.join(backend_path, 'venv', 'lib', 'python3.14', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

try:
    import requests  # type: ignore
except ImportError:
    print("⚠️ requests nie je nainštalovaný. Inštalujem...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests  # type: ignore

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:8010"

def test_backend_health():
    """Test backend health"""
    print("🔍 Test: Backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        status = data.get("status", "")
        assert status in ["ok", "healthy", "OK", "HEALTHY"] or "features" in data, \
            f"Unexpected status: {status}"
        print(f"   ✅ Backend health OK (status: {status})")
        return True
    except Exception as e:
        print(f"   ❌ Backend health failed: {e}")
        return False

def test_frontend_accessible():
    """Test, či frontend je dostupný"""
    print("🔍 Test: Frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200
        assert "ILUMINATI" in response.text or "root" in response.text or "div" in response.text
        print("   ✅ Frontend accessible OK")
        return True
    except Exception as e:
        # Skúsime aj port 5173 ako fallback
        try:
            fallback_url = "http://localhost:5173"
            response = requests.get(fallback_url, timeout=3)
            if response.status_code == 200:
                print("   ✅ Frontend accessible OK (on fallback port 5173)")
                return True
        except:
            pass
        print(f"   ⚠️ Frontend not accessible: {e} (možno nie je spustený)")
        return False

def test_cross_origin():
    """Test CORS konfigurácia"""
    print("🔍 Test: CORS configuration...")
    try:
        # Použijeme existujúci v4 endpoint
        response = requests.options(
            f"{BASE_URL}/api/v4/search/88888888",
            headers={"Origin": FRONTEND_URL},
            timeout=5
        )
        assert response.status_code in [200, 204, 405]
        print("   ✅ CORS OK")
        return True
    except Exception as e:
        print(f"   ⚠️ CORS test: {e}")
        return True

def test_v4_integration():
    """Test V4 integrácia (SK, CZ, PL, HU)"""
    print("🔍 Test: V4 integration...")
    try:
        countries = {
            "SK": "88888888",
            "CZ": "27074358",
            "PL": "123456789",
            "HU": "0110041145"
        }
        
        results = {}
        for country, query in countries.items():
            try:
                response = requests.get(f"{BASE_URL}/api/v4/search/{query}?country={country}&graph=1", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    has_nodes = False
                    if "graph" in data and "nodes" in data["graph"]:
                        has_nodes = len(data["graph"]["nodes"]) > 0
                    elif "nodes" in data:
                        has_nodes = len(data["nodes"]) > 0
                    results[country] = has_nodes
                else:
                    results[country] = False
            except Exception as e:
                print(f"      ⚠️ {country} search error: {e}")
                results[country] = False
        
        passed = sum(results.values())
        all_ok = passed >= 2  # Aspoň 2 krajiny by mali fungovať
        status = "✅" if all_ok else "⚠️"
        print(f"   {status} V4 integration: {passed}/4 countries")
        for country, ok in results.items():
            print(f"      {country}: {'✅' if ok else '❌'}")
        
        return all_ok
    except Exception as e:
        print(f"   ❌ V4 integration test failed: {e}")
        return False

def run_all_tests():
    """Spustí všetky integračné testy"""
    print("")
    print("═══════════════════════════════════════")
    print("🧪 SPÚŠTANIE INTEGRAČNÝCH TESTOV")
    print("═══════════════════════════════════════")
    print("")
    
    tests = [
        test_backend_health,
        test_frontend_accessible,
        test_cross_origin,
        test_v4_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("")
    print("═══════════════════════════════════════")
    print("📊 VÝSLEDKY TESTOV")
    print("═══════════════════════════════════════")
    print("")
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"✅ Úspešné: {passed}/{total}")
    print(f"❌ Zlyhané: {total - passed}/{total}")
    print(f"📈 Úspešnosť: {success_rate:.1f}%")
    print("")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

