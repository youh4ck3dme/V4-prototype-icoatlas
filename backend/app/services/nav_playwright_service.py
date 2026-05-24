"""
Playwright-based service for Hungary using companyregister.hu.
Uses headless Chromium to search Hungarian company registry.
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fastapi import HTTPException
from ..models.company import Company


class NAVPlaywrightService:
    """Service for fetching Hungarian company data via companyregister.hu."""
    
    async def fetch_company(self, cegjegyzek_szam: str) -> Company:
        """
        Fetch company data from companyregister.hu using Playwright.
        """
        import time
        start_time = time.time()
        
        # Normalize format (ensure dashes, remove CG. prefix)
        clean_id = cegjegyzek_szam.replace("CG.", "").replace(" ", "")
        if "-" not in clean_id and len(clean_id) >= 10:
            formatted = f"{clean_id[:2]}-{clean_id[2:4]}-{clean_id[4:]}"
        else:
            formatted = clean_id
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    ignore_https_errors=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate to companyregister.hu
                await page.goto('https://companyregister.hu/', wait_until='domcontentloaded', timeout=20000)
                # Wait for initial page load
                await page.wait_for_selector('input', timeout=5000)
                
                # Find and fill search input
                # Try visible search input first
                search_input = page.locator('input[placeholder*="Search"], input[placeholder*="Keresés"], input#search, input[type="text"]').first
                if await search_input.count() > 0:
                    await search_input.fill(formatted)
                    await asyncio.sleep(0.5)
                    await page.keyboard.press('Enter')
                else:
                    # Fallback if no input found
                    await browser.close()
                    raise HTTPException(status_code=502, detail="Search input not found on HU site")
                
                # Wait for results or "not found"
                try:
                    # Target both results table or a "not found" message
                    await page.wait_for_selector('table, .alert, .not-found, text=Company name:', timeout=10000)
                except:
                    pass
                
                # Extract data from table rows and key-value pairs
                name = ""
                address = ""
                status = "AKTÍV"
                
                # Snapshot of all text for status check
                page_text = await page.evaluate("() => document.body.innerText")
                
                # Try all rows
                trs = await page.locator('tr').all()
                for tr in trs:
                    txt = await tr.text_content()
                    if not txt: continue
                    txt = txt.strip()
                    
                    # Robust Name detection
                    if any(key in txt for key in ['Company name:', 'Cégnév:', 'A cég megnevezése:']):
                        parts = re.split(r'Company name:|Cégnév:|A cég megnevezése:', txt, flags=re.IGNORECASE)
                        if len(parts) > 1 and not name:
                            name = parts[1].strip().split('\n')[0].strip()
                    
                    # Robust Address detection
                    if any(key.lower() in txt.lower() for key in ['registered seat:', 'registered office:', 'Székhely:', 'A cég székhelye:']):
                        parts = re.split(r'seat:|office:|Székhely:|székhelye:', txt, flags=re.IGNORECASE)
                        if len(parts) > 1 and not address:
                            address = parts[1].strip().split('\n')[0].strip()

                # Status check from whole page content
                page_content = page_text.lower()
                if any(x in page_content for x in ["megszűnt", "törölt", "dissolved", "cancelled"]):
                    status = "MEGSZŰNT"
                elif any(x in page_content for x in ["felszámolás", "liquidation", "liquidation"]):
                    status = "FELSZÁMOLÁS ALATT"
                elif any(x in page_content for x in ["kényszertörlés", "compulsory strike-off"]):
                    status = "KÉNYSZERTÖRLÉS"
                
                await browser.close()
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                if not name:
                    # Record fail health metrics if we had a system to do so
                    raise HTTPException(status_code=404, detail=f"HU Company {cegjegyzek_szam} not found")
                
                adoszam = None
                adoszam_match = re.search(r'\b\d{8}-\d-\d{2}\b', page_text)
                if adoszam_match:
                    adoszam = adoszam_match.group(0)

                return Company(
                    ico=cegjegyzek_szam,
                    name=name,
                    address=address or "Nincs adat",
                    status=status,
                    raw_data={
                        "source": "companyregister.hu",
                        "provider_latency_ms": latency_ms,
                        "provider_ok": True,
                        "adoszam": adoszam
                    }
                )

                
        except PlaywrightTimeout:
            raise HTTPException(status_code=504, detail="Timeout pri načítaní HU dát")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Chyba Playwright: {str(e)}")
