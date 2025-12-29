"""
Playwright-based KRS service for Poland.
Uses headless Chromium to bypass Cloudflare protection on rejestr.io.
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fastapi import HTTPException
from ..models.company import Company


class KRSPlaywrightService:
    """Service for fetching Polish company data via Playwright headless browser."""
    
    async def fetch_company(self, krs_number: str) -> Company:
        """
        Fetch company data from rejestr.io using Playwright.
        
        Args:
            krs_number: Polish KRS number (e.g., "0000014565")
            
        Returns:
            Company object with extracted data
        """
        # Normalize KRS number (remove leading zeros for URL)
        clean_krs = krs_number.lstrip("0") or "0"
        url = f"https://rejestr.io/krs/{clean_krs}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Navigate and wait for content
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for Cloudflare challenge to resolve (if present)
                await asyncio.sleep(2)
                
                # Check if we got blocked
                if "Just a moment" in await page.content():
                    await asyncio.sleep(5)  # Wait longer for challenge
                
                # Extract company name (h1 tag)
                name = ""
                try:
                    name_el = await page.wait_for_selector("h1", timeout=10000)
                    if name_el:
                        name = await name_el.text_content() or ""
                        name = name.strip()
                except PlaywrightTimeout:
                    pass
                
                # Extract address
                address = ""
                try:
                    # Look for address in common selectors
                    addr_selectors = [
                        "[data-testid='address']",
                        ".company-address",
                        "td:has-text('Adres') + td",
                        "text=Adres >> xpath=../following-sibling::*"
                    ]
                    for sel in addr_selectors:
                        try:
                            addr_el = page.locator(sel).first
                            if await addr_el.count() > 0:
                                address = await addr_el.text_content() or ""
                                address = address.strip()
                                if address:
                                    break
                        except:
                            continue
                except Exception:
                    pass
                
                # Extract status
                status = "AKTYWNA"
                page_text = await page.content()
                if "wykreślona" in page_text.lower() or "rozwiązana" in page_text.lower():
                    status = "WYKREŚLONA"
                elif "w likwidacji" in page_text.lower():
                    status = "W LIKWIDACJI"
                
                await browser.close()
                
                if not name:
                    raise HTTPException(status_code=404, detail=f"KRS {krs_number} nie znaleziono")
                
                return Company(
                    ico=krs_number,
                    name=name,
                    address=address or "Brak danych",
                    status=status,
                    raw_data={"source": "rejestr.io via Playwright"}
                )
                
        except PlaywrightTimeout:
            raise HTTPException(status_code=504, detail="Timeout pri načítaní KRS dát")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Chyba Playwright: {str(e)}")
