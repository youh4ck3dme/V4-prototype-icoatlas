from bs4 import BeautifulSoup
import unicodedata
import re

with open("backend/tests/fixtures/orsr/sample_31322832.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
text = soup.get_text()

if "Akcionár" in text:
    print("FOUND Akcionár in overall text")
else:
    print("NOT FOUND Akcionár in overall text")

count = 0
for t in soup.find_all("table"):
    for row in t.find_all("tr"):
        cells = row.find_all("td")
        if not cells: continue
        left = cells[0].get_text(strip=True)
        if "Akcion" in left:
            print(f"FOUND IN ROW: '{left}'")
            count += 1

print(f"Total rows with Akcion found: {count}")
