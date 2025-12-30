
import requests
from bs4 import BeautifulSoup
import re
import sys

# Define target ICO
ICO = "36394333"

def debug_scrape(ico):
    print(f"Starting debug scrape for ICO: {ico}")
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()

    search_url = f"https://www.orsr.sk/hladaj_subjekt.asp?ICO={ico}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = session.get(search_url, headers=headers, timeout=10)
        print(f"Search Response Status: {response.status_code}")
        print(f"Response Encoding: {response.encoding}")
        
        # Manually force windows-1250 if not detected
        if response.encoding.lower() != 'windows-1250':
             print("Forcing windows-1250 encoding...")
             response.encoding = 'windows-1250'

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Dump partial HTML
        print("\n--- HTML PREVIEW (Start) ---")
        print(response.text[:1000])
        print("--- HTML PREVIEW (End) ---\n")

        # Find link logic
        print("Searching for detail link...")
        detail_link = soup.find("a", href=lambda x: x and "vypis.asp?ID=" in x)
        
        if detail_link:
            print(f"✅ Found detail link via lambda: {detail_link}")
        else:
            print("❌ Lambda search failed. Trying alternate extraction...")
            all_links = soup.find_all("a", href=True)
            found = False
            for link in all_links:
                href = link.get("href", "")
                if "vypis.asp" in href:
                    print(f"   Candidate link found: {href} | Text: {link.get_text(strip=True)}")
                    if "ID=" in href:
                        detail_link = link
                        found = True
                        break
            
            if found:
                print(f"✅ Found detail link via iteration: {detail_link}")
            else:
                print("❌ No link with 'vypis.asp' and 'ID=' found.")

        if not detail_link:
            return

        # Extract ID
        href = detail_link["href"]
        try:
            detail_id = href.split("ID=")[1].split("&")[0]
            print(f"Extracted ID: {detail_id}")
        except Exception as e:
            print(f"❌ ID Extraction failed: {e}")
            return

        detail_url = f"https://www.orsr.sk/vypis.asp?ID={detail_id}&SID=2&P=0"
        print(f"Fetching detail URL: {detail_url}")
        
        detail_response = session.get(detail_url, headers=headers, timeout=10)
        detail_response.encoding = 'windows-1250'
        
        print(f"Detail Response Status: {detail_response.status_code}")
        
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        
        # Extract Legal Form
        print("Extracting basic data...")
        form_elem = detail_soup.find("td", string=lambda x: x and "Právna forma:" in str(x))
        if form_elem:
            print(f"✅ Found form element: {form_elem.get_text(strip=True)}")
            form_row = form_elem.find_next_sibling("td")
            if form_row:
                print(f"   Value: {form_row.get_text(strip=True)}")
        else:
            print("❌ Legal form element not found")
            # Try alternate search
            tds = detail_soup.find_all("td")
            for td in tds:
                if "Právna forma:" in td.get_text():
                    print(f"   Found via text search: {td.get_text(strip=True)}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_scrape(ICO)
