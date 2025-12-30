# Live API Test Results (Phase 17)

This file documents the live API test results for Phase 17.

```bash
# Activation of environment
source /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas/.venv/bin/activate

# Shell information
# To update your account to use zsh, please run `chsh -s /bin/zsh`.
# For more details, please visit <https://support.apple.com/kb/HT208050>.

# API Test Command
curl -s "http://localhost:8000/api/v4/search/SK/00686930"
```

## JSON Response (Tatra banka, a.s.)

```json
{
  "country": "SK",
  "primary_id": "00686930",
  "legal_name": "Tatra banka, a.s.",
  "status": "Aktívna",
  "source_api": "SK_ORSR",
  "fetched_at": "2025-12-21T13:53:58.718808",
  "tax_id": null,
  "vat_id": null,
  "legal_form": "Akciová spoločnosť",
  "street": "Hodžovo námestie 3 Bratislava 1",
  "city": "Hodžovo námestie 3 Bratislava 1",
  "postal_code": "811 06",
  "registration_date": null,
  "dissolution_date": null,
  "executives": [
    "Michal Liday",
    "Natália Major",
    "Bernhard Henhappel",
    "Peter Matúš",
    "Martin Kubík",
    "Zuzana Koštialová",
    "Oliver Pichler"
  ],
  "shareholders": [],
  "risk_score": 0,
  "risk_flags": null,
  "raw_data": {
    "ico": "00686930",
    "country": "SK",
    "name": "Tatra banka, a.s.",
    "legal_form": "Akciová spoločnosť",
    "address": "Hodžovo námestie 3 Bratislava 1 811 06",
    "postal_code": "811 06",
    "city": "Hodžovo námestie 3 Bratislava 1",
    "region": "Bratislavský",
    "district": "Bratislava I",
    "executives": [
      "Michal Liday",
      "Natália Major",
      "Bernhard Henhappel",
      "Peter Matúš",
      "Martin Kubík",
      "Zuzana Koštialová",
      "Oliver Pichler"
    ],
    "shareholders": [],
    "founded": null,
    "status": "Aktívna",
    "dic": null,
    "ic_dph": null,
    "registration_id": "71/B",
    "registration_section": "Sa",
    "capital": "64 326 228 EUR Rozsah splatenia: 64 326 228 EUR",
    "street": "Hodžovo námestie 3 Bratislava 1",
    "zip": "811 06"
  }
}
```

> [!NOTE]
> Detailed shell information and troubleshooting can be found at <https://support.apple.com/kb/HT208050>.
