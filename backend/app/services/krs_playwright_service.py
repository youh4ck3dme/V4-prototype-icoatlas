"""
Playwright-based KRS service for Poland using biznes.gov.pl.
Uses headless Chromium to search Polish company registry.
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fastapi import HTTPException
from ..models.company import Company


class KRSPlaywrightService:
    """Service for fetching Polish company data via biznes.gov.pl."""
    
    async def fetch_company(self, nip_or_krs: str) -> Company:
        """
        Fetch company data from biznes.gov.pl using Playwright.
        
        Args:
            nip_or_krs: Polish NIP or KRS number (e.g., "1990123066")
            
        Returns:
            Company object with extracted data
        """
        # Clean the number
        clean_id = nip_or_krs.replace("-", "").replace(" ", "")
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    ignore_https_errors=True,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Navigate to biznes.gov.pl company search
                await page.goto('https://www.biznes.gov.pl/pl/wyszukiwarka-firm', wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(2)
                
                # Find the main search input
                search_input = page.locator('input[name="search"], input[placeholder*="Szukaj"]').first
                if await search_input.count() > 0:
                    await search_input.fill(clean_id)
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(3)
                    await page.wait_for_load_state("networkidle", timeout=15000)
                
                # Get page content
                page_content = await page.content()
                
                # Look for company results
                name = ""
                address = ""
                
                # Try to find company name in results
                result_links = page.locator('a.result-link, .search-result a, .company-name, h2 a, h3 a').first
                if await result_links.count() > 0:
                    name = await result_links.text_content()
                    name = name.strip() if name else ""
                    
                    # Click to get details
                    try:
                        await result_links.click()
                        await asyncio.sleep(2)
                        page_content = await page.content()
                    except:
                        pass
                
                # Try table-based extraction for address
                if not address:
                    try:
                        trs = await page.locator('tr, .info-row, dt').all()
                        for tr in trs:
                            txt = await tr.text_content()
                            if 'Adres' in txt or 'Siedziba' in txt:
                                parts = txt.split(':')
                                if len(parts) > 1:
                                    address = parts[1].strip().split('\n')[0].strip()
                                    break
                    except:
                        pass
                
                # Extract status
                status = "AKTYWNA"
                if "wykreślona" in page_content.lower() or "nieaktywna" in page_content.lower():
                    status = "WYKREŚLONA"
                elif "zawieszona" in page_content.lower():
                    status = "ZAWIESZONA"
                elif "w likwidacji" in page_content.lower():
                    status = "W LIKWIDACJI"
                
                await browser.close()
                
                if not name:
                    raise HTTPException(status_code=404, detail=f"NIP/KRS {nip_or_krs} nie znaleziono")
                
                import re
                def pl_nip_checksum_ok(nip10: str) -> bool:
                    if not re.fullmatch(r"\d{10}", nip10):
                        return False
                    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
                    total = sum(int(nip10[i]) * weights[i] for i in range(9))
                    chk = total % 11
                    if chk == 10:
                        return False
                    return chk == int(nip10[9])

                nip_val = None
                for m in re.finditer(r'\b\d{10}\b', page_content):
                    candidate = m.group(0)
                    if pl_nip_checksum_ok(candidate):
                        nip_val = candidate
                        break

                return Company(
                    ico=nip_or_krs,
                    name=name,
                    address=address or "Brak danych",
                    status=status,
                    raw_data={
                        "source": "biznes.gov.pl via Playwright",
                        "nip": nip_val
                    }
                )
                
        except PlaywrightTimeout:
            raise HTTPException(status_code=504, detail="Timeout pri načítaní PL dát")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Chyba Playwright: {str(e)}")
