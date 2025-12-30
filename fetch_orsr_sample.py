import httpx
import asyncio
import sys
from bs4 import BeautifulSoup
import urllib.parse

async def fetch_sample(ico):
    # ORSR vyzaduje cp1250 encoding pre query parametre aj POST data
    search_url = "https://www.orsr.sk/hladaj_ico.asp"
    
    # Skusime GET s cp1250 encoded parametrami
    # Ale pozor, requests/httpx robia url encoding automaticky v utf-8
    # Musime recne encodovat
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.orsr.sk/search_ico.asp",
        "Origin": "https://www.orsr.sk",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # POKUS 1: POST s CP1250 body
        print(f"Searching for {ico} (POST)...")
        # Rucne vytvorime body string
        body = f"ICO={ico}&SID=0&search=1"
        # encode do cp1250 bytes
        content = body.encode('cp1250')
        
        resp = await client.post(search_url, content=content, headers=headers)
        
        # Robust encoding detection
        try:
             text = resp.content.decode('cp1250')
        except:
             text = resp.content.decode('utf-8', errors='replace')

        soup = BeautifulSoup(text, "lxml")
        
        # Debug: Save search result
        with open("debug_orsr_search_post.html", "w", encoding="utf-8") as f:
            f.write(text)

        link = soup.select_one("table a[href^='vypis.asp']")
        if not link:
            link = soup.find("a", href=lambda x: x and "vypis.asp" in x)
            
        if link:
            # Oprava relativneho linku
            # Link je casto './vypis.asp?ID=...' alebo 'vypis.asp?ID=...'
            href = link["href"]
            if href.startswith("./"):
                href = href[2:]
            elif href.startswith("/"):
                href = href[1:]
                
            detail_url = "https://www.orsr.sk/" + href
            print(f"Fetching detail: {detail_url}")
            dresp = await client.get(detail_url, headers=headers)
            
            try:
                d_text = dresp.content.decode('cp1250')
            except:
                d_text = dresp.content.decode('utf-8', errors='replace')
            
            filename = f"backend/tests/fixtures/orsr/sample_{ico}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(d_text)
            print(f"Saved to {filename}")
            return

        print("POST failed, trying GET fallback...")
        
        # POKUS 2: GET s CP1250 params
        # ICO je cislo, takze encoding je safe, ale pre istotu
        resp = await client.get(f"https://www.orsr.sk/hladaj_ico.asp?ICO={ico}&SID=0&search=1", headers=headers)
        try:
             text = resp.content.decode('cp1250')
        except:
             text = resp.content.decode('utf-8', errors='replace')
             
        soup = BeautifulSoup(text, "lxml")
        link = soup.select_one("table a[href^='vypis.asp']")
        if not link:
            link = soup.find("a", href=lambda x: x and "vypis.asp" in x)
        
        if link:
            href = link["href"]
            if href.startswith("./"):
                href = href[2:]
            elif href.startswith("/"):
                href = href[1:]
            detail_url = "https://www.orsr.sk/" + href
            print(f"Fetching detail (GET): {detail_url}")
            dresp = await client.get(detail_url, headers=headers)
            try:
                d_text = dresp.content.decode('cp1250')
            except:
                d_text = dresp.content.decode('utf-8', errors='replace')
            
            filename = f"backend/tests/fixtures/orsr/sample_{ico}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(d_text)
            print(f"Saved to {filename}")
        else:
            print("Link not found in both POST and GET.")

if __name__ == "__main__":
    import os
    os.makedirs("backend/tests/fixtures/orsr", exist_ok=True)
    ico = sys.argv[1] if len(sys.argv) > 1 else "31322832"
    asyncio.run(fetch_sample(ico))
