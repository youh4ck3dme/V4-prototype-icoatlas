import pytest
import httpx
from backend.app.main import app
from backend.app.api.endpoints.search_v4 import _build_in_memory_company_graph

def test_build_in_memory_company_graph_structure():
    """Unit test for the in-memory graph builder fallback"""
    company = {
        "atlas_id": "test_123",
        "ico": "12345678",
        "country": "SK",
        "legal_name": "Test Company s.r.o.",
        "street": "Priemyselná 1",
        "city": "Bratislava",
        "postal_code": "82109",
        "dic": "2020202020",
    }
    executives = [
        {"name": "Ján Novák", "role": "konateľ", "since": "01.01.2020"}
    ]
    owners = [
        {"name": "Peter Kováč", "share": "5000 EUR"}
    ]
    ubos = [
        {"name": "Jozef Skutočný"}
    ]

    graph = _build_in_memory_company_graph(company, executives, owners, ubos)

    assert "nodes" in graph and "edges" in graph
    assert graph.get("fallback") is True

    node_types = {n["type"] for n in graph["nodes"]}
    assert "COMPANY" in node_types
    assert "ADDRESS" in node_types
    assert "PERSON" in node_types
    assert "UBO" in node_types

    edge_types = {e["type"] for e in graph["edges"]}
    assert "HAS_ADDRESS" in edge_types
    assert "EXECUTIVE_OF" in edge_types
    assert "OWNER_OF" in edge_types
    assert "SKUTOČNÝ_MAJITEĽ" in edge_types


@pytest.mark.asyncio
async def test_search_v4_graph_offline_resilience():
    """Integration test: /api/v4/search with graph=1 returns resilient graph structure"""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/v4/search/88888888", params={"country": "SK", "graph": 1})
        assert r.status_code == 200
        data = r.json()

    assert "graph" in data
    g = data["graph"]
    assert "nodes" in g and "edges" in g
    assert len(g["nodes"]) > 0
    assert len(g["edges"]) > 0
