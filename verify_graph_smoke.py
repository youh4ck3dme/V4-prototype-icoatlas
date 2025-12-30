import os
import asyncio
from backend.app.services.graph_service import GraphService

# Ensure we connect to localhost DB
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/iluminati"

def smoke_test():
    print("🚬 Starting Graph Smoke Test...")
    gs = GraphService()
    
    # 1. Ingest Company A (The Anchor)
    print("Ingesting Company A...")
    node_a = gs.ingest_company_relationships(
        atlas_id="TEST001",
        country="SK",
        company_label="Test Company A s.r.o.",
        address={"street": "Einsteinova 1", "city": "Bratislava", "postal_code": "85101"},
        source="SMOKE_TEST"
    )
    print(f"Company A Node ID: {node_a}")

    # 2. Ingest Company B (Same Address)
    print("Ingesting Company B (Same Address)...")
    node_b = gs.ingest_company_relationships(
        atlas_id="TEST002",
        country="SK",
        company_label="Test Company B s.r.o.",
        address={"street": "Einsteinova 1", "city": "Bratislava", "postal_code": "85101"},
        source="SMOKE_TEST"
    )
    print(f"Company B Node ID: {node_b}")

    # 3. Build Graph for Company A
    print("Building Graph for Company A...")
    graph = gs.build_company_graph(atlas_id="TEST001", country="SK", limit_related_per_anchor=10)
    
    # 4. Verify Results
    print("\n📊 Graph Results:")
    summary = graph["summary"]
    print(f"Summary: {summary}")
    
    related = summary.get("related_companies", 0)
    derived = summary.get("derived_edges", 0)
    
    if related >= 1 and derived >= 1:
        print("\n✅ SUCCESS: Found related company via SAME_ADDRESS_AS!")
        # Validate edge type
        edges = graph["edges"]
        address_links = [e for e in edges if e["type"] == "SAME_ADDRESS_AS"]
        print(f"Found {len(address_links)} SAME_ADDRESS_AS edges.")
        for e in address_links:
             print(f"  - {e['from']} -> {e['to']} (via {e['data']})")
    else:
        print("\n❌ FAILURE: Did not find related companies.")
        print(graph)

    gs.close()

if __name__ == "__main__":
    smoke_test()
