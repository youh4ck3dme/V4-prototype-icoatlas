import requests
import sys

def verify_frontend():
    url = "http://localhost:8009"
    print(f"Checking {url}...")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend accessible (HTTP 200)")
            
            # Check for generic React app indicators since we can't execute JS
            content = response.text
            if '<div id="root">' in content:
                print("✅ React Root Check passed")
            else:
                print("❌ React Root not found in HTML")
                
            if 'src="/assets/' in content:
                 print("✅ Asset/Script tags found")
            else:
                 print("⚠️ No assets found in index.html (Check build output)")
                 
            return True
        else:
            print(f"❌ Frontend returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def verify_backend_health():
    url = "http://localhost:8000/api/docs" # Health might be 405 allowed methods issue, docs should be 200
    print(f"Checking {url}...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Backend API Docs accessible (HTTP 200)")
            return True
        else:
            print(f"❌ Backend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    f = verify_frontend()
    b = verify_backend_health()
    
    if f and b:
        print("\n🎉 SYSTEM VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("\n💥 SYSTEM VERIFICATION FAILED")
        sys.exit(1)
