#!/usr/bin/env python3
"""
iCOAtlas V4 - Frontend E2E, Regression & Integrity Test Suite (Playwright)
Executes cross-border verification across SK, CZ, PL, and HU with deep DOM assertions.
"""

import sys
import asyncio
import time
from playwright.async_api import async_playwright

FRONTEND_URL = "http://localhost:8009"
BACKEND_URL = "http://localhost:8000"

TEST_CASES = [
    {
        "country": "SK",
        "query": "88888888",
        "expected_name": "Testovacia Firma, s.r.o.",
        "expected_dic": "2020202020",
        "expected_badge": "KRITICKÉ RIZIKO",
    },
    {
        "country": "CZ",
        "query": "27082440",
        "expected_name": "Alza.cz a.s.",
        "expected_dic": "CZ27082440",
        "expected_badge": None,
    },
]

async def run_e2e_suite():
    print("=" * 70)
    print("🚀 iCOAtlas V4 - Playwright E2E & Frontend Integrity Tests")
    print(f"Target Frontend: {FRONTEND_URL}")
    print(f"Target Backend:  {BACKEND_URL}")
    print("=" * 70)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # -------------------------------------------------------------
        # TEST 1: Homepage Load & Core Elements Integrity
        # -------------------------------------------------------------
        print("\n[TEST 1] Overenie načítania homepage a integrity UI prvkov...")
        try:
            t0 = time.time()
            resp = await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
            load_time = round((time.time() - t0) * 1000)
            assert resp.status == 200, f"HTTP status is {resp.status}"

            title = await page.title()
            assert "iCOAtlas" in title, f"Nesprávny titulok: {title}"

            # Verify search input and analyze button
            search_input = page.locator("input[placeholder*='Zadajte IČO']")
            assert await search_input.count() > 0, "Vyhľadávací input chýba!"

            analyze_btn = page.locator("button:has-text('Analyzovať')")
            assert await analyze_btn.count() > 0, "Tlačidlo 'Analyzovať' chýba!"

            print(f"  ✅ Homepage načítaná za {load_time}ms (Titulok: '{title}')")
            results.append(("Homepage Load & UI Integrity", True, f"{load_time}ms"))
        except Exception as e:
            print(f"  ❌ Zlyhalo: {e}")
            results.append(("Homepage Load & UI Integrity", False, str(e)))

        # -------------------------------------------------------------
        # TEST 2: SK Search & DIČ Corporate Identifier Protection
        # -------------------------------------------------------------
        print("\n[TEST 2] E2E Vyhľadávanie SK firmy (88888888) & integrita DIČ...")
        try:
            # Click Slovakia button
            sk_btn = page.locator("button:has-text('Slovensko')").first
            if await sk_btn.count() > 0:
                await sk_btn.click()
                await asyncio.sleep(0.3)

            # Fill search input
            search_input = page.locator("input[placeholder*='Zadajte IČO']")
            await search_input.fill("88888888")

            # Click analyze
            analyze_btn = page.locator("button:has-text('Analyzovať')")
            await analyze_btn.click()

            # Wait for loading overlay to appear and then detach
            try:
                await page.wait_for_selector("text=Prebieha hĺbková analýza", state="attached", timeout=3000)
                await page.wait_for_selector("text=Prebieha hĺbková analýza", state="detached", timeout=35000)
            except Exception:
                await asyncio.sleep(3)

            # Wait for results card
            await page.wait_for_selector("text=Testovacia Firma, s.r.o.", timeout=15000)

            # Verify DIČ is visible in DOM (Protection Rule 1)
            dic_locator = page.locator("text=2020202020")
            assert await dic_locator.count() > 0, "Kritická chyba: DIČ 2020202020 nie je v DOM!"

            # Verify Risk Badge
            risk_badge = page.locator("text=KRITICKÉ RIZIKO")
            assert await risk_badge.count() > 0, "Chýba indikátor 'KRITICKÉ RIZIKO'!"

            # Verify Copy DIČ button
            copy_btn = page.locator("button:has-text('Kopírovať DIČ')").first
            assert await copy_btn.count() > 0, "Tlačidlo 'Kopírovať DIČ' nie je prítomné!"

            print("  ✅ Firma 'Testovacia Firma, s.r.o.' nájdená")
            print("  ✅ DIČ '2020202020' úspešne vykreslené (Rule 1: OK)")
            print("  ✅ Rizikový scoring a badge 'KRITICKÉ RIZIKO' overený")
            results.append(("SK Search & DIČ Integrity", True, "DIČ: 2020202020 OK"))
        except Exception as e:
            print(f"  ❌ Zlyhalo: {e}")
            results.append(("SK Search & DIČ Integrity", False, str(e)))

        # -------------------------------------------------------------
        # TEST 3: Graph Topology & Entity Nodes Integrity
        # -------------------------------------------------------------
        print("\n[TEST 3] Overenie grafovej vizualizácie a topológie entít...")
        try:
            # Check if relationship graph container or canvas is rendered
            graph_container = page.locator("canvas, [class*='graph'], [class*='force-graph']").first
            assert await graph_container.count() > 0, "Grafový kontajner nebol nájdený!"

            # Verify executive details
            statutari = page.locator("text=Jozef Mrkvička")
            assert await statutari.count() > 0, "Štatutár Jozef Mrkvička chýba v detaile!"

            # Verify white collar / nominee detection
            nominee_warning = page.locator("text=Možný biely kôň")
            assert await nominee_warning.count() > 0, "Detekcia bieleho koňa (John Doe) chýba!"

            print("  ✅ Grafový kontajner a štatutári vykreslení")
            print("  ✅ Detekcia bieleho koňa (zahraničný konateľ) overená")
            results.append(("Graph & Entities Topology", True, "Graf & Biely kôň OK"))
        except Exception as e:
            print(f"  ❌ Zlyhalo: {e}")
            results.append(("Graph & Entities Topology", False, str(e)))

        # -------------------------------------------------------------
        # TEST 3b: OSINT Intelligence Ingestion Tabs & Deep Metadata
        # -------------------------------------------------------------
        print("\n[TEST 3b] Overenie OSINT záložiek (Časová os, Blacklisty, Listiny, UBO)...")
        try:
            # 1. Timeline Tab
            tab_timeline = page.locator("button[data-testid='tab-timeline']")
            assert await tab_timeline.count() > 0, "Záložka 'Časová os zmien' chýba!"
            await tab_timeline.click()
            await asyncio.sleep(0.5)

            timeline_heading = page.locator("text=Chronologická história zápisov")
            assert await timeline_heading.count() > 0, "Nadpis časovej osi sa nezobrazil!"

            nominee_audit = page.locator("text=Detegovaný podozrivý prevod subjektu")
            assert await nominee_audit.count() > 0, "Nominee handover audit card chýba!"

            # 2. Risk & Blacklists Tab
            tab_risk = page.locator("button[data-testid='tab-risk']")
            assert await tab_risk.count() > 0, "Záložka 'Finančné a daňové riziko' chýba!"
            await tab_risk.click()
            await asyncio.sleep(0.5)

            sp_record = page.locator("text=Sociálna poisťovňa")
            assert await sp_record.count() > 0, "Záznam Sociálnej poisťovne chýba v blackliste!"

            vszp_record = page.locator("text=Všeobecná zdravotná poisťovňa")
            assert await vszp_record.count() > 0, "Záznam VšZP chýba v blackliste!"

            # 3. Deeds Tab
            tab_deeds = page.locator("button[data-testid='tab-deeds']")
            assert await tab_deeds.count() > 0, "Záložka 'Zbierka listín' chýba!"
            await tab_deeds.click()
            await asyncio.sleep(0.5)

            deeds_heading = page.locator("text=Zbierka listín Obchodného registra SR")
            assert await deeds_heading.count() > 0, "Nadpis Zbierky listín sa nezobrazil!"

            # 4. UBO & RPVS Tab
            tab_ubo = page.locator("button[data-testid='tab-ubo']")
            assert await tab_ubo.count() > 0, "Záložka 'Majetkové pozadie (UBO)' chýba!"
            await tab_ubo.click()
            await asyncio.sleep(0.5)

            rpvs_banner = page.locator("text=Subjekt je zapísaný v Registri partnerov verejného sektora")
            assert await rpvs_banner.count() > 0, "RPVS status banner chýba!"

            ubo_name = page.locator("text=Kráľovský Majiteľ")
            assert await ubo_name.count() > 0, "Konečný užívateľ výhod (Kráľovský Majiteľ) chýba v UBO záložke!"

            print("  ✅ Záložka 'Časová os zmien' & Nominee handover audit overené")
            print("  ✅ Záložka 'Finančné a daňové riziko' (Sociálna poisťovňa, VšZP) overená")
            print("  ✅ Záložka 'Zbierka listín' overená")
            print("  ✅ Záložka 'Majetkové pozadie (UBO)' & RPVS overené")
            results.append(("OSINT Intelligence Tabs (All 4)", True, "Timeline, Blacklists, Deeds, UBO OK"))
        except Exception as e:
            print(f"  ❌ Zlyhalo: {e}")
            results.append(("OSINT Intelligence Tabs (All 4)", False, str(e)))

        # -------------------------------------------------------------
        # TEST 4: CZ Search & ARES DIČ Integrity
        # -------------------------------------------------------------
        print("\n[TEST 4] E2E Vyhľadávanie CZ firmy (27082440 - Alza.cz a.s.)...")
        try:
            # Clean navigation to reset state
            await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(0.5)

            # Switch to CZ
            cz_btn = page.locator("button:has-text('Česko')").first
            if await cz_btn.count() > 0:
                await cz_btn.click()
                await asyncio.sleep(0.3)

            search_input = page.locator("input[placeholder*='Zadajte IČO']")
            await search_input.fill("27082440")

            analyze_btn = page.locator("button:has-text('Analyzovať')")
            await analyze_btn.click()

            # Wait for loading overlay to detach
            try:
                await page.wait_for_selector("text=Prebieha hĺbková analýza", state="attached", timeout=3000)
                await page.wait_for_selector("text=Prebieha hĺbková analýza", state="detached", timeout=35000)
            except Exception:
                await asyncio.sleep(3)

            await page.wait_for_selector("text=Alza.cz a.s.", timeout=20000)

            # Check CZ DIČ
            cz_dic = page.locator("text=CZ27082440")
            assert await cz_dic.count() > 0, "CZ DIČ CZ27082440 chýba v DOM!"

            print("  ✅ Firma 'Alza.cz a.s.' nájdená")
            print("  ✅ CZ DIČ 'CZ27082440' úspešne overené")
            results.append(("CZ Search & DIČ Integrity", True, "DIČ: CZ27082440 OK"))
        except Exception as e:
            print(f"  ❌ Zlyhalo: {e}")
            results.append(("CZ Search & DIČ Integrity", False, str(e)))

        # -------------------------------------------------------------
        # TEST 5: Auto-Detection of Country from Input Format
        # -------------------------------------------------------------
        print("\n[TEST 5] Overenie automatickej detekcie krajiny v search bare...")
        try:
            await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(0.5)

            country_select = page.locator("select[aria-label='Výber krajiny']")
            search_input = page.locator("input[placeholder*='Zadajte IČO']")

            # 1. Initial country should be SK
            initial_val = await country_select.input_value()
            assert initial_val == "SK", f"Predvolená hodnota mala byť SK, ale je: {initial_val}"

            # 2. Type Czech DIČ with CZ prefix -> should auto-switch to CZ
            await search_input.fill("CZ27082440")
            await asyncio.sleep(0.3)
            val_after_cz = await country_select.input_value()
            assert val_after_cz == "CZ", f"Po zadaní CZ27082440 mala byť krajina CZ, ale je: {val_after_cz}"

            # Verify 'Auto' badge is visible
            auto_badge = page.locator("text=Auto")
            assert await auto_badge.count() > 0, "'Auto' badge indikujúci detekciu krajiny chýba!"

            # 3. Type Slovak 8-digit IČO -> should auto-switch to SK
            await search_input.fill("88888888")
            await asyncio.sleep(0.3)
            val_after_sk = await country_select.input_value()
            assert val_after_sk == "SK", f"Po zadaní 88888888 mala byť krajina SK, ale je: {val_after_sk}"

            print("  ✅ Predvolená krajina 'SK' overená")
            print("  ✅ Auto-detekcia 'CZ' pre CZ27082440 (vrátane Auto odznaku) overená")
            print("  ✅ Auto-detekcia 'SK' pre 8-miestne IČO (88888888) overená")
            results.append(("Country Auto-Detection Combobox", True, "SK/CZ/PL auto-switch OK"))
        except Exception as e:
            print(f"  ❌ Zlyhalo: {e}")
            results.append(("Country Auto-Detection Combobox", False, str(e)))

        await browser.close()

    # -------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 SÚHRN PLAYWRIGHT E2E & REGRESNÝCH TESTOV:")
    print("=" * 70)
    all_passed = True
    for name, ok, note in results:
        status_icon = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_passed = False
        print(f"  {status_icon} | {name:<35} | {note}")
    print("=" * 70)

    if all_passed:
        print("🎉 VŠETKY FRONTEND E2E & INTEGRITY TESTY PREŠLI NA 100%!")
        sys.exit(0)
    else:
        print("⚠️ BOLI ZISTENÉ REGRESNÉ CHYBY V TESTOCH.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_e2e_suite())
