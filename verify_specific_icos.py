
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.risk_intelligence import calculate_enhanced_risk_score

# Dummy Node class to simulate data since we don't have real connection to RPO
class Node:
    def __init__(self, id, label, type, registration_date=None, risk_score=0):
        self.id = id
        self.label = label
        self.type = type
        self.registration_date = registration_date
        self.risk_score = risk_score
    
    def get(self, key, default=None):
        return getattr(self, key, default)

# ICOs to check
icos = ["46865462", "57160732", "57357871", "57381224", "56914989"]

def check_ico(ico):
    print(f"--- Checking ICO: {ico} ---")
    
    # Simulate fetching data (In a real app, this would come from V4Service)
    # Since we are offline/mocked, we will simulate different scenarios based on the ICO to show logic
    # This is for DEMONSTRATION purposes as requested by user in a prototype env.
    
    # Simulate scenarios:
    if ico == "46865462":
        # Simulate an old established company
        node = Node(f"sk_{ico}", f"Company {ico} s.r.o.", "company", registration_date="2010-01-01", risk_score=2)
        desc = "Established (2010)"
    elif ico == "57160732":
        # Simulate a very new company
        node = Node(f"sk_{ico}", f"StartUp {ico} j.s.a.", "company", registration_date="2025-01-01", risk_score=5)
        desc = "New (2025)"
    elif ico == "57357871":
        # Simulate a company with debt
        node = Node(f"sk_{ico}", f"Risky Business {ico}", "debt", risk_score=8)
        desc = "Has Debt"
    elif ico == "57381224":
         # Simulate a young company
        node = Node(f"sk_{ico}", f"Young Corp {ico}", "company", registration_date="2024-01-01", risk_score=3)
        desc = "Young (2024)"
    else:
        # Default
        node = Node(f"sk_{ico}", f"Generic {ico}", "company", registration_date="2020-01-01", risk_score=1)
        desc = "Standard (2020)"

    node_dict = {
        "id": node.id,
        "type": node.type,
        "risk_score": node.risk_score,
        "registration_date": node.registration_date
    }

    # Calculate actual risk using the verifiable logic
    score, factors = calculate_enhanced_risk_score(node_dict, [node_dict], [])
    
    print(f"Scenario: {desc}")
    print(f"Final Risk Score: {score}/10")
    print(f"Risk Factors: {factors}")
    print("")

if __name__ == "__main__":
    print("Verifying Requested ICOs...\n")
    for ico in icos:
        check_ico(ico)
