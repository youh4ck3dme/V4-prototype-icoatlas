from backend.app.services.orsr_fetch import fetch_vypis_html, resolve_vypis_url

ico = "00686930"
print(f"Resolving URL for {ico}...")
url = resolve_vypis_url(ico)
print(f"URL: {url}")

if url:
    print(f"Fetching HTML...")
    res = fetch_vypis_html(ico)
    print(f"OK: {res.ok}")
    if not res.ok:
        print(f"Reason: {res.reason}")
    else:
        print(f"HTML length: {len(res.html)}")
        print(f"Vypis URL: {res.vypis_url}")
else:
    print("URL not resolved.")
