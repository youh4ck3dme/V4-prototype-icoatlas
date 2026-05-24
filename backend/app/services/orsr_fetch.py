from __future__ import annotations
import re
import httpx
from dataclasses import dataclass

ORSR_BASE = "https://www.orsr.sk"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

@dataclass
class OrsrFetchResult:
    ico: str
    vypis_url: str | None
    html: str | None
    ok: bool
    reason: str | None = None

def _norm_ico(ico: str) -> str:
    ico = (ico or "").strip()
    ico = re.sub(r"\s+", "", ico)
    return ico

def _get(url: str, timeout: int = 15) -> httpx.Response:
    # ORSR often uses cp1250. httpx handles encoding well, but we can force it if needed.
    # Note: we use sync client for simplicity as it matches original requests logic
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        r = client.get(url, headers={"User-Agent": UA})
        # ORSR is always windows-1250. Force it to avoid auto-detection issues.
        r.encoding = "windows-1250"
        return r

def resolve_vypis_url(ico: str) -> str | None:
    ico = _norm_ico(ico)
    if not ico:
        return None
    url = f"{ORSR_BASE}/hladaj_ico.asp?ICO={ico}"
    r = _get(url)

    # Najstabilnejšie: prvý link na vypis.asp
    import html as html_lib
    text = html_lib.unescape(r.text)
    m = re.search(r'href="(vypis\.asp\?[^"]+)"', text, re.IGNORECASE)
    if not m:
        return None

    href = m.group(1)
    # Ensure we don't have leading slashes if we append to BASE
    return f"{ORSR_BASE}/{href.lstrip('/')}"

def fetch_vypis_html(ico: str) -> OrsrFetchResult:
    ico = _norm_ico(ico)
    if not ico:
        return OrsrFetchResult(ico=ico, vypis_url=None, html=None, ok=False, reason="EMPTY_ICO")

    try:
        vypis_url = resolve_vypis_url(ico)
        if not vypis_url:
            return OrsrFetchResult(ico=ico, vypis_url=None, html=None, ok=False, reason="VYPIS_URL_NOT_FOUND")

        r = _get(vypis_url)
        html = r.text or ""
        if len(html) < 2000:
            return OrsrFetchResult(ico=ico, vypis_url=vypis_url, html=html, ok=False, reason="HTML_TOO_SMALL")

        return OrsrFetchResult(ico=ico, vypis_url=vypis_url, html=html, ok=True)
    except Exception as e:
        return OrsrFetchResult(ico=ico, vypis_url=None, html=None, ok=False, reason=f"EXC:{type(e).__name__}")
