import os
import pytest
import httpx
from backend.app.main import app

@pytest.mark.asyncio
async def test_person_graph_end_to_end():
    # Use Tatra banka IČO as per task.md suggestion
    raw = "00686930"

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "SK", "graph": 1})
        assert r.status_code == 200
        data = r.json()

    assert "company" in data
    assert "graph" in data

    # enrichment check
    comp = data["company"]
    assert "executives" in comp
    assert "owners" in comp
    assert "orsr_vypis_url" in comp

    # graph sanity check
    g = data["graph"]
    assert "nodes" in g and "edges" in g
    
    node_types = {n.get("type") for n in g["nodes"]}
    assert "COMPANY" in node_types
    
    # Check if PERSON nodes are created
    person_nodes = [n for n in g["nodes"] if n["type"] == "PERSON"]
    print(f"\nFound {len(person_nodes)} person nodes in graph.")
    
    # At least some people should be found for Tatra banka
    assert len(person_nodes) > 0, "Graph should contain PERSON nodes from ORSR"
    
    # Check for edges
    edge_types = {e.get("type") for e in g["edges"]}
    assert "EXECUTIVE_OF" in edge_types or "OWNER_OF" in edge_types, "Graph should have person-to-company edges"

@pytest.mark.asyncio
async def test_papi_hair_design_enrichment():
    raw = "54684994" # Papi Hair Design
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "SK", "graph": 1})
        assert r.status_code == 200
        data = r.json()

    assert "company" in data
    comp = data["company"]
    
    # Check enriched fields
    assert comp["legal_name"] == "Papi Hair Design, s. r. o."
    assert comp["capital"] == "5 000 EUR Rozsah splatenia: 5 000 EUR"
    
    # Check activities
    assert len(comp["activities"]) == 13
    assert "Pánske, dámske a detské kaderníctvo" in comp["activities"]
    
    # Check executives
    executives = comp["executives"]
    assert len(executives) == 1
    assert executives[0]["name"] == "Róbert Papcun"
    assert executives[0]["role"] == "konateľ"
    assert "Masarykova 1645/23" in executives[0]["address"]
    assert executives[0]["since"] == "16.06.2022"

    # Check owners
    owners = comp["owners"]
    assert len(owners) == 1
    assert owners[0]["name"] == "Róbert Papcun"
    assert "Vklad: 5 000 EUR" in owners[0]["share"]
    assert "Masarykova 1645/23" in owners[0]["address"]

