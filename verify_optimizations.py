import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from backend.services.risk_intelligence import calculate_company_age, calculate_enhanced_risk_score

def test_db_pooling_config():
    print("🧪 Testing DB Pooling Configuration...")
    from backend.services.database import engine
    
    if not engine:
        print("❌ Database engine not initialized. Run backend/services/database.py first or ensure init_database is called.")
        # Try to init specifically
        from backend.services.database import init_database, DATABASE_URL
        init_database()
        from backend.services.database import engine
        
    pool = engine.pool
    print(f"   Pool class: {type(pool)}")
    
    if isinstance(pool, QueuePool):
        print(f"   ✅ Pool type is QueuePool")
        print(f"   Pool size: {pool.size()} (Expected: 20)")
        print(f"   Max overflow: {pool._max_overflow} (Expected: 40)")
        
        if pool.size() == 20 and pool._max_overflow == 40:
             print("   ✅ Pool parameters match configuration")
        else:
             print("   ❌ Pool parameters mismatch!")
    else:
        print(f"   ❌ Pool type mismatch! Expected QueuePool, got {type(pool)}")

def test_risk_scoring_age():
    print("\n🧪 Testing Smart Risk Scoring (Company Age)...")
    
    # Test case 1: New company (0.5 years old)
    today = datetime.now()
    # Approx 6 months ago
    reg_date_new = datetime.fromtimestamp(today.timestamp() - (180 * 24 * 3600)).strftime("%Y-%m-%d")
    
    node_new = {
        "id": "1",
        "type": "company",
        "registration_date": reg_date_new,
        "risk_score": 5
    }
    
    age = calculate_company_age(node_new)
    print(f"   New company age: {age:.2f} years")
    
    # Calculate score (should add +2 for < 1 year)
    score_new, factors_new = calculate_enhanced_risk_score(node_new, [node_new], [])
    print(f"   Base score: 5, Calculated score: {score_new}, Factors: {factors_new}")
    
    if score_new == 7:
        print("   ✅ New company risk penalty applied correctly (+2)")
    else:
        print(f"   ❌ New company risk penalty failed. Got {score_new}, expected 7")

    # Test case 2: Old company (15 years old)
    reg_date_old = datetime.fromtimestamp(today.timestamp() - (15 * 365.25 * 24 * 3600)).strftime("%Y-%m-%d")
    
    node_old = {
        "id": "2",
        "type": "company",
        "registration_date": reg_date_old,
        "risk_score": 5
    }
    
    age_old = calculate_company_age(node_old)
    print(f"   Old company age: {age_old:.2f} years")
    
    # Calculate score (should subtract -1 for > 10 years)
    score_old, factors_old = calculate_enhanced_risk_score(node_old, [node_old], [])
    print(f"   Base score: 5, Calculated score: {score_old}, Factors: {factors_old}")
    
    if score_old == 4:
        print("   ✅ Old company stability bonus applied correctly (-1)")
    else:
        print(f"   ❌ Old company stability bonus failed. Got {score_old}, expected 4")

if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.getcwd())
    
    try:
        test_db_pooling_config()
        test_risk_scoring_age()
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
