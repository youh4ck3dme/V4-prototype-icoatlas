import requests
from bs4 import BeautifulSoup
import re

ico = "54430178"
search_url = f"https://www.orsr.sk/hladaj_ico.asp?ICO={ico}&SID=0"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

response = requests.get(search_url, headers=headers)
response.encoding = 'windows-1250'
soup = BeautifulSoup(response.text, "html.parser")

detail_link = soup.find("a", href=lambda x: x and "vypis.asp?ID=" in x)
if detail_link:
    href = detail_link["href"]
    detail_id = href.split("ID=")[1].split("&")[0]
    sid = href.split("SID=")[1].split("&")[0]
    detail_url = f"https://www.orsr.sk/vypis.asp?ID={detail_id}&SID={sid}&P=0"
    print(f"Detail URL: {detail_url}")
    
    depth_response = requests.get(detail_url, headers=headers)
    depth_response.encoding = 'windows-1250'
    detail_soup = BeautifulSoup(depth_response.text, "html.parser")
    
    # Debug Registration ID and Section
    print("\n--- Testing Registration ID & Section ---")
    for span in detail_soup.find_all("span", class_="tl"):
        text = span.get_text().lower()
        print(f"Found Label: {text}")
        if "oddiel:" in text:
            # Try find_next_sibling correctly
            val_span = span.find_next_sibling("span", class_="ra")
            if val_span:
                print(f"✅ Oddiel found via next_sibling: {val_span.get_text(strip=True)}")
            else:
                # Try parent lookup
                parent_td = span.parent
                all_ra = parent_td.find_all("span", class_="ra")
                if all_ra:
                    print(f"✅ Oddiel found via parent: {all_ra[0].get_text(strip=True)}")
        elif "vložka číslo:" in text or "vlozka" in text:
            val_span = span.find_next_sibling("span", class_="ra")
            if val_span:
                print(f"✅ Vlozka found via next_sibling: {val_span.get_text(strip=True)}")
            else:
                parent_td = span.parent
                all_ra = parent_td.find_all("span", class_="ra")
                if all_ra:
                    print(f"✅ Vlozka found via parent: {all_ra[-1].get_text(strip=True)}")

    # Debug Capital
    print("\n--- Testing Capital ---")
    tds = detail_soup.find_all("td")
    for td in tds:
        txt = td.get_text().lower()
        if "výška základného imania:" in txt or "vyska zakladneho imania:" in txt:
            print(f"✅ Capital label found in TD: {txt}")
            next_td = td.find_next_sibling("td")
            if next_td:
                print(f"✅ Capital value found: {next_td.get_text(strip=True)}")

