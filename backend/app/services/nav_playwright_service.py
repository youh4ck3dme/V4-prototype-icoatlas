"""
Playwright-based service for Hungary using companyregister.hu.
Uses headless Chromium to search Hungarian company registry.
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fastapi import HTTPException
from ..models.company import Company


class NAVPlaywrightService:
    """Service for fetching Hungarian company data via companyregister.hu."""
    
    async def fetch_company(self, cegjegyzek_szam: str) -> Company:
        """
        Fetch company data from companyregister.hu using Playwright.
        
        Args:
            cegjegyzek_szam: Hungarian company registration number (e.g., "01-09-707490")
            
        Returns:
            Company object with extracted data
        """
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
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Navigate to companyregister.hu
                await page.goto('https://companyregister.hu/', wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(2)
                
                # Find and fill search input
                search_input = page.locator('input[type="text"], input[type="search"], input#search').first
                if await search_input.count() > 0:
                    await search_input.fill(formatted)
                    await asyncio.sleep(1)
                    
                    # Click search button or press Enter
                    search_btn = page.locator('button:has-text("Search"), button[type="submit"]').first
                    if await search_btn.count() > 0:
                        await search_btn.click()
                    else:
                        await page.keyboard.press('Enter')
                    
                    await asyncio.sleep(3)
                    await page.wait_for_load_state("networkidle", timeout=15000)
                
                # Extract data from table rows
                name = ""
                address = ""
                status = "AKTÍV"
                
                try:
                    trs = await page.locator('tr').all()
                    for tr in trs:
                        txt = await tr.text_content()
                        if not txt:
                            continue
                        txt = txt.strip()
                        
                        if 'Company name:' in txt:
                            # Extract company name after the label
                            parts = txt.split('Company name:')
                            if len(parts) > 1:
                                name = parts[1].strip()
                        
                        elif 'registered seat:' in txt.lower() or 'Székhely' in txt:
                            parts = txt.split(':')
                            if len(parts) > 1:
                                address = ':'.join(parts[1:]).strip()
                
                except Exception as e:
                    pass
                
                # Get page content for status
                page_content = await page.content()
                if "megszűnt" in page_content.lower() or "törölt" in page_content.lower() or "dissolved" in page_content.lower():
                    status = "MEGSZŰNT"
                elif "felszámolás" in page_content.lower() or "liquidation" in page_content.lower():
                    status = "FELSZÁMOLÁS ALATT"
                
                await browser.close()
                
                if not name:
                    raise HTTPException(status_code=404, detail=f"Cégjegyzékszám {cegjegyzek_szam} nem található")
                
                return Company(
                    ico=cegjegyzek_szam,
                    name=name,
                    address=address or "Nincs adat",
                    status=status,
                    raw_data={"source": "companyregister.hu via Playwright"}
                )
                
        except PlaywrightTimeout:
            raise HTTPException(status_code=504, detail="Timeout pri načítaní HU dát")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Chyba Playwright: {str(e)}")
