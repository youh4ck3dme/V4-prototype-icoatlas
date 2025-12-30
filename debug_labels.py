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
for table in soup.find_all("table"):
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 2:
            left = normalize_text(cells[0].get_text())
            val = normalize_text(cells[1].get_text())
            print(f"L: '{left}' -> V: '{val}'")
