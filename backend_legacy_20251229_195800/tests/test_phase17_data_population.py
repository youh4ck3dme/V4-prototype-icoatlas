"""
Test Phase 17: Verifikácia populácie nových polí
Testuje, či sa nové polia (executives, shareholders, financials, atď.) správne naplňajú.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.sk_orsr_provider import get_orsr_provider
from services.database import get_db_session, CompanyCache
import json


def test_orsr_data_population():
    """Test, či ORSR provider správne naplní nové polia"""
    print("\n🔍 Test 1: ORSR Data Population")
    print("=" * 60)
    
    # Použiť reálne slovenské IČO (napr. Tatra banka)
    test_ico = "00686930"  # Tatra banka
    
    provider = get_orsr_provider()
    data = provider.lookup_by_ico(test_ico, force_refresh=True)
    
    if not data:
        print(f"❌ Nepodarilo sa získať dáta pre IČO {test_ico}")
        return False
    
    print(f"\n✅ Získané dáta pre IČO {test_ico}:")
    print(f"   Názov: {data.get('name')}")
    print(f"   Právna forma: {data.get('legal_form')}")
    print(f"   Status: {data.get('status')}")
    print(f"   Dátum vzniku: {data.get('founded')}")
    
    # Kontrola executives
    executives = data.get('executives', [])
    print(f"\n   Konatelia ({len(executives)}):")
    for exec in executives[:3]:  # Ukázať prvých 3
        print(f"     - {exec}")
    if len(executives) > 3:
        print(f"     ... a ďalších {len(executives) - 3}")
    
    # Kontrola shareholders
    shareholders = data.get('shareholders', [])
    print(f"\n   Spoločníci ({len(shareholders)}):")
    for share in shareholders[:3]:
        print(f"     - {share}")
    if len(shareholders) > 3:
        print(f"     ... a ďalších {len(shareholders) - 3}")
    
    # Kontrola finančných dát
    financials = data.get('financial_data')
    if financials:
        print(f"\n   Finančné dáta:")
        print(f"     Rok: {financials.get('year')}")
        print(f"     Výnosy: {financials.get('revenue')}")
        print(f"     Zisk: {financials.get('profit')}")
    
    # Kontrola adresných polí
    print(f"\n   Adresa:")
    print(f"     Ulica: {data.get('street')}")
    print(f"     Mesto: {data.get('city')}")
    print(f"     PSČ: {data.get('zip')}")
    print(f"     Okres: {data.get('district')}")
    print(f"     Kraj: {data.get('region')}")
    
    # Overenie, že kľúčové polia sú naplnené
    required_fields = ['name', 'legal_form', 'executives']
    missing_fields = [f for f in required_fields if not data.get(f)]
    
    if missing_fields:
        print(f"\n⚠️  Chýbajúce polia: {', '.join(missing_fields)}")
        return False
    
    print("\n✅ Test 1 PASSED: Všetky kľúčové polia sú naplnené")
    return True


def test_database_storage():
    """Test, či sa dáta správne ukladajú do DB"""
    print("\n\n🔍 Test 2: Database Storage")
    print("=" * 60)
    
    test_ico = "00686930"
    
    with get_db_session() as db:
        if not db:
            print("❌ Databáza nie je dostupná")
            return False
        
        company = db.query(CompanyCache).filter(
            CompanyCache.identifier == test_ico,
            CompanyCache.country == "SK"
        ).first()
        
        if not company:
            print(f"❌ Firma {test_ico} nie je v databáze")
            return False
        
        print(f"\n✅ Firma nájdená v databáze:")
        print(f"   ID: {company.id}")
        print(f"   Názov: {company.company_name}")
        print(f"   Právna forma: {company.legal_form}")
        print(f"   Status: {company.status}")
        print(f"   Dátum vzniku: {company.establishment_date}")
        
        # Kontrola JSON polí
        if company.executives:
            print(f"\n   Konatelia v DB ({len(company.executives)}):")
            for exec in company.executives[:3]:
                print(f"     - {exec}")
        
        if company.shareholders:
            print(f"\n   Spoločníci v DB ({len(company.shareholders)}):")
            for share in company.shareholders[:3]:
                print(f"     - {share}")
        
        if company.financials:
            print(f"\n   Finančné dáta v DB:")
            print(f"     {json.dumps(company.financials, indent=6, ensure_ascii=False)}")
        
        # Overenie
        if not company.executives:
            print("\n⚠️  Pole 'executives' je prázdne v DB")
            return False
        
        if not company.legal_form:
            print("\n⚠️  Pole 'legal_form' je prázdne v DB")
            return False
        
        print("\n✅ Test 2 PASSED: Dáta sú správne uložené v DB")
        return True


def test_export_fields():
    """Test, či export obsahuje nové polia"""
    print("\n\n🔍 Test 3: Export Fields")
    print("=" * 60)
    
    from services.export_service import export_to_csv
    
    # Simulované dáta
    graph_data = {
        "nodes": [
            {
                "id": "sk_00686930",
                "label": "Test Firma s.r.o.",
                "type": "company",
                "country": "SK",
                "risk_score": 2,
                "executives": ["Ján Novák", "Peter Horák"],
                "shareholders": ["Investor A", "Investor B"],
                "legal_form": "Spoločnosť s ručením obmedzeným",
                "status": "Aktívna",
                "founded": "2020-01-15",
                "street": "Hlavná 123",
                "city": "Bratislava",
                "zip": "81101",
            }
        ],
        "edges": []
    }
    
    csv_content = export_to_csv(graph_data)
    
    # Kontrola, či CSV obsahuje nové stĺpce
    required_columns = ["Konatelia", "Spoločníci", "Právna forma", "Stav"]
    header_line = csv_content.split('\n')[0]
    
    missing_columns = [col for col in required_columns if col not in header_line]
    
    if missing_columns:
        print(f"❌ Chýbajúce stĺpce v CSV: {', '.join(missing_columns)}")
        print(f"\nCSV Header:\n{header_line}")
        return False
    
    print(f"✅ CSV obsahuje všetky nové stĺpce:")
    for col in required_columns:
        print(f"   ✓ {col}")
    
    # Ukázať prvé riadky CSV
    print(f"\nPrvé 3 riadky CSV:")
    for i, line in enumerate(csv_content.split('\n')[:3]):
        print(f"   {line[:100]}...")
    
    print("\n✅ Test 3 PASSED: Export obsahuje nové polia")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PHASE 17: VERIFIKÁCIA POPULÁCIE NOVÝCH POLÍ")
    print("=" * 60)
    
    results = []
    
    # Test 1: ORSR Data Population
    results.append(("ORSR Data Population", test_orsr_data_population()))
    
    # Test 2: Database Storage
    results.append(("Database Storage", test_database_storage()))
    
    # Test 3: Export Fields
    results.append(("Export Fields", test_export_fields()))
    
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
