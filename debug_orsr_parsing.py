import httpx
import asyncio
from bs4 import BeautifulSoup

async def debug_orsr():
    ico = "35760892"
    search_url = "https://www.orsr.sk/hladaj_ico.asp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.orsr.sk/search_ico.asp",
        "Origin": "https://www.orsr.sk",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Step 1: POST Search
        data = {"ICO": ico, "SID": "0", "search": "1"}
        print(f"Searching for {ico}...")
        resp = await client.post(search_url, data=data, headers=headers)
        print(f"Search Response Status: {resp.status_code}")
        
        with open("debug_orsr_search_results.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
            
        soup = BeautifulSoup(resp.text, "lxml")
        link = soup.select_one("table a[href^='vypis.asp']")
        if not link:
            print("No vypis.asp link found in search results.")
            # Let's try to find ANY link that might be it
            link = soup.find("a", string=lambda x: x and "Aktuálny" in x)
            
        if link:
            detail_url = "https://www.orsr.sk/" + link["href"].lstrip("/")
            print(f"Following detail link: {detail_url}")
            dresp = await client.get(detail_url, headers=headers)
            print(f"Detail Response Status: {dresp.status_code}")
            
            with open("debug_orsr_real_detail.html", "w", encoding="utf-8") as f:
                f.write(dresp.text)
            
            dsoup = BeautifulSoup(dresp.text, "lxml")
            # Look for labels in ALL tables
            for i, table in enumerate(dsoup.find_all("table")):
                for cell in table.find_all("td"):
                    txt = cell.get_text(strip=True)
                    if "Obchodné meno" in txt or "Obchodn" in txt:
                        print(f"Table {i} - Label: {txt}")
                        sibling = cell.find_next_sibling("td")
                        if sibling:
                            print(f"  Value: {sibling.get_text(strip=True)}")
        else:
            print("Failed to find detail link.")

if __name__ == "__main__":
    asyncio.run(debug_orsr())
