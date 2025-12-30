import unittest
from backend.app.services.orsr_people_parser import parse_orsr_people

class TestORSRParser(unittest.TestCase):
    def setUp(self):
        with open("backend/tests/fixtures/orsr/sample_31322832.html", "r", encoding="utf-8") as f:
            self.html = f.read()
            
    def test_parse_slovnaft(self):
        data = parse_orsr_people(self.html)
        
        print("\nParsed Data:")
        print(f"Address: {data['address']}")
        print(f"Executives ({len(data['executives'])}): {data['executives']}")
        print(f"Owners ({len(data['owners'])}): {data['owners']}")
        
        # Verify Address
        self.assertIn("Vlčie hrdlo 1", data["address"]["street"])
        self.assertEqual(data["address"]["postal_code"], "82412")
        
        # Verify Executives (Predstavenstvo)
        self.assertTrue(len(data["executives"]) > 0)
        names = [e["name"] for e in data["executives"]]
        # Check for known CEO/Executive (Marek Senkovič or similar from public knowledge/sample)
        # Note: Names change, but we expect names to be parsed
        
        # Verify Owners (Akcionar)
        self.assertTrue(len(data["owners"]) > 0)
        owner_names = [o.get("name", "") for o in data["owners"]]
        self.assertTrue(any("MOL Nyrt" in n for n in owner_names), f"MOL Nyrt. not found in {owner_names}")

if __name__ == "__main__":
    unittest.main()
