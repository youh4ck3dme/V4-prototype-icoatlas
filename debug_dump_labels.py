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
all_rows = []
for t in soup.find_all("table"):
    all_rows.extend(t.find_all("tr"))

print(f"Total rows collected: {len(all_rows)}")

for i, row in enumerate(all_rows):
    cells = row.find_all("td")
    if not cells: continue
    left = normalize_text(cells[0].get_text(strip=True))
    if left and ("Akcio" in left or "akcio" in left):
        print(f"ROW {i}: '{left}'")
