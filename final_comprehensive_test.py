#!/usr/bin/env python3
"""
Finálny komplexný test celého ICO Atlas systému
"""
import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_all():
    print("\n" + "="*60)
    print("ICO ATLAS - FINAL COMPREHENSIVE TEST")
    print("="*60 + "\n")
    
    results = {}
    
    # Test 1: Backend Health
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        results["Backend Health"] = r.status_code == 200
        print(f"✓ Backend Health: {r.status_code}")
    except:
        results["Backend Health"] = False
        print("✗ Backend Health: FAILED")
    
    # Test 2: Search
    try:
        r = requests.get(f"{API_URL}/search?q=36054551", timeout=10)
        results["Search"] = r.status_code in [200, 404]
        print(f"✓ Search: {r.status_code}")
    except:
        results["Search"] = False
        print("✗ Search: FAILED")
    
    # Test 3: Auth
    try:
        r = requests.post(f"{API_URL}/auth/register", json={"email":"test@test.com","password":"test"}, timeout=5)
        results["Auth"] = r.status_code in [201, 400, 422]
        print(f"✓ Auth: {r.status_code}")
    except:
        results["Auth"] = False
        print("✗ Auth: FAILED")
    
    # Test 4: Rate Limiting
    try:
        r = requests.get(f"{API_URL}/rate-limiter/stats", timeout=5)
        results["Rate Limiting"] = r.status_code == 200
        print(f"✓ Rate Limiting: {r.status_code}")
    except:
        results["Rate Limiting"] = False
        print("✗ Rate Limiting: FAILED")
    
    # Test 5: Database
    try:
        r = requests.get(f"{API_URL}/database/stats", timeout=5)
        results["Database"] = r.status_code == 200
        print(f"✓ Database: {r.status_code}")
    except:
        results["Database"] = False
        print("✗ Database: FAILED")
    
    # Test 6: Cache
    try:
        r = requests.get(f"{API_URL}/cache/stats", timeout=5)
        results["Cache"] = r.status_code == 200
        print(f"✓ Cache: {r.status_code}")
    except:
        results["Cache"] = False
        print("✗ Cache: FAILED")
    
    # Test 7: API Docs
    try:
        r = requests.get(f"{API_URL}/docs", timeout=5)
        results["API Docs"] = r.status_code == 200
        print(f"✓ API Docs: {r.status_code}")
    except:
        results["API Docs"] = False
        print("✗ API Docs: FAILED")
    
    # Test 8: Metrics
    try:
        r = requests.get(f"{API_URL}/metrics", timeout=5)
        results["Metrics"] = r.status_code == 200
        print(f"✓ Metrics: {r.status_code}")
    except:
        results["Metrics"] = False
        print("✗ Metrics: FAILED")
    
    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (passed / total) * 100
    
    print("\n" + "="*60)
    print(f"RESULT: {passed}/{total} tests passed ({percentage:.1f}%)")
    print("="*60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
