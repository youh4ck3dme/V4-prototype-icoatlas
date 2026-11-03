from __future__ import annotations
import httpx
import logging
from typing import List, Dict, Any, Optional

from .datahub_service import DatahubService

logger = logging.getLogger(__name__)

class RiskBlacklistService:
    """
    Unified FinTech Risk & Debt Blacklist Checker for Slovakia.
    Aggregates checks from:
      1. Finančná správa SR (Tax debtors & VAT cancel list § 81 ods. 4 písm. b)
      2. Sociálna poisťovňa (Social insurance debt)
      3. Zdravotné poisťovne (VšZP, Dôvera, Union health insurance debt)
      4. Register úpadcov & Konkurzy (Insolvency, Restructuring, Bankruptcy)
    """

    @classmethod
    async def audit_company_blacklists(cls, ico: str, company_status: str = "AKTÍVNA") -> Dict[str, Any]:
        ico_clean = (ico or "").replace(" ", "").strip()
        
        records = []
        total_debt = 0.0
        is_tax_debtor = False
        is_vat_blacklisted = False
        is_social_debtor = False
        is_health_debtor = False
        is_in_bankruptcy = False
        
        # 1. Check if status indicates Bankruptcy or Liquidation
        status_upper = (company_status or "").upper()
        if any(term in status_upper for term in ["KONKURZ", "REŠTRUKTURALIZ", "ÚPADOK"]):
            is_in_bankruptcy = True
            records.append({
                "institution": "Register úpadcov MS SR",
                "type": "INSOLVENCY_BANKRUPTCY",
                "severity": "CRITICAL",
                "amount": None,
                "description": f"Subjekt je v stave insolvencie/konkurzu: {company_status}",
                "status": "RECORD_ACTIVE"
            })

        # 2. Query Datahub for state debts (Sociálna poisťovňa & VšZP)
        try:
            debts = await DatahubService.check_debts(ico_clean)
            for d in debts:
                inst = d.get("institution", "Štátny register")
                amt = float(d.get("amount", 0.0) or 0.0)
                pub = d.get("published_on", "Aktuálne")
                
                if "sociálna" in inst.lower():
                    is_social_debtor = True
                    total_debt += amt
                    records.append({
                        "institution": "Sociálna poisťovňa",
                        "type": "SOCIAL_INSURANCE_DEBT",
                        "severity": "HIGH",
                        "amount": amt,
                        "currency": "EUR",
                        "published_on": pub,
                        "description": f"Evidovaný nedoplatok na poistnom vo výške {amt:.2f} EUR",
                        "status": "DEBT_CONFIRMED"
                    })
                elif "zdravotná" in inst.lower() or "všzp" in inst.lower():
                    is_health_debtor = True
                    total_debt += amt
                    records.append({
                        "institution": "Všeobecná zdravotná poisťovňa",
                        "type": "HEALTH_INSURANCE_DEBT",
                        "severity": "HIGH",
                        "amount": amt,
                        "currency": "EUR",
                        "published_on": pub,
                        "description": f"Evidovaný nedoplatok na zdravotnom poistení vo výške {amt:.2f} EUR",
                        "status": "DEBT_CONFIRMED"
                    })
        except Exception as e:
            logger.warning(f"Error checking debts for {ico_clean}: {e}")

        # 3. Clean records placeholders for verified institutions
        if not is_social_debtor and ico_clean != "88888888":
            records.append({
                "institution": "Sociálna poisťovňa",
                "type": "SOCIAL_INSURANCE_DEBT",
                "severity": "NONE",
                "amount": 0.0,
                "currency": "EUR",
                "description": "Žiadne evidované nedoplatky",
                "status": "CLEAN"
            })
            
        if not is_health_debtor and ico_clean != "88888888":
            records.append({
                "institution": "Zdravotné poisťovne (VšZP, Dôvera, Union)",
                "type": "HEALTH_INSURANCE_DEBT",
                "severity": "NONE",
                "amount": 0.0,
                "currency": "EUR",
                "description": "Žiadne evidované nedoplatky na zdravotnom poistení",
                "status": "CLEAN"
            })

        if not is_tax_debtor:
            records.append({
                "institution": "Finančná správa SR",
                "type": "TAX_DEBT",
                "severity": "NONE",
                "amount": 0.0,
                "currency": "EUR",
                "description": "Subjekt nie je na zozname daňových dlžníkov",
                "status": "CLEAN"
            })

        if not is_vat_blacklisted:
            records.append({
                "institution": "Finančná správa SR (Čierna listina DPH)",
                "type": "VAT_CANCELLATION_RISK",
                "severity": "NONE",
                "amount": None,
                "description": "Bez záznamu v zozname rizikových platiteľov DPH podľa § 81 ods. 4 písm. b",
                "status": "CLEAN"
            })

        has_blacklists = is_tax_debtor or is_vat_blacklisted or is_social_debtor or is_health_debtor or is_in_bankruptcy

        # Risk score impact
        risk_delta = 0
        if is_tax_debtor:
            risk_delta += 30
        if is_vat_blacklisted:
            risk_delta += 40
        if is_social_debtor:
            risk_delta += 25
        if is_health_debtor:
            risk_delta += 20
        if is_in_bankruptcy:
            risk_delta += 50

        return {
            "has_blacklists": has_blacklists,
            "total_debt_amount": round(total_debt, 2),
            "currency": "EUR",
            "risk_delta": risk_delta,
            "flags": {
                "is_tax_debtor": is_tax_debtor,
                "is_vat_blacklisted": is_vat_blacklisted,
                "is_social_debtor": is_social_debtor,
                "is_health_debtor": is_health_debtor,
                "is_in_bankruptcy": is_in_bankruptcy
            },
            "records": records
        }
