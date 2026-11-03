import pytest
import httpx
from backend.app.main import app
from backend.app.services.orsr_history_parser import (
    parse_orsr_full_history,
    parse_orsr_deeds
)
from backend.app.services.risk_blacklist_service import RiskBlacklistService
from backend.app.services.rpvs_service import RPVSService

SAMPLE_P1_HTML = """
<!DOCTYPE HTML>
<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=windows-1250"></head>
<body>
<table width="100%">
<tr><td><span class="tl">Oddiel:&nbsp;</span> <span class="ra">Sro</span></td>
<td><span class="tl">Vložka číslo:&nbsp;</span> <span class="ra">49430/S </span></td></tr>
</table>
<table width="100%">
<tr>
  <td width="20%"><span class="tl">Obchodné meno:&nbsp;</span></td>
  <td width="80%">
    <table width="100%">
      <tr><td><span class="ro"> MK-EU s. r. o. </span> (od: 30.11.2017 do: 20.05.2024)</td></tr>
      <tr><td><span class="ra"> EB-EU s. r. o. </span> (od: 21.05.2024)</td></tr>
    </table>
  </td>
</tr>
</table>
<table width="100%">
<tr>
  <td width="20%"><span class="tl">Sídlo:&nbsp;</span></td>
  <td width="80%">
    <table width="100%">
      <tr><td><span class="ro"> Hronská 10, Zvolen 960 01 </span> (od: 30.11.2017 do: 20.05.2024)</td></tr>
      <tr><td><span class="ra"> Kukučínova 22, Banská Bystrica 974 01 </span> (od: 21.05.2024)</td></tr>
    </table>
  </td>
</tr>
</table>
<table width="100%">
<tr>
  <td width="20%"><span class="tl">Štatutárny orgán:&nbsp;</span></td>
  <td width="80%">
    <table width="100%">
      <tr><td><span class="ro"> Marek Kostovčík </span> (od: 30.11.2017 do: 20.05.2024)</td></tr>
      <tr><td><span class="ra"> Erik Babčan </span> (od: 21.05.2024)</td></tr>
    </table>
  </td>
</tr>
</table>
<table width="100%">
<tr>
  <td width="20%"><span class="tl">Spoločníci:&nbsp;</span></td>
  <td width="80%">
    <table width="100%">
      <tr><td><span class="ro"> Marek Kostovčík </span> (od: 30.11.2017 do: 20.05.2024)</td></tr>
      <tr><td><span class="ra"> Erik Babčan </span> (od: 21.05.2024)</td></tr>
    </table>
  </td>
</tr>
</table>
</body>
</html>
"""

SAMPLE_ZBL_HTML = """
<!DOCTYPE HTML>
<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=windows-1250"></head>
<body>
<table>
<tr>
  <td>Názov dokumentu: Riadna účtovná závierka 2023.pdf Typ dokumentu: 1-G Účtovná závierka</td>
  <td>Dátum doručenia: 30.06.2024</td>
</tr>
<tr>
  <td>Názov dokumentu: Spoločenská zmluva a stanovy.pdf Typ dokumentu: 1-B Zmena spoločenskej zmluvy</td>
  <td>Dátum doručenia: 21.05.2024</td>
</tr>
</table>
</body>
</html>
"""


def test_parse_orsr_full_history():
    parsed = parse_orsr_full_history(SAMPLE_P1_HTML, current_data={"registration_date": "30.11.2017", "executives": [{"name": "Erik Babčan"}], "owners": [{"name": "Erik Babčan"}]})
    assert any(h["name"] == "MK-EU s. r. o." for h in parsed["historical_names"])
    assert len(parsed["timeline"]) >= 2
    
    types = [t["type"] for t in parsed["timeline"]]
    assert "NAME_CHANGE" in types
    assert "SEAT_RELOCATION" in types

    analysis = parsed["nominee_handover_analysis"]
    assert analysis["total_name_changes"] == 1
    assert analysis["total_relocations"] == 1
    assert analysis["total_historical_executives"] >= 1


def test_parse_orsr_deeds():
    deeds = parse_orsr_deeds(SAMPLE_ZBL_HTML)
    assert len(deeds) == 2
    assert deeds[0]["category"] == "FINANCIAL_STATEMENT"
    assert deeds[0]["delivery_date"] == "30.06.2024"
    assert deeds[1]["category"] == "LEGAL_CONTRACT"
    assert deeds[1]["delivery_date"] == "21.05.2024"


@pytest.mark.asyncio
async def test_risk_blacklist_service():
    res = await RiskBlacklistService.audit_company_blacklists("88888888", "AKTÍVNA")
    assert res["has_blacklists"] is True
    assert res["total_debt_amount"] > 0
    assert any(r["institution"] == "Sociálna poisťovňa" for r in res["records"])
    assert any(r["institution"] == "Všeobecná zdravotná poisťovňa" for r in res["records"])


@pytest.mark.asyncio
async def test_rpvs_service():
    res = await RPVSService.get_rpvs_details("88888888", "Testovacia Firma, s.r.o.")
    assert res["is_registered_in_rpvs"] is True
    assert len(res["ubos"]) >= 1
    ubo = res["ubos"][0]
    assert ubo["name"] == "Kráľovský Majiteľ"
    assert ubo["voting_rights_percentage"] == 100.0
    assert res["authorized_person"]["attorney"] == "JUDr. Milan Spravodlivý"


@pytest.mark.asyncio
async def test_v4_search_endpoint_osint_contract():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/v4/search/88888888", params={"country": "SK", "graph": 1})
        assert r.status_code == 200
        data = r.json()

    # Rule 1 integrity: DIČ must exist and match 2020202020
    assert "company" in data
    assert data["company"].get("dic") in [2020202020, "2020202020"]

    # OSINT Contracts: history, deeds, blacklists, ubo_rpvs
    assert "history" in data
    assert "timeline" in data["history"]
    assert len(data["history"]["timeline"]) >= 3

    assert "deeds" in data
    assert len(data["deeds"]) >= 3

    assert "blacklists" in data
    assert data["blacklists"]["has_blacklists"] is True
    assert len(data["blacklists"]["records"]) >= 4

    assert "ubo_rpvs" in data
    assert data["ubo_rpvs"]["is_registered_in_rpvs"] is True
    assert len(data["ubo_rpvs"]["ubos"]) >= 1
