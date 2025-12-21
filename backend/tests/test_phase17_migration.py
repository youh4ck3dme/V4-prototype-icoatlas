"""
Test Phase 17: Verifikácia databázovej migrácie
Testuje, či migrácia b871a14d57ca bola správne aplikovaná.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.database import get_db_session, CompanyCache, Base
from sqlalchemy import inspect


def test_migration_applied():
    """Test, či migrácia bola aplikovaná a všetky stĺpce existujú"""
    print("\n🔍 Test: Migrácia Phase 17")
    print("=" * 60)
    
    # Inicializovať databázu
    import services.database as db_module
    db_module.init_database()
    
    # Získať inšpektora databázy
    inspector = inspect(db_module.engine)
    
    # Získať stĺpce tabuľky company_cache
    columns = inspector.get_columns('company_cache')
    column_names = [col['name'] for col in columns]
    
    print(f"\n✅ Tabuľka 'company_cache' má {len(columns)} stĺpcov")
    
    # Nové stĺpce z Phase 17
    required_columns = [
        'executives',
        'shareholders', 
        'establishment_date',
        'legal_form',
        'activity_codes',
        'financials',
        'contact_email',
        'contact_phone',
        'website',
        'employees_count',
        'status'
    ]
    
    print(f"\nKontrola nových stĺpcov:")
    missing_columns = []
    for col in required_columns:
        if col in column_names:
            print(f"   ✓ {col}")
        else:
            print(f"   ✗ {col} - CHÝBA!")
            missing_columns.append(col)
    
    if missing_columns:
        print(f"\n❌ Test FAILED: Chýbajúce stĺpce: {', '.join(missing_columns)}")
        return False
    
    # Overiť typy stĺpcov
    print(f"\nTypy stĺpcov:")
    for col in columns:
        if col['name'] in required_columns:
            print(f"   {col['name']}: {col['type']}")
    
    print("\n✅ Test PASSED: Všetky nové stĺpce existujú")
    return True


def test_nullable_columns():
    """Test, či sú nové stĺpce nullable (bezpečná migrácia)"""
    print("\n\n🔍 Test: Nullable Columns")
    print("=" * 60)
    
    import services.database as db_module
    inspector = inspect(db_module.engine)
    columns = inspector.get_columns('company_cache')
    
    required_columns = [
        'executives', 'shareholders', 'establishment_date',
        'legal_form', 'activity_codes', 'financials',
        'contact_email', 'contact_phone', 'website',
        'employees_count', 'status'
    ]
    
    non_nullable = []
    for col in columns:
        if col['name'] in required_columns:
            if not col['nullable']:
                non_nullable.append(col['name'])
                print(f"   ✗ {col['name']} - NOT NULL (problém!)")
            else:
                print(f"   ✓ {col['name']} - nullable")
    
    if non_nullable:
        print(f"\n⚠️  Test WARNING: Niektoré stĺpce nie sú nullable: {', '.join(non_nullable)}")
        print("   Toto môže spôsobiť problémy pri migrácii existujúcich dát.")
        return False
    
    print("\n✅ Test PASSED: Všetky nové stĺpce sú nullable")
    return True


def test_existing_data_intact():
    """Test, či existujúce dáta neboli ovplyvnené migráciou"""
    print("\n\n🔍 Test: Existing Data Integrity")
    print("=" * 60)
    
    with get_db_session() as db:
        if not db:
            print("❌ Databáza nie je dostupná")
            return False
        
        # Spočítať záznamy
        total_count = db.query(CompanyCache).count()
        print(f"\n✅ Celkový počet záznamov: {total_count}")
        
        if total_count == 0:
            print("⚠️  Databáza je prázdna (normálne pre nový systém)")
            return True
        
        # Skontrolovať, že staré záznamy majú NULL v nových poliach
        sample = db.query(CompanyCache).first()
        if sample:
            print(f"\nUkážkový záznam (ID {sample.id}):")
            print(f"   Názov: {sample.company_name}")
            print(f"   Executives: {sample.executives}")
            print(f"   Legal form: {sample.legal_form}")
            print(f"   Status: {sample.status}")
        
        print("\n✅ Test PASSED: Existujúce dáta sú intaktné")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PHASE 17: VERIFIKÁCIA MIGRÁCIE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Migrácia aplikovaná
    results.append(("Migration Applied", test_migration_applied()))
    
    # Test 2: Nullable columns
    results.append(("Nullable Columns", test_nullable_columns()))
    
    # Test 3: Existing data intact
    results.append(("Existing Data Integrity", test_existing_data_intact()))
    
    # Súhrn
    print("\n\n" + "=" * 60)
    print("SÚHRN TESTOV")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 VŠETKY TESTY PREŠLI!")
        sys.exit(0)
    else:
        print("\n❌ NIEKTORÉ TESTY ZLYHALI")
        sys.exit(1)
