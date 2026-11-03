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
    
    # At least some people should be found for Tatra banka if ORSR public register is reachable
    if comp.get("people_source") == "SK_ORSR_HTML":
        assert len(person_nodes) > 0, "Graph should contain PERSON nodes from ORSR"
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
    assert any(x in executives[0]["address"] for x in ["Masarykova 1645/23", "09.07.1990"])
    assert executives[0]["since"] == "16.06.2022"

    # Check owners
    owners = comp["owners"]
    assert len(owners) == 1
    assert owners[0]["name"] == "Róbert Papcun"
    assert "Vklad: 5 000 EUR" in owners[0]["share"]
    assert any(x in owners[0]["address"] for x in ["Masarykova 1645/23", "09.07.1990"])


@pytest.mark.asyncio
async def test_eb_eu_sro_full_orsr_enrichment():
    """Test full ORSR extract parsing for EB-EU s. r. o. (51226511)"""
    raw = "51226511"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "SK", "graph": 1})
        assert r.status_code == 200
        data = r.json()

    assert "company" in data
    comp = data["company"]
    
    # Official ORSR registration identifiers
    assert comp["legal_name"] == "EB-EU s. r. o."
    assert comp["court"] == "Okresný súd Banská Bystrica"
    assert comp["section"] == "Sro"
    assert comp["insert_number"] == "49430/S"
    assert comp["registration_date"] == "30.11.2017"
    assert "Konateľ koná v mene spoločnosti" in comp["acting_on_behalf"]
    
    # Capital structure
    assert "5 000 EUR" in comp["capital"]
    assert comp["capital_amount"] == "5 000 EUR"
    assert comp["capital_paid"] == "5 000 EUR"
    assert comp["capital_details"]["currency"] == "EUR"
    
    # Owners structure (corporate + natural person)
    owners = comp["owners"]
    assert len(owners) >= 2
    tavira = next((o for o in owners if "Tavira" in o["name"]), None)
    assert tavira is not None
    assert tavira["type"] == "COMPANY"
    assert tavira["ico"] == "52374220"
    assert "2 500 EUR" in tavira["share"]
    assert tavira["deposit"] == "2 500 EUR"
    assert tavira["paid"] == "2 500 EUR"
    
    erik = next((o for o in owners if "Erik Babčan" in o["name"]), None)
    assert erik is not None
    assert erik["type"] == "PERSON"
    assert erik["birth_date"] == "30.05.1989"
    assert "2 500 EUR" in erik["share"]
    
    # Executive & Nominee integrity
    executives = comp["executives"]
    assert len(executives) >= 1
    ex_erik = next((e for e in executives if "Erik Babčan" in e["name"]), None)
    assert ex_erik is not None
    assert ex_erik.get("potential_nominee") is not True
    assert ex_erik["birth_date"] == "30.05.1989"
    assert comp["risk_score"] == 0
    
    # Graph structure
    g = data.get("graph", {})
    node_ids = {n["id"]: n for n in g.get("nodes", [])}
    assert "COMPANY:SK:52374220" in node_ids
    assert node_ids["COMPANY:SK:52374220"]["type"] == "COMPANY"
    assert "PERSON:SK:Erik Babčan" in node_ids
    assert node_ids["PERSON:SK:Erik Babčan"]["type"] == "PERSON"

