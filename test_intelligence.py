import sys
import os
from pprint import pprint

# Pridať backend do path
sys.path.append(os.path.abspath("backend"))

from services.intelligence_service import generate_nexus_story, get_nexus_metadata

def test_nexus_briefing():
    print("🧪 Testujem Nexus Briefing...")
    
    nodes = [
        {"id": "sk_123", "label": "BAMAT Service, s. r. o.", "type": "company", "country": "SK", "city": "Čadca", "risk_score": 2},
        {"id": "cz_456", "label": "BAMAT holdings a.s.", "type": "company", "country": "CZ", "city": "Praha", "risk_score": 5},
        {"id": "pers_1", "label": "Jozef Bamatovič", "type": "person", "country": "SK"}
    ]
    
    edges = [
        {"source": "cz_456", "target": "sk_123", "type": "OWNER"},
        {"source": "pers_1", "target": "sk_123", "type": "MANAGED_BY"}
    ]
    
    story = generate_nexus_story(nodes, edges, "sk_123")
    metadata = get_nexus_metadata(nodes, edges)
    
    print("\nVygenerovaný príbeh:")
    print(story)
    
    print("\nMetadáta:")
    pprint(metadata)
    
    # Assertions
    assert "BAMAT Service" in story
    assert "Nexus" in story
    assert "Česko" in story
    assert metadata["is_cross_border"] is True
    assert "CZ" in metadata["involved_countries"]
    
    print("\n✅ Test prebehol úspešne!")

if __name__ == "__main__":
    test_nexus_briefing()
