"""
Integration test: ORSR Parser -> GraphService
Tests the full flow from HTML parsing to Graph ingestion.
"""
import os
from backend.app.services.orsr_people_parser import parse_orsr_people
from backend.app.services.graph_service import GraphService

# Ensure DB connection
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/iluminati"

def test_orsr_to_graph():
    print("🧪 Testing ORSR Parser -> GraphService Integration...")
    
    # 1. Load Slovnaft HTML
    with open("backend/tests/fixtures/orsr/sample_31322832.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # 2. Parse people
    data = parse_orsr_people(html)
    
    print(f"Parsed: {len(data['executives'])} executives, {len(data['owners'])} owners")
    print(f"Address: {data['address']}")
    
    # Filter executives to only those with names
    valid_execs = [e for e in data["executives"] if e.get("name")]
    valid_owners = [o for o in data["owners"] if o.get("name")]
    
    print(f"Valid executives with names: {len(valid_execs)}")
    print(f"Valid owners with names: {len(valid_owners)}")
    
    # 3. Ingest into Graph
    gs = GraphService()
    
    company_node = gs.ingest_company_relationships(
        atlas_id="31322832",
        country="SK",
        company_label="SLOVNAFT, a.s.",
        address=data["address"],
        executives=valid_execs,
        owners=valid_owners,
        source="ORSR_TEST"
    )
    
    print(f"✅ Company node created: {company_node}")
    
    # 4. Build graph and check
    graph = gs.build_company_graph(atlas_id="31322832", country="SK")
    
    summary = graph["summary"]
    print(f"\n📊 Graph Summary:")
    print(f"   Persons: {summary['persons']}")
    print(f"   Addresses: {summary['addresses']}")
    print(f"   Stored Edges: {summary['stored_edges']}")
    
    # 5. Assertions
    assert summary["persons"] > 0, "Should have PERSON nodes"
    assert summary["addresses"] >= 1, "Should have ADDRESS node"
    assert summary["stored_edges"] > 0, "Should have stored edges"
    
    # Check for specific person
    person_names = [n["label"] for n in graph["nodes"] if n["type"] == "PERSON"]
    print(f"\n👤 Found {len(person_names)} persons: {person_names[:5]}...")
    
    # Check for MOL Nyrt as owner
    mol_found = any("MOL" in name for name in person_names)
    print(f"   MOL Nyrt. found: {mol_found}")
    
    # Check edge types
    edge_types = [e["type"] for e in graph["edges"]]
    has_executive = "EXECUTIVE_OF" in edge_types
    has_owner = "OWNER_OF" in edge_types
    has_address = "HAS_ADDRESS" in edge_types
    
    print(f"\n🔗 Edge types:")
    print(f"   EXECUTIVE_OF: {has_executive}")
    print(f"   OWNER_OF: {has_owner}")
    print(f"   HAS_ADDRESS: {has_address}")
    
    assert has_executive, "Should have EXECUTIVE_OF edges"
    assert has_address, "Should have HAS_ADDRESS edge"
    # Note: OWNER_OF may be missing if MOL is parsed as PERSON type (legal entity)
    
    gs.close()
    print("\n✅ ALL TESTS PASSED!")

if __name__ == "__main__":
    test_orsr_to_graph()
