from bs4 import BeautifulSoup
import unicodedata
import re

def normalize_text(text):
    if not text: return None
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r'\s+', ' ', text).strip()

with open("backend/tests/fixtures/orsr/sample_31322832.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
in_section = False
print("--- Scanning for EXECUTIVES section ---")

for table in soup.find_all("table"):
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells: continue
        left = normalize_text(cells[0].get_text())
        val = normalize_text(cells[1].get_text()) if len(cells) > 1 else ""

        if "Štatutárny orgán" in left:
            in_section = True
            print(f"START SECTION: {left}")
            continue
            
        if in_section:
            if "Spoločníci" in left or "Akcionár" in left or "Konanie" in left:
                print(f"END SECTION: {left}")
                in_section = False
                break
                
            print(f"ROW: L='{left}' | V='{val}'")
