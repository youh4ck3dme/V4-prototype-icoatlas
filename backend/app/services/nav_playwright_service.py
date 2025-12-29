"""
Playwright-based NAV service for Hungary.
Uses headless Chromium to scrape Hungarian company registry.
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fastapi import HTTPException
from ..models.company import Company


class NAVPlaywrightService:
    """Service for fetching Hungarian company data via Playwright headless browser."""
    
    async def fetch_company(self, cegjegyzek_szam: str) -> Company:
        """
        Fetch company data from Hungarian registry using Playwright.
        
        Args:
            cegjegyzek_szam: Hungarian company registration number (e.g., "01-10-041585")
            
        Returns:
            Company object with extracted data
        """
        # Normalize format (ensure dashes)
        clean_id = cegjegyzek_szam.replace("-", "").replace(" ", "")
        if len(clean_id) >= 10:
            formatted = f"{clean_id[:2]}-{clean_id[2:4]}-{clean_id[4:]}"
        else:
            formatted = cegjegyzek_szam
            
        # Try ceginfo.hu first
        url = f"https://www.ceginfo.hu/{formatted}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Navigate and wait
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # Check for 404/not found
                page_content = await page.content()
                if "nem található" in page_content.lower() or "404" in await page.title():
                    # Try e-cegjegyzek.hu as fallback
                    alt_url = f"https://www.e-cegjegyzek.hu/?cegkereses"
                    await page.goto(alt_url, wait_until="networkidle", timeout=30000)
                    
                    # Fill search form
                    try:
                        await page.fill('input[name="cegjegyzekszam"]', formatted)
                        await page.click('button[type="submit"]')
                        await page.wait_for_load_state("networkidle")
                    except:
                        pass
                
                # Extract company name
                name = ""
                name_selectors = ["h1", "h2", ".ceg-nev", ".company-name", "[class*='name']"]
                for sel in name_selectors:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0:
                            text = await el.text_content()
                            if text and len(text.strip()) > 3:
                                name = text.strip()
                                break
                    except:
                        continue
                
                # Extract address
                address = ""
                addr_selectors = [
                    "text=Székhely >> xpath=../following-sibling::*",
                    "[class*='address']",
                    "text=Cím >> xpath=../following-sibling::*"
                ]
                for sel in addr_selectors:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0:
                            text = await el.text_content()
                            if text:
                                address = text.strip()
                                break
                    except:
                        continue
                
                # Extract status
                status = "AKTÍV"
                if "megszűnt" in page_content.lower() or "törölt" in page_content.lower():
                    status = "MEGSZŰNT"
                elif "felszámolás" in page_content.lower():
                    status = "FELSZÁMOLÁS ALATT"
                
                await browser.close()
                
                if not name:
                    raise HTTPException(status_code=404, detail=f"Cégjegyzékszám {cegjegyzek_szam} nem található")
                
                return Company(
                    ico=cegjegyzek_szam,
                    name=name,
                    address=address or "Nincs adat",
                    status=status,
                    raw_data={"source": "HU Registry via Playwright"}
                )
                
        except PlaywrightTimeout:
            raise HTTPException(status_code=504, detail="Timeout pri načítaní HU dát")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Chyba Playwright: {str(e)}")
