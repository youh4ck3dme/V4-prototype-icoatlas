"""
Intelligence Service pre ILUMINATI SYSTEM
Generuje inteligentné zhrnutia vzťahov a "nexus" story pre firmy.
"""

from typing import Dict, List, Optional
from collections import Counter

def generate_nexus_story(nodes: List[Dict], edges: List[Dict], main_company_id: str) -> str:
    """
    Generuje textové zhrnutie firemnej štruktúry a vzťahov.
    """
    main_node = next((n for n in nodes if n.get("id") == main_company_id), None)
    if not main_node:
        return "Nepodarilo sa vygenerovať príbeh: Hlavná firma sa nenašla."

    name = main_node.get("label", "neznáma firma")
    country = main_node.get("country", "SK")
    city = main_node.get("city", "neznáme mesto")
    
    country_map = {
        "SK": "Slovensko",
        "CZ": "Česko",
        "PL": "Poľsko",
        "HU": "Maďarsko"
    }
    
    country_full = country_map.get(country, country)
    
    story = [f"{name} je firma so sídlom v krajine {country_full} ({city})."]
    
    # Analýza vlastníkov
    owners = []
    for edge in edges:
        if edge.get("target") == main_company_id and edge.get("type") == "OWNER":
            owner_node = next((n for n in nodes if n.get("id") == edge.get("source")), None)
            if owner_node:
                owners.append(owner_node)
                
    if owners:
        owner_names = [o.get("label") for o in owners]
        if len(owner_names) == 1:
            story.append(f"Hlavným vlastníkom je {owner_names[0]}.")
        else:
            story.append(f"Vlastnícku štruktúru tvoria: {', '.join(owner_names)}.")
            
    # Hľadanie cezhraničných prvkov
    countries_involved = set(n.get("country") for n in nodes if n.get("country"))
    if len(countries_involved) > 1:
        others = [country_map.get(c, c) for c in countries_involved if c != country]
        story.append(f"Analýza odhalila cezhraničný Nexus s prepojením na {', '.join(others)}.")
    else:
        story.append("Štruktúra je lokálneho charakteru bez zjavných zahraničných prepojení v okruhu 1. úrovne.")

    # Rizikový profil
    risk_score = main_node.get("risk_score", 0)
    if risk_score >= 7:
        story.append("❗ Rizikový profil spoločnosti je vysoký na základe sieťovej analýzy.")
    elif risk_score >= 4:
        story.append("⚠ Spoločnosť vykazuje mierne zvýšené riziko.")
        
    return " ".join(story)

def get_nexus_metadata(nodes: List[Dict], edges: List[Dict]) -> Dict:
    """
    Vráti metadáta o nexuse pre potreby frontendu.
    """
    countries = [n.get("country") for n in nodes if n.get("country")]
    country_counts = Counter(countries)
    
    return {
        "is_cross_border": len(country_counts) > 1,
        "primary_country": country_counts.most_common(1)[0][0] if countries else "SK",
        "involved_countries": list(country_counts.keys()),
        "node_count": len(nodes),
        "edge_count": len(edges)
    }
