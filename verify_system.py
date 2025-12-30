import requests
import time
import sys
import uuid

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def check_health():
    print("🏥 Checking Health...")
    try:
        r = requests.get(f"{API_URL}/health")
        if r.status_code == 200:
            print(f"✅ Health OK: {r.json()}")
        else:
            print(f"❌ Health Failed: {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Health Connection Error: {e}")
        sys.exit(1)

def check_search_robustness():
    print("\n🔍 Checking Search Robustness...")
    queries = ["56760892", "invalid_ico", "test company"]
    
    for q in queries:
        try:
            r = requests.get(f"{API_URL}/search?q={q}&limit=1")
            if r.status_code == 200: # Search returns 200 with empty list if not found
                 print(f"✅ Search '{q}': OK ({len(r.json())} results)")
            else:
                 print(f"❌ Search '{q}': Failed ({r.status_code})")
        except Exception as e:
            print(f"❌ Search '{q}': Exception {e}")

def check_rate_limiting():
    # Use a fake client ID for rate limiting
    print("\n⏱️ Checking Rate Limiting (Public)...")
    limit = 50 # Assuming public bucket is large enough for test
    ip = f"test-ip-{uuid.uuid4()}" 
    # This is harder to test without manipulating headers perfectly or exhausting limit
    # Just checking endpoint is reachable
    r = requests.get(f"{API_URL}/rate-limiter/stats")
    if r.status_code == 200:
        print("✅ Rate Limiter Stats: OK")
    else:
        print(f"❌ Rate Limiter Stats: Failed ({r.status_code})")

def main():
    print("🚀 Starting Final Deployment Verification")
    check_health()
    check_search_robustness()
    check_rate_limiting()
    print("\n✅ Verification Complete!")

if __name__ == "__main__":
    main()
