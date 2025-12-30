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
    
    data = {
        "name": None,
        "address": None,
        "executives": [],
        "registration_id": None,
        "registration_section": None,
        "capital": None
    }
    
    tds = detail_soup.find_all("td")
    
    # Name
    name_elem = None
    for td in tds:
        txt = td.get_text().lower()
        if "obchodné meno:" in txt or "obchodne meno:" in txt:
            name_elem = td
            break
    if name_elem:
        name_row = name_elem.find_next_sibling("td")
        if name_row:
            data["name"] = name_row.get_text(separator=" ", strip=True).split("(od:")[0].strip()
            print(f"Name: {data['name']}")

    # Address
    address_elem = None
    for td in tds:
        txt = td.get_text().lower()
        if "sídlo:" in txt or "sidlo:" in txt:
            address_elem = td
            break
    if address_elem:
        address_row = address_elem.find_next_sibling("td")
        if address_row:
            data["address"] = address_row.get_text(separator=" ", strip=True).split("(od:")[0].strip()
            print(f"Address: {data['address']}")

    # Registration
    for span in detail_soup.find_all("span", class_="tl"):
        text = span.get_text().lower()
        if "oddiel:" in text:
            val_span = span.find_next("span", class_="ra")
            if val_span:
                data["registration_section"] = val_span.get_text(strip=True)
                print(f"Section: {data['registration_section']}")
        elif "vložka číslo:" in text or "vlozka" in text:
            val_span = span.find_next("span", class_="ra")
            if val_span:
                data["registration_id"] = val_span.get_text(" ", strip=True)
                print(f"Reg ID: {data['registration_id']}")

    # Capital
    capital_elem = None
    for td in tds:
        txt = td.get_text().lower()
        if "výška základného imania:" in txt or "vyska zakladneho imania:" in txt:
            capital_elem = td
            break
    if capital_elem:
        capital_row = capital_elem.find_next_sibling("td")
        if capital_row:
            data["capital"] = capital_row.get_text(separator=" ", strip=True).split("(od:")[0].strip()
            print(f"Capital: {data['capital']}")

else:
    print("No detail link found")
