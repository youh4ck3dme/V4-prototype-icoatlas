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

def _get(url: str, timeout: int = 20, retries: int = 2) -> httpx.Response:
    # ORSR often uses cp1250. httpx handles encoding well, but we can force it if needed.
    # Note: we use sync client for simplicity as it matches original requests logic
    import time
    last_err = None
    for attempt in range(retries):
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                r = client.get(url, headers={"User-Agent": UA})
                r.encoding = "windows-1250"
                return r
        except Exception as e:
            last_err = e
            time.sleep(1)
    if last_err:
        raise last_err

def resolve_vypis_url(ico: str) -> str | None:
    ico = _norm_ico(ico)
    if not ico:
        return None
    url = f"{ORSR_BASE}/hladaj_ico.asp?ICO={ico}"
    r = _get(url)

    import html as html_lib
    text = html_lib.unescape(r.text)
    matches = re.findall(r'href=[\"\']?(vypis\.asp\?[^\"\'\s>]+)', text, re.IGNORECASE)
    if not matches:
        return None

    clean_matches = [m.replace("&amp;", "&") for m in matches]
    current_matches = [m for m in clean_matches if "p=0" in m.lower()]
    candidates = current_matches if current_matches else clean_matches

    def _extract_id(href: str) -> int:
        m = re.search(r"ID=(\d+)", href, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    best_match = max(candidates, key=_extract_id)
    return f"{ORSR_BASE}/{best_match.lstrip('/')}"

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
